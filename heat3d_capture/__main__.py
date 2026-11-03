"""
Command line for the capture exporter.

The interface (`python -m heat3d_capture.ui`) is the way in for scanning live —
it has the overlay, the coverage map and the preview. This is for the other case:
a recording that is already on disk, reconstructed offline with the camera path
solved all at once.

    python -m heat3d_capture reconstruct lap.mp4 -o lap.glb

That path exists because live tracking loses a racetrack, and it is worth being
plain that it is slow: it hands overlapping windows of frames to a model that
solves all their cameras together, which is minutes per window on a desktop GPU,
not frames per second. Progress is printed as it goes so a long run is legible
rather than silent.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _reconstruct(args: argparse.Namespace) -> int:
    from .pose.feedforward import DEFAULT_MODEL, describe_licence
    from .scan.offline import OfflineProgress, reconstruct_video

    print(describe_licence(args.model))
    print()

    # PyTorch, VGGT and transformers are not in requirements.txt: only this
    # verb needs them. Checked first, and installed only on a yes.
    from .runtime.preflight import OFFLINE, ensure_console

    if not ensure_console(OFFLINE):
        print(
            "\nThe offline path needs these; see requirements-offline.txt.",
            file=sys.stderr,
        )
        return 1

    started = time.monotonic()
    last = {"stage": ""}

    def show(p: OfflineProgress) -> None:
        elapsed = time.monotonic() - started
        if p.stage != last["stage"]:
            print(f"[{elapsed:6.0f}s] {p.stage}")
            last["stage"] = p.stage
        if p.total:
            print(f"[{elapsed:6.0f}s]   {p.done + 1}/{p.total}  {p.note}", flush=True)

    try:
        result = reconstruct_video(
            args.video,
            args.out,
            solve_budget=args.solve_budget,
            fuse_interval=args.fuse_interval,
            model=args.model,
            on_progress=show,
        )
    except (OSError, ValueError) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    print()
    print(result.summary())
    # A run that produced no file is a failure even though nothing raised, and
    # the exit code has to say so or a script around this will not notice.
    return 0 if result.export else 1


def _route(args: argparse.Namespace) -> int:
    """
    Write the driven route as it arrives, rather than at the end.

    The positions are the cheapest thing in the pipeline and the hardest to get
    again — they need the game running, the right track loaded, and someone to
    drive it. A lap held in memory and lost to a later failure is exactly what
    this is here to stop, so the recorder saves the file every few seconds
    while it grows, each time whole (see `Recorder`).
    """
    import time

    from .telemetry.record import Recorder

    print(f"listening on port {args.port}. Drive, then press Ctrl+C when done.")
    started = time.monotonic()
    last_report = 0.0
    with Recorder(port=args.port, out=args.out) as recorder:
        try:
            while True:
                recorder.poll()
                elapsed = time.monotonic() - started
                if elapsed - last_report >= 1.0:
                    last_report = elapsed
                    kept = len(recorder.positions)
                    if recorder.packets == 0:
                        print(
                            f"\r[{elapsed:5.0f}s] nothing on port {args.port} yet - "
                            "is Data Out on?",
                            end="",
                            flush=True,
                        )
                    else:
                        where = recorder.positions[-1] if kept else None
                        place = (
                            f"  at {where[0]:8.0f} {where[1]:7.0f} {where[2]:8.0f}"
                            if where is not None
                            else ""
                        )
                        print(
                            f"\r[{elapsed:5.0f}s] {recorder.packets} packets, "
                            f"{kept} positions{place}   ",
                            end="",
                            flush=True,
                        )
                if args.seconds and elapsed >= args.seconds:
                    break
        except KeyboardInterrupt:
            pass
        route = recorder.finish()

    print()
    if not len(route):
        print(
            "No positions recorded.\n"
            "  In Forza: Settings -> HUD and Gameplay -> Data Out = ON,\n"
            f"  IP 127.0.0.1, port {args.port}. The car has to be moving."
        )
        return 1

    written = route.save(args.out)
    print(route.summary())
    print(f"\nwrote {written} and {written.with_suffix('.json')}")
    return 0


def _telemetry(args: argparse.Namespace) -> int:
    """
    Record every channel the game sends, one file per lap, for the Race tab.

    Relays each packet on to `--forward` unchanged, so an app already reading
    the game's telemetry (FH Companion) keeps working: point the game at this
    port, and that app at the forward one.
    """
    if args.game == "trackmania":
        # Trackmania is recorded by an Openplanet plugin that writes the files itself.
        import shutil

        source = Path(__file__).resolve().parents[1] / "mods" / "trackmania" / "Heat3dRecorder"
        target = Path.home() / "OpenplanetNext" / "Plugins" / "Heat3dRecorder"
        if args.install:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            print(f"plugin copied to {target}. In Openplanet: Developer > Load plugin, then drive.")
        print(f"runs are written to {Path.home() / 'OpenplanetNext' / 'PluginStorage' / 'Heat3dRecorder'} - load those CSVs in the Race tab.")
        return 0
    if args.game == "beamng":
        from .telemetry import beamng

        if args.install:
            print(f"protocol mod copied to {beamng.install()}. Switch on Options > Other > Protocols > others.")
        written = beamng.run(args.out, port=args.port if args.port != 5300 else beamng.PORT)
        print(f"\n{len(written)} laps written to {args.out}")
        return 0
    if args.game in ("wrc", "dirtrally2", "dirtrally", "dirt4", "rbr"):
        from .telemetry import rally

        port = args.port if args.port != 5300 else rally.DEFAULT_PORTS[args.game]
        if args.game == "wrc" and args.configure:
            config = Path(args.configure)
            print(f"{config}: {rally.configure_wrc(config, port=port)}")
        written = rally.run(args.out, game=args.game, port=port, surface=args.surface)
        print(f"\n{len(written)} stages written to {args.out}")
        return 0
    if args.game != "forza":
        from .telemetry import kunos

        print(f"reading {args.game}'s shared memory. Laps go to {args.out}. Ctrl+C to stop.")
        written = kunos.run(args.out, game=args.game)
        print(f"\n{len(written)} laps written to {args.out}")
        return 0

    from .telemetry.fulllap import parse_forward, run

    forward = parse_forward(args.forward)
    relay = f", passing everything on to {forward[0]}:{forward[1]}" if forward else ""
    print(f"listening on port {args.port}{relay}. Laps go to {args.out}. Ctrl+C to stop.")
    written = run(args.out, port=args.port, forward=forward)
    print(f"\n{len(written)} laps written to {args.out}")
    return 0


def _laps(args: argparse.Namespace) -> int:
    """
    Turn a recorded course into the two files everything downstream wants.

    A route, which says which piece of map to cut out of the game's archive, and
    a table of every sample of every lap, which is the analysis. They are written
    together because separating them is how they end up out of step: a heatmap
    over the wrong stretch of ground looks plausible and is worthless.
    """
    from .telemetry.fhcompanion import (
        NoLapLibrary,
        courses,
        find_course,
        read_course,
    )

    try:
        if args.course is None:
            found = courses(args.library)
            print(f"{len(found)} courses")
            for folder in found:
                name = folder.name.split(" (")[0]
                laps = sum(
                    1 for p in folder.rglob("*.json") if p.name != "course.json"
                )
                print(f"  {laps:4} laps  {name}")
            print("\nName one to write it out:  -o <file> <course>")
            return 0
        folder = find_course(args.course, args.library)
    except (NoLapLibrary, KeyError) as exc:
        print(exc, file=sys.stderr)
        return 1

    course = read_course(folder)
    if not len(course):
        print(f"{course.name} has no readable laps", file=sys.stderr)
        return 1
    print(course.summary())

    out = args.out or Path(course.name.lower().replace(" ", "_"))
    route = course.save_route(out, margin=args.margin)
    samples = course.save_samples(out)
    low, high = course.bounds
    print(
        f"\nwrote {route} and {samples}"
        f"\n\nThe map under it:"
        f"\n  python -m heat3d_gamefiles terrain <track folder> "
        f"--route {route.name} -o {Path(out).stem}.glb"
        f"\n  (or --box {low[0] - args.margin:.0f} {low[2] - args.margin:.0f} "
        f"{high[0] + args.margin:.0f} {high[2] + args.margin:.0f})"
    )
    return 0


def _hud(args: argparse.Namespace) -> int:
    """
    Read a game's HUD out of the player's own recording, after the match.

    The points popup becomes the player's own actions, the down and deploy
    screens their deaths, the minimap their track on a mosaic of the level, and
    the kill feed timed events beside them. Nothing here touches the game: it
    is a video file, read back. See docs/hud-video.md.
    """
    from .hud.ocr import NoOcr
    from .hud.run import Options, Progress, run

    out = args.out or Path(args.video.stem)
    if out.suffix.lower() in (".parquet", ".json", ".jsonl", ".png"):
        out = out.with_suffix("")
    opts = Options(
        game=args.game,
        player=args.player,
        fps=args.fps,
        start=args.start,
        duration=args.seconds,
        gpu=False if args.cpu else None,
        metres_per_pixel=args.metres_per_pixel,
    )
    started = time.monotonic()

    def show(p: Progress) -> None:
        elapsed = time.monotonic() - started
        print(f"[{elapsed:6.0f}s] {p.t:6.0f} / {p.duration:.0f} s of video  {p.note}", flush=True)

    try:
        result = run(args.video, out, opts, on_progress=show)
    except (OSError, ValueError, NoOcr) as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    s = result.summary
    print()
    print(f"player: {s['player'] or 'unknown'} ({s['player_from']})")
    print(
        f"kills {s['kills']}, deaths {s['deaths']}, K/D {s['kd'] if s['kd'] is not None else '-'}, "
        f"{s['lives']} lives, {s['seconds_in_play']:.0f} s in play, {s['feed_lines']} kill-feed lines"
    )
    print(f"own events from {s['own_events_from']}")
    if s["actions"]:
        print(
            f"assists {s['assists']}, revives {s['revives']}, revived {s['revived']}, captures {s['captures']}, "
            f"score {s['score'] if s['score'] is not None else '-'} in {s['popups']} popups"
        )
        print("actions: " + ", ".join(f"{k} {v}" for k, v in s["actions"].items()))
    for m in s["maps"]:
        north = "north up" if m["north_up"] else "north unknown (no compass agreement)"
        print(f"  {m['table']}: {m['rows']} rows, {m['seconds_of_track']:.0f} s of track, {north}")
    print()
    for f in result.files:
        print(f"wrote {f}")
    return 0


def _locate_game(args: argparse.Namespace):
    """The game profile, with whatever the command line overrides."""
    from .locate.camera import hfov_from_vertical
    from .locate.profiles import parse_box, profile

    game = profile(args.game)
    vfov, vehicle_vfov = args.vfov, getattr(args, "vehicle_vfov", None)
    if args.game == "bf6" and not (args.fov or vfov) and args.action != "eval":
        # The player's own field of view, from the game's settings file (read only).
        from .locate.profiles import settings_fov

        found = settings_fov(args.settings)
        if "vfov" in found:
            vfov = found["vfov"]
            vehicle_vfov = vehicle_vfov or found.get("vehicle_vfov")
            print(f"field of view from {found['file']}: {vfov:g} vertical, vehicles {found.get('vehicle_vfov', '-')}")
    hfov = args.fov or (hfov_from_vertical(vfov, 16 / 9) if vfov else None)
    hud = tuple(game.hud) + tuple(parse_box(b) for b in args.mask or [])
    if args.no_hud_mask:
        hud = tuple(parse_box(b) for b in args.mask or [])
    return game.with_overrides(
        hfov=hfov,
        vehicle_hfov=hfov_from_vertical(vehicle_vfov, 16 / 9) if vehicle_vfov else None,
        eye_heights=tuple(args.eye) if args.eye else None,
        max_speed=args.max_speed,
        hud=hud,
    )


def _locate(args: argparse.Namespace) -> int:
    """
    Where each frame of a recording was taken, from the picture against the
    level's own geometry: `build` renders and indexes a level once, `frames`
    locates a recording against it, `eval` compares a result with known
    poses. See docs/locate.md.
    """
    try:
        game = _locate_game(args)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    started = time.monotonic()

    if args.action == "build":
        from .locate.database import BuildOptions, build
        from .locate.render import Light

        options = BuildOptions(
            spacing=args.spacing,
            yaw_step=args.yaw_step,
            pitches=tuple(args.pitch),
            positions=str(args.positions) if args.positions else None,
            box=tuple(args.box) if args.box else None,
            places=args.places,
            head=str(args.head) if args.head else None,
        )
        light = Light(textured=not args.untextured, shadows=args.shadows)

        def say(text: str) -> None:
            print(f"[{time.monotonic() - started:6.0f}s] {text}", flush=True)

        try:
            build(args.level, args.out, game, options, light=light, on_progress=say)
        except (OSError, ValueError) as exc:
            print(f"\n{exc}", file=sys.stderr)
            return 1
        return 0

    if args.action == "train":
        from .locate import poses as places_of
        from .locate.level import load
        from .locate.train import TrainOptions, real_pairs, train

        level = load(args.level)
        box = tuple(args.box) if args.box else None
        places, cars = places_of.places(level, args.spacing / level.unit_metres, args.places, box=box)
        real = [pair for table, video in (args.real or []) for pair in real_pairs(table, video, game, least=args.real_confidence)]
        print(f"{len(places):,} training places for players, {0 if cars is None else len(cars):,} for vehicles, {len(real)} real frames", flush=True)
        train(args.level, places, game, args.out, TrainOptions(steps=args.steps), real=real or None, vehicle_places=cars,
              on_progress=lambda text: print(f"[{time.monotonic() - started:6.0f}s] {text}", flush=True))
        print(f"wrote {args.out}")
        return 0

    if args.action == "frames":
        from .locate.run import Options, Progress, locate_frames

        if not args.source.exists():
            print(f"no such file or folder: {args.source}", file=sys.stderr)
            return 2
        out = args.out or Path(args.source.stem + ".locate")
        options = Options(
            fps=args.fps,
            start=args.start,
            seconds=args.seconds,
            width=args.width,
            hfov=game.hfov,
            shortlist=args.shortlist,
            normalisation=args.normalise,
            minimap=str(args.minimap) if args.minimap else None,
            prior_radius=args.prior_radius,
            anchor=str(args.minimap_anchor) if args.minimap_anchor else None,
            level_search=not args.no_level_search,
            lives=str(args.lives) if args.lives else None,
            level=str(args.level) if args.level else None,
            check_every=args.check_every,
            sequence=not args.no_sequence,
            fit_fov=args.fit_fov,
            zoomed=not args.no_zoomed,
            checks=not args.no_checks,
        )

        def show(p: Progress) -> None:
            print(f"[{time.monotonic() - started:6.0f}s] {p.t:7.1f} s  {p.note}", flush=True)

        try:
            files, summary = locate_frames(args.source, args.db, out, game, options, on_progress=show)
        except (OSError, ValueError) as exc:
            print(f"\n{exc}", file=sys.stderr)
            return 1
        print()
        by = summary["by_source"]
        print(
            f"{summary['frames']} frames: {by['visual']} placed from the picture, {by['minimap']} from the minimap, "
            f"{by['none']} not placed; {summary['outliers']} visual fixes voted out; {summary['lives']} lives; "
            f"{summary['seconds_per_frame']:.2f} s a frame"
        )
        for f in files:
            print(f"wrote {f}")
        return 0

    from .locate.evaluate import compare, read_poses

    located = read_poses(str(args.located))
    truth = read_poses(str(args.truth))
    try:
        result = compare(located, truth, args.offset, args.unit_metres)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    import json

    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="heat3d_capture",
        description="Reconstruct a level from a recording.",
        epilog=(
            "For live scanning with the overlay and coverage map, run "
            "python -m heat3d_capture.ui instead."
        ),
    )
    sub = parser.add_subparsers(dest="verb", required=True)

    p = sub.add_parser(
        "route",
        help="record a lap's positions from the game's telemetry, and nothing else",
    )
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--port", type=int, default=5300)
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="stop after this long; 0 means run until interrupted",
    )
    p.set_defaults(run=_route)

    p = sub.add_parser(
        "telemetry",
        help="record every telemetry channel, one file per lap, for the viewer's Race tab",
    )
    p.add_argument("-o", "--out", type=Path, default=Path("laps"), help="folder for the lap files")
    p.add_argument("--port", type=int, default=5300, help="the port the game sends to")
    p.add_argument(
        "--forward",
        default=None,
        help="host:port to pass every packet on to, e.g. 127.0.0.1:5301 for FH Companion",
    )
    p.add_argument(
        "--game",
        choices=["forza", "ac", "acc", "acevo", "acrally", "wrc", "dirtrally2", "dirtrally", "dirt4", "rbr", "beamng", "trackmania"],
        default="forza",
        help=(
            "forza (Data Out over UDP, the default); an Assetto Corsa game from its shared memory; "
            "wrc, dirtrally2, dirtrally, dirt4 or rbr from their UDP telemetry; beamng from the heat3d "
            "protocol mod; trackmania from the Openplanet plugin's files (see docs/games.md)"
        ),
    )
    p.add_argument("--install", action="store_true", help="beamng / trackmania: copy the mod or plugin into the game's folder first")
    p.add_argument("--configure", default=None, help="wrc: the game's telemetry config.json to switch the packet on in (backed up first)")
    p.add_argument(
        "--surface",
        choices=["tarmac", "loose", "snow", "ice", "mixed"],
        default=None,
        help=(
            "rally games: the stage's surface, written into each file; without it the "
            "file names none and the viewer works it out"
        ),
    )
    p.set_defaults(run=_telemetry)

    p = sub.add_parser(
        "laps", help="read a recorded lap library, and write out one course"
    )
    p.add_argument(
        "course",
        nargs="?",
        default=None,
        help="course name, loosely matched; omit to list what is there",
    )
    p.add_argument("-o", "--out", type=Path, default=None)
    p.add_argument(
        "--library",
        type=Path,
        default=None,
        help="where the laps live (default: %%LOCALAPPDATA%%/FHCompanion/laps)",
    )
    p.add_argument(
        "--margin",
        type=float,
        default=80.0,
        help="metres of map to keep around the course (default 80)",
    )
    p.set_defaults(run=_laps)

    p = sub.add_parser("reconstruct", help="solve a recording offline and write a .glb")
    p.add_argument("video", type=Path)
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument(
        "--solve-budget",
        type=int,
        default=260,
        help=(
            "how many frames the solver may use (default 260). They are spaced by "
            "how far the picture moves rather than by the clock, so a fast section "
            "gets more of them. More is more accurate and much slower: cost is "
            "minutes per window of 16."
        ),
    )
    p.add_argument(
        "--fuse-interval",
        type=float,
        default=0.4,
        help="seconds between frames fused into geometry (default 0.4)",
    )
    p.add_argument(
        "--model",
        choices=["vggt-1b", "vggt-1b-commercial"],
        default="vggt-1b",
        help="which weights to solve with (default vggt-1b, non-commercial)",
    )
    p.set_defaults(run=_reconstruct)

    p = sub.add_parser(
        "hud",
        help="read the player's own actions, deaths and minimap track, and the kill feed, out of a recording, after the match",
    )
    p.add_argument("video", type=Path)
    p.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="output path without extension; the files are <out>.parquet, .events.jsonl, .summary.json, .map.png, .map.json",
    )
    p.add_argument("--game", choices=["bf6"], default="bf6", help="whose HUD to read (default bf6, Battlefield 6)")
    p.add_argument(
        "--player",
        default=None,
        help="the player's name as the kill feed shows it, matched loosely; without it the squad list or the feed's own-name colour is used",
    )
    p.add_argument("--fps", type=float, default=5.0, help="minimap samples per second (default 5)")
    p.add_argument("--start", type=float, default=0.0, help="seconds into the video to begin at")
    p.add_argument("--seconds", type=float, default=None, help="how much of the video to read (default: all of it)")
    p.add_argument(
        "--metres-per-pixel",
        type=float,
        default=None,
        help="the minimap's scale, if known: metres per minimap pixel at the usual zoom (296 per minimap at 1080p); without it positions are in those pixels",
    )
    p.add_argument("--cpu", action="store_true", help="decode on the CPU even when an NVIDIA card is there")
    p.set_defaults(run=_hud)

    p = sub.add_parser(
        "locate",
        help="where each frame of a recording was taken, from the picture against the level's geometry",
    )
    actions = p.add_subparsers(dest="action", required=True)
    build = actions.add_parser("build", help="render a level from every place a player can stand, and index it")
    build.add_argument("level", type=Path, help="the level's .glb (or .gltf), textured, in the viewer's frame")
    build.add_argument("-o", "--out", type=Path, required=True, help="the database folder to write")
    build.add_argument("--spacing", type=float, default=2.5, help="metres between the places views are taken from (default 2.5)")
    build.add_argument("--yaw-step", type=float, default=30.0, help="degrees between the views' directions (default 30)")
    build.add_argument("--pitch", type=float, nargs="+", default=[0.0], help="pitches to render at, degrees up (default 0)")
    build.add_argument(
        "--positions",
        type=Path,
        default=None,
        help="a table (Parquet or CSV with x, y, z in the level's frame, at the feet) to take places from instead of every floor",
    )
    build.add_argument("--untextured", action="store_true", help="render shape and light only (a level whose textures are missing)")
    build.add_argument("--shadows", action="store_true", help="cast the sun's shadows in the renders (the level's own sun when it names one)")
    build.add_argument(
        "--places",
        choices=["auto", "nav", "ground", "floors"],
        default="auto",
        help="where views are taken from: nav (players on the navigation mesh, vehicles on the ground), ground, floors (every upward face); auto (default): nav when the level has one",
    )
    build.add_argument("--head", type=Path, default=None, help="a per-map head from `locate train` for the descriptors")
    build.add_argument(
        "--box",
        type=float,
        nargs=4,
        metavar=("X0", "Z0", "X1", "Z1"),
        default=None,
        help="only places inside this box, in the level's units: the part of the level anyone plays in",
    )
    frames = actions.add_parser("frames", help="locate the frames of a recording (or a folder of pictures)")
    frames.add_argument("source", type=Path, help="a video, a picture, or a folder of pictures")
    frames.add_argument("--db", type=Path, required=True, help="the database `locate build` wrote")
    frames.add_argument("-o", "--out", type=Path, default=None, help="output path without extension (default <source>.locate)")
    frames.add_argument("--level", type=Path, default=None, help="the level's .glb, if it moved since the database was built")
    frames.add_argument("--fps", type=float, default=2.0, help="frames located per second of video (default 2)")
    frames.add_argument("--start", type=float, default=0.0, help="seconds into the video to begin at")
    frames.add_argument("--seconds", type=float, default=None, help="how much of the video to read (default: all of it)")
    frames.add_argument("--width", type=int, default=960, help="the width frames are matched at (default 960)")
    frames.add_argument("--shortlist", type=int, default=8, help="database views tried per frame (default 8)")
    frames.add_argument("--normalise", choices=["none", "clahe", "gray"], default="none", help="light normalisation before matching (default none)")
    frames.add_argument("--minimap", type=Path, default=None, help="the `hud` verb's table: the fallback where the picture gives no fix")
    frames.add_argument(
        "--prior-radius",
        type=float,
        default=None,
        help="optional speed-up: search only database views this many metres from the minimap's position (needs --minimap)",
    )
    frames.add_argument(
        "--minimap-anchor",
        type=Path,
        default=None,
        help="a JSON file tying the minimap to the level (scale, rotation, shift, its measured error; docs/locate.md): the minimap becomes a search prior from the first frame (needs --minimap)",
    )
    frames.add_argument(
        "--lives",
        type=Path,
        default=None,
        help="the `hud` verb's table whose deaths, spawns and revives say when the player was in play (default: the --minimap table); positions jump only across a death",
    )
    frames.add_argument(
        "--no-level-search",
        action="store_true",
        help="with a prior: when the search near it finds nothing, do not search the whole level as well",
    )
    frames.add_argument(
        "--check-every",
        type=int,
        default=0,
        help="every N located frames, write <out>.check/<frame>.jpg: the frame beside the level rendered at its fix, the frame's edges drawn over it",
    )
    frames.add_argument("--no-sequence", action="store_true", help="decide every frame on its own, not along the run")
    frames.add_argument("--no-zoomed", action="store_true", help="do not solve zoomed views (scopes, sights) from their neighbours' fixes")
    frames.add_argument("--no-checks", action="store_true", help="do not write a check picture for every visual fix (<out>.check)")
    frames.add_argument(
        "--fit-fov",
        action="store_true",
        help="after the run, fit the field of view to the strongest fixes (per view) and report it in the summary, for the next run's --fov",
    )
    trainer = actions.add_parser("train", help="train a per-map place model on renders of the level (and frames already located)")
    trainer.add_argument("level", type=Path, help="the level's .glb")
    trainer.add_argument("-o", "--out", type=Path, required=True, help="the head file to write (.pt)")
    trainer.add_argument("--spacing", type=float, default=4.0, help="metres between the floor points training views are taken from (default 4)")
    trainer.add_argument("--box", type=float, nargs=4, metavar=("X0", "Z0", "X1", "Z1"), default=None, help="only this part of the level")
    trainer.add_argument("--places", choices=["auto", "nav", "ground", "floors"], default="auto", help="where training views are taken from (as for build)")
    trainer.add_argument("--steps", type=int, default=600, help="training steps (default 600)")
    trainer.add_argument(
        "--real",
        nargs=2,
        action="append",
        metavar=("TABLE", "VIDEO"),
        default=None,
        help="a `locate frames` table and its recording: its confident fixes join as real pairs (repeatable)",
    )
    trainer.add_argument("--real-confidence", type=float, default=0.85, help="the confidence a fix needs to join as a real pair (default 0.85)")
    evaluate = actions.add_parser("eval", help="compare a located table with known camera poses")
    evaluate.add_argument("located", type=Path, help="the table `locate frames` wrote")
    evaluate.add_argument("--truth", type=Path, required=True, help="a table of time, x, y, z, yaw, pitch in the level's frame")
    evaluate.add_argument("--offset", type=float, default=None, help="truth time = video time + this (default: searched for)")
    evaluate.add_argument("--unit-metres", type=float, default=1.0, help="metres per level unit, for the errors (default 1)")
    for q in (build, frames, evaluate, trainer):
        q.add_argument("--game", choices=["bf6", "generic"], default="bf6", help="the game's profile (default bf6)")
        q.add_argument("--eye", type=float, nargs="+", default=None, help="eye heights above the floor, metres, standing first")
        q.add_argument("--fov", type=float, default=None, help="horizontal field of view of the recording, degrees")
        q.add_argument("--vfov", type=float, default=None, help="or the vertical one (Battlefield's slider), for a 16:9 recording")
        q.add_argument("--vehicle-vfov", type=float, default=None, help="the vertical field of view of vehicle cameras (Battlefield's vehicle slider)")
        q.add_argument(
            "--settings",
            default=None,
            help="bf6: the game's settings file to read the field of view from (default: the newest under Documents/Battlefield 6/settings); used when no --fov/--vfov is given",
        )
        q.add_argument("--max-speed", type=float, default=None, help="metres a second a player can move, for the outlier vote")
        q.add_argument("--mask", action="append", default=None, help="another screen box that is not the level: x,y,w,h on 1920x1080; repeatable")
        q.add_argument("--no-hud-mask", action="store_true", help="drop the profile's HUD boxes (keep only --mask ones)")
    p.set_defaults(run=_locate)

    args = parser.parse_args(argv)
    # The verbs that take no video: the existence check below is about the
    # recording a reconstruction reads, and these do not read one.
    if args.verb in ("route", "laps", "telemetry", "locate"):
        return args.run(args)
    if not args.video.exists():
        print(f"no such file: {args.video}", file=sys.stderr)
        return 2
    return args.run(args)


def _check_for_update() -> None:
    """A newer release of the tools: say so, and offer it (see heat3d_update in the repository root)."""
    import sys as _sys
    from pathlib import Path as _Path

    root = str(_Path(__file__).resolve().parents[1])
    if root not in _sys.path:
        _sys.path.append(root)
    try:
        import heat3d_update
    except ImportError:
        return
    heat3d_update.startup("heat3d_capture")


if __name__ == "__main__":
    _check_for_update()
    raise SystemExit(main())
