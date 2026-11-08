"""
Single fixes -> a track: neighbours vote out a fix that contradicts them,
each life is smoothed on its own, and where the picture gave nothing the
minimap's position (when there is one) stands in, marked as such.

**Outliers.** A player cannot be further from where they were a moment ago
than their speed allows. Each visual fix is compared with the fixes within a
few seconds before it and, separately, after it; consistent means "no further
apart than `max_speed` x the time between them, plus a margin". A fix that
disagrees with most of its neighbours on *both* sides is an outlier and is
dropped. Requiring both sides is what keeps the first fix after a respawn:
it disagrees with everything before it, and agrees with everything after.

**Lives.** The track breaks where two consecutive kept fixes are further
apart than their speed allows (a respawn, or a teleport), where the gap
between fixes is long, and where the minimap's own table starts a new life.
Smoothing never crosses a break.

**Smoothing.** Inside a life, each position is fused with a straight line
through the fixes round it in time (a weighted local linear fit), each
weighted by its uncertainty: a strong fix stays where it is, a weak one is
pulled towards its strong neighbours. A line, not an average, so a player
running past is not dragged behind. The view angles are not smoothed: a
turn of the view is real, and fast. The unsmoothed values are kept in
`x_raw` etc.

**The minimap fallback.** The minimap table (`hud` verb) is in its own
mosaic's frame: pixels, x east, y north. It is related to the level by one
similarity (turn, scale, shift), fitted here on the times where both have
a position - robustly, so the visual outliers do not pull it. For a frame
the picture could not place, that turns the minimap's position into the
level's, with `source = minimap`, and an uncertainty from how well the fit
held (its residuals) - a minimap never says how high the player is, so the
height is carried over from the nearest visual fix of the same life.

**A known anchor.** When the minimap's relation to the level is already
known (`Anchor`: fitted once per map on the visual fixes of several clips,
each clip's mosaic tied to the others by its shift), it is used as it is -
for the fallback and, in `run.py`, as the search prior - and its measured
error is the minimap rows' uncertainty.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Row:
    time: float
    ok: bool
    position: np.ndarray | None = None
    yaw: float | None = None
    pitch: float | None = None
    confidence: float = 0.0
    inliers: int = 0
    rmse: float = 0.0
    note: str = ""
    #: What kind of view the frame was (views.py): foot, vehicle, zoomed.
    view: str = "foot"
    #: The search was cut to the minimap's neighbourhood (run.py): the picture placed it there.
    prior: bool = False
    #: The fastest this frame's player or vehicle can be moving (level units a second): from the
    #: speed the HUD showed round it, or its class (run.py). None: the track's own limits.
    speed_limit: float | None = None
    #: The vehicle's speed its HUD showed in this frame (metres a second), when it shows one.
    hud_speed: float | None = None
    #: The frame is indoors (closed in all round, no sky): the minimap leads (run.py).
    indoor: bool = False
    #: The camera itself, where `position` is the player's or vehicle's (run.body): they differ in
    #: a vehicle's third-person view, where the camera rides behind and above.
    cam: np.ndarray | None = None
    #: The horizontal field of view the frame was solved with, and for a zoomed view its zoom.
    hfov: float | None = None
    zoom: float | None = None
    # filled in here
    source: str = "none"
    kept: bool = False
    life: int = -1
    #: The life the footage puts this frame in (lives.py); None: not in play. Unset (-1): lives unknown.
    play_life: int | None = -1
    smooth: np.ndarray | None = None
    smooth_yaw: float | None = None
    uncertainty: float | None = None


#: The source of a fix the picture made after the search was cut to the minimap's neighbourhood.
VISUAL_PRIOR = "visual+minimap-prior"
#: Sources the picture placed.
VISUAL_SOURCES = ("visual", VISUAL_PRIOR)


@dataclass
class Minimap:
    """A minimap track: time, x (east), y (north), heading (degrees clockwise from north), life."""

    time: np.ndarray
    xy: np.ndarray
    heading: np.ndarray
    life: np.ndarray
    #: Metres of the level a minimap pixel showed, where the table measured it (`locate minimap`).
    zoom: np.ndarray | None = None

    def zoom_at(self, t: float, within: float = 3.0) -> float | None:
        """The largest measured zoom within `within` seconds of t, or None."""
        if self.zoom is None or not len(self.time):
            return None
        i, j = np.searchsorted(self.time, [t - within, t + within])
        return float(np.nanmax(self.zoom[i:j])) if j > i and np.isfinite(self.zoom[i:j]).any() else None

    def at(self, t: float, within: float = 0.6) -> tuple[np.ndarray, float, int] | None:
        if not len(self.time):
            return None
        i = int(np.searchsorted(self.time, t))
        best = min((j for j in (i - 1, i) if 0 <= j < len(self.time)), key=lambda j: abs(self.time[j] - t))
        if abs(self.time[best] - t) > within:
            return None
        return self.xy[best], float(self.heading[best]), int(self.life[best])


def read_minimap(path: str) -> Minimap:
    """The `hud` verb's table: its position rows."""
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    names = t.column_names
    col = {n: t[n].to_pylist() for n in names}
    keep = [i for i in range(t.num_rows) if col.get("x", [None])[i] is not None and col.get("y", [None])[i] is not None]
    time = np.array([col["time"][i] for i in keep], float)
    xy = np.array([[col["x"][i], col["y"][i]] for i in keep], float).reshape(-1, 2)
    heading = np.array([col["heading"][i] if "heading" in col and col["heading"][i] is not None else np.nan for i in keep], float)
    sessions = [col["session"][i] if "session" in col else "" for i in keep]
    lookup: dict[str, int] = {}
    life = np.array([lookup.setdefault(s, len(lookup)) for s in sessions], int)
    order = np.argsort(time, kind="stable")
    zoom = None
    if "residual" in col and "zoom" in col:  # a `locate minimap` table: its zoom is measured, in metres
        zoom = np.array([np.nan if col["zoom"][i] is None else col["zoom"][i] for i in keep], float)[order]
    return Minimap(time[order], xy[order], heading[order], life[order], zoom)


@dataclass
class Similarity:
    """Minimap (x east, y north) -> level (x, z): level_xz = scale * Rot @ xy + shift."""

    scale: float
    rotation: np.ndarray  # 2x2
    shift: np.ndarray
    #: RMS residual of the fit's inliers, level units.
    residual: float
    pairs: int
    inliers: int

    def apply(self, xy: np.ndarray) -> np.ndarray:
        return self.scale * (np.atleast_2d(xy) @ self.rotation.T) + self.shift


def fit_similarity(src: np.ndarray, dst: np.ndarray, threshold: float, rounds: int = 400, seed: int = 0) -> Similarity | None:
    """A 2D similarity, possibly with a mirror, from pairs: RANSAC on two points, then least squares on the inliers."""
    n = len(src)
    if n < 4:
        return None
    rng = np.random.default_rng(seed)
    best: np.ndarray | None = None
    for _ in range(rounds):
        i, j = rng.choice(n, 2, replace=False)
        for mirror in (False, True):
            s = _umeyama(src[[i, j]], dst[[i, j]], mirror)
            if s is None:
                continue
            err = np.linalg.norm(s.apply(src) - dst, axis=1)
            inl = err < threshold
            if best is None or inl.sum() > best.sum():
                best = inl
    if best is None or best.sum() < 4:
        return None
    s = None
    for mirror in (False, True):
        t = _umeyama(src[best], dst[best], mirror)
        if t is not None and (s is None or t.residual < s.residual):
            s = t
    if s is None:
        return None
    s.pairs, s.inliers = n, int(best.sum())
    return s


def _umeyama(src: np.ndarray, dst: np.ndarray, mirror: bool) -> Similarity | None:
    a = src.copy()
    if mirror:
        a[:, 1] = -a[:, 1]
    ma, mb = a.mean(0), dst.mean(0)
    A, B = a - ma, dst - mb
    var = (A**2).sum() / len(a)
    if var <= 1e-12:
        return None
    U, S, Vt = np.linalg.svd(B.T @ A / len(a))
    D = np.eye(2)
    if np.linalg.det(U @ Vt) < 0:
        D[1, 1] = -1
    R = U @ D @ Vt
    scale = float(np.trace(np.diag(S) @ D) / var)
    if mirror:
        R = R @ np.diag([1.0, -1.0])
    shift = mb - scale * (R @ (ma * ([1.0, -1.0] if mirror else [1.0, 1.0])))
    sim = Similarity(scale, R, shift, 0.0, len(src), len(src))
    sim.residual = float(np.sqrt(np.mean(np.sum((sim.apply(src) - dst) ** 2, axis=1))))
    return sim


@dataclass
class TrackOptions:
    #: Level units a second a player may move; from the game profile.
    max_speed: float
    #: Level units added to every distance allowance: what a good fix may be off by.
    margin: float
    #: Seconds either side a fix is checked against.
    window: float = 3.0
    #: Seconds between kept fixes that break a life.
    gap: float = 8.0
    #: Gaussian sigma of the smoothing, seconds.
    sigma: float = 0.5
    #: Rows the minimap may stand in for are no further than this from a minimap sample, seconds.
    minimap_within: float = 0.6
    #: Level units a second in a vehicle; None: as on foot.
    vehicle_speed: float | None = None


@dataclass
class Anchor:
    """
    Minimap (x east, y north) -> level (x, z), known before the run: a
    similarity and the error it showed against visual fixes (level units).
    """

    similarity: "Similarity"
    #: Median and 90th percentile of |minimap carried to the level - visual fix|.
    median: float
    p90: float
    pairs: int
    #: What this run's own confident fixes say the anchor is off by: (time, level dx, dz). A
    #: stitched minimap drifts a little across a map, so the correction is local in time.
    corrections: list = field(default_factory=list)
    #: Seconds round a frame whose corrections count.
    window: float = 120.0
    #: A warp from the level itself (the game's own map registered to the level, the clip's mosaic
    #: to that map): level x and z on a grid over minimap units, bilinear between the nodes. A
    #: stitched minimap is not quite flat, so where there is a grid it replaces the similarity.
    grid: dict | None = None

    def _warp(self, xy: np.ndarray) -> np.ndarray | None:
        g = self.grid
        if g is None:
            return None
        fx = (float(xy[0]) - g["x0"]) / g["step"]
        fy = (float(xy[1]) - g["y0"]) / g["step"]
        i, j = int(math.floor(fy)), int(math.floor(fx))
        if not (0 <= i < g["ny"] - 1 and 0 <= j < g["nx"] - 1):
            return None
        a, b = fy - i, fx - j
        out = []
        for m in (g["x"], g["z"]):
            out.append((1 - a) * ((1 - b) * m[i, j] + b * m[i, j + 1]) + a * ((1 - b) * m[i + 1, j] + b * m[i + 1, j + 1]))
        return np.array(out)

    def correction(self, t: float) -> tuple[np.ndarray, float | None]:
        """The anchor's local error at time t from this run's fixes, and how well they agree (or None: no fix yet)."""
        if not self.corrections:
            return np.zeros(2), None
        c = np.array(self.corrections, float)
        near = c[np.abs(c[:, 0] - t) <= self.window]
        if len(near) < 2:
            # Fixes far off in time say nothing about the error here: the minimap drifts with place,
            # and the player has moved.
            return np.zeros(2), None
        d = np.median(near[:, 1:], axis=0)
        spread = float(np.percentile(np.linalg.norm(near[:, 1:] - d, axis=1), 90)) if len(near) >= 3 else None
        return d, spread

    def yaw(self, heading: float) -> float:
        """A minimap heading (degrees clockwise from north) as a yaw in the level's frame (camera.direction)."""
        north = self.similarity.rotation @ np.array([0.0, 1.0])
        east = self.similarity.rotation @ np.array([1.0, 0.0])
        h = math.radians(heading)
        d = math.sin(h) * east + math.cos(h) * north
        return math.degrees(math.atan2(-d[1], d[0]))

    def to_level(self, xy: np.ndarray, t: float | None = None) -> np.ndarray:
        """The minimap's xy on the level; with t, moved by this run's own correction round t."""
        p = self._warp(np.asarray(xy, float).ravel())
        if p is None:
            p = self.similarity.apply(xy)[0]
        return p if t is None else p + self.correction(t)[0]


def read_anchor(path: str) -> Anchor:
    """
    An anchor file: {"scale", "rotation" (2x2), "shift", "median", "p90", "pairs"}, or with "clip_shift"
    added to xy first; optionally "grid" (x0, y0, step, nx, ny, x, z: level x and z at each node over
    the clip's own minimap units), which then places every point inside it.
    """
    import json

    d = json.loads(open(path, encoding="utf-8").read())
    rot = np.array(d["rotation"], float)
    shift = np.array(d["shift"], float)
    scale = float(d["scale"])
    if d.get("clip_shift"):
        # This clip's mosaic is the reference's moved by clip_shift (minimap units).
        shift = shift + scale * rot @ np.array(d["clip_shift"], float)
    sim = Similarity(scale, rot, shift, float(d.get("median", 0.0)), int(d.get("pairs", 0)), int(d.get("pairs", 0)))
    grid = None
    if d.get("grid"):
        g = d["grid"]
        grid = {"x0": float(g["x0"]), "y0": float(g["y0"]), "step": float(g["step"]), "nx": int(g["nx"]), "ny": int(g["ny"]),
                "x": np.array(g["x"], float), "z": np.array(g["z"], float)}
    return Anchor(sim, float(d.get("median", 0.0)), float(d.get("p90", 0.0)), int(d.get("pairs", 0)), grid=grid)


def build_track(rows: list[Row], options: TrackOptions, minimap: Minimap | None = None, anchor: Anchor | None = None) -> tuple[list[Row], dict]:
    rows = sorted(rows, key=lambda r: r.time)
    report: dict = {"frames": len(rows), "visual_fixes": sum(r.ok for r in rows)}
    known = any(r.play_life != -1 for r in rows)
    if known:
        for r in rows:
            if r.ok and r.play_life is None:
                r.ok = False
                r.note = (r.note + "; " if r.note else "") + "not in play (dead, down or deploying)"
    fixes = [r for r in rows if r.ok and r.position is not None]
    times = np.array([r.time for r in fixes])
    pos = np.array([r.position for r in fixes]).reshape(-1, 3)
    conf = np.array([max(0.05, r.confidence) for r in fixes])

    fast = np.array([r.view == "vehicle" for r in fixes])

    limits = [r.speed_limit for r in fixes]

    def consistent(i: int, j: int) -> bool:
        if limits[i] is not None and limits[j] is not None:
            speed = max(limits[i], limits[j])
        else:
            speed = options.vehicle_speed if options.vehicle_speed and (fast[i] or fast[j]) else options.max_speed
        return float(np.linalg.norm(pos[i] - pos[j])) <= speed * abs(times[i] - times[j]) + options.margin

    # Outliers: against both sides.
    outlier = np.zeros(len(fixes), bool)
    for i in range(len(fixes)):
        votes = []
        for side in (-1, 1):
            agree = disagree = 0.0
            j = i + side
            while 0 <= j < len(fixes) and abs(times[j] - times[i]) <= options.window:
                if consistent(i, j):
                    agree += conf[j]
                else:
                    disagree += conf[j]
                j += side
            votes.append((agree, disagree))
        sides = [(a, d) for a, d in votes if a + d > 0]
        if sides and all(d > a for a, d in sides):
            outlier[i] = True
    report["outliers"] = int(outlier.sum())

    kept = [k for k in range(len(fixes)) if not outlier[k]]
    life = 0
    lives = np.full(len(fixes), -1)
    mm_life = None
    report["jump_dropped"] = 0
    report["jumps_without_death"] = 0
    if known:
        # The lives are the footage's: a position may jump only where the player died. Within a
        # life a step that breaks the speed means one side is wrong: the weaker goes - unless
        # both are strong and the run marked them (a missed death, or a real teleport).
        flagged = lambda k: "jump without detected death" in (fixes[k].note or "")
        changed = True
        while changed:
            changed = False
            for a, b in zip(kept, kept[1:]):
                if fixes[a].play_life != fixes[b].play_life or consistent(a, b):
                    continue
                if flagged(a) and flagged(b):
                    continue
                weak = a if (fixes[a].inliers, conf[a]) < (fixes[b].inliers, conf[b]) else b
                outlier[weak] = True
                fixes[weak].note = (fixes[weak].note + "; " if fixes[weak].note else "") + "dropped: a jump within a life, weaker than its neighbour"
                report["jump_dropped"] += 1
                kept = [k for k in kept if k != weak]
                changed = True
                break
        report["jumps_without_death"] = sum(
            1 for a, b in zip(kept, kept[1:]) if fixes[a].play_life == fixes[b].play_life and not consistent(a, b)
        )
        order = {}
        for k in kept:
            lives[k] = order.setdefault(fixes[k].play_life, len(order))
        life = len(order) - 1
    for n, k in enumerate(kept if not known else []):
        if n:
            p = kept[n - 1]
            jump = not consistent(k, p) or times[k] - times[p] > options.gap
            if minimap is not None:
                here = minimap.at(times[k], options.minimap_within)
                if here is not None and mm_life is not None and here[2] != mm_life:
                    jump = True
                if here is not None:
                    mm_life = here[2]
            if jump:
                life += 1
        lives[k] = life
    report["lives"] = life + 1 if kept else 0

    # Smoothing within each life: each fix against a line through its
    # neighbours, weighted by how certain each is. A strong fix stays where it
    # is - a player strafing or stopping is real motion, and a fix good to a
    # few centimetres knows that better than any line - and a weak one is
    # pulled towards where its strong neighbours put it.
    unc = {k: visual_uncertainty(fixes[k].inliers, options.margin) for k in kept}
    motion = options.margin / 3.0
    for k in kept:
        r = fixes[k]
        r.kept, r.source, r.life = True, VISUAL_PRIOR if r.prior else "visual", int(lives[k])
        r.smooth_yaw = r.yaw
        others = [j for j in kept if j != k and lives[j] == lives[k] and abs(times[j] - times[k]) <= 3 * options.sigma]
        own = 1.0 / unc[k] ** 2
        if len(others) < 2:
            r.smooth, r.uncertainty = pos[k].copy(), unc[k]
            continue
        dt = times[others] - times[k]
        w = np.exp(-0.5 * (dt / options.sigma) ** 2) / np.array([unc[j] ** 2 for j in others])
        # Weighted least squares of position = a + b * dt: a is the line's position at this fix.
        A = np.stack([np.ones_like(dt), dt], axis=1)
        AtW = A.T * w
        try:
            coef = np.linalg.solve(AtW @ A + 1e-9 * np.eye(2), AtW @ pos[others])
        except np.linalg.LinAlgError:
            r.smooth, r.uncertainty = pos[k].copy(), unc[k]
            continue
        line = coef[0]
        # How far the line itself may be off: its fit, and motion no line follows (a turn, a stop).
        spread = float(np.sqrt(np.sum(w[:, None] * (A @ coef - pos[others]) ** 2) / w.sum()))
        line_var = spread**2 + motion**2
        fused = (own * pos[k] + line / line_var) / (own + 1.0 / line_var)
        r.smooth = fused
        r.uncertainty = float(math.sqrt(1.0 / (own + 1.0 / line_var)))
    for k in np.flatnonzero(outlier):
        fixes[k].note = (fixes[k].note + "; " if fixes[k].note else "") + "outlier: contradicts its neighbours"

    # The minimap where the picture gave nothing.
    report["minimap"] = None
    if minimap is not None and (len(kept) >= 4 or anchor is not None):
        if anchor is not None:
            sim = anchor.similarity
        else:
            src, dst, at = [], [], []
            for k in kept:
                here = minimap.at(times[k], options.minimap_within)
                if here is not None:
                    src.append(here[0])
                    dst.append(fixes[k].smooth[[0, 2]])
                    at.append(k)
            sim = fit_similarity(np.array(src).reshape(-1, 2), np.array(dst).reshape(-1, 2), threshold=4 * options.margin)
        if sim is not None:
            report["minimap"] = {
                "pairs": sim.pairs,
                "inliers": sim.inliers,
                "residual": round(sim.residual, 3),
                "scale": sim.scale,
            }
            filled = 0
            for r in rows:
                if r.kept:
                    continue
                if known and r.play_life is None:
                    continue  # dead or deploying: the minimap shows nothing of the player
                here = minimap.at(r.time, options.minimap_within)
                if here is None:
                    continue
                xz = anchor.to_level(here[0], r.time) if anchor is not None else sim.apply(here[0])[0]
                near = [k for k in kept if abs(times[k] - r.time) <= options.gap and (not known or fixes[k].play_life == r.play_life)]
                if near:
                    height = fixes[min(near, key=lambda k: abs(times[k] - r.time))].smooth[1]
                elif kept:
                    height = float(np.median(pos[kept, 1]))
                else:
                    height = float("nan")  # no fix at all: the minimap knows no height
                r.smooth = np.array([xz[0], height, xz[1]])
                r.source = "minimap"
                r.uncertainty = (anchor.p90 if anchor is not None else 2.0 * sim.residual) + options.margin
                r.confidence = float(max(0.05, min(0.5, sim.inliers / max(1, sim.pairs)) * 0.5))
                if math.isfinite(here[1]):
                    north = sim.rotation @ np.array([0.0, 1.0])
                    east = sim.rotation @ np.array([1.0, 0.0])
                    h = math.radians(here[1])
                    d = math.sin(h) * east + math.cos(h) * north  # level (x, z)
                    r.smooth_yaw = math.degrees(math.atan2(-d[1], d[0]))
                filled += 1
            report["minimap"]["filled"] = filled
    report["unplaced"] = sum(1 for r in rows if r.smooth is None)
    return rows, report


def visual_uncertainty(inliers: int, margin: float) -> float:
    """
    A visual fix's typical error, level units, by its inlier count, as a
    fraction of the margin (1.5 m): about 5 cm with 150 inliers or more,
    20 cm with 60, 60 cm below. Measured on renders, these are the order and
    the ratios rather than a promise for real frames (docs/locate.md).
    """
    if inliers >= 150:
        f = 0.033
    elif inliers >= 60:
        f = 0.133
    else:
        f = 0.4
    return f * margin
