"""
The player's own actions, read from the points popup the game draws under the crosshair.

Every time the player scores - a kill, an assist, a revive, a resupply, a
capture tick - Battlefield 6 shows it just left of and below the screen's
centre, in one popup that grows as more happens:

    [ribbon]  (icon)                    a title row, now and then: a ribbon or a multi-kill
    (icons)  300                        one icon per action, and the popup's running total
    Name                                who it was about (the victim, the teammate), for a moment
    [KILL x2] [VEHICLE DESTROYED]       one boxed tag per kind of action, with a count

The popup stays while the player keeps scoring and for about three seconds
after, then folds into one line (`[KILL x2] 300`) and goes. The tag row is a
sliding window of the last few kinds; a kind that comes back keeps counting.

Each read of the popup becomes a `PopupRead`: the tags (matched to a table of
known texts, tolerant of the recogniser's slips), the total, the name and its
colour, the title. `Popups` puts the reads of one popup together and turns
the growth of each tag's count into events, timed at the first read that
showed them. A tag the table does not know is kept as an event `points` with
its text, never dropped and never guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

import numpy as np

from .ocr import Text, clean_name

# ---------------------------------------------------------------- the table

#: What each tag means, as (text the game prints, event). The event names are
#: the table's `event` column. Several texts can mean one event.
TAGS: tuple[tuple[str, str], ...] = (
    ("KILL", "kill"),
    # A kill by a headshot shows HEADSHOT in place of KILL.
    ("HEADSHOT", "kill"),
    ("HEADSHOT KILL", "kill"),
    ("ASSIST", "assist"),
    ("KILL ASSIST", "assist"),
    ("DAMAGE ASSIST", "assist"),
    ("SQUAD DAMAGE ASSIST", "assist"),
    ("ASSIST COUNTS AS KILL", "kill_assist"),
    ("SUPPRESSION ASSIST", "suppression_assist"),
    ("ENEMY SUPPRESSION", "suppression"),
    ("SMOKE ASSIST", "smoke_assist"),
    ("SQUAD SMOKE ASSIST", "smoke_assist"),
    ("SPOT", "spot"),
    ("SPOTTED", "spot"),
    ("SPOT ASSIST", "spot_assist"),
    ("SPOT BONUS", "spot_assist"),
    ("ENEMY DESIGNATION", "spot"),
    ("REVIVE", "reviving"),
    ("SQUAD REVIVE", "reviving"),
    ("CONCEALED REVIVE", "reviving_bonus"),
    ("HEAL", "heal"),
    ("SQUAD HEAL", "heal"),
    ("SUPPLY", "resupply"),
    ("RESUPPLY", "resupply"),
    ("SQUAD SUPPLY", "resupply"),
    ("REPAIR", "repair"),
    ("VEHICLE REPAIR", "repair"),
    ("SQUAD REPAIR", "repair"),
    ("CAPTURING", "capturing"),
    ("RECAPTURING", "capturing"),
    ("CAPTURED", "capture"),
    ("OBJECTIVE CAPTURED", "capture"),
    ("NEUTRALIZING", "neutralizing"),
    ("NEUTRALIZED", "neutralize"),
    ("OBJECTIVE NEUTRALIZED", "neutralize"),
    ("DEFENDING", "defense"),
    ("OBJECTIVE DEFENDED", "defense"),
    ("ORDER COMPLETED", "order"),
    ("VEHICLE DESTROYED", "vehicle_destroyed"),
    ("VEHICLE DESTROYED SUPPORT", "vehicle_destroyed_assist"),
    ("VEHICLE DISABLED", "vehicle_disabled"),
    ("VEHICLE DAMAGE", "vehicle_damage"),
    ("EQUIPMENT DESTROYED", "equipment_destroyed"),
    ("SQUAD WIPE", "squad_wipe"),
    ("SAVIOR", "savior"),
    ("AVENGER", "avenger"),
    ("OFFENSIVE", "offensive"),
    ("DEFENSIVE", "defensive"),
    ("SPAWNED ON", "teammate_arrived"),
    ("SPAWN ASSIST", "teammate_arrived"),
    ("VEHICLE SPAWN", "teammate_arrived"),
    ("SQUAD VEHICLE SPAWN", "teammate_arrived"),
    ("TEAM TRANSPORT", "transport"),
    ("DRIVER ASSIST", "driver_assist"),
    ("FORCED BAIL", "forced_bail"),
    ("DEFENSE DEPLOYED", "fortify"),
)

#: Titles that say how many kills in a row: the number in `count`.
MULTI_KILLS = {
    "DOUBLE KILL": 2,
    "TRIPLE KILL": 3,
    "QUAD KILL": 4,
    "QUADRUPLE KILL": 4,
    "MULTI KILL": 5,
}


#: Actions the popup names someone with: the victim, the teammate helped. The others
#: (captures, orders, vehicle damage, ribbons) show the name of whatever came before.
ABOUT_SOMEONE = {
    "kill", "assist", "kill_assist", "suppression", "suppression_assist", "smoke_assist", "spot",
    "spot_assist", "driver_assist", "reviving", "reviving_bonus", "heal", "resupply", "repair", "savior",
    "avenger", "offensive", "defensive", "teammate_arrived", "points",
}


def _fold(s: str) -> str:
    """A text as letters only, upper case, with the recogniser's usual letter swaps undone."""
    s = s.upper().replace("Q", "O")
    # A digit between letters is a letter misread.
    s = re.sub(r"(?<=[A-Z])[0-9](?=[A-Z])", lambda m: "OIZEASGTBP"[int(m.group())], s)
    return re.sub(r"[^A-Z]", "", s)


#: Ribbons seen in the title row, to print their names whole when the recogniser runs the words together.
#: Any other title is kept as read.
RIBBONS = (
    "BALLISTIC", "TANK BUSTER", "DEMOLITIONIST", "SPEARHEAD", "TROOPER", "ENGINEER EXPERT", "SENTINEL",
    "FIRE SUPPORT", "PAYBACK", "ROADMASTER", "MARAUDER", "AVENGER", "SAVIOR",
)

_KEYS = [(_fold(t), t, e) for t, e in TAGS]
_TITLE_KEYS = [(_fold(t), t, n) for t, n in MULTI_KILLS.items()]


def _ratio(a: str, b: str) -> float:
    """How alike two folded texts are; I and L, which the recogniser swaps in this font, count as one."""
    r = SequenceMatcher(None, a, b, autojunk=False).ratio()
    if r < 1.0 and ("I" in a or "L" in a):
        r = max(r, SequenceMatcher(None, a.replace("L", "I"), b.replace("L", "I"), autojunk=False).ratio())
    return r


def _need(n: int) -> float:
    """How alike a read has to be to a key of `n` letters to be it: short keys need to be closer."""
    return 0.85 if n <= 5 else 0.8


def _match_whole(s: str) -> tuple[str, str, float] | None:
    """The key `s` (folded) is, when it is clearly one: (printed text, event, likeness)."""
    scored = sorted(((_ratio(s, k), t, e) for k, t, e in _KEYS), reverse=True)
    best, second = scored[0], scored[1]
    if best[0] >= _need(len(s)) and (best[0] >= 0.95 or best[0] - second[0] >= 0.05):
        return best[1], best[2], best[0]
    return None


_SEG_CACHE: dict[str, tuple[float, list[tuple[str, str]]] | None] = {}


def _split(s: str) -> tuple[float, list[tuple[str, str]]] | None:
    """
    `s` (folded) as one or more keys in a row, and how well the worst piece fits:
    the recogniser joins neighbouring tags into one read ("CAPTUREDORDERCOMPLETED").
    None when it cannot be made of keys.
    """
    if s in _SEG_CACHE:
        return _SEG_CACHE[s]
    best: tuple[float, list[tuple[str, str]]] | None = None
    whole = _match_whole(s) if s else None
    if whole is not None:
        best = (whole[2], [(whole[0], whole[1])])
    if len(s) >= 6 and (best is None or best[0] < 0.97):
        # Peel a key off the front, allowing a letter more or less, and split the rest.
        for k, t, e in _KEYS:
            for n in (len(k) - 1, len(k), len(k) + 1):
                if n < 3 or n > len(s) - 3:
                    continue
                r = _ratio(s[:n], k)
                if r < _need(len(k)):
                    continue
                rest = _split(s[n:])
                if rest is not None and (best is None or min(r, rest[0]) > best[0]):
                    best = (min(r, rest[0]), [(t, e)] + rest[1])
    if len(_SEG_CACHE) < 20000:
        _SEG_CACHE[s] = best
    return best


def _segment(s: str) -> list[tuple[str, str]] | None:
    """The keys `s` (folded) is made of, as (printed text, event); None when it is not made of keys."""
    found = _split(s)
    return found[1] if found else None


#: A count after a tag: "x2", "X 3", "×4", or a digit the "x" was lost from.
_COUNT = re.compile(r"(?:\s*[xX×*]\s*|[^A-Za-z0-9]+|(?<=[A-Za-z]))(\d{1,2})(?=[^A-Za-z0-9]|$|[A-Za-z]{3})")


@dataclass
class Tag:
    """One tag of the popup as read once: the event, the text it was matched to (or the raw read), the count."""

    event: str
    text: str
    #: The tag's multiplier: 1 with none printed; None when the read is too damaged to tell.
    count: int | None


def read_tags(raw: str) -> list[Tag] | None:
    """
    The tags in one line of text, or None when the line is not made of tags.

    The count belongs to the tag it follows. A line that is partly known and
    partly not is not trusted as tags; `parse` decides whether an unknown line
    is a tag the table does not know.
    """
    text = raw.strip()
    if not text:
        return None
    parts: list[tuple[str, int | None]] = []
    pos = 0
    for m in _COUNT.finditer(text):
        before = text[pos : m.start()]
        if _fold(before):
            parts.append((before, int(m.group(1))))
        pos = m.end()
    tail = text[pos:].strip()
    if _fold(tail):
        count: int | None = 1
        if tail[-1:] in "xX×" and len(tail) > 3 and _segment(_fold(tail)) is None and _segment(_fold(tail[:-1])):
            # A trailing "x" with its digit lost: a count, but not which.
            tail, count = tail[:-1], None
        parts.append((tail, count))
    if not parts:
        return None
    tags: list[Tag] = []
    for words, count in parts:
        seg = _segment(_fold(words))
        if seg is None:
            return None
        for i, (t, e) in enumerate(seg):
            tags.append(Tag(e, t, count if i == len(seg) - 1 else 1))
    return tags


def read_title(raw: str) -> tuple[str, str, int | None]:
    """A title-row text as (event, text, count): a multi-kill, or a ribbon by its name."""
    s = _fold(raw)
    best = max(((_ratio(s, k), t, n) for k, t, n in _TITLE_KEYS), default=(0.0, "", 0))
    if best[0] >= 0.85:
        return "multi_kills", best[1], best[2]
    known = max(((_ratio(s, _fold(r)), r) for r in RIBBONS), default=(0.0, ""))
    if known[0] >= 0.85:
        number = re.search(r"\d+$", raw.strip())
        return "ribbon", known[1] + (f" {number.group()}" if number and not known[1][-1].isdigit() else ""), None
    words = re.sub(r"[^A-Za-z0-9 ]", " ", raw).upper()
    words = re.sub(r"(?<=[A-Z])(?=\d)", " ", words)
    return "ribbon", " ".join(words.split()), None


def _part_of(s: str, keys: set[str]) -> bool:
    """Whether `s` is (nearly) a stretch of one of `keys`."""
    n = len(s)
    for k in keys:
        if n <= len(k) and any(_ratio(s, k[i : i + n]) >= 0.85 for i in range(len(k) - n + 1)):
            return True
    return False


# ---------------------------------------------------------------- one read


@dataclass(frozen=True)
class Layout:
    """Where the popup's rows are, in reference (1920x1080) pixels."""

    #: The total's left edge is right of this; the tags' and name's right edges are left of `right`.
    number_x: float = 735.0
    right: float = 800.0
    #: Between the icons (or a name, or a folded tag) and the total's first digit: a line the
    #: recogniser ran across it is cut here.
    cut: float = 755.0
    #: Rows by the y of a line's middle. The name is under the total, or (a teammate's action
    #: with no icon) left of it; it is right-aligned, ending right of `name_right`.
    title: tuple[float, float] = (628.0, 664.0)
    number: tuple[float, float] = (672.0, 716.0)
    name: tuple[float, float] = (690.0, 748.0)
    name_right: float = 700.0
    tags: tuple[float, float] = (684.0, 790.0)
    #: A tag the table does not know is believed only in the tag rows, below this.
    tag_rows: float = 714.0
    #: Nothing of the popup reaches left of this.
    left: float = 260.0


@dataclass
class PopupRead:
    t: float
    tags: list[Tag] = field(default_factory=list)
    total: int | None = None
    name: str = ""
    side: str = ""
    titles: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.tags and self.total is None


_DIGITS = re.compile(r"^[\s,.'·]*(\d[\d,.]{0,6})\s*$")


def _number(raw: str) -> int | None:
    m = _DIGITS.match(raw.replace("O", "0").replace("o", "0"))
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if not digits or len(digits) > 5:
        return None
    return int(digits)


def parse(
    t: float, image: np.ndarray | None, texts: list[Text], *, origin: tuple[float, float], scale: float,
    layout: Layout = Layout(),
) -> PopupRead:
    """
    One sample's popup from the OCR of its crop. `origin` is the crop's top left
    in reference pixels and `scale` crop pixels per reference pixel.
    """
    from .killfeed import NEUTRAL, text_colour

    out = PopupRead(t=t)
    ox, oy = origin

    def ref(v: Text) -> tuple[float, float, float]:
        return ox + v.x0 / scale, ox + v.x1 / scale, oy + v.cy / scale

    names: list[tuple[Text, str]] = []
    unknown: list[Text] = []
    for v in texts:
        x0, x1, cy = ref(v)
        if x1 < layout.left:
            continue
        raw = v.text.strip()
        # The total, alone or run together with what is left of it.
        if x1 > layout.cut + 10 and layout.number[0] <= cy <= layout.number[1]:
            n = _number(raw)
            if n is not None:
                if x0 >= layout.cut - 15:
                    out.total = n
                continue
            if x0 < layout.cut - 15:
                m = re.match(r"^(.*?[^\d\s])\s*(\d{1,5})$", raw)
                if m and _number(m.group(2)) is not None:
                    out.total = _number(m.group(2))
                    raw = m.group(1)
                    if not re.search(r"[A-Za-z]", raw):
                        continue
        if layout.title[0] <= cy <= layout.title[1]:
            letters = re.sub(r"[^A-Za-z]", "", raw)
            if len(letters) >= 4 and letters.upper() == letters and x1 >= 500 and x1 <= layout.right:
                out.titles.append(raw)
            continue
        if not (layout.tags[0] <= cy <= layout.tags[1]) or x1 > layout.right + 40:
            continue
        tags = read_tags(raw)
        if tags is not None:
            out.tags.extend(tags)
            continue
        if not re.search(r"[A-Za-z]", raw) or x1 > layout.right:
            continue
        side = text_colour(image, v)[0] if image is not None else NEUTRAL
        letters = re.sub(r"[^A-Za-z]", "", raw)
        if side == NEUTRAL and len(letters) >= 4 and letters.upper() == letters and cy >= layout.tag_rows:
            unknown.append(v)
        elif layout.name[0] <= cy <= layout.name[1]:
            names.append((v, side))
    if out.tags or out.total is not None:
        names = [(v, side) for v, side in names if ref(v)[1] >= layout.name_right]
        # An unknown line is a tag only on the known tags' row, or, with none known, where
        # nothing else could be: a name in an unexpected colour is not a tag.
        rows = [oy + v.cy / scale for v in texts if read_tags(v.text) and oy + v.cy / scale >= layout.tag_rows]
        if rows:
            unknown = [v for v in unknown if any(abs(ref(v)[2] - y) <= 8 for y in rows)]
        elif names:
            unknown = []
        for v in unknown:
            out.tags.append(Tag("points", " ".join(re.sub(r"[^A-Za-z0-9 ]", " ", v.text).upper().split()), 1))
        if names:
            v, side = max(names, key=lambda n: n[0].score)
            out.name, out.side = clean_name(v.text), side
    else:
        out.titles = []
    return out


def split_at_total(
    image: np.ndarray, texts: list[Text], recognise, *, origin: tuple[float, float], scale: float,
    layout: Layout = Layout(),
) -> list[Text]:
    """
    Lines on the total's row that the recogniser ran across from an icon, a name or
    a folded tag into the total ("Name10", "REVIVE185", an icon read as "1"): cut at
    `layout.cut` and each side read again with `recognise` (a list of crops in,
    a list of (text, score) out).
    """
    ox, oy = origin
    cut = (layout.cut - ox) * scale
    out: list[Text] = []
    todo: list[tuple[Text, Text]] = []
    for v in texts:
        cy = oy + v.cy / scale
        if layout.number[0] <= cy <= layout.number[1] and v.x0 < cut - 2 * scale and v.x1 > cut + 12 * scale:
            todo.append((Text(v.x0, v.y0, cut, v.y1, "", v.score), Text(cut, v.y0, v.x1, v.y1, "", v.score)))
        else:
            out.append(v)
    if todo:
        h, w = image.shape[:2]
        crops = []
        for pair in todo:
            for b in pair:
                crops.append(image[max(0, int(b.y0)) : min(h, int(b.y1) + 1), max(0, int(b.x0)) : min(w, int(b.x1) + 1)])
        reads = recognise(crops)
        for i, (left, right) in enumerate(todo):
            for b, (text, score) in zip((left, right), reads[2 * i : 2 * i + 2]):
                if text.strip():
                    b.text, b.score = text, score
                    out.append(b)
    return out


# ---------------------------------------------------------------- popups over time


@dataclass
class PointEvent:
    """One action of the player's, from a popup."""

    t: float
    event: str
    #: The tag's text as the table has it (or the raw read for an unknown tag, or a title).
    text: str
    #: Points the popup's total grew by at this moment; shared with `shared - 1` other events when several came at once.
    points: int | None = None
    shared: int = 1
    #: Who it was about (a kill's victim, the teammate revived), and that name's colour.
    name: str = ""
    side: str = ""
    popup: int = 0
    #: How many reads showed this event's tag at its count or above.
    seen: int = 0
    #: Read once only: not an event unless something else vouches for it.
    weak: bool = False


@dataclass
class Popup:
    index: int
    reads: list[PopupRead] = field(default_factory=list)

    @property
    def start(self) -> float:
        return self.reads[0].t

    @property
    def last(self) -> float:
        return self.reads[-1].t

    def counts(self, reads: int = 2) -> dict[str, int]:
        """Each tag text's highest count shown in `reads` reads or more."""
        seen: dict[str, list[int]] = {}
        for r in self.reads:
            for tag in r.tags:
                if tag.count is not None:
                    seen.setdefault(tag.text, []).append(tag.count)
        out = {}
        for text, cs in seen.items():
            cs.sort(reverse=True)
            if len(cs) >= reads:
                out[text] = cs[reads - 1]
        return out

    def last_change(self) -> float:
        """When the popup last grew: its total, or a tag's count, went up."""
        best_total = -1
        best: dict[str, int] = {}
        when = self.start
        for r in self.reads:
            grew = r.total is not None and r.total > best_total
            for g in r.tags:
                if g.count is not None and g.count > best.get(g.text, 0):
                    best[g.text] = g.count
                    grew = True
            if r.total is not None:
                best_total = max(best_total, r.total)
            if grew:
                when = r.t
        return when


class Popups:
    """
    Reads in, events out.

    Reads of one popup follow each other with no more than `gap` seconds of
    nothing between them. A popup that seems to end and come back - with
    every tag at its count or above and a total no smaller, before it could
    have folded away (`stays` seconds after it last grew) - was one popup the
    recogniser lost for a while (blur, a bright background), not a second
    one: nothing in it is counted twice.
    """

    def __init__(self, *, gap: float = 0.9, stays: float = 3.2, min_seen: int = 2):
        self.gap = gap
        self.stays = stays
        self.min_seen = min_seen
        self.popups: list[Popup] = []

    def add(self, read: PopupRead) -> None:
        if read.empty:
            return
        cur = self.popups[-1] if self.popups else None
        if cur is not None and read.t - cur.last <= self.gap + 1e-6:
            cur.reads.append(read)
            return
        if cur is not None and read.t - cur.last_change() <= self.stays + self.gap and self._continues(cur, read):
            cur.reads.append(read)
            return
        self.popups.append(Popup(index=len(self.popups), reads=[read]))

    @staticmethod
    def _continues(cur: Popup, read: PopupRead) -> bool:
        totals = [r.total for r in cur.reads if r.total is not None]
        if read.total is not None and totals and read.total < max(totals):
            return False
        last_tags = {g.text: g.count for g in cur.reads[-1].tags}
        if not read.tags:
            return read.total is not None and bool(totals) and read.total >= max(totals)
        for g in read.tags:
            if g.text in last_tags and g.count is not None and last_tags[g.text] is not None and g.count < last_tags[g.text]:
                return False
        return any(g.text in last_tags for g in read.tags)

    def finish(self, *, weak: bool = False) -> list[PointEvent]:
        """The events, in time order; with `weak`, those read only once as well (marked)."""
        out: list[PointEvent] = []
        for p in self.popups:
            out += [e for e in self._events(p) if weak or not e.weak]
        out.sort(key=lambda e: e.t)
        return out

    def _events(self, p: Popup) -> list[PointEvent]:
        events: list[PointEvent] = []
        finals = p.counts()
        once = p.counts(1)
        # Tags: the k-th of a kind at the first read showing a count of k or more.
        # A count read only once is kept apart as weak: a short tag (KILL) is now and
        # then read in one sample only, and another source may vouch for it.
        known = {_fold(g.text) for r in p.reads for g in r.tags if g.event != "points"}
        for text, top in once.items():
            final = finals.get(text, 0)
            event = next((g.event for r in p.reads for g in r.tags if g.text == text), "points")
            if event == "points" and _part_of(_fold(text), known):
                # A known tag read with its start hidden ("DESTROYED"): not an action of its own.
                continue
            firsts: dict[int, float] = {}
            support: dict[int, int] = {}
            for r in p.reads:
                c = max((g.count for g in r.tags if g.text == text and g.count is not None), default=0)
                for k in range(1, min(c, top) + 1):
                    firsts.setdefault(k, r.t)
                    support[k] = support.get(k, 0) + 1
            for k in range(1, top + 1):
                if k in firsts:
                    events.append(PointEvent(t=firsts[k], event=event, text=text, popup=p.index, seen=support[k],
                                             weak=k > final))
        # Titles: each distinct one once, when seen twice.
        titles: dict[str, list[float]] = {}
        for r in p.reads:
            for raw in r.titles:
                event, text, n = read_title(raw)
                key = next((k for k in titles if _ratio(_fold(k), _fold(text)) >= 0.8), text)
                titles.setdefault(key, []).append(r.t)
        for text, ts in titles.items():
            if len(ts) >= self.min_seen:
                event, text2, _ = read_title(text)
                events.append(PointEvent(t=ts[0], event=event, text=text2, popup=p.index, seen=len(ts)))
        events.sort(key=lambda e: (e.t, e.event in ("multi_kills", "ribbon")))
        self._points(p, events)
        self._names(p, events)
        return events

    def total(self, p: Popup) -> int | None:
        """The popup's final total: the highest read twice."""
        vals = sorted((r.total for r in p.reads if r.total is not None), reverse=True)
        for i in range(len(vals) - 1):
            if vals[i] == vals[i + 1]:
                return vals[i]
        return None

    @staticmethod
    def _points(p: Popup, events: list[PointEvent]) -> None:
        """What the total grew by at each event's moment: the steps of totals read twice in a row."""
        steady: list[tuple[float, int]] = []
        vals = [(r.t, r.total) for r in p.reads if r.total is not None]
        for (ta, a), (tb, b) in zip(vals, vals[1:]):
            if a == b and (not steady or b >= steady[-1][1]) and (not steady or steady[-1][1] != b):
                steady.append((ta, b))
        scoring = [e for e in events if e.event not in ("multi_kills", "ribbon")]
        moments = sorted({e.t for e in scoring})
        for i, m in enumerate(moments):
            nxt = moments[i + 1] if i + 1 < len(moments) else float("inf")
            before = [v for t, v in steady if t < m]
            after = [v for t, v in steady if m <= t < nxt]
            if not after:
                continue
            delta = after[-1] - (before[-1] if before else 0)
            if delta <= 0:
                continue
            group = [e for e in scoring if e.t == m]
            for e in group:
                e.points = delta
                e.shared = len(group)

    @staticmethod
    def _names(p: Popup, events: list[PointEvent]) -> None:
        """Each event's name: the one shown in the second after it, a new one when the popup has several."""
        used: set[str] = set()
        for e in events:
            if e.event not in ABOUT_SOMEONE:
                continue
            near: dict[str, list[str]] = {}
            for r in p.reads:
                if e.t - 0.05 <= r.t <= e.t + 1.25 and r.name:
                    near.setdefault(r.name, []).append(r.side)
            if not near:
                continue
            ranked = sorted(near.items(), key=lambda kv: (kv[0] in used, -len(kv[1])))
            name, sides = ranked[0]
            e.name = name
            e.side = max(set(sides), key=sides.count)
            used.add(name)
