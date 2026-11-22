"""
Assetto Corsa, Assetto Corsa Competizione, AC EVO and AC Rally, recorded for
the Race tab: one `heat3d-session` file per session (its every lap, and for
ACC and AC EVO the other cars' positions), or with `--per-lap` one
`heat3d-lap` file per lap.

Kunos's games publish their telemetry for apps the documented way: named
shared-memory pages that the game writes and anyone may read. Nothing is
injected into the game and nothing it does not publish is read.

- `Local\\acpmf_physics`: AC, ACC and AC Rally. `Local\\acevo_pmf_physics`: AC EVO.
  The first 800 bytes are one layout in all four - pedals, speed, the car's
  accelerations and attitude, and per wheel the load, pressure, core and
  surface temperatures, suspension travel, camber, slip ratio and slip angle -
  and they include each tyre's contact point in world coordinates. The mean of
  the four is the car's position, from the physics page alone.
- `Local\\acpmf_graphics`: AC and ACC count laps here (`completedLaps`, the
  last lap's time), with the position along the lap, the sector, the pit flags
  and, in ACC, every car's position by its id. AC EVO's own graphics page
  (`Local\\acevo_pmf_graphics`) has the position along the lap (`npos`), the
  lap times, the pit and valid-lap flags and every car's position; its laps
  close where `npos` passes 1. AC Rally drives stages rather than laps, so
  there a lap is found from the positions instead: it closes when the car
  comes back past the point it started from, and a stage closes when the car
  stops at the end of it.

References: the AC1 shared memory SDK; the ACC shared memory documentation
(v1.8); AC EVO's physics layout as measured in `albertowd/live-telemetry-evo`
(docs/SHARED_MEMORY.md), its graphics and static pages from the published
SharedFileOut.h documentation (2026-04-28); AC Rally's as read by
`LuizZak/AssettoCorsaRallyTelemetryReader`.

Slip is the one channel whose meaning differs between games. Forza sends slip
normalised so that 1 is the edge of grip; Kunos sends the physical slip ratio
and slip angle. They are divided by a typical peak (0.12 for slip ratio, 0.14
rad - 8 degrees - for slip angle) so the viewer's "past 1 means sliding"
reading holds for both, approximately; the raw values are kept too.
"""

from __future__ import annotations

import json
import math
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .lapfile import RawLog, clean

WHEELS = ("FL", "FR", "RL", "RR")

#: Physics page, offsets shared by AC (1.7+), ACC, AC EVO and AC Rally.
PHYSICS_SIZE = 800
#: How much of it AC (the first game) is guaranteed to have.
PHYSICS_AC1_SIZE = 580

G = 9.80665
SLIP_RATIO_PEAK = 0.12
SLIP_ANGLE_PEAK = 0.14

# (offset, struct format, name)
_SCALARS = [
    (0, "i", "packetId"),
    (4, "f", "gas"),
    (8, "f", "brake"),
    (16, "i", "gear"),
    (20, "i", "rpms"),
    (24, "f", "steerAngle"),
    (28, "f", "speedKmh"),
    (208, "f", "heading"),
    (212, "f", "pitch"),
    (216, "f", "roll"),
    (200, "f", "drs"),
    (248, "i", "pitLimiterOn"),
    (276, "f", "turboBoost"),
    (364, "f", "clutch"),
]
# Only in the 800-byte page (ACC, AC EVO, AC Rally).
_SCALARS_FULL = [
    (564, "f", "brakeBias"),
    (672, "i", "tcInAction"),
    (676, "i", "absInAction"),
]
_VECTORS = [
    (32, 3, "velocity"),
    (44, 3, "accG"),
    (296, 3, "localAngularVel"),
]
#: The car's velocity in its own frame, from AC 1.12 on and in the others: the
#: drift angle is the angle between it and the car's nose.
LOCAL_VELOCITY = 568
#: ACC, AC Rally and AC EVO report the aids acting here, 0..1 (AC's own page
#: holds its settings in the same slots, so it is read only for those).
TC_ACTING = 204
ABS_ACTING = 252
# Per wheel, FL FR RL RR.
_WHEELS = [
    (56, "wheelSlip"),
    (72, "wheelLoad"),
    (88, "wheelsPressure"),
    (104, "wheelAngularSpeed"),
    (152, "tyreCoreTemperature"),
    (168, "camberRAD"),
    (184, "suspensionTravel"),
    (348, "brakeTemp"),
    (368, "tyreTempI"),
    (384, "tyreTempM"),
    (400, "tyreTempO"),
]
_WHEELS_FULL = [
    (640, "slipRatio"),
    (656, "slipAngle"),
    (740, "padLife"),
    (756, "discLife"),
]
TYRE_CONTACT_POINT = 420  # float[4][3], world XYZ

#: Graphics page of AC and ACC: the lap counter and the last lap's time.
GRAPHICS_SIZE = 256
G_COMPLETED_LAPS = 132
G_LAST_LAP_MS = 144
G_NORMALISED_POSITION = 248

MAPPINGS = {
    "ac": ("Local\\acpmf_physics", "Local\\acpmf_graphics", "Local\\acpmf_static"),
    "acc": ("Local\\acpmf_physics", "Local\\acpmf_graphics", "Local\\acpmf_static"),
    "acrally": ("Local\\acpmf_physics", None, "Local\\acpmf_static"),
    "acevo": ("Local\\acevo_pmf_physics", "Local\\acevo_pmf_graphics", "Local\\acevo_pmf_static"),
}
GAME_NAMES = {
    "ac": "assetto-corsa",
    "acc": "assetto-corsa-competizione",
    "acrally": "assetto-corsa-rally",
    "acevo": "assetto-corsa-evo",
}

#: The sizes each page is opened at, largest first: a game whose page is
#: smaller (an older build, or AC where ACC's longer page is tried) is opened
#: at the next size that fits. The fields a size does not reach are absent.
GRAPHICS_SIZES = {
    "ac": (300, 256),
    "acc": (1412, 1240, 256),
    # car_ids came in a 2026-04 build; before it the page ended at 3944.
    "acevo": (4904, 3944),
}
STATIC_SIZES = {"ac": (688, 256), "acc": (688, 256), "acrally": (256,), "acevo": (208,)}

#: AC and ACC graphics page, the part they share (`SPageFileGraphic`).
_G_SHARED = [
    (4, "i", "status"),
    (8, "i", "session"),
    (132, "i", "completedLaps"),
    (136, "i", "position"),
    (140, "i", "iCurrentTime"),
    (144, "i", "iLastTime"),
    (148, "i", "iBestTime"),
    (156, "f", "distanceTraveled"),
    (160, "i", "isInPit"),
    (164, "i", "currentSectorIndex"),
    (168, "i", "lastSectorTime"),
    (172, "i", "numberOfLaps"),
    (248, "f", "normalizedCarPosition"),
]
#: AC from here on: the player's car position, then flags.
_G_AC = [(276, "i", "isInPitLane")]
#: ACC from here on: every car on track, by its id (ACC shared memory v1.8).
ACC_ACTIVE_CARS = 252
ACC_CAR_COORDINATES = 256  # float[60][3]
ACC_CAR_ID = 976  # int[60]
ACC_PLAYER_CAR_ID = 1216
_G_ACC = [(1236, "i", "isInPitLane"), (1320, "i", "sessionIndex"), (1408, "i", "isValidLap")]
#: AC EVO's own graphics page (`SPageFileGraphicEvo`, Kunos's SharedFileOut.h
#: as of 2026-04-28; natural C alignment, the inner structs at their stated sizes).
_G_EVO = [
    (4, "i", "status"),
    (156, "i", "steerDegrees"),
    (188, "i", "iCurrentTime"),
    (1244, "f", "normalizedCarPosition"),
    (2384, "i", "completedLaps"),
    (2388, "I", "position"),
    (2396, "i", "iLastTime"),
    (2400, "i", "iBestTime"),
    (2476 + 72, "i", "currentLap"),  # session_state.current_lap
    (3119, "B", "isInPit"),
    (3120, "B", "isInPitLane"),
    (3121, "B", "isValidLap"),
]
EVO_PLAYER_ID = 24  # uint64 pair
EVO_CAR_MODEL = 3086  # char[33]
EVO_CAR_COORDINATES = 3124  # float[60][3]
EVO_ACTIVE_CARS = 3852
EVO_CAR_IDS = 3944  # uint64[60][2]

#: The session types AC and ACC number (EVO has its own and is written as a number).
SESSION_TYPES = {
    "ac": {0: "practice", 1: "qualify", 2: "race", 3: "hotlap", 4: "time-attack", 5: "drift", 6: "drag"},
    "acc": {0: "practice", 1: "qualify", 2: "race", 3: "hotlap", 4: "hotstint", 5: "superpole"},
}


def decode_graphics(page: bytes, game: str) -> dict:
    """
    The graphics page's lap, sector and pit fields, and for ACC and AC EVO every
    car's position (`cars`: id -> (x, y, z)) with the player's id. Fields past
    the page's size are left out.
    """
    out: dict = {}
    fields = _G_EVO if game == "acevo" else _G_SHARED + (_G_ACC if game == "acc" else _G_AC)
    for offset, fmt, name in fields:
        if offset + struct.calcsize(fmt) <= len(page):
            out[name] = struct.unpack_from("<" + fmt, page, offset)[0]
    cars: dict = {}
    if game == "acc" and len(page) >= ACC_PLAYER_CAR_ID + 4:
        active = max(0, min(60, struct.unpack_from("<i", page, ACC_ACTIVE_CARS)[0]))
        ids = struct.unpack_from("<60i", page, ACC_CAR_ID)
        xyz = struct.unpack_from("<180f", page, ACC_CAR_COORDINATES)
        for k in range(active):
            cars[ids[k]] = xyz[k * 3 : k * 3 + 3]
        out["playerCarId"] = struct.unpack_from("<i", page, ACC_PLAYER_CAR_ID)[0]
    elif game == "acevo" and len(page) >= EVO_ACTIVE_CARS + 1:
        active = min(60, page[EVO_ACTIVE_CARS])
        xyz = struct.unpack_from("<180f", page, EVO_CAR_COORDINATES)
        if len(page) >= EVO_CAR_IDS + 960:
            ids = [struct.unpack_from("<QQ", page, EVO_CAR_IDS + 16 * k) for k in range(60)]
            out["playerCarId"] = struct.unpack_from("<QQ", page, EVO_PLAYER_ID)
        else:
            ids = list(range(60))
        for k in range(active):
            cars[ids[k]] = xyz[k * 3 : k * 3 + 3]
        out["carModel"] = page[EVO_CAR_MODEL : EVO_CAR_MODEL + 33].split(b"\x00", 1)[0].decode("latin-1", "ignore")
    if cars:
        out["cars"] = cars
    return out


def graphics_channels(g: dict) -> dict:
    """The graphics fields written beside the physics ones, per sample."""
    out = {}
    for source, name in (
        ("normalizedCarPosition", "lapFraction"),
        ("currentSectorIndex", "sector"),
        ("isInPit", "inPit"),
        ("isInPitLane", "inPitLane"),
        ("isValidLap", "lapValid"),
        ("iCurrentTime", "lapTimeMs"),
        ("position", "racePosition"),
        ("steerDegrees", "steerDegrees"),
    ):
        if source in g:
            out[name] = g[source]
    return out


def decode_physics(page: bytes) -> dict:
    """One physics page to a flat dict of the raw fields, per wheel as `name.FL`."""
    out: dict = {}
    scalars = list(_SCALARS) + (list(_SCALARS_FULL) if len(page) >= PHYSICS_SIZE else [])
    for offset, fmt, name in scalars:
        out[name] = struct.unpack_from("<" + fmt, page, offset)[0]
    for offset, n, name in _VECTORS:
        out[name] = struct.unpack_from(f"<{n}f", page, offset)
    wheels = list(_WHEELS) + (list(_WHEELS_FULL) if len(page) >= PHYSICS_SIZE else [])
    for offset, name in wheels:
        values = struct.unpack_from("<4f", page, offset)
        for wheel, value in zip(WHEELS, values):
            out[f"{name}.{wheel}"] = value
    if len(page) >= TYRE_CONTACT_POINT + 48:
        points = struct.unpack_from("<12f", page, TYRE_CONTACT_POINT)
        out["contact"] = [points[i * 3 : i * 3 + 3] for i in range(4)]
    if len(page) >= LOCAL_VELOCITY + 12:
        out["localVelocity"] = struct.unpack_from("<3f", page, LOCAL_VELOCITY)
    out["tcActing"] = struct.unpack_from("<f", page, TC_ACTING)[0]
    out["absActing"] = struct.unpack_from("<f", page, ABS_ACTING)[0]
    return out


#: Temperatures AC Rally sends in kelvin where the others send Celsius.
KELVIN_FIELDS = ("tyreCoreTemperature", "tyreTempI", "tyreTempM", "tyreTempO", "brakeTemp")


def frame_from(raw: dict, clock: float, game: str = "ac") -> dict | None:
    """
    The raw fields as the viewer's canonical channels. None when the page holds
    no position - the game is in a menu, or the car is in the garage.
    """
    contact = raw.get("contact")
    if not contact:
        return None
    x = sum(p[0] for p in contact) / 4
    y = sum(p[1] for p in contact) / 4
    z = sum(p[2] for p in contact) / 4
    if x == 0 and y == 0 and z == 0:
        return None
    acc = raw["accG"]
    frame = {
        "time": clock,
        "x": x,
        "y": y,
        "z": z,
        "speed": raw["speedKmh"] / 3.6,
        "throttle": raw["gas"],
        "brake": raw["brake"],
        "clutch": raw["clutch"],
        "steerRaw": raw["steerAngle"],
        # 0 reverse, 1 neutral, 2 first: the viewer counts -1, 0, 1.
        "gear": raw["gear"] - 1,
        "rpm": raw["rpms"],
        "latAcc": acc[0] * G,
        "vertAcc": acc[1] * G,
        "longAcc": acc[2] * G,
        "yaw": raw["heading"],
        "pitch": raw["pitch"],
        "roll": raw["roll"],
        "yawRate": raw["localAngularVel"][1],
        "drs": raw["drs"],
        "pitLimiter": raw["pitLimiterOn"],
        "boost": raw["turboBoost"],
    }
    # Channels the first game's page does not have; named as the viewer's
    # channel table names them, so its input panel and car pick them up.
    for source, name in (("brakeBias", "brakeBias"), ("tcInAction", "tcActive"), ("absInAction", "absActive")):
        if source in raw:
            frame[name] = raw[source]
    if game in ("acc", "acrally", "acevo"):
        # The aids acting, as ACC documents these slots (its own flags are unused).
        frame["tcActive"] = 1.0 if raw.get("tcActing", 0.0) > 0.0 else 0.0
        frame["absActive"] = 1.0 if raw.get("absActing", 0.0) > 0.0 else 0.0
    # Everything else the page decode read, so a lap file holds all of it:
    # the page counter, the steering as sent, the world velocity, the pitch
    # and roll rates, the aids' raw slots, and per wheel the slip and contact point.
    frame["packetId"] = raw["packetId"]
    frame["steerAngle"] = raw["steerAngle"]
    for axis, value in zip("XYZ", raw["velocity"]):
        frame[f"worldVel{axis}"] = value
    frame["angVelX"], frame["angVelZ"] = raw["localAngularVel"][0], raw["localAngularVel"][2]
    frame["tcActing"] = raw.get("tcActing")
    frame["absActing"] = raw.get("absActing")
    for k, wheel in enumerate(WHEELS):
        if f"wheelSlip.{wheel}" in raw:
            frame[f"wheelSlip.{wheel}"] = raw[f"wheelSlip.{wheel}"]
        for axis, value in zip("XYZ", contact[k]):
            frame[f"contact{axis}.{wheel}"] = value
    local = raw.get("localVelocity")
    if local and any(local):
        # Car frame: x sideways, y up, z forwards. Which side x points to is
        # documented both ways; the viewer reads the drift angle's size.
        frame["latVel"] = local[0]
        frame["vertVel"] = local[1]
        frame["longVel"] = local[2]
    renames = {
        "tyreCoreTemperature": ("tireTemp", 1.0),
        "tyreTempI": ("tireTempInner", 1.0),
        "tyreTempM": ("tireTempMiddle", 1.0),
        "tyreTempO": ("tireTempOuter", 1.0),
        "wheelsPressure": ("tirePressure", 1.0),
        "wheelLoad": ("wheelLoad", 1.0),
        "wheelAngularSpeed": ("wheelSpeed", 1.0),
        "camberRAD": ("camber", 1.0),
        "suspensionTravel": ("suspensionM", 1.0),
        "brakeTemp": ("brakeTemp", 1.0),
        "slipRatio": ("slipRatio", 1.0 / SLIP_RATIO_PEAK),
        "slipAngle": ("slipAngle", 1.0 / SLIP_ANGLE_PEAK),
        "padLife": ("padLife", 1.0),
        "discLife": ("discLife", 1.0),
    }
    for source, (name, scale) in renames.items():
        for wheel in WHEELS:
            key = f"{source}.{wheel}"
            if key in raw:
                value = raw[key]
                if game == "acrally" and source in KELVIN_FIELDS and value > 200:
                    value -= 273.15
                frame[f"{name}.{wheel}"] = value * scale
                if source in ("slipRatio", "slipAngle"):
                    frame[f"{name}Raw.{wheel}"] = raw[key]
    return frame


@dataclass
class KLap:
    """One lap (or stage) of frames."""

    number: int
    frames: list[dict] = field(default_factory=list)
    seconds: float | None = None
    complete: bool = False
    #: The game's own verdict on the lap, where it gives one (ACC, AC EVO).
    valid: bool | None = None

    @property
    def metres(self) -> float:
        total = 0.0
        for a, b in zip(self.frames, self.frames[1:]):
            total += math.hypot(b["x"] - a["x"], b["y"] - a["y"], b["z"] - a["z"])
        return total


def document(lap: KLap, *, game: str, track: str | None, car: str | dict | None, info: dict | None = None) -> dict:
    """
    A lap as a `heat3d-lap` document, as `fulllap` writes Forza's. `info` is
    what the static page said of the session (`layout`, `trackLength`, the
    car's skin and limits, `session`), written beside the track and car.
    """
    frames = lap.frames
    t0 = frames[0]["time"]
    names = [k for k in frames[0] if k not in ("time", "steerRaw")]
    channels: dict[str, list] = {"time": [], "distance": [], "steer": []}
    for name in names:
        channels[name] = []
    # Steering: whatever the game's units, -1..1 by the most the lap used,
    # when that is beyond the -1..1 an input would already be in.
    most = max((abs(f["steerRaw"]) for f in frames if math.isfinite(f["steerRaw"])), default=1.0)
    steer_scale = 1.0 / most if most > 1.05 else 1.0
    travelled = 0.0
    previous = None
    for f in frames:
        if previous is not None:
            travelled += math.hypot(f["x"] - previous["x"], f["y"] - previous["y"], f["z"] - previous["z"])
        previous = f
        channels["time"].append(round(f["time"] - t0, 4))
        channels["distance"].append(round(travelled, 3))
        channels["steer"].append(clean(f["steerRaw"] * steer_scale, 4))
        for name in names:
            # None for a value that is not a finite number: NaN is not JSON.
            channels[name].append(clean(f.get(name)))
    # Suspension as 0..1 of the travel this lap used, for the car's bars.
    for wheel in WHEELS:
        travel = channels.get(f"suspensionM.{wheel}")
        finite = [v for v in travel or [] if v is not None]
        if finite:
            lo, hi = min(finite), max(finite)
            span = hi - lo if hi > lo else 1.0
            channels[f"suspension.{wheel}"] = [None if v is None else round((v - lo) / span, 4) for v in travel]
    seconds = lap.seconds if lap.seconds is not None else channels["time"][-1]
    info = info or {}
    car_doc = dict(car) if isinstance(car, dict) else ({"name": car} if car else {})
    for key in ("skin", "maxRpm", "maxFuel", "tyreRadius"):
        if info.get(key) not in (None, "", 0):
            car_doc.setdefault(key, info[key])
    doc = {
        "format": "heat3d-lap",
        "version": 1,
        "game": game,
        "track": track,
        "recordedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "car": car_doc,
        "lap": {"number": lap.number, "seconds": round(seconds, 4), "complete": lap.complete, "metres": round(lap.metres, 1)},
        # What the numbers mean where games differ: see lapfile.py.
        "meta": {"slip": "scaled", "discipline": "rally" if "rally" in game else "circuit"},
        "units": {
            "time": "s",
            "distance": "m",
            "speed": "m/s",
            "tireTemp": "degC",
            "tirePressure": "psi",
            "wheelLoad": "N",
            "suspensionM": "m",
            "suspension": "0..1 of the lap's travel",
            "slipRatio": f"normalised: raw / {SLIP_RATIO_PEAK}",
            "slipAngle": f"normalised: raw rad / {SLIP_ANGLE_PEAK}",
            "brakeTemp": "degC",
            "lapFraction": "0..1 of the lap, the game's own",
            "lapTimeMs": "ms",
        },
        "channels": channels,
    }
    # The track's layout and length, as the game names them: what a track
    # export is matched by (AC's layouts are folders of one track).
    for key in ("layout", "trackLength", "sectorCount", "session", "online"):
        if info.get(key) not in (None, ""):
            doc[key] = info[key]
    if lap.valid is False:
        doc["lap"]["valid"] = False
    return doc


class CounterSplitter:
    """Laps by the game's own counter (AC, ACC): the lap time is the game's."""

    def __init__(self, *, minimum_metres: float = 300.0):
        self.minimum = minimum_metres
        self.current: KLap | None = None

    def feed(self, frame: dict, laps: int, last_lap_ms: int) -> list[KLap]:
        done: list[KLap] = []
        if self.current is None:
            self.current = KLap(number=laps)
        elif laps != self.current.number:
            closing = self.current
            if laps == closing.number + 1:
                closing.complete = True
                if last_lap_ms > 0:
                    closing.seconds = last_lap_ms / 1000.0
            if closing.frames and closing.metres >= self.minimum:
                done.append(closing)
            self.current = KLap(number=laps)
        self.current.frames.append(frame)
        return done

    def flush(self) -> list[KLap]:
        lap, self.current = self.current, None
        return [lap] if lap and len(lap.frames) > 1 and lap.metres >= self.minimum else []


class LineSplitter:
    """
    Laps without a counter (AC EVO, AC Rally): the point the recording started
    at is the line. A lap closes where the car next passes closest to it,
    heading the same way, having gone at least `minimum_metres`; a stage (or
    any run) closes when the car stands still for `stop_seconds`.
    """

    def __init__(self, *, radius: float = 15.0, minimum_metres: float = 300.0, stop_seconds: float = 8.0):
        self.radius = radius
        self.minimum = minimum_metres
        self.stop = stop_seconds
        self.line: tuple[float, float] | None = None
        self.direction: tuple[float, float] | None = None
        self.current: KLap | None = None
        self.number = 0
        self._travelled = 0.0
        self._near: list[int] = []
        self._still_since: float | None = None

    def _dist(self, f: dict) -> float:
        return math.hypot(f["x"] - self.line[0], f["z"] - self.line[1])

    def feed(self, frame: dict) -> list[KLap]:
        done: list[KLap] = []
        if self.current is None:
            self.current = KLap(number=self.number)
            self._travelled = 0.0
            self._near = []
        cur = self.current
        if cur.frames:
            prev = cur.frames[-1]
            self._travelled += math.hypot(frame["x"] - prev["x"], frame["z"] - prev["z"])
        cur.frames.append(frame)
        if self.line is None:
            self.line = (frame["x"], frame["z"])
        if self.direction is None and self._travelled > 5:
            dx, dz = frame["x"] - self.line[0], frame["z"] - self.line[1]
            n = math.hypot(dx, dz) or 1.0
            self.direction = (dx / n, dz / n)

        # Standing still at the end of a run.
        if frame["speed"] < 1.0:
            self._still_since = self._still_since if self._still_since is not None else frame["time"]
            if frame["time"] - self._still_since >= self.stop:
                done += self.flush()
                return done
        else:
            self._still_since = None

        # Back past the line: the closest sample within the radius closes the lap.
        if self.direction is not None and self._travelled > self.minimum:
            if self._dist(frame) < self.radius:
                self._near.append(len(cur.frames) - 1)
            elif self._near:
                best = min(self._near, key=lambda i: self._dist(cur.frames[i]))
                f = cur.frames
                j = min(len(f) - 1, best + 1)
                heading = (f[j]["x"] - f[best]["x"], f[j]["z"] - f[best]["z"])
                same_way = heading[0] * self.direction[0] + heading[1] * self.direction[1] > 0
                self._near = []
                if same_way:
                    # The line is wherever the recording began, so every lap
                    # runs line to line - but one begun from standstill is a
                    # launch, not a lap to compare.
                    closing = KLap(number=cur.number, frames=f[: best + 1], complete=f[0]["speed"] > 5.0)
                    closing.seconds = f[best]["time"] - f[0]["time"]
                    if closing.metres >= self.minimum:
                        done.append(closing)
                    self.number += 1
                    rest = f[best:]
                    self.current = KLap(number=self.number, frames=rest)
                    self._travelled = KLap(0, rest).metres
        return done

    def flush(self) -> list[KLap]:
        lap, self.current = self.current, None
        self.number += 1
        if lap is None or len(lap.frames) < 2 or lap.metres < self.minimum:
            return []
        return [lap]


class PositionSplitter:
    """
    Laps by the game's own position along the lap (AC EVO: `npos`, 0..1): a
    lap closes when it falls from near 1 to near 0, which is where the game's
    line is. The lap time is the game's when its last-lap time changes within
    a few seconds of the line; until then it is the samples' span.
    """

    def __init__(self, *, minimum_metres: float = 300.0, settle_seconds: float = 3.0):
        self.minimum = minimum_metres
        self.settle = settle_seconds
        self.current: KLap | None = None
        self.number = 0
        self._last_fraction: float | None = None
        self._last_lap_ms: int | None = None
        #: The lap just closed, waiting for the game's time for it.
        self.closed: KLap | None = None
        self._closed_at = 0.0

    def feed(self, frame: dict, fraction: float, last_lap_ms: int, valid: bool | None = None) -> list[KLap]:
        done: list[KLap] = []
        if self.current is None:
            self.current = KLap(number=self.number)
        cur = self.current
        if self._last_lap_ms is None:
            self._last_lap_ms = last_lap_ms
        if self.closed is not None:
            if last_lap_ms != self._last_lap_ms and last_lap_ms > 0:
                self.closed.seconds = last_lap_ms / 1000.0
                self.closed = None
            elif frame["time"] - self._closed_at > self.settle:
                self.closed = None
        self._last_lap_ms = last_lap_ms
        crossed = self._last_fraction is not None and self._last_fraction > 0.9 and fraction < 0.1
        self._last_fraction = fraction
        if crossed and cur.frames:
            # A lap begun at the line, not part-way round where recording started.
            first = cur.frames[0].get("lapFraction")
            cur.complete = first is not None and first < 0.05
            if cur.metres >= self.minimum:
                done.append(cur)
                self.closed = cur
                self._closed_at = frame["time"]
            self.number += 1
            self.current = cur = KLap(number=self.number)
        if valid is False:
            cur.valid = False
        elif valid is True and cur.valid is None:
            cur.valid = True
        cur.frames.append(frame)
        return done

    def flush(self) -> list[KLap]:
        lap, self.current = self.current, None
        self.number += 1
        return [lap] if lap and len(lap.frames) > 1 and lap.metres >= self.minimum else []


def _wide(page: bytes, offset: int, chars: int) -> str:
    raw = page[offset : offset + chars * 2]
    return raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0].strip()


def _narrow(page: bytes, offset: int, chars: int) -> str:
    return page[offset : offset + chars].split(b"\x00", 1)[0].decode("latin-1", errors="ignore").strip()


def static_info(page: bytes, game: str) -> dict:
    """
    What the static page says of the session: `track`, `layout` (AC's track
    configuration), `car`, and where the page is long enough the track's length,
    its sector count, the car's skin and limits, and whether the session is
    online. The player's name is on the page too and is not read.
    """

    def num(fmt: str, offset: int):
        if offset + struct.calcsize(fmt) > len(page):
            return None
        return struct.unpack_from("<" + fmt, page, offset)[0]

    info: dict = {}
    try:
        if game == "acevo":
            info["track"] = _narrow(page, 136, 33) or None
            info["layout"] = _narrow(page, 169, 33) or None
            length = num("f", 204)
            if length and math.isfinite(length) and length > 0:
                info["trackLength"] = round(length, 1)
            session = num("i", 32)
            if session is not None:
                info["session"] = session
            online = page[86] if len(page) > 86 else None
            if online is not None:
                info["online"] = bool(online)
            return info
        info["car"] = _wide(page, 68, 33) or None
        info["track"] = _wide(page, 134, 33) or None
        if game == "acrally" or len(page) < 600:
            return info
        sectors = num("i", 400)
        if sectors and 0 < sectors < 100:
            info["sectorCount"] = sectors
        rpm = num("i", 412)
        if rpm and 0 < rpm < 30000:
            info["maxRpm"] = rpm
        fuel = num("f", 416)
        if fuel and math.isfinite(fuel) and 0 < fuel < 1000:
            info["maxFuel"] = round(fuel, 2)
        radius = struct.unpack_from("<4f", page, 436)
        if all(math.isfinite(r) and 0.1 < r < 1.0 for r in radius):
            info["tyreRadius"] = [round(r, 4) for r in radius]
        length = num("f", 520)
        if length and math.isfinite(length) and length > 0:
            info["trackLength"] = round(length, 1)
        info["layout"] = _wide(page, 524, 33) or None
        if len(page) >= 688:
            info["skin"] = _wide(page, 604, 33) or None
            info["online"] = bool(num("i", 684))
    except (struct.error, ValueError):
        pass
    return info


def read_static(page: bytes, game: str) -> tuple[str | None, str | None]:
    """Track and car from the static page, where the layout is known."""
    info = static_info(page, game)
    track = info.get("track")
    if game == "acevo" and info.get("layout"):
        track = f"{track or ''} {info['layout']}".strip()
    return (track or None, info.get("car"))


def lap_filename(lap: KLap, game: str) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    seconds = lap.seconds if lap.seconds is not None else lap.frames[-1]["time"] - lap.frames[0]["time"]
    kind = "lap" if lap.complete else "run"
    return f"{stamp}_{game}_{kind}{lap.number}_{seconds:.3f}s.lap.json"


def write(lap: KLap, folder: Path, *, game: str, track: str | None, car: str | dict | None, info: dict | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / lap_filename(lap, game)
    doc = document(lap, game=GAME_NAMES[game], track=track, car=car, info=info)
    path.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    return path


class OtherCars:
    """
    The other cars' positions, from the graphics page's table of every car (ACC,
    AC EVO), a few times a second. The table is believed only once the
    player's own entry is seen where the physics page puts the player's car.
    """

    def __init__(self, hz: float = 10.0, tolerance_m: float = 8.0):
        self.period = 1.0 / hz
        self.tolerance = tolerance_m
        self.tracks: dict = {}
        self._next = 0.0
        self.agree = 0
        self.disagree = 0

    def feed(self, clock: float, g: dict, own: tuple[float, float, float]) -> None:
        cars = g.get("cars")
        if not cars or clock < self._next:
            return
        self._next = clock + self.period
        player = g.get("playerCarId")
        if player in cars:
            mine = cars[player]
        else:
            # No id to go by: the nearest entry is the player's.
            mine = min(cars.values(), key=lambda p: math.dist(p, own))
            player = next(k for k, v in cars.items() if v is mine)
        if math.dist(mine, own) <= self.tolerance:
            self.agree += 1
        else:
            self.disagree += 1
        for key, (x, y, z) in cars.items():
            if key == player or (x == 0 and y == 0 and z == 0):
                continue
            t = self.tracks.setdefault(key, {"time": [], "x": [], "y": [], "z": []})
            t["time"].append(round(clock, 3))
            t["x"].append(round(x, 3))
            t["y"].append(round(y, 3))
            t["z"].append(round(z, 3))

    def trusted(self) -> bool:
        return self.agree >= 5 and self.agree >= 4 * self.disagree

    def documents(self, t0: float) -> list[dict]:
        if not self.trusted():
            return []
        out = []
        for key, t in self.tracks.items():
            if len(t["time"]) < 2:
                continue
            ident = "-".join(f"{part:x}" for part in key) if isinstance(key, tuple) else str(key)
            out.append({"id": ident, "channels": dict(t, time=[round(v - t0, 3) for v in t["time"]])})
        return out


class Session:
    """
    One session (practice, qualifying, a race; one track, layout and car) as
    one `heat3d-session` file: every lap, the runs between them, and for ACC
    and AC EVO the other cars' positions. Rewritten after every lap, so a
    session cut short keeps what was driven.
    """

    def __init__(self, folder: Path, *, game: str, info: dict, started: float):
        self.folder = folder
        self.game = game
        self.info = dict(info)
        self.started = started
        self.laps: list[KLap] = []
        self.others = OtherCars()
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = folder / f"{stamp}_{game}_session.json"

    def add(self, lap: KLap) -> None:
        self.laps.append(lap)

    def document(self) -> dict:
        info = self.info
        laps = [document(lap, game=GAME_NAMES[self.game], track=info.get("track"), car=info.get("car"), info=info) for lap in self.laps]
        doc = {
            "format": "heat3d-session",
            "version": 1,
            "game": GAME_NAMES[self.game],
            "track": info.get("track"),
            "layout": info.get("layout"),
            "car": {"name": info["car"]} if info.get("car") else {},
            "recordedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "session": info.get("session"),
            "laps": laps,
        }
        names = SESSION_TYPES.get(self.game, {})
        if isinstance(info.get("session"), int) and info["session"] in names:
            doc["sessionType"] = names[info["session"]]
        others = self.others.documents(self.laps[0].frames[0]["time"] if self.laps else self.started)
        if others:
            doc["others"] = others
        return doc

    def write(self) -> Path | None:
        if not self.laps:
            return None
        self.folder.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.document(), separators=(",", ":")), encoding="utf-8")
        tmp.replace(self.path)
        return self.path


def session_key(info: dict, g: dict) -> tuple:
    """What changes when a new session begins: the track, layout, car, the session's type and index."""
    return (info.get("track"), info.get("layout"), info.get("car"), g.get("session"), g.get("sessionIndex"))


def _open(name: str, size: int):
    """A read-only view of a named mapping the game created. Windows only."""
    import mmap

    return mmap.mmap(-1, size, tagname=name, access=mmap.ACCESS_READ)


def _open_sized(name: str, sizes: tuple[int, ...]):
    """The mapping at the largest of `sizes` it has; (view, size)."""
    error: OSError | None = None
    for size in sizes:
        try:
            return _open(name, size), size
        except OSError as e:
            error = e
    raise error or OSError(name)


def _splitter(game: str, graphics_size: int):
    if game == "acevo":
        # The position along the lap is in every EVO page this reads.
        return PositionSplitter() if graphics_size >= 2404 else LineSplitter()
    if game in ("ac", "acc"):
        return CounterSplitter()
    return LineSplitter()


def run(out: str | Path, *, game: str, hz: float = 200.0, per_lap: bool = False) -> list[Path]:
    """
    Record until Ctrl+C; returns the files written. One `heat3d-session` file
    per session, or with `per_lap` one `heat3d-lap` file per lap as before.
    """
    if sys.platform != "win32":
        raise SystemExit("The Assetto Corsa games publish their telemetry as Windows shared memory: record on the PC the game runs on.")
    if game not in MAPPINGS:
        raise SystemExit(f"unknown game {game!r}; one of {', '.join(MAPPINGS)}")
    physics_name, graphics_name, static_name = MAPPINGS[game]
    out = Path(out)
    physics, size = _open_sized(physics_name, (PHYSICS_SIZE, PHYSICS_AC1_SIZE))
    graphics, graphics_size = _open_sized(graphics_name, GRAPHICS_SIZES[game]) if graphics_name else (None, 0)
    static, static_size = _open_sized(static_name, STATIC_SIZES[game])
    splitter = _splitter(game, graphics_size)
    written: list[Path] = []
    last_packet = None
    info: dict = {}
    session: Session | None = None
    key = None
    start = time.perf_counter()
    period = 1.0 / hz
    # Every page as mapped, kept whole each time it changes (3DHeat's converter rule).
    raw = RawLog(out, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{game}", game=GAME_NAMES[game])
    kept: dict[str, bytes] = {}

    def keep(kind: str, data: bytes, used: bool = False) -> None:
        if kept.get(kind) != data:
            kept[kind] = data
            raw.keep(kind, data, used=used)

    def close_session() -> None:
        nonlocal session
        if session is not None:
            path = session.write()
            if path is not None and path not in written:
                written.append(path)
            session = None

    def finished(laps: list[KLap]) -> None:
        for lap in laps:
            first = lap.frames[0].get("lapFraction") if lap.frames else None
            if lap.complete and first is not None and 0.05 < first < 0.95:
                # Joined part-way round: the game's lap time is not this run's.
                lap.complete = False
            if per_lap:
                written.append(write(lap, out, game=game, track=info.get("track"), car=info.get("car"), info=info))
                print(f"  {written[-1].name}")
            elif session is not None:
                session.add(lap)
                session.write()
                kind = "lap" if lap.complete else "run"
                seconds = lap.seconds if lap.seconds is not None else lap.frames[-1]["time"] - lap.frames[0]["time"]
                print(f"  {kind} {lap.number}: {seconds:.3f} s -> {session.path.name}")

    try:
        while True:
            page = bytes(physics[:size])
            packet = struct.unpack_from("<i", page, 0)[0]
            g_page = bytes(graphics[:graphics_size]) if graphics is not None else b""
            if graphics is not None:
                keep(graphics_name.split("\\")[-1], g_page)
            s_page = bytes(static[:static_size])
            keep(static_name.split("\\")[-1], s_page)
            if packet != last_packet and packet != 0:
                last_packet = packet
                clock = time.perf_counter() - start
                frame = frame_from(decode_physics(page), clock, game)
                keep(physics_name.split("\\")[-1], page, frame is not None)
                if frame is not None:
                    g = decode_graphics(g_page, game) if g_page else {}
                    now_info = static_info(s_page, game)
                    if game == "acevo" and g.get("carModel"):
                        now_info["car"] = g["carModel"]
                    now_key = session_key(now_info, g)
                    if key is not None and now_key != key:
                        # Another session: what was driven so far is the last one's.
                        finished(splitter.flush())
                        close_session()
                        splitter = _splitter(game, graphics_size)
                    if key != now_key:
                        key, info = now_key, now_info
                        if not per_lap:
                            session = Session(out, game=game, info=info, started=clock)
                    frame.update(graphics_channels(g))
                    if session is not None:
                        session.others.feed(clock, g, (frame["x"], frame["y"], frame["z"]))
                    if isinstance(splitter, CounterSplitter):
                        if g_page:
                            done = splitter.feed(frame, g.get("completedLaps", 0), g.get("iLastTime", 0))
                        else:
                            done = splitter.feed(frame, 0, 0)
                        valid = g.get("isValidLap")
                        if valid is not None and splitter.current is not None and not valid:
                            splitter.current.valid = False
                    elif isinstance(splitter, PositionSplitter):
                        valid = g.get("isValidLap")
                        waiting = splitter.closed is not None
                        done = splitter.feed(frame, g.get("normalizedCarPosition", 0.0), g.get("iLastTime", 0), None if valid is None else bool(valid))
                        if waiting and splitter.closed is None and session is not None and session.laps:
                            # The game's lap time came a little after the line.
                            session.write()
                    else:
                        done = splitter.feed(frame)
                    finished(done)
            time.sleep(period)
    except KeyboardInterrupt:
        pass
    finished(splitter.flush())
    close_session()
    raw.close()
    return written
