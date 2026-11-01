"""
Tests for telemetry-driven poses.

Where a game publishes where it is, guessing is absurd — but the published
numbers arrive on a different clock from the frames, and the interesting failures
are all in lining those up. So these are mostly about time: interpolating between
samples, refusing to interpolate across a gap, and refusing to answer at all
outside the window that was recorded.
"""

from __future__ import annotations

import numpy as np
import pytest

from heat3d_capture.pose.odometry import Intrinsics
from heat3d_capture.pose.telemetry_pose import (
    MAX_GAP,
    ForzaPoseSource,
    TelemetryPoseTrack,
    pose_from_forza,
)


class FakeFrame:
    """The fields `pose_from_forza` reads, without a socket."""

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0, roll=0.0, speed=10.0):
        self.x, self.y, self.z = x, y, z
        self.yaw, self.pitch, self.roll = yaw, pitch, roll
        self.speed = speed
        self.is_race_on = True


class TestConversion:
    def test_the_position_is_the_games_own(self):
        # Forza is Y-up already, and the lap files keep y as the height. The
        # surface has to land on the same coordinates as the laps driven over
        # it; an earlier version swapped y and z and laid the track on its side.
        pose = pose_from_forza(FakeFrame(x=10.0, y=-4.0, z=2.5))
        assert pose.translation == pytest.approx([10.0, -4.0, 2.5])

    def test_the_matrix_is_orthonormal_and_carries_the_mirror(self):
        # Forza's world is left-handed and the camera's is not, so the honest
        # matrix is a reflection: orthonormal, determinant -1.
        pose = pose_from_forza(FakeFrame(yaw=0.6, pitch=-0.2, roll=0.1))
        r = pose.rotation
        assert r @ r.T == pytest.approx(np.eye(3), abs=1e-9)
        assert np.linalg.det(r) == pytest.approx(-1.0)

    def test_level_and_heading_along_z_the_camera_looks_along_z(self):
        r = pose_from_forza(FakeFrame()).rotation
        assert r[:, 2] == pytest.approx([0.0, 0.0, 1.0])  # forward
        assert r[:, 0] == pytest.approx([1.0, 0.0, 0.0])  # right
        # The camera's y is down the picture, and down is minus the height:
        # the road below the horizon is fused below the car, not above it.
        assert r[:, 1] == pytest.approx([0.0, -1.0, 0.0])

    def test_yaw_is_the_direction_of_travel(self):
        # Measured on recorded laps: atan2(dx, dz) of the path equals the yaw.
        yaw = 0.8
        forward = pose_from_forza(FakeFrame(yaw=yaw)).rotation[:, 2]
        assert np.arctan2(forward[0], forward[2]) == pytest.approx(yaw)

    def test_a_positive_pitch_is_nose_down(self):
        # Measured: the slope climbed is minus the pitch.
        forward = pose_from_forza(FakeFrame(pitch=0.2)).rotation[:, 2]
        assert forward[1] == pytest.approx(-np.sin(0.2))

    def test_a_positive_roll_drops_the_right_side(self):
        # Measured: the roll is positive when the right-hand suspension is the
        # compressed one.
        right = pose_from_forza(FakeFrame(roll=0.1)).rotation[:, 0]
        assert right[1] == pytest.approx(-np.sin(0.1))


class TestAGapInTheFeed:
    def test_vision_carries_on_in_the_games_own_coordinates(self):
        """
        Telemetry poses are reflections, and PnP only ever returns rotations.
        Without folding the mirror back in, the first frame of a gap was placed
        sixteen metres out and every frame after it followed.
        """
        from heat3d_capture.pose.odometry import Pose, VisualOdometry

        from .scene import render, walk

        k = Intrinsics.from_fov(320, 240, 80.0)
        flip = np.diag([1.0, -1.0, 1.0])
        truth = [Pose(f.pose.rotation @ flip, f.pose.translation) for f in walk(k, steps=30)]
        vo = VisualOdometry(k)
        for i, pose in enumerate(truth[:12]):
            frame = render(pose, k)
            inverse = (1.0 / np.maximum(frame.depth, 1e-3)).astype(np.float32)
            # The feed answers for eight frames, then goes quiet.
            result = vo.track(frame.image, inverse, known_pose=pose if i < 8 else None)
            assert result.tracked
            if i >= 8:
                assert np.linalg.norm(result.pose.translation - pose.translation) < 0.2
                assert np.linalg.det(result.pose.rotation) == pytest.approx(-1.0)


class TestTrack:
    def _track(self, n=5, spacing=0.05):
        track = TelemetryPoseTrack()
        for i in range(n):
            track.add(FakeFrame(x=float(i), yaw=i * 0.1), now=i * spacing)
        return track

    def test_interpolates_between_samples(self):
        pose = self._track().at(0.075)  # halfway between samples 1 and 2
        assert pose is not None
        assert pose.translation[0] == pytest.approx(1.5, abs=1e-6)

    def test_lands_exactly_on_a_sample(self):
        assert self._track().at(0.10).translation[0] == pytest.approx(2.0)

    def test_refuses_outside_the_recorded_window(self):
        # A frame captured before telemetry started, or after it stopped, has no
        # pose. Extrapolating would put its geometry somewhere plausible and
        # wrong, which nothing downstream can detect.
        track = self._track()
        assert track.at(-1.0) is None
        assert track.at(99.0) is None

    def test_refuses_across_a_long_gap(self):
        # A pause or a dropped connection. A straight line between two distant
        # samples is a chord across whatever the car actually did.
        track = TelemetryPoseTrack()
        track.add(FakeFrame(x=0.0), now=0.0)
        track.add(FakeFrame(x=100.0), now=MAX_GAP * 3)
        assert track.at(MAX_GAP) is None

    def test_interpolated_rotations_stay_rotations(self):
        # Blending two rotation matrices elementwise does not give a rotation —
        # it shrinks toward the mean, and a non-orthonormal matrix skews every
        # point that frame contributes. (Determinant -1: the game's world is
        # left-handed, see `pose_from_forza`.)
        track = TelemetryPoseTrack()
        track.add(FakeFrame(yaw=0.0), now=0.0)
        track.add(FakeFrame(yaw=1.4), now=0.1)
        r = track.at(0.05).rotation
        assert r @ r.T == pytest.approx(np.eye(3), abs=1e-9)
        assert np.linalg.det(r) == pytest.approx(-1.0)

    def test_rotation_interpolation_goes_halfway(self):
        track = TelemetryPoseTrack()
        track.add(FakeFrame(yaw=0.0), now=0.0)
        track.add(FakeFrame(yaw=1.0), now=0.2)
        expected = pose_from_forza(FakeFrame(yaw=0.5)).rotation
        assert track.at(0.1).rotation == pytest.approx(expected, abs=1e-6)

    def test_too_few_samples_is_no_answer(self):
        track = TelemetryPoseTrack()
        assert track.at(0.0) is None
        track.add(FakeFrame(), now=0.0)
        assert track.at(0.0) is None

    def test_old_samples_are_dropped(self):
        # A half-hour scan at sixty packets a second, with nothing needing a pose
        # once its frame has been fused.
        track = TelemetryPoseTrack(window=1.0)
        for i in range(500):
            track.add(FakeFrame(x=float(i)), now=i * 0.02)
        assert len(track) <= 60

    def test_knows_whether_the_car_is_moving(self):
        track = TelemetryPoseTrack()
        track.add(FakeFrame(speed=0.0), now=0.0)
        assert not track.moving
        track.add(FakeFrame(speed=25.0), now=0.1)
        assert track.moving


class TestSource:
    def test_starting_and_stopping_does_not_raise(self):
        # Telemetry is an upgrade. A scan that would have worked on vision alone
        # must not be stopped because of anything that happens here.
        source = ForzaPoseSource(port=5398)
        source.start()
        source.stop()

    def test_status_reads_as_prose_before_anything_arrives(self):
        source = ForzaPoseSource(port=5399)
        assert "not started" in source.status
        assert not source.active


class TestAgainstTheReconstructor:
    def test_a_published_pose_is_used_instead_of_solving_for_one(self):
        from heat3d_capture.scan.reconstruct import Reconstructor

        from .scene import survey

        k = Intrinsics.from_fov(480, 270, 90.0)
        frames = survey(k, steps=20)

        class Source:
            """Hands back the true pose for every frame."""

            def __init__(self, frames):
                self.frames = frames

            def at(self, t):
                index = int(round(t))
                return self.frames[index].pose if 0 <= index < len(self.frames) else None

        r = Reconstructor(
            k, voxel=0.25, pose_source=Source(frames), mask_hud=False, camera_height=None
        )
        for i, frame in enumerate(frames):
            with np.errstate(divide="ignore"):
                inverse = np.where(np.isfinite(frame.depth), 1.0 / frame.depth, 0.0)
            r.add(frame.image, inverse.astype(np.float32), timestamp=float(i))

        # Every frame placed, and placed exactly where the feed said — not near
        # it, at it. That is the whole argument for using telemetry.
        assert r.state.tracked == len(frames)
        truth = np.array([f.pose.translation for f in frames])
        assert r.trajectory.positions == pytest.approx(truth, abs=1e-9)

    def test_it_falls_back_when_the_feed_has_no_answer(self):
        from heat3d_capture.scan.reconstruct import Reconstructor

        from .scene import walk

        # A gentler walk: a fast sweep at low resolution defeats feature
        # matching, which is a property of the test scene and not of the fallback.
        k = Intrinsics.from_fov(480, 270, 90.0)
        frames = walk(k, steps=20)

        class Silent:
            def at(self, t):
                return None

        r = Reconstructor(
            k, voxel=0.25, pose_source=Silent(), mask_hud=False, camera_height=None
        )
        for i, frame in enumerate(frames):
            with np.errstate(divide="ignore"):
                inverse = np.where(np.isfinite(frame.depth), 1.0 / frame.depth, 0.0)
            r.add(frame.image, inverse.astype(np.float32), timestamp=float(i))
        # Solved visually instead, rather than stopping.
        assert r.state.tracked >= 5
