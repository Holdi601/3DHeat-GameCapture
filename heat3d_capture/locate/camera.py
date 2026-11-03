"""
Where a camera is and where it looks, in the level's frame, and the few
conversions between the ways that is written down.

A pose here is a position and two angles, the way a game's first-person view
is held: **yaw** about the level's up axis (Y), **pitch** up from the
horizontal, both in degrees, no roll. Yaw 0 looks along +X and grows towards
-Z, so in a level written in the viewer's frame - a game's (X, Z, -Y) - it is
the game's own yaw.

Two other forms are needed and kept next to it: OpenCV's camera (x right,
y down, z forward; the rotation takes level to camera) for PnP, and OpenGL's
matrices for the renderer. The intrinsics are a pinhole with square pixels,
centred, from the horizontal field of view.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

UP = np.array([0.0, 1.0, 0.0])


@dataclass
class Pose:
    position: np.ndarray  # (3,) the eye, level units
    yaw: float
    pitch: float
    roll: float = 0.0

    @property
    def forward(self) -> np.ndarray:
        return direction(self.yaw, self.pitch)

    def rotation(self) -> np.ndarray:
        """Level -> OpenCV camera."""
        return rotation_cv(self.yaw, self.pitch, self.roll)


def direction(yaw: float, pitch: float) -> np.ndarray:
    y, p = math.radians(yaw), math.radians(pitch)
    return np.array([math.cos(p) * math.cos(y), math.sin(p), -math.cos(p) * math.sin(y)])


def rotation_cv(yaw: float, pitch: float, roll: float = 0.0) -> np.ndarray:
    """Rows: the camera's right, down and forward, in the level's frame."""
    f = direction(yaw, pitch)
    y = math.radians(yaw)
    right = np.array([math.sin(y), 0.0, math.cos(y)])  # f x UP, normalised: it never degenerates
    down = np.cross(f, right)
    if roll:
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        right, down = c * right + s * down, -s * right + c * down
    return np.stack([right, down, f])


def angles(rotation: np.ndarray) -> tuple[float, float, float]:
    """Yaw, pitch, roll (degrees) of a level -> OpenCV camera rotation."""
    f = rotation[2]
    yaw = math.degrees(math.atan2(-f[2], f[0]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, f[1]))))
    flat = rotation_cv(yaw, pitch)
    roll = math.degrees(math.atan2(float(rotation[0] @ flat[1]), float(rotation[0] @ flat[0])))
    return yaw, pitch, roll


def focal(width: int, hfov: float) -> float:
    return (width / 2.0) / math.tan(math.radians(hfov) / 2.0)


def intrinsics(width: int, height: int, hfov: float) -> np.ndarray:
    f = focal(width, hfov)
    return np.array([[f, 0.0, width / 2.0], [0.0, f, height / 2.0], [0.0, 0.0, 1.0]])


def hfov_for_aspect(hfov: float, aspect_from: float, aspect_to: float) -> float:
    """
    The horizontal field of view the same vertical one gives at another aspect.

    Games that state their FOV for 4:3 (Source's 90) keep the vertical and
    widen the horizontal on a wider screen ("Hor+"): 90 at 4:3 is about 106.3
    at 16:9.
    """
    half = math.tan(math.radians(hfov) / 2.0) * aspect_to / aspect_from
    return math.degrees(2.0 * math.atan(half))


def hfov_from_vertical(vfov: float, aspect: float) -> float:
    return math.degrees(2.0 * math.atan(math.tan(math.radians(vfov) / 2.0) * aspect))


def angle_between(r1: np.ndarray, r2: np.ndarray) -> float:
    """The rotation angle (degrees) between two rotations."""
    c = (np.trace(r1 @ r2.T) - 1.0) / 2.0
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def gl_view(pose: Pose) -> np.ndarray:
    """Level -> OpenGL eye space (x right, y up, looking down -z)."""
    r = pose.rotation()
    flip = np.diag([1.0, -1.0, -1.0])
    m = np.eye(4)
    m[:3, :3] = flip @ r
    m[:3, 3] = -(flip @ r) @ pose.position
    return m


def gl_projection(width: int, height: int, hfov: float, near: float, far: float) -> np.ndarray:
    fx = 1.0 / math.tan(math.radians(hfov) / 2.0)
    fy = fx * width / height
    m = np.zeros((4, 4))
    m[0, 0] = fx
    m[1, 1] = fy
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2.0 * far * near / (near - far)
    m[3, 2] = -1.0
    return m
