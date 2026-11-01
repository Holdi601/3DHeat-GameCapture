"""
One recording in, the player's track and the kill feed out.

The work runs in three lanes at once, because each waits on something
different: ffmpeg decodes in its own process; one thread registers minimaps
(OpenCV, which lets go of Python's lock while it works); one thread reads text
(ONNX Runtime, likewise). The main thread only hands samples out.

Afterwards the pieces are put together: in-play stretches become lives, a
kill-feed line naming the player as victim is a death, as killer a kill; the
compass turns the mosaic north up; and everything is written out (see
`output.py`).
"""

from __future__ import annotations

import math
import queue
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import compass as compass_mod
from .killfeed import FRIENDLY, NEUTRAL, SQUAD, Feed, FeedEvent, FeedReader, Gate, parse_rows
from .minimap import MinimapTracker, TrackPoint
from .ocr import Reader, clean_name, similarity
from .output import heading_vector, map_anchors, write_json, write_jsonl, write_map, write_table
from .profiles import PROFILES, Profile
from .video import probe, samples

#: How alike a read has to be to the player's name to be them.
NAME_MATCH = 0.75
#: A gap in play at least this long is a death or a round change even with no feed line to say so.
DEATH_GAP = 6.0
#: How long after a feed death the player may stay on screen (downed, kill cam) before it counts as a revive.
DOWNED = 40.0


@dataclass
class Options:
    game: str = "bf6"
    player: str | None = None
    fps: float = 5.0
    feed_fps: float = 2.5
    compass_every: float = 3.0
    squad_every: float = 15.0
    start: float = 0.0
    duration: float | None = None
    gpu: bool | None = None
    metres_per_pixel: float | None = None
    #: Feed lines read in fewer samples than this are dropped as misreads.
    min_seen: int = 2
    #: Islands (separate mosaics) with less track than this, in seconds, are not written.
    min_island: float = 30.0


@dataclass
class Progress:
    t: float
    duration: float
    note: str


@dataclass
class Result:
    files: list[Path] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def _is_me(name: str, player: str | None) -> bool:
    return bool(player) and similarity(name, player) >= NAME_MATCH


def _event_kind(e: FeedEvent, player: str | None) -> str:
    """What a feed line is from the player's side: kill, death, teamkill, suicide, squadwipe, or other."""
    if re.search(r"S[OQ0]UAD$", e.victim.upper()) or e.marker == "crosses":
        return "squadwipe" if _is_me(e.killer, player) else "other-squadwipe"
    k, v = _is_me(e.killer, player), _is_me(e.victim, player)
    if k and v:
        return "suicide"
    if k:
        return "teamkill" if e.side("victim") in (FRIENDLY, SQUAD) else "kill"
    if v:
        return "death"
    return "other"


def guess_player(squad_reads: list[str], events: list[FeedEvent]) -> tuple[str | None, str]:
    """
    Who the player is, when not told: the squad list's own row, else the feed's own-name colour.

    Returns the name and how it was found, or None and why not.
    """
    if squad_reads:
        votes = Counter(squad_reads)
        name, n = votes.most_common(1)[0]
        if n >= 3 and n >= 0.6 * len(squad_reads):
            return name, f"the squad list's own row ({n} of {len(squad_reads)} reads)"
    # The game draws the player's own name (and their squad's) in a pale green
    # rather than the team's blue: the name that comes up most in that colour.
    neutral = Counter()
    for e in events:
        if e.side("killer") in (NEUTRAL, SQUAD):
            neutral[e.killer] += 1
        if e.side("victim") in (NEUTRAL, SQUAD):
            neutral[e.victim] += 1
    merged: Counter = Counter()
    for name, n in neutral.items():
        for known in merged:
            if similarity(name, known) >= NAME_MATCH:
                merged[known] += n
                break
        else:
            merged[name] += n
    if merged:
        name, n = merged.most_common(1)[0]
        total = sum(merged.values())
        if n >= 3 and n >= 0.6 * total:
            return name, f"the feed's own-name colour ({n} of {total} names drawn in it)"
    return None, "not found: no squad list with a highlighted row, and no name the feed drew in the player's colour"


def _squad_own_row(reader: Reader, image: np.ndarray) -> str | None:
    """The squad list's highlighted row: the brightest name, when it is clearly brighter than the rest."""
    texts = [t for t in reader.read(image) if t.score >= 0.6 and len(clean_name(t.text)) >= 3]
    if not texts:
        return None
    lum = []
    for t in texts:
        p = image[int(t.y0) : int(t.y1), int(t.x0) : int(t.x1)].reshape(-1, 3).astype(np.float32)
        g = p.mean(axis=1)
        lum.append(float(g[g >= np.percentile(g, 85)].mean()) if len(g) else 0.0)
    order = np.argsort(lum)[::-1]
    best = order[0]
    if len(texts) > 1 and lum[best] - lum[order[1]] < 15:
        return None
    return clean_name(texts[best].text)


def run(video: Path, out: Path, opts: Options, on_progress: Callable[[Progress], None] | None = None) -> Result:
    profile: Profile = PROFILES[opts.game]
    info = probe(video)
    duration = opts.duration if opts.duration is not None else max(0.0, info.duration - opts.start)
    reader = Reader()
    tracker = MinimapTracker(profile.player, profile.map_key)
    feed = Feed()
    gate = Gate()
    feed_reader = FeedReader(reader)
    feed_region = profile.region("feed")
    strips = [profile.region(n) for n in ("compass", "compass_sight")]

    play: list[tuple[float, bool]] = []
    bearings: list[compass_mod.Bearing] = []
    squad_reads: list[str] = []
    errors: list[BaseException] = []
    counters = Counter()

    map_q: queue.Queue = queue.Queue(maxsize=64)
    text_q: queue.Queue = queue.Queue(maxsize=64)

    def map_lane() -> None:
        try:
            while True:
                item = map_q.get()
                if item is None:
                    return
                t, image = item
                here = tracker.in_play(image)
                play.append((t, here))
                if here:
                    tracker.add(t, image)
                else:
                    tracker.break_track()
                    tracker.out_of_play += 1
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    def text_lane() -> None:
        try:
            while True:
                item = text_q.get()
                if item is None:
                    return
                kind, t, payload = item
                if kind == "feed":
                    if not gate.due(t, payload):
                        continue
                    counters["feed reads"] += 1
                    texts = feed_reader.read(payload)
                    rows = parse_rows(
                        payload, texts, pitch=profile.feed_pitch * feed_region.scale,
                        text_h=profile.feed_text * feed_region.scale, reader=reader,
                    )
                    feed.add(t, rows)
                elif kind == "compass":
                    counters["compass reads"] += 1
                    b = compass_mod.read(
                        reader, t,
                        [(img, r.box.x, 1.0 / r.scale) for img, r in zip(payload, strips)],
                        profile.compass_letters, profile.compass_mark,
                    )
                    if b is not None:
                        bearings.append(b)
                elif kind == "squad":
                    name = _squad_own_row(reader, payload)
                    if name:
                        squad_reads.append(name)
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    lanes = [threading.Thread(target=map_lane, daemon=True), threading.Thread(target=text_lane, daemon=True)]
    for lane in lanes:
        lane.start()

    started = time.monotonic()
    feed_step = max(1, round(opts.fps / opts.feed_fps))
    compass_step = max(1, round(opts.fps * opts.compass_every))
    squad_step = max(1, round(opts.fps * opts.squad_every))
    last_note = 0.0
    try:
        for s in samples(video, profile, fps=opts.fps, start=opts.start, duration=duration, gpu=opts.gpu):
            if errors:
                break
            map_q.put((s.t, s.regions["minimap"].copy()))
            if s.index % feed_step == 0:
                text_q.put(("feed", s.t, s.regions["feed"].copy()))
            if s.index % compass_step == 0:
                text_q.put(("compass", s.t, [s.regions["compass"].copy(), s.regions["compass_sight"].copy()]))
            if s.index % squad_step == 0:
                text_q.put(("squad", s.t, s.regions["squad"].copy()))
            now = time.monotonic()
            if on_progress and now - last_note >= 5.0:
                last_note = now
                on_progress(Progress(
                    s.t - opts.start, duration,
                    f"{tracker.placed} minimaps placed, {len(feed.events)} feed lines so far",
                ))
    finally:
        map_q.put(None)
        text_q.put(None)
        for lane in lanes:
            lane.join()
    if errors:
        raise errors[0]
    elapsed = time.monotonic() - started
    if on_progress:
        on_progress(Progress(duration, duration, f"read in {elapsed:.0f} s; putting it together"))

    events = feed.finish(min_seen=opts.min_seen)
    return assemble(
        video, out, opts, profile, tracker, sorted(play), events, bearings, squad_reads,
        timing={"seconds": round(elapsed, 1), "video_seconds": round(duration, 1), **counters,
                "feed lines read": feed_reader.read_lines, "feed lines reused": feed_reader.reused_lines},
    )


# ---------------------------------------------------------------- assembly


def drop_spikes(track: list[TrackPoint], step: float, *, limit: float = 10.0) -> tuple[list[TrackPoint], int]:
    """
    The track without points that jump away from both neighbours and back.

    A minimap now and then matches the mosaic at a wrong zoom and lands its
    player tens of pixels off for one sample. A point further than `limit`
    mosaic pixels (scaled by its zoom) from the median of the two samples
    before and the two after it, while those four agree among themselves, is
    such a jump. Points with a gap in time round them are left alone.
    """
    keep = [True] * len(track)
    for i in range(2, len(track) - 2):
        near = track[i - 2 : i + 3]
        if near[-1].t - near[0].t > 4 * step + 1e-6 or len({p.island for p in near}) > 1:
            continue
        others = [p for j, p in enumerate(near) if j != 2]
        mx = float(np.median([p.x for p in others]))
        my = float(np.median([p.y for p in others]))
        spread = max(math.hypot(p.x - mx, p.y - my) for p in others)
        dev = math.hypot(track[i].x - mx, track[i].y - my)
        scale = float(np.median([p.scale for p in others])) or 1.0
        if dev > limit * scale and dev > 2.5 * spread:
            keep[i] = False
    return [p for p, k in zip(track, keep) if k], keep.count(False)


def _play_intervals(play: list[tuple[float, bool]], step: float) -> list[tuple[float, float]]:
    """In-play stretches, ignoring a state that lasts a single sample (a flicker, a menu fading)."""
    if not play:
        return []
    flags = [p for _, p in play]
    times = [t for t, _ in play]
    for i in range(1, len(flags) - 1):
        if flags[i - 1] == flags[i + 1] != flags[i]:
            flags[i] = flags[i - 1]
    out = []
    start = None
    for t, f in zip(times, flags):
        if f and start is None:
            start = t
        elif not f and start is not None:
            out.append((start, t - step))
            start = None
    if start is not None:
        out.append((start, times[-1]))
    return out


@dataclass
class _Frame:
    """How an island's mosaic becomes the table's plane: x east, y north."""

    #: Mosaic -> table: scale by 1/s, turn by `turn` degrees clockwise, flip y.
    s: float
    turn: float
    north: bool
    #: Spread of the compass against the mosaic, degrees, and how many reads agreed.
    spread: float | None = None
    agreeing: int = 0
    per: float = 1.0

    def apply(self, x: float, y: float) -> tuple[float, float]:
        c, sn = math.cos(math.radians(self.turn)), math.sin(math.radians(self.turn))
        x, y = x / self.s, y / self.s
        u, v = c * x - sn * y, sn * x + c * y
        return u * self.per, -v * self.per

    def heading(self, mosaic_heading: float) -> float:
        return (mosaic_heading + self.turn) % 360.0


def assemble(
    video: Path, out: Path, opts: Options, profile: Profile, tracker: MinimapTracker,
    play: list[tuple[float, bool]], events: list[FeedEvent], bearings: list[compass_mod.Bearing],
    squad_reads: list[str], *, timing: dict[str, Any],
) -> Result:
    result = Result()
    step = 1.0 / opts.fps
    stem = out.name
    folder = out.parent

    # Who the player is.
    if opts.player:
        player, how = opts.player, "given with --player"
    else:
        player, how = guess_player(squad_reads, events)

    # Single-sample jumps (a minimap matched at the wrong zoom) come out before anything else.
    track, spikes = drop_spikes(tracker.track, step)

    # Islands: the mosaics. The ones with enough track are written, largest first.
    points: dict[int, list[TrackPoint]] = {}
    for p in track:
        points.setdefault(p.island, []).append(p)
    islands = sorted(points, key=lambda i: -len(points[i]))
    keep = [i for i in islands if len(points[i]) * step >= opts.min_island] or islands[:1]

    # Each island turned north up from the compass, scaled to the usual zoom.
    frames: dict[int, _Frame] = {}
    compass_pairs: dict[int, int] = {}
    for i in keep:
        pts = points[i]
        s = float(np.median([p.scale for p in pts])) or 1.0
        times = np.array([p.t for p in pts])
        pairs = []
        for b in bearings:
            j = int(np.searchsorted(times, b.t))
            for k in (j - 1, j):
                if 0 <= k < len(pts) and abs(pts[k].t - b.t) <= step * 0.6:
                    pairs.append((b.heading, pts[k].heading))
                    break
        found = compass_mod.north_offset(pairs)
        compass_pairs[i] = len(pairs)
        if found is not None and found[2] >= 3 and found[2] >= 0.5 * len(pairs):
            frames[i] = _Frame(s=s, turn=found[0], north=True, spread=round(found[1], 1), agreeing=found[2])
        else:
            frames[i] = _Frame(s=s, turn=0.0, north=False, agreeing=found[2] if found else 0)
        frames[i].per = opts.metres_per_pixel or 1.0

    intervals = _play_intervals(play, step)
    kinds = [(e, _event_kind(e, player)) for e in events]
    deaths = [e.t for e, k in kinds if k in ("death", "suicide")]

    def life_of(t: float) -> int | None:
        for n, (a, b) in enumerate(intervals):
            if a - step <= t <= b + step:
                return n
        return None

    # How each in-play stretch begins: the clip's own start, a spawn after a death
    # or a long gap, or a resumption after a short pause (the big map opened).
    starts: list[str] = []
    lives: list[int] = []
    life = 0
    for n, (a, b) in enumerate(intervals):
        if n == 0:
            starts.append("start" if a - opts.start <= 2 * step + 1.0 else "spawn")
            lives.append(life)
            continue
        gap_from = intervals[n - 1][1]
        died = any(gap_from - DOWNED <= d <= a for d in deaths)
        if died or a - gap_from >= DEATH_GAP:
            life += 1
            starts.append("spawn")
        else:
            starts.append("")
        lives.append(life)

    def session(n: int) -> str:
        return f"{video.stem}#{lives[n] + 1:02d}"

    # Position rows, per island.
    rows_by_island: dict[int, list[dict[str, Any]]] = {i: [] for i in keep}
    placed_by_time = sorted(track, key=lambda p: p.t)
    ptimes = np.array([p.t for p in placed_by_time])

    def nearest(t: float, *, before: bool = False, within: float = 3.0) -> TrackPoint | None:
        if not len(ptimes):
            return None
        j = int(np.searchsorted(ptimes, t, side="right"))
        cands = [j - 1] if before else [j - 1, j]
        best = None
        for k in cands:
            if 0 <= k < len(placed_by_time) and abs(placed_by_time[k].t - t) <= within:
                if best is None or abs(placed_by_time[k].t - t) < abs(best.t - t):
                    best = placed_by_time[k]
        return best

    def row_at(p: TrackPoint, event: str, n: int | None, **extra: Any) -> dict[str, Any] | None:
        if p.island not in frames:
            return None
        f = frames[p.island]
        x, y = f.apply(p.x, p.y)
        heading = f.heading(p.heading)
        dx, dy, dz = heading_vector(heading)
        r = {
            "time": round(p.t, 3), "event": event, "x": round(x, 2), "y": round(y, 2), "z": 0.0,
            "player": "me", "team": "own", "session": session(n) if n is not None else f"{video.stem}#00",
            "heading": round(heading, 1), "dir_x": dx, "dir_y": dy, "dir_z": dz,
            # How far the minimap was zoomed out against its usual zoom (vehicles zoom out).
            "zoom": round(p.scale / f.s, 3),
        }
        r.update({k: v for k, v in extra.items() if v is not None})
        return r

    # A death ends the life's route there; what follows on screen before the
    # player leaves play (downed, kill cam) is not walking, unless they get up again.
    cut: list[tuple[float, float]] = []
    revives: list[float] = []
    for d in deaths:
        n = life_of(d)
        if n is None:
            continue
        end = intervals[n][1]
        if end - d <= DOWNED:
            cut.append((d, end + step))
        else:
            # Still in play long after: revived. The route picks up a few seconds on.
            revives.append(d + 2.0)
    revive_at = set()
    for r_t in revives:
        j = int(np.searchsorted(ptimes, r_t))
        if j < len(placed_by_time) and life_of(placed_by_time[j].t) == life_of(r_t):
            revive_at.add(j)
    first_of_interval: set[int] = set()
    for j, p in enumerate(placed_by_time):
        n = life_of(p.t)
        if n is None or any(a < p.t <= b for a, b in cut):
            continue
        event = "position"
        if n not in first_of_interval:
            first_of_interval.add(n)
            if starts[n]:
                event = starts[n]
        elif j in revive_at:
            event = "revive"
        r = row_at(p, event, n)
        if r is not None:
            rows_by_island[p.island].append(r)

    # The feed: every line to the jsonl; the player's own as rows where they were.
    feed_rows = []
    counts = Counter()
    for e, kind in kinds:
        me = "killer" if _is_me(e.killer, player) else ("victim" if _is_me(e.victim, player) else None)
        doc = {
            "time": round(e.t, 2), "last": round(e.last, 2),
            "kind": kind if me else ("squadwipe" if "squadwipe" in kind else ("kill" if e.killer else "death")),
            "killer": e.killer, "victim": e.victim,
            "killer_side": e.side("killer"), "victim_side": e.side("victim"),
            "weapon": e.weapon, "marker": e.marker, "headshot": e.marker == "skull",
            "seen": e.seen, "me": me,
        }
        p = nearest(e.t, before=(kind == "death")) if me else None
        if p is not None and p.island in frames:
            n = life_of(p.t)
            r = row_at(p, kind, n, killer=e.killer, victim=e.victim, weapon=e.weapon or None,
                       headshot=e.marker == "skull", marker=e.marker or None)
            if r is not None:
                r["time"] = round(e.t, 3)
                rows_by_island[p.island].append(r)
                doc["x"], doc["y"] = r["x"], r["y"]
                if len(keep) > 1:
                    doc["map"] = keep.index(p.island) + 1
        feed_rows.append(doc)
        if me:
            counts[kind] += 1

    # Lives that ended with no feed line to say how: the route still ends.
    for n, (a, b) in enumerate(intervals):
        if n + 1 < len(intervals) and starts[n + 1] == "spawn" and not any(a <= d <= b + step for d in deaths):
            p = nearest(b, before=True, within=2 * step + 0.5)
            if p is not None:
                r = row_at(p, "end", n)
                if r is not None:
                    r["time"] = round(b + step / 2, 3)
                    rows_by_island[p.island].append(r)

    # Write.
    maps = []
    for idx, i in enumerate(keep):
        rows = sorted(rows_by_island[i], key=lambda r: (r["time"], r["event"] != "position"))
        name = stem if idx == 0 else f"{stem}.map{idx + 1}"
        table = write_table(folder / f"{name}.parquet", rows, game=profile.name, scale=1.0)
        result.files.append(table)
        f = frames[i]
        island = tracker.islands[i]
        pic = island.picture()
        entry: dict[str, Any] = {
            "table": table.name, "rows": len(rows), "north_up": f.north,
            "compass_reads": compass_pairs.get(i, 0), "compass_reads_agreeing": f.agreeing,
            "compass_spread_degrees": f.spread,
            "seconds_of_track": round(len(points[i]) * step, 1),
        }
        if pic is not None:
            png, side = _write_picture(folder / f"{name}.map.png", pic, island.origin, f, island.weight)
            result.files += [png, side]
            entry["image"] = png.name
        maps.append(entry)

    events_path = write_jsonl(folder / f"{stem}.events.jsonl", feed_rows)
    result.files.append(events_path)

    alive = sum(b - a + step for a, b in intervals)
    distance = 0.0
    for i in keep:
        f = frames[i]
        prev = None
        for p in points[i]:
            q = f.apply(p.x, p.y)
            if prev is not None and p.t - prev[0] <= 2 * step + 1e-6 and life_of(p.t) == life_of(prev[0]):
                distance += math.hypot(q[0] - prev[1][0], q[1] - prev[1][1])
            prev = (p.t, q)
    kills = counts["kill"]
    deaths_n = counts["death"] + counts["suicide"]
    summary = {
        "format": "heat3d-hud-summary",
        "version": 1,
        "game": profile.title,
        "video": video.name,
        "player": player,
        "player_from": how,
        "kills": kills,
        "deaths": deaths_n,
        "kd": round(kills / deaths_n, 2) if deaths_n else None,
        "teamkills": counts["teamkill"],
        "suicides": counts["suicide"],
        "squad_wipes": counts["squadwipe"],
        "lives": (max(lives) + 1) if lives else 0,
        "seconds_in_play": round(alive, 1),
        "distance": round(distance, 1),
        "distance_units": "metres" if opts.metres_per_pixel else "minimap pixels at the usual zoom (296 per minimap on a 1080p screen)",
        "feed_lines": len(events),
        "maps": maps,
        "track": {
            "minimaps_sampled": tracker.seen + tracker.out_of_play,
            "in_play": tracker.seen,
            "placed": tracker.placed,
            "not_placed": tracker.rejected,
            "dropped_as_jumps": spikes,
            "islands_unjoined": len([i for i in tracker.islands if i.joined_to is None and i.frames]),
            "islands_written": len(keep),
        },
        "assumptions": {
            "headshot": "the skull marker before a victim's name is taken to mean a headshot",
            "units": "positions are minimap pixels unless --metres-per-pixel is given",
        },
        "compass_reads": len(bearings),
        "timing": timing,
    }
    result.summary = summary
    result.files.append(write_json(folder / f"{stem}.summary.json", summary))
    return result


def _write_picture(png: Path, pic: np.ndarray, origin: np.ndarray, f: _Frame, weight: np.ndarray):
    """The island's mosaic turned and scaled like its track, cropped to what was seen."""
    import cv2

    seen = weight > 0.5
    ys, xs = np.nonzero(seen)
    if not len(xs):
        empty = np.zeros((2, 2, 3), np.uint8)
        return write_map(png, empty, map_anchors(2, 2, 0, 0, f.per), {})
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pic = pic[y0:y1, x0:x1]
    # Canvas pixel -> mosaic -> turned and scaled (y still down, in units of `1/s` mosaic pixels).
    c, sn = math.cos(math.radians(f.turn)), math.sin(math.radians(f.turn))
    ox, oy = origin[0] + x0, origin[1] + y0
    M = np.array([[c, -sn, 0.0], [sn, c, 0.0]]) / f.s
    M[:, 2] = M[:, :2] @ np.array([ox, oy])
    h, w = pic.shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]], np.float64) @ M.T
    lo = np.floor(corners.min(axis=0))
    hi = np.ceil(corners.max(axis=0))
    M[:, 2] -= lo
    size = (int(hi[0] - lo[0]), int(hi[1] - lo[1]))
    out = cv2.warpAffine(pic, M, size, flags=cv2.INTER_LINEAR, borderValue=0)
    # Picture pixel (0, 0) is at turned (lo); the table's y is the turned y negated.
    anchors = map_anchors(size[0], size[1], lo[0] * f.per, -lo[1] * f.per, f.per)
    note = {
        "north_up": f.north,
        "units": "metres" if f.per != 1.0 else "minimap pixels at the usual zoom",
        "privacy": "made from the player's own recording; keep it local",
    }
    return write_map(png, out, anchors, note)
