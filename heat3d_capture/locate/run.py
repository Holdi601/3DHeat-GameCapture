"""
A recording (or a folder of pictures) -> a table of where each sampled frame
was taken: the `locate frames` verb.

    <out>.parquet       one row per sampled frame, 3DHeat format, the level's frame
    <out>.summary.json  what was found, how often, how sure, and how long it took

Every row says where its position came from (`source`): `visual` (solved
from the picture against the level), `visual+minimap-prior` (solved from the
picture, the search cut to the minimap's neighbourhood), `minimap` (the
picture failed or was voted out, the minimap track stood in) or `none`
(neither). `confidence`
(0..1) and `uncertainty` (level units, a typical error) say how far to trust
it. See docs/locate.md.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

import numpy as np

from .camera import direction
from .database import open_db
from .profiles import GameProfile
from .track import VISUAL_SOURCES, Row, TrackOptions, build_track, read_anchor, read_minimap

PICTURES = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


@dataclass
class Options:
    fps: float = 2.0
    start: float = 0.0
    seconds: float | None = None
    width: int = 960
    hfov: float | None = None
    shortlist: int = 8
    normalisation: str = "none"
    #: The minimap table to fall back on (and, with `prior_radius`, to search near).
    minimap: str | None = None
    #: Metres: search only database views this close to the minimap's position.
    #: Optional; off by default, because a wrong prior then means a wrong fix.
    prior_radius: float | None = None
    #: The minimap's relation to the level, known before the run (track.Anchor, a JSON file). With
    #: it the minimap is a search prior from the first frame: views within `prior_radius` (default
    #: 30 m plus the anchor's 90th-percentile error) of where it puts the player.
    anchor: str | None = None
    #: When the search near the prior finds nothing, search the whole level as well.
    level_search: bool = True
    #: With an anchored minimap: render first from where it puts the camera, looking where its
    #: heading points (a few positions and pitches round that), before trying database views.
    seeds: bool = True
    #: The HUD reader's table whose start, spawn, death, end, downed and revived events say when
    #: the player was in play (lives.py); by default the minimap table, which carries them. A
    #: position may then jump only across a death.
    lives: str | None = None
    level: str | None = None
    #: Every this many frames, a picture of the frame beside the level rendered at its fix (0: none).
    check_every: int = 0
    #: Choose among each frame's candidate poses along the run (sequence.py), not frame by frame.
    sequence: bool = True
    #: After the run, fit the field of view to the strongest fixes, per view (localize.fit_hfov).
    fit_fov: bool = False
    #: Solve zoomed views from their neighbours' fixes, with the zoom free (localize.locate_zoomed).
    zoomed: bool = True
    #: Write a picture for every visual fix into <out>.check: the frame beside the level rendered at it.
    checks: bool = True


@dataclass
class Progress:
    done: int
    total: int | None
    t: float
    note: str


def frames(source: Path, fps: float, start: float = 0.0, seconds: float | None = None) -> Iterator[tuple[float, np.ndarray]]:
    """(time, RGB frame) at `fps` from a video, or from every picture in a folder (`fps` then gives their times)."""
    import cv2

    if source.is_dir() or source.suffix.lower() in PICTURES:
        files = sorted(p for p in source.iterdir() if p.suffix.lower() in PICTURES) if source.is_dir() else [source]
        for k, p in enumerate(files):
            t = k / fps
            if t < start or (seconds is not None and t > start + seconds):
                continue
            img = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if img is not None:
                yield t, cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise ValueError(f"{source}: not a video OpenCV can read")
    rate = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if start > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000.0)
    # A frame's time is its own timestamp, not its count over the nominal
    # rate: recordings drift from their nominal rate (a quarter of a second
    # in six minutes was seen), and everything that reads a frame back by its
    # time - check pictures, the zoomed pass, training on real frames, the
    # minimap - seeks by timestamp.
    want = start
    try:
        while True:
            if seconds is not None and want > start + seconds:
                break
            while True:
                if not cap.grab():
                    return
                t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if t >= want - 0.5 / rate:
                    break
            ok, img = cap.retrieve()
            if not ok:
                return
            yield t, cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            want += 1.0 / fps
            while want < t - 0.5 / rate:
                want += 1.0 / fps
    finally:
        cap.release()


def _indoor(locator, near: np.ndarray, game: GameProfile, unit: float) -> bool:
    """
    Whether where the minimap puts the player is indoors: from an eye there,
    looking four ways, the level is close all round and no sky shows.
    """
    from .camera import Pose

    d = np.linalg.norm(locator._place - near[[0, 2]], axis=1)
    top = float(locator.db.views.position[int(np.argmin(d)), 1]) + 2.0 / unit
    drop = locator.renderer.below(np.array([near[0], top, near[2]]))[1]
    if not math.isfinite(drop):
        return False
    eye = np.array([near[0], top - drop + game.eye_heights[0] / unit, near[2]])
    sky, close = 0.0, 0.0
    for yaw in (0.0, 90.0, 180.0, 270.0):
        r = locator.renderer.render(Pose(eye, yaw, 10.0), 90.0, want_color=False)
        sky += float((r.depth <= 0).mean()) / 4
        hit = r.depth[r.depth > 0]
        close += float(np.median(hit) < 8.0 / unit) / 4 if hit.size else 0.0
    return sky < 0.01 and close >= 0.75


def _nav_floor(rows: list[Row], level) -> dict:
    """
    Indoors the minimap leads: a frame the picture did not place, indoors,
    with a minimap position, gets that x/z and the height of a floor of the
    navigation mesh there - the one nearest the last fix before it (or
    after) - and says so: source "minimap+nav-floor".
    """
    fixes = [r for r in rows if r.source in VISUAL_SOURCES and r.smooth is not None]
    n = placed = 0
    for r in rows:
        if not r.indoor:
            continue
        n += 1
        if r.source != "minimap" or r.smooth is None:
            continue
        floors = level.floors_at(float(r.smooth[0]), float(r.smooth[2]))
        if not floors:
            continue
        near = min(fixes, key=lambda q: abs(q.time - r.time), default=None)
        ref = near.smooth[1] if near is not None else floors[0]
        floor = min(floors, key=lambda y: abs(y - ref))
        r.smooth = np.array([r.smooth[0], floor, r.smooth[2]])
        r.source = "minimap+nav-floor"
        placed += 1
    return {"frames": n, "minimap_nav_floor": placed}


_SPEED_READER = None


def _hud_speed(rgb: np.ndarray, game: GameProfile) -> float | None:
    """The vehicle's speed as its HUD shows it (metres a second), or None: no readout, or unread."""
    global _SPEED_READER
    if game.speed_box is None:
        return None
    import re

    import cv2

    h, w = rgb.shape[:2]
    sx, sy = w / 1920.0, h / 1080.0
    x, y, bw, bh = game.speed_box
    crop = rgb[int(y * sy) : int((y + bh) * sy), int(x * sx) : int((x + bw) * sx)]
    if crop.size == 0 or crop.max() < 120:
        return None
    if _SPEED_READER is None:
        try:
            from ..hud.ocr import Reader

            _SPEED_READER = Reader(limit=320)
        except Exception:
            _SPEED_READER = False
    if not _SPEED_READER:
        return None
    crop = cv2.resize(crop, (int(bw * 1.0), int(bh * 1.0)))
    texts = _SPEED_READER.read(cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
    for t in texts:
        m = re.search(r"(\d{1,4})\s*K\s*P\s*H", t.text.upper().replace("O", "0"))
        if m:
            return float(m.group(1)) * game.speed_unit
    return None


def _speed_limits(rows: list[Row], game: GameProfile, unit: float) -> None:
    """
    How far each frame's player may have moved per second: the speed the HUD
    showed within 3 s of it (the fastest such reading, a third again and
    2 m/s on top, for speeding up), else its class's limit - a player on foot,
    or a ground vehicle in a vehicle view. Air vehicles are not told apart
    from ground ones (no clip shows one): a stretch faster than a ground
    vehicle is flagged by the track as a jump, not trusted.
    """
    from .views import VEHICLE, ZOOMED

    shown = [(r.time, r.hud_speed) for r in rows if r.hud_speed is not None]
    ground = dict(game.class_speeds).get("ground", game.vehicle_speed)
    for r in rows:
        near = [s for t, s in shown if abs(t - r.time) <= 3.0]
        if near:
            r.speed_limit = (max(near) * 1.33 + 2.0) / unit
        elif r.view == VEHICLE or (r.view == ZOOMED and r.hud_speed is not None):
            r.speed_limit = ground / unit
        else:
            r.speed_limit = game.max_speed / unit


def _seeds(locator, near: np.ndarray, yaw: float, view: str, game: GameProfile, unit: float) -> list:
    """
    Camera poses round where an anchored minimap puts the player: the player
    (or vehicle) at `near`, looking along `yaw`. On foot the eye at eye
    height over the ground there; in a vehicle the chase camera
    behind and above it (the profile's offset). Five positions (the point
    and 4 m to each side) at two pitches.
    """
    from .camera import Pose

    d = np.linalg.norm(locator._place - near[[0, 2]], axis=1)
    vehicle = view == "vehicle"
    # The ground there: straight down from a little above the closest database view (whose
    # height is an eye's or a vehicle camera's over the ground).
    top = float(locator.db.views.position[int(np.argmin(d)), 1]) + 2.0 / unit
    drop = locator.renderer.below(np.array([near[0], top, near[2]]))[1]
    ground = top - drop if math.isfinite(drop) else top - 2.0 / unit - game.eye_heights[0] / unit
    y = math.radians(yaw)
    fwd = np.array([math.cos(y), 0.0, -math.sin(y)])
    side = np.array([math.sin(y), 0.0, math.cos(y)])
    if vehicle:
        ahead, down = game.vehicle_offset
        base = np.array([near[0], ground + down / unit, near[2]]) - fwd * ahead / unit
    else:
        base = np.array([near[0], ground + game.eye_heights[0] / unit, near[2]])
    pitches = (-10.0, 0.0) if vehicle else (0.0, -8.0)
    out = []
    for off in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)):
        p = base + (fwd * off[0] + side * off[1]) / unit
        for pt in pitches:
            out.append(Pose(p, yaw, pt))
    return out


def body(camera: np.ndarray, yaw: float, view: str, game: GameProfile, unit: float) -> np.ndarray:
    """
    Where the player or their vehicle is, from where the camera is.

    On foot and through a sight the camera is the player's eye: the same
    place. In a vehicle's third-person view the camera rides behind and above
    the vehicle; the profile's `vehicle_offset` (ahead, down; metres) along
    the camera's horizontal view direction and straight down takes it back to
    the vehicle.
    """
    if view != "vehicle":
        return np.asarray(camera, float).copy()
    ahead, down = game.vehicle_offset
    y = math.radians(yaw)
    return np.asarray(camera, float) + np.array([math.cos(y) * ahead, -down, -math.sin(y) * ahead]) / unit


def read_frames(source: Path, times: list[float], fps: float = 2.0) -> Iterator[tuple[float, np.ndarray]]:
    """The frames at these times (seconds), in order, RGB: from a video by seeking, from a folder of pictures `fps` apart."""
    import cv2

    if source.is_dir() or source.suffix.lower() in PICTURES:
        files = sorted(p for p in source.iterdir() if p.suffix.lower() in PICTURES) if source.is_dir() else [source]
        for t in sorted(times):
            k = int(round(t * fps))
            if 0 <= k < len(files):
                img = cv2.imread(str(files[k]), cv2.IMREAD_COLOR)
                if img is not None:
                    yield t, cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return
    cap = cv2.VideoCapture(str(source))
    try:
        for t in sorted(times):
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, img = cap.read()
            if ok:
                yield t, cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()


def locate_frames(
    source: Path,
    db_folder: Path,
    out: Path,
    game: GameProfile,
    options: Options,
    on_progress: Callable[[Progress], None] | None = None,
) -> tuple[list[Path], dict]:
    from .database import level_for
    from .localize import Locator

    started = time.monotonic()
    db = open_db(db_folder)
    level = level_for(db, options.level)
    unit = level.unit_metres
    locator = Locator(
        db,
        level,
        width=options.width,
        hfov=options.hfov or game.hfov,
        shortlist=options.shortlist,
        normalisation=options.normalisation,
    )
    minimap = read_minimap(options.minimap) if options.minimap else None
    anchor = read_anchor(options.anchor) if options.anchor else None
    if anchor is not None and minimap is None:
        raise ValueError("an anchor ties a minimap to the level: give the minimap table too (--minimap)")
    prior_m = options.prior_radius or (30.0 + anchor.p90 * unit if anchor is not None else None)
    from .lives import read_lives

    lives_path = options.lives or options.minimap
    lives = read_lives(lives_path) if lives_path else None
    margin = 1.5 / unit
    track_opts = TrackOptions(max_speed=game.max_speed / unit, margin=margin, vehicle_speed=game.vehicle_speed / unit)
    from .views import FOOT, SCREEN, VEHICLE, ZOOMED, detector

    detect = detector(game.views)
    counts = {FOOT: 0, VEHICLE: 0, ZOOMED: 0, SCREEN: 0}
    rows: list[Row] = []
    cands: list[list] = []
    #: The strongest fixes per view, kept for fitting the field of view: (inliers, frame, mask, pose).
    strongest: dict[str, list] = {}
    masks: dict[tuple[int, int, str], np.ndarray] = {}
    prior_sim = None
    for n, (t, rgb) in enumerate(frames(source, options.fps, options.start, options.seconds)):
        h, w = rgb.shape[:2]
        view = detect(rgb) if detect else FOOT
        counts[view] = counts.get(view, 0) + 1
        if (w, h, view) not in masks:
            masks[(w, h, view)] = game.mask(w, h, view)
        shown = _hud_speed(rgb, game) if view in (ZOOMED, VEHICLE) else None
        if view in (ZOOMED, SCREEN):
            note = "zoomed view (a scope or sight): not solved" if view == ZOOMED else "not a view of the level (a map or menu)"
            rows.append(Row(time=t, ok=False, note=note, view=view, hud_speed=shown))
            cands.append([])
            if on_progress:
                on_progress(Progress(n + 1, None, t, f"{view} view, not located"))
            continue
        hfov = (game.vehicle_hfov or options.hfov or game.hfov) if view == VEHICLE else None
        highest = game.vehicle_height / unit if view == VEHICLE else None
        near = radius = None
        if anchor is not None:
            # The minimap, carried to the level by the anchor, cuts the search
            # to a disc; the pose itself is still the picture's.
            here = minimap.at(t)
            if here is not None:
                xz = anchor.to_level(here[0], t)
                near = np.array([xz[0], 0.0, xz[1]])
                _, spread = anchor.correction(t)
                # Once this run's own fixes have measured the anchor's error here, that error
                # (at least 5 m) replaces the one measured on other clips.
                err = anchor.p90 if spread is None else max(5.0 / unit, spread)
                radius = options.prior_radius / unit if options.prior_radius else 30.0 / unit + err
        elif minimap is not None and options.prior_radius:
            # The optional speed-up: once enough visual fixes have tied the
            # minimap to the level, search only round the minimap's position.
            if prior_sim is None and sum(r.ok for r in rows) >= 8 and n % 10 == 0:
                prior_sim = _similarity_of(rows, track_opts, minimap)
            here = minimap.at(t) if prior_sim is not None else None
            if here is not None:
                xz = prior_sim.apply(here[0])[0]
                near = np.array([xz[0], 0.0, xz[1]])
                radius = options.prior_radius / unit
        mask = masks[(w, h, view)]
        fix = None
        if near is not None and options.seeds and here is not None and math.isfinite(here[1]):
            # The minimap says where, and its heading which way, the camera looked (to a few
            # metres and degrees, measured): start from there. The picture still decides.
            seeds = _seeds(locator, near, anchor.yaw(here[1]), view, game, unit)
            fix = locator.locate(rgb, mask, seeds=seeds, hfov=hfov, highest=highest)
        if fix is None or not fix.ok:
            other = locator.locate(rgb, mask, near=near, radius=radius, hfov=hfov, highest=highest)
            if fix is None or other.ok or other.inliers > fix.inliers:
                fix = other
        prior = near is not None
        indoor = False
        if near is not None and not fix.ok:
            from .localize import MIN_INLIERS

            b = None if fix.pose is None else body(fix.pose.position, fix.pose.yaw, view, game, unit)
            if b is not None and fix.inliers >= MIN_INLIERS and np.linalg.norm(b[[0, 2]] - near[[0, 2]]) <= radius:
                # A weak fit that agrees with the minimap - the level destroyed round it, smoke - is
                # still the picture's: kept, with its lower confidence, for the sequence to judge.
                fix.ok = True
                fix.note = "weak fit that agrees with the minimap"
            elif view == FOOT and here is not None:
                indoor = _indoor(locator, near, game, unit)
        if near is not None and not fix.ok and options.level_search:
            # A prior that led nowhere is no reason to give up: the whole level.
            wide = locator.locate(rgb, mask, hfov=hfov, highest=highest)
            if wide.ok or (wide.pose is not None and (fix.pose is None or wide.inliers > fix.inliers)):
                fix, prior = wide, False
        p = fix.pose
        if anchor is not None and fix.ok and p is not None and fix.confidence >= 0.7 and near is not None:
            # A confident fix tells how far off the anchor is here; only one near the prior is
            # believed for that, so a stray fix cannot drag the prior after it.
            here = minimap.at(t)
            b = body(p.position, p.yaw, view, game, unit)[[0, 2]]
            if here is not None and np.linalg.norm(b - near[[0, 2]]) <= radius:
                anchor.corrections.append((t, *(b - anchor.similarity.apply(here[0])[0])))
        if options.fit_fov and fix.ok and p is not None:
            import cv2

            keep = strongest.setdefault(view, [])
            small = cv2.resize(rgb, (options.width, int(round(h * options.width / w))), interpolation=cv2.INTER_AREA)
            keep.append((fix.inliers, small, game.mask(small.shape[1], small.shape[0], view), p))
            keep.sort(key=lambda k: -k[0])
            del keep[12:]
        if options.check_every and n % options.check_every == 0:
            _check_picture(Path(str(out) + ".check") / f"{n:05d}_{t:08.2f}s_{view}.jpg", rgb, locator, fix, hfov or locator.hfov)
        used = hfov or locator.hfov
        cands.append([(body(c.position, c.yaw, view, game, unit), c.inliers, c.yaw, c.pitch, c.rmse, c.position.copy()) for c in fix.candidates])
        rows.append(
            Row(
                time=t,
                ok=fix.ok,
                position=None if p is None else body(p.position, p.yaw, view, game, unit),
                yaw=None if p is None else p.yaw,
                pitch=None if p is None else p.pitch,
                confidence=fix.confidence,
                inliers=fix.inliers,
                rmse=fix.rmse,
                note=fix.note,
                view=view,
                cam=None if p is None else p.position.copy(),
                hfov=used,
                prior=prior,
                hud_speed=shown,
                indoor=indoor,
            )
        )
        if on_progress:
            where = "" if p is None else f"at {p.position[0]:.0f} {p.position[1]:.0f} {p.position[2]:.0f}"
            on_progress(Progress(n + 1, None, t, f"{view:7s} {'ok ' if fix.ok else 'no '} {fix.inliers:4d} inliers {where} {fix.note}"))
    fitted: dict[str, float | None] = {}
    if options.fit_fov:
        from .localize import fit_hfov

        for v, keep in strongest.items():
            start = (game.vehicle_hfov or game.hfov) if v == VEHICLE else (options.hfov or game.hfov)
            est, each = fit_hfov(locator, [(k[1], k[2], k[3]) for k in keep], start=start)
            fitted[v] = None if est is None else round(est, 2)
            if on_progress:
                on_progress(Progress(len(rows), None, 0.0, f"field of view, {v}: {fitted[v]} from {len(each)} fixes (ran with {start:.1f})"))
    _speed_limits(rows, game, unit)
    if lives is not None:
        from .lives import frame_lives

        for r, k in zip(rows, frame_lives([r.time for r in rows], [r.view for r in rows], lives)):
            r.play_life = k
    chosen = 0
    jumps: list[tuple[float, float]] = []
    if options.sequence and rows:
        chosen = _decide_by_sequence(rows, cands, track_opts, lives is not None, jumps)
    zoom_report = None
    if options.zoomed and any(r.view == ZOOMED for r in rows):
        zoom_report = _solve_zoomed(source, rows, locator, game, unit, options, masks, on_progress)
    rows, report = build_track(rows, track_opts, minimap, anchor)
    report["indoor"] = _nav_floor(rows, level) if anchor is not None else None
    report["sequence_changed"] = chosen
    report["lives_read"] = None if lives is None else {
        "lives": sum(1 for a, b in lives.spans),
        "deaths": sum(1 for _, why in lives.cuts if why == "death"),
        "revives": len(lives.downs),
        "frames_out_of_play": sum(1 for r in rows if r.play_life is None),
    }
    report["jump_without_detected_death"] = [[round(a, 2), round(b, 2)] for a, b in jumps]
    report["zoomed"] = zoom_report
    if options.checks:
        report["check_pictures"] = _check_pictures(source, rows, locator, Path(str(out) + ".check"), options.fps)
    locator.close()
    out = Path(out)
    table = write_table(out.with_suffix(".parquet"), rows, unit=unit, game=game.name, source=source.name, vehicle_offset=game.vehicle_offset, measured=game.vehicle_offset_measured)
    summary = {
        "source": str(source),
        "database": str(db_folder),
        "level": str(level.path),
        "game": game.name,
        "unit_metres": unit,
        "hfov": options.hfov or game.hfov,
        "fps": options.fps,
        "prior_radius_m": prior_m,
        "anchor": None if anchor is None else {
            "median_m": round(anchor.median * unit, 2),
            "p90_m": round(anchor.p90 * unit, 2),
            "pairs": anchor.pairs,
            "corrected_by": len(anchor.corrections),
            "correction_median_m": round(float(np.median(np.linalg.norm(np.array(anchor.corrections)[:, 1:], axis=1))) * unit, 2) if anchor.corrections else None,
        },
        "minimap_share": None if minimap is None else round(sum(1 for r in rows if minimap.at(r.time) is not None) / max(1, len(rows)), 3),
        "hfov_fitted": fitted or None,
        **report,
        "by_source": {s: sum(1 for r in rows if r.source == s) for s in ("visual", "visual+minimap-prior", "minimap", "minimap+nav-floor", "none")},
        "by_view": {
            v: {
                "frames": counts.get(v, 0),
                "visual": sum(1 for r in rows if r.view == v and r.source == "visual"),
                "visual+minimap-prior": sum(1 for r in rows if r.view == v and r.source == "visual+minimap-prior"),
                "minimap": sum(1 for r in rows if r.view == v and r.source == "minimap"),
            }
            for v in (FOOT, VEHICLE, ZOOMED, SCREEN)
        },
        "seconds": round(time.monotonic() - started, 1),
        "seconds_per_frame": round((time.monotonic() - started) / max(1, len(rows)), 3),
    }
    side = out.with_suffix(".summary.json")
    side.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return [table, side], summary


def _solve_zoomed(source: Path, rows: list[Row], locator, game: GameProfile, unit: float, options: Options, masks: dict, on_progress) -> dict:
    """
    The zoomed frames, each from the nearest fix within a few seconds: on
    foot the sight starts at that fix's eye; in a vehicle on the vehicle,
    2.5 m over the ground under its middle (a turret's sight). How far it may
    have moved since grows with the time between them: 2 m, and 4 m a second
    on foot, 8 in a vehicle, at most 12 m. Their zoom is solved
    (locate_zoomed).
    """
    from .views import VEHICLE, ZOOMED

    todo = []
    fixes = [r for r in rows if r.ok and r.position is not None and r.view not in (ZOOMED, "screen")]
    for r in rows:
        if r.view != ZOOMED:
            continue
        near = min(fixes, key=lambda q: abs(q.time - r.time), default=None)
        if near is None or abs(near.time - r.time) > 6.0:
            r.note = "zoomed view: no fix within 6 s to start from"
            continue
        # In a vehicle the sight rides on it: the vehicle is 2.5 m below it, as `seat` is above.
        up = np.array([0.0, 2.5 / unit, 0.0]) if near.view == VEHICLE else np.zeros(3)
        seat = near.position + up if near.view == VEHICLE else near.cam
        reach = min(12.0, 2.0 + (8.0 if near.view == VEHICLE else 4.0) * abs(near.time - r.time))
        todo.append((r, seat, near.yaw, near.pitch or 0.0, reach, up))
    zooms = []
    by_time = {round(r.time, 3): rest for r, *rest in todo}
    rows_at = {round(r.time, 3): r for r, *_ in todo}
    for t, rgb in read_frames(source, [r.time for r, *_ in todo], options.fps):
        r = rows_at[round(t, 3)]
        seat, yaw, pitch, reach, up = by_time[round(t, 3)]
        h, w = rgb.shape[:2]
        key = (w, h, ZOOMED)
        if key not in masks:
            masks[key] = game.mask(w, h, ZOOMED)
        fix, zoom = locator.locate_zoomed(rgb, masks[key], seat, yaw, options.hfov or game.hfov, pitch=pitch, reach=reach)
        if fix.pose is not None and fix.ok:
            r.ok, r.position, r.cam = True, fix.pose.position - up, fix.pose.position.copy()
            r.yaw, r.pitch, r.inliers, r.rmse, r.confidence = fix.pose.yaw, fix.pose.pitch, fix.inliers, fix.rmse, fix.confidence
            r.zoom = zoom
            r.hfov = math.degrees(2 * math.atan(math.tan(math.radians(options.hfov or game.hfov) / 2) / zoom)) if zoom else None
            r.note = f"zoomed view, x{zoom:.1f}"
            zooms.append(zoom)
        else:
            r.note = fix.note
        if on_progress:
            on_progress(Progress(0, None, t, f"zoomed  {'ok ' if fix.ok else 'no '} {fix.inliers:4d} inliers zoom {zoom if zoom else '-'}"))
    return {
        "frames": sum(1 for r in rows if r.view == ZOOMED),
        "tried": len(todo),
        "placed": len(zooms),
        "zoom": None if not zooms else {"median": round(float(np.median(zooms)), 2), "min": round(min(zooms), 2), "max": round(max(zooms), 2), "each": [round(z, 2) for z in zooms]},
    }


def _check_pictures(source: Path, rows: list[Row], locator, folder: Path, fps: float) -> int:
    """A picture for every visual fix: the frame beside the level rendered at its camera, the frame's edges over the render."""
    from .camera import Pose

    wanted = {round(r.time, 3): r for r in rows if r.source in VISUAL_SOURCES and r.cam is not None}
    written = 0
    for t, rgb in read_frames(source, [r.time for r in wanted.values()], fps):
        r = wanted[round(t, 3)]
        fix = _Shown(Pose(r.cam, r.yaw, r.pitch or 0.0), r.ok, r.inliers, r.confidence, r.note)
        kind = "visual" if r.source == "visual" else "visual-prior"
        _check_picture(folder / f"{t:08.2f}s_{r.view}_{kind}.jpg", rgb, locator, fix, r.hfov)
        written += 1
    return written


@dataclass
class _Shown:
    pose: object
    ok: bool
    inliers: int
    confidence: float
    note: str


def _decide_by_sequence(rows: list[Row], cands: list[list], opts: TrackOptions, with_lives: bool = False, jumps: list | None = None) -> int:
    """
    Choose each frame's pose among its candidates along the whole run
    (sequence.py), and make the choice the row's: a weak candidate its
    neighbours agree with becomes a fix, a strong one they all contradict
    stops being one. Returns how many rows changed.

    With the lives the footage showed (`Row.play_life`), the path jumps only
    across a death. Where it left out a stretch of strong fixes (confidence
    0.9 and up, two or more agreeing with each other) that contradicts it,
    it does not guess: both stretches are kept, marked "jump without
    detected death" (a missed death, or a real teleport), and listed in
    `jumps` as (from, to) seconds.
    """
    from .localize import MIN_INLIERS
    from .sequence import decode, emission

    speeds = [r.speed_limit if r.speed_limit is not None else (opts.vehicle_speed if (r.view == "vehicle" and opts.vehicle_speed) else opts.max_speed) for r in rows]
    strong_before = [(r.ok and r.confidence >= 0.9 and r.position is not None, None if r.position is None else r.position.copy(), r.yaw, r.pitch, r.inliers, r.rmse, None if r.cam is None else r.cam.copy(), r.confidence) for r in rows]
    picks = decode(
        [r.time for r in rows],
        [[(c[0], c[1]) for c in cs] for cs in cands],
        speeds,
        opts.margin,
        lives=[r.play_life for r in rows] if with_lives else None,
    )
    changed = 0
    for r, cs, pick in zip(rows, cands, picks):
        was_ok = r.ok
        if pick.index is None:
            if was_ok:
                r.ok = False
                r.note = (r.note + "; " if r.note else "") + "left out by the sequence: its neighbours disagree"
                changed += 1
            continue
        pos, inl, yaw, pitch, rmse, cam = cs[pick.index]
        moved = r.position is None or float(np.linalg.norm(pos - r.position)) > 1e-6
        r.position, r.yaw, r.pitch, r.inliers, r.rmse, r.cam = pos.copy(), yaw, pitch, inl, rmse, cam.copy()
        # Believed when the neighbours along the path agree with it, or when it
        # was the frame's own confident fix all along.
        r.ok = (inl >= MIN_INLIERS and pick.support >= 2) or (was_ok and not moved)
        seq_conf = emission(inl) / 4.0 * (0.6 + 0.1 * min(4, pick.support))
        r.confidence = max(r.confidence if (was_ok and not moved) else 0.0, min(1.0, seq_conf))
        if r.ok and (moved or not was_ok):
            r.note = "chosen along the sequence"
            changed += 1
        elif was_ok and not r.ok:
            r.note = (r.note + "; " if r.note else "") + "left out by the sequence: its neighbours disagree"
            changed += 1
    if with_lives:
        _keep_strong_contradictions(rows, strong_before, speeds, opts, jumps if jumps is not None else [])
    return changed


def _keep_strong_contradictions(rows: list[Row], before: list, speeds: list[float], opts: TrackOptions, jumps: list) -> None:
    """Strong fixes the path left out that agree with each other: put back, and with the path's contradicting frames, marked."""
    NOTE = "jump without detected death"
    lost = [i for i, (strong, pos, *_rest) in enumerate(before) if strong and (not rows[i].ok or np.linalg.norm(rows[i].position - pos) > opts.margin)]

    def agree(i, j, pi, pj):
        return np.linalg.norm(pi - pj) <= max(speeds[i], speeds[j]) * abs(rows[i].time - rows[j].time) + opts.margin

    group = [i for i in lost if any(j != i and rows[j].play_life == rows[i].play_life and abs(rows[j].time - rows[i].time) <= 6.0
                                    and agree(i, j, before[i][1], before[j][1]) for j in lost)]
    for i in group:
        _, pos, yaw, pitch, inl, rmse, cam, conf = before[i]
        r = rows[i]
        r.ok, r.position, r.yaw, r.pitch, r.inliers, r.rmse, r.cam, r.confidence = True, pos, yaw, pitch, inl, rmse, cam, conf
        r.note = NOTE
    # The path's own fixes those contradict, within a few seconds: marked too.
    for i in group:
        for j, r in enumerate(rows):
            if j in group or not r.ok or r.play_life != rows[i].play_life or abs(r.time - rows[i].time) > 10.0:
                continue
            if not agree(i, j, rows[i].position, r.position):
                r.note = NOTE if not r.note else (r.note + "; " + NOTE if NOTE not in r.note else r.note)
    # Stretches: runs of marked frames.
    marked = sorted(r.time for r in rows if r.note and NOTE in r.note)
    for t in marked:
        if jumps and t - jumps[-1][1] <= 6.0:
            jumps[-1] = (jumps[-1][0], t)
        else:
            jumps.append((t, t))


def _check_picture(path: Path, rgb: np.ndarray, locator, fix, hfov: float | None = None) -> None:
    """
    The frame, and beside it the level rendered at the fix with the frame's
    edges drawn over it: if they line up, the fix is right. For checking a
    run by eye where there is no truth to compare with.
    """
    import cv2

    from .camera import Pose

    w = locator.width
    h = int(round(rgb.shape[0] * w / rgb.shape[1]))
    frame = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
    if fix.pose is not None:
        locator.renderer.resize(w, h)
        render = locator.renderer.render(Pose(fix.pose.position, fix.pose.yaw, fix.pose.pitch), hfov or locator.hfov, locator.light).color.copy()
        edges = cv2.Canny(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), 80, 160) > 0
        render[edges] = (255, 40, 40)
        label = f"{'ok' if fix.ok else 'not ok'}  {fix.inliers} inliers  confidence {fix.confidence:.2f}"
    else:
        render = np.zeros_like(frame)
        label = fix.note or "no fix"
    both = np.hstack([frame, render])
    cv2.putText(both, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(both, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])


def _similarity_of(rows: list[Row], options: TrackOptions, minimap):
    from .track import fit_similarity

    src, dst = [], []
    for r in rows:
        if r.ok and r.position is not None:
            here = minimap.at(r.time, options.minimap_within)
            if here is not None:
                src.append(here[0])
                dst.append(r.position[[0, 2]])
    return fit_similarity(np.array(src).reshape(-1, 2), np.array(dst).reshape(-1, 2), threshold=4 * options.margin)


def write_table(
    path: Path,
    rows: list[Row],
    *,
    unit: float,
    game: str,
    source: str,
    vehicle_offset: tuple[float, float] = (0.0, 0.0),
    measured: bool = False,
) -> Path:
    """The rows as a 3DHeat table in the level's frame (Y up), with the viewer's reading instructions."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    def num(values):
        return pa.array([None if v is None or (isinstance(v, float) and not math.isfinite(v)) else float(v) for v in values], type=pa.float64())

    first: set[int] = set()
    seen: set[int] = set()
    for i, r in enumerate(rows):
        if r.smooth is not None and r.life not in seen:
            seen.add(r.life)
            first.add(i)
    # Rows the minimap filled belong to the life of the visual fix nearest in time.
    life_of = []
    for r in rows:
        if r.life >= 0 or r.smooth is None:
            life_of.append(r.life)
            continue
        near = min((q for q in rows if q.life >= 0), key=lambda q: abs(q.time - r.time), default=None)
        life_of.append(near.life if near is not None else -1)
    pos = [r.smooth for r in rows]
    yaw = [r.smooth_yaw if r.smooth_yaw is not None else None for r in rows]
    pitch = [r.pitch if r.source in VISUAL_SOURCES else None for r in rows]
    dirs = [direction(y, p or 0.0) if y is not None else None for y, p in zip(yaw, pitch)]
    stem = Path(source).stem
    columns = {
        "time": num([r.time for r in rows]),
        "event": pa.array(["start" if i in first else "position" for i in range(len(rows))]).dictionary_encode(),
        "x": num([None if p is None else p[0] for p in pos]),
        "y": num([None if p is None else p[1] for p in pos]),
        "z": num([None if p is None else p[2] for p in pos]),
        "yaw": num(yaw),
        "pitch": num(pitch),
        "dir_x": num([None if d is None else d[0] for d in dirs]),
        "dir_y": num([None if d is None else d[1] for d in dirs]),
        "dir_z": num([None if d is None else d[2] for d in dirs]),
        "player": pa.array(["me"] * len(rows)).dictionary_encode(),
        "team": pa.array(["own"] * len(rows)).dictionary_encode(),
        "session": pa.array([f"{stem}#{l + 1:02d}" if l >= 0 else "" for l in life_of]).dictionary_encode(),
        # The life the footage showed (the HUD's deaths), 1 = the first; empty out of play or unread.
        "life": pa.array([r.play_life + 1 if r.play_life is not None and r.play_life >= 0 else None for r in rows], type=pa.int32()),
        "source": pa.array([r.source for r in rows]).dictionary_encode(),
        "view": pa.array([r.view for r in rows]).dictionary_encode(),
        "confidence": num([r.confidence if r.source != "none" else 0.0 for r in rows]),
        "uncertainty": num([r.uncertainty for r in rows]),
        "inliers": pa.array([int(r.inliers) for r in rows], type=pa.int32()),
        "rmse": num([r.rmse if r.inliers else None for r in rows]),
        "x_raw": num([None if r.position is None else r.position[0] for r in rows]),
        "y_raw": num([None if r.position is None else r.position[1] for r in rows]),
        "z_raw": num([None if r.position is None else r.position[2] for r in rows]),
        "yaw_raw": num([r.yaw for r in rows]),
        "pitch_raw": num([r.pitch for r in rows]),
        "kept": pa.array([bool(r.kept) for r in rows]),
        "cam_x": num([None if r.cam is None else r.cam[0] for r in rows]),
        "cam_y": num([None if r.cam is None else r.cam[1] for r in rows]),
        "cam_z": num([None if r.cam is None else r.cam[2] for r in rows]),
        "hfov": num([r.hfov for r in rows]),
        "zoom": num([r.zoom for r in rows]),
        "note": pa.array([r.note for r in rows]),
    }
    table = pa.table(columns)
    hints = {
        "version": 1,
        "kind": "heat3d-locate",
        "game": game,
        # The level's own frame: Y up, the level's units.
        "axes": {"up": "y", "flipX": False, "flipY": False, "flipZ": False, "scale": 1},
        "unitMetres": unit,
        # x, y, z are the player (the eye) or their vehicle; cam_* the camera that saw the frame.
        "vehicleOffset": {"ahead": vehicle_offset[0], "down": vehicle_offset[1], "measured": measured},
        "columns": {
            "x": "x",
            "y": "y",
            "z": "z",
            "time": "time",
            "timeUnit": "seconds",
            "personId": "player",
            "teamId": "team",
            "sessionId": "session",
            "lookMode": "vector",
            "dirX": "dir_x",
            "dirY": "dir_y",
            "dirZ": "dir_z",
            # Every other column, so the viewer keeps it (its inspect card shows only these).
            "extra": ["event", "life", "yaw", "pitch", "source", "view", "confidence", "uncertainty", "inliers", "rmse", "x_raw", "y_raw", "z_raw",
                      "yaw_raw", "pitch_raw", "kept", "cam_x", "cam_y", "cam_z", "hfov", "zoom", "note"],
        },
    }
    meta = dict(table.schema.metadata or {})
    meta[b"heat3d"] = json.dumps(hints).encode("utf-8")
    table = table.replace_schema_metadata(meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    return path
