"""
Make a render look more like a frame of the game, for training.

A render of the level is clean: one light, no haze, no smoke, no one in the
way, no HUD, no compression. A frame of the game is none of that. The
per-map model (train.py) only learns to see past the difference if it is
shown it, so every training render passes through a random mix of:

- **colour**: gamma, white balance, saturation, contrast, brightness - the
  game's grading and exposure;
- **haze**: the far away fades towards a sky colour, by the render's own
  depth, as the game's fog and aerial perspective do;
- **bloom** round bright areas, and a **vignette**;
- **smoke**: soft grey or black clouds, see-through or not;
- **occluders**: dark upright shapes the size of players, and in the
  vehicle views the player's own vehicle filling the lower middle;
- **destruction**: what the game can destroy (the render's `destructible`
  pixels, when the level tags them) replaced, part by part, by rubble-coloured
  noise or by what is behind it; and **dust** hanging low over the ground;
- **motion blur**, **sensor noise** and **JPEG** artefacts.

The HUD is not drawn: at query time its boxes are masked out of the frame,
and the training renders are masked the same way (train.py).
"""

from __future__ import annotations

import numpy as np


def game_look(
    rgb: np.ndarray,
    depth: np.ndarray,
    rng: np.random.Generator,
    *,
    unit_metres: float = 1.0,
    vehicle: bool = False,
    destructible: np.ndarray | None = None,
) -> np.ndarray:
    """A randomly game-like version of an RGB uint8 render with its depth (level units, 0 = sky)."""
    import cv2

    h, w = rgb.shape[:2]
    rgb = destroyed(rgb, destructible, rng) if destructible is not None else rgb
    img = rgb.astype(np.float32) / 255.0
    # Haze by distance.
    if rng.random() < 0.7:
        reach = rng.uniform(250.0, 2500.0) / unit_metres
        hit = depth > 0
        a = np.where(hit, 1.0 - np.exp(-depth / reach), 0.0)[..., None] * rng.uniform(0.4, 0.9)
        haze = np.array([rng.uniform(0.7, 0.9), rng.uniform(0.72, 0.9), rng.uniform(0.75, 0.95)], np.float32)
        img = img * (1 - a) + haze * a
    # Grade.
    img = np.clip(img, 0, 1) ** rng.uniform(0.7, 1.4)
    img = img * rng.uniform(0.85, 1.15, 3).astype(np.float32)
    gray = img.mean(axis=2, keepdims=True)
    img = gray + (img - gray) * rng.uniform(0.45, 1.3)
    img = (img - 0.5) * rng.uniform(0.75, 1.35) + 0.5 + rng.uniform(-0.1, 0.1)
    img = np.clip(img, 0, 1)
    # Bloom.
    if rng.random() < 0.5:
        bright = np.clip(img - rng.uniform(0.6, 0.85), 0, 1)
        img = np.clip(img + cv2.GaussianBlur(bright, (0, 0), rng.uniform(5, 20)) * rng.uniform(0.3, 1.2), 0, 1)
    # Vignette.
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / w, (yy - h / 2) / h)
    img *= (1 - rng.uniform(0.0, 0.45) * r[..., None] ** 2)
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    # Smoke.
    for _ in range(rng.integers(0, 4)):
        layer = np.zeros((h, w), np.float32)
        cx, cy = int(rng.integers(0, w)), int(rng.integers(0, h))
        cv2.ellipse(layer, (cx, cy), (int(rng.integers(w // 12, w // 2)), int(rng.integers(h // 12, h // 2))), float(rng.uniform(0, 180)), 0, 360, 1.0, -1)
        layer = cv2.GaussianBlur(layer, (0, 0), rng.uniform(8, 30)) * rng.uniform(0.3, 0.95)
        tone = rng.uniform(20, 200)
        out = (out * (1 - layer[..., None]) + tone * layer[..., None]).astype(np.uint8)
    # Dust low over the ground, as a battle raises it.
    if rng.random() < 0.4:
        y0 = int(h * rng.uniform(0.45, 0.75))
        ramp = np.clip((np.arange(h, dtype=np.float32) - y0) / max(1, h - y0), 0, 1)[:, None]
        layer = cv2.GaussianBlur((rng.random((h // 8 + 1, w // 8 + 1)) > 0.5).astype(np.float32), (0, 0), 3)
        layer = cv2.resize(layer, (w, h)) * ramp * rng.uniform(0.2, 0.7)
        tone = np.array([rng.uniform(140, 200), rng.uniform(125, 180), rng.uniform(100, 160)], np.float32)
        out = (out * (1 - layer[..., None]) + tone * layer[..., None]).astype(np.uint8)
    # People in the way.
    for _ in range(rng.integers(0, 4)):
        cx, cy = int(rng.integers(0, w)), int(rng.integers(h // 3, h))
        ax, ay = int(rng.integers(max(2, w // 80), w // 18)), int(rng.integers(h // 25, h // 4))
        c = tuple(int(v) for v in rng.integers(20, 110, 3))
        cv2.ellipse(out, (cx, cy), (ax, ay), 0, 0, 360, c, -1)
    # The player's own vehicle, in a vehicle's third-person view.
    if vehicle and rng.random() < 0.8:
        c = tuple(int(v) for v in rng.integers(30, 120, 3))
        top = int(h * rng.uniform(0.45, 0.65))
        pts = np.array([[int(w * 0.25), h], [int(w * 0.33), top], [int(w * 0.67), top], [int(w * 0.75), h]], np.int32)
        cv2.fillPoly(out, [pts], c)
    # Motion blur.
    if rng.random() < 0.4:
        n = int(rng.integers(3, 11))
        k = np.zeros((n, n), np.float32)
        k[n // 2, :] = 1.0 / n
        rot = cv2.getRotationMatrix2D((n / 2 - 0.5, n / 2 - 0.5), float(rng.uniform(0, 180)), 1.0)
        k = cv2.warpAffine(k, rot, (n, n))
        out = cv2.filter2D(out, -1, k / max(k.sum(), 1e-6))
    # Noise and compression.
    out = np.clip(out.astype(np.float32) + rng.normal(0, rng.uniform(0, 6), out.shape), 0, 255).astype(np.uint8)
    ok, enc = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(35, 92))])
    return cv2.imdecode(enc, cv2.IMREAD_UNCHANGED) if ok else out


def destroyed(rgb: np.ndarray, destructible: np.ndarray, rng: np.random.Generator, *, share: float = 0.5) -> np.ndarray:
    """
    The render with part of what the game can destroy gone: blobs of the
    destructible pixels, about `share` of them, filled with rubble-coloured
    noise (greys and browns, coarse) - a wall shot to pieces, a house fallen
    in. The rest stays as it is.
    """
    import cv2

    if not destructible.any():
        return rgb
    h, w = rgb.shape[:2]
    blobs = cv2.resize((rng.random((max(2, h // 40), max(2, w // 40))) < share).astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
    gone = destructible & (blobs > 0)
    if not gone.any():
        return rgb
    base = np.array([rng.uniform(90, 160), rng.uniform(80, 140), rng.uniform(65, 120)], np.float32)
    grain = cv2.resize(rng.normal(0, 28, (h // 6 + 1, w // 6 + 1)).astype(np.float32), (w, h))
    rubble = np.clip(base + grain[..., None] + rng.normal(0, 10, (h, w, 1)), 0, 255).astype(np.uint8)
    out = rgb.copy()
    out[gone] = rubble[gone]
    return out
