"""
The kill feed, read row by row and turned into events.

A row is `killer  [weapon]  [marker]  victim`. Names are read with OCR; the
weapon is not named (the feed shows an icon, and there is no list of icons to
name it from), but every distinct icon silhouette gets a class of its own, so
"the same weapon" is still something that can be counted. Colours say whose
side a name is on, relative to the player: the profile's friendly colour,
enemy colour, and the neutral (pale) colour the game uses for the player's own
name.

Rows stay up for several seconds and scroll as new ones arrive, so a row is
seen many times. An event is one killer-victim pair seen within a window; its
time is the first sample that showed it, and its names are the reads that came
up most often across all the samples that showed it - one bad read does not
rename anyone.

The feed is public on-screen information about everyone in the match, and all
of it is kept, but only as what the feed said: who, whom, with what, when.
Positions come only from the player's own minimap, and only for the player.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from .ocr import Text, clean_name, similarity

FRIENDLY = "friendly"
ENEMY = "enemy"
NEUTRAL = "neutral"
SQUAD = "squad"


def text_colour(image: np.ndarray, box: Text) -> tuple[str, np.ndarray]:
    """
    Which side a name's colour says it is on, and the colour itself (BGR).

    The text is told from what is behind it by how far each pixel is from the
    box's median: names are drawn with some transparency, so on a bright sky
    an orange name is a darkening of the blue channel rather than anything
    orange. What survives every background is the sign of red-minus-blue in
    that difference.
    """
    h, w = image.shape[:2]
    x0, y0 = max(0, int(box.x0)), max(0, int(box.y0))
    x1, y1 = min(w, int(math.ceil(box.x1))), min(h, int(math.ceil(box.y1)))
    patch = image[y0:y1, x0:x1].reshape(-1, 3).astype(np.float32)
    if len(patch) < 8:
        return NEUTRAL, np.zeros(3)
    bg = np.median(patch, axis=0)
    d = patch - bg
    n = np.linalg.norm(d, axis=1)
    top = n >= np.percentile(n, 80)
    dd = d[top].mean(axis=0)
    pix = patch[top].mean(axis=0)
    b, g, r = dd
    norm = float(np.linalg.norm(dd)) + 1.0
    s = (r - b) / norm
    if s > 0.22:
        return ENEMY, pix
    if s < -0.2:
        return FRIENDLY, pix
    pb, pg, pr = pix
    if pg - (pr + pb) / 2 > 18 and pg - max(pr, pb) > 6:
        return SQUAD, pix
    return NEUTRAL, pix


@dataclass
class Row:
    """One kill-feed row as read from one sample."""

    y: float
    killer: str
    victim: str
    killer_side: str
    victim_side: str
    #: The weapon icon's silhouette (a small binary picture), for classing; None when not found.
    icon: np.ndarray | None = None
    #: What stood between the icon and the victim: "skull", "arrow", "chevrons", "crosses" or "".
    marker: str = ""
    score: float = 0.0


def _ink(band: np.ndarray) -> np.ndarray:
    """Pixels that are drawn, in a strip of the feed: far from the strip's own background."""
    flat = band.reshape(-1, 3).astype(np.float32)
    bg = np.median(flat, axis=0)
    d = np.linalg.norm(band.astype(np.float32) - bg, axis=2)
    return (d > max(45.0, float(np.percentile(d, 60)) * 1.6)).astype(np.uint8)


def _icons(
    image: np.ndarray, y0: int, y1: int, x0: int, x1: int, text_h: float, colour: np.ndarray | None = None
) -> tuple[np.ndarray | None, str]:
    """
    The weapon icon's silhouette and the marker, from the gap between the two names.

    The weapon is drawn in the killer's colour: with `colour` (the killer's
    name as it came out on this background) the silhouette is the pixels of
    that colour, which leaves the background out of it far better than
    "different from the background" does.
    """
    import cv2

    if x1 - x0 < text_h:
        return None, ""
    band = image[y0:y1, x0:x1]
    ink = _ink(band)
    if colour is not None:
        near = np.linalg.norm(band.astype(np.float32) - colour.astype(np.float32), axis=2) < 70
        weapon_ink = (near & (ink > 0)).astype(np.uint8)
    else:
        weapon_ink = ink
    n, labels, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    comps = [stats[i] for i in range(1, n) if stats[i][cv2.CC_STAT_AREA] >= max(6, text_h * text_h * 0.02)]
    if not comps:
        return None, ""
    comps.sort(key=lambda s: s[cv2.CC_STAT_LEFT])
    # Group components that touch (an icon is often drawn in pieces).
    groups: list[list[np.ndarray]] = []
    for s in comps:
        left = s[cv2.CC_STAT_LEFT]
        if groups:
            prev_right = max(g[cv2.CC_STAT_LEFT] + g[cv2.CC_STAT_WIDTH] for g in groups[-1])
            if left - prev_right < 0.35 * text_h:
                groups[-1].append(s)
                continue
        groups.append([s])

    def extent(g: list[np.ndarray]) -> tuple[int, int, int, int]:
        xa = min(s[cv2.CC_STAT_LEFT] for s in g)
        ya = min(s[cv2.CC_STAT_TOP] for s in g)
        xb = max(s[cv2.CC_STAT_LEFT] + s[cv2.CC_STAT_WIDTH] for s in g)
        yb = max(s[cv2.CC_STAT_TOP] + s[cv2.CC_STAT_HEIGHT] for s in g)
        return xa, ya, xb, yb

    marker = ""
    if len(groups) >= 2:
        xa, ya, xb, yb = extent(groups[-1])
        w, h = xb - xa, yb - ya
        if w < 2.2 * text_h:
            marker = _marker(ink[ya:yb, xa:xb], len(groups[-1]), text_h)
            if marker:
                groups = groups[:-1]
    # The weapon: the widest group left.
    best = max(groups, key=lambda g: extent(g)[2] - extent(g)[0])
    xa, ya, xb, yb = extent(best)
    sil = weapon_ink[ya:yb, xa:xb]
    if sil.size and sil.any():
        ys, xs = np.nonzero(sil)
        sil = sil[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    if sil.size == 0 or (xb - xa) < 0.8 * text_h:
        return None, marker
    return cv2.resize(sil.astype(np.float32), (48, 16), interpolation=cv2.INTER_AREA), marker


def _marker(sil: np.ndarray, pieces: int, text_h: float) -> str:
    """Name the small icon before a victim by its shape."""
    import cv2

    h, w = sil.shape
    if h == 0 or w == 0:
        return ""
    fill = float(sil.mean())
    if pieces >= 3:
        return "crosses"
    if h < 0.75 * text_h and w < 0.75 * text_h:
        return "arrow"
    # Holes: the skull's eyes. Count background regions not touching the border.
    inv = (1 - sil).astype(np.uint8)
    n, labels = cv2.connectedComponents(inv, connectivity=4)
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])))
    holes = sum(1 for i in range(1, n) if i not in border and (labels == i).sum() >= 3)
    if holes >= 1 and 0.7 < w / h < 1.4 and fill > 0.45:
        return "skull"
    if w / h >= 1.2 or pieces == 2:
        return "chevrons"
    return "other"


#: Performance counters some players run in that corner of the screen, read as text.
_COUNTER = re.compile(r"\b(fps|cpu|gpu|sim|mp/?s)\s*[0-9]", re.IGNORECASE)


def parse_rows(image: np.ndarray, texts: list[Text], *, pitch: float, text_h: float, reader=None) -> list[Row]:
    """
    Rows out of one kill-feed crop's OCR. `pitch` and `text_h` are in this crop's pixels.

    Lines too small to be a name (an fps counter someone runs in that corner)
    and lines with a slash in them are not names and are dropped. `reader`
    (an `ocr.Reader`) re-reads the halves of a line that ran across an icon.
    """
    names = [
        t for t in texts
        if t.height >= 0.6 * text_h and "/" not in t.text and not _COUNTER.search(t.text) and clean_name(t.text)
    ]
    names.sort(key=lambda t: t.cy)
    rows: list[list[Text]] = []
    for t in names:
        if rows and abs(t.cy - np.mean([r.cy for r in rows[-1]])) < 0.4 * pitch:
            rows[-1].append(t)
        else:
            rows.append([t])
    out: list[Row] = []
    for row in rows:
        row.sort(key=lambda t: t.x0)
        sides = [text_colour(image, t)[0] for t in row]
        # Neighbouring pieces of one name (a space read as a gap) join up.
        merged: list[tuple[Text, str]] = []
        for t, side in zip(row, sides):
            if merged:
                last, lside = merged[-1]
                # One colour, or one side washed out to neutral by the background.
                same = lside == side or NEUTRAL in (lside, side)
                if same and t.x0 - last.x1 < 0.6 * text_h:
                    merged[-1] = (
                        Text(last.x0, min(last.y0, t.y0), t.x1, max(last.y1, t.y1), f"{last.text} {t.text}",
                             min(last.score, t.score)),
                        side,
                    )
                    continue
            merged.append((t, side))
        if len(merged) == 1:
            split = _split(image, merged[0][0], text_h, reader)
            if split is None:
                lone = _killerless(image, merged[0][0], merged[0][1], text_h)
                if lone is not None:
                    out.append(lone)
                continue
            merged = split
        (k, ks), (v, vs) = merged[0], merged[-1]
        killer, victim = clean_name(k.text), clean_name(v.text)
        if not killer or not victim:
            continue
        y0 = int(max(0, min(k.y0, v.y0)))
        y1 = int(max(k.y1, v.y1))
        icon, marker = _icons(image, y0, y1, int(k.x1) + 2, int(v.x0) - 2, text_h, colour=text_colour(image, k)[1])
        if icon is None and (ks == vs or NEUTRAL in (ks, vs)) and v.x0 - k.x1 < 2.5 * text_h:
            # Two words of one name in one colour with nothing between them: a
            # row whose killer has faded out, not a kill between namesakes.
            continue
        out.append(Row(
            y=float((k.cy + v.cy) / 2), killer=killer, victim=victim, killer_side=ks, victim_side=vs,
            icon=icon, marker=marker, score=min(k.score, v.score),
        ))
    return out


def _killerless(image: np.ndarray, t: Text, side: str, text_h: float) -> Row | None:
    """
    A row with a victim and an icon but no killer: a death to the world (a fall, the
    play area, a vehicle wreck), or a killer's name faded out before the victim's.

    Only a name in the victims' column counts (its right end near the feed's
    right edge) with an icon close to its left; anything else on its own is a
    piece of a row that will be read whole in another sample.
    """
    import cv2

    h, w = image.shape[:2]
    if t.x1 < w - 2.0 * text_h:
        return None
    victim = clean_name(t.text)
    if not victim:
        return None
    y0, y1 = int(max(0, t.y0)), int(min(h, t.y1))
    x0, x1 = int(max(0, t.x0 - 3.0 * text_h)), int(max(0, t.x0 - 2))
    if x1 - x0 < text_h or y1 <= y0:
        return None
    ink = _ink(image[y0:y1, x0:x1])
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if not any(stats[i][cv2.CC_STAT_HEIGHT] >= 0.5 * text_h for i in range(1, n)):
        return None
    return Row(y=float(t.cy), killer="", victim=victim, killer_side="", victim_side=side, score=t.score)


def _split(image: np.ndarray, t: Text, text_h: float, reader=None) -> list[tuple[Text, str]] | None:
    """
    One read that ran across the icon from one name into the other: cut it at the widest gap.

    Only when the two halves differ in colour - the killer and the victim of a
    kill are on opposite sides - so a long name with a space in it is not cut.
    """
    x0, x1 = int(t.x0), int(t.x1)
    y0, y1 = int(max(0, t.y0)), int(t.y1)
    band = image[y0:y1, x0:x1]
    if band.size == 0:
        return None
    ink = _ink(band).max(axis=0)
    runs, start = [], None
    for i, v in enumerate(ink):
        if not v and start is None:
            start = i
        elif v and start is not None:
            runs.append((start, i))
            start = None
    runs = [r for r in runs if r[0] > 0 and r[1] - r[0] >= 0.5 * text_h]
    if not runs:
        return None
    a, b = max(runs, key=lambda r: r[1] - r[0])
    left = Text(t.x0, t.y0, t.x0 + a, t.y1, "", t.score)
    right = Text(t.x0 + b, t.y0, t.x1, t.y1, "", t.score)
    ls, rs = text_colour(image, left)[0], text_colour(image, right)[0]
    if ls == rs or NEUTRAL in (ls, rs):
        return None
    if reader is not None:
        crops = [image[y0:y1, x0 : x0 + a], image[y0:y1, x0 + b : x1]]
        (lt, _), (rt, _) = reader.recognise(crops)
        left.text, right.text = lt, rt
    else:
        # No reader to hand: cut the joint read at the gap's share of its words.
        words = t.text.split()
        if len(words) < 2:
            return None
        share = a / max(1, x1 - x0)
        cut = max(1, min(len(words) - 1, round(share * len(words))))
        left.text, right.text = " ".join(words[:cut]), " ".join(words[cut:])
    return [(left, ls), (right, rs)]


@dataclass
class FeedEvent:
    """One kill-feed line, from its first appearance to its last."""

    t: float
    last: float
    killers: Counter = field(default_factory=Counter)
    victims: Counter = field(default_factory=Counter)
    killer_side: Counter = field(default_factory=Counter)
    victim_side: Counter = field(default_factory=Counter)
    markers: Counter = field(default_factory=Counter)
    icons: list[np.ndarray] = field(default_factory=list)
    seen: int = 0
    weapon: str = ""

    @property
    def killer(self) -> str:
        """The killer's name; empty when no sighting showed one."""
        named = Counter({k: n for k, n in self.killers.items() if k})
        return _best_read(named) if named else ""

    @property
    def victim(self) -> str:
        return _best_read(self.victims)

    @property
    def marker(self) -> str:
        m = [k for k, _ in self.markers.most_common() if k]
        return m[0] if m and self.markers[m[0]] * 2 >= self.seen else ""

    def side(self, which: str) -> str:
        c = self.killer_side if which == "killer" else self.victim_side
        return c.most_common(1)[0][0] if c else ""

    def matches(self, row: Row, t: float, window: float, life: float) -> bool:
        if t - self.last > window or t - self.t > life:
            return False
        v = max(_alike(row.victim, x) for x in self.victims)
        if not row.killer or not any(self.killers.elements()):
            # A row without its killer (faded out, or there was none): the victim decides.
            return v >= 0.8
        k = max(_alike(row.killer, x) for x in self.killers if x)
        # Both alike, and one of them clearly the same name.
        return min(k, v) >= 0.7 and max(k, v) >= 0.8

    def add(self, row: Row, t: float) -> None:
        self.last = t
        self.seen += 1
        self.killers[row.killer] += 1
        self.victims[row.victim] += 1
        if row.killer:
            self.killer_side[row.killer_side] += 1
        self.victim_side[row.victim_side] += 1
        self.markers[row.marker] += 1
        if row.icon is not None and len(self.icons) < 6:
            self.icons.append(row.icon)


def _alike(a: str, b: str) -> float:
    """
    How alike two reads of a name are, where one may be cut short.

    A name at the end of a row can be partly covered (another overlay, the
    row sliding in), and the read is then the start of the name: it is alike
    when it agrees with the start of the other.
    """
    s = similarity(a, b)
    n = min(len(a), len(b))
    if n >= 4 and len(a) != len(b):
        s = max(s, 0.9 * similarity(a[:n], b[:n]))
    return s


def _best_read(reads: Counter) -> str:
    """The most frequent read, or a longer one it is the start of (the full name, when the common read was cut short)."""
    best, n = reads.most_common(1)[0]
    for other, m in reads.most_common():
        if len(other) > len(best) + 1 and m >= max(2, n // 3) and similarity(other[: len(best)], best) >= 0.9:
            best = other
    return best


class Feed:
    """
    Rows in, events out: the de-duplication across samples.

    A row is the same event as one read before when its names are alike, it
    was last read less than `window` seconds ago (a visible row is read at
    least every couple of seconds), and the event is younger than `life` (no
    row stays up longer; the same pair again later is a new kill).
    """

    def __init__(self, *, window: float = 5.0, life: float = 14.0):
        self.window = window
        self.life = life
        self.events: list[FeedEvent] = []

    def add(self, t: float, rows: list[Row]) -> None:
        for row in rows:
            found = None
            for e in reversed(self.events):
                if t - e.last > self.window:
                    break
                if e.matches(row, t, self.window, self.life):
                    found = e
                    break
            if found is None:
                found = FeedEvent(t=t, last=t)
                self.events.append(found)
            found.add(row, t)
            # Keep the list in order of last sighting, so the scan above can stop early.
            self.events.sort(key=lambda e: e.last)

    def finish(self, *, min_seen: int = 2) -> list[FeedEvent]:
        """
        The events, in order of first appearance.

        A row read once only is dropped when `min_seen` > 1: a real row stays up
        for seconds and is read many times, a misread survives one sample.
        """
        out = [e for e in self.events if e.seen >= min_seen]
        out.sort(key=lambda e: e.t)
        classify_icons(out)
        return out


def classify_icons(events: list[FeedEvent], *, threshold: float = 0.75) -> None:
    """Give events whose weapon icons look alike the same class name: icon01, icon02, ..."""
    classes: list[np.ndarray] = []
    for e in events:
        if not e.icons:
            e.weapon = ""
            continue
        sil = np.mean(e.icons, axis=0)
        best, score = -1, 0.0
        for i, c in enumerate(classes):
            s = _likeness(sil, c)
            if s > score:
                best, score = i, s
        if best >= 0 and score >= threshold:
            e.weapon = f"icon{best + 1:02d}"
        else:
            classes.append(sil)
            e.weapon = f"icon{len(classes):02d}"


def _likeness(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float((a * b).sum() / d) if d > 0 else 0.0


class Gate:
    """
    Whether the feed has changed enough since it was last read to read it again.

    OCR is the expensive part of reading a feed, and most samples show the
    rows the last one showed. The test is on the feed's strongly coloured
    pixels (the names and icons) at low resolution: a new row, a scroll or a
    row going away moves a good share of them; a cloud behind the feed does not.
    Every `every` seconds it reads regardless, so a faded row is not missed.
    """

    def __init__(self, *, change: float = 0.12, every: float = 2.0):
        self.change = change
        self.every = every
        self.last_t = -1e9
        self.last: np.ndarray | None = None

    @staticmethod
    def signature(image: np.ndarray) -> np.ndarray:
        import cv2

        small = cv2.resize(image, (image.shape[1] // 4, image.shape[0] // 4), interpolation=cv2.INTER_AREA)
        mx = small.max(axis=2).astype(np.int16)
        mn = small.min(axis=2).astype(np.int16)
        return ((mx - mn) > 70) & (mx > 120)

    def due(self, t: float, image: np.ndarray) -> bool:
        sig = self.signature(image)
        ink = int(sig.sum())
        if ink < 6:
            # Nothing coloured at all: an empty feed (or a menu).
            if self.last is not None and int(self.last.sum()) >= 6:
                self.last = sig
            return False
        if self.last is None or t - self.last_t >= self.every:
            self._take(t, sig)
            return True
        diff = int((sig ^ self.last).sum())
        if diff / max(ink, int(self.last.sum()), 40) > self.change:
            self._take(t, sig)
            return True
        return False

    def _take(self, t: float, sig: np.ndarray) -> None:
        self.last = sig
        self.last_t = t


class FeedReader:
    """
    OCR for a kill feed that is read again and again: lines already read are not read twice.

    Finding the lines is cheap; reading them is most of the cost. A line whose
    picture matches one read in the previous sample (rows scroll, so it may have
    moved) takes that text instead of being read again.
    """

    def __init__(self, reader, *, likeness: float = 0.85):
        self.reader = reader
        self.likeness = likeness
        self.previous: list[tuple[np.ndarray, Text]] = []
        self.read_lines = 0
        self.reused_lines = 0

    @staticmethod
    def _signature(image: np.ndarray, t: Text) -> np.ndarray | None:
        import cv2

        h, w = image.shape[:2]
        x0, y0 = max(0, int(t.x0)), max(0, int(t.y0))
        x1, y1 = min(w, int(math.ceil(t.x1))), min(h, int(math.ceil(t.y1)))
        if x1 - x0 < 4 or y1 - y0 < 4:
            return None
        crop = image[y0:y1, x0:x1].astype(np.float32)
        # The text's own colour against the box's median: the background behind a
        # translucent name changes from sample to sample, the name does not.
        crop = np.linalg.norm(crop - np.median(crop.reshape(-1, 3), axis=0), axis=2)
        sig = cv2.resize(crop, (96, 16), interpolation=cv2.INTER_AREA)
        sig -= sig.mean()
        n = float(np.linalg.norm(sig))
        if n <= 0:
            return None
        # The aspect ratio rides along in the first cell, so a short and a long
        # line that squash to similar pictures still differ.
        return np.append(sig.ravel() / n, (x1 - x0) / (y1 - y0))

    def read(self, image: np.ndarray, keep=None) -> list[Text]:
        """The lines in `image`; with `keep`, only the boxes `keep(box)` is true for are read at all."""
        boxes = self.reader.detect(image)
        if keep is not None:
            boxes = [b for b in boxes if keep(b)]
        sigs = [self._signature(image, b) for b in boxes]
        todo: list[int] = []
        for i, (b, sig) in enumerate(zip(boxes, sigs)):
            hit = None
            if sig is not None:
                for psig, pt in self.previous:
                    if abs(psig[-1] - sig[-1]) > 0.12 * sig[-1]:
                        continue
                    if float((psig[:-1] * sig[:-1]).sum()) >= self.likeness:
                        hit = pt
                        break
            if hit is not None:
                b.text, b.score = hit.text, hit.score
                self.reused_lines += 1
            else:
                todo.append(i)
        if todo:
            h, w = image.shape[:2]
            crops = []
            for i in todo:
                b = boxes[i]
                pad = 0.12 * b.height
                crops.append(image[max(0, int(b.y0 - pad)) : min(h, int(b.y1 + pad) + 1),
                                   max(0, int(b.x0 - pad)) : min(w, int(b.x1 + pad) + 1)])
            for i, (text, score) in zip(todo, self.reader.recognise(crops)):
                boxes[i].text, boxes[i].score = text, score
            self.read_lines += len(todo)
        self.previous = [(sig, b) for b, sig in zip(boxes, sigs) if sig is not None and b.text]
        return [b for b in boxes if b.text and b.score >= 0.5]
