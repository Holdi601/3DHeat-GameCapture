"""
Putting the frames' colour back onto the finished surface.

Fusion already carries colour, averaged per voxel as points land in it. That is
cheap, it is available live, and it is blurry: every pixel that fell in a
quarter-metre cell is averaged flat, including pixels from frames that saw the
cell edge-on from thirty metres away.

This does the job properly, once, at the end. Each vertex of the extracted mesh
is projected back into the frames that actually saw it well, and only those
contribute. The difference is the difference between a colour per voxel and a
colour per vertex sampled from the best view available.

Why colour and not a texture atlas
----------------------------------
The obvious next step is UV-unwrapping the mesh and packing a texture, and it is
deliberately not taken. The viewer renders levels *untextured on purpose* — solid
ground, near-transparent wireframe structures — because the whole point of the
background geometry is to sit behind a heatmap without competing with it. An
atlas would be invisible there, would multiply the file size, and would need an
unwrapper to earn none of it back.

Per-vertex colour is written as glTF `COLOR_0`, which the viewer shows when its
"Captured colour" switch is on (it is off by default) and which Blender and
every other glTF tool reads. The mesh is voxel-dense, so a colour per vertex is a sample
every few centimetres rather than a flat shade per face.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..pose.odometry import Intrinsics, Pose

#: A face turned more than this far from the camera contributes nothing. At
#: grazing angles one pixel covers metres of surface, so the colour it reports is
#: an average of things that are not the same thing.
MAX_OBLIQUITY = 0.34  # cos, about 70 degrees off head-on

#: Views beyond this distance are ignored where a nearer one exists. Colour from
#: far away is both blurrier and more likely to be something else entirely.
FAR_VIEW = 35.0

#: How many frames may contribute to one vertex. Blending a few suppresses
#: per-frame exposure wobble; blending many just averages back to the blur this
#: exists to avoid. They are the best few by `_quality`, not the first few.
MAX_VIEWS = 4

#: Pixels per cell of the depth buffer the occlusion test draws the mesh into.
#: The mesh is voxel-dense, so its vertices cover a surface without gaps at
#: this size; a finer buffer would let farther vertices show through between
#: the nearer ones.
OCCLUSION_CELL = 2

#: How much farther than the nearest vertex in its cell a vertex may be and
#: still count as seen: a margin for the voxel size, and a share of the
#: distance for a surface that slopes away within one cell.
OCCLUSION_MARGIN = 0.3
OCCLUSION_SLACK = 0.05


@dataclass
class Keyframe:
    """One frame kept for texturing: what it saw, and from where."""

    image: np.ndarray
    pose: Pose


def project_colours(
    vertices: np.ndarray,
    normals: np.ndarray,
    keyframes: list[Keyframe],
    k: Intrinsics,
    *,
    fallback: np.ndarray | None = None,
) -> np.ndarray:
    """
    Colour every vertex from the frames that saw it best.

    "Best" is ranked: each view a vertex has is scored by how square-on and how
    near it was (`_quality`), and the `MAX_VIEWS` highest-scoring ones are
    blended, weighted by that score. The frames' order does not matter — an
    earlier version took the first four that qualified, so a vertex glimpsed
    early at a poor angle kept that colour however well it was seen later.

    A view in which the vertex was hidden counts for nothing. Each frame draws
    the mesh's own vertices into a coarse depth buffer, and a vertex well behind
    the nearest one at its pixel was behind something in that frame — a wall
    between the camera and the road beyond — so the pixel there shows the wall.

    Returns (N,3) float32 in 0..1. Vertices no frame saw keep `fallback` — the
    voxel-averaged colour from fusion — rather than going black, because a black
    patch reads as a hole in the geometry rather than as missing colour.
    """
    vertices = np.asarray(vertices, dtype=np.float64).reshape(-1, 3)
    normals = np.asarray(normals, dtype=np.float64).reshape(-1, 3)
    count = len(vertices)

    # The best few views of each vertex so far: their scores and colours. A
    # new view replaces the weakest of them when it scores higher.
    best = np.zeros((count, MAX_VIEWS), dtype=np.float64)
    colour = np.zeros((count, MAX_VIEWS, 3), dtype=np.float64)

    for keyframe in keyframes:
        pose = keyframe.pose
        image = keyframe.image
        height, width = image.shape[:2]

        camera_points = (vertices - pose.translation) @ pose.rotation
        z = camera_points[:, 2]
        ahead = z > 1e-3
        if not ahead.any():
            continue

        pixels = k.project(camera_points)
        inside = (
            ahead
            & np.isfinite(pixels).all(axis=1)
            & (pixels[:, 0] >= 0)
            & (pixels[:, 0] <= width - 1)
            & (pixels[:, 1] >= 0)
            & (pixels[:, 1] <= height - 1)
        )
        if not inside.any():
            continue

        # How square-on the surface is to this camera. A face seen edge-on is
        # sampled across metres by one pixel.
        to_camera = pose.translation - vertices
        distance = np.linalg.norm(to_camera, axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            facing = np.abs(np.einsum("ij,ij->i", normals, to_camera / distance[:, None]))
        usable = (
            inside
            & np.isfinite(facing)
            & (facing > MAX_OBLIQUITY)
            & (distance < FAR_VIEW)
        )
        if usable.any():
            usable &= _unoccluded(pixels, z, inside, (height, width))
        if not usable.any():
            continue

        rows = np.clip(np.round(pixels[usable, 1]).astype(int), 0, height - 1)
        cols = np.clip(np.round(pixels[usable, 0]).astype(int), 0, width - 1)
        sampled = image[rows, cols].astype(np.float64) / 255.0

        score = _quality(facing[usable], distance[usable])
        index = np.flatnonzero(usable)
        weakest = np.argmin(best[index], axis=1)
        better = score > best[index, weakest]
        index, weakest = index[better], weakest[better]
        best[index, weakest] = score[better]
        colour[index, weakest] = sampled[better]

    weight = best.sum(axis=1)
    coloured = weight > 1e-9
    out = np.full((count, 3), 0.5, dtype=np.float32)
    if fallback is not None:
        fallback = np.asarray(fallback, dtype=np.float32).reshape(-1, 3)
        if len(fallback) == count:
            out = fallback.copy()
    blended = np.einsum("nv,nvc->nc", best[coloured], colour[coloured])
    out[coloured] = (blended / weight[coloured, None]).astype(np.float32)
    return np.clip(out, 0.0, 1.0)


def _quality(facing: np.ndarray, distance: np.ndarray) -> np.ndarray:
    """
    How good a view of a vertex is: head-on and near beats glancing and far.

    Both the ranking and the blend weight, so the views kept are the ones that
    would have dominated the blend anyway.
    """
    return facing * (1.0 - distance / FAR_VIEW)


def _unoccluded(
    pixels: np.ndarray, z: np.ndarray, inside: np.ndarray, shape: tuple[int, int]
) -> np.ndarray:
    """
    Which vertices are not behind another part of the mesh in this frame.

    The vertices in view are drawn into a depth buffer of `OCCLUSION_CELL`
    pixel cells, keeping the nearest per cell; a vertex is seen when it is no
    farther than that, give or take the margin. Vertices out of view come back
    False.
    """
    height, width = shape
    cell = OCCLUSION_CELL
    rows = np.zeros(len(z), dtype=np.int64)
    cols = np.zeros(len(z), dtype=np.int64)
    rows[inside] = np.clip(pixels[inside, 1] // cell, 0, (height - 1) // cell).astype(np.int64)
    cols[inside] = np.clip(pixels[inside, 0] // cell, 0, (width - 1) // cell).astype(np.int64)
    nearest = np.full(((height - 1) // cell + 1, (width - 1) // cell + 1), np.inf)
    np.minimum.at(nearest, (rows[inside], cols[inside]), z[inside])
    seen = np.zeros(len(z), dtype=bool)
    front = nearest[rows[inside], cols[inside]]
    seen[inside] = z[inside] <= front * (1.0 + OCCLUSION_SLACK) + OCCLUSION_MARGIN
    return seen


class KeyframeStore:
    """
    A bounded set of frames kept back for texturing.

    Bounded because the frames are the largest thing in the process: a half-hour
    scan is thousands of images, and keeping them all to colour a mesh at the end
    would cost more memory than everything else put together. Kept frames are
    spread across the scan rather than being the most recent ones, so the whole
    walk contributes rather than only its tail.
    """

    def __init__(self, *, limit: int = 160):
        self.limit = limit
        self._frames: list[Keyframe] = []
        self._seen = 0

    def __len__(self) -> int:
        return len(self._frames)

    @property
    def frames(self) -> list[Keyframe]:
        return self._frames

    def add(self, image: np.ndarray, pose: Pose) -> None:
        self._seen += 1
        if len(self._frames) < self.limit:
            self._frames.append(Keyframe(image=image.copy(), pose=pose))
            return
        # Past the limit, replace a frame at random with decreasing probability —
        # reservoir sampling, which keeps a uniform spread over the whole scan
        # instead of the last N frames of it.
        index = np.random.default_rng(self._seen).integers(0, self._seen)
        if index < self.limit:
            self._frames[int(index)] = Keyframe(image=image.copy(), pose=pose)
