"""The Assetto Corsa family recorder, on synthetic shared-memory pages."""

import json
import math
import struct

from heat3d_capture.telemetry import kunos


def physics_page(*, x=10.0, y=2.0, z=-5.0, speed_kmh=108.0, gas=1.0, brake=0.0, gear=4, steer=0.1, packet=7, full=True):
    page = bytearray(kunos.PHYSICS_SIZE if full else kunos.PHYSICS_AC1_SIZE)
    struct.pack_into("<i", page, 0, packet)
    struct.pack_into("<f", page, 4, gas)
    struct.pack_into("<f", page, 8, brake)
    struct.pack_into("<i", page, 16, gear)
    struct.pack_into("<i", page, 20, 6500)
    struct.pack_into("<f", page, 24, steer)
    struct.pack_into("<f", page, 28, speed_kmh)
    struct.pack_into("<3f", page, 44, 1.5, 0.1, -0.5)
    struct.pack_into("<4f", page, 152, 85, 86, 90, 91)  # core temperature
    struct.pack_into("<4f", page, 184, 0.02, 0.03, 0.04, 0.05)  # suspension travel
    struct.pack_into("<4f", page, 348, 400, 410, 300, 310)  # brake temperature
    struct.pack_into("<f", page, 364, 0.0)
    for i, (dx, dz) in enumerate([(1, 1.4), (-1, 1.4), (1, -1.4), (-1, -1.4)]):
        struct.pack_into("<3f", page, kunos.TYRE_CONTACT_POINT + i * 12, x + dx, y - 0.3, z + dz)
    if full:
        struct.pack_into("<4f", page, 640, -0.06, -0.06, 0.12, 0.24)  # slip ratio
        struct.pack_into("<f", page, 564, 0.57)  # brake bias
        struct.pack_into("<i", page, 676, 1)  # ABS acting
        struct.pack_into("<4f", page, 740, 0.9, 0.9, 0.95, 0.95)  # pad life
    return bytes(page)


def test_decodes_the_shared_layout():
    raw = kunos.decode_physics(physics_page())
    frame = kunos.frame_from(raw, 1.5)
    assert frame["x"] == 10.0 and frame["z"] == -5.0
    assert abs(frame["y"] - 1.7) < 1e-6
    assert abs(frame["speed"] - 30.0) < 1e-5
    assert frame["gear"] == 3
    assert abs(frame["latAcc"] - 1.5 * kunos.G) < 1e-4
    assert frame["tireTemp.RR"] == 91
    assert frame["brakeTemp.FL"] == 400
    # Slip ratio normalised: 0.12 is the edge of grip, and so reads 1.
    assert abs(frame["slipRatio.RL"] - 1.0) < 1e-5
    assert abs(frame["slipRatioRaw.RR"] - 0.24) < 1e-6
    # The aids and settings, under the viewer's names.
    assert abs(frame["brakeBias"] - 0.57) < 1e-6
    assert frame["absActive"] == 1 and frame["tcActive"] == 0
    assert abs(frame["padLife.RL"] - 0.95) < 1e-6


def test_first_game_page_has_no_slip():
    frame = kunos.frame_from(kunos.decode_physics(physics_page(full=False)), 0.0)
    assert "slipRatio.FL" not in frame
    assert "brakeBias" not in frame and "absActive" not in frame
    assert frame["tireTemp.FL"] == 85


def test_no_position_no_frame():
    page = bytearray(kunos.PHYSICS_SIZE)
    assert kunos.frame_from(kunos.decode_physics(bytes(page)), 0.0) is None


def circle_frames(laps=2.5, radius=100.0, speed=30.0, hz=50):
    circumference = 2 * math.pi * radius
    n = int(laps * circumference / speed * hz)
    for i in range(n):
        t = i / hz
        a = (speed * t) / radius
        page = physics_page(x=radius * math.sin(a), z=radius * (1 - math.cos(a)), speed_kmh=speed * 3.6, packet=i + 1)
        yield kunos.frame_from(kunos.decode_physics(page), t)


def test_laps_by_the_line_when_there_is_no_counter():
    splitter = kunos.LineSplitter()
    laps = []
    for frame in circle_frames():
        laps += splitter.feed(frame)
    laps += splitter.flush()
    # Two whole laps from the starting point, and the half lap after them.
    complete = [lap for lap in laps if lap.complete]
    assert len(laps) == 3
    assert len(complete) == 2
    period = 2 * math.pi * 100 / 30
    assert abs(laps[0].seconds - period) < 0.1
    assert abs(complete[0].seconds - period) < 0.1


def test_laps_by_the_game_counter():
    splitter = kunos.CounterSplitter()
    laps = []
    for i, frame in enumerate(circle_frames(laps=2.2)):
        lap_number = int(frame["time"] / (2 * math.pi * 100 / 30))
        laps += splitter.feed(frame, lap_number, 20944 if lap_number else 0)
    assert len(laps) == 2
    assert laps[1].complete and laps[1].seconds == 20.944


def test_writes_a_heat3d_lap(tmp_path):
    lap = kunos.KLap(number=1, frames=list(circle_frames(laps=1.0)), complete=True)
    path = kunos.write(lap, tmp_path, game="acc", track="Monza", car="Ferrari 296 GT3")
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["format"] == "heat3d-lap"
    assert doc["game"] == "assetto-corsa-competizione"
    assert doc["track"] == "Monza" and doc["car"]["name"] == "Ferrari 296 GT3"
    ch = doc["channels"]
    assert ch["time"][0] == 0 and ch["distance"][-1] > 600
    assert set(ch["suspension.FL"]) == {0.0} or max(ch["suspension.FL"]) <= 1.0
    assert "steerRaw" not in ch and ch["steer"][0] == 0.1


def test_reads_the_static_page():
    page = bytearray(256)
    page[68 : 68 + 2 * 12] = "porsche_992\x00".encode("utf-16-le")
    page[134 : 134 + 2 * 6] = "monza\x00".encode("utf-16-le")
    assert kunos.read_static(bytes(page), "acc") == ("monza", "porsche_992")
    evo = bytearray(256)
    evo[136:141] = b"Imola"
    assert kunos.read_static(bytes(evo), "acevo")[0] == "Imola"


def test_drift_angle_aids_and_kelvin_by_game():
    page = bytearray(physics_page())
    # The car's own velocity: 3 m/s sideways at 30 forwards.
    struct.pack_into("<3f", page, kunos.LOCAL_VELOCITY, 3.0, 0.0, 30.0)
    struct.pack_into("<f", page, kunos.TC_ACTING, 0.4)
    # AC Rally sends temperatures in kelvin.
    struct.pack_into("<4f", page, 348, 673.15, 683.15, 573.15, 583.15)
    raw = kunos.decode_physics(bytes(page))
    rally = kunos.frame_from(raw, 1.0, "acrally")
    assert abs(rally["latVel"] - 3.0) < 1e-6 and abs(rally["longVel"] - 30.0) < 1e-6
    assert abs(rally["brakeTemp.FL"] - 400.0) < 1e-3
    # ACC reports the aids acting in those slots; AC keeps its settings there.
    assert kunos.frame_from(raw, 1.0, "acc")["tcActive"] == 1.0
    assert kunos.frame_from(raw, 1.0, "ac")["tcActive"] == 0
    # Celsius elsewhere stays as it is.
    assert abs(kunos.frame_from(raw, 1.0, "acc")["brakeTemp.FL"] - 673.15) < 1e-3


def test_the_lap_says_what_its_slip_means(tmp_path):
    lap = kunos.KLap(number=1, frames=list(circle_frames(laps=1.0)), complete=True)
    doc = json.loads(kunos.write(lap, tmp_path, game="acrally", track=None, car=None).read_text(encoding="utf-8"))
    assert doc["meta"] == {"slip": "scaled", "discipline": "rally"}


def test_a_value_that_is_not_a_number_is_written_as_null(tmp_path):
    """NaN and Infinity are not JSON: the browser's JSON.parse refuses the whole file."""
    frames = list(circle_frames(laps=1.0))
    frames[3] = dict(frames[3], rpm=float("nan"), **{"suspensionM.FL": float("inf")})
    lap = kunos.KLap(number=1, frames=frames, complete=True)
    text = kunos.write(lap, tmp_path, game="acc", track=None, car=None).read_text(encoding="utf-8")
    doc = json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert doc["channels"]["rpm"][3] is None
    assert doc["channels"]["suspensionM.FL"][3] is None and doc["channels"]["suspension.FL"][3] is None
    assert all(v is not None for i, v in enumerate(doc["channels"]["suspension.FL"]) if i != 3)


def test_a_lap_file_holds_everything_the_page_decode_read():
    import struct as _struct

    import pytest

    page = bytearray(kunos.PHYSICS_SIZE)
    _struct.pack_into("<i", page, 0, 77)
    _struct.pack_into("<f", page, 24, 0.25)
    _struct.pack_into("<3f", page, 32, 1.0, 2.0, 3.0)
    _struct.pack_into("<3f", page, 296, 0.1, 0.2, 0.3)
    _struct.pack_into("<4f", page, 56, 0.5, 0.6, 0.7, 0.8)
    for w in range(4):
        _struct.pack_into("<3f", page, kunos.TYRE_CONTACT_POINT + 12 * w, 10.0 + w, 1.0, 20.0)
    frame = kunos.frame_from(kunos.decode_physics(bytes(page)), 0.0, "acc")
    assert frame["packetId"] == 77 and frame["steerAngle"] == 0.25
    assert (frame["worldVelX"], frame["worldVelY"], frame["worldVelZ"]) == (1.0, 2.0, 3.0)
    assert frame["angVelX"] == pytest.approx(0.1) and frame["angVelZ"] == pytest.approx(0.3)
    assert frame["wheelSlip.RR"] == pytest.approx(0.8) and frame["contactX.RR"] == 13.0


def acc_graphics(*, laps=0, last_ms=0, fraction=0.0, cars=None, player=0, valid=1, session=2, size=1412):
    page = bytearray(size)
    struct.pack_into("<i", page, 4, 2)
    struct.pack_into("<i", page, 8, session)
    struct.pack_into("<i", page, kunos.G_COMPLETED_LAPS, laps)
    struct.pack_into("<i", page, kunos.G_LAST_LAP_MS, last_ms)
    struct.pack_into("<i", page, 164, 1)
    struct.pack_into("<f", page, kunos.G_NORMALISED_POSITION, fraction)
    if size >= kunos.ACC_PLAYER_CAR_ID + 4:
        cars = cars or {}
        struct.pack_into("<i", page, kunos.ACC_ACTIVE_CARS, len(cars))
        for k, (ident, xyz) in enumerate(cars.items()):
            struct.pack_into("<3f", page, kunos.ACC_CAR_COORDINATES + 12 * k, *xyz)
            struct.pack_into("<i", page, kunos.ACC_CAR_ID + 4 * k, ident)
        struct.pack_into("<i", page, kunos.ACC_PLAYER_CAR_ID, player)
        struct.pack_into("<i", page, 1408, valid)
    return bytes(page)


def test_acc_graphics_every_car_and_the_lap_fields():
    g = kunos.decode_graphics(acc_graphics(laps=3, last_ms=101500, fraction=0.25, cars={7: (1.0, 2.0, 3.0), 9: (4.0, 5.0, 6.0)}, player=9), "acc")
    assert g["completedLaps"] == 3 and g["iLastTime"] == 101500 and g["currentSectorIndex"] == 1
    assert abs(g["normalizedCarPosition"] - 0.25) < 1e-6 and g["isValidLap"] == 1
    assert g["playerCarId"] == 9 and g["cars"][7] == (1.0, 2.0, 3.0)
    ch = kunos.graphics_channels(g)
    assert ch["sector"] == 1 and ch["lapValid"] == 1 and abs(ch["lapFraction"] - 0.25) < 1e-6
    # AC's shorter page: the shared fields, no table of cars.
    ac = kunos.decode_graphics(acc_graphics(laps=2, size=300), "ac")
    assert ac["completedLaps"] == 2 and "cars" not in ac and "isInPitLane" in ac


def evo_graphics(*, fraction=0.0, last_ms=0, valid=1, cars=(), size=4904):
    page = bytearray(size)
    struct.pack_into("<i", page, 4, 2)
    struct.pack_into("<f", page, 1244, fraction)
    struct.pack_into("<i", page, 2396, last_ms)
    page[3121] = valid
    page[kunos.EVO_ACTIVE_CARS] = len(cars)
    struct.pack_into("<QQ", page, kunos.EVO_PLAYER_ID, 1, 2)
    for k, xyz in enumerate(cars):
        struct.pack_into("<3f", page, kunos.EVO_CAR_COORDINATES + 12 * k, *xyz)
        if size >= kunos.EVO_CAR_IDS + 960:
            struct.pack_into("<QQ", page, kunos.EVO_CAR_IDS + 16 * k, k + 1, k + 2)
    page[kunos.EVO_CAR_MODEL : kunos.EVO_CAR_MODEL + 9] = b"bmw_m4_gt"
    return bytes(page)


def test_evo_graphics_by_kunos_layout():
    g = kunos.decode_graphics(evo_graphics(fraction=0.5, last_ms=95000, cars=[(1.0, 0.0, 1.0), (50.0, 0.0, 9.0)]), "acevo")
    assert abs(g["normalizedCarPosition"] - 0.5) < 1e-6 and g["iLastTime"] == 95000 and g["isValidLap"] == 1
    assert g["playerCarId"] == (1, 2) and g["cars"][(2, 3)] == (50.0, 0.0, 9.0)
    assert g["carModel"] == "bmw_m4_gt"
    # A build before car_ids: the table by index, nothing to name the player by.
    old = kunos.decode_graphics(evo_graphics(cars=[(1.0, 0.0, 1.0)], size=3944), "acevo")
    assert old["cars"] == {0: (1.0, 0.0, 1.0)} and "playerCarId" not in old


def test_static_page_layout_length_and_skin():
    page = bytearray(688)
    page[68 : 68 + 2 * 12] = "porsche_992\x00".encode("utf-16-le")
    page[134 : 134 + 2 * 6] = "monza\x00".encode("utf-16-le")
    struct.pack_into("<i", page, 400, 3)
    struct.pack_into("<i", page, 412, 9000)
    struct.pack_into("<f", page, 520, 5793.0)
    page[524 : 524 + 2 * 3] = "gp\x00".encode("utf-16-le")
    page[604 : 604 + 2 * 5] = "red1\x00".encode("utf-16-le")
    struct.pack_into("<i", page, 684, 1)
    info = kunos.static_info(bytes(page), "acc")
    assert info["track"] == "monza" and info["layout"] == "gp" and info["car"] == "porsche_992"
    assert info["trackLength"] == 5793.0 and info["sectorCount"] == 3 and info["maxRpm"] == 9000
    assert info["skin"] == "red1" and info["online"] is True
    evo = bytearray(208)
    evo[136:141] = b"imola"
    evo[169:171] = b"gp"
    struct.pack_into("<f", evo, 204, 4909.0)
    e = kunos.static_info(bytes(evo), "acevo")
    assert e["track"] == "imola" and e["layout"] == "gp" and e["trackLength"] == 4909.0


def test_evo_laps_close_where_the_lap_position_passes_one():
    splitter = kunos.PositionSplitter()
    laps = []
    period = 2 * math.pi * 100 / 30
    for frame in circle_frames(laps=2.5):
        fraction = (frame["time"] / period) % 1.0
        frame["lapFraction"] = fraction
        lap_index = int(frame["time"] / period)
        last_ms = int(period * 1000) if lap_index >= 1 and frame["time"] - lap_index * period > 0.5 else 0
        laps += splitter.feed(frame, fraction, last_ms, True)
    laps += splitter.flush()
    complete = [lap for lap in laps if lap.complete]
    assert len(complete) == 2 and complete[0].valid is True
    # The game's time, taken when it changed just after the line.
    assert complete[0].seconds == int(period * 1000) / 1000


def test_a_session_file_holds_every_lap_and_the_other_cars(tmp_path):
    info = {"track": "monza", "layout": "", "car": "honda_nsx_gt3_evo", "session": 2}
    session = kunos.Session(tmp_path, game="acc", info=info, started=0.0)
    frames = list(circle_frames(laps=1.0))
    for f in frames:
        g = {"cars": {1: (f["x"], f["y"], f["z"]), 2: (f["x"] + 30, f["y"], f["z"])}, "playerCarId": 1}
        session.others.feed(f["time"], g, (f["x"], f["y"], f["z"]))
    session.add(kunos.KLap(number=0, frames=frames[: len(frames) // 2]))
    session.add(kunos.KLap(number=1, frames=frames[len(frames) // 2 :], complete=True, seconds=10.5))
    doc = json.loads(session.write().read_text(encoding="utf-8"))
    assert doc["format"] == "heat3d-session" and doc["sessionType"] == "race"
    assert len(doc["laps"]) == 2 and doc["laps"][1]["lap"]["seconds"] == 10.5
    assert doc["laps"][0]["format"] == "heat3d-lap" and doc["laps"][0]["car"]["name"] == "honda_nsx_gt3_evo"
    assert [o["id"] for o in doc["others"]] == ["2"]
    assert len(doc["others"][0]["channels"]["x"]) > 10


def test_other_cars_are_dropped_when_the_table_does_not_hold_the_player():
    others = kunos.OtherCars()
    for i in range(50):
        others.feed(i * 0.2, {"cars": {1: (500.0, 0.0, 0.0), 2: (600.0, 0.0, 0.0)}, "playerCarId": 1}, (0.0, 0.0, 0.0))
    assert others.documents(0.0) == []


def test_the_recorder_writes_one_session_file(tmp_path, monkeypatch):
    """The whole loop on pages that change between reads: two laps and the run after them, one file."""
    period = 2 * math.pi * 100 / 30
    hz = 50
    n = int(2.6 * period * hz)
    state = {"i": 0}

    class Page:
        def __init__(self, make):
            self.make = make

        def __getitem__(self, key):
            return self.make(state["i"])[key]

    def physics(i):
        a = 30 * (i / hz) / 100
        return physics_page(x=100 * math.sin(a), z=100 * (1 - math.cos(a)), packet=i + 1)

    def graphics(i):
        t = i / hz
        lap = int(t / period)
        return acc_graphics(laps=lap, last_ms=int(period * 1000) if lap else 0, fraction=(t / period) % 1.0)

    static = bytearray(688)
    static[134 : 134 + 12] = "monza\x00".encode("utf-16-le")
    views = {
        "Local\\acpmf_physics": Page(physics),
        "Local\\acpmf_graphics": Page(graphics),
        "Local\\acpmf_static": Page(lambda i: bytes(static)),
    }
    monkeypatch.setattr(kunos, "_open", lambda name, size: views[name])
    monkeypatch.setattr(kunos.sys, "platform", "win32")
    clock = {"t": 0.0}
    monkeypatch.setattr(kunos.time, "perf_counter", lambda: clock["t"])

    def sleep(_s):
        state["i"] += 1
        clock["t"] = state["i"] / hz
        if state["i"] >= n:
            raise KeyboardInterrupt

    monkeypatch.setattr(kunos.time, "sleep", sleep)
    written = kunos.run(tmp_path, game="acc")
    sessions = [p for p in written if p.name.endswith("_session.json")]
    assert len(sessions) == 1
    doc = json.loads(sessions[0].read_text(encoding="utf-8"))
    assert doc["track"] == "monza" and len(doc["laps"]) == 3
    assert [lap["lap"]["complete"] for lap in doc["laps"]] == [True, True, False]
    assert "lapFraction" in doc["laps"][0]["channels"] and "sector" in doc["laps"][0]["channels"]
