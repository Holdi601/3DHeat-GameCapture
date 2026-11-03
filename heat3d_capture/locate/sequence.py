"""
Frames in a row, decided together.

One frame alone can be fooled: a look-alike wall elsewhere, a repeated
building module, a solve with too few inliers to be believed. A run of
frames rarely is, because a player cannot be in two far-apart places a
second apart. So each frame keeps every physically possible pose it found
(`Fix.candidates`, strongest first), and the path through them that is best
supported - many inliers, and every step no longer than the player's speed
allows - is chosen at once, as a hidden Markov model is decoded (Viterbi).

A frame may also choose nothing: a gap costs nothing but the score it would
have added, so a frame with only a stray candidate is skipped rather than
dragging the path to it. A path is broken where it would have to jump (a
respawn); the pieces are decoded on their own.

What it returns is per frame the chosen candidate (or none) and how many
neighbours within the window agree with it - the support a chosen weak fix
draws on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class Choice:
    index: int | None  # into that frame's candidates
    support: int  # chosen frames within the window consistent with this one


def emission(inliers: int) -> float:
    """What a candidate's inliers are worth: saturating, so 400 is not ten times 40."""
    return 4.0 * (1.0 - math.exp(-max(0, inliers - 6) / 40.0))


def decode(
    times: list[float],
    candidates: list[list[tuple[np.ndarray, int]]],
    speed: float | list[float],
    margin: float,
    *,
    window: int = 8,
    jump: float = 6.0,
    support_within: float = 6.0,
    lives: list[int | None] | None = None,
) -> list[Choice]:
    """
    `candidates[f]`: (position, inliers) per candidate of frame f. `speed`
    (one, or one per frame - a vehicle's frames are faster) and `margin` in
    level units (a second, and on top); a step uses the faster of its two
    frames. `window`: how many
    frames back a step may reach over gaps. `jump`: what breaking the path
    costs - a respawn, or one wrong stretch given up on. `support_within`:
    the seconds a neighbour may be away to count as agreeing - further, and
    the distance it could have covered is so large that agreeing says
    nothing (a vehicle 16 s away could be anywhere within half a kilometre).

    `lives` (one per frame; None where the player is not in play): the lives
    the footage showed (lives.py). Then the path may jump only from one life
    to the next, at no cost; within a life every step keeps to the speed,
    however long the gap, and a frame that would need a jump is left out -
    the weaker side of a contradiction loses. Frames out of play choose
    nothing. Without `lives` the path breaks wherever a jump pays (`jump`).
    """
    n = len(times)
    speeds = list(speed) if isinstance(speed, (list, tuple, np.ndarray)) else [float(speed)] * n
    if lives is not None:
        return _decode_lives(times, candidates, speeds, margin, window, support_within, lives)
    # best[f][k]: best score of a path ending in candidate k of frame f; back[f][k]: (frame, cand) before it.
    best: list[list[float]] = [[0.0] * len(c) for c in candidates]
    back: list[list[tuple[int, int] | None]] = [[None] * len(c) for c in candidates]
    # The best score of any path ending at or before frame f, for starting anew after a break.
    upto = [0.0] * (n + 1)
    upto_at: list[tuple[int, int] | None] = [None] * (n + 1)
    for f in range(n):
        upto[f + 1], upto_at[f + 1] = upto[f], upto_at[f]
        for k, (p, inl) in enumerate(candidates[f]):
            e = emission(inl)
            # Start anew (after a break, or at the very start).
            score, prev = upto[f] + e - (jump if upto_at[f] is not None else 0.0), upto_at[f]
            for g in range(max(0, f - window), f):
                dt = times[f] - times[g]
                for j, (q, _) in enumerate(candidates[g]):
                    if np.linalg.norm(p - q) <= max(speeds[f], speeds[g]) * dt + margin and best[g][j] + e > score:
                        score, prev = best[g][j] + e, (g, j)
            best[f][k], back[f][k] = score, prev
            if score > upto[f + 1]:
                upto[f + 1], upto_at[f + 1] = score, (f, k)
    return _choices(times, candidates, speeds, margin, support_within, best, upto_at[n], back, None)


def _decode_lives(times, candidates, speeds, margin, window, support_within, lives) -> list[Choice]:
    n = len(times)
    best: list[list[float]] = [[0.0] * len(c) for c in candidates]
    back: list[list[tuple[int, int] | None]] = [[None] * len(c) for c in candidates]
    # Per life, the best path ending in it so far: (score, (frame, cand)); and the best over all
    # lives before the current one, from which a new life starts for free.
    in_life: dict[int, tuple[float, tuple[int, int]]] = {}
    before: tuple[float, tuple[int, int] | None] = (0.0, None)
    current: int | None = None
    order: list[int] = []
    for f in range(n):
        life = lives[f]
        if life is None:
            continue
        if life != current:
            # Entering a life: every path ending in an earlier one may carry on from here, free.
            for L in order:
                if L in in_life and in_life[L][0] > before[0]:
                    before = in_life[L]
            if life not in order:
                order.append(life)
            current = life
        for k, (p, inl) in enumerate(candidates[f]):
            e = emission(inl)
            score, prev = before[0] + e, before[1]
            # Within the life: from a recent frame, or from the life's best path however long ago,
            # as long as the step keeps to the speed.
            tries = [(g, j) for g in range(max(0, f - window), f) if lives[g] == life for j in range(len(candidates[g]))]
            if life in in_life:
                tries.append(in_life[life][1])
            for g, j in tries:
                q = candidates[g][j][0]
                dt = times[f] - times[g]
                if best[g][j] + e > score and np.linalg.norm(p - q) <= max(speeds[f], speeds[g]) * dt + margin:
                    score, prev = best[g][j] + e, (g, j)
            # Starting from an earlier life while this one already has a path leaves that path's
            # frames out: the scores at the end decide which stretch of the life was right.
            best[f][k], back[f][k] = score, prev
            if np.isfinite(score) and (life not in in_life or score > in_life[life][0]):
                in_life[life] = (score, (f, k))
    end: tuple[int, int] | None = None
    top = before[0]
    end = before[1]
    for L in order:
        if L in in_life and in_life[L][0] > top:
            top, end = in_life[L]
    return _choices(times, candidates, speeds, margin, support_within, best, end, back, lives)


def _choices(times, candidates, speeds, margin, support_within, best, end, back, lives) -> list[Choice]:
    n = len(times)
    window = 8
    chosen: list[int | None] = [None] * n
    at = end
    while at is not None:
        f, k = at
        chosen[f] = k
        at = back[f][k]
    out = []
    for f in range(n):
        if chosen[f] is None:
            out.append(Choice(None, 0))
            continue
        p = candidates[f][chosen[f]][0]
        support = 0
        for g in range(max(0, f - window), min(n, f + window + 1)):
            if g == f or chosen[g] is None or abs(times[f] - times[g]) > support_within:
                continue
            if lives is not None and lives[g] != lives[f]:
                continue
            q = candidates[g][chosen[g]][0]
            if np.linalg.norm(p - q) <= max(speeds[f], speeds[g]) * abs(times[f] - times[g]) + margin:
                support += 1
        out.append(Choice(chosen[f], support))
    return out
