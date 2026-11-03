"""
A level's database for locating frames: the poses of many renders of it, and
one global descriptor per render.

    <db>/db.json      what it was built from and with: the level, the game
                      profile, field of view, light, descriptor model, counts
    <db>/views.npz    position, yaw, pitch of every view; its descriptor (float16)

Only what retrieval needs is stored. The local features and their 3D points,
which a frame is finally solved against, are not: they are made again at
query time by rendering the few views retrieval picked, which takes
milliseconds and means a database is a few hundred megabytes rather than tens
of gigabytes. It also means that after a first solve, the level can be
rendered at the solved pose itself and matched again - the refinement that
brings the position from "near that view" down to centimetres (see
`localize.py`). The price is that locating needs the level file and an
OpenGL context, not just the database.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from . import poses as P
from .features import GLOBAL_MODEL, GLOBAL_SIZE, GlobalDescriptor
from .level import Level, load
from .profiles import GameProfile
from .render import Light, Renderer


@dataclass
class BuildOptions:
    #: Metres between the places views are taken from.
    spacing: float = 2.5
    yaw_step: float = 30.0
    pitches: tuple[float, ...] = (0.0,)
    #: A table of floor positions to take places from instead of every floor.
    positions: str | None = None
    #: Only places inside this box: x0, z0, x1, z1 in level units.
    box: tuple[float, float, float, float] | None = None
    #: Where views are taken from (poses.places): `auto` (the navigation mesh when the level
    #: carries one, else every floor), `nav`, `ground`, `floors`.
    places: str = "auto"
    #: A per-map head (train.py) for the descriptors.
    head: str | None = None
    batch: int = 128
    seed: int = 0


@dataclass
class Database:
    folder: Path
    meta: dict
    views: P.Views
    descriptors: np.ndarray  # (n, d) float32, unit length

    @property
    def hfov(self) -> float:
        return float(self.meta["hfov"])


def build(
    level_path: str | Path,
    out: str | Path,
    game: GameProfile,
    options: BuildOptions | None = None,
    *,
    light: Light | None = None,
    on_progress: Callable[[str], None] = print,
) -> Database:
    options = options or BuildOptions()
    started = time.monotonic()
    level = load(level_path)
    unit = level.unit_metres
    if light is None:
        light = Light()
    if level.extras.get("sun") and light.sun == Light().sun:
        # The level says where its sun is: light the renders from there, as the game does.
        light = Light(**{**asdict(light), "sun": tuple(float(v) for v in level.extras["sun"])})
    on_progress(f"{Path(level_path).name}: {level.triangles:,} triangles, 1 unit = {unit:g} m")
    h, w = GLOBAL_SIZE
    renderer = Renderer(level, w, h)
    spacing = options.spacing / unit
    eyes = [e / unit for e in game.eye_heights]
    vehicle = game.vehicle_camera / unit if game.vehicle_camera else None
    if options.positions:
        floor = P.points_from_table(options.positions, spacing, options.box)
        on_progress(f"{len(floor):,} places from {options.positions}")
        cars = None
    else:
        floor, cars = P.places(level, spacing, options.places, options.seed, options.box)
        on_progress(f"{len(floor):,} places for players, {options.spacing:g} m apart ({options.places}); checking each from its eye")
        floor = floor[P.check(renderer, floor, eyes[0])]
        on_progress(f"{len(floor):,} kept (the rest are inside geometry or have no headroom)")
        if vehicle and cars is not None:
            cars = cars[P.check(renderer, cars, vehicle)]
            on_progress(f"{len(cars):,} places for vehicle cameras, {vehicle * unit:g} m over the ground")
    views = P.views_at(floor, eyes, options.yaw_step, list(options.pitches), options.seed)
    if vehicle and cars is not None and len(cars):
        views = P.merge(views, P.views_at(cars, [vehicle], options.yaw_step, list(options.pitches), options.seed + 1))
    on_progress(f"{len(views):,} views: {len(eyes)} eye height(s){' and the vehicle camera' if vehicle else ''} x {int(360 / options.yaw_step)} yaws x {len(options.pitches)} pitch(es)")

    describe = GlobalDescriptor(head=options.head)
    desc = np.zeros((len(views), describe.dim), np.float16)
    last = time.monotonic()
    for start in range(0, len(views), options.batch):
        stop = min(len(views), start + options.batch)
        pictures = [renderer.render(views.pose(i), game.hfov, light).color for i in range(start, stop)]
        desc[start:stop] = describe(pictures)
        if time.monotonic() - last > 5 or stop == len(views):
            last = time.monotonic()
            on_progress(f"  {stop:,} / {len(views):,} rendered and described")
    renderer.release()

    folder = Path(out)
    folder.mkdir(parents=True, exist_ok=True)
    np.savez(
        folder / "views.npz",
        position=views.position,
        yaw=views.yaw,
        pitch=views.pitch,
        place=views.place,
        eye=views.eye,
        descriptor=desc,
    )
    stat = Path(level_path).stat()
    meta = {
        "version": 1,
        "level": str(Path(level_path).resolve()),
        "level_bytes": stat.st_size,
        "level_mtime": stat.st_mtime,
        "unit_metres": unit,
        "game": asdict(game),
        "hfov": game.hfov,
        "light": asdict(light),
        "descriptor": {
            "model": GLOBAL_MODEL,
            "size": list(GLOBAL_SIZE),
            "dim": describe.dim,
            "head": str(Path(options.head).resolve()) if options.head else None,
        },
        "options": asdict(options),
        "views": len(views),
        "places": int(len(floor)),
        "vehicle_places": int(len(cars)) if (not options.positions and cars is not None and vehicle) else 0,
        "seconds": round(time.monotonic() - started, 1),
    }
    (folder / "db.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    on_progress(f"wrote {folder} ({len(views):,} views) in {meta['seconds']:.0f} s")
    return Database(folder, meta, views, desc.astype(np.float32))


def open_db(folder: str | Path) -> Database:
    folder = Path(folder)
    meta_path = folder / "db.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"{folder} is not a locate database (no db.json); build one with `locate build`")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    z = np.load(folder / "views.npz")
    views = P.Views(z["position"], z["yaw"], z["pitch"], z["place"], z["eye"])
    return Database(folder, meta, views, z["descriptor"].astype(np.float32))


def level_for(db: Database, given: str | Path | None = None) -> Level:
    """The level the database was built from, or the one given; refuses one that changed since."""
    path = Path(given or db.meta["level"])
    if not path.exists():
        raise FileNotFoundError(f"the level {path} is not there; pass --level <the .glb the database was built from>")
    if path.stat().st_size != db.meta.get("level_bytes"):
        raise ValueError(f"{path} is not the file {db.folder} was built from (its size differs); rebuild the database")
    return load(path)
