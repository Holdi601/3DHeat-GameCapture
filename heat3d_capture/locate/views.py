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
- **screen**: no HUD of a match - neither the minimap's key cap (`M`, bottom
  left, in every view while playing) nor a vehicle's health bar: a menu, the
  end of a round, the scoreboard, the desktop, the camera of a dead player;
  or dark edges round a dark middle, as on the deploy map. Not located. The
  cap is a keyboard prompt: footage played on a gamepad is not known to show one;
- **vehicle**: the seat diagram at the bottom centre has a thin bar under it,
  in the same place for every vehicle, on dark ground and light (a light
  grey-blue, a few levels off the sand at worst). The bar is the vehicle's
  health, ten or twelve segments lit from the left, so a damaged vehicle
  lights only part of it. The key prompts beside the diagram (`C CAMERA`, `E EXIT`) count too,
  but they move with the vehicle's layout and their caps vanish on bright
  ground, so alone they miss vehicles;
- **on foot**: in a match and neither. A player down with the minimap still
  showing reads as on foot; the lives (lives.py) say that he is out of play.

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


#: The bar under the seat diagram (x, y, w, h), reference pixels.
_BF6_BAR = (860, 1050, 200, 6)
#: Which share of it, from the left, may be lit: the bar is the vehicle's health.
_BF6_BAR_LIT = (1.0, 0.8, 0.6, 0.4, 0.2)
#: The inside of the minimap's key cap (x, y, w, h), reference pixels. It sits a pixel or two either way.
_BF6_MAP_KEY = (46, 1021, 18, 18)
_BF6_MAP_KEY_SHIFT = 2


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


def _seat_bar(rgb: np.ndarray) -> bool:
    """The health bar under the vehicle seat diagram, from its left end: one light grey along and across, lighter than just above and below it."""
    h, w = rgb.shape[:2]
    s = w / 1920.0
    x, y, bw, bh = _BF6_BAR
    y0, y1 = int(round(y * s)), int(round((y + bh) * s))
    pad = max(1, int(round(1 * s)))
    side = max(2, int(round(3 * s)))
    # Reference pixels may fall between pixels of a small frame: a row's margin stays out of each.
    grey = rgb[:, int(x * s) : int((x + bw) * s)].mean(axis=2).astype(np.float32)
    band = grey[y0 + pad : y1 - pad]
    above = grey[y0 - pad - side : y0 - pad]
    below = grey[y1 + pad : y1 + pad + side]
    if not (band.size and above.size and below.size):
        return False
    middle = band.mean(axis=0)
    spread = band.std(axis=0)
    # Opaque and one grey, whatever is behind it; averaged along it, a few levels of step on each
    # side stand out even on bright, textured sand, so the longest stretch that holds is what counts.
    for share in _BF6_BAR_LIT:
        n = max(1, int(round(share * middle.size)))
        m = middle[:n]
        level = float(np.median(m))
        step_up = float(m.mean() - above[:, :n].mean())
        step_down = float(m.mean() - below[:, :n].mean())
        if level > 110.0 and min(step_up, step_down) > 4.0 and float(np.median(np.abs(m - level))) < 4.0 and float(np.median(spread[:n])) < 3.0:
            return True
    return False


def _map_key(rgb: np.ndarray) -> bool:
    """The minimap's key cap where it belongs: light up to its edges, a dark letter inside. Looked at in place: a road on the map may touch it."""
    h, w = rgb.shape[:2]
    s = w / 1920.0
    x, y, bw, bh = _BF6_MAP_KEY
    m = max(1, int(round(2 * s)))
    for dy in range(-_BF6_MAP_KEY_SHIFT, _BF6_MAP_KEY_SHIFT + 1):
        for dx in range(-_BF6_MAP_KEY_SHIFT, _BF6_MAP_KEY_SHIFT + 1):
            p = rgb[int((y + dy) * s) : int((y + dy + bh) * s), int((x + dx) * s) : int((x + dx + bw) * s)]
            if p.shape[0] <= 2 * m or p.shape[1] <= 2 * m:
                continue
            light, dark = p.min(axis=2) > 150, p.max(axis=2) < 110
            edge = np.ones(p.shape[:2], bool)
            edge[m:-m, m:-m] = False
            if light.mean() >= 0.45 and 0.05 <= dark.mean() <= 0.45 and light[edge].mean() >= 0.6 and dark[edge].mean() <= 0.15:
                return True
    return False


def bf6(rgb: np.ndarray) -> str:
    """The view of a Battlefield 6 frame (RGB, any 16:9 size)."""
    seat = _seat_bar(rgb)
    if not seat and not _map_key(rgb):
        return SCREEN
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    edges = [float(_box(gray[:, :, None], b).mean()) for b in _BF6_EDGES]
    if max(edges) < 30.0:
        middle = float(_box(gray[:, :, None], _BF6_MIDDLE).mean())
        if middle < 90.0:
            return SCREEN
        if min(edges) < 10.0:
            return ZOOMED
    if seat:
        return VEHICLE
    scale = w / 1920.0
    if all(_key_cap(_box(rgb, b, grow=6), (b[2] * scale, b[3] * scale)) for b in _BF6_KEYS):
        return VEHICLE
    return FOOT


DETECTORS = {"bf6": bf6}


def detector(name: str | None):
    """The game's view detector, or None: every frame is then taken as on foot."""
    return DETECTORS.get(name or "")
