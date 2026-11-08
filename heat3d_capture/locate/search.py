"""
Where to look for a whole recording's frames, with no prior: the shortlists.

One frame's global descriptor against the whole level is a weak signal: the
right place is among the top few views for one frame in ten or twenty. Two
things stop a run of frames from adding that signal up. Some views look like
every frame (a generic stretch of sand) and win everywhere, so a path through
the level settles on them. And a player can be nearly anywhere within a few
frames, so a path can hop from one chance peak to the next.

So the frames of a recording are described first and searched together:

1. **Common views count for less.** Each view's similarities are measured
   against its own mean and spread over the recording's frames of that class.
2. **Places, not views.** Each frame gives every cell of a grid over the level
   a score from the rank of its best view: the log of how much likelier that
   rank is than chance, so that a clear winner is not worth much more than a
   good place, and one chance peak cannot carry a path.
3. **Along the life.** The best path through the cells is worked out both ways
   along each life, each step within what the player can cover between the two
   frames; a frame's belief in a cell is the score of the best path through it.
4. **The shortlist** takes the best view of each cell, best believed first.

This measures each view against the recording itself, which punishes the place
a player hardly leaves: there the views of the right place look like every
frame of the recording. Plain retrieval does well on exactly those recordings,
and the filter does well where the player moves, so the shortlist takes from
the two in turn (`merge`). Neither replaces matching: what is shortlisted is
only tried, and the picture decides.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SearchOptions:
    #: Metres, the side of a cell of the grid over the level.
    cell: float = 24.0
    #: Metres a second a player covers on foot, and in a vehicle view.
    foot_speed: float = 10.0
    vehicle_speed: float = 20.0
    #: Metres on top of that in any one step.
    margin: float = 10.0
    #: Metres no step reaches further than, however long the gap.
    longest: float = 600.0
    #: What a path gives up to be anywhere at all in the next frame, as a score. High on purpose: about eight good frames.
    jump: float = 40.0
    #: Softens the rank's score: a rank this far from the top is about half as telling as the top.
    rank_softening: float = 10.0
    #: Fewer frames of a class than this cannot say what is common among them: not normalised.
    least_frames: int = 16


def normalise_views(sims: np.ndarray, floor: float = 1e-3) -> np.ndarray:
    """Similarities (frames x views), each view's against its own mean and spread over these frames."""
    return (sims - sims.mean(axis=0)) / (sims.std(axis=0) + floor)


def cell_scores(sims: np.ndarray, cells: np.ndarray, n_cells: int, softening: float) -> np.ndarray:
    """(frames, n_cells): how much likelier than chance the rank of each cell's best view is; 0 for a cell without views."""
    order = np.argsort(cells, kind="stable")
    present, start = np.unique(cells[order], return_index=True)
    out = np.zeros((len(sims), n_cells), np.float32)
    for k, s in enumerate(sims):
        best = np.maximum.reduceat(s[order], start)
        rank = np.empty(len(best), np.int64)
        rank[np.argsort(-best)] = np.arange(len(best))
        out[k, present] = np.log(len(best) / (rank + softening))
    return out


def _disc(radius: float) -> np.ndarray:
    r = int(np.ceil(radius))
    y, x = np.ogrid[-r : r + 1, -r : r + 1]
    return x * x + y * y <= radius * radius + 0.5


def belief_along_life(scores: np.ndarray, reach: list[float], shape: tuple[int, int], jump: float) -> np.ndarray:
    """
    The score of the best path through each cell at each frame, forward and
    backward. `reach[j]`: how many cells the step from frame j-1 to j can
    cover (`reach[0]` is not used). A path may also be anywhere for `jump`.
    """
    from scipy import ndimage

    n = len(scores)
    fw = np.zeros_like(scores)
    bw = np.zeros_like(scores)
    fw[0] = scores[0]
    for j in range(1, n):
        p = ndimage.maximum_filter(fw[j - 1].reshape(shape), footprint=_disc(reach[j]), mode="constant", cval=-1e9).ravel()
        fw[j] = scores[j] + np.maximum(p, fw[j - 1].max() - jump)
        fw[j] -= fw[j].max()
    for j in range(n - 2, -1, -1):
        ahead = bw[j + 1] + scores[j + 1]
        p = ndimage.maximum_filter(ahead.reshape(shape), footprint=_disc(reach[j + 1]), mode="constant", cval=-1e9).ravel()
        bw[j] = np.maximum(p, ahead.max() - jump)
        bw[j] -= bw[j].max()
    return fw + bw


def along_lives(
    descriptors: np.ndarray,
    q: np.ndarray,
    places: np.ndarray,
    vehicle_views: np.ndarray | None,
    times: list[float],
    views: list[str],
    lives: list[int | None],
    n: int,
    options: SearchOptions,
    unit: float = 1.0,
) -> list[list[int]]:
    """
    Per frame, up to `n` database views (indices) by the belief along its life.

    `descriptors`: the database's (views, d); `q`: the frames' (frames, d);
    `places`: each view's (x, z) in level units; `vehicle_views`: which views
    are from a vehicle's camera, or None; `views`, `lives`: each frame's class
    and life. A frame not in a life gets an empty list: there is nothing to
    follow it along. Frames of a class search that class's views only.
    """
    out: list[list[int]] = [[] for _ in times]
    cell = options.cell / unit
    low = places.min(axis=0)
    gx, gz = ((places - low) / cell).astype(int).T
    shape = (int(gx.max()) + 1, int(gz.max()) + 1)
    flat = gx * shape[1] + gz
    n_cells = shape[0] * shape[1]
    scores = np.zeros((len(times), n_cells), np.float32)
    # Each frame's views' normalised similarities are only kept in the cells' best: a frame's list needs no more.
    best_view = np.full((len(times), n_cells), -1, np.int32)
    classes = ["vehicle", "other"] if vehicle_views is not None else ["other"]
    for cls in classes:
        frames = [k for k, v in enumerate(views) if (v == "vehicle") == (cls == "vehicle") and lives[k] is not None]
        if not frames:
            continue
        ids = np.arange(len(descriptors)) if vehicle_views is None else np.flatnonzero(vehicle_views == (cls == "vehicle"))
        if not len(ids):
            continue
        sims = q[frames].astype(np.float32) @ descriptors[ids].astype(np.float32).T
        if len(frames) >= options.least_frames:
            sims = normalise_views(sims)
        scores[frames] = cell_scores(sims, flat[ids], n_cells, options.rank_softening)
        order = np.argsort(flat[ids], kind="stable")
        present, start = np.unique(flat[ids][order], return_index=True)
        ends = np.append(start[1:], len(order))
        members = ids[order]
        for row, k in enumerate(frames):
            s = sims[row][order]
            for c, a, b in zip(present, start, ends):
                best_view[k, c] = members[a + int(np.argmax(s[a:b]))]
    for life in sorted({x for x in lives if x is not None}):
        idx = [k for k, x in enumerate(lives) if x == life]
        reach = [0.0] * len(idx)
        for j in range(1, len(idx)):
            a, b = idx[j - 1], idx[j]
            speed = options.vehicle_speed if "vehicle" in (views[a], views[b]) else options.foot_speed
            reach[j] = min(speed * (times[b] - times[a]) + options.margin, options.longest) / options.cell
        belief = belief_along_life(scores[idx], reach, shape, options.jump)
        for j, k in enumerate(idx):
            chosen: list[int] = []
            for c in np.argsort(-belief[j]):
                if best_view[k, c] >= 0:
                    chosen.append(int(best_view[k, c]))
                    if len(chosen) >= n:
                        break
            out[k] = chosen
    return out


def merge(first: list[int], second: list[int], n: int) -> list[int]:
    """Two shortlists in turn, each view once, at most `n`."""
    out: list[int] = []
    for k in range(max(len(first), len(second))):
        for side in (first, second):
            if k < len(side) and side[k] not in out:
                out.append(side[k])
                if len(out) >= n:
                    return out
    return out
