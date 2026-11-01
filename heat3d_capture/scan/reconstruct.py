"""
The middle of the pipeline: keyframes in, geometry and a coverage report out.

Separate from `ScanSession` because the session's job is capture and pacing, and
this one's is geometry. Keeping them apart means a recorded scan can be
re-reconstructed with different settings without capturing again — which is the
only practical way to tune any of the numbers below, since the alternative is
walking the level again for every experiment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..capture.flowmask import FlowMask
from ..capture.quality import Advice, QualityWatcher
from ..capture.screenmask import ScreenMask
from ..fusion.coverage import CoverageGrid, WeakSpot
from ..fusion.texture import KeyframeStore, project_colours
from ..fusion.volume import SurfaceVolume, mesh_to_parts
from ..pose.groundscale import DRIVING_HEIGHT, GROUND_BAND, GROUND_WIDTH, GroundCalibrator
from ..pose.odometry import Intrinsics, Trajectory, VisualOdometry

#: Take every Nth pixel when back-projecting. A 960x540 frame is half a million
#: points, and neighbouring pixels of one surface are not half a million
#: independent measurements — they are one surface sampled densely. Every second
#: pixel in each direction keeps the shape and quarters the cost.
PIXEL_STRIDE = 2

#: Depth beyond this is dropped. Monocular error grows roughly with the square of
#: distance, so distant points contribute noise shaped like geometry — a smeared
#: shell behind everything real, which is worse than a hole.
MAX_DEPTH = 60.0

#: And below this, nothing is real: the near field of a game frame is the weapon
#: model, the HUD, and the car's own bonnet, none of which are level geometry.
MIN_DEPTH = 0.35

#: Frames gathered before the flow-based mask can decide anything. Long enough
#: that a world feature has visibly travelled and an instrument has not.
FLOW_WARMUP = 40


@dataclass
class ReconstructionState:
    """What the reconstruction knows so far. Read live by the interface."""

    frames: int = 0
    #: Frames whose camera position is known. With telemetry this is every frame
    #: that arrived while the feed was live.
    tracked: int = 0
    #: Frames that actually contributed geometry. Always at most `tracked`: a
    #: frame can be perfectly located and still have nothing fusable, when its
    #: depth could not be tied to a scale.
    #:
    #: Counted apart because conflating the two made the telemetry path report
    #: nine frames in ten as *lost* when every one of them was positioned
    #: exactly — the pose was never in doubt, only the depth scale.
    fused: int = 0
    lost: int = 0
    surface_voxels: int = 0
    coverage_voxels: int = 0
    well_observed: float = 0.0
    mean_quality: float = 0.0
    trajectory_length: float = 0.0
    weak_spots: list[WeakSpot] = field(default_factory=list)
    #: Places the driver marked by hand (the mark hotkey), as camera positions
    #: in the scan's world, in metres. Drawn on the maps, listed, and saved with
    #: the level (see `Reconstructor.export`).
    marked: list[np.ndarray] = field(default_factory=list)
    last_reason: str = ""
    #: How much of the frame is being ignored as HUD or camera-mounted.
    masked_fraction: float = 0.0
    mask_note: str = ""
    #: How the global scale was fixed, or why it was not.
    scale_note: str = ""
    #: False when the capture geometry itself makes reconstruction impossible.
    reconstructable: bool = True
    capture_note: str = ""
    relocalisations: int = 0
    loop_closures: int = 0
    #: Sharpness of the last frame as a fraction of this capture's own median.
    #: 1.0 is typical for the capture; well below is motion blur.
    sharpness: float = 1.0
    #: One instruction for the user, chosen by what is most wrong right now.
    advice: str = ""
    #: "ok", "warn" or "stop", so the overlay can colour it without parsing.
    advice_level: str = "ok"

    @property
    def tracking_health(self) -> float:
        """Fraction of frames whose camera was located."""
        return self.tracked / self.frames if self.frames else 0.0

    @property
    def fusion_health(self) -> float:
        """Fraction of located frames that could actually be fused."""
        return self.fused / self.tracked if self.tracked else 0.0


class Reconstructor:
    """
    Accumulates keyframes into a surface and a coverage map.

    Both grids are updated on every keyframe rather than at the end, because the
    coverage map is the thing the user steers by while walking. A reconstruction
    that only reports at the end can tell someone their scan was poor; this one
    can tell them in time to fix it.
    """

    def __init__(
        self,
        intrinsics: Intrinsics,
        *,
        voxel: float = 0.25,
        coverage_voxel: float = 0.5,
        mask_hud: bool = True,
        pose_source=None,
        keep_for_texture: int = 160,
        camera_height: float | None = DRIVING_HEIGHT,
        loop_closure: bool = False,
    ):
        self.k = intrinsics
        self.odometry = VisualOdometry(intrinsics, loop_closure=loop_closure)
        self.volume = SurfaceVolume(voxel=voxel)
        self.coverage = CoverageGrid(voxel=coverage_voxel)
        self.screen = ScreenMask() if mask_hud else None
        #: The better of the two detectors. Change-based masking asks which
        #: pixels stay the same, and a cockpit does not: needles sweep, minimaps
        #: rotate. This asks which features persist without *travelling*, which
        #: is what belongs to the camera however it is animated. Measured on real
        #: footage it left features with a median travel of 58 px against 5 px.
        self.flow = FlowMask() if mask_hud else None
        self._warmup: list = []
        #: Something that can answer "where was the camera at time t" exactly —
        #: a telemetry feed. When it answers, its pose is used instead of the
        #: visual solve; when it cannot (a gap in the feed), the frame is placed
        #: visually, carrying on from the last pose it gave.
        self.pose_source = pose_source
        #: Frames held back to colour the finished mesh. Bounded and spread
        #: across the whole scan, not the most recent ones.
        self.keyframes = KeyframeStore(limit=keep_for_texture) if keep_for_texture else None
        #: Metres the camera sits above the ground, used once to fix the global
        #: scale. None leaves the reconstruction unit-less but self-consistent.
        self.camera_height = camera_height
        self._ground = (
            GroundCalibrator(intrinsics, height=camera_height)
            if camera_height is not None
            else None
        )
        #: Metres per unit of the level as fused, applied when it is written.
        #: 1 when the scale was fixed before the origin (the first frame had
        #: ground to measure); otherwise the factor a later keyframe's ground
        #: found, since everything already fused is in the first frame's unit.
        self.metres_per_unit = 1.0
        self.state = ReconstructionState()
        #: Judges each frame as it arrives, so the overlay can say "slow down"
        #: while there is still time to slow down. Cheap: one Laplacian pass.
        self.quality = QualityWatcher()
        self._pixels = self._pixel_grid()

    def _pixel_grid(self) -> np.ndarray:
        ys, xs = np.mgrid[0 : self.k.height : PIXEL_STRIDE, 0 : self.k.width : PIXEL_STRIDE]
        return np.stack([xs.ravel(), ys.ravel()], axis=1).astype(np.float64)

    def add(
        self,
        image: np.ndarray,
        inverse_depth: np.ndarray,
        *,
        timestamp: float | None = None,
    ) -> ReconstructionState:
        """Locate one keyframe and fuse it. Safe to call from a worker thread."""
        self.state.frames += 1

        mask = None
        if self.flow is not None and not self.flow.ready:
            import cv2

            self._warmup.append(
                cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
            )
            if len(self._warmup) >= FLOW_WARMUP:
                self.flow.observe_sequence(self._warmup)
                self._warmup = []

        if self.flow is not None and self.flow.ready:
            mask = self.flow.mask(image.shape[:2])
            self.state.mask_note = self.flow.describe()
            self.state.masked_fraction = 0.0 if mask is None else float((mask == 0).mean())
        elif self.screen is not None:
            # Only learn from frames where the camera actually moved. A parked
            # camera makes everything static, and learning from that would teach
            # the detector that the whole level is a HUD.
            # Used only until the flow detector has seen enough, so a scan is
            # not blind for its first second.
            self.screen.update(image, moving=self.state.tracked > 0)
            mask = self.screen.mask(image.shape[:2])
            self.state.masked_fraction = self.screen.static_fraction()
            self.state.mask_note = self.screen.describe()

        # Judged on the world, not on the dashboard: an instrument panel is
        # always perfectly sharp and would make a hopelessly blurred road read
        # as crisp.
        measured = self.quality.observe(image, mask=mask)
        self.state.sharpness = measured.relative

        if self._ground is not None and self.state.frames == 1:
            # Once, on the very first frame, before the origin's unit is read and
            # before anything inherits it.
            #
            # An earlier version gathered five frames and then reset the tracker
            # to re-base the chain. That worked and was a bad idea: it silently
            # discarded the opening of every scan and restarted tracking, which
            # broke eleven tests that quite reasonably expected every frame to be
            # placed. One frame is enough — measured across three minutes of real
            # driving, single-frame estimates agreed to within 6%.
            fit = self._ground.offer(inverse_depth)
            self.state.scale_note = self._ground.note
            if fit is not None:
                self.odometry._origin_fit = fit

        known = None
        if self.pose_source is not None and timestamp is not None:
            known = self.pose_source.at(timestamp)
            if known is not None:
                self.state.scale_note = "in metres, from the telemetry's positions"

        result = self.odometry.track(image, inverse_depth, known_pose=known, mask=mask)
        self.state.relocalisations = self.odometry.relocalisations
        self.state.loop_closures = self.odometry.loop_closures

        if not result.tracked:
            self.state.lost += 1
            self.state.last_reason = result.reason
            self._advise()
            return self.state

        self.state.tracked += 1
        self.state.last_reason = ""
        self._advise()
        if result.fit is not None and self.state.frames > 1:
            self._measure_ground_later(inverse_depth, result.fit)
        if result.fit is None:
            # Located but not fusable: the camera is where the feed says, and
            # nothing in this frame can be tied to a scale yet. Not a loss, and
            # not something to fuse either.
            self.state.last_reason = "positioned, but its depth has no scale yet"
            return self.state

        metric = result.fit.apply(inverse_depth)
        rows = self._pixels[:, 1].astype(int)
        cols = self._pixels[:, 0].astype(int)
        depths = metric[rows, cols]
        usable = np.isfinite(depths) & (depths > MIN_DEPTH) & (depths < MAX_DEPTH)
        if mask is not None:
            # The second half of the masking job: a weapon model is real geometry
            # in the wrong coordinate system, and fusing it smears a gun barrel
            # along the whole path walked.
            usable &= mask[rows, cols] > 0
        if not usable.any():
            return self.state

        pixels = self._pixels[usable]
        camera_points = self.k.unproject(pixels, depths[usable])
        world = result.pose.to_world(camera_points)

        colours = None
        if image.ndim == 3:
            colours = (
                image[pixels[:, 1].astype(int), pixels[:, 0].astype(int)].astype(np.float32) / 255.0
            )

        # Weighted by how well the camera was located. Geometry fused with a
        # doubtful pose lands in the wrong place, and letting it push the surface
        # around as hard as a confident frame is how a scan degrades silently.
        self.volume.integrate(world, weight=max(0.1, result.confidence), colours=colours)
        self.coverage.observe(world, result.pose.translation, confidence=result.confidence)
        self.state.fused += 1
        if self.keyframes is not None and image.ndim == 3:
            self.keyframes.add(image, result.pose)

        # Checked periodically rather than every frame: it walks the whole grid,
        # and the answer does not change between one keyframe and the next.
        if self.state.fused % 25 == 0:
            ok, note = self.coverage.reconstructable()
            self.state.reconstructable = ok
            self.state.capture_note = note

        summary = self.coverage.summary()
        self.state.surface_voxels = len(self.volume)
        self.state.coverage_voxels = summary["voxels"]
        self.state.well_observed = summary["well_observed"]
        self.state.mean_quality = summary["mean_quality"]
        self.state.trajectory_length = self.trajectory.length * self.metres_per_unit
        return self.state

    def _measure_ground_later(self, inverse_depth: np.ndarray, chained) -> None:
        """
        Try the ground again on a later keyframe, when the first had none.

        The origin is already fixed by then and everything fused is in its
        unit, so the scale is not fed back into the chain. It is measured here
        as metres per unit — what this frame's ground says its depth is, over
        what the chain says it is — and applied to the whole level when it is
        written, and to the distances shown meanwhile.
        """
        ground = self._ground
        # Not with telemetry: its positions are in metres already, and each
        # frame's depth is anchored to them (`VisualOdometry._with_known_pose`).
        if self.pose_source is not None or ground is None or ground.settled or ground.gave_up:
            return
        fit = ground.offer(inverse_depth)
        self.state.scale_note = ground.note
        if fit is None:
            return
        h, w = inverse_depth.shape[:2]
        band = inverse_depth[
            int(h * GROUND_BAND[0]) : int(h * GROUND_BAND[1]),
            int(w * GROUND_WIDTH[0]) : int(w * GROUND_WIDTH[1]),
        ]
        metres = fit.apply(band)
        units = chained.apply(band)
        usable = np.isfinite(metres) & np.isfinite(units) & (units > 1e-9)
        if not usable.any():
            return
        self.metres_per_unit = float(np.median(metres[usable] / units[usable]))
        self.state.scale_note = (
            f"{ground.note}; found on frame {self.state.frames}, so the level is "
            f"scaled by {self.metres_per_unit:.3g} when it is written"
        )

    def _advise(self) -> None:
        """Refresh the live instruction. Called on every frame, tracked or not."""
        advice: Advice = self.quality.advise(self.state)
        self.state.advice = advice.text
        self.state.advice_level = advice.level

    def refresh_weak_spots(self) -> list[WeakSpot]:
        """
        Recompute the places worth revisiting.

        Kept off the per-frame path: it clusters the whole grid, which is cheap
        in absolute terms and not cheap enough to do sixty times a second. The
        interface calls it on a slower timer.
        """
        self.state.weak_spots = self.coverage.weak_spots()
        return self.state.weak_spots

    @property
    def trajectory(self) -> Trajectory:
        return Trajectory(poses=self.odometry.poses, results=self.odometry.results)

    def mark(self) -> np.ndarray | None:
        """
        Note where the camera is now as a place to come back to.

        For what the driver noticed and the coverage metric cannot see — a
        corner taken badly, a stretch where the view was blocked. None when no
        frame has been placed yet, so there is nowhere to mark.
        """
        positions = self.trajectory.positions
        if len(positions) == 0:
            return None
        here = np.array(positions[-1], dtype=np.float64)
        self.state.marked.append(here)
        return here

    def export(self, path: str | Path, *, name: str = "scan") -> Path | None:
        """
        Write the level. Returns None when there is nothing worth writing.

        None rather than an empty file, because an empty `.glb` in the output
        folder reads as a successful scan that produced nothing, and that is a
        harder thing to debug than an honest refusal.

        Spots marked by hand go beside it as `<name>.marks.json`, in the same
        coordinates as the level (see `write_marks`).
        """
        from ..geometry.glb import METRES_TO_VIEWER, write_glb

        mesh = self.volume.to_mesh()
        if mesh.is_empty():
            return None

        # Colour projected from the frames that saw each vertex best, rather than
        # the voxel average fusion produced along the way. Skipped when no frames
        # were kept, in which case the voxel colour is what there is.
        colours = None
        if self.keyframes is not None and len(self.keyframes):
            colours = project_colours(
                mesh.vertices,
                mesh.normals,
                self.keyframes.frames,
                self.k,
                fallback=mesh.colours,
            )

        parts = mesh_to_parts(mesh, name=name, colours=colours)
        if not parts:
            return None
        written = write_glb(
            path,
            parts,
            scale=METRES_TO_VIEWER * self.metres_per_unit,
            generator="heat3d-capture-scan",
        )
        if self.state.marked:
            write_marks(written, [m * self.metres_per_unit for m in self.state.marked])
        return written


def marks_path(level: str | Path) -> Path:
    """Where the hand-marked spots of a level are kept: beside it."""
    level = Path(level)
    return level.with_name(level.stem + ".marks.json")


def write_marks(level: str | Path, marked) -> Path:
    """
    The hand-marked spots of a scan, beside its level.

    Each in the level's own coordinates (the GLB's scale applied, so a mark
    sits on the mesh it was made over) and in metres, numbered as the window
    lists them.
    """
    import json

    from ..geometry.glb import METRES_TO_VIEWER

    path = marks_path(level)
    marks = [
        {
            "number": i,
            "position": [round(float(v) * METRES_TO_VIEWER, 3) for v in where],
            "metres": [round(float(v), 4) for v in where],
        }
        for i, where in enumerate(marked, start=1)
    ]
    path.write_text(
        json.dumps(
            {
                "format": "heat3d-scan-marks",
                "version": 1,
                "level": Path(level).name,
                "scale": METRES_TO_VIEWER,
                "marks": marks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
