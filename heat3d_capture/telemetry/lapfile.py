"""
One lap or stage as a `heat3d-lap` file, for any game.

Every recorder decodes its game's packets into frames - flat dicts under the
canonical channel names (`docs/lap-format.md`), per wheel as
`name.FL` - and hands a finished run here. What the file says about the game
beyond the numbers goes in `meta`, which the viewer reads to interpret them:

- `slip`: what the slip channels hold, where the game sends any - `peak`
  (normalised so past 1 the tyre lets go), `scaled` (a physical slip divided
  by a typical tarmac peak), `physical` (a fraction and radians), `index`
  (a 0..1 sliding measure);
- `discipline`: `circuit`, `rally` or `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` or `mixed`, when known.

Channels a game does not send are simply absent; the viewer derives what it
can (drift angle, slip from wheel speeds, airborne) from what is there. A
sample a channel has no value for - missing from that frame, or not a finite
number - is written as `null`: `NaN` and `Infinity` are not JSON, and a
browser's `JSON.parse` refuses the whole file over one of them.
"""

from __future__ import annotations

import json
import math
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

WHEELS = ("FL", "FR", "RL", "RR")

#: Units the viewer's channel table stores, for the file's own record.
UNITS = {
    "time": "s",
    "distance": "m",
    "x": "m",
    "y": "m",
    "z": "m",
    "speed": "m/s",
    "latVel": "m/s, car frame, to the right",
    "longVel": "m/s, car frame, forwards",
    "vertVel": "m/s, car frame, up",
    "latAcc": "m/s2",
    "longAcc": "m/s2",
    "vertAcc": "m/s2",
    "yaw": "rad",
    "throttle": "0..1",
    "brake": "0..1",
    "clutch": "0..1",
    "handbrake": "0..1",
    "steer": "-1..1, positive right",
    "wheelSurfaceSpeed": "m/s",
    "wheelSpeed": "rad/s",
    "suspensionM": "m",
    "suspension": "0..1 of the lap's travel",
    "brakeTemp": "degC",
    "tireTemp": "degC",
}


def clean(value, digits: int = 5):
    """A sample as JSON can hold it: rounded, and None where it is not a finite number."""
    if isinstance(value, float):
        return round(value, digits) if math.isfinite(value) else None
    return value


@dataclass
class Run:
    """One lap or stage of frames."""

    number: int
    frames: list[dict] = field(default_factory=list)
    #: The game's own time for it, when the game said.
    seconds: float | None = None
    complete: bool = False

    @property
    def metres(self) -> float:
        total = 0.0
        for a, b in zip(self.frames, self.frames[1:]):
            total += math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))
        return total


def document(run: Run, *, game: str, meta: dict, track: str | None = None, car: dict | None = None) -> dict:
    """A run as a `heat3d-lap` document."""
    frames = run.frames
    t0 = frames[0]["time"]
    names = sorted({k for f in frames for k in f} - {"time"})
    channels: dict[str, list] = {"time": [], "distance": []}
    for name in names:
        if name != "distance":
            channels[name] = []
    travelled = 0.0
    previous = None
    for f in frames:
        if previous is not None:
            travelled += math.dist((previous["x"], previous["y"], previous["z"]), (f["x"], f["y"], f["z"]))
        previous = f
        channels["time"].append(round(f["time"] - t0, 4))
        channels["distance"].append(round(travelled, 3))
        for name in names:
            if name == "distance":
                continue
            channels[name].append(clean(f.get(name)))
    # Suspension as 0..1 of the travel this run used, for the car's bars and
    # for telling a wheel hanging in the air.
    for wheel in WHEELS:
        travel = channels.get(f"suspensionM.{wheel}")
        if travel and f"suspension.{wheel}" not in channels:
            finite = [v for v in travel if v is not None]
            if not finite:
                continue
            lo, hi = min(finite), max(finite)
            span = hi - lo if hi > lo else 1.0
            channels[f"suspension.{wheel}"] = [None if v is None else round((v - lo) / span, 4) for v in travel]
    seconds = run.seconds if run.seconds is not None else channels["time"][-1]
    return {
        "format": "heat3d-lap",
        "version": 1,
        "game": game,
        "track": track,
        "recordedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "car": car or {},
        "lap": {"number": run.number, "seconds": round(seconds, 4), "complete": run.complete, "metres": round(run.metres, 1)},
        "meta": meta,
        "units": {k: v for k, v in UNITS.items() if k in channels or any(c.startswith(k + ".") for c in channels)},
        "channels": channels,
    }


def write(run: Run, folder: str | Path, *, game: str, meta: dict, track: str | None = None, car: dict | None = None) -> Path:
    """Write a run; the file name carries the game, the time and the run's length."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    doc = document(run, game=game, meta=meta, track=track, car=car)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kind = "stage" if meta.get("discipline") == "rally" else "lap"
    tag = "" if run.complete else "_partial"
    path = folder / f"{game}_{stamp}_{kind}{run.number}_{doc['lap']['seconds']:.3f}s{tag}.json"
    path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    return path


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ---------------------------------------------------------------- everything received

#: 3DHeat's converter rule, which the raw sidecar follows.
RULE = "https://github.com/Holdi601/3DHeat/blob/main/docs/converters.md"
_FRAME = struct.Struct("<II")


class RawLog:
    """
    Everything a recorder receives, kept whole beside its lap files.

    A lap file holds the channels the decoder understands, for the laps it
    closed; the game sends more than that - packets in the menus and between
    laps, bytes nobody has named, pages the decoder reads only in part. 3DHeat's
    converter rule (docs/converters.md in the viewer's repository) keeps all of
    it: every packet or page is framed into `<name>.raw.bin` the moment it
    arrives, so a crash loses nothing, and `close()` turns that into
    `<name>.raw.parquet` (zstd; columns `time`, `ms`, `type`, `used`,
    `payload`, `text`, as the watcher's `heat.raw.parquet`) when pyarrow is
    installed - without it the `.raw.bin` stays, readable by `read_frames`.
    `<name>.summary.json` gets the self-check: per `type`, how many items were
    seen, how many also went into lap files (`used`), and `lost`, which is 0.

    `type` is the source's own word for an item (a packet's format, a shared
    memory page's name); `used` says the decoder turned it into a lap's frame.
    """

    def __init__(self, folder: str | Path, name: str, *, game: str = ""):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.game = game
        self.counts: dict[str, list[int]] = {}
        self.started = time.time()
        self._mono = time.monotonic()
        self._file = (self.folder / f"{name}.raw.bin").open("ab")
        self._flushed = self._mono

    @property
    def bin_path(self) -> Path:
        return self.folder / f"{self.name}.raw.bin"

    def keep(self, type: str, payload: bytes | None = None, *, used: bool = False, text: str | None = None) -> None:
        """One item, whole."""
        if self._file is None:
            return
        now = time.monotonic()
        head = {"time": round(now - self._mono, 4), "ms": int(time.time() * 1000), "type": str(type), "used": bool(used)}
        if text is not None:
            head["text"] = text
        h = json.dumps(head, separators=(",", ":")).encode("utf-8")
        body = bytes(payload) if payload is not None else b""
        self._file.write(_FRAME.pack(len(h), len(body)))
        self._file.write(h)
        self._file.write(body)
        c = self.counts.setdefault(head["type"], [0, 0])
        c[0] += 1
        c[1] += int(bool(used))
        if now - self._flushed >= 2.0:
            self._flushed = now
            self._file.flush()

    def completeness(self) -> dict:
        types = {
            k: {"seen": n, "decoded": 0, "partial": used, "raw": n - used, "lost": 0}
            for k, (n, used) in sorted(self.counts.items())
        }
        return {"rule": RULE, "sidecars": [f"{self.name}.raw.parquet"], "types": types, "lost": 0}

    def close(self) -> Path | None:
        """The sidecar and its summary; returns the sidecar (None when nothing arrived)."""
        if self._file is None:
            return None
        self._file.close()
        self._file = None
        if not self.counts:
            self.bin_path.unlink(missing_ok=True)
            return None
        out: Path = self.bin_path
        try:
            out = write_parquet(self.bin_path, self.folder / f"{self.name}.raw.parquet")
        except ImportError:
            pass
        summary = {
            "format": "heat3d-raw-summary",
            "version": 1,
            "game": self.game,
            "started": datetime.fromtimestamp(self.started).astimezone().isoformat(timespec="seconds"),
            "sidecar": out.name,
            "selfCheck": {"completeness": self.completeness()},
        }
        if out.suffix != ".parquet":
            summary["selfCheck"]["completeness"]["sidecars"] = [out.name]
        (self.folder / f"{self.name}.summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return out

    def __enter__(self) -> "RawLog":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def read_frames(path: str | Path):
    """A `.raw.bin`'s items as (head, payload), in order; a frame cut short by a crash ends it."""
    with Path(path).open("rb") as f:
        while True:
            frame = f.read(_FRAME.size)
            if len(frame) < _FRAME.size:
                return
            nh, nb = _FRAME.unpack(frame)
            h = f.read(nh)
            body = f.read(nb)
            if len(h) < nh or len(body) < nb:
                return
            try:
                head = json.loads(h)
            except ValueError:
                return
            yield head, body


def write_parquet(source: str | Path, target: str | Path, *, batch_bytes: int = 64 << 20) -> Path:
    """A `.raw.bin` as Parquet (zstd), a row group every `batch_bytes`; the `.raw.bin` is removed after."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    source, target = Path(source), Path(target)
    schema = pa.schema(
        [("time", pa.float64()), ("ms", pa.int64()), ("type", pa.dictionary(pa.int32(), pa.string())),
         ("used", pa.bool_()), ("payload", pa.binary()), ("text", pa.string())],
        metadata={b"heat3d": json.dumps({"version": 1, "kind": "heat3d-raw", "rule": RULE}).encode("utf-8")},
    )
    tmp = target.with_name(target.name + ".tmp")

    def table(cols: dict) -> "pa.Table":
        return pa.Table.from_arrays(
            [pa.array(cols["time"], pa.float64()), pa.array(cols["ms"], pa.int64()),
             pa.array(cols["type"], pa.string()).dictionary_encode().cast(schema.field("type").type),
             pa.array(cols["used"], pa.bool_()), pa.array(cols["payload"], pa.binary()),
             pa.array(cols["text"], pa.string())],
            schema=schema,
        )

    with pq.ParquetWriter(tmp, schema, compression="zstd") as writer:
        cols: dict[str, list] = {k: [] for k in schema.names}
        size = 0
        for head, body in read_frames(source):
            for k in ("time", "ms", "type", "used", "text"):
                cols[k].append(head.get(k))
            cols["payload"].append(body)
            size += len(body) + 64
            if size >= batch_bytes:
                writer.write_table(table(cols))
                cols = {k: [] for k in schema.names}
                size = 0
        if cols["time"]:
            writer.write_table(table(cols))
    tmp.replace(target)
    source.unlink(missing_ok=True)
    return target
