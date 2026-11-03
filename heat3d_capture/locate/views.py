"""
What kind of view a frame is, from the HUD: the player on foot, a vehicle's
third-person camera, or a zoomed view (a scope, a gunner's sight).

It decides how the frame is solved. On foot: the infantry field of view and
eye heights. In a vehicle: the vehicle field of view, the vehicle itself
masked (it fills the lower middle of the picture and is not part of the
level), and a camera allowed to ride metres above the ground. Zoomed: not
solved at all - the zoom is not known, a scope shows a sliver of the level
that the database's wide views do not resemble, and a guess would be a wrong
position along the view - the row says so instead.

The cues are drawn by the game, so they are per game. Battlefield 6:

- **zoomed**: a sight blacks out the screen's edges - one of them black
  (mean below 10), both dark (below 30) - round a bright picture (the
  middle's mean above 90). A frame merely dark at its edges (a wall in
  shadow) has neither edge that black; tank gunners' and drivers' own views
  count as zoomed too;
- **screen**: dark edges round a dark middle is no view of the level but the
  deploy map, a menu or the scoreboard; not located;
- **vehicle**: the seat diagram at the bottom centre comes with its key
  prompts (`C CAMERA`, `E EXIT`): two light key caps with a dark letter, at
  fixed places;
- **on foot**: neither.

Boxes are on the 1920x1080 reference screen, like the HUD masks.
"""

from __future__ import annotations

import numpy as np

FOOT = "foot"
VEHICLE = "vehicle"
ZOOMED = "zoomed"
#: Not a view of the level at all: the deploy map, a menu, the scoreboard.
SCREEN = "screen"

#: Battlefield 6: the two key caps beside the vehicle seat diagram (x, y, w, h), reference pixels.
_BF6_KEYS = ((1045, 932, 22, 20), (1045, 978, 22, 22))
#: The screen edges a sight blacks out.
_BF6_EDGES = ((0, 400, 60, 280), (1860, 400, 60, 280))
#: The middle of the screen, for telling a sight (bright picture) from a menu (dark).
_BF6_MIDDLE = (700, 300, 520, 480)


def _box(rgb: np.ndarray, box: tuple[int, int, int, int], grow: int = 0) -> np.ndarray:
    h, w = rgb.shape[:2]
    sx, sy = w / 1920.0, h / 1080.0
    x, y, bw, bh = box
    x0, y0 = max(0, int((x - grow) * sx)), max(0, int((y - grow) * sy))
    x1, y1 = min(w, int((x + bw + grow) * sx)), min(h, int((y + bh + grow) * sy))
    return rgb[y0:y1, x0:x1]


def _key_cap(patch: np.ndarray, size: tuple[float, float]) -> bool:
    """A light square about `size` (w, h pixels) with a dark letter in it, somewhere in the patch."""
    import cv2

    if patch.size == 0:
        return False
    light = (patch.min(axis=2) > 150).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(light, connectivity=4)
    want_w, want_h = size
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if not (0.7 * want_w <= w <= 1.4 * want_w and 0.7 * want_h <= h <= 1.4 * want_h):
            continue
        cap = patch[y : y + h, x : x + w]
        dark = (cap.max(axis=2) < 110).mean()
        # Light all round, a letter's worth of dark inside.
        if area >= 0.45 * w * h and 0.04 < dark < 0.45:
            return True
    return False


def bf6(rgb: np.ndarray) -> str:
    """The view of a Battlefield 6 frame (RGB, any 16:9 size)."""
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    edges = [float(_box(gray[:, :, None], b).mean()) for b in _BF6_EDGES]
    if max(edges) < 30.0:
        middle = float(_box(gray[:, :, None], _BF6_MIDDLE).mean())
        if middle < 90.0:
            return SCREEN
        if min(edges) < 10.0:
            return ZOOMED
    scale = w / 1920.0
    if all(_key_cap(_box(rgb, b, grow=6), (b[2] * scale, b[3] * scale)) for b in _BF6_KEYS):
        return VEHICLE
    return FOOT


DETECTORS = {"bf6": bf6}


def detector(name: str | None):
    """The game's view detector, or None: every frame is then taken as on foot."""
    return DETECTORS.get(name or "")
