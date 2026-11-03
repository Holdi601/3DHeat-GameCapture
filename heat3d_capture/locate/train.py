"""
A per-map place model: trained on renders of the level, to find the
database views that show the same place as a frame of the game.

The global descriptor that comes with DINOv2 alone puts the right views of a
real frame among the first hundred of a play area's two hundred thousand -
close, and not close enough for a shortlist of a dozen (docs/locate.md). This
trains a small head on top of DINOv2, which stays frozen, for one level:

- **Head** (`PlaceHead`): each patch token through a two-layer projection,
  pooled by generalised mean over the patches that show the level (the HUD
  is masked as at query time), joined with the projected class token, unit
  length. A few hundred thousand weights, all written here (MIT); DINOv2's
  weights are Apache-2.0.
- **Pairs**: a place on the level's floors, a direction; two renders of it
  from poses jittered by a metre or two and a dozen degrees, at fields of
  view up to 10 degrees apart, under different light (sun, shadows, ambient)
  - each passed through `augment.game_look` - are the same place. Every other
  pair in the batch is another place, unless it happens to lie within a few
  metres and the same direction, in which case it is left out of the loss
  rather than pushed away.
- **Real frames** with a known pose (pseudo-labels: fixes found by the
  pipeline itself, chosen along a sequence) can be added: the frame and a
  render at its pose make a pair, the gap the renders only imitate.
- **Loss**: InfoNCE (the symmetric contrastive loss of SimCLR) at a learned
  temperature.

The head is saved with what it was trained on; `locate build --head` uses it
for the database's descriptors, and `frames` then uses it for the frames.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np


@dataclass
class TrainOptions:
    steps: int = 600
    #: Pairs per batch (two renders each).
    batch: int = 48
    lr: float = 1e-3
    dim: int = 512
    #: How far apart the two renders of a pair may be: metres, degrees.
    jitter_m: float = 1.5
    jitter_yaw: float = 12.0
    fov_jitter: float = 10.0
    #: Two places nearer than this (metres) and facing within `near_yaw` degrees are not negatives.
    near_m: float = 8.0
    near_yaw: float = 45.0
    #: Share of pairs from real frames, when there are any.
    real_share: float = 0.15
    seed: int = 0


def real_pairs(table: str | Path, video: str | Path, game, *, width: int = 960, least: float = 0.85) -> list[dict]:
    """
    Frames of a recording with the pose `locate frames` found for them - its
    visual rows the track kept, confident at least `least` - ready to train on.
    """
    import cv2
    import pyarrow.parquet as pq

    t = pq.read_table(str(table)).to_pydict()
    cap = cv2.VideoCapture(str(video))
    out = []
    for i, time_s in enumerate(t["time"]):
        if t["source"][i] not in ("visual", "visual+minimap-prior") or not t["kept"][i] or (t["confidence"][i] or 0) < least:
            continue
        view = t["view"][i] if "view" in t else "foot"
        cap.set(cv2.CAP_PROP_POS_MSEC, float(time_s) * 1000.0)
        ok, frame = cap.read()
        if not ok:
            continue
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(cv2.resize(frame, (width, int(round(h * width / w))), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        out.append(
            {
                "rgb": rgb,
                "mask": game.mask(rgb.shape[1], rgb.shape[0], view),
                "position": [t["x_raw"][i], t["y_raw"][i], t["z_raw"][i]],
                "yaw": t["yaw_raw"][i],
                "pitch": t["pitch_raw"][i],
                "hfov": (game.vehicle_hfov or game.hfov) if view == "vehicle" else game.hfov,
                "view": view,
            }
        )
    cap.release()
    return out


def place_head(dim_in: int, dim: int):
    import torch
    from torch import nn

    class PlaceHead(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Sequential(nn.Linear(dim_in, 1024), nn.GELU(), nn.Linear(1024, dim // 2))
            self.cls = nn.Linear(dim_in, dim // 2)
            self.p = nn.Parameter(torch.tensor(3.0))
            self.logit_scale = nn.Parameter(torch.tensor(math.log(1 / 0.07)))

        def forward(self, tokens, keep):
            x = torch.relu(self.proj(tokens[:, 1:])) + 1e-6
            w = keep.float().unsqueeze(2)
            p = self.p.clamp(1.0, 8.0)
            gem = ((x**p * w).sum(1) / w.sum(1).clamp(min=1)) ** (1 / p)
            out = torch.cat([nn.functional.normalize(gem, dim=1), nn.functional.normalize(self.cls(tokens[:, 0]), dim=1)], dim=1)
            return nn.functional.normalize(out, dim=1)

    return PlaceHead()


def load_head(path: str | Path, dev: str):
    import torch

    blob = torch.load(str(path), map_location=dev, weights_only=False)
    head = place_head(blob["dim_in"], blob["dim"])
    head.load_state_dict(blob["state"])
    return head.to(dev).eval(), blob


def train(
    level_path: str | Path,
    places: np.ndarray,
    game,
    out: str | Path,
    options: TrainOptions | None = None,
    *,
    real: list[dict] | None = None,
    vehicle_places: np.ndarray | None = None,
    on_progress: Callable[[str], None] = print,
) -> Path:
    """
    Train a head for one level. `places`: floor points (level units) to take
    the players' training views from, `vehicle_places` the vehicles' (the
    same when not given); `real`: pseudo-labelled frames, each
    {"rgb": uint8 RGB, "mask": bool, "position", "yaw", "pitch", "hfov", "view"}.
    """
    import torch

    from .camera import Pose
    from .augment import game_look
    from .features import GlobalDescriptor
    from .level import load
    from .render import Light, Renderer

    options = options or TrainOptions()
    rng = np.random.default_rng(options.seed)
    torch.manual_seed(options.seed)
    level = load(level_path)
    unit = level.unit_metres
    from .features import GLOBAL_SIZE

    gh, gw = GLOBAL_SIZE
    renderer = Renderer(level, gw, gh)
    describe = GlobalDescriptor()
    dev = describe.dev
    dim_in = describe.dim // 2
    head = place_head(dim_in, options.dim).to(dev)
    opt = torch.optim.AdamW(head.parameters(), lr=options.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, options.steps)
    sun = level.extras.get("sun")
    eyes = [(e / unit, False) for e in game.eye_heights] + ([(game.vehicle_camera / unit, True)] if game.vehicle_camera else [])
    cars = vehicle_places if vehicle_places is not None and len(vehicle_places) else places
    jit = options.jitter_m / unit
    started = time.monotonic()

    def light() -> Light:
        if sun is not None and rng.random() < 0.5:
            s = tuple(float(v) for v in sun)
        else:
            el, az = math.radians(rng.uniform(20, 70)), rng.uniform(0, 2 * math.pi)
            s = (math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az))
        return Light(sun=s, ambient=float(rng.uniform(0.2, 0.45)), diffuse=float(rng.uniform(0.5, 0.95)), sky=float(rng.uniform(0.05, 0.3)), shadows=bool(rng.random() < 0.5))

    def view(p: np.ndarray, yaw: float, pitch: float, eye: float, vehicle: bool) -> tuple[np.ndarray, np.ndarray]:
        hfov = (game.vehicle_hfov if vehicle and game.vehicle_hfov else game.hfov) + rng.uniform(-options.fov_jitter, options.fov_jitter)
        d = rng.normal(0, jit / 2, 3)
        d[1] = 0.0
        pose = Pose(p + d + np.array([0.0, eye, 0.0]), yaw + rng.uniform(-options.jitter_yaw, options.jitter_yaw), pitch + rng.uniform(-5, 5))
        r = renderer.render(pose, hfov, light())
        rgb = game_look(r.color, r.depth, rng, unit_metres=unit, vehicle=vehicle, destructible=r.destructible)
        return rgb, game.mask(rgb.shape[1], rgb.shape[0], "vehicle" if vehicle else "foot")

    def tokens(pictures: list[np.ndarray], masks: list[np.ndarray]):
        return describe.tokens(pictures, masks)

    log = []
    for step in range(options.steps):
        n_real = int(round(options.batch * options.real_share)) if real else 0
        a_img, a_mask, b_img, b_mask, where = [], [], [], [], []
        for _ in range(options.batch - n_real):
            eye, vehicle = eyes[rng.integers(len(eyes))]
            pool = cars if vehicle else places
            p = pool[rng.integers(len(pool))]
            yaw, pitch = float(rng.uniform(-180, 180)), float(rng.uniform(-15, 10))
            for imgs, msks in ((a_img, a_mask), (b_img, b_mask)):
                rgb, m = view(p, yaw, pitch, eye, vehicle)
                imgs.append(rgb)
                msks.append(m)
            where.append((p[0], p[2], yaw))
        for _ in range(n_real):
            f = real[rng.integers(len(real))]
            a_img.append(f["rgb"])
            a_mask.append(f["mask"])
            vehicle = f.get("view") == "vehicle"
            pose = Pose(np.asarray(f["position"], float), float(f["yaw"]), float(f["pitch"]))
            r = renderer.render(pose, float(f["hfov"]), light())
            b_img.append(game_look(r.color, r.depth, rng, unit_metres=unit, vehicle=vehicle, destructible=r.destructible))
            b_mask.append(game.mask(r.color.shape[1], r.color.shape[0], "vehicle" if vehicle else "foot"))
            where.append((f["position"][0], f["position"][2], float(f["yaw"])))
        ta, ka = tokens(a_img, a_mask)
        tb, kb = tokens(b_img, b_mask)
        za, zb = head(ta, ka), head(tb, kb)
        z = torch.cat([za, zb])
        sim = z @ z.T * head.logit_scale.exp().clamp(max=100)
        n = len(za)
        wh = np.array(where)
        dist = np.hypot(wh[:, None, 0] - wh[None, :, 0], wh[:, None, 1] - wh[None, :, 1]) * unit
        turn = np.abs((wh[:, None, 2] - wh[None, :, 2] + 180) % 360 - 180)
        near = torch.from_numpy(np.tile((dist < options.near_m) & (turn < options.near_yaw), (2, 2))).to(dev)
        eye_mask = torch.eye(2 * n, dtype=torch.bool, device=dev)
        target = torch.cat([torch.arange(n, 2 * n), torch.arange(0, n)]).to(dev)
        # Leave out self and near-duplicates, but never the positive.
        drop = (near | eye_mask) & ~torch.nn.functional.one_hot(target, 2 * n).bool()
        sim = sim.masked_fill(drop, float("-inf"))
        loss = torch.nn.functional.cross_entropy(sim, target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        with torch.no_grad():
            acc = float((sim.argmax(1) == target).float().mean())
        log.append((float(loss), acc))
        if step % 20 == 0 or step == options.steps - 1:
            l = np.mean([x[0] for x in log[-20:]])
            a = np.mean([x[1] for x in log[-20:]])
            on_progress(f"step {step + 1}/{options.steps}  loss {l:.3f}  pair accuracy {a:.2f}  {time.monotonic() - started:.0f} s")
    renderer.release()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state": head.state_dict(),
            "dim_in": dim_in,
            "dim": options.dim,
            "backbone": describe.model_name,
            "level": str(Path(level_path).resolve()),
            "options": asdict(options),
            "places": int(len(places)),
            "real_pairs": len(real or []),
            "seconds": round(time.monotonic() - started, 1),
        },
        str(out),
    )
    out.with_suffix(".json").write_text(json.dumps({"loss": log[-1][0], "accuracy": log[-1][1], "steps": options.steps}, indent=1), encoding="utf-8")
    return out
