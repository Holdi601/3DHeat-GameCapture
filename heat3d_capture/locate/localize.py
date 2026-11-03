"""
One frame -> where the camera was and where it looked, against the level.

1. **Retrieval.** The frame's global descriptor (HUD masked out) against
   every view in the database: the most similar few dozen are a shortlist,
   thinned so that it holds different places and directions rather than
   eight turns of one spot. With no prior this is the whole level - the
   default. With one (`near`, `radius`) only views near it are considered,
   which is faster and cannot find the right place if the prior is wrong.
2. **Matching.** Each shortlisted view is rendered again at the frame's size
   and field of view, with its depth. ALIKED keypoints of frame and render
   are matched with LightGlue; a matched render pixel plus its depth is a 3D
   point of the level, so each match is a 2D-3D correspondence.
3. **Pose.** PnP with RANSAC on those, then a refinement that keeps the
   camera level (no roll: a first-person view does not tilt sideways) and
   minimises the reprojection error of the inliers. The view with the most
   inliers wins.
4. **Render and compare.** The level is rendered at the solved pose and
   matched again, which replaces the database view - up to a few metres and
   tens of degrees away - with one that nearly coincides with the frame, so
   more and better-placed matches survive. Repeated while it helps.

The result says how sure it is: inliers, reprojection error, and whether a
different place came close (`runner_up`). `confidence` folds these into one
number, 0..1, calibrated on renders (docs/locate.md); `ok` is the verdict
the track builds on. Two more checks were tried and dropped because they did
not tell right fixes from wrong ones on the bench: the global descriptor of
the frame against the render at the solved pose, and how well the level's
depth edges at that pose fall on the frame's edges.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from .camera import Pose, angles, intrinsics
from .database import Database, level_for
from .features import GlobalDescriptor, Keypoints, LocalMatcher, normalise
from .level import Level
from .render import Light, Render, Renderer

#: Below this many PnP inliers a solve is not believed.
MIN_INLIERS = 25
#: Reprojection error (pixels at the working width) an inlier may have.
PIXELS = 4.0
#: Matches on static parts of the level enough to solve on without the destructible ones.
STATIC_ENOUGH = 40
#: The confidence a fix needs to be `ok`. On the bench (docs/locate.md),
#: fixes from 0.85 up were right 97.5-99% of the time; between 0.7 and 0.85,
#: on a database of every floor, about half. A frame left out is filled by
#: the track or the minimap; a wrong one is not.
OK_CONFIDENCE = 0.85
#: Metres above standing eye height a camera may be and still be a player's:
#: a jump, a drop off a ledge, a ladder. Generous on purpose - the look-alikes
#: this test catches sit inside geometry or far off any floor, and a true pose
#: in mid-air must not be thrown away.
JUMP = 3.0


@dataclass
class Fix:
    ok: bool
    pose: Pose | None
    inliers: int = 0
    matches: int = 0
    #: RMS reprojection error of the inliers, pixels at the working width.
    rmse: float = 0.0
    confidence: float = 0.0
    #: Retrieval rank of the database view the solve started from (0 = best).
    rank: int = -1
    #: Inliers of the best solve at a different place (more than `apart` away): near `inliers` is ambiguous.
    runner_up: int = 0
    tried: int = 0
    #: Fraction of an 8 x 8 grid over the frame that has inliers: matches all on one patch are weak evidence.
    spread: float = 0.0
    seconds: float = 0.0
    note: str = ""
    #: Every solve tried: retrieval rank, inliers, position, height over the floor, possible or not.
    solves: list = field(default_factory=list)
    #: The physically possible poses found, strongest first, one per place (`Candidate`): what a
    #: sequence of frames chooses among when the strongest is not the one its neighbours agree with.
    candidates: list = field(default_factory=list)


@dataclass
class Candidate:
    position: np.ndarray
    yaw: float
    pitch: float
    inliers: int
    rmse: float


@dataclass
class _Solve:
    rotation: np.ndarray
    position: np.ndarray
    inliers: int
    matches: int
    rmse: float
    #: The inliers' pixels in the frame.
    pixels: np.ndarray | None = None
    #: The inliers' 3D points in the level, matching `pixels`.
    points: np.ndarray | None = None


def confidence(inliers: int, runner_up: int, rmse: float, noise: float = 1.5) -> float:
    """
    One number for how far a fix can be trusted.

    Inliers saturate (150 are about as good as 600), a close second at another
    place halves it at a tie, and a reprojection error above `noise` - what a
    right fix shows on these frames (profiles.pixel_noise) - lowers it.
    """
    base = 1.0 - math.exp(-max(0, inliers - MIN_INLIERS / 2) / 40.0)
    ambiguity = 1.0 - 0.5 * min(1.0, runner_up / max(1, inliers)) ** 2
    sharp = 1.0 / (1.0 + max(0.0, rmse - noise) / 3.0)
    return float(max(0.0, min(1.0, base * ambiguity * sharp)))


class Locator:
    def __init__(
        self,
        db: Database,
        level: Level | None = None,
        *,
        width: int = 960,
        hfov: float | None = None,
        shortlist: int = 8,
        light: Light | None = None,
        normalisation: str = "none",
        max_keypoints: int = 2048,
        refine: int = 2,
        enough: int = 250,
    ):
        self.db = db
        self.level = level or level_for(db)
        self.unit = self.level.unit_metres
        self.width = width
        self.hfov = hfov or db.hfov
        self.shortlist = shortlist
        self.light = light or Light(**db.meta.get("light", {}))
        self.normalisation = normalisation
        self.refine = refine
        self.enough = enough
        self.renderer = Renderer(self.level, width, int(round(width * 9 / 16)))
        self.describe = GlobalDescriptor(db.meta["descriptor"]["model"], head=db.meta["descriptor"].get("head"))
        self.matcher = LocalMatcher(max_keypoints)
        self._place = db.views.position[:, [0, 2]]
        spacing = float(db.meta.get("options", {}).get("spacing", 2.5)) / self.unit
        #: Two fixes further apart than this are different places.
        self.apart = max(3.0 / self.unit, 1.5 * spacing)
        game = db.meta.get("game", {})
        eyes = [float(e) / self.unit for e in game.get("eye_heights", [1.6])]
        lowest = game.get("lowest_eye")
        #: How high above a floor a camera may be: from the lowest the game's
        #: eye goes (prone), or a little under its lowest eye height, to the
        #: highest plus a jump.
        self.above_floor = (float(lowest) / self.unit if lowest else 0.85 * min(eyes), max(eyes) + JUMP / self.unit)
        #: What a right fix's reprojection error is on these frames (profiles.pixel_noise).
        self.noise = float(game.get("pixel_noise", 1.5))

    # -- retrieval ---------------------------------------------------------

    def candidates(self, q: np.ndarray, near: np.ndarray | None = None, radius: float | None = None) -> list[int]:
        """The shortlist for a frame's global descriptor `q`."""
        sims = self.db.descriptors @ q
        if near is not None and radius:
            far = np.linalg.norm(self._place - np.asarray(near, float)[[0, 2]], axis=1) > radius
            sims = np.where(far, -np.inf, sims)
        order = np.argsort(-sims)[: max(64, self.shortlist * 12)]
        chosen: list[int] = []
        spacing = float(self.db.meta.get("options", {}).get("spacing", 2.5)) / self.unit
        for i in order:
            if not np.isfinite(sims[i]):
                break
            close = False
            for j in chosen:
                d = np.linalg.norm(self.db.views.position[i] - self.db.views.position[j])
                turn = abs((self.db.views.yaw[i] - self.db.views.yaw[j] + 180.0) % 360.0 - 180.0)
                if d < 0.75 * spacing and turn < 40.0:
                    close = True
                    break
            if not close:
                chosen.append(int(i))
            if len(chosen) >= self.shortlist:
                break
        return chosen

    # -- one solve against one render -------------------------------------

    def _solve(self, query: Keypoints, render: Render, K: np.ndarray, size: tuple[int, int]) -> _Solve | None:
        import cv2

        found = self._correspondences(query, render, K, size)
        if found is None:
            return None
        points, qxy, n_pairs = found
        ok, rvec, tvec, inl = cv2.solvePnPRansac(
            points.astype(np.float64),
            qxy.astype(np.float64),
            K,
            None,
            iterationsCount=2000,
            reprojectionError=PIXELS,
            confidence=0.9999,
            flags=cv2.SOLVEPNP_SQPNP,
        )
        if not ok or inl is None or len(inl) < 6:
            return None
        inl = inl.ravel()
        Rq = cv2.Rodrigues(rvec)[0]
        C = (-Rq.T @ tvec).ravel()
        yaw, pitch, _ = angles(Rq)
        pose, err = _level_refine(points[inl], qxy[inl], K, Pose(C, yaw, pitch))
        # Count again with the refined, roll-free pose: that is the pose reported.
        proj = _project(points, K, pose)
        e = np.linalg.norm(proj - qxy, axis=1)
        keep = e < PIXELS
        rmse = float(np.sqrt(np.mean(e[keep] ** 2))) if keep.any() else float("inf")
        return _Solve(pose.rotation(), pose.position, int(keep.sum()), n_pairs, rmse, qxy[keep], points[keep])

    def _correspondences(self, query: Keypoints, render: Render, K: np.ndarray, size: tuple[int, int]):
        """The frame's keypoints matched to the render, with the level points its depth puts under them: (points, frame pixels, matches), or None."""
        w, h = size
        valid = render.depth > 0
        ref = self.matcher.detect(normalise(render.color, self.normalisation), valid)
        pairs, _ = self.matcher.match(query, ref)
        if len(pairs) < 8:
            return None
        uv = ref.xy[pairs[:, 1]]
        ix = np.clip(np.round(uv).astype(int), 0, [w - 1, h - 1])
        depth = render.depth
        z = depth[ix[:, 1], ix[:, 0]]
        # A keypoint on an edge can take the depth of what is behind it: keep
        # only those whose neighbourhood agrees on the distance.
        lo = np.full(len(ix), np.inf)
        hi = np.zeros(len(ix))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                n = depth[np.clip(ix[:, 1] + dy, 0, h - 1), np.clip(ix[:, 0] + dx, 0, w - 1)]
                n = np.where(n > 0, n, np.inf)
                lo = np.minimum(lo, n)
                hi = np.maximum(hi, np.where(np.isfinite(n), n, np.inf))
        good = (z > 0) & np.isfinite(hi) & (hi - lo < 0.04 * z)
        if good.sum() < 8:
            return None
        if render.destructible is not None:
            # What the game can destroy may be gone, or rubble, in the frame: trust the static
            # level (terrain, roads, the large structures) and drop matches on destructible parts
            # when enough static ones are left to solve on.
            static = good & ~render.destructible[ix[:, 1], ix[:, 0]]
            if static.sum() >= STATIC_ENOUGH:
                good = static
        uv, z, qxy = uv[good], z[good], query.xy[pairs[good, 0]]
        R = render.pose.rotation()
        rays = np.linalg.solve(K, np.vstack([uv.T, np.ones(len(uv))])).T * z[:, None]
        points = rays @ R + render.pose.position
        return points, qxy, len(pairs)

    # -- one frame ---------------------------------------------------------

    def locate(
        self,
        rgb: np.ndarray,
        mask: np.ndarray | None = None,
        *,
        near: np.ndarray | None = None,
        radius: float | None = None,
        seeds: list[Pose] | None = None,
        hfov: float | None = None,
        highest: float | None = None,
    ) -> Fix:
        """
        `rgb`: the frame, uint8 RGB, any size; `mask`: True where it shows the
        level; `hfov`: its field of view when not the locator's own (a
        vehicle's camera); `highest`: how far above a floor the camera may
        be, level units, when not a player's eye. `near`, `radius`: consider
        only database views that close. `seeds`: poses to start from instead
        of database views (a prior that says where and which way); the fix is
        judged by the same rules either way.
        """
        saved = self.hfov, self.above_floor
        if hfov:
            self.hfov = hfov
        if highest:
            self.above_floor = (self.above_floor[0], highest)
        try:
            return self._locate(rgb, mask, near, radius, seeds)
        finally:
            self.hfov, self.above_floor = saved

    def _locate(self, rgb: np.ndarray, mask: np.ndarray | None, near: np.ndarray | None, radius: float | None, seeds: list[Pose] | None = None) -> Fix:
        import cv2

        started = time.monotonic()
        h0, w0 = rgb.shape[:2]
        w = self.width
        h = int(round(h0 * w / w0))
        if (w0, h0) != (w, h):
            rgb = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
            if mask is not None:
                mask = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
        self.renderer.resize(w, h)
        K = intrinsics(w, h, self.hfov)
        if seeds:
            # Poses to start from, given (a prior that says where and which way): rendered and
            # matched like database views, then judged by exactly the same rules.
            shortlist = list(range(len(seeds)))
            pose_of = lambda i: seeds[i]
        else:
            described = self.describe([rgb], [mask])[0]
            shortlist = self.candidates(described, near, radius)
            pose_of = self.db.views.pose
        if not shortlist:
            return Fix(False, None, note="no database view near the prior", seconds=time.monotonic() - started)
        query = self.matcher.detect(normalise(rgb, self.normalisation), mask)
        if len(query.xy) < 20:
            return Fix(False, None, note="too little texture in the frame", seconds=time.monotonic() - started)

        solves: list[tuple[int, _Solve]] = []
        for rank, i in enumerate(shortlist):
            r = self.renderer.render(pose_of(i), self.hfov, self.light)
            s = self._solve(query, r, K, (w, h))
            if s is not None:
                solves.append((rank, s))
                if s.inliers >= self.enough:
                    break
        tried = len(solves)
        if not solves:
            return Fix(False, None, tried=len(shortlist), note="no shortlisted view matched", seconds=time.monotonic() - started)
        # A pose no player could have - not at eye height over a floor, or
        # inside geometry - is a match to look-alike texture elsewhere (a tiled
        # floor matched to a wall of the same material), however many inliers.
        solves.sort(key=lambda rs: -rs[1].inliers)
        tried_log = []
        possible: list[tuple[int, _Solve]] = []
        for rank, s in solves:
            check = self.renderer.below(s.position) if s.inliers >= MIN_INLIERS // 2 else (float("nan"), float("nan"), 1.0)
            fine = s.inliers < MIN_INLIERS // 2 or self._possible(*check)
            tried_log.append(
                {"rank": rank, "inliers": s.inliers, "position": s.position.round(2).tolist(), "floor": [round(c, 2) for c in check], "possible": fine}
            )
            if fine:
                possible.append((rank, s))
        impossible = len(solves) - len(possible)
        if not possible:
            return Fix(False, None, tried=tried, note="no physically possible pose (not at eye height over a floor)", seconds=time.monotonic() - started, solves=tried_log)
        # The strongest few places, each refined by rendering at its own solve
        # and matching again, before one is chosen: the right place gains far
        # more from that than a look-alike does, which is often what separates
        # them (a look-alike can lead before refinement).
        contenders: list[tuple[int, _Solve]] = []
        for rank, s in possible:
            if s.inliers < max(MIN_INLIERS // 2, 0.4 * possible[0][1].inliers) or len(contenders) >= 3:
                break
            if any(np.linalg.norm(s.position - c.position) <= self.apart for _, c in contenders):
                continue
            contenders.append((rank, self._refine(query, s, K, (w, h))))
        if not contenders:
            contenders = [possible[0]]
        contenders.sort(key=lambda rs: -rs[1].inliers)
        rank, best = contenders[0]
        runner_up = max(
            [s.inliers for _, s in contenders[1:] if np.linalg.norm(s.position - best.position) > self.apart]
            + [s.inliers for _, s in possible if np.linalg.norm(s.position - best.position) > self.apart],
            default=0,
        )
        for entry in tried_log:
            for _, c in contenders:
                if entry["possible"] and np.linalg.norm(np.array(entry["position"]) - c.position) <= self.apart:
                    entry["refined"] = max(entry.get("refined", 0), c.inliers)
        candidates: list[Candidate] = []
        for _, c in sorted(contenders + possible, key=lambda rs: -rs[1].inliers):
            if c.inliers < MIN_INLIERS // 2 or any(np.linalg.norm(c.position - k.position) <= self.apart for k in candidates):
                continue
            cy, cp, _ = angles(c.rotation)
            candidates.append(Candidate(c.position.copy(), cy, cp, c.inliers, c.rmse))
        yaw, pitch, roll = angles(best.rotation)
        spread = _spread(best.pixels, w, h)
        conf = confidence(best.inliers, runner_up, best.rmse, self.noise)
        ambiguous = runner_up >= 0.8 * best.inliers
        ok = best.inliers >= MIN_INLIERS and not ambiguous and conf >= OK_CONFIDENCE
        if ok:
            note = ""
        elif best.inliers >= MIN_INLIERS and ambiguous:
            note = "ambiguous: another place matched nearly as well"
        elif best.inliers >= MIN_INLIERS:
            note = "not confident enough"
        else:
            note = "too few inliers"
        if impossible:
            note = (note + "; " if note else "") + f"{impossible} impossible pose(s) set aside"
        return Fix(
            ok,
            Pose(best.position, yaw, pitch, roll),
            inliers=best.inliers,
            matches=best.matches,
            rmse=best.rmse,
            confidence=conf if ok else min(conf, 0.3),
            rank=rank,
            runner_up=runner_up,
            tried=tried,
            spread=spread,
            seconds=time.monotonic() - started,
            note=note,
            solves=tried_log,
            candidates=candidates,
        )

    def locate_zoomed(
        self,
        rgb: np.ndarray,
        mask: np.ndarray | None,
        near: np.ndarray,
        yaw: float | None,
        base_hfov: float,
        *,
        zooms: tuple[float, ...] = (1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0),
        spread: float = 30.0,
        pitch: float = 0.0,
        reach: float = 4.0,
    ) -> tuple[Fix, float | None]:
        """
        A zoomed frame (a scope, a gunner's sight): its zoom is unknown, and a
        sliver of the level looks like none of the database's wide views, so
        it is not searched for over the level. It is solved from where the
        player was a moment before or after: `near`, the sight's position from
        a neighbouring fix, good to `reach` metres, and `yaw`, roughly where
        they looked (None for all round).

        A narrow view pins its position poorly - a step back and a little more
        zoom look almost the same - so the position is first held at `near`
        and only the direction and zoom are searched for. For each zoom the
        level is rendered there in directions round `yaw`; the frame's
        keypoints matched to a render, with the level points under them, give
        the direction (a rotation fitted to the rays, robustly) for a range of
        focal lengths round that zoom's, and the one that agrees with the most
        points wins. Its agreeing points then settle position, direction and
        zoom together, the position held to within about `reach` of `near`,
        and are counted in pixels like any fix. Returns the fix and the zoom
        factor (the tangent of the half field of view against `base_hfov`'s),
        or None.
        """
        import cv2

        started = time.monotonic()
        h0, w0 = rgb.shape[:2]
        w = self.width
        h = int(round(h0 * w / w0))
        small = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
        m = None if mask is None else cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
        query = self.matcher.detect(normalise(small, self.normalisation), m)
        if len(query.xy) < 20:
            return Fix(False, None, note="zoomed view: too little texture"), None
        self.renderer.resize(w, h)
        seat = np.asarray(near, float)
        base = math.tan(math.radians(base_hfov) / 2)
        best = None
        for z in zooms:
            hfov = math.degrees(2 * math.atan(base / z))
            step = max(3.0, 0.6 * hfov)
            yaws = [yaw + d for d in np.arange(-spread, spread + 1e-6, step)] if yaw is not None else list(np.arange(-180.0, 180.0, step))
            K = intrinsics(w, h, hfov)
            # The narrower the view, the less a wrong pitch overlaps: try a few.
            pitches = [pitch] if z < 3 else [pitch - 0.3 * hfov * h / w, pitch, pitch + 0.3 * hfov * h / w]
            for y in yaws:
                for pt in pitches:
                    r = self.renderer.render(Pose(seat, float(y), float(pt)), hfov, self.light)
                    found = self._correspondences(query, r, K, (w, h))
                    if found is None:
                        continue
                    sol = _aim(found[0], found[1], seat, (w, h), hfov, reach / self.unit)
                    if sol is not None and (best is None or sol[2] > best[0][2]):
                        best = (sol, found)
        if best is None or best[0][2] < MIN_INLIERS:
            return Fix(False, None, inliers=0 if best is None else best[0][2], note="zoomed view: no zoom and direction matched", seconds=time.monotonic() - started), None
        (pose, hfov, _, _, agree), (points, qxy, n_pairs) = best
        # Then position, direction and zoom together, the position held near the seat; once more
        # rendered at the answer, closer to the frame, with more matches.
        pose, hfov, inliers, rmse = _settle(points[agree], qxy[agree], (w, h), pose, hfov, seat, reach / self.unit)
        r = self.renderer.render(pose, hfov, self.light)
        found = self._correspondences(query, r, intrinsics(w, h, hfov), (w, h))
        if found is not None:
            again = _settle(found[0], found[1], (w, h), pose, hfov, seat, reach / self.unit)
            if again[2] >= inliers:
                pose, hfov, inliers, rmse = again
                n_pairs = found[2]
        conf = confidence(inliers, 0, rmse, self.noise)
        ok = inliers >= MIN_INLIERS and conf >= OK_CONFIDENCE and self.plausible(pose.position)
        zoom = base / math.tan(math.radians(hfov) / 2)
        fix = Fix(
            ok,
            pose,
            inliers=inliers,
            matches=n_pairs,
            rmse=rmse,
            confidence=conf if ok else min(conf, 0.3),
            seconds=time.monotonic() - started,
            note="" if ok else "zoomed view: not confident enough",
            candidates=[Candidate(pose.position.copy(), pose.yaw, pose.pitch, inliers, rmse)],
        )
        return fix, zoom

    def _refine(self, query: Keypoints, best: _Solve, K: np.ndarray, size: tuple[int, int]) -> _Solve:
        """Render at the solved pose, match again, solve again; while it gains inliers and stays possible."""
        for _ in range(self.refine):
            yaw, pitch, _ = angles(best.rotation)
            r = self.renderer.render(Pose(best.position, yaw, pitch), self.hfov, self.light)
            s = self._solve(query, r, K, size)
            if s is None or s.inliers < best.inliers or not self.plausible(s.position):
                break
            moved = np.linalg.norm(s.position - best.position)
            best = s
            if moved < 0.05 / self.unit:
                break
        return best

    def plausible(self, position: np.ndarray) -> bool:
        """At a player's eye height over a floor, and not inside geometry."""
        return self._possible(*self.renderer.below(position))

    def _possible(self, nearest: float, typical: float, front: float) -> bool:
        """Some floor within reach under the eye, none closer than the lowest eye height, not inside geometry."""
        lo, hi = self.above_floor
        return nearest <= hi and typical >= lo and front > 0.5

    def close(self) -> None:
        self.renderer.release()


def fit_hfov(
    locator: "Locator",
    items: list[tuple[np.ndarray, np.ndarray | None, Pose]],
    *,
    start: float | None = None,
) -> tuple[float | None, list[float]]:
    """
    The horizontal field of view a recording was made with, from its own
    frames. For each (frame RGB, mask, solid fix) the level is rendered at the
    fix, matched and solved; then the pose and the focal length are refined
    together on the inliers, minimising the reprojection error. The focal
    length is pinned down by the depth in the scene - near and far points
    move differently under a change of focal length and of position - so
    each frame gives an estimate, and the median of them is the answer.
    Returns it (None when no frame could be solved) and the per-frame values.
    """
    import cv2
    from scipy.optimize import least_squares

    hfov0 = start or locator.hfov
    found: list[float] = []
    for rgb, mask, pose in items:
        h0, w0 = rgb.shape[:2]
        w = locator.width
        h = int(round(h0 * w / w0))
        small = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
        m = None if mask is None else cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
        query = locator.matcher.detect(normalise(small, locator.normalisation), m)
        locator.renderer.resize(w, h)
        render = locator.renderer.render(Pose(pose.position, pose.yaw, pose.pitch), hfov0, locator.light)
        s = locator._solve(query, render, intrinsics(w, h, hfov0), (w, h))
        if s is None or s.inliers < MIN_INLIERS or s.points is None:
            continue
        yaw, pitch, _ = angles(s.rotation)
        start_pose = Pose(s.position, yaw, pitch)
        scale = max(1.0, float(np.median(np.linalg.norm(s.points - s.position, axis=1))))
        f0 = intrinsics(w, h, hfov0)[0, 0]

        def residual(x: np.ndarray) -> np.ndarray:
            K = intrinsics(w, h, hfov0)
            K[0, 0] = K[1, 1] = f0 * math.exp(x[5])
            q = Pose(start_pose.position + x[:3] * scale, start_pose.yaw + x[3], start_pose.pitch + x[4])
            return (_project(s.points, K, q) - s.pixels).ravel()

        fit = least_squares(residual, np.zeros(6), loss="huber", f_scale=2.0, max_nfev=200, x_scale=[0.01, 0.01, 0.01, 1.0, 1.0, 0.05])
        f = f0 * math.exp(fit.x[5])
        found.append(math.degrees(2 * math.atan((w / 2) / f)))
    if not found:
        return None, found
    return float(np.median(found)), found


def _spread(pixels: np.ndarray | None, w: int, h: int, cells: int = 8) -> float:
    if pixels is None or not len(pixels):
        return 0.0
    gx = np.clip((pixels[:, 0] / w * cells).astype(int), 0, cells - 1)
    gy = np.clip((pixels[:, 1] / h * cells).astype(int), 0, cells - 1)
    return len(set(zip(gx.tolist(), gy.tolist()))) / float(cells * cells)


def _project(points: np.ndarray, K: np.ndarray, pose: Pose) -> np.ndarray:
    cam = (points - pose.position) @ pose.rotation().T
    z = np.maximum(cam[:, 2], 1e-6)
    return np.stack([K[0, 0] * cam[:, 0] / z + K[0, 2], K[1, 1] * cam[:, 1] / z + K[1, 2]], axis=1)


def _aim(points: np.ndarray, uv: np.ndarray, seat: np.ndarray, size: tuple[int, int], hfov: float, reach: float):
    """
    The direction and field of view a camera at `seat` saw these level points
    at these pixels with: (pose, hfov, inliers, rms error in degrees), or None.

    For each field of view round `hfov` the pixels become rays; a rotation
    from the level's directions to the rays is fitted to two of them at a time
    (RANSAC), then to all that agree, roll held at 0. Agreeing means within an
    angle that allows for the seat being up to `reach` off, for a point that
    far away.
    """
    w, h = size
    d = points - seat
    dist = np.linalg.norm(d, axis=1)
    use = dist > 1e-6
    if use.sum() < 8:
        return None
    d, dist, uv = d[use] / dist[use, None], dist[use], uv[use]
    tol = np.radians(0.6) + 0.5 * np.arctan2(reach, np.maximum(dist, reach))
    rng = np.random.default_rng(0)
    best = None
    for scale in np.linspace(0.75, 1.3, 23):
        hf = math.degrees(2 * math.atan(math.tan(math.radians(hfov) / 2) * scale))
        f = (w / 2) / math.tan(math.radians(hf) / 2)
        rays = np.stack([(uv[:, 0] - w / 2) / f, (uv[:, 1] - h / 2) / f, np.ones(len(uv))], axis=1)
        rays /= np.linalg.norm(rays, axis=1, keepdims=True)
        top = None
        for _ in range(150):
            i, j = rng.choice(len(d), 2, replace=False)
            R = _kabsch(d[[i, j]], rays[[i, j]])
            if R is None:
                continue
            a = np.arccos(np.clip(np.sum((d @ R.T) * rays, axis=1), -1, 1))
            inl = a < tol
            if top is None or inl.sum() > top.sum():
                top = inl
        if top is None or top.sum() < 3:
            continue
        R = _kabsch(d[top], rays[top])
        if R is None:
            continue
        yaw, pitch, _ = angles(R)
        R = Pose(seat, yaw, pitch).rotation()
        a = np.arccos(np.clip(np.sum((d @ R.T) * rays, axis=1), -1, 1))
        inl = a < tol
        n = int(inl.sum())
        if best is None or n > best[2]:
            err = float(np.degrees(np.sqrt(np.mean(a[inl] ** 2)))) if n else 90.0
            best = (Pose(seat.copy(), yaw, pitch), hf, n, err, np.flatnonzero(use)[inl])
    return best


def _settle(points: np.ndarray, uv: np.ndarray, size: tuple[int, int], start: Pose, hfov: float, seat: np.ndarray, reach: float):
    """
    From a direction and zoom found at `seat`: position, yaw, pitch and field
    of view together, minimising the reprojection error (robustly), the
    position held to within about `reach` of the seat. Returns (pose, hfov,
    inliers, rmse in pixels) counted over all `points`.
    """
    from scipy.optimize import least_squares

    w, h = size
    f0 = (w / 2) / math.tan(math.radians(hfov) / 2)

    def pose_of(x: np.ndarray) -> Pose:
        return Pose(start.position + x[:3] * reach, start.yaw + x[3], max(-89.0, min(89.0, start.pitch + x[4])))

    def residual(x: np.ndarray) -> np.ndarray:
        K = np.array([[f0 * math.exp(x[5]), 0, w / 2], [0, f0 * math.exp(x[5]), h / 2], [0, 0, 1.0]])
        r = (_project(points, K, pose_of(x)) - uv).ravel()
        # The seat is known to about `reach`: a pixel's worth of cost per `reach` moved.
        return np.concatenate([r, 2.0 * x[:3]])

    fit = least_squares(residual, np.zeros(6), loss="huber", f_scale=2.0, max_nfev=80, x_scale=[0.1, 0.1, 0.1, 1.0, 1.0, 0.05])
    pose = pose_of(fit.x)
    f = f0 * math.exp(fit.x[5])
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1.0]])
    e = np.linalg.norm(_project(points, K, pose) - uv, axis=1)
    keep = e < PIXELS
    rmse = float(np.sqrt(np.mean(e[keep] ** 2))) if keep.any() else float("inf")
    return pose, math.degrees(2 * math.atan((w / 2) / f)), int(keep.sum()), rmse


def _kabsch(a: np.ndarray, b: np.ndarray) -> np.ndarray | None:
    """The rotation taking unit vectors `a` (rows) closest to `b`."""
    U, S, Vt = np.linalg.svd(b.T @ a)
    if S[1] < 1e-9:
        return None
    D = np.diag([1.0, 1.0, np.sign(np.linalg.det(U @ Vt))])
    return U @ D @ Vt


def _level_refine(points: np.ndarray, uv: np.ndarray, K: np.ndarray, start: Pose) -> tuple[Pose, float]:
    """Position, yaw and pitch minimising the reprojection error (robustly), roll held at 0."""
    from scipy.optimize import least_squares

    scale = max(1.0, float(np.median(np.linalg.norm(points - start.position, axis=1))))

    def residual(x: np.ndarray) -> np.ndarray:
        pose = Pose(start.position + x[:3] * scale, start.yaw + x[3], start.pitch + x[4])
        return (_project(points, K, pose) - uv).ravel()

    fit = least_squares(residual, np.zeros(5), loss="huber", f_scale=2.0, max_nfev=60, x_scale=[0.01, 0.01, 0.01, 1.0, 1.0])
    x = fit.x
    pose = Pose(start.position + x[:3] * scale, start.yaw + x[3], max(-89.0, min(89.0, start.pitch + x[4])))
    return pose, float(np.sqrt(np.mean(fit.fun**2)))
