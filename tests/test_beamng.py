"""BeamNG's heat3d protocol packets, as the Lua mod packs them, into lap files."""

from __future__ import annotations

import json
import math
import struct

from heat3d_capture.telemetry import beamng


def packet(*, t: float, pos, vel, fwd, up=(0.0, 0.0, 1.0), speeds=(20.0, 20.0, 24.0, 24.0), material=1.0) -> bytes:
    floats = [t, *pos, *vel, *fwd, *up, 0.1, 1.0, 0.0, 0.0, 0.0, 0.2, 6000.0, 3.0, 0.0, 0.0]
    floats += list(speeds)  # surface speed
    floats += [s / 0.33 for s in speeds]  # rotation
    floats += [3000.0] * 4  # load
    floats += [material] * 4
    assert len(floats) == beamng.FLOATS
    return beamng.MAGIC + struct.pack(f"<{beamng.FLOATS}f", *floats)


def test_packet_layout_matches_the_lua_struct():
    # char[4] then 39 floats, as the mod's getStructDefinition declares.
    assert beamng.LENGTH == 4 + 4 * 39
    lua = (beamng.MOD / "lua" / "vehicle" / "protocols" / "heat3d.lua").read_text(encoding="utf-8")
    declared = lua[lua.index("[[") : lua.index("]]")]
    count = 0
    for line in declared.splitlines():
        line = line.strip().rstrip(";")
        if not line.startswith("float"):
            continue
        for name in line[len("float") :].split(","):
            count += int(name[name.index("[") + 1 : name.index("]")]) if "[" in name else 1
    assert count == beamng.FLOATS


def test_world_turns_to_y_up_and_the_car_frame_comes_out():
    # BeamNG: Z up. The car points along world +Y and slides 0.2 rad to its side.
    speed = 25.0
    slide = 0.2
    fwd = (0.0, 1.0, 0.0)
    vel = (speed * math.sin(slide), speed * math.cos(slide), 0.0)
    frame = beamng.frame_from(beamng.decode(packet(t=1.0, pos=(10.0, 20.0, 5.0), vel=vel, fwd=fwd)))
    # (x, y, z) -> (x, z, -y): height is y now.
    assert (frame["x"], frame["y"], frame["z"]) == (10.0, 5.0, -20.0)
    assert math.isclose(math.atan2(abs(frame["latVel"]), frame["longVel"]), slide, abs_tol=1e-5)
    assert math.isclose(frame["speed"], speed, rel_tol=1e-6)
    assert frame["wheelSurfaceSpeed.RL"] == 24.0 and frame["groundContact.FL"] == 1.0


def test_off_the_ground_when_no_material():
    frame = beamng.frame_from(beamng.decode(packet(t=1.0, pos=(0, 0, 0), vel=(0, 10, 0), fwd=(0, 1, 0), material=-1.0)))
    assert frame["groundContact.FL"] == 0.0


def test_a_lap_round_a_circle_is_written(tmp_path):
    rec = beamng.Recorder(tmp_path)
    out = []
    radius = 100.0
    speed = 30.0
    for k in range(0, 1400):
        t = k * 0.05
        a = speed * t / radius
        pos = (radius * math.sin(a), radius * (1 - math.cos(a)), 0.0)
        vel = (speed * math.cos(a), speed * math.sin(a), 0.0)
        fwd = (math.cos(a), math.sin(a), 0.0)
        out += rec.feed(packet(t=t, pos=pos, vel=vel, fwd=fwd))
    assert out, "a lap closes when the car comes back past where it started"
    doc = json.loads(out[0].read_text())
    assert doc["game"] == "beamng" and doc["lap"]["complete"]
    assert abs(doc["lap"]["metres"] - 2 * math.pi * radius) < 25
    # Centripetal acceleration from the velocity: v^2 / r sideways.
    lat = doc["channels"]["latAcc"]
    assert abs(abs(lat[len(lat) // 2]) - speed**2 / radius) < 0.5


def test_a_reset_keeps_what_was_driven_before_it(tmp_path):
    """
    Resetting the car restarts its clock, and the recorder used to answer that
    by replacing the lap splitter - and the open run in it - unwritten.
    """
    rec = beamng.Recorder(tmp_path)
    out = []
    speed = 30.0
    # 20 s down a straight: 600 m, never back past the start, so no lap closes.
    for k in range(400):
        t = k * 0.05
        out += rec.feed(packet(t=t, pos=(0.0, speed * t, 0.0), vel=(0.0, speed, 0.0), fwd=(0.0, 1.0, 0.0)))
    assert out == []
    # Reset: the clock is back at zero.
    out += rec.feed(packet(t=0.0, pos=(0.0, 0.0, 0.0), vel=(0.0, 0.0, 0.0), fwd=(0.0, 1.0, 0.0)))
    assert len(out) == 1
    doc = json.loads(out[0].read_text())
    assert not doc["lap"]["complete"] and doc["lap"]["metres"] > 500


def test_every_packet_is_kept_whole_beside_the_laps(tmp_path):
    """3DHeat's converter rule: every packet whole, the mod's and anything else on the port."""
    import pyarrow.parquet as pq

    rec = beamng.Recorder(tmp_path)
    packets = [packet(t=k * 0.05, pos=(k * 1.0, 0.0, 0.0), vel=(20.0, 0.0, 0.0), fwd=(1.0, 0.0, 0.0)) for k in range(5)]
    for p in (*packets, b"not beamng"):
        rec.feed(p)
    rec.close()
    (sidecar,) = tmp_path.glob("*_beamng.raw.parquet")
    t = pq.read_table(sidecar).to_pydict()
    assert t["payload"] == [*packets, b"not beamng"]
    assert t["type"] == ["H3D1"] * 5 + ["10-byte"]
    assert t["used"] == [True] * 5 + [False]
    frame = beamng.frame_from(beamng.decode(packets[0]))
    assert frame["wheelMaterial.FL"] == 1.0 and "forwardX" in frame and "worldVelX" in frame
