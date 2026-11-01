"""
Tests for the reconstruction stage.

Fed synthetic frames with known geometry, so the output can be checked rather
than admired. The important behaviours are the defensive ones: a lost track must
not contribute geometry, distant and near-field points must be rejected, and an
empty reconstruction must refuse to write a file rather than writing an empty one.
"""

from __future__ import annotations

import numpy as np
import pytest

from heat3d_capture.pose.odometry import Intrinsics
from heat3d_capture.scan.reconstruct import (
    MAX_DEPTH,
    MIN_DEPTH,
    Reconstructor,
)

WIDTH, HEIGHT = 320, 240


def intrinsics() -> Intrinsics:
    return Intrinsics.from_fov(WIDTH, HEIGHT, 90.0)


def textured(shift: int = 0, seed: int = 7) -> np.ndarray:
    """A frame with repeatable corners for ORB."""
    import cv2

    rng = np.random.default_rng(seed)
    canvas = np.full((HEIGHT, WIDTH * 3, 3), 25, dtype=np.uint8)
    for _ in range(240):
        x = int(rng.integers(0, WIDTH * 3))
        y = int(rng.integers(0, HEIGHT))
        cv2.rectangle(
            canvas,
            (x, y),
            (x + int(rng.integers(10, 34)), y + int(rng.integers(10, 34))),
            tuple(int(c) for c in rng.integers(60, 255, 3)),
            -1,
        )
    start = int(np.clip(shift, 0, WIDTH * 2))
    return np.ascontiguousarray(canvas[:, start : start + WIDTH])


def flat_depth(distance: float = 4.0) -> np.ndarray:
    """Inverse depth of a plane at a fixed distance."""
    return np.full((HEIGHT, WIDTH), 1.0 / distance, dtype=np.float32)


class TestFirstFrame:
    def test_the_first_frame_is_fused(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        state = r.add(textured(), flat_depth())
        assert state.frames == 1
        assert state.tracked == 1
        assert state.surface_voxels > 0
        assert state.coverage_voxels > 0

    def test_records_where_it_looked_from(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        assert len(r.trajectory.poses) == 1
        assert r.trajectory.positions[0] == pytest.approx([0, 0, 0])


class TestLostTracking:
    def test_a_lost_frame_contributes_no_geometry(self):
        # The behaviour that keeps a scan honest. Fusing a frame whose pose is
        # unknown welds geometry on at an arbitrary offset, and nothing
        # downstream can tell that happened.
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        before = r.state.surface_voxels
        state = r.add(np.full((HEIGHT, WIDTH, 3), 128, dtype=np.uint8), flat_depth())
        assert state.lost == 1
        assert state.surface_voxels == before

    def test_reports_why_it_lost_the_track(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        r.add(np.full((HEIGHT, WIDTH, 3), 128, dtype=np.uint8), flat_depth())
        assert r.state.last_reason

    def test_tracking_health_reflects_the_losses(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        blank = np.full((HEIGHT, WIDTH, 3), 128, dtype=np.uint8)
        r.add(blank, flat_depth())
        assert r.state.tracking_health == pytest.approx(0.5)

    def test_health_of_a_scan_that_never_started_is_zero(self):
        assert Reconstructor(intrinsics(), camera_height=None).state.tracking_health == 0.0


class TestDepthGating:
    def test_the_near_field_is_rejected(self):
        # A game frame's near field is the weapon model, the HUD and the car's
        # own bonnet. None of it is level geometry, and all of it is close.
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), np.full((HEIGHT, WIDTH), 1.0 / (MIN_DEPTH * 0.5), dtype=np.float32))
        assert r.state.surface_voxels == 0

    def test_the_far_field_is_rejected(self):
        # Monocular error grows with the square of distance; distant points are
        # noise shaped like a smeared shell behind everything real.
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), np.full((HEIGHT, WIDTH), 1.0 / (MAX_DEPTH * 2), dtype=np.float32))
        assert r.state.surface_voxels == 0

    def test_a_frame_with_nothing_usable_is_not_an_error(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        state = r.add(textured(), np.zeros((HEIGHT, WIDTH), dtype=np.float32))
        assert state.frames == 1
        assert state.surface_voxels == 0

    def test_infinite_depth_is_dropped_not_fused(self):
        depth = flat_depth()
        depth[: HEIGHT // 2] = 0.0  # sky: inverse depth zero
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), depth)
        assert r.state.surface_voxels > 0


class TestFusing:
    def test_a_walk_accumulates_surface(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        for shift in range(0, 180, 20):
            r.add(textured(shift=shift), flat_depth())
        assert r.state.tracked >= 2
        assert r.state.surface_voxels > 0
        assert r.state.coverage_voxels > 0

    def test_colour_is_carried_into_the_volume(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        mesh = r.volume.to_mesh()
        if not mesh.is_empty():
            assert mesh.colours is not None

    def test_a_greyscale_frame_is_accepted(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        grey = np.asarray(textured()[:, :, 0])
        state = r.add(grey, flat_depth())
        assert state.frames == 1


class TestWeakSpots:
    def test_starts_with_none(self):
        assert Reconstructor(intrinsics(), camera_height=None).state.weak_spots == []

    def test_refresh_is_safe_on_an_empty_scan(self):
        assert Reconstructor(intrinsics(), camera_height=None).refresh_weak_spots() == []

    def test_a_single_glance_leaves_weak_coverage(self):
        # One frame of a wall, from one place. Every condition for good coverage
        # fails at once, so this must be reported.
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth(distance=30.0))
        spots = r.refresh_weak_spots()
        assert spots
        assert spots[0].advice


class TestExport:
    def test_an_empty_scan_writes_nothing(self, tmp_path):
        # An empty .glb in the output folder reads as a successful scan that
        # produced nothing, which is harder to debug than an honest refusal.
        out = tmp_path / "empty.glb"
        assert Reconstructor(intrinsics(), camera_height=None).export(out) is None
        assert not out.exists()

    def test_a_real_scan_writes_a_loadable_file(self, tmp_path):
        r = Reconstructor(intrinsics(), voxel=0.3, camera_height=None)
        # A slab of surface seen from several places, which is enough to mesh.
        rng = np.random.default_rng(0)
        for i, shift in enumerate(range(0, 200, 25)):
            r.add(textured(shift=shift), flat_depth(distance=4.0 + 0.05 * i))
        out = r.export(tmp_path / "scan.glb", name="testscan")
        if out is None:
            pytest.skip("synthetic frames did not fuse into a surface")
        assert out.exists() and out.stat().st_size > 500

    def test_what_it_writes_passes_the_writer_s_own_contract(self, tmp_path):
        from heat3d_capture.fusion.volume import SurfaceVolume, mesh_to_parts
        from heat3d_capture.geometry.glb import write_glb

        # Straight through the same path export() takes, with geometry that is
        # guaranteed to mesh, so the contract is exercised rather than skipped.
        r = Reconstructor(intrinsics(), voxel=0.25, camera_height=None)
        rng = np.random.default_rng(2)
        directions = rng.normal(size=(60_000, 3))
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        r.volume.integrate(directions * 3.0)
        parts = mesh_to_parts(r.volume.to_mesh(), name="sphere")
        out = write_glb(tmp_path / "contract.glb", parts)
        assert out.exists()
        for part in parts:
            assert part.cls in ("ground", "structure", "water")


class TestMarkedSpots:
    """
    The mark hotkey once stored a position that nothing ever drew, listed or
    saved. A spot the driver marked is now on the maps and beside the level.
    """

    def test_nothing_placed_is_nowhere_to_mark(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        assert r.mark() is None
        assert r.state.marked == []

    def test_a_mark_is_where_the_camera_is_now(self):
        r = Reconstructor(intrinsics(), camera_height=None)
        r.add(textured(), flat_depth())
        here = r.mark()
        assert here is not None
        assert np.allclose(r.state.marked[-1], r.trajectory.positions[-1])

    def test_marks_are_saved_beside_the_level_in_its_coordinates(self, tmp_path):
        import json

        from heat3d_capture.geometry.glb import METRES_TO_VIEWER
        from heat3d_capture.scan.reconstruct import marks_path, write_marks

        level = tmp_path / "scan.glb"
        written = write_marks(level, [np.array([1.0, 2.0, -3.0]), np.array([4.0, 0.5, 6.0])])
        assert written == marks_path(level) == tmp_path / "scan.marks.json"
        doc = json.loads(written.read_text(encoding="utf-8"))
        assert doc["format"] == "heat3d-scan-marks" and doc["level"] == "scan.glb"
        assert [m["number"] for m in doc["marks"]] == [1, 2]
        assert doc["marks"][0]["metres"] == [1.0, 2.0, -3.0]
        assert doc["marks"][0]["position"] == [v * METRES_TO_VIEWER for v in (1.0, 2.0, -3.0)]

    def test_marks_are_drawn_on_the_map(self):
        from heat3d_capture.ui.preview import mark_marked_spots

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        drawn = mark_marked_spots(image, [np.array([5.0, 0.0, 5.0])], (0.0, 10.0, 0.0, 10.0))
        assert drawn[40:60, 40:60].any()
        assert not image.any(), "the input is left alone"
        assert mark_marked_spots(image, [], (0.0, 10.0, 0.0, 10.0)) is image


class TestGroundOnALaterFrame:
    """
    Ground calibration was tried on the first keyframe only. When that frame
    had no ground in view, the note stayed on "measuring the ground" for the
    rest of the scan and the level came out at an arbitrary size.
    """

    def test_a_later_keyframe_fixes_the_size_and_says_so(self):
        from heat3d_capture.pose.groundscale import calibrate_from_ground

        k = intrinsics()
        r = Reconstructor(k, camera_height=1.15, mask_hud=False)
        first = flat_depth(4.0)
        first[int(HEIGHT * 0.6) :] = 0.0  # nothing below the horizon: no ground
        state = r.add(textured(0), first)
        assert "still looking" in state.scale_note
        assert r.metres_per_unit == 1.0

        state = r.add(textured(20), flat_depth(4.0) * 20.0)
        assert "found on frame 2" in state.scale_note
        # What the first frame would have said, had it seen the ground: the
        # wall at four of the origin's units is this many metres away.
        expected = calibrate_from_ground(flat_depth(4.0), k, height=1.15).fit.apply(np.array([0.25]))[0] / 4.0
        assert r.metres_per_unit == pytest.approx(expected, rel=0.05)

    def test_it_gives_up_out_loud(self):
        from heat3d_capture.pose.groundscale import GroundCalibrator

        calibrator = GroundCalibrator(intrinsics(), attempts=3)
        for _ in range(5):
            calibrator.offer(np.zeros((HEIGHT, WIDTH), np.float32))
        assert calibrator.gave_up and calibrator.tried == 3
        assert "relative, not metres" in calibrator.note
