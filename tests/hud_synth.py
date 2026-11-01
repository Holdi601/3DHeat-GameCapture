"""
A made-up level, a made-up minimap of it and a made-up kill feed.

Everything the HUD tests read is drawn here, from a seeded random generator:
no frame of any real game is in the repository. The level is a dark grey-blue
ground with light roads, blocky buildings and faint contour lines - the kind of
picture a minimap draws - and the minimap is a window onto it that turns with
the player, with the overlays a real one has on top (a view cone, a coloured
objective marker that moves about, a key hint in the corner).

Because the level is known, so is the answer: where the player was, at every
sample, to the pixel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

#: The minimap's size in the tests, and the player's point on it (the profile's).
SIZE = 296
PLAYER = (0.5, 0.497)
KEY = (14 / 296, 269 / 296, 20 / 296, 22 / 296)


def level(size: int = 2400, seed: int = 7) -> np.ndarray:
    """A BGR picture of a level, `size` square."""
    import cv2

    rng = np.random.default_rng(seed)
    img = np.zeros((size, size, 3), np.uint8)
    img[:] = (58, 48, 40)
    # Faint contours: wavy lines a shade lighter than the ground.
    for k in range(40):
        cx, cy = rng.uniform(0, size, 2)
        r = rng.uniform(80, 500)
        cv2.circle(img, (int(cx), int(cy)), int(r), (66, 56, 47), 1, cv2.LINE_AA)
    # Buildings: rotated blocks, darker or lighter than the ground.
    for k in range(2200):
        cx, cy = rng.uniform(0, size, 2)
        w, h = rng.uniform(6, 36, 2)
        ang = rng.uniform(0, 180)
        box = cv2.boxPoints(((float(cx), float(cy)), (float(w), float(h)), float(ang))).astype(np.int32)
        shade = int(rng.integers(70, 110))
        cv2.fillConvexPoly(img, box, (shade + 12, shade + 4, shade - 4), cv2.LINE_AA)
        cv2.polylines(img, [box], True, (shade + 40, shade + 30, shade + 20), 1, cv2.LINE_AA)
    # Trees and rocks: small dark blobs, the texture between buildings.
    for k in range(5000):
        cx, cy = rng.uniform(0, size, 2)
        cv2.circle(img, (int(cx), int(cy)), int(rng.integers(2, 5)), (44, 38, 33), -1, cv2.LINE_AA)
    # Roads: light grey-blue polylines with bends.
    for k in range(26):
        pts = [rng.uniform(0, size, 2)]
        ang = rng.uniform(0, 2 * math.pi)
        for _ in range(8):
            ang += rng.uniform(-0.6, 0.6)
            step = rng.uniform(80, 220)
            pts.append(pts[-1] + step * np.array([math.cos(ang), math.sin(ang)]))
        cv2.polylines(img, [np.array(pts, np.int32)], False, (170, 150, 132), int(rng.integers(4, 9)), cv2.LINE_AA)
    return img


@dataclass
class View:
    """One sample: the minimap, and where the player truly was and faced on the level."""

    image: np.ndarray
    x: float
    y: float
    #: Degrees clockwise from the level picture's up.
    heading: float


def minimap(world: np.ndarray, x: float, y: float, heading: float, *, zoom: float = 1.0, t: float = 0.0,
            overlays: bool = True) -> np.ndarray:
    """
    The minimap at a place: `heading` turned to the top, the player at PLAYER, `zoom` level pixels per minimap pixel inverse.

    Overlays are drawn the way the game draws them: a translucent yellow-green
    cone up from the player, the player's own marker, an orange diamond that
    drifts (an objective clamped to the edge), and the key hint.
    """
    import cv2

    px, py = PLAYER[0] * SIZE, PLAYER[1] * SIZE
    # Minimap pixel -> level pixel: rotate by the heading round the player, scale by 1/zoom.
    a = math.radians(heading)
    c, s = math.cos(a), math.sin(a)
    inv = np.array([[c, -s], [s, c]]) / zoom
    A = np.zeros((2, 3))
    A[:, :2] = inv
    A[:, 2] = np.array([x, y]) - inv @ np.array([px, py])
    img = cv2.warpAffine(world, A, (SIZE, SIZE), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderValue=(30, 30, 30))
    if not overlays:
        return img
    cone = img.copy()
    tri = np.array([[px, py], [px - 40, py - 95], [px + 40, py - 95]], np.int32)
    cv2.fillConvexPoly(cone, tri, (60, 140, 120))
    img = cv2.addWeighted(cone, 0.35, img, 0.65, 0)
    cv2.circle(img, (int(px), int(py)), 6, (240, 250, 245), -1, cv2.LINE_AA)
    dx = int(40 + 200 * (0.5 + 0.5 * math.sin(t * 0.7)))
    diamond = np.array([[dx, 10], [dx + 9, 19], [dx, 28], [dx - 9, 19]], np.int32)
    cv2.fillConvexPoly(img, diamond, (40, 90, 230), cv2.LINE_AA)
    kx, ky, kw, kh = (int(KEY[0] * SIZE), int(KEY[1] * SIZE), int(KEY[2] * SIZE), int(KEY[3] * SIZE))
    cv2.rectangle(img, (kx, ky), (kx + kw, ky + kh), (185, 185, 185), -1)
    cv2.putText(img, "M", (kx + 4, ky + kh - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (10, 10, 10), 1, cv2.LINE_AA)
    return img


def walk(world: np.ndarray, start: tuple[float, float], legs: list[tuple[float, float]], *, step: float = 6.0,
         zoom: float = 1.0) -> list[View]:
    """
    A walk from `start`: each leg is (turn in degrees, distance in level pixels).

    The view faces the direction of travel, so the minimap turns as the walk
    does - which is what makes registering it a rotation problem and not just
    a sliding one.
    """
    x, y = start
    heading = 0.0
    views = []
    t = 0.0
    for turn, dist in legs:
        # Turn on the spot over a few samples, the way a player swings the view.
        n = max(1, int(abs(turn) / 20))
        for _ in range(n):
            heading = (heading + turn / n) % 360
            views.append(View(minimap(world, x, y, heading, zoom=zoom, t=t), x, y, heading))
            t += 0.2
        for _ in range(max(1, int(dist / step))):
            x += step * math.sin(math.radians(heading))
            y -= step * math.cos(math.radians(heading))
            views.append(View(minimap(world, x, y, heading, zoom=zoom, t=t), x, y, heading))
            t += 0.2
    return views


def compass_strip(heading: float, *, width: int = 1020, height: int = 72, per_degree: float = 4.0) -> np.ndarray:
    """A compass strip like the game's: labels every 30 degrees sliding under a mark at the centre."""
    import cv2

    img = np.full((height, width, 3), 30, np.uint8)
    names = {0: "N", 90: "E", 180: "S", 270: "W"}
    for b in range(0, 360, 15):
        d = (b - heading + 180) % 360 - 180
        x = width / 2 + d * per_degree
        if not 0 <= x < width:
            continue
        if b % 30:
            cv2.line(img, (int(x), height - 30), (int(x), height - 20), (200, 200, 200), 1)
            continue
        label = names.get(b, str(b))
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.putText(img, label, (int(x - tw / 2), height - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (235, 235, 235), 2, cv2.LINE_AA)
    return img


#: Colours the feed draws names in (BGR), as measured on the game's: the
#: player's team, the other team, and the player's own name.
CYAN = (250, 215, 115)
ORANGE = (100, 135, 245)
PALE = (217, 246, 228)


def feed_row(killer: str, victim: str, killer_colour, victim_colour, *, width: int = 912, height: int = 60,
             background=(40, 34, 30), skull: bool = False) -> tuple[np.ndarray, list[tuple[float, float, float, float, str]]]:
    """
    One kill-feed row, right-aligned like the game's, at twice reference size.

    Returns the picture and the text boxes an OCR would find (x0, y0, x1, y1, text).
    """
    import cv2

    img = np.zeros((height, width, 3), np.uint8)
    img[:] = background
    font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2
    (vw, vh), _ = cv2.getTextSize(victim, font, scale, thick)
    (kw, kh), _ = cv2.getTextSize(killer, font, scale, thick)
    base = height // 2 + vh // 2
    vx = width - 24 - vw
    cv2.putText(img, victim, (vx, base), font, scale, victim_colour, thick, cv2.LINE_AA)
    x = vx - 16
    if skull:
        cv2.circle(img, (x - 14, height // 2), 13, victim_colour, -1, cv2.LINE_AA)
        cv2.circle(img, (x - 19, height // 2 - 2), 3, background, -1)
        cv2.circle(img, (x - 9, height // 2 - 2), 3, background, -1)
        x -= 40
    # The weapon: a long thin silhouette with a grip.
    cv2.rectangle(img, (x - 110, height // 2 - 4), (x, height // 2 + 3), killer_colour, -1)
    cv2.rectangle(img, (x - 80, height // 2), (x - 68, height // 2 + 14), killer_colour, -1)
    x -= 130
    kx = x - kw
    cv2.putText(img, killer, (kx, base), font, scale, killer_colour, thick, cv2.LINE_AA)
    boxes = [
        (kx - 2, base - kh - 4, kx + kw + 2, base + 6, killer),
        (vx - 2, base - vh - 4, vx + vw + 2, base + 6, victim),
    ]
    return img, boxes
