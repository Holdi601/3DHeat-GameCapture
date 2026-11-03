"""
Where the database's views are taken from: every place a player could stand,
at eye height, looking all round.

Places are points on the level's upward-facing triangles, spread evenly
(area-weighted, then thinned to one per `spacing` on a 3D grid, so two floors
of a building both get theirs). Each is checked from its eye with six small
depth renders, a cube round it, before it is kept:

- **inside geometry**: a camera inside a closed mesh (a rock, a wall, a
  prop) sees mostly back faces; more than a few percent of them and the
  place is dropped.
- **no headroom**: something solid less than the eye height above the
  floor - a crawl space, the underside of a stair.

What it cannot tell is a roof or a ledge no player reaches. Those views cost
database space and add a few wrong candidates to retrieval, which the
matching rejects; where a table of real positions exists (a previous run, a
track recorded some other way) `points_from_table` uses those instead.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .camera import Pose
from .level import Level


@dataclass
class Views:
    """The database's poses: one row per view."""

    position: np.ndarray  # (n, 3) the eye
    yaw: np.ndarray  # (n,)
    pitch: np.ndarray  # (n,)
    place: np.ndarray  # (n,) index of the floor point it was taken from
    eye: np.ndarray  # (n,) index into the eye heights

    def __len__(self) -> int:
        return len(self.yaw)

    def pose(self, i: int) -> Pose:
        return Pose(self.position[i].astype(np.float64), float(self.yaw[i]), float(self.pitch[i]))


def ground_points(
    level: Level, spacing: float, seed: int = 0, box: tuple[float, float, float, float] | None = None, *, parts: str | None = None
) -> np.ndarray:
    """
    Points on the floors, about one per `spacing` (level units), as a 3D grid
    would hold them; only inside `box` (x0, z0, x1, z1, level units) when
    given - a game's level file often carries kilometres of backdrop round
    the part anyone plays in.
    """
    a, b, c = level.ground(parts=parts)
    if box is not None and len(a):
        x0, z0, x1, z1 = min(box[0], box[2]), min(box[1], box[3]), max(box[0], box[2]), max(box[1], box[3])
        m = (a + b + c) / 3.0
        inside = (m[:, 0] >= x0) & (m[:, 0] <= x1) & (m[:, 2] >= z0) & (m[:, 2] <= z1)
        a, b, c = a[inside], b[inside], c[inside]
    if not len(a):
        return np.zeros((0, 3))
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    total = float(area.sum())
    rng = np.random.default_rng(seed)
    # Several samples per grid cell, so thinning keeps one in nearly every cell that has floor.
    n = int(min(5_000_000, max(1000, 6 * total / spacing**2)))
    pick = rng.choice(len(area), size=n, p=area / total)
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    pts = a[pick] + u[:, None] * (b[pick] - a[pick]) + v[:, None] * (c[pick] - a[pick])
    return thin(pts, spacing)


def thin(points: np.ndarray, spacing: float) -> np.ndarray:
    """One point per grid cell: `spacing` across, half that in height (floors close above each other)."""
    if not len(points):
        return points
    cell = np.floor(points / np.array([spacing, spacing / 2, spacing])).astype(np.int64)
    _, first = np.unique(cell, axis=0, return_index=True)
    return points[np.sort(first)]


def points_from_table(path: str, spacing: float, box: tuple[float, float, float, float] | None = None) -> np.ndarray:
    """Floor points from a Parquet or CSV table with x, y, z in the level's frame (feet, not eyes)."""
    if str(path).lower().endswith(".parquet"):
        import pyarrow.parquet as pq

        t = pq.read_table(path, columns=["x", "y", "z"])
        pts = np.stack([t[k].to_numpy(zero_copy_only=False) for k in ("x", "y", "z")], axis=1).astype(float)
    else:
        pts = np.genfromtxt(path, delimiter=",", names=True)
        pts = np.stack([pts["x"], pts["y"], pts["z"]], axis=1)
    pts = pts[np.isfinite(pts).all(axis=1)]
    if box is not None:
        x0, z0, x1, z1 = min(box[0], box[2]), min(box[1], box[3]), max(box[0], box[2]), max(box[1], box[3])
        pts = pts[(pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 2] >= z0) & (pts[:, 2] <= z1)]
    return thin(pts, spacing)


def check(renderer, points: np.ndarray, eye: float, *, back_faces: float = 0.05, size: int = 32) -> np.ndarray:
    """True for each floor point whose eye is outside geometry and has headroom."""
    from .camera import Pose

    keep = np.zeros(len(points), bool)
    old = renderer.size
    renderer.resize(size, size)
    faces = [(0.0, 0.0), (90.0, 0.0), (180.0, 0.0), (270.0, 0.0), (0.0, 89.9), (0.0, -89.9)]
    try:
        for i, p in enumerate(points):
            e = p + np.array([0.0, eye, 0.0])
            hits = fronts = 0
            headroom = True
            for yaw, pitch in faces:
                r = renderer.render(Pose(e, yaw, pitch), 90.0, want_color=False)
                hit = r.depth > 0
                hits += int(hit.sum())
                fronts += int((r.front & hit).sum())
                if pitch > 0 and hit.any():
                    # Straight up: the nearest surface over the middle of the view.
                    mid = r.depth[size // 4 : 3 * size // 4, size // 4 : 3 * size // 4]
                    mid = mid[mid > 0]
                    if len(mid) and float(np.median(mid)) < 0.15 * eye:
                        headroom = False
            keep[i] = headroom and hits > 0 and (hits - fronts) <= back_faces * hits
    finally:
        renderer.resize(*old)
    return keep


def places(level: Level, spacing: float, kind: str = "auto", seed: int = 0, box=None) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Where views are taken from: (soldiers' floor points, vehicles' floor points or None).

    - `nav`: soldiers on the level's navigation mesh (`nav:` parts) - exactly
      where the game lets them walk - and vehicles on the `ground:` parts (the
      terrain and roads), as far apart;
    - `ground`: both on the `ground:` parts;
    - `floors`: every upward face (roofs and crates too);
    - `auto`: `nav` when the level carries a navigation mesh, else `floors`.
    """
    from .level import HELPER

    if kind == "auto":
        kind = "nav" if level.has(HELPER) else "floors"
    if kind == "nav":
        walk = ground_points(level, spacing, seed, box, parts=HELPER)
        if box is None and len(walk):
            # Vehicles drive where players walk, not over the kilometres of
            # backdrop a level's ground carries: within the navigation mesh's
            # extent and 50 m round it.
            reach = 50.0 / level.unit_metres
            lo, hi = walk.min(axis=0), walk.max(axis=0)
            box = (lo[0] - reach, lo[2] - reach, hi[0] + reach, hi[2] + reach)
        return walk, ground_points(level, spacing, seed + 1, box, parts="ground:")
    if kind == "ground":
        pts = ground_points(level, spacing, seed, box, parts="ground:")
        return pts, pts
    if kind == "floors":
        pts = ground_points(level, spacing, seed, box)
        return pts, pts
    raise ValueError(f"unknown kind of places {kind!r}: auto, nav, ground or floors")


def merge(a: Views, b: Views) -> Views:
    """Two sets of views as one; `b`'s places and eye indices follow `a`'s."""
    return Views(
        np.concatenate([a.position, b.position]),
        np.concatenate([a.yaw, b.yaw]),
        np.concatenate([a.pitch, b.pitch]),
        np.concatenate([a.place, b.place + (a.place.max() + 1 if len(a.place) else 0)]),
        np.concatenate([a.eye, b.eye + (a.eye.max() + 1 if len(a.eye) else 0)]).astype(np.int8),
    )


def views_at(points: np.ndarray, eyes: list[float], yaw_step: float, pitches: list[float], seed: int = 0) -> Views:
    """Every point x eye height x yaw x pitch; the yaws start at a random turn per point."""
    rng = np.random.default_rng(seed)
    pos, yaw, pitch, place, eye = [], [], [], [], []
    steps = np.arange(0.0, 360.0, yaw_step)
    for i, p in enumerate(points):
        start = rng.random() * yaw_step
        for k, h in enumerate(eyes):
            for pt in pitches:
                for y in steps:
                    pos.append(p + np.array([0.0, h, 0.0]))
                    yaw.append(((start + y + 180.0) % 360.0) - 180.0)
                    pitch.append(pt)
                    place.append(i)
                    eye.append(k)
    return Views(
        np.array(pos, np.float32).reshape(-1, 3),
        np.array(yaw, np.float32),
        np.array(pitch, np.float32),
        np.array(place, np.int32),
        np.array(eye, np.int8),
    )
