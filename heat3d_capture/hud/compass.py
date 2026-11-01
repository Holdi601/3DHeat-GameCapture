"""
Which way the player faces, from the compass strip at the top of the screen.

The strip prints bearings (numbers every so many degrees, letters at the
cardinal points) that slide under a fixed mark. Two labels read off it fix
both the strip's scale (pixels per degree, which differs between the normal
view and a vehicle's sight) and the bearing under the mark. A single label
fixes nothing, since the scale is unknown, and is not used.

The minimap gives heading too, but only relative to the mosaic it builds; the
compass is what turns that into north. A run needs only a handful of good
compass reads for that, so the strip is read every few seconds, not every
sample.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .ocr import Text


@dataclass
class Bearing:
    t: float
    #: Degrees clockwise from north, of the view.
    heading: float
    #: Pixels per degree, in reference-screen pixels.
    scale: float
    labels: int


def _wrap(d: float) -> float:
    return (d + 180.0) % 360.0 - 180.0


def labels(texts: list[Text], letters: dict[str, float]) -> list[tuple[float, float]]:
    """(x, bearing) for every compass label among the texts. A box that holds several labels is spread over its width."""
    out = []
    for t in texts:
        tokens = re.findall(r"[0-9]{2,3}|[A-Za-z]+", t.text)
        if not tokens:
            continue
        values = []
        for tok in tokens:
            up = tok.upper()
            if up in letters:
                values.append(letters[up])
            elif tok.isdigit() and int(tok) < 360 and int(tok) % 15 == 0 and int(tok) > 0:
                values.append(float(int(tok)))
            else:
                values = []
                break
        if not values:
            continue
        step = (t.x1 - t.x0) / len(values)
        for i, v in enumerate(values):
            out.append((t.x0 + step * (i + 0.5), v))
    return out


def solve(found: list[tuple[float, float]], mark: float, *, scale_range=(1.2, 8.0)) -> tuple[float, float] | None:
    """
    Heading under `mark` and pixels per degree, from labels (x, bearing); None unless two or more agree.

    Every pair of labels proposes a scale; the median of the plausible ones is
    taken, and each label then proposes a heading. The answer stands only if
    most labels agree on it to within two degrees.
    """
    if len(found) < 2:
        return None
    found = sorted(found)
    scales = []
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            (xa, ba), (xb, bb) = found[i], found[j]
            db = _wrap(bb - ba)
            if abs(db) < 1e-6:
                continue
            k = (xb - xa) / db
            if scale_range[0] <= k <= scale_range[1]:
                scales.append(k)
    if not scales:
        return None
    scales.sort()
    k = scales[len(scales) // 2]
    heads = [(b - (x - mark) / k) % 360.0 for x, b in found]
    # Circular median: the proposal with the smallest summed distance to the others.
    best = min(heads, key=lambda h: sum(abs(_wrap(h - o)) for o in heads))
    agree = [h for h in heads if abs(_wrap(h - best)) <= 2.0]
    if len(agree) < 2 or len(agree) * 2 < len(heads) + 1:
        return None
    mean = math.degrees(math.atan2(
        sum(math.sin(math.radians(h)) for h in agree), sum(math.cos(math.radians(h)) for h in agree)
    )) % 360.0
    return mean, k


def blobs(image) -> list[tuple[int, int, int, int]]:
    """
    The labels on a strip, as boxes (x0, y0, x1, y1): bright, colourless ink, grouped across small gaps.

    The text detector reads a compass strip as one long line and loses where
    each label is, which is the whole point; finding the labels by their ink
    keeps their positions, and each is then read on its own. Tick marks are
    thin and short and are dropped.
    """
    import cv2
    import numpy as np

    mx = image.max(axis=2).astype(np.int16)
    mn = image.min(axis=2).astype(np.int16)
    ink = ((mx > 170) & (mx - mn < 70)).astype(np.uint8)
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    h = image.shape[0]
    parts = []
    for i in range(1, n):
        x, y, w, hh, area = stats[i]
        if hh < 0.18 * h or hh > 0.7 * h or area < 6:
            continue
        if w <= 0.12 * hh and hh < 0.3 * h:
            continue
        parts.append([x, y, x + w, y + hh])
    parts.sort()
    groups: list[list[int]] = []
    for p in parts:
        if groups:
            g = groups[-1]
            gap = p[0] - g[2]
            height = max(g[3] - g[1], p[3] - p[1])
            if gap < 0.45 * height and abs((p[1] + p[3]) - (g[1] + g[3])) < height:
                g[0], g[1], g[2], g[3] = min(g[0], p[0]), min(g[1], p[1]), max(g[2], p[2]), max(g[3], p[3])
                continue
        groups.append(list(p))
    # A label is a few characters: wider than a tick, not a whole line of text.
    return [tuple(g) for g in groups if (g[2] - g[0]) >= 0.35 * (g[3] - g[1]) and (g[2] - g[0]) < 4.5 * (g[3] - g[1])]


def read(reader, t: float, strips: list[tuple], letters: dict[str, float], mark_ref: float) -> Bearing | None:
    """
    The heading at time `t`, from the first strip that gives one.

    `strips` are (image, x_of_strip_left_in_reference_px, reference_px_per_image_px).
    """
    import cv2

    for image, left, per in strips:
        boxes = blobs(image)
        if len(boxes) < 2:
            continue
        h, w = image.shape[:2]
        crops = []
        for x0, y0, x1, y1 in boxes:
            pad = max(2, (y1 - y0) // 3)
            crop = image[max(0, y0 - pad) : min(h, y1 + pad), max(0, x0 - pad) : min(w, x1 + pad)]
            # The recogniser is unsure of a lone letter with no margin round it.
            crops.append(cv2.copyMakeBorder(crop, pad, pad, 2 * pad, 2 * pad, cv2.BORDER_REPLICATE))
        # A low bar: a single letter reads with little confidence, and a wrong
        # label is outvoted by the others in `solve`.
        texts = [
            Text(x0, y0, x1, y1, text, score)
            for (x0, y0, x1, y1), (text, score) in zip(boxes, reader.recognise(crops))
            if score >= 0.15
        ]
        found = [(left + x * per, b) for x, b in labels(texts, letters)]
        res = solve(found, mark_ref)
        if res is not None:
            return Bearing(t=t, heading=res[0], scale=res[1], labels=len(found))
    return None


def north_offset(pairs: list[tuple[float, float]]) -> tuple[float, float, int] | None:
    """
    From (compass heading, mosaic heading) pairs: the turn that puts the mosaic north up.

    Returns (offset, spread, agreeing): add `offset` to a mosaic heading to get a
    bearing. `spread` is the median disagreement in degrees, `agreeing` how many
    pairs lie within 10 degrees of the answer.
    """
    if not pairs:
        return None
    diffs = [(c - m) % 360.0 for c, m in pairs]
    best = min(diffs, key=lambda h: sum(min(abs(_wrap(h - o)), 30.0) for o in diffs))
    near = [d for d in diffs if abs(_wrap(d - best)) <= 10.0]
    off = math.degrees(math.atan2(
        sum(math.sin(math.radians(d)) for d in near), sum(math.cos(math.radians(d)) for d in near)
    )) % 360.0
    spread = sorted(abs(_wrap(d - off)) for d in diffs)[len(diffs) // 2]
    return off, spread, len(near)
