"""
The level's reference map, and the minimap read against it.

The minimap tells where the player is in every frame, but only on its own
picture of the map. The HUD reader stitches those minimaps into a mosaic and
the mosaic is not flat: its scale drifts with the zoom each minimap was read
at, a place seen twice can be drawn twice, and one clip's mosaic is not
another's. A similarity fitted on a few picture fixes then holds only near
them - tens of metres off elsewhere.

So the minimap is placed on the level by the level itself, in two steps:

1. **The reference map.** The deploy screen draws the whole map, north up,
   flat, at one scale - one picture, not stitched. The level seen from
   straight above (`topdown`) shows the same things standing up from the
   ground: tanks, buildings, walls. Both become blob pictures (on the level,
   height above the ground round it; on the map, what is drawn lighter than
   the ground round it), and the map is placed on the level by normalised
   cross-correlation over scale and a small turn, then refined by matching
   tiles of it one by one (`calibrate`). The result is one similarity, map
   pixel -> level x, z, and the map resampled onto the level's own frame
   (`RefMap`).
2. **The minimap, frame by frame.** Each sampled minimap - the HUD reader's
   crop and overlay mask - is matched (SIFT) to the reference map round where
   the player was last, or anywhere when nowhere is known, and a similarity
   (turn, zoom, shift) is fitted (`register_minimaps`). The player's point
   carried through it is the position on the level; the minimap's up (its
   view cone) is the heading; its scale is how far the minimap was zoomed,
   measured rather than assumed. Nothing is stitched, so nothing drifts.

The table it writes reads like the HUD reader's (x east, y north, here in the
level's metres with y = -z), with an anchor beside it that is the identity,
so `locate frames --minimap ... --minimap-anchor ...` takes it unchanged.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

#: Metres: the ground round a point, for "standing up from the ground" (height on the level, brightness on the map).
GROUND_RADIUS = 15.0
#: Metres: smaller things (the map's roads and grid lines, the level's clutter) are opened away.
BLOB_SIZE = 3.0


# --------------------------------------------------------------------------- the level from above


@dataclass
class TopDown:
    """The level seen from straight above: colour and height (level units, NaN where nothing)."""

    color: np.ndarray
    height: np.ndarray
    x0: float
    z0: float
    #: Level units a pixel; pixel (u, v) is level (x0 + u * mpp, z0 + v * mpp).
    mpp: float

    def save(self, prefix: Path) -> None:
        import cv2

        cv2.imwrite(str(prefix) + ".color.png", self.color)
        np.save(str(prefix) + ".height.npy", self.height)
        Path(str(prefix) + ".json").write_text(json.dumps({"x0": self.x0, "z0": self.z0, "mpp": self.mpp, "width": self.color.shape[1], "height": self.color.shape[0]}))

    @staticmethod
    def load(prefix: Path) -> "TopDown":
        import cv2

        d = json.loads(Path(str(prefix) + ".json").read_text())
        return TopDown(cv2.imread(str(prefix) + ".color.png"), np.load(str(prefix) + ".height.npy"), d["x0"], d["z0"], d["mpp"])


def topdown(level, mpp: float = 0.656, bounds: tuple[float, float, float, float] | None = None, tile: int = 512) -> TopDown:
    """
    Render the level from straight above, in tiles seen from 1.5 km over their middles through a
    narrow lens (tall things lean by a few metres at most). `mpp` in metres; `bounds` (x0, z0,
    x1, z1) in level units, default the level's.
    """
    from .camera import Pose
    from .render import Light, Renderer

    unit = level.unit_metres
    step = mpp / unit
    lo, hi = level.bounds
    x0, z0, x1, z1 = bounds if bounds is not None else (lo[0], lo[2], hi[0], hi[2])
    W, H = int(math.ceil((x1 - x0) / step)), int(math.ceil((z1 - z0) / step))
    up = 1500.0 / unit
    # Levels carry far-off backdrop kilometres high; what matters is below 800 m.
    ceil = min(float(hi[1]), 800.0 / unit)
    top = ceil + up
    r = Renderer(level, tile, tile, near=up * 0.5, far=up + ceil - float(lo[1]) + 100.0 / unit)
    color = np.zeros((H, W, 3), np.uint8)
    height = np.full((H, W), np.nan, np.float32)
    hfov = math.degrees(2 * math.atan((tile * step / 2) / (top - 150.0 / unit)))
    light = Light(sun=(-0.4, 0.8, 0.3), ambient=0.45, diffuse=0.6)
    try:
        for v0 in range(0, H, tile):
            for u0 in range(0, W, tile):
                cx, cz = x0 + (u0 + tile / 2) * step, z0 + (v0 + tile / 2) * step
                # Yaw 90 looking down: image right is +x, image down is +z.
                img = r.render(Pose(np.array([cx, top, cz]), 90.0, -89.99), hfov, light)
                h = np.where(img.depth > 0, top - img.depth, np.nan)
                hh, ww = min(tile, H - v0), min(tile, W - u0)
                color[v0 : v0 + hh, u0 : u0 + ww] = img.color[:hh, :ww, ::-1]
                height[v0 : v0 + hh, u0 : u0 + ww] = h[:hh, :ww]
    finally:
        r.release()
    return TopDown(color, height, float(x0), float(z0), float(step))


# --------------------------------------------------------------------------- the reference map


def _open(img: np.ndarray, size_px: float) -> np.ndarray:
    import cv2

    k = int(size_px) | 1
    return cv2.morphologyEx(img.astype(np.float32), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))


def level_blobs(top: TopDown, unit_metres: float = 1.0) -> np.ndarray:
    """What stands up from the ground round it, 0..1 (8 m and more is 1)."""
    import cv2

    h = np.nan_to_num(top.height, nan=float(np.nanmin(top.height)))
    m = top.mpp * unit_metres
    rel = np.clip(h - cv2.GaussianBlur(h, (0, 0), GROUND_RADIUS / m), 0, 8.0 / unit_metres) / (8.0 / unit_metres)
    return _open(rel, BLOB_SIZE / m)


def map_overlays(image: np.ndarray) -> np.ndarray:
    """True where the map is the map: not a coloured marker, team area border, label or the dark outside."""
    import cv2

    g = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    chroma = image.max(2).astype(np.int16) - image.min(2).astype(np.int16)
    over = cv2.dilate(((chroma > 60) | (g > 230)).astype(np.uint8), np.ones((15, 15), np.uint8))
    return (over == 0) & (g > 10)


def map_blobs(image: np.ndarray, valid: np.ndarray, metres: float) -> np.ndarray:
    """The map's raised things at `metres` a map pixel: drawn lighter than the ground round them."""
    import cv2

    g = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    bg = cv2.GaussianBlur(g, (0, 0), GROUND_RADIUS / metres)
    return _open(np.clip((g - bg) / 0.12, 0, 1) * valid, BLOB_SIZE / metres)


def _turned(scale: float, turn: float) -> np.ndarray:
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    return scale * np.array([[c, -s], [s, c]])


@dataclass
class Calibration:
    """Map pixel -> level (x, z) in level units: `matrix` (2x3), and how well the map's tiles agreed with it."""

    matrix: np.ndarray
    tiles: int
    inliers: int
    median: float
    p90: float
    coarse: dict = field(default_factory=dict)

    def apply(self, uv: np.ndarray) -> np.ndarray:
        return np.atleast_2d(uv) @ self.matrix[:, :2].T + self.matrix[:, 2]


def calibrate(
    top: TopDown,
    image: np.ndarray,
    *,
    unit_metres: float = 1.0,
    scales: Iterable[float] | None = None,
    turns: Iterable[float] = (-3, -2, -1, 0, 1, 2, 3),
    coarse: float = 2.0,
    tile: float = 90.0,
    search: float = 25.0,
) -> Calibration | None:
    """
    Place a north-up map picture (the deploy screen's) on the level. `scales`: metres a map pixel
    to try (default 0.40-0.61); `coarse`, `tile`, `search` in metres. None when too few tiles agree.
    """
    import cv2

    m = top.mpp * unit_metres  # metres a level pixel
    lb = level_blobs(top, unit_metres)
    valid = map_overlays(image).astype(np.float32)
    lc = cv2.resize(lb, None, fx=m / coarse, fy=m / coarse, interpolation=cv2.INTER_AREA)
    H0, W0 = image.shape[:2]
    best = None
    for sc in scales if scales is not None else np.arange(0.40, 0.615, 0.01):
        mb = map_blobs(image, valid, sc)
        for turn in turns:
            R = _turned(sc / coarse, turn)
            corners = np.array([[0, 0], [W0, 0], [0, H0], [W0, H0]], float) @ R.T
            off = -corners.min(0)
            size = tuple(int(v) for v in np.ceil(corners.max(0) - corners.min(0)) + 1)
            M = np.c_[R, off]
            t = cv2.warpAffine(mb, M, size, flags=cv2.INTER_AREA)
            tv = cv2.warpAffine(valid, M, size, flags=cv2.INTER_NEAREST)
            if t.shape[0] >= lc.shape[0] or t.shape[1] >= lc.shape[1]:
                continue
            r = np.nan_to_num(cv2.matchTemplate(lc, t, cv2.TM_CCORR_NORMED, mask=tv))
            _, p, _, loc = cv2.minMaxLoc(r)
            if best is None or p > best[0]:
                r2 = r.copy()
                cv2.circle(r2, loc, int(60 / coarse), 0, -1)
                best = (p, float(sc), float(turn), loc, float(r2.max()), off)
    if best is None:
        return None
    p, sc, turn, loc, second, off = best
    # Map pixel -> level units.
    per = 1.0 / unit_metres
    A0 = np.c_[_turned(sc * per, turn), np.array([top.x0, top.z0]) + (np.array(loc) - off) * coarse * per]

    # Fine: tiles of the map's blobs laid on the level's pixels by A0, each matched round its place.
    mb = map_blobs(image, valid, sc)
    to_px = np.array([[1 / top.mpp, 0, -top.x0 / top.mpp], [0, 1 / top.mpp, -top.z0 / top.mpp]])
    Mp = np.c_[to_px[:, :2] @ A0[:, :2], to_px[:, :2] @ A0[:, 2] + to_px[:, 2]]
    LH, LW = lb.shape
    wf = cv2.warpAffine(mb, Mp, (LW, LH))
    wv = cv2.warpAffine(valid, Mp, (LW, LH), flags=cv2.INTER_NEAREST)
    inv = cv2.invertAffineTransform(Mp)
    T, P = int(tile / m), int(search / m)
    src, dst = [], []
    for v0 in range(P, LH - T - P, T // 2):
        for u0 in range(P, LW - T - P, T // 2):
            tf, tv = wf[v0 : v0 + T, u0 : u0 + T], wv[v0 : v0 + T, u0 : u0 + T]
            if tv.mean() < 0.6 or tf.mean() < 0.01:
                continue
            r = cv2.matchTemplate(lb[v0 - P : v0 + T + P, u0 - P : u0 + T + P], tf, cv2.TM_CCOEFF_NORMED)
            _, pk, _, l = cv2.minMaxLoc(r)
            r2 = r.copy()
            cv2.circle(r2, l, int(6 / m), -1, -1)
            if pk < 0.35 or pk - r2.max() < 0.05:
                continue  # a repeated pattern or nothing to match: no say
            cu, cv_ = u0 + T / 2, v0 + T / 2
            src.append(inv @ np.array([cu, cv_, 1.0]))
            dst.append((top.x0 + (cu + l[0] - P) * top.mpp, top.z0 + (cv_ + l[1] - P) * top.mpp))
    coarse_report = {"metres_per_map_pixel": sc, "turn": turn, "score": float(p), "next_place": second}
    if len(src) < 6:
        return None
    src, dst = np.array(src, np.float64), np.array(dst, np.float64)
    S, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=5.0 * per, maxIters=20000)
    if S is None:
        return None
    inl = inl.ravel().astype(bool)
    e = np.linalg.norm(src @ S[:, :2].T + S[:, 2] - dst, axis=1)
    tiles_report = {"median": float(np.median(e[inl])), "p90": float(np.percentile(e[inl], 90))}
    # Last, the whole map at once round the tiles' answer: a few dozen tiles leave the scale loose
    # by a percent (metres at the map's ends); all of the map's blobs together pin it.
    S, score = _refine_whole(lb, top, image, valid, S, unit_metres)
    coarse_report.update({"whole_map_score": score, "tiles": tiles_report})
    e = np.linalg.norm(src @ S[:, :2].T + S[:, 2] - dst, axis=1)
    inl = e < 5.0 * per
    return Calibration(S, len(src), int(inl.sum()), float(np.median(e[inl])), float(np.percentile(e[inl], 90)), coarse_report)


def _refine_whole(lb: np.ndarray, top: TopDown, image: np.ndarray, valid: np.ndarray, S: np.ndarray, unit_metres: float,
                  scale_span: float = 0.03, scale_step: float = 0.0025, turn_span: float = 0.6, turn_step: float = 0.2,
                  shift: float = 12.0) -> tuple[np.ndarray, float]:
    """The similarity map pixel -> level that best lays all the map's blobs on the level's (masked NCC)."""
    import cv2

    m = top.mpp
    H0, W0 = image.shape[:2]
    cen = np.array([W0 / 2, H0 / 2])
    lc0 = S[:, :2] @ cen + S[:, 2]
    s0 = math.hypot(S[0, 0], S[1, 0])  # level units a map pixel
    t0 = math.degrees(math.atan2(S[1, 0], S[0, 0]))
    P = int(shift / unit_metres / m)
    pad = int(max(W0, H0) * s0 / m) + P
    lbp = np.pad(lb, pad)
    best = (-1.0, S)
    for sc in np.arange(s0 * (1 - scale_span), s0 * (1 + scale_span) + 1e-9, s0 * scale_step):
        mb = map_blobs(image, valid, sc * unit_metres)
        for turn in np.arange(t0 - turn_span, t0 + turn_span + 1e-9, turn_step):
            R = _turned(sc / m, turn)
            corners = (np.array([[0, 0], [W0, 0], [0, H0], [W0, H0]], float) - cen) @ R.T
            off = -corners.min(0)
            size = tuple(int(v) for v in np.ceil(corners.max(0) - corners.min(0)) + 1)
            M = np.c_[R, off - R @ cen]
            t = cv2.warpAffine(mb, M, size, flags=cv2.INTER_AREA)
            tv = cv2.warpAffine(valid, M, size, flags=cv2.INTER_NEAREST)
            u0 = int((lc0[0] - top.x0) / m - off[0]) - P + pad
            v0 = int((lc0[1] - top.z0) / m - off[1]) - P + pad
            win = lbp[v0 : v0 + size[1] + 2 * P, u0 : u0 + size[0] + 2 * P]
            if win.shape[0] < size[1] or win.shape[1] < size[0]:
                continue
            r = np.nan_to_num(cv2.matchTemplate(win, t, cv2.TM_CCORR_NORMED, mask=tv))
            _, p, _, l = cv2.minMaxLoc(r)
            if p > best[0]:
                cx = top.x0 + (u0 - pad + l[0] + off[0]) * m
                cz = top.z0 + (v0 - pad + l[1] + off[1]) * m
                Rl = _turned(sc, turn)
                best = (float(p), np.c_[Rl, np.array([cx, cz]) - Rl @ cen])
    return best[1], best[0]


@dataclass
class RefMap:
    """The map laid on the level's frame: pixel (u, v) is level (x0 + u * mpp, z0 + v * mpp), level units."""

    image: np.ndarray
    valid: np.ndarray
    x0: float
    z0: float
    mpp: float
    calibration: dict = field(default_factory=dict)

    def to_level(self, uv: np.ndarray) -> np.ndarray:
        uv = np.atleast_2d(uv)
        return np.c_[self.x0 + uv[:, 0] * self.mpp, self.z0 + uv[:, 1] * self.mpp]

    def to_pixel(self, xz: np.ndarray) -> np.ndarray:
        xz = np.atleast_2d(xz)
        return np.c_[(xz[:, 0] - self.x0) / self.mpp, (xz[:, 1] - self.z0) / self.mpp]

    def save(self, prefix: Path) -> None:
        import cv2

        cv2.imwrite(str(prefix) + ".png", self.image)
        cv2.imwrite(str(prefix) + ".valid.png", self.valid.astype(np.uint8) * 255)
        Path(str(prefix) + ".json").write_text(json.dumps({
            "format": "heat3d-reference-map", "version": 1, "x0": self.x0, "z0": self.z0, "mpp": self.mpp,
            "width": int(self.image.shape[1]), "height": int(self.image.shape[0]), "calibration": self.calibration,
            "privacy": "made from the player's own recording of the game; keep it local",
        }, indent=1))

    @staticmethod
    def load(prefix: Path) -> "RefMap":
        import cv2

        d = json.loads(Path(str(prefix) + ".json").read_text())
        return RefMap(cv2.imread(str(prefix) + ".png"), cv2.imread(str(prefix) + ".valid.png", 0) > 0, d["x0"], d["z0"], d["mpp"], d.get("calibration", {}))


def reference_map(image: np.ndarray, cal: Calibration, mpp: float) -> RefMap:
    """The map picture resampled onto the level's frame at `mpp` level units a pixel."""
    import cv2

    S = cal.matrix
    H, W = image.shape[:2]
    corners = np.array([[0, 0], [W, 0], [0, H], [W, H]], float) @ S[:, :2].T + S[:, 2]
    (x0, z0), (x1, z1) = np.floor(corners.min(0)), np.ceil(corners.max(0))
    to_px = np.array([[1 / mpp, 0, -x0 / mpp], [0, 1 / mpp, -z0 / mpp]])
    M = np.c_[to_px[:, :2] @ S[:, :2], to_px[:, :2] @ S[:, 2] + to_px[:, 2]]
    size = (int((x1 - x0) / mpp), int((z1 - z0) / mpp))
    img = cv2.warpAffine(image, M, size, flags=cv2.INTER_AREA)
    valid = cv2.warpAffine(map_overlays(image).astype(np.uint8), M, size, flags=cv2.INTER_NEAREST) > 0
    report = {"matrix": S.tolist(), "tiles": cal.tiles, "inliers": cal.inliers, "median": cal.median, "p90": cal.p90, "coarse": cal.coarse}
    return RefMap(img, valid, float(x0), float(z0), float(mpp), report)


# --------------------------------------------------------------------------- the minimap, frame by frame


@dataclass
class MinimapFix:
    t: float
    #: Level x, z (level units).
    position: np.ndarray
    #: Degrees clockwise from north (level -z), where the minimap's view cone points.
    heading: float
    #: Metres of the level a minimap pixel (at the HUD profile's 1080p size) shows: the zoom.
    zoom: float
    inliers: int
    #: Median distance of the matched features from the fitted similarity, metres.
    residual: float
    #: "refmap": this minimap matched the reference map; "hud": the HUD reader's mosaic, moved by
    #: the offset the nearest reference-map fixes measured (`fill_from_hud`).
    source: str = "refmap"


class MinimapRegistrar:
    """
    Registers minimaps to a reference map. `work` is the minimap's size (pixels) as registered, the
    HUD reader's (its profile's minimap box at 1080p). `player` is the player's point on the
    minimap, `key` the key-hint square (hud/profiles.py), both as fractions.
    """

    def __init__(self, ref: RefMap, player: tuple[float, float], key: tuple[float, float, float, float] | None, *,
                 work: int = 296, unit_metres: float = 1.0, near: float = 160.0, min_inliers: int = 12):
        import cv2

        self.ref = ref
        self.player = player
        self.key = key
        self.work = work
        self.unit_metres = unit_metres
        self.near = near
        self.min_inliers = min_inliers
        self.clahe = cv2.createCLAHE(2.0, (8, 8))
        sift = cv2.SIFT_create(40000, contrastThreshold=0.015)
        grey = cv2.cvtColor(ref.image, cv2.COLOR_BGR2GRAY)
        k, self.desc = sift.detectAndCompute(self.clahe.apply(grey), cv2.erode(ref.valid.astype(np.uint8) * 255, np.ones((5, 5), np.uint8)))
        self.pts = np.float32([p.pt for p in k]).reshape(-1, 2)
        self.sift = cv2.SIFT_create(1500, contrastThreshold=0.02)
        self.matcher = cv2.BFMatcher(cv2.NORM_L2)

    def register(self, t: float, image: np.ndarray, near: np.ndarray | None = None) -> MinimapFix | None:
        """One minimap (BGR). `near`: level x, z the player is expected round (else the whole map)."""
        import cv2

        from ..hud.minimap import overlay_mask

        img = cv2.resize(image, (self.work, self.work), interpolation=cv2.INTER_AREA)
        mask = overlay_mask(img, self.player, self.key)
        k, d = self.sift.detectAndCompute(self.clahe.apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)), mask)
        if d is None or len(k) < self.min_inliers:
            return None
        if near is not None:
            c = self.ref.to_pixel(near)[0]
            sel = np.flatnonzero(np.hypot(self.pts[:, 0] - c[0], self.pts[:, 1] - c[1]) <= self.near / self.unit_metres / self.ref.mpp)
            if len(sel) < 2 * self.min_inliers:
                return None
        else:
            sel = np.arange(len(self.pts))
        good = [m[0] for m in self.matcher.knnMatch(d, self.desc[sel], k=2) if len(m) == 2 and m[0].distance < 0.85 * m[1].distance]
        if len(good) < self.min_inliers:
            return None
        src = np.float32([k[g.queryIdx].pt for g in good])
        dst = self.pts[sel[[g.trainIdx for g in good]]]
        A, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=4.0, maxIters=4000, confidence=0.995)
        if A is None:
            return None
        inl = inl.ravel().astype(bool)
        metres = self.ref.mpp * self.unit_metres
        zoom = math.hypot(A[0, 0], A[1, 0]) * metres
        if inl.sum() < self.min_inliers or not (0.25 < zoom < 1.6):
            return None
        e = np.linalg.norm(src[inl] @ A[:, :2].T + A[:, 2] - dst[inl], axis=1) * metres
        p = A @ np.array([self.player[0] * self.work, self.player[1] * self.work, 1.0])
        up = A[:, :2] @ np.array([0.0, -1.0])  # the view cone, always up on the minimap
        heading = (math.degrees(math.atan2(up[0], -up[1])) + 360.0) % 360.0
        return MinimapFix(t, self.ref.to_level(p)[0], heading, zoom, int(inl.sum()), float(np.median(e)))


def register_minimaps(
    frames: Iterable[tuple[float, np.ndarray]],
    reg: MinimapRegistrar,
    *,
    guess: Callable[[float], np.ndarray | None] | None = None,
    speed: float = 40.0,
    on_fix: Callable[[int, MinimapFix | None], None] | None = None,
) -> list[MinimapFix]:
    """
    Every (time, minimap) in order. Searched round the last fix while it is recent (4 s), else round
    `guess(t)` when given and then, if that finds nothing, over the whole map; a fix further from
    the last than `speed` m/s allows (plus 15 m) is a wrong match and dropped.
    """
    out: list[MinimapFix] = []
    last: MinimapFix | None = None
    unit = reg.unit_metres
    for n, (t, img) in enumerate(frames):
        near, recent = None, last is not None and t - last.t < 4.0
        if recent:
            near = last.position
        elif guess is not None:
            near = guess(t)
        fix = reg.register(t, img, near)
        if fix is None and near is not None and not recent:
            fix = reg.register(t, img, None)  # the guess may be wrong: the whole map
        if fix is not None and last is not None and t - last.t < 2.0:
            if np.linalg.norm(fix.position - last.position) * unit > speed * (t - last.t) + 15.0:
                fix = None
        if fix is not None:
            out.append(fix)
            last = fix
        if on_fix:
            on_fix(n, fix)
    return out


def fill_from_hud(fixes: list[MinimapFix], hud, anchor, step: float, *, within: float = 120.0, least: int = 3) -> list[MinimapFix]:
    """
    Where no minimap matched the reference map - the deploy screen draws nothing outside the play
    area, and a minimap that is mostly outside it has nothing to match - the HUD reader's own
    track (`hud`, read with `read_minimap`) placed by `anchor`, moved by the offset between the two
    readings that the reference-map fixes measured nearest in time (up to 10 each side, within
    `within` seconds, at least `least`; the nearer side's, or both weighted by nearness). The
    mosaic drifts with place, so the offset is only trusted near the fixes that measured it.
    """
    if not fixes or not len(hud.time):
        return []
    ft = np.array([f.t for f in fixes])
    off = []
    for f in fixes:
        h = hud.at(f.t, 0.6)
        off.append(np.full(2, np.nan) if h is None else f.position - anchor.to_level(h[0]))
    off = np.array(off)
    ok = np.isfinite(off[:, 0])
    ft, off = ft[ok], off[ok]
    if len(ft) < least:
        return []
    rot = anchor.similarity.rotation
    north, east = rot @ np.array([0.0, 1.0]), rot @ np.array([1.0, 0.0])
    out = []
    for t in np.arange(hud.time[0], hud.time[-1] + 1e-9, step):
        i = int(np.searchsorted(ft, t))
        if (i < len(ft) and ft[i] - t <= 0.6) or (i > 0 and t - ft[i - 1] <= 0.6):
            continue  # the reference map placed this one
        h = hud.at(t, 0.6)
        if h is None:
            continue
        sides = []
        for lo, hi in ((max(0, i - 10), i), (i, min(len(ft), i + 10))):
            sel = np.arange(lo, hi)
            sel = sel[np.abs(ft[sel] - t) <= within]
            if len(sel) >= least:
                sides.append((float(np.min(np.abs(ft[sel] - t))), np.median(off[sel], axis=0)))
        if not sides:
            continue
        w = np.array([1.0 / (d + 1.0) for d, _ in sides])
        shift = sum(wi * o for wi, (_, o) in zip(w, sides)) / w.sum()
        heading = float("nan")
        if np.isfinite(h[1]):
            d = math.sin(math.radians(h[1])) * east + math.cos(math.radians(h[1])) * north
            heading = (math.degrees(math.atan2(d[0], -d[1])) + 360.0) % 360.0
        out.append(MinimapFix(float(t), anchor.to_level(h[0]) + shift, heading, float("nan"), 0, float("nan"), "hud"))
    return out


def write_minimap_table(fixes: list[MinimapFix], path: Path, *, video: str, lives: Callable[[float], int] | None = None) -> tuple[Path, Path]:
    """
    The fixes as a minimap table (x east, y north: level x and -z, level units; heading; zoom) and
    its anchor (`<path>.anchor.json`, the identity with the mirror that turns y back into z).
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    fixes = sorted(fixes, key=lambda f: f.t)
    stem = Path(video).stem
    t = pa.table({
        "time": pa.array([round(f.t, 3) for f in fixes], pa.float64()),
        "event": pa.array(["position"] * len(fixes)).dictionary_encode(),
        "x": pa.array([round(float(f.position[0]), 3) for f in fixes], pa.float64()),
        "y": pa.array([round(-float(f.position[1]), 3) for f in fixes], pa.float64()),
        "heading": pa.array([round(f.heading, 1) for f in fixes], pa.float64()),
        "zoom": pa.array([round(f.zoom, 4) for f in fixes], pa.float64()),
        "inliers": pa.array([f.inliers for f in fixes], pa.int32()),
        "residual": pa.array([round(f.residual, 2) for f in fixes], pa.float64()),
        "source": pa.array([f.source for f in fixes]).dictionary_encode(),
        "session": pa.array([f"{stem}#{(lives(f.t) if lives else 0) + 1:02d}" for f in fixes]).dictionary_encode(),
    })
    meta = {b"heat3d": json.dumps({"version": 1, "kind": "heat3d-minimap", "frame": "level: x = level x, y = -level z",
                                   "zoom": "level metres a minimap pixel at 1080p"}).encode()}
    pq.write_table(t.replace_schema_metadata(meta), path)
    res = np.array([f.residual for f in fixes if f.source == "refmap"] or [0.0])
    anchor = Path(str(path).replace(".parquet", "") + ".anchor.json")
    anchor.write_text(json.dumps({
        "scale": 1.0, "rotation": [[1.0, 0.0], [0.0, -1.0]], "shift": [0.0, 0.0],
        # The registration's own scatter; the reference map's placement (its tiles) adds to it.
        "median": float(np.median(res)), "p90": float(np.percentile(res, 90)) + 2.0, "pairs": len(fixes),
        "source": "the minimap registered frame by frame to the level's reference map",
    }, indent=1))
    return path, anchor
