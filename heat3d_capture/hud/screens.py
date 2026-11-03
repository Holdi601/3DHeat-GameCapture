"""
The player's own death, from the screens the game shows for it.

When Battlefield 6's player goes down, the bottom of the screen says so
(MAN DOWN, REQUEST REVIVE, SKIP (HOLD), NEARBY MEDICS; once a revive is asked
for, REVIVE REQUESTED and CANCEL REQUEST), and a card in the bottom right
names who did it (with DAMAGE LOG or PLAYER CARD under it). Killed outright,
only the card shows. Either way it ends one of two ways: a teammate revives
the player, and the screens go and play carries on; or the player bleeds
out or gives up, and the deploy screen follows (DEPLOY in its bottom right).

So a death is a stretch of these screens followed by the deploy screen or a
long time out of play; the same stretch followed by play is a revive by
someone else. The moment is the stretch's start - when the player went down -
not the deploy screen's.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

#: What a word on these screens says: the player is down, has been killed (the killer's card), or is choosing where to deploy.
DOWN = "down"
CARD = "card"
DEPLOY = "deploy"

WORDS: tuple[tuple[str, str], ...] = (
    ("MAN DOWN", DOWN),
    ("REQUEST REVIVE", DOWN),
    ("REVIVE REQUESTED", DOWN),
    ("CANCEL REQUEST", DOWN),
    ("NEARBY MEDICS", DOWN),
    ("SKIP HOLD", DOWN),
    ("DAMAGE LOG", CARD),
    ("PLAYER CARD", CARD),
    ("DEPLOY", DEPLOY),
)


def _fold(s: str) -> str:
    return re.sub(r"[^A-Z]", "", s.upper().replace("Q", "O"))


_KEYS = [(_fold(w), kind) for w, kind in WORDS]


def kinds(texts: list[str]) -> set[str]:
    """Which of the screens the lines of text read in a sample belong to."""
    out: set[str] = set()
    for raw in texts:
        # The killer card's score line: "YOU 1 [skull] 2 FOE", often read in pieces.
        if re.search(r"\bYOU\s*[0-9O]+.*FOE", raw.upper()) or re.fullmatch(r"\s*[0-9]+\s*FOE\s*", raw.upper()):
            out.add(CARD)
        s = _fold(raw)
        if len(s) < 4:
            continue
        # Keys hidden inside a longer read (a key-hint letter in front: "FDAMAGELOG").
        for k, kind in _KEYS:
            if k in s or (len(s) <= len(k) + 3 and SequenceMatcher(None, s, k).ratio() >= 0.85):
                out.add(kind)
    return out


@dataclass
class Episode:
    """A stretch of down or killed screens."""

    start: float
    end: float
    kinds: set[str] = field(default_factory=set)
    reads: int = 0
    #: "death" (the deploy screen or a long time out of play followed) or "revived".
    outcome: str = ""
    #: When play resumed after a revive.
    back: float | None = None


def episodes(reads: list[tuple[float, set[str]]], *, gap: float = 4.0, min_reads: int = 2) -> list[Episode]:
    """Down and card screens in a row, with less than `gap` seconds between sightings, as episodes."""
    out: list[Episode] = []
    for t, ks in sorted(reads, key=lambda r: r[0]):
        ks = ks & {DOWN, CARD}
        if not ks:
            continue
        if out and t - out[-1].end <= gap:
            e = out[-1]
            e.end = t
        else:
            e = Episode(start=t, end=t)
            out.append(e)
        e.kinds |= ks
        e.reads += 1
    return [e for e in out if e.reads >= min_reads]


def outcomes(
    eps: list[Episode], reads: list[tuple[float, set[str]]], play: list[tuple[float, float]], *,
    deploy_within: float = 12.0, out_of_play: float = 6.0, settle: float = 3.0,
) -> None:
    """
    Decide each episode.

    A death: the deploy screen shows within `deploy_within` seconds after the
    episode's last sighting (and before the next episode), or the player is out
    of play `settle` seconds after it and stays out for `out_of_play` seconds
    or more. A revive by someone else: still in play `settle` seconds after the
    screens went. "unknown" when the recording ends first.

    `play` is the in-play stretches (start, end); the minimap stays up while
    the player is down, so a down player is in play.
    """
    deploys = sorted(t for t, ks in reads if DEPLOY in ks)
    after = sorted(t for t, ks in reads if not ks & {DOWN, CARD})
    last = play[-1][1] if play else None
    for i, e in enumerate(eps):
        horizon = e.end + deploy_within
        if i + 1 < len(eps):
            horizon = min(horizon, eps[i + 1].start)
        if any(e.start <= t <= horizon for t in deploys):
            e.outcome = "death"
            continue
        probe = e.end + settle
        if any(a <= probe <= b for a, b in play):
            e.outcome = "revived"
            e.back = next((t for t in after if t > e.end), e.end)
            continue
        if last is None or probe > last:
            # The recording ends here: how it ended is not shown.
            e.outcome = "unknown"
            continue
        nxt = min((a for a, _ in play if a > probe), default=None)
        left = max((b for _, b in play if b < probe), default=e.end)
        e.outcome = "death" if nxt is None or nxt - left >= out_of_play else "unknown"
