"""
The player's own track, from a minimap that turns with them.

A player-centred minimap is a moving window onto one fixed picture of the
level. Each sampled minimap is registered onto a mosaic of the ones before it
with a similarity transform (turn, zoom, shift); the player's fixed point on
the minimap, carried through that transform, is where they were on the mosaic,
and the turn is which way they faced.

Registering to the mosaic rather than to the previous frame is what keeps the
track from wandering: errors do not add up frame by frame, and coming back to a
place lands on the features stored the first time it was seen. The mosaic is
held as features (SIFT keypoints in mosaic coordinates) for registration and as
an averaged picture for the output.

What is masked, because it does not belong to the level:

- anything strongly coloured or near white: objective markers, squad and
  vehicle icons, pings, the play-area boundary, the dotted route lines, the
  sector name, the key hint;
- a disc round the player's point (their own marker) and the view cone above
  it, which stay put on the screen while the map turns under them.

A spawn somewhere not seen before cannot be placed on the mosaic. It starts an
island of its own, which is joined to the main one as soon as a minimap of it
matches the main one (a road both have seen); islands never joined stay apart
and are reported as such.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# Colour above which a pixel is an overlay rather than the map: the spread of
# its channels (0-255). The map is dark, grey-blue and quiet; markers are not.
CHROMA_LIMIT = 52
# Brightness above which a pixel is an overlay (white icons, text).
BRIGHT_LIMIT = 205


@dataclass
class Pose:
    """Where one minimap sits on the mosaic: mosaic = A @ [x, y, 1] for a minimap pixel."""

    A: np.ndarray
    inliers: int
    island: int

    @property
    def scale(self) -> float:
        return float(math.hypot(self.A[0, 0], self.A[1, 0]))

    @property
    def angle(self) -> float:
        """Degrees clockwise (on screen, y down) from the mosaic's up to the minimap's up."""
        # The minimap's up (0, -1) carried into the mosaic.
        ux, uy = -self.A[0, 1], -self.A[1, 1]
        return math.degrees(math.atan2(ux, -uy)) % 360.0

    def apply(self, x: float, y: float) -> tuple[float, float]:
        p = self.A @ np.array([x, y, 1.0])
        return float(p[0]), float(p[1])


def compose(outer: np.ndarray, inner: np.ndarray) -> np.ndarray:
    """2x3 transforms: `outer` after `inner`."""
    a = np.vstack([outer, [0, 0, 1]])
    b = np.vstack([inner, [0, 0, 1]])
    return (a @ b)[:2]


def invert(A: np.ndarray) -> np.ndarray:
    return np.linalg.inv(np.vstack([A, [0, 0, 1]]))[:2]


def overlay_mask(image: np.ndarray, player: tuple[float, float], key: tuple[float, float, float, float] | None) -> np.ndarray:
    """255 where the pixel is the level's own picture, 0 where something is drawn over it."""
    import cv2

    h, w = image.shape[:2]
    mx = image.max(axis=2).astype(np.int16)
    mn = image.min(axis=2).astype(np.int16)
    keep = ((mx - mn) < CHROMA_LIMIT) & (mx < BRIGHT_LIMIT)
    # The view cone is a faint yellow-green wash over the blue-grey map.
    b = image[..., 0].astype(np.int16)
    g = image[..., 1].astype(np.int16)
    keep &= ~((g - b) > 10)
    mask = keep.astype(np.uint8) * 255
    # Edges of markers are blended into the map; grow the holes a little.
    mask = cv2.erode(mask, np.ones((5, 5), np.uint8))
    px, py = player[0] * w, player[1] * h
    cv2.circle(mask, (int(px), int(py)), int(0.075 * w), 0, -1)
    # The cone: a wedge above the player that never turns on screen.
    cone = np.array(
        [[px, py], [px - 0.16 * w, py - 0.36 * h], [px + 0.16 * w, py - 0.36 * h]], np.int32
    )
    cv2.fillConvexPoly(mask, cone, 0)
    if key is not None:
        kx, ky, kw, kh = key
        pad = 0.02
        cv2.rectangle(
            mask,
            (int((kx - pad) * w), int((ky - pad) * h)),
            (int((kx + kw + pad) * w), int((ky + kh + pad) * h)),
            0, -1,
        )
    # The rim: markers clamped to the edge, and the edge's own anti-aliasing.
    rim = int(0.03 * w)
    mask[:rim] = 0
    mask[-rim:] = 0
    mask[:, :rim] = 0
    mask[:, -rim:] = 0
    return mask


def key_present(image: np.ndarray, key: tuple[float, float, float, float]) -> bool:
    """
    Is the minimap's key-hint square there: a light, colourless square with a dark letter in it.

    It is drawn whenever the minimap is, and nowhere on a death or deploy
    screen, so it is the cheap test for "the player is in play". Searched a few
    pixels around its place because the minimap's frame moves slightly when
    it zooms.
    """
    import cv2

    h, w = image.shape[:2]
    kx, ky, kw, kh = key
    x0, y0 = int(kx * w), int(ky * h)
    bw, bh = max(4, int(kw * w)), max(4, int(kh * h))
    pad = max(2, int(0.025 * w))
    xa, ya = max(0, x0 - pad), max(0, y0 - pad)
    patch = image[ya : min(h, y0 + bh + pad), xa : min(w, x0 + bw + pad)]
    if patch.size == 0:
        return False
    grey = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY).astype(np.float32)
    chroma = (patch.max(axis=2).astype(np.int16) - patch.min(axis=2).astype(np.int16))
    light = ((grey > 130) & (chroma < 40)).astype(np.float32)
    # Box filter: the fraction of light pixels in each box-sized window.
    frac = cv2.boxFilter(light, -1, (bw, bh), normalize=True, borderType=cv2.BORDER_CONSTANT)
    yy, xx = np.unravel_index(int(np.argmax(frac)), frac.shape)
    best = float(frac[yy, xx])
    if best < 0.55 or best > 0.95:
        # Mostly light but not entirely: the letter takes a bite out of the square.
        return False
    cx, cy = xx, yy
    inner = grey[max(0, cy - bh // 4) : cy + bh // 4 + 1, max(0, cx - bw // 4) : cx + bw // 4 + 1]
    if inner.size == 0 or float((inner < 90).mean()) < 0.08:
        return False
    # The square stands out from what is round it - which is usually the dark map,
    # but can be a lighter tinted area (a team's sector), so the test is contrast.
    ring = np.concatenate([grey[:, :2].ravel(), grey[:, -2:].ravel(), grey[:2].ravel(), grey[-2:].ravel()])
    box = grey[max(0, cy - bh // 2) : cy + bh // 2 + 1, max(0, cx - bw // 2) : cx + bw // 2 + 1]
    lit = box[box > 130]
    return len(lit) > 0 and float(np.median(ring)) < float(np.median(lit)) - 40


@dataclass
class Island:
    """One connected mosaic: its features and its picture."""

    number: int
    points: np.ndarray = field(default_factory=lambda: np.zeros((0, 2), np.float32))
    descriptors: np.ndarray = field(default_factory=lambda: np.zeros((0, 128), np.float32))
    #: The picture: running sums of colour and weight, on a canvas whose pixel (0, 0)
    #: is mosaic point `origin`.
    colour: np.ndarray | None = None
    weight: np.ndarray | None = None
    origin: np.ndarray = field(default_factory=lambda: np.zeros(2))
    #: Where it was joined to, and how: island coordinates -> that island's.
    joined_to: int | None = None
    frames: int = 0

    def add_points(self, pts: np.ndarray, desc: np.ndarray) -> None:
        if len(pts):
            self.points = np.vstack([self.points, pts.astype(np.float32)])
            self.descriptors = np.vstack([self.descriptors, desc.astype(np.float32)])

    def paint(self, image: np.ndarray, mask: np.ndarray, A: np.ndarray) -> None:
        """Average the minimap's unmasked pixels into the picture."""
        import cv2

        h, w = image.shape[:2]
        corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], np.float64) @ A.T
        lo = np.floor(corners.min(axis=0)) - 2
        hi = np.ceil(corners.max(axis=0)) + 2
        self._grow(lo, hi)
        ox, oy = self.origin
        x0, y0 = int(lo[0] - ox), int(lo[1] - oy)
        x1, y1 = int(hi[0] - ox), int(hi[1] - oy)
        shift = np.array([[1, 0, -lo[0]], [0, 1, -lo[1]]], np.float64)
        M = compose(shift, A)
        size = (x1 - x0, y1 - y0)
        warped = cv2.warpAffine(image, M, size, flags=cv2.INTER_LINEAR, borderValue=0)
        wmask = cv2.warpAffine(mask, M, size, flags=cv2.INTER_NEAREST, borderValue=0)
        wt = (wmask > 0).astype(np.float32)
        self.colour[y0:y1, x0:x1] += warped.astype(np.float32) * wt[..., None]
        self.weight[y0:y1, x0:x1] += wt

    def _grow(self, lo: np.ndarray, hi: np.ndarray) -> None:
        """Make the canvas cover mosaic points lo..hi, growing in steps so it is not copied every frame."""
        step = 512
        if self.colour is None:
            self.origin = np.floor(lo / step) * step
            top = np.ceil(hi / step) * step
            size = (top - self.origin).astype(int)
            self.colour = np.zeros((size[1], size[0], 3), np.float32)
            self.weight = np.zeros((size[1], size[0]), np.float32)
            return
        h, w = self.weight.shape
        have_lo = self.origin
        have_hi = self.origin + np.array([w, h])
        if (lo >= have_lo).all() and (hi <= have_hi).all():
            return
        new_lo = np.minimum(have_lo, np.floor(lo / step) * step)
        new_hi = np.maximum(have_hi, np.ceil(hi / step) * step)
        size = (new_hi - new_lo).astype(int)
        colour = np.zeros((size[1], size[0], 3), np.float32)
        weight = np.zeros((size[1], size[0]), np.float32)
        dx, dy = (have_lo - new_lo).astype(int)
        colour[dy : dy + h, dx : dx + w] = self.colour
        weight[dy : dy + h, dx : dx + w] = self.weight
        self.colour, self.weight, self.origin = colour, weight, new_lo

    def picture(self) -> np.ndarray | None:
        """The averaged mosaic; narrow holes left by masked overlays (a boundary line) filled from round them."""
        import cv2

        if self.colour is None:
            return None
        wt = np.maximum(self.weight, 1e-6)[..., None]
        out = np.clip(self.colour / wt, 0, 255).astype(np.uint8)
        seen = (self.weight >= 0.5).astype(np.uint8)
        closed = cv2.morphologyEx(seen, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        holes = (closed > 0) & (seen == 0)
        if holes.any():
            out = cv2.inpaint(out, holes.astype(np.uint8), 5, cv2.INPAINT_TELEA)
        out[closed == 0] = 0
        return out

    def absorb(self, other: "Island", M: np.ndarray) -> None:
        """Take another island's features and picture, `M` carrying its coordinates into these."""
        import cv2

        if len(other.points):
            pts = np.hstack([other.points, np.ones((len(other.points), 1), np.float32)]) @ M.T
            self.add_points(pts, other.descriptors)
        if other.colour is not None:
            h, w = other.weight.shape
            # Its canvas pixel -> its mosaic -> ours.
            to_ours = compose(M, np.array([[1, 0, other.origin[0]], [0, 1, other.origin[1]]], np.float64))
            corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], np.float64) @ to_ours.T
            lo = np.floor(corners.min(axis=0)) - 2
            hi = np.ceil(corners.max(axis=0)) + 2
            self._grow(lo, hi)
            ox, oy = self.origin
            x0, y0 = int(lo[0] - ox), int(lo[1] - oy)
            x1, y1 = int(hi[0] - ox), int(hi[1] - oy)
            Mc = compose(np.array([[1, 0, -lo[0]], [0, 1, -lo[1]]], np.float64), to_ours)
            size = (x1 - x0, y1 - y0)
            self.colour[y0:y1, x0:x1] += cv2.warpAffine(other.colour, Mc, size, flags=cv2.INTER_LINEAR)
            self.weight[y0:y1, x0:x1] += cv2.warpAffine(other.weight, Mc, size, flags=cv2.INTER_LINEAR)
        self.frames += other.frames


@dataclass
class TrackPoint:
    t: float
    #: Mosaic coordinates of the player, in the island's frame at the time of the fix.
    x: float
    y: float
    #: Degrees clockwise from the mosaic's up.
    heading: float
    scale: float
    inliers: int
    island: int
    #: The pose itself, so a later join can carry the point into another island.
    A: np.ndarray


class MinimapTracker:
    """
    Feed it minimaps in time order; it keeps the mosaic and the track.

    `work` is the size the minimap is registered at, in pixels. Keypoints are
    stored at the scale of the first minimap an island saw.
    """

    def __init__(
        self,
        player: tuple[float, float],
        key: tuple[float, float, float, float] | None,
        *,
        work: int = 296,
        min_inliers: int = 14,
        features: int = 900,
    ):
        import cv2

        self.player = player
        self.key = key
        self.work = work
        self.min_inliers = min_inliers
        self.sift = cv2.SIFT_create(nfeatures=features, contrastThreshold=0.02)
        self.matcher = cv2.BFMatcher(cv2.NORM_L2)
        self.islands: list[Island] = []
        self.track: list[TrackPoint] = []
        self.current: Island | None = None
        self.last: Pose | None = None
        self.last_key_A: np.ndarray | None = None
        self.last_key_t = -1e9
        self.lost_since: float | None = None
        #: Counters for the summary.
        self.seen = 0
        self.placed = 0
        self.rejected = 0
        self.out_of_play = 0

    # ------------------------------------------------------------------ input

    def prepare(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        import cv2

        if image.shape[0] != self.work:
            image = cv2.resize(image, (self.work, self.work), interpolation=cv2.INTER_AREA)
        return image, overlay_mask(image, self.player, self.key)

    def in_play(self, image: np.ndarray) -> bool:
        return True if self.key is None else key_present(image, self.key)

    def break_track(self) -> None:
        """The player left play (death, deploy screen): the next fix starts afresh."""
        self.last = None

    def add(self, t: float, image: np.ndarray) -> TrackPoint | None:
        """Register one minimap. Returns the player's point, or None when it could not be placed."""
        import cv2

        self.seen += 1
        image, mask = self.prepare(image)
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Local contrast: the map's detail is faint; equalising brings it to the detector.
        grey = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(grey)
        kps, desc = self.sift.detectAndCompute(grey, mask)
        if desc is None or len(kps) < self.min_inliers:
            self.rejected += 1
            return None
        pts = np.array([k.pt for k in kps], np.float32)

        pose = None
        if self.current is not None and len(self.current.points):
            pose = self._register(self.current, pts, desc, near=self.last)
            if pose is None and self.last is None:
                # Back in play after a gap: anywhere on this island.
                pose = self._register(self.current, pts, desc, near=None)
        if pose is None:
            for other in self.islands:
                if other is self.current or other.joined_to is not None or not len(other.points):
                    continue
                pose = self._register(other, pts, desc, near=None)
                if pose is not None:
                    self.current = other
                    break
        if pose is None and self.last is not None:
            # Still moving, but the mosaic here is thin: one more try against all of it.
            pose = self._register(self.current, pts, desc, near=None)
        if pose is None:
            if self.last is not None and self.current is not None:
                # Lost mid-play: a few misses are tolerated before giving up on continuity.
                self.rejected += 1
                if self.lost_since is None:
                    self.lost_since = t
                if t - self.lost_since < 3.0:
                    return None
            # Nowhere known: a new island, at this minimap's own coordinates.
            island = Island(number=len(self.islands))
            self.islands.append(island)
            self.current = island
            pose = Pose(A=np.array([[1.0, 0, 0], [0, 1.0, 0]]), inliers=len(pts), island=island.number)
            island.add_points(pts, desc)
            self.last_key_A = pose.A
            self.last_key_t = t
        else:
            self.lost_since = None
            self._maybe_keyframe(t, pose, pts, desc)
            pose = self._maybe_join(t, pose, pts, desc)
        island = self.islands[pose.island]
        island.frames += 1
        island.paint(image, mask, pose.A)
        self.last = pose
        self.placed += 1
        h, w = image.shape[:2]
        x, y = pose.apply(self.player[0] * w, self.player[1] * h)
        point = TrackPoint(
            t=t, x=x, y=y, heading=pose.angle, scale=pose.scale, inliers=pose.inliers,
            island=pose.island, A=pose.A.copy(),
        )
        self.track.append(point)
        return point

    # --------------------------------------------------------- registration

    def _register(self, island: Island, pts: np.ndarray, desc: np.ndarray, *, near: Pose | None) -> Pose | None:
        import cv2

        cand = np.arange(len(island.points))
        if near is not None:
            c = np.array(near.apply(self.work / 2, self.work / 2))
            radius = 1.2 * self.work * near.scale
            d = np.hypot(*(island.points - c).T)
            cand = cand[d < radius]
        if len(cand) < self.min_inliers:
            return None
        db = island.descriptors[cand]
        matches = self.matcher.knnMatch(desc.astype(np.float32), db, k=2)
        src, dst = [], []
        for m in matches:
            if len(m) < 2:
                continue
            a, b = m
            if a.distance < 0.82 * b.distance:
                src.append(pts[a.queryIdx])
                dst.append(island.points[cand[a.trainIdx]])
        if len(src) < 8:
            return None
        src = np.array(src, np.float32)
        dst = np.array(dst, np.float32)
        thresh = 3.0 * (near.scale if near is not None else 1.0)
        A, inl = cv2.estimateAffinePartial2D(
            src, dst, method=cv2.RANSAC, ransacReprojThreshold=thresh, maxIters=3000, confidence=0.995
        )
        if A is None:
            return None
        n = int(inl.sum())
        scale = math.hypot(A[0, 0], A[1, 0])
        if not (0.3 < scale < 3.0):
            return None
        if near is None:
            # A placement found anywhere on the island has to be convincing on its own.
            if n < self.min_inliers * 2:
                return None
        else:
            # Near the last fix a weaker match will do, as long as it agrees with
            # where the player can have got to: zoom does not jump by a third,
            # and the map does not slide by more than a third of itself, between samples.
            if n < max(8, int(self.min_inliers * 0.7)):
                return None
            if not (0.75 < scale / near.scale < 1.33):
                return None
            here = A @ np.array([self.work / 2, self.work / 2, 1.0])
            there = near.A @ np.array([self.work / 2, self.work / 2, 1.0])
            if math.hypot(*(here - there)) > 0.35 * self.work * near.scale:
                return None
        return Pose(A=A.astype(np.float64), inliers=n, island=island.number)

    def _maybe_keyframe(self, t: float, pose: Pose, pts: np.ndarray, desc: np.ndarray) -> None:
        """Store this minimap's features that the island does not have yet."""
        if self.last_key_A is not None:
            moved = np.hypot(*(pose.A[:, 2] - self.last_key_A[:, 2])) / max(pose.scale, 1e-6)
            turn = abs(((Pose(self.last_key_A, 0, 0).angle - pose.angle) + 180) % 360 - 180)
            if moved < 0.12 * self.work and turn < 25 and t - self.last_key_t < 4.0:
                return
        island = self.islands[pose.island]
        mapped = np.hstack([pts, np.ones((len(pts), 1), np.float32)]) @ pose.A.T
        if len(island.points):
            # Skip points the island already has within a couple of pixels.
            near = self.matcher.knnMatch(mapped.astype(np.float32), island.points.astype(np.float32), k=1)
            fresh = np.array([not m or m[0].distance > 2.5 * pose.scale for m in near])
        else:
            fresh = np.ones(len(pts), bool)
        island.add_points(mapped[fresh], desc[fresh])
        self.last_key_A = pose.A.copy()
        self.last_key_t = t

    def _maybe_join(self, t: float, pose: Pose, pts: np.ndarray, desc: np.ndarray) -> Pose:
        """Every so often, try this minimap on the other islands: one match joins them. Returns the pose, moved if its island was."""
        if len(self.islands) < 2 or self.placed % 10:
            return pose
        here = self.islands[pose.island]
        for other in self.islands:
            if other is here or other.joined_to is not None or not len(other.points):
                continue
            found = self._register(other, pts, desc, near=None)
            if found is None:
                continue
            # minimap -> other is `found.A`; minimap -> here is `pose.A`.
            # The smaller island moves into the larger one.
            if len(other.points) >= len(here.points):
                big, small, M = other, here, compose(found.A, invert(pose.A))
            else:
                big, small, M = here, other, compose(pose.A, invert(found.A))
            big.absorb(small, M)
            small.joined_to = big.number
            small.points = np.zeros((0, 2), np.float32)
            small.descriptors = np.zeros((0, 128), np.float32)
            small.colour = small.weight = None
            for p in self.track:
                if p.island == small.number:
                    p.A = compose(M, p.A)
                    p.x, p.y = (M @ np.array([p.x, p.y, 1.0])).tolist()
                    p.island = big.number
                    p.heading = Pose(p.A, 0, 0).angle
            if self.last_key_A is not None and here is small:
                self.last_key_A = compose(M, self.last_key_A)
            if self.last is not None and self.last.island == small.number:
                self.last = Pose(compose(M, self.last.A), self.last.inliers, big.number)
            self.current = big
            if pose.island == small.number:
                pose = Pose(compose(M, pose.A), pose.inliers, big.number)
            return pose
        return pose
