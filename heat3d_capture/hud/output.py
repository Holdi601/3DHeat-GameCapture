"""
What a HUD run writes: the table the viewer opens, the feed as lines, a summary, the mosaic.

    <name>.parquet        the player's track and their events, 3DHeat format
    <name>.events.jsonl   the player's own actions and deaths, and every kill-feed line,
                          everyone's, with its time
    <name>.summary.json   kills, deaths, assists, revives, score, time alive, distance;
                          what was and was not found
    <name>.map.png        the mosaic of the minimap, north up when the compass allowed
    <name>.map.json       where that picture lies in the table's coordinates: the two
                          anchors the viewer's Map image panel asks for

The table follows the watcher's conventions (`heat3d_watch/session.py`): one
row per thing that happened, `event` saying what, `player` saying who ("me" -
it is only ever the player's own rows that have a position), `session` one
per life, and the viewer's reading instructions in the Parquet footer under
`heat3d`. Its plane is x east, y north, z zero, so the footer says z is up.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

#: Columns in this order; anything else a row carries follows.
COLUMNS = (
    "time", "event", "x", "y", "z", "player", "team", "session", "heading", "dir_x", "dir_y", "dir_z",
    "source", "text", "points", "subject", "killer", "victim", "weapon", "headshot", "marker",
)


def write_table(path: Path, rows: list[dict[str, Any]], *, game: str, scale: float = 1.0) -> Path:
    """`rows` as Parquet with the `heat3d` footer. `scale` is metres per unit, 1 when unknown."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    extra: list[str] = []
    for r in rows:
        for k in r:
            if k not in COLUMNS and k not in extra:
                extra.append(k)
    names = [c for c in COLUMNS if any(c in r for r in rows)] + extra
    columns: dict[str, pa.Array] = {}
    for name in names:
        values = [r.get(name) for r in rows]
        if name in ("time", "x", "y", "z", "heading", "dir_x", "dir_y", "dir_z"):
            columns[name] = pa.array([None if v is None else float(v) for v in values], type=pa.float64())
        elif name == "headshot":
            columns[name] = pa.array([bool(v) if v is not None else None for v in values], type=pa.bool_())
        elif all(v is None or (isinstance(v, (int, float)) and not isinstance(v, bool)) for v in values):
            columns[name] = pa.array([None if v is None else float(v) for v in values], type=pa.float64())
        else:
            columns[name] = pa.array(["" if v is None else str(v) for v in values], type=pa.string()).dictionary_encode()
    table = pa.table(columns)
    hints = {
        "version": 1,
        "kind": "heat3d-hud",
        "game": game,
        # x east, y north, z 0: the plane is x-y, so z is up.
        "axes": {"up": "z", "flipX": False, "flipY": False, "flipZ": False, "scale": scale},
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
            "extra": [
                c for c in ("event", "source", "text", "points", "subject", "killer", "victim", "weapon", "marker", "headshot")
                if c in names
            ],
        },
    }
    meta = dict(table.schema.metadata or {})
    meta[b"heat3d"] = json.dumps(hints).encode("utf-8")
    table = table.replace_schema_metadata(meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    return path


def write_json(path: Path, doc: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def map_anchors(width: int, height: int, x0: float, y0: float, per_pixel: float) -> list[dict[str, float]]:
    """
    The viewer's two map anchors for a picture whose pixel (0, 0) is at table (x0, y0).

    Rows of the picture run southwards (table y falls as the pixel row rises),
    which is the viewer's default "Flip north/south" on.
    """
    return [
        {"px": 0, "py": 0, "worldX": x0, "worldZ": y0},
        {"px": width, "py": height, "worldX": x0 + width * per_pixel, "worldZ": y0 - height * per_pixel},
    ]


def write_map(png: Path, picture: np.ndarray, anchors: list[dict[str, float]], note: dict[str, Any]) -> tuple[Path, Path]:
    import cv2

    png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(png), picture)
    doc = {
        "format": "heat3d-map-image",
        "version": 1,
        "image": png.name,
        "width": int(picture.shape[1]),
        "height": int(picture.shape[0]),
        "flipNorthSouth": True,
        "anchors": anchors,
        "howTo": (
            "In the viewer: Background / level panel > Map image... > choose the PNG, keep 'Flip "
            "north/south' on, and type the two anchors below into Placement (px, py, world X, world Z)."
        ),
        **note,
    }
    side = png.with_suffix(".json")
    side.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return png, side


def heading_vector(heading: float | None) -> tuple[float | None, float | None, float | None]:
    """A bearing (degrees clockwise from north) as a direction in the table's x-east, y-north plane."""
    if heading is None or not math.isfinite(heading):
        return None, None, None
    r = math.radians(heading)
    return round(math.sin(r), 5), round(math.cos(r), 5), 0.0
