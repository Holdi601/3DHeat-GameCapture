"""
A located table against the truth: how far off, how often, by source.

The truth is any table of the camera's real poses in the level's frame -
`time`, `x`, `y`, `z` (the eye), `yaw`, `pitch` in this package's
convention (camera.py) - from wherever exact poses can be had: a game's
demo or replay played back while recording, a scripted camera path. The
two clocks rarely start together, so the offset between them is a
parameter, or is searched for (`offset=None`): the one at which the visual
fixes lie closest to the truth. A found offset is reported, and should be
looked at - with too few good fixes it can lock onto a coincidence.
"""

from __future__ import annotations

import math

import numpy as np

from .camera import angle_between, rotation_cv


def read_poses(path: str) -> dict[str, np.ndarray]:
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    out = {}
    for name in ("time", "x", "y", "z", "yaw", "pitch"):
        if name in t.column_names:
            out[name] = np.array([np.nan if v is None else v for v in t[name].to_pylist()], float)
    for name in ("source", "confidence", "kept"):
        if name in t.column_names:
            out[name] = np.array(t[name].to_pylist(), dtype=object)
    return out


def interpolate(truth: dict[str, np.ndarray], times: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Position, yaw, pitch of the truth at `times`, and which of them lie inside it."""
    order = np.argsort(truth["time"])
    t = truth["time"][order]
    pos = np.stack([np.interp(times, t, truth[k][order]) for k in ("x", "y", "z")], axis=1)
    yr = np.unwrap(np.radians(truth["yaw"][order]))
    yaw = np.degrees(np.interp(times, t, yr))
    pitch = np.interp(times, t, truth["pitch"][order])
    inside = (times >= t[0]) & (times <= t[-1])
    # Not across a hole in the truth (a death, a cut): nearest sample within half a second.
    idx = np.clip(np.searchsorted(t, times), 1, len(t) - 1)
    near = np.minimum(np.abs(t[idx] - times), np.abs(t[idx - 1] - times)) < 0.5
    return pos, yaw, pitch, inside & near


def find_offset(located: dict[str, np.ndarray], truth: dict[str, np.ndarray], span: float = 30.0) -> float:
    """The clock offset (truth time = located time + offset) that puts the visual fixes closest to the truth."""
    visual = np.array([s in ("visual", "visual+minimap-prior") for s in located.get("source", [])]) if "source" in located else np.isfinite(located["x"])
    t = located["time"][visual]
    p = np.stack([located[k][visual] for k in ("x", "y", "z")], axis=1)
    if len(t) < 5:
        raise ValueError("fewer than 5 visual fixes: too few to find the clock offset; pass it")

    def cost(offset: float) -> float:
        pos, _, _, ok = interpolate(truth, t + offset)
        if ok.sum() < max(5, len(t) // 4):
            return math.inf
        return float(np.median(np.linalg.norm(pos[ok] - p[ok], axis=1)))

    lo = float(truth["time"].min() - t.max())
    hi = float(truth["time"].max() - t.min())
    lo, hi = max(lo, -span) if span else lo, min(hi, span) if span else hi
    grid = np.arange(lo, hi, 0.25)
    best = min(grid, key=cost)
    fine = np.arange(best - 0.3, best + 0.3, 0.02)
    return float(min(fine, key=cost))


def compare(located: dict[str, np.ndarray], truth: dict[str, np.ndarray], offset: float | None, unit_metres: float) -> dict:
    if offset is None:
        offset = find_offset(located, truth, span=0)
    t = located["time"]
    pos, yaw, pitch, inside = interpolate(truth, t + offset)
    p = np.stack([located[k] for k in ("x", "y", "z")], axis=1)
    has = np.isfinite(p).all(axis=1) & inside
    err = np.full(len(t), np.nan)
    err[has] = np.linalg.norm(p[has] - pos[has], axis=1) * unit_metres
    ang = np.full(len(t), np.nan)
    for i in np.flatnonzero(has):
        if np.isfinite(located["yaw"][i]):
            lp = located["pitch"][i] if "pitch" in located and np.isfinite(located["pitch"][i]) else pitch[i]
            ang[i] = angle_between(rotation_cv(located["yaw"][i], lp), rotation_cv(yaw[i], pitch[i]))
    sources = located.get("source", np.array(["visual"] * len(t), dtype=object))

    def stats(sel: np.ndarray) -> dict:
        e, a = err[sel & np.isfinite(err)], ang[sel & np.isfinite(ang)]
        return {
            "frames": int(sel.sum()),
            "median_m": _q(e, 50),
            "p90_m": _q(e, 90),
            "within_1m": float((e < 1.0).mean()) if len(e) else None,
            "within_3m": float((e < 3.0).mean()) if len(e) else None,
            "median_deg": _q(a, 50),
            "p90_deg": _q(a, 90),
        }

    frames = int(inside.sum())
    return {
        "offset_s": round(offset, 3),
        "frames_in_truth": frames,
        "placed": float(np.isfinite(err).sum() / max(1, frames)),
        "all": stats(has),
        **{s: stats(has & (sources == s)) for s in ("visual", "visual+minimap-prior", "minimap")},
    }


def _q(x: np.ndarray, p: float) -> float | None:
    return round(float(np.percentile(x, p)), 3) if len(x) else None
