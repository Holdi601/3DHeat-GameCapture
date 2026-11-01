"""
Camera poses from a game that publishes them.

Where a game says where it is, guessing is absurd. Forza's telemetry feed gives
position and orientation every simulation tick, exactly, for free — and using it
removes the two things that limit visual odometry: drift, which accumulates
without bound over a lap, and scale, which monocular vision cannot recover at all.

A track reconstructed with telemetry poses is metrically correct end to end. One
reconstructed from vision alone is correct locally and slowly wrong globally.

Lining up two clocks
--------------------
The hard part is not the poses, it is *when* they happened. Telemetry arrives on
a UDP socket and frames arrive from the compositor, and the game's own timestamp
counts from something unrelated to either. Three clocks, no common origin.

So the game's timestamp is not used for alignment at all. Each packet is stamped
with the monotonic time it *arrived*, which is the same clock the capture stamps
frames with, and poses are interpolated to a frame's time from the samples either
side. That inherits the network's jitter — a millisecond or two on loopback —
which at 200 km/h is about six centimetres, and is the price of not having to
solve clock synchronisation. Visual odometry's error over a lap is metres.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import numpy as np

from .odometry import Pose

#: Refuse to interpolate across a gap longer than this. A pause, an alt-tab or a
#: dropped connection leaves two samples far apart, and a straight line between
#: them is not where the car went — it is a chord across whatever it actually did.
MAX_GAP = 0.35


#: The car's axes (x right, y up, z forward) to the camera's (x right, y down,
#: z forward, as OpenCV and `Intrinsics.unproject` have it). One axis flips.
CAR_TO_CAMERA = np.diag([1.0, -1.0, 1.0])


def car_rotation(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """
    World-from-car, from Forza's attitude angles.

    The senses were read off recorded laps rather than assumed: the direction
    of travel `atan2(dx, dz)` equals the yaw, so yaw turns +z toward +x; the
    slope climbed equals minus the pitch, so a positive pitch is nose down; and
    the roll is positive when the right-hand suspension is the compressed one,
    so a positive roll drops the right side.
    """
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    # Negated so that the matrix below lifts the left side for a positive roll.
    cr, sr = np.cos(-roll), np.sin(-roll)

    # Yaw about up, then pitch, then roll — the order a vehicle's attitude is
    # reported in.
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rp = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    rr = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return ry @ rp @ rr


def pose_from_forza(frame) -> Pose:
    """
    Turn one telemetry frame into a camera pose.

    Forza reports yaw, pitch and roll of the *car*, and a position in metres.
    The camera is treated as being at the car — a chase camera's offset is not
    published and guessing it would put every reconstruction a few metres behind
    itself, which is worse than the error it would fix.

    The position is kept exactly as the game sends it. Forza's world is already
    Y-up (x and z across the map, y the height), which is how the lap files and
    route files write it too, so a surface reconstructed here lands on the same
    coordinates as the racing lines recorded over it. An earlier version swapped
    y and z on the belief that the game was Z-up, and laid every track on its
    side.

    That world is left-handed — the car's own axes are x right, y up, z forward
    — while the camera's are right-handed, so the rotation returned is a
    reflection (determinant -1) rather than a rotation. That is the honest
    matrix: it maps camera rays into the game's own coordinates, which is what
    every use of `Pose` does with it. Interpolation (`_slerp`) is unaffected,
    because the turn *between* two such poses is a proper rotation.
    """
    position = np.array([frame.x, frame.y, frame.z], dtype=np.float64)
    rotation = car_rotation(frame.yaw, frame.pitch, frame.roll) @ CAR_TO_CAMERA
    return Pose(rotation=rotation, translation=position)


@dataclass
class _Sample:
    t: float  # monotonic arrival time
    pose: Pose
    speed: float


class TelemetryPoseTrack:
    """
    A rolling buffer of poses, queryable at a frame's timestamp.

    Deliberately a *buffer* and not a recording: a scan can run for half an hour
    at sixty packets a second, and nothing needs a pose once its frame has been
    fused. Old samples are dropped.
    """

    def __init__(self, *, window: float = 30.0):
        self.window = window
        self._samples: list[_Sample] = []
        self._lock = threading.Lock()
        self.received = 0

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)

    def add(self, frame, *, now: float | None = None) -> None:
        """Record one telemetry frame, stamped with its arrival time."""
        t = time.monotonic() if now is None else now
        pose = pose_from_forza(frame)
        with self._lock:
            self.received += 1
            self._samples.append(_Sample(t, pose, frame.speed))
            cutoff = t - self.window
            # Trimmed from the front; samples arrive in order, so the first one
            # still inside the window ends the search.
            drop = 0
            for sample in self._samples:
                if sample.t >= cutoff:
                    break
                drop += 1
            if drop:
                del self._samples[:drop]

    def at(self, t: float) -> Pose | None:
        """
        The pose at time `t`, interpolated. None when it cannot be known.

        None rather than the nearest sample: a frame captured during a gap in the
        feed has no published pose, and pretending otherwise puts its geometry
        somewhere plausible and wrong. The reconstructor then places that frame
        the way it would without telemetry — visual tracking, carried on from the
        last pose the feed gave — and is back on the feed's poses as soon as the
        feed answers again. Only if the visual tracking also fails is the frame
        untracked.
        """
        with self._lock:
            samples = list(self._samples)
        if len(samples) < 2:
            return None
        if t < samples[0].t or t > samples[-1].t:
            return None

        # Binary search for the bracketing pair.
        low, high = 0, len(samples) - 1
        while high - low > 1:
            middle = (low + high) // 2
            if samples[middle].t <= t:
                low = middle
            else:
                high = middle
        before, after = samples[low], samples[high]
        gap = after.t - before.t
        if gap > MAX_GAP:
            return None
        if gap < 1e-9:
            return before.pose

        alpha = (t - before.t) / gap
        translation = before.pose.translation * (1 - alpha) + after.pose.translation * alpha
        rotation = _slerp(before.pose.rotation, after.pose.rotation, alpha)
        return Pose(rotation=rotation, translation=translation)

    @property
    def moving(self) -> bool:
        with self._lock:
            return bool(self._samples) and self._samples[-1].speed > 0.5


def _slerp(a: np.ndarray, b: np.ndarray, alpha: float) -> np.ndarray:
    """
    Interpolate between two rotations.

    Through the rotation *between* them rather than by blending the matrices
    elementwise. A blended matrix is not a rotation — it shrinks toward the mean
    as the angle grows, and feeding a non-orthonormal matrix into the projection
    skews every point that frame contributes.
    """
    from scipy.spatial.transform import Rotation

    relative = Rotation.from_matrix(a.T @ b)
    # `as_rotvec` scales cleanly: a fraction of the axis-angle vector is the same
    # fraction of the turn.
    partial = Rotation.from_rotvec(relative.as_rotvec() * alpha)
    return a @ partial.as_matrix()


class ForzaPoseSource:
    """
    Listens for Forza telemetry on a thread and keeps the track fed.

    Started and stopped with the scan. Failure to bind the port is reported
    rather than raised: telemetry is an *upgrade*, and a scan that would have
    worked on vision alone must not be stopped because a port was busy.
    """

    def __init__(self, *, port: int = 5300, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.track = TelemetryPoseTrack()
        self.error: str | None = None
        self._listener = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def active(self) -> bool:
        """True once packets are arriving and the layout has been established."""
        return self._listener is not None and self._listener.layout is not None

    @property
    def status(self) -> str:
        if self.error:
            return self.error
        if self._thread is None:
            return "not started"
        if not self.track.received:
            return f"listening on {self.host}:{self.port} — no packets yet"
        if not self.active:
            return "packets arriving; drive a few metres so the layout can be identified"
        return f"{self.track.received} packets, layout {self._listener.layout.name}"

    def start(self) -> bool:
        from ..telemetry.forza import ForzaListener

        try:
            self._listener = ForzaListener(self.host, self.port, timeout=0.5)
        except OSError as exc:
            self.error = f"could not listen on {self.host}:{self.port} — {exc}"
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def _run(self) -> None:
        import socket

        assert self._listener is not None
        while not self._stop.is_set():
            try:
                packet, _ = self._listener._sock.recvfrom(2048)
            except socket.timeout:
                continue
            except OSError:
                return
            frame = self._listener.feed(packet)
            if frame is not None and frame.is_race_on:
                self.track.add(frame)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._listener:
            self._listener.close()
            self._listener = None
