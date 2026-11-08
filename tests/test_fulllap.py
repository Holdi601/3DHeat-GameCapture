"""
Full-telemetry lap recording: every channel, one file per lap, and the relay.

Packets are built the way the game builds them, with the Speed field matching
the velocity so layout detection accepts them, and every field this decodes set
to a distinct value so a wrong offset reads the wrong number rather than a
plausible zero.
"""

from __future__ import annotations

import json
import math
import socket
import struct

import pytest

from heat3d_capture.telemetry.forza import DASH_BLOCK_LENGTH, FH_DASH_LENGTH, FM_DASH_LENGTH, detect_layout
from heat3d_capture.telemetry.fulllap import (
    FM2023_LENGTH,
    FullRecorder,
    Lap,
    LapSplitter,
    decode_full,
    parse_forward,
)

HORIZON_BASE = FH_DASH_LENGTH - DASH_BLOCK_LENGTH


def packet(
    *,
    length: int = FH_DASH_LENGTH,
    base: int = HORIZON_BASE,
    lap: int = 1,
    current_lap: float = 10.0,
    last_lap: float = 0.0,
    distance: float = 1000.0,
    position=(100.0, 5.0, -200.0),
    velocity=(3.0, 0.0, 4.0),
    race_on: bool = True,
    timestamp: int = 1000,
) -> bytes:
    buf = bytearray(b"\xcd" * length)
    struct.pack_into("<i", buf, 0, 1 if race_on else 0)
    struct.pack_into("<I", buf, 4, timestamp)
    struct.pack_into("<3f", buf, 8, 8000.0, 900.0, 6123.0)
    struct.pack_into("<3f", buf, 20, 4.0, 0.5, -9.0)  # accel x (lat), y, z (long)
    struct.pack_into("<3f", buf, 32, *velocity)
    struct.pack_into("<3f", buf, 44, 0.1, 0.25, 0.3)  # angular velocity
    struct.pack_into("<3f", buf, 56, 1.0, 0.02, -0.01)
    struct.pack_into("<4f", buf, 68, 0.4, 0.45, 0.5, 0.55)  # suspension
    struct.pack_into("<4f", buf, 84, -0.2, -0.3, 1.2, 1.4)  # slip ratio
    struct.pack_into("<4f", buf, 100, 90.0, 91.0, 92.0, 93.0)
    struct.pack_into("<4i", buf, 116, 0, 1, 0, 0)
    struct.pack_into("<4f", buf, 132, 0.0, 0.0, 0.0, 0.0)
    struct.pack_into("<4f", buf, 148, 0.0, 0.0, 0.0, 0.0)
    struct.pack_into("<4f", buf, 164, 0.6, 0.7, 0.3, 0.2)  # slip angle
    struct.pack_into("<4f", buf, 180, 0.8, 0.9, 1.1, 1.3)  # combined slip
    struct.pack_into("<4f", buf, 196, 0.05, 0.06, 0.07, 0.08)
    struct.pack_into("<5i", buf, 212, 1032, 3, 700, 2, 8)
    struct.pack_into("<3f", buf, base, *position)
    struct.pack_into("<f", buf, base + 12, math.hypot(*velocity))
    struct.pack_into("<2f", buf, base + 16, 350_000.0, 540.0)
    struct.pack_into("<4f", buf, base + 24, 212.0, 176.0, 158.0, 140.0)  # Fahrenheit
    struct.pack_into("<f", buf, base + 48, distance)
    struct.pack_into("<3f", buf, base + 52, 0.0, last_lap, current_lap)
    struct.pack_into("<f", buf, base + 64, 100.0)
    struct.pack_into("<H", buf, base + 68, lap)
    struct.pack_into("<6B", buf, base + 70, 1, 255, 51, 0, 0, 4)
    struct.pack_into("<3b", buf, base + 76, -127, 64, 0)
    if length == FM2023_LENGTH:
        struct.pack_into("<4f", buf, base + DASH_BLOCK_LENGTH, 0.1, 0.2, 0.3, 0.4)
        struct.pack_into("<i", buf, base + DASH_BLOCK_LENGTH + 16, 860)
    return bytes(buf)


class TestDecoding:
    def test_every_wheel_channel_lands_on_its_wheel(self):
        layout = detect_layout([packet()])
        frame = decode_full(packet(), layout)
        assert frame["slipRatio.RL"] == pytest.approx(1.2)
        assert frame["slipAngle.FR"] == pytest.approx(0.7)
        assert frame["combinedSlip.RR"] == pytest.approx(1.3)
        assert frame["suspension.FL"] == pytest.approx(0.4)
        assert frame["wheelSpeed.RR"] == pytest.approx(93.0)
        assert frame["rumble.FR"] == 1

    def test_units_are_the_canonical_ones(self):
        layout = detect_layout([packet()])
        frame = decode_full(packet(), layout)
        # 212 F is 100 C; pedals 0..1; steering -1..1.
        assert frame["tireTemp.FL"] == pytest.approx(100.0)
        assert frame["tireTemp.RR"] == pytest.approx(60.0)
        assert frame["throttle"] == pytest.approx(1.0)
        assert frame["brake"] == pytest.approx(0.2)
        assert frame["steer"] == pytest.approx(-1.0)
        assert frame["latAcc"] == pytest.approx(4.0)
        assert frame["longAcc"] == pytest.approx(-9.0)
        assert frame["yawRate"] == pytest.approx(0.25)
        assert frame["rpm"] == pytest.approx(6123.0)
        assert frame["power"] == pytest.approx(350_000.0)

    def test_motorsport_2023_adds_tyre_wear_and_the_track(self):
        pkt = packet(length=FM2023_LENGTH, base=FM_DASH_LENGTH - DASH_BLOCK_LENGTH)
        layout = detect_layout([pkt])
        frame = decode_full(pkt, layout)
        assert frame["tireWear.RR"] == pytest.approx(0.4)
        assert frame["trackOrdinal"] == 860


def frames(laps):
    """Frames through a splitter: (lap, current_lap, last_lap, distance) tuples."""
    layout = detect_layout([packet()])
    out = []
    stamp = 1000
    for lap, current, last, distance in laps:
        stamp += 16
        out.append(decode_full(packet(lap=lap, current_lap=current, last_lap=last, distance=distance, timestamp=stamp), layout))
    return out


class TestSplitting:
    def test_a_lap_closes_when_the_counter_moves_with_the_games_own_time(self):
        splitter = LapSplitter()
        done = []
        for frame in frames([(1, 0.0, 0.0, 0.0), (1, 30.0, 0.0, 900.0), (1, 52.0, 0.0, 1900.0), (2, 0.1, 52.103, 1905.0)]):
            done += splitter.feed(frame)
        assert len(done) == 1
        assert done[0].complete and done[0].seconds == pytest.approx(52.103)
        assert done[0].number == 1 and len(done[0].frames) == 3

    def test_a_sprint_is_kept_when_the_race_stops(self):
        splitter = LapSplitter()
        for frame in frames([(0, 0.0, 0.0, 0.0), (0, 60.0, 0.0, 3000.0)]):
            splitter.feed(frame)
        done = splitter.flush()
        assert len(done) == 1 and not done[0].complete

    def test_a_few_metres_in_a_menu_are_not_a_lap(self):
        splitter = LapSplitter()
        for frame in frames([(0, 0.0, 0.0, 0.0), (0, 2.0, 0.0, 30.0)]):
            splitter.feed(frame)
        assert splitter.flush() == []

    def test_a_long_silence_closes_the_lap(self):
        splitter = LapSplitter()
        layout = detect_layout([packet()])
        splitter.feed(decode_full(packet(timestamp=1000, distance=0.0), layout))
        splitter.feed(decode_full(packet(timestamp=1016, distance=800.0), layout))
        done = splitter.feed(decode_full(packet(timestamp=9000, distance=900.0, lap=1), layout))
        assert len(done) == 1


class TestTheFile:
    def test_the_document_is_a_heat3d_lap_with_columns(self):
        lap = Lap(number=1, frames=frames([(1, 5.0, 0.0, 100.0), (1, 6.0, 0.0, 130.0)]), seconds=51.0, complete=True)
        doc = lap.document(layout="Horizon dash")
        assert doc["format"] == "heat3d-lap" and doc["version"] == 1
        assert doc["car"]["carOrdinal"] == 1032 and doc["car"]["carPI"] == 700
        assert doc["channels"]["time"] == [0.0, 1.0]
        assert doc["channels"]["distance"] == [0.0, 30.0]
        assert "tireTemp.FL" in doc["channels"] and "slipRatio.RR" in doc["channels"]
        assert "carOrdinal" not in doc["channels"]
        json.dumps(doc)


class TestRelay:
    def test_every_packet_is_passed_on_unchanged(self, tmp_path):
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(("127.0.0.1", 0))
        listener.settimeout(2.0)
        port = listener.getsockname()[1]
        recorder = FullRecorder(tmp_path, port=0, forward=("127.0.0.1", port))
        try:
            sent = packet()
            recorder.feed(sent)
            received, _ = listener.recvfrom(2048)
            assert received == sent
        finally:
            recorder.close()
            listener.close()

    def test_a_whole_lap_through_the_recorder_writes_a_file(self, tmp_path):
        recorder = FullRecorder(tmp_path, port=0)
        try:
            stamp = 1000
            for lap, current, last, distance in [(1, 0.0, 0.0, 0.0), (1, 30.0, 0.0, 900.0), (2, 0.1, 50.5, 1905.0)]:
                stamp += 16
                recorder.feed(packet(lap=lap, current_lap=current, last_lap=last, distance=distance, timestamp=stamp))
        finally:
            recorder.close()
        written = sorted(tmp_path.glob("*.lap.json"))
        assert written, "no lap file"
        doc = json.loads(written[0].read_text(encoding="utf-8"))
        assert doc["lap"]["seconds"] == pytest.approx(50.5)

    def test_forward_addresses_parse(self):
        assert parse_forward("127.0.0.1:5301") == ("127.0.0.1", 5301)
        assert parse_forward(":5301") == ("127.0.0.1", 5301)
        assert parse_forward(None) is None


class TestWhatTheFileSays:
    def doc(self, **kwargs):
        lap = Lap(number=1, frames=frames([(1, 5.0, 0.0, 100.0), (1, 6.0, 0.0, 130.0)]), seconds=51.0, complete=True)
        return lap.document(layout="Horizon dash", **kwargs)

    def test_the_car_local_velocity_is_under_the_names_the_viewer_reads(self):
        # Data Out's velocity is the car's own (x right, y up, z forward). As
        # velX/velY/velZ the viewer had no mapping for it and estimated drift
        # from the path instead.
        channels = self.doc()["channels"]
        assert channels["latVel"][0] == pytest.approx(3.0)
        assert channels["vertVel"][0] == pytest.approx(0.0)
        assert channels["longVel"][0] == pytest.approx(4.0)
        assert not {"velX", "velY", "velZ"} & set(channels)

    def test_meta_and_track_are_written_like_every_other_recorder(self):
        doc = self.doc()
        assert doc["meta"] == {"slip": "peak", "discipline": "circuit"}
        assert "track" in doc and doc["track"] is None

    def test_units_are_only_those_of_channels_present(self):
        doc = self.doc()
        for name in doc["units"]:
            assert name in doc["channels"] or any(c.startswith(name + ".") for c in doc["channels"]), name
        assert "latVel" in doc["units"] and "tireTemp" in doc["units"]

    def test_the_motorsport_track_number_is_kept(self):
        pkt = packet(length=FM2023_LENGTH, base=FM_DASH_LENGTH - DASH_BLOCK_LENGTH)
        layout = detect_layout([pkt])
        lap = Lap(number=1, frames=[decode_full(pkt, layout)] * 2, complete=False)
        assert lap.document()["lap"]["trackOrdinal"] == 860

    def test_a_non_finite_value_is_written_as_null(self, tmp_path):
        from heat3d_capture.telemetry.fulllap import write_lap

        lap = Lap(number=1, frames=frames([(1, 5.0, 0.0, 100.0), (1, 6.0, 0.0, 130.0)]), seconds=51.0, complete=True)
        lap.frames[1] = dict(lap.frames[1], boost=float("nan"))
        text = write_lap(lap, tmp_path, layout="Horizon dash").read_text(encoding="utf-8")
        assert "NaN" not in text
        assert json.loads(text)["channels"]["boost"][1] is None


class TestEverythingKept:
    """3DHeat's converter rule: every packet received is kept whole, and a lap file holds all the packet holds."""

    def test_the_recorder_keeps_every_packet_whole(self, tmp_path):
        import pyarrow.parquet as pq

        menu = packet(race_on=False, velocity=(0.0, 0.0, 0.0))  # before the layout is known
        stranger = b"\x07" * 17
        laps = []
        stamp = 1000
        for lap, current, last, distance in [(1, 0.0, 0.0, 0.0), (1, 30.0, 0.0, 900.0), (2, 0.1, 50.5, 1905.0)]:
            stamp += 16
            laps.append(packet(lap=lap, current_lap=current, last_lap=last, distance=distance, timestamp=stamp))
        recorder = FullRecorder(tmp_path, port=0)
        try:
            for sent in (menu, stranger, *laps):
                recorder.feed(sent)
        finally:
            recorder.close()
        (sidecar,) = tmp_path.glob("*_forza.raw.parquet")
        t = pq.read_table(sidecar).to_pydict()
        assert t["payload"] == [menu, stranger, *laps]
        assert t["type"] == ["dash-horizon", "17-byte", "dash-horizon", "dash-horizon", "dash-horizon"]
        assert t["used"] == [False, False, True, True, True]
        (summary,) = tmp_path.glob("*_forza.summary.json")
        check = json.loads(summary.read_text(encoding="utf-8"))["selfCheck"]["completeness"]
        assert check["lost"] == 0 and check["types"]["17-byte"]["raw"] == 1
        assert not list(tmp_path.glob("*.raw.bin"))

    def test_a_lap_file_keeps_the_game_s_clock_and_the_bytes_nobody_names(self, tmp_path):
        recorder = FullRecorder(tmp_path, port=0, raw=False)
        try:
            stamp = 1000
            for lap, current, last, distance in [(1, 0.0, 0.0, 0.0), (1, 30.0, 0.0, 900.0), (2, 0.1, 50.5, 1905.0)]:
                stamp += 16
                recorder.feed(packet(lap=lap, current_lap=current, last_lap=last, distance=distance, timestamp=stamp))
        finally:
            recorder.close()
        (written,) = tmp_path.glob("*.lap.json")
        doc = json.loads(written.read_text(encoding="utf-8"))
        assert doc["channels"]["timestampMs"] == [1016, 1032]
        assert {"raceTime", "bestLap", "lastLap"} <= set(doc["channels"])
        # Horizon's packet: the bytes between the Sled block and the dash block, as sent (0xcd in the test packet).
        assert doc["unparsed"]["ranges"] == [[232, HORIZON_BASE]]
        assert doc["unparsed"]["hex"] == ["cd" * (HORIZON_BASE - 232)] * 2
        assert not list(tmp_path.glob("*.raw.*"))
