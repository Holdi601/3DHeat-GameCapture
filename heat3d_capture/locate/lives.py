"""
When the player was alive and in play, from what the footage itself showed.

A position may jump only where the player died: within one life it moves no
faster than a player on foot or a vehicle can. So the lives are not guessed
from the positions (a single wrong fix would open a new one) but read from
the HUD reader's table (`hud` verb), whose events come from the screens the
game shows:

- `start`: play begins (the clip's own start, or after a long time out of
  play); `spawn`: the player deploys after a death. Either opens a life.
- `death`: the player went down and did not come back (the deploy screen
  followed); `end`: play stopped (menus, loading, the end of the clip). Either
  closes the open life. Until the next start or spawn the player is not in
  play: no frame there is placed (it shows a death camera, a map, a menu).
- `downed` followed by `revived`: the player went down and a teammate brought
  them back. The life goes on - they are where they went down - but the
  frames between show no player's view and are not placed.

A run with no such table has one life; the run's own non-play frames (a long
stretch of menus, `views.SCREEN`) cut it as well.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

#: Events that open a life, close one, and bracket a down that ended in a revive.
OPEN = ("start", "spawn")
CLOSE = ("death", "end")


@dataclass
class Lives:
    """Lives as time spans: life k is in play from spans[k][0] to spans[k][1] (seconds)."""

    spans: list[tuple[float, float]]
    #: Down spans that ended in a revive (the life goes on).
    downs: list[tuple[float, float]] = field(default_factory=list)
    #: Deaths and ends read, with their time: what cut each life.
    cuts: list[tuple[float, str]] = field(default_factory=list)
    #: Seconds of slack round a span's ends (the HUD samples every 0.2 s, the screens every 0.5-1 s).
    slack: float = 1.0

    def life(self, t: float) -> int | None:
        """The life a time falls in, or None: dead, deploying, or out of play."""
        for k, (a, b) in enumerate(self.spans):
            if a - self.slack <= t <= b:
                return k
        return None

    def down(self, t: float) -> bool:
        """The player is down (and will be revived) at t: in their life, but showing no view of their own."""
        return any(a <= t <= b for a, b in self.downs)

    @classmethod
    def whole(cls) -> "Lives":
        return cls([(-np.inf, np.inf)])


def read_lives(path: str, *, pause: float = 10.0) -> Lives:
    """
    The lives a HUD reader's table records (its start, spawn, death, end,
    downed and revived events). Play that stops and starts again within
    `pause` seconds with no death between (the big map opened, a scoreboard)
    is the same life.
    """
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    if "event" not in table.column_names:
        return Lives.whole()
    t = table.select(["time", "event"]).to_pydict()
    events = sorted((float(tm), ev) for tm, ev in zip(t["time"], t["event"]) if ev in OPEN + CLOSE + ("downed", "revived"))
    spans: list[tuple[float, float]] = []
    downs: list[tuple[float, float]] = []
    cuts: list[tuple[float, str]] = []
    open_at: float | None = None
    down_at: float | None = None
    for tm, ev in events:
        if ev in OPEN and open_at is None and cuts and cuts[-1][1] == "end" and tm - cuts[-1][0] <= pause:
            # A short pause: the life carries on.
            open_at = spans.pop()[0]
            cuts.pop()
            continue
        if ev in OPEN:
            if open_at is not None:
                # A spawn with no death before it: one was missed. The life still ends here.
                spans.append((open_at, tm))
                cuts.append((tm, "spawn without a death read"))
            open_at = tm
        elif ev in CLOSE:
            if open_at is None and not spans:
                # Play was already on when the table starts reading.
                open_at = -np.inf
            if open_at is not None:
                spans.append((open_at, tm))
                cuts.append((tm, ev))
                open_at = None
        elif ev == "downed":
            down_at = tm
        elif ev == "revived" and down_at is not None:
            downs.append((down_at, tm))
            down_at = None
    if open_at is not None:
        spans.append((open_at, np.inf))
    if not events:
        spans = [(-np.inf, np.inf)]
    return Lives(spans, downs, cuts)


def frame_lives(times: list[float], views: list[str], lives: Lives, *, screen: str = "screen", long_screen: float = 10.0) -> list[int | None]:
    """
    Each frame's life: its life in `lives`, cut again where the run's own
    frames showed no level (menus, loading) for longer than `long_screen`
    seconds; None where the player is not in play or is down.
    """
    out: list[tuple | None] = []
    extra = 0
    run_from: float | None = None
    last: tuple | None = None
    for t, v in zip(times, views):
        if v == screen:
            run_from = t if run_from is None else run_from
            out.append(None)
            continue
        if run_from is not None and t - run_from >= long_screen:
            extra += 1
        run_from = None
        k = lives.life(t)
        if k is None or lives.down(t):
            out.append(None)
            continue
        key = (k, extra)
        if last is not None and key[0] != last[0]:
            extra = 0
            key = (k, 0)
        last = key
        out.append(key)
    # Number them in order of appearance: small, stable ids.
    ids: dict[tuple, int] = {}
    return [None if x is None else ids.setdefault(x, len(ids)) for x in out]
