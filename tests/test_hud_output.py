"""
The pieces put together: lives, the player's events, north, and the files.

A synthetic match: two lives walked on the drawn level, a gap between them
where the player was dead, a kill in the first life and the feed line for the
death that ended it. The compass is told the true heading (the drawn level's
up is north), so after assembly the table has to say, in x-east y-north, where
the walk truly went and which way it faced - the sign conventions of the turn
and the flip are exactly what this checks.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections import Counter

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from heat3d_capture.hud.compass import Bearing  # noqa: E402
from heat3d_capture.hud.killfeed import ENEMY, FRIENDLY, SQUAD, Feed, Row  # noqa: E402
from heat3d_capture.hud.minimap import MinimapTracker  # noqa: E402
from heat3d_capture.hud.output import map_anchors  # noqa: E402
from heat3d_capture.hud.profiles import BF6  # noqa: E402
from heat3d_capture.hud.run import Options, assemble  # noqa: E402

from . import hud_synth as hs  # noqa: E402

ME = "Made_Up_Me"


@pytest.fixture(scope="module")
def match(tmp_path_factory):
    world = hs.level()
    life1 = hs.walk(world, (900, 1200), [(0, 180), (90, 150)])
    life2 = hs.walk(world, (1000, 1150), [(180, 120), (-90, 120)])
    tracker = MinimapTracker(hs.PLAYER, hs.KEY)
    play, bearings, truth = [], [], []
    t = 0.0
    for v in life1:
        play.append((t, True))
        tracker.add(t, v.image)
        bearings.append(Bearing(t=t, heading=v.heading, scale=3.0, labels=3))
        truth.append((t, v))
        t += 0.2
    death_t = t - 1.0
    for _ in range(50):  # ten seconds dead
        play.append((t, False))
        tracker.break_track()
        tracker.out_of_play += 1
        t += 0.2
    for v in life2:
        play.append((t, True))
        tracker.add(t, v.image)
        truth.append((t, v))
        t += 0.2
    feed = Feed()
    rows = [
        (3.0, Row(0, ME, "Someone_Else", SQUAD, ENEMY)),
        (death_t, Row(0, "Rival_Player", ME, ENEMY, SQUAD, marker="arrow")),
        (5.0, Row(0, "Third_Party", "Fourth_One", FRIENDLY, ENEMY)),
    ]
    for when, row in rows:
        feed.add(when, [row])
        feed.add(when + 0.4, [row])
    out = tmp_path_factory.mktemp("hud") / "match"
    video = out.parent / "made_up_clip.mp4"
    result = assemble(
        video, out, Options(player=ME), BF6, tracker, play, feed.finish(), bearings, [], timing={},
    )
    return result, out, truth, death_t


def table(out):
    t = pq.read_table(str(out) + ".parquet")
    return t, t.to_pylist()


def test_files_are_written(match):
    result, out, _, _ = match
    names = sorted(p.name for p in result.files)
    assert names == sorted(["match.parquet", "match.map.png", "match.map.json", "match.events.jsonl", "match.summary.json"])


def test_footer_tells_the_viewer_how_to_read_it(match):
    _, out, _, _ = match
    t, _ = table(out)
    hints = json.loads(t.schema.metadata[b"heat3d"])
    assert hints["axes"]["up"] == "z"
    cols = hints["columns"]
    assert (cols["x"], cols["y"], cols["z"], cols["time"], cols["personId"], cols["sessionId"]) == (
        "x", "y", "z", "time", "player", "session")
    assert cols["lookMode"] == "vector" and cols["dirX"] == "dir_x"
    assert "event" in cols["extra"]


def test_lives_events_and_sessions(match):
    _, out, _, death_t = match
    _, rows = table(out)
    events = Counter(r["event"] for r in rows)
    assert events["start"] == 1 and events["spawn"] == 1 and events["kill"] == 1 and events["death"] == 1
    assert {r["player"] for r in rows} == {"me"}
    sessions = sorted({r["session"] for r in rows})
    assert sessions == ["made_up_clip#01", "made_up_clip#02"]
    death = next(r for r in rows if r["event"] == "death")
    assert death["time"] == pytest.approx(death_t) and death["session"] == "made_up_clip#01"
    assert death["killer"] == "Rival_Player"
    # Nothing of the first life after its death: the route ends there.
    assert not [r for r in rows if r["session"] == "made_up_clip#01" and r["time"] > death_t + 1e-3]
    spawn = next(r for r in rows if r["event"] == "spawn")
    assert spawn["session"] == "made_up_clip#02"
    assert spawn["time"] == min(r["time"] for r in rows if r["session"] == "made_up_clip#02")


def test_track_is_north_up_and_true(match):
    _, out, truth, _ = match
    _, rows = table(out)
    pos = {round(r["time"], 3): r for r in rows if r["event"] in ("position", "start", "spawn")}
    pairs = [(pos[round(t, 3)], v) for t, v in truth if round(t, 3) in pos]
    assert len(pairs) > 0.9 * len(truth)
    # Table x east, y north; the drawn level has x east, y south. Same up to a shift.
    dx = np.array([r["x"] - v.x for r, v in pairs])
    dy = np.array([r["y"] + v.y for r, v in pairs])
    assert np.ptp(dx) < 4.0 and np.ptp(dy) < 4.0
    for r, v in pairs:
        assert abs((r["heading"] - v.heading + 180) % 360 - 180) < 2.0
        assert r["dir_x"] == pytest.approx(math.sin(math.radians(r["heading"])), abs=1e-3)


def test_events_and_summary(match):
    _, out, _, _ = match
    lines = [json.loads(x) for x in (out.parent / "match.events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 3
    mine = [x for x in lines if x["me"]]
    assert {x["kind"] for x in mine} == {"kill", "death"}
    assert all("x" in x for x in mine)
    other = next(x for x in lines if not x["me"])
    assert "x" not in other
    s = json.loads((out.parent / "match.summary.json").read_text(encoding="utf-8"))
    assert (s["kills"], s["deaths"], s["kd"], s["lives"]) == (1, 1, 1.0, 2)
    assert s["maps"][0]["north_up"] is True
    assert s["player"] == ME


def test_map_image_lines_up_with_the_table(match):
    _, out, truth, _ = match
    side = json.loads((out.parent / "match.map.json").read_text(encoding="utf-8"))
    a, b = side["anchors"]
    img = cv2.imread(str(out) + ".map.png")
    assert (img.shape[1], img.shape[0]) == (side["width"], side["height"])
    # The viewer's mapQuadFromAnchors, in Python: a table point back to a picture pixel.
    sx = (b["worldX"] - a["worldX"]) / (b["px"] - a["px"])
    sz = (b["worldZ"] - a["worldZ"]) / (b["py"] - a["py"])
    _, rows = table(out)
    world = hs.level()
    errs = []
    for r in rows[::7]:
        px = a["px"] + (r["x"] - a["worldX"]) / sx
        py = a["py"] + (r["y"] - a["worldZ"]) / sz
        # The mosaic at the player's spot looks like the level at the true spot.
        t = next(v for tt, v in truth if abs(tt - r["time"]) < 1e-6) if r["event"] != "kill" else None
        if t is None or not (8 <= px < img.shape[1] - 8 and 8 <= py < img.shape[0] - 8):
            continue
        got = img[int(py) - 6 : int(py) + 7, int(px) - 6 : int(px) + 7].astype(float).mean()
        want = world[int(t.y) - 6 : int(t.y) + 7, int(t.x) - 6 : int(t.x) + 7].astype(float).mean()
        errs.append(abs(got - want))
    assert errs and np.median(errs) < 12


def test_anchors_match_the_viewers_placement():
    a, b = map_anchors(200, 100, x0=-50.0, y0=30.0, per_pixel=2.0)
    assert (a["worldX"], a["worldZ"]) == (-50.0, 30.0)
    assert (b["worldX"], b["worldZ"]) == (350.0, -170.0)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_video_samples_cut_the_regions(tmp_path):
    from heat3d_capture.hud.video import layout, probe, samples

    clip = tmp_path / "made_up.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30:duration=2",
         "-pix_fmt", "yuv420p", str(clip)],
        check=True,
    )
    info = probe(clip)
    assert (info.width, info.height) == (1280, 720)
    got = list(samples(clip, BF6, fps=5.0, gpu=False))
    assert 9 <= len(got) <= 11
    plan = layout(BF6.regions)
    for r in BF6.regions:
        assert got[0].regions[r.name].shape[:2] == (r.size[1], r.size[0])
        assert plan.places[r.name][2:] == r.size
    assert got[3].t == pytest.approx(0.6)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_other_aspect_ratios_are_refused(tmp_path):
    from heat3d_capture.hud.video import probe

    clip = tmp_path / "wide.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=1280x540:rate=10:duration=1",
         "-pix_fmt", "yuv420p", str(clip)],
        check=True,
    )
    with pytest.raises(ValueError, match="16:9"):
        probe(clip)


def test_a_single_sample_jump_is_dropped_and_a_turn_is_not():
    from heat3d_capture.hud.minimap import TrackPoint
    from heat3d_capture.hud.run import drop_spikes

    def point(t, x, y):
        return TrackPoint(t=t, x=x, y=y, heading=0.0, scale=1.0, inliers=50, island=0, A=np.eye(2, 3))

    # Walking east at 2 px a sample, one sample thrown 30 px off, then a sharp turn north.
    pts = [point(i * 0.2, 2.0 * i, 0.0) for i in range(10)]
    pts[5] = point(1.0, 10.0, 30.0)
    pts += [point((10 + i) * 0.2, 18.0, -2.0 * (i + 1)) for i in range(10)]
    kept, dropped = drop_spikes(pts, 0.2)
    assert dropped == 1
    assert all(abs(p.t - 1.0) > 1e-9 for p in kept)
    assert len(kept) == len(pts) - 1
