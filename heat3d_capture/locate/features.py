"""
What a picture is described by: one vector for the whole of it, to find the
renders that show the same place, and points with descriptors, to match it
to one of them pixel for pixel.

- **Global**: DINOv2 (Meta, Apache-2.0, `facebook/dinov2-base` from the
  Hugging Face hub), its patch tokens pooled by generalised mean and joined
  with the class token. Not trained for places; it does not need to be,
  because it is only asked to put the right renders among the first few
  dozen, and the matching below decides.
- **Local**: ALIKED keypoints and descriptors (BSD-3-Clause) matched with
  LightGlue (Apache-2.0), both through kornia (Apache-2.0); the weights are
  fetched by kornia on first use. SuperPoint, the usual partner of
  LightGlue, is deliberately not used: its weights are non-commercial.

Every picture can carry a mask of the pixels that are not the level - the
HUD, the crosshair, the player's own weapon - and nothing is described or
matched there (see `profiles.py`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

GLOBAL_MODEL = "facebook/dinov2-base"
#: DINOv2 works on 14-pixel patches: 16 x 28 of them, a 16:9 picture.
GLOBAL_SIZE = (224, 392)
_MEAN = np.array([0.485, 0.456, 0.406])
_STD = np.array([0.229, 0.224, 0.225])


def device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def normalise(rgb: np.ndarray, mode: str) -> np.ndarray:
    """
    Take some of the light out of a picture before it is described.

    `clahe` equalises the brightness locally (on L of Lab), which narrows the
    gap between a render's flat light and a frame's shadows and exposure;
    `none` leaves it.
    """
    if mode == "none":
        return rgb
    import cv2

    if mode == "clahe":
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    if mode == "gray":
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        g = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(g)
        return np.repeat(g[:, :, None], 3, axis=2)
    raise ValueError(f"unknown normalisation {mode!r}")


class GlobalDescriptor:
    """
    DINOv2's tokens pooled into one vector; with `head` (a per-map head from
    train.py) pooled by that head instead.
    """

    def __init__(self, model: str = GLOBAL_MODEL, dev: str | None = None, head: str | None = None):
        import torch
        from transformers import AutoModel

        self.dev = dev or device()
        self.model_name = model
        self.model = AutoModel.from_pretrained(model).to(self.dev).eval()
        if self.dev == "cuda":
            self.model = self.model.half()
        self.torch = torch
        self.head = None
        self.head_dim = None
        if head:
            from .train import load_head

            self.head, blob = load_head(head, self.dev)
            self.head_dim = int(blob["dim"])

    @property
    def dim(self) -> int:
        return self.head_dim or 2 * int(self.model.config.hidden_size)

    def tokens(self, pictures: list[np.ndarray], masks: list[np.ndarray | None] | None = None):
        """The backbone's tokens (n, 1 + patches, d) as float32, and which patches show the level (n, patches)."""
        import cv2

        torch = self.torch
        h, w = GLOBAL_SIZE
        masks = masks or [None] * len(pictures)
        batch, keep = [], []
        for rgb, mask in zip(pictures, masks):
            small = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
            if mask is not None:
                m = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
                small[~m] = small[m].mean(axis=0) if m.any() else 0.5
                patches = cv2.resize(m.astype(np.float32), (w // 14, h // 14), interpolation=cv2.INTER_AREA) > 0.5
            else:
                patches = np.ones((h // 14, w // 14), bool)
            batch.append((small - _MEAN) / _STD)
            keep.append(patches.ravel())
        x = torch.from_numpy(np.stack(batch).transpose(0, 3, 1, 2).astype(np.float32)).to(self.dev)
        if self.dev == "cuda":
            x = x.half()
        k = torch.from_numpy(np.stack(keep)).to(self.dev)
        with torch.no_grad():
            tokens = self.model(pixel_values=x).last_hidden_state.float()
        return tokens, k

    def pooled(self, tokens, keep):
        """The plain descriptor from tokens: class token and GeM of the patches, joined."""
        torch = self.torch
        cls = torch.nn.functional.normalize(tokens[:, 0], dim=1)
        patch = tokens[:, 1:].clamp(min=1e-6)
        weight = keep.float().unsqueeze(2)
        gem = ((patch**3 * weight).sum(1) / weight.sum(1).clamp(min=1)) ** (1 / 3)
        gem = torch.nn.functional.normalize(gem, dim=1)
        return torch.nn.functional.normalize(torch.cat([cls, gem], dim=1), dim=1)

    def __call__(self, pictures: list[np.ndarray], masks: list[np.ndarray | None] | None = None) -> np.ndarray:
        """(n, dim) float32, unit length: RGB uint8 pictures, masks True where the level shows."""
        tokens, keep = self.tokens(pictures, masks)
        with self.torch.no_grad():
            out = self.head(tokens, keep) if self.head is not None else self.pooled(tokens, keep)
        return out.cpu().numpy().astype(np.float32)


@dataclass
class Keypoints:
    xy: np.ndarray  # (n, 2) pixels
    descriptors: "object"  # torch tensor (n, d) on the device
    size: tuple[int, int]  # (w, h)


class LocalMatcher:
    """
    ALIKED and LightGlue. `max_keypoints` are kept of those on the level: the detector is asked for
    `detected` first, because a frame's strongest keypoints are mostly on what is masked afterwards
    (the HUD, the player's vehicle) and would otherwise use up the budget. `threshold` is low for
    the same reason as the budget is high: a frame of the game and a render of the level share few
    strong corners, and the flat, sunlit parts of a frame have only weak ones.
    """

    def __init__(self, max_keypoints: int = 2048, dev: str | None = None, threshold: float = 0.1, detected: int | None = None):
        import kornia.feature as KF
        import torch

        self.dev = dev or device()
        self.torch = torch
        self.keep = max_keypoints
        self.detector = KF.ALIKED.from_pretrained(
            "aliked-n16", max_num_keypoints=detected or max_keypoints, detection_threshold=threshold, device=torch.device(self.dev)
        ).eval()
        self.matcher = KF.LightGlue("aliked").to(self.dev).eval()

    def detect(self, rgb: np.ndarray, valid: np.ndarray | None = None) -> Keypoints:
        """Keypoints of an RGB uint8 picture, only where `valid` (when given) is True, the strongest `max_keypoints` of those."""
        torch = self.torch
        h, w = rgb.shape[:2]
        x = torch.from_numpy(rgb).to(self.dev).permute(2, 0, 1)[None].float() / 255.0
        with torch.no_grad():
            f = self.detector(x)[0]
        xy = f.keypoints.cpu().numpy()
        d = f.descriptors
        score = f.keypoint_scores.cpu().numpy()
        if valid is not None and len(xy):
            ix = np.clip(np.round(xy).astype(int), 0, [w - 1, h - 1])
            ok = valid[ix[:, 1], ix[:, 0]]
            xy, score = xy[ok], score[ok]
            d = d[torch.from_numpy(ok).to(d.device)]
        if len(xy) > self.keep:
            top = np.argsort(-score)[: self.keep]
            xy = xy[top]
            d = d[torch.from_numpy(top).to(d.device)]
        return Keypoints(xy, d, (w, h))

    def match(self, a: Keypoints, b: Keypoints) -> tuple[np.ndarray, np.ndarray]:
        """Index pairs (m, 2) into a and b, and their scores."""
        torch = self.torch
        if len(a.xy) < 4 or len(b.xy) < 4:
            return np.zeros((0, 2), int), np.zeros(0)

        def side(k: Keypoints) -> dict:
            return {
                "keypoints": torch.from_numpy(k.xy).float().to(self.dev)[None],
                "descriptors": k.descriptors[None].float(),
                "image_size": torch.tensor([k.size], dtype=torch.float32, device=self.dev),
            }

        with torch.no_grad():
            out = self.matcher({"image0": side(a), "image1": side(b)})
        return out["matches"][0].cpu().numpy(), out["scores"][0].float().cpu().numpy()
