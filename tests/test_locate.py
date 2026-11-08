"""
Locating frames in a level, on a level drawn for the purpose (locate_world.py).

The cheap parts always run: the camera conventions, the HUD mask, the track's
outlier vote, lives and minimap fallback, the clock offset of the evaluation.
Rendering needs an OpenGL context (moderngl); the whole pipeline needs the
models too, and is skipped unless their weights are already downloaded, so
the suite never fetches half a gigabyte on its own.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from heat3d_capture.locate import camera
from heat3d_capture.locate.profiles import PROFILES, parse_box
from heat3d_capture.locate.track import Minimap, Row, TrackOptions, build_track, fit_similarity

from .locate_world import write_yard


def test_rotation_and_angles_round_trip():
    for yaw, pitch in [(0, 0), (90, 10), (-135, -30), (179, 20), (33.3, -5)]:
        r = camera.rotation_cv(yaw, pitch)
        assert np.allclose(r @ r.T, np.eye(3), atol=1e-9)
        assert np.isclose(np.linalg.det(r), 1.0)
        y, p, roll = camera.angles(r)
        assert math.isclose(((y - yaw + 180) % 360) - 180, 0, abs_tol=1e-6)
        assert math.isclose(p, pitch, abs_tol=1e-6) and abs(roll) < 1e-6
        # The camera's forward axis is the pose's direction, and its down axis points down.
        assert np.allclose(r[2], camera.direction(yaw, pitch))
        assert r[1][1] < 0


def test_yaw_is_the_games_yaw_in_the_viewers_frame():
    # A game looking along its +Y (yaw 90) looks along -Z in the viewer's (X, Z, -Y).
    assert np.allclose(camera.direction(90, 0), [0, 0, -1], atol=1e-12)
    assert np.allclose(camera.direction(0, 90), [0, 1, 0], atol=1e-12)


def test_field_of_view_conversions():
    # Source's 90 at 4:3 is about 106.26 at 16:9.
    assert math.isclose(camera.hfov_for_aspect(90, 4 / 3, 16 / 9), 106.26, abs_tol=0.01)
    assert math.isclose(camera.hfov_from_vertical(90, 1.0), 90.0)
    k = camera.intrinsics(1920, 1080, 90)
    assert math.isclose(k[0, 0], 960.0) and k[1, 2] == 540


def test_hud_mask_scales_with_the_frame():
    game = PROFILES["bf6"]
    small, big = game.mask(960, 540), game.mask(3840, 2160)
    assert not small[540 // 2, 960 // 2] and not big[1080, 1920]  # the crosshair
    assert not small[540 - 100, 60] and not big[2160 - 400, 240]  # the minimap, bottom left
    assert small[200, 300]  # the level
    assert 0.15 < 1 - small.mean() < 0.5 and abs(small.mean() - big.mean()) < 0.01
    assert parse_box("10,20,30,40") == (10, 20, 30, 40)
    with pytest.raises(ValueError):
        parse_box("1,2,3")


def _walk(times, start, velocity):
    return [np.array(start, float) + np.array(velocity, float) * t for t in times]


def test_track_votes_out_a_jump_and_keeps_a_respawn():
    times = np.arange(0, 20, 0.5)
    pos = _walk(times, (0, 1.6, 0), (3, 0, 0))
    # A respawn at t=10: somewhere far away, walking on from there.
    for i, t in enumerate(times):
        if t >= 10:
            pos[i] = np.array([100.0, 1.6, 50.0]) + np.array([0, 0, 3.0]) * (t - 10)
    rows = [Row(float(t), True, p.copy(), 0.0, 0.0, 0.9, 200) for t, p in zip(times, pos)]
    # One wrong fix in the first life, one in the second.
    rows[5].position = np.array([60.0, 1.6, -40.0])
    rows[30].position = np.array([-80.0, 1.6, 10.0])
    out, report = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5))
    assert report["outliers"] == 2
    assert not out[5].kept and not out[30].kept
    assert out[20].kept and out[20].source == "visual"  # the first fix after the respawn
    assert report["lives"] == 2
    assert {r.life for r in out if r.kept} == {0, 1}
    # Smoothing does not pull across the respawn.
    assert np.linalg.norm(out[20].smooth - pos[20]) < 1.0
    assert np.linalg.norm(out[19].smooth - pos[19]) < 1.0


def test_minimap_fills_in_where_the_picture_failed():
    times = np.arange(0, 30, 0.5)
    truth = _walk(times, (5, 2.0, -3), (2, 0, 1))
    # The minimap: its own frame, turned 30 degrees, scaled, shifted and mirrored (y north).
    a = math.radians(30)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    mm_xy = np.array([(rot @ p[[0, 2]]) * 4.0 + [500, 300] for p in truth]) * [1, -1]
    minimap = Minimap(times, mm_xy, np.full(len(times), np.nan), np.zeros(len(times), int))
    rows = []
    for i, (t, p) in enumerate(zip(times, truth)):
        failed = 20 <= i < 30
        rows.append(Row(float(t), not failed, None if failed else p.copy(), 0.0, 0.0, 0.8, 150))
    out, report = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5), minimap)
    assert report["minimap"]["filled"] == 10
    for i in range(20, 30):
        assert out[i].source == "minimap"
        assert np.linalg.norm(out[i].smooth[[0, 2]] - truth[i][[0, 2]]) < 0.1
        assert out[i].uncertainty is not None and out[i].confidence <= 0.5
    assert all(out[i].source == "visual" for i in range(0, 20))


def test_similarity_fit_ignores_outliers():
    rng = np.random.default_rng(1)
    src = rng.uniform(-100, 100, (60, 2))
    a = math.radians(-70)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    dst = src @ rot.T * 0.5 + [10, -20]
    dst[:8] += rng.uniform(30, 80, (8, 2))
    sim = fit_similarity(src, dst, threshold=1.0)
    assert sim is not None and sim.inliers == 52
    assert math.isclose(sim.scale, 0.5, rel_tol=1e-6) and sim.residual < 1e-6


def test_evaluation_finds_the_clock_offset():
    from heat3d_capture.locate.evaluate import compare

    t = np.arange(0, 60, 1 / 64)
    truth = {
        "time": t,
        "x": 10 * np.sin(t / 5),
        "y": np.full(len(t), 1.6),
        "z": 7 * np.cos(t / 3),
        "yaw": (t * 10) % 360 - 180,
        "pitch": np.zeros(len(t)),
    }
    lt = np.arange(0, 40, 0.5)
    off = 12.34
    located = {
        "time": lt,
        "x": np.interp(lt + off, t, truth["x"]),
        "y": np.full(len(lt), 1.6),
        "z": np.interp(lt + off, t, truth["z"]),
        "yaw": np.interp(lt + off, t, np.degrees(np.unwrap(np.radians(truth["yaw"])))),
        "pitch": np.zeros(len(lt)),
        "source": np.array(["visual"] * len(lt), dtype=object),
    }
    result = compare(located, truth, None, 1.0)
    assert abs(result["offset_s"] - off) < 0.03
    assert result["visual"]["median_m"] < 0.05 and result["visual"]["median_deg"] < 0.5


# -- rendering ---------------------------------------------------------------


@pytest.fixture(scope="module")
def yard(tmp_path_factory):
    pytest.importorskip("cv2")
    return write_yard(tmp_path_factory.mktemp("yard") / "yard.glb")


@pytest.fixture(scope="module")
def renderer(yard):
    pytest.importorskip("moderngl")
    from heat3d_capture.locate.level import load
    from heat3d_capture.locate.render import Renderer

    try:
        r = Renderer(load(yard), 320, 180)
    except Exception as exc:  # no OpenGL 3.3 here
        pytest.skip(f"no OpenGL context: {exc}")
    yield r
    r.release()


def test_level_reads_textures_and_floors(yard):
    from heat3d_capture.locate.level import load

    level = load(yard)
    assert level.unit_metres == 1.0
    assert all(m.image is not None for m in level.materials[:-1])
    a, b, c = level.ground()
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
    # The yard's floor plus the crates' tops.
    assert 1600 < area < 1700


def test_depth_is_the_distance_along_the_view(renderer):
    from heat3d_capture.locate.render import Light

    # From above the middle - over every crate, which are at most 3.5 m high -
    # looking north (-Z) at the wall 20 m away, then a little down at the floor.
    pose = camera.Pose(np.array([0.0, 4.0, 0.0]), 90.0, 0.0)
    r = renderer.render(pose, 90.0, Light())
    h, w = r.depth.shape
    assert math.isclose(float(r.depth[h // 2, w // 2]), 20.0, rel_tol=0.005)
    down = renderer.render(camera.Pose(pose.position, 90.0, -89.9), 90.0, Light())
    assert float(down.depth[h // 2, w // 2]) == pytest.approx(4.0, rel=0.005) or float(down.depth[h // 2, w // 2]) < 4.0
    assert r.front[h // 2, w // 2]
    assert r.color.shape == (h, w, 3) and r.color.std() > 10


def test_places_inside_crates_are_dropped(renderer):
    from heat3d_capture.locate import poses

    level = renderer.level
    pts = poses.ground_points(level, 4.0)
    keep = poses.check(renderer, pts, 1.6)
    # Floor points under crates are inside them; tops of crates are floors too, and keep.
    assert 0.5 < keep.mean() < 1.0
    from .locate_world import yard as parts

    crates = [np.concatenate([q[0] for q in quads]) for name, quads, _ in parts() if name.startswith("structure:crate")]
    tall = [c for c in crates if c[:, 1].max() > 1.8]
    assert tall
    lo, hi = tall[0].min(axis=0), tall[0].max(axis=0)
    centre = np.array([[(lo[0] + hi[0]) / 2, 0.0, (lo[2] + hi[2]) / 2]])
    assert not poses.check(renderer, centre, 1.6)[0]
    # Near the north wall, where no crate stands (they all lie within 16.5 m of the middle).
    assert poses.check(renderer, np.array([[0.5, 0.0, -18.0]]), 1.6)[0]


def _models_cached() -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache
        import torch

        from heat3d_capture.locate.features import GLOBAL_MODEL

        hub = torch.hub.get_dir()
    except Exception:
        return False
    import os

    found = try_to_load_from_cache(GLOBAL_MODEL, "config.json")
    ckpt = os.path.join(hub, "checkpoints")
    have = os.path.isdir(ckpt) and any(f.startswith("aliked") for f in os.listdir(ckpt))
    return isinstance(found, str) and have


@pytest.mark.skipif(not _models_cached(), reason="DINOv2 / ALIKED / LightGlue weights not downloaded")
def test_frames_are_located_in_the_yard(yard, tmp_path, renderer):
    """The whole pipeline: build a database of the yard, then locate renders from poses it never saw."""
    pytest.importorskip("kornia")
    from heat3d_capture.locate.database import BuildOptions, build
    from heat3d_capture.locate.localize import Locator
    from heat3d_capture.locate.render import Light

    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    db = build(yard, tmp_path / "db", game, BuildOptions(spacing=5.0, yaw_step=45.0), on_progress=lambda s: None)
    assert len(db.views) > 100
    locator = Locator(db, renderer.level, width=640, shortlist=6)
    rng = np.random.default_rng(3)
    errors, turns = [], []
    for _ in range(6):
        while True:
            x, z = rng.uniform(-17, 17, 2)
            # Not inside a crate: the depth straight down must be the eye height.
            pose = camera.Pose(np.array([x, 1.5 + rng.uniform(0, 0.2), z]), float(rng.uniform(-180, 180)), float(rng.uniform(-20, 10)))
            locator.renderer.resize(640, 360)
            down = locator.renderer.render(camera.Pose(pose.position, 0.0, -89.9), 90.0, want_color=False)
            if abs(float(down.depth[180, 320]) - pose.position[1]) < 0.05:
                break
        frame = locator.renderer.render(pose, 90.0, Light(sun=(-0.5, 0.7, 0.2), ambient=0.3, diffuse=0.7)).color
        fix = locator.locate(frame)
        assert fix.pose is not None
        errors.append(float(np.linalg.norm(fix.pose.position - pose.position)))
        turns.append(camera.angle_between(fix.pose.rotation(), pose.rotation()))
    locator.close()
    assert np.median(errors) < 0.25 and np.median(turns) < 2.0


def test_table_says_where_every_row_came_from(tmp_path):
    pa = pytest.importorskip("pyarrow")
    import json

    import pyarrow.parquet as pq

    from heat3d_capture.locate.run import write_table

    times = np.arange(0, 10, 0.5)
    truth = _walk(times, (0, 1.6, 0), (1, 0, 0))
    mm = Minimap(times, np.array([p[[0, 2]] for p in truth]), np.zeros(len(times)), np.zeros(len(times), int))
    rows = [Row(float(t), i % 5 != 0, p.copy() if i % 5 else None, 0.0, 0.0, 0.9, 120) for i, (t, p) in enumerate(zip(times, truth))]
    rows.append(Row(20.0, False))  # far past the minimap: nothing places it
    out, _ = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5), mm)
    path = write_table(tmp_path / "x.parquet", out, unit=1.0, game="generic", source="clip.mp4")
    t = pq.read_table(path)
    sources = t["source"].to_pylist()
    assert set(sources) == {"visual", "minimap", "none"}
    assert all(s == "minimap" for s, r in zip(sources, out) if not r.ok and r.time < 10)
    assert t["x"].to_pylist()[-1] is None and t["confidence"].to_pylist()[-1] == 0.0
    assert t["event"].to_pylist()[0] == "start" and t["session"].to_pylist()[0] == "clip#01"
    hints = json.loads(t.schema.metadata[b"heat3d"])
    assert hints["kind"] == "heat3d-locate" and hints["axes"]["up"] == "y"
    # Every column that has no role is listed, or the viewer drops it.
    roles = {v for k, v in hints["columns"].items() if k not in ("extra", "timeUnit", "lookMode")}
    assert set(t.column_names) - roles == set(hints["columns"]["extra"])
    assert t["life"].type == pa.int32()


def test_frames_reads_a_folder_of_pictures_in_order(tmp_path):
    cv2 = pytest.importorskip("cv2")
    from heat3d_capture.locate.run import frames

    for k in range(3):
        cv2.imwrite(str(tmp_path / f"f{k}.png"), np.full((9, 16, 3), 40 * k, np.uint8))
    got = list(frames(tmp_path, fps=2.0))
    assert [t for t, _ in got] == [0.0, 0.5, 1.0]
    assert got[2][1].shape == (9, 16, 3) and got[2][1][0, 0, 0] == 80


def test_floor_under_the_eye(renderer):
    nearest, typical, front = renderer.below(np.array([0.5, 1.6, -18.0]))
    assert nearest == pytest.approx(1.6, rel=0.02) and typical == pytest.approx(1.6, rel=0.02) and front == 1.0
    # Nothing under a point outside the yard's floor.
    assert renderer.below(np.array([500.0, 1.6, 0.0]))[0] == float("inf")


def test_smoothing_keeps_strong_fixes_and_pulls_weak_ones():
    times = np.arange(0, 8, 0.5)
    # A strafe - left, right, fast: real motion no line through the neighbours
    # follows - then a straight run.
    truth = [np.array([3.0 * math.sin(2.5 * t), 1.6, 0.0]) if t < 3 else np.array([3.0 * math.sin(7.5) + 5.0 * (t - 3), 1.6, 0.0]) for t in times]
    rows = [Row(float(t), True, p.copy(), 0.0, 0.0, 0.9, 300) for t, p in zip(times, truth)]
    # One weak fix on the run, half a metre off.
    weak = 11
    rows[weak].position = truth[weak] + np.array([0.0, 0.0, 0.5])
    rows[weak].inliers = 30
    out, _ = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5))
    strong = [np.linalg.norm(r.smooth - p) for i, (r, p) in enumerate(zip(out, truth)) if i != weak]
    assert max(strong) < 0.05
    assert np.linalg.norm(out[weak].smooth - truth[weak]) < 0.25
    assert out[weak].uncertainty > out[weak - 1].uncertainty
    # The view angles are the fixes' own.
    assert all(r.smooth_yaw == r.yaw for r in out)


def test_views_from_the_hud():
    cv2 = pytest.importorskip("cv2")
    from heat3d_capture.locate.views import FOOT, SCREEN, VEHICLE, ZOOMED, bf6

    def with_map_key(picture):
        out = picture.copy()
        cv2.rectangle(out, (44, 1019), (65, 1040), (190, 195, 200), -1)
        cv2.rectangle(out, (50, 1024), (52, 1036), (10, 10, 10), -1)
        cv2.rectangle(out, (58, 1024), (60, 1036), (10, 10, 10), -1)
        cv2.line(out, (51, 1024), (55, 1032), (10, 10, 10), 2)
        cv2.line(out, (59, 1024), (55, 1032), (10, 10, 10), 2)
        return out

    rng = np.random.default_rng(0)
    bare = rng.integers(60, 140, (1080, 1920, 3)).astype(np.uint8)
    # No HUD of a match at all: the desktop, a menu, the end of a round.
    assert bf6(bare) == SCREEN
    frame = with_map_key(bare)
    assert bf6(frame) == FOOT
    assert bf6(cv2.resize(frame, (3840, 2160), interpolation=cv2.INTER_NEAREST)) == FOOT
    # It sits a pixel or two either way; a road on the minimap running into it is still the key.
    assert bf6(np.roll(frame, 2, axis=0)) == FOOT
    road = frame.copy()
    cv2.line(road, (20, 1000), (46, 1022), (190, 195, 200), 3)
    assert bf6(road) == FOOT
    vehicle = frame.copy()
    for x, y, letter in ((1045, 932, "C"), (1045, 978, "E")):
        cv2.rectangle(vehicle, (x, y), (x + 22, y + 21), (190, 200, 205), -1)
        cv2.putText(vehicle, letter, (x + 5, y + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 2)
    assert bf6(vehicle) == VEHICLE
    # The same at 4K and at a quarter of 1080p.
    assert bf6(cv2.resize(vehicle, (3840, 2160), interpolation=cv2.INTER_NEAREST)) == VEHICLE
    assert bf6(cv2.resize(vehicle, (960, 540), interpolation=cv2.INTER_AREA)) == VEHICLE
    # The bar under the seat diagram alone: a vehicle whose key caps moved or vanish on bright
    # ground, at every size - and the same strip of texture without a bar is on foot.
    sand = with_map_key(rng.integers(150, 200, (1080, 1920, 3)).astype(np.uint8))
    barred = sand.copy()
    barred[1050:1056, 860:1060] = (205, 205, 210)
    assert bf6(sand) == FOOT
    assert bf6(barred) == VEHICLE
    # A damaged vehicle: the bar is its health, lit from the left.
    damaged = sand.copy()
    damaged[1050:1056, 860:920] = (205, 205, 210)
    assert bf6(damaged) == VEHICLE
    # A light strip anywhere else along the bar, with the left unlit, is no health bar.
    elsewhere = sand.copy()
    elsewhere[1050:1056, 980:1060] = (205, 205, 210)
    assert bf6(elsewhere) == FOOT
    assert bf6(cv2.resize(barred, (3840, 2160), interpolation=cv2.INTER_NEAREST)) == VEHICLE
    zoomed = vehicle.copy()
    zoomed[:, :200] = 5
    zoomed[:, -200:] = 5
    # The HUD is drawn over a sight's black edges.
    assert bf6(with_map_key(zoomed)) == ZOOMED
    # Dark edges round a dark middle: the deploy map - not a view of the level, whatever else shows.
    menu = np.full((1080, 1920, 3), 15, np.uint8)
    menu[300:780, 700:1220] = 60
    menu[:, :200] = 5
    assert bf6(menu) == SCREEN
    assert bf6(with_map_key(menu)) == SCREEN
    # A wall in shadow at both edges, but neither edge black: an ordinary view.
    shadow = frame.copy()
    shadow[:, :200] = 22
    shadow[:, -200:] = 25
    assert bf6(with_map_key(shadow)) == FOOT
    # A plain light patch where the keys go, without letters, is not a vehicle's.
    blank = frame.copy()
    blank[925:1010, 1035:1080] = 200
    assert bf6(blank) == FOOT


def test_vehicle_mask_and_settings_file(tmp_path):
    from heat3d_capture.locate.profiles import settings_fov

    game = PROFILES["bf6"]
    foot, car = game.mask(960, 540), game.mask(960, 540, "vehicle")
    assert foot[400, 480] and not car[400, 480]
    f = tmp_path / "PROFSAVE_profile"
    f.write_bytes(b"GstAudio.Volume 1\nGstRender.FieldOfViewVertical 69.000000\nGstRender.FieldOfViewVerticalVehicle 53.000000\n")
    got = settings_fov(str(f))
    assert got["vfov"] == 69.0 and got["vehicle_vfov"] == 53.0
    assert math.isclose(camera.hfov_from_vertical(69.0, 16 / 9), 101.4, abs_tol=0.1)


def test_vehicles_may_move_faster_than_players():
    times = np.arange(0, 10, 0.5)
    truth = _walk(times, (0, 3.5, 0), (20, 0, 0))  # 20 m/s, a vehicle
    rows = [Row(float(t), True, p.copy(), 0.0, 0.0, 0.9, 200, view="vehicle") for t, p in zip(times, truth)]
    out, report = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=30.0))
    assert report["outliers"] == 0 and report["lives"] == 1
    on_foot = [Row(r.time, True, r.position.copy(), 0.0, 0.0, 0.9, 200) for r in rows]
    _, report = build_track(on_foot, TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=30.0))
    # On foot nobody moves 20 m/s: every fix contradicts its neighbours.
    assert report["outliers"] == len(on_foot)


def test_sequence_follows_the_consistent_path_not_the_strongest_frame():
    from heat3d_capture.locate.sequence import decode

    times = list(np.arange(0, 10, 0.5))
    truth = _walk(np.array(times), (0, 1.6, 0), (3, 0, 0))
    rng = np.random.default_rng(2)
    cands = []
    for i, p in enumerate(truth):
        here = [(p + rng.normal(0, 0.1, 3), 40)]
        # A look-alike far away, stronger than the right place, in every third frame.
        if i % 3 == 0:
            here.insert(0, (np.array([200.0, 1.6, -80.0]) + rng.normal(0, 5, 3), 120))
        cands.append(here)
    picks = decode(times, cands, 8.0, 1.5)
    for i, (pick, p) in enumerate(zip(picks, truth)):
        assert pick.index is not None
        assert np.linalg.norm(cands[i][pick.index][0] - p) < 1.0
        assert pick.support >= 2
    # A respawn: the path breaks and carries on from the new place.
    later = [(np.array([500.0, 1.6, 500.0]) + np.array([0, 0, 2.0]) * k, 60) for k in range(10)]
    picks = decode(times + [20 + 0.5 * k for k in range(10)], cands + [[c] for c in later], 8.0, 1.5)
    assert all(p.index == 0 for p in picks[-10:])


@pytest.mark.skipif(not _models_cached(), reason="DINOv2 / ALIKED / LightGlue weights not downloaded")
def test_field_of_view_is_found_from_the_frames(yard, tmp_path, renderer):
    """Frames rendered at 80 degrees, a locator told 90: the fit finds 80."""
    pytest.importorskip("kornia")
    from heat3d_capture.locate.database import BuildOptions, build
    from heat3d_capture.locate.localize import Locator, fit_hfov
    from heat3d_capture.locate.render import Light

    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    db = build(yard, tmp_path / "db", game, BuildOptions(spacing=6.0, yaw_step=60.0), on_progress=lambda s: None)
    locator = Locator(db, renderer.level, width=640, hfov=90.0)
    items = []
    for x, z, yaw in ((-10.0, 5.0, 30.0), (8.0, -6.0, 150.0), (2.0, 12.0, -100.0)):
        pose = camera.Pose(np.array([x, 1.6, z]), yaw, -5.0)
        locator.renderer.resize(640, 360)
        frame = locator.renderer.render(pose, 80.0, Light(sun=(-0.4, 0.8, 0.3))).color
        # The fix the run found: near the truth, as a solve under the wrong FOV would be.
        items.append((frame, None, camera.Pose(pose.position + np.array([0.3, 0.0, -0.2]), yaw + 2.0, -4.0)))
    est, each = fit_hfov(locator, items)
    locator.close()
    assert est is not None and len(each) >= 2
    assert abs(est - 80.0) < 2.0


@pytest.mark.skipif(not _models_cached(), reason="DINOv2 / ALIKED / LightGlue weights not downloaded")
def test_a_head_trains_and_describes(yard, tmp_path):
    """A few steps of training on the yard: the head is written, loads, and gives unit vectors of its size."""
    from heat3d_capture.locate import poses
    from heat3d_capture.locate.augment import game_look
    from heat3d_capture.locate.features import GlobalDescriptor
    from heat3d_capture.locate.level import load
    from heat3d_capture.locate.train import TrainOptions, train

    level = load(yard)
    places = poses.ground_points(level, 4.0, parts="ground:")
    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    out = train(yard, places, game, tmp_path / "head.pt", TrainOptions(steps=3, batch=4, dim=64), on_progress=lambda s: None)
    describe = GlobalDescriptor(head=str(out))
    rng = np.random.default_rng(0)
    pics = [rng.integers(0, 255, (180, 320, 3)).astype(np.uint8) for _ in range(2)]
    v = describe(pics)
    assert v.shape == (2, 64) and np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-4)
    # The game look keeps the picture's size and type.
    looked = game_look(pics[0], np.full((180, 320), 10.0, np.float32), rng, vehicle=True)
    assert looked.shape == pics[0].shape and looked.dtype == np.uint8


def test_cut_outs_are_cut_out_and_the_navigation_mesh_is_not_drawn(tmp_path):
    pytest.importorskip("moderngl")
    from heat3d_capture.locate import poses
    from heat3d_capture.locate.level import load
    from heat3d_capture.locate.render import Light, Renderer

    from .locate_world import write_yard

    level = load(write_yard(tmp_path / "yard_extras.glb", extras=True))
    fence = next(m for m in level.materials if m.name == "structure:fence")
    assert fence.alpha == "MASK" and fence.cutoff == 0.5
    try:
        r = Renderer(level, 320, 180)
    except Exception as exc:
        pytest.skip(f"no OpenGL context: {exc}")
    # From the middle, eye height, looking south (+Z) through the fence, 12 m away, at the wall 20 m away.
    out = r.render(camera.Pose(np.array([0.0, 1.6, 0.0]), -90.0, 0.0), 60.0, Light.flat())
    depth = out.depth[60:120, 100:220]
    color = out.color[60:120, 100:220].reshape(-1, 3).astype(int)
    red = (color[:, 0] > 180) & (color[:, 1] < 80) & (color[:, 2] < 80)
    # The bars are drawn at the fence, the holes show the wall behind it.
    assert 0.1 < red.mean() < 0.9
    assert np.isclose(depth, 12.0, rtol=0.03).mean() > 0.1 and np.isclose(depth, 20.0, rtol=0.03).mean() > 0.1
    # The navigation mesh, 5 cm over the floor, is never drawn: straight down the floor is at the eye height.
    down = r.below(np.array([10.0, 1.6, 10.0]))
    assert down[0] == pytest.approx(1.6, rel=0.01)
    r.release()
    # Places from the navigation mesh stay off its hole round the middle; vehicles go on the ground.
    walk, cars = poses.places(level, 3.0, "auto")
    assert len(walk) > 20 and not ((np.abs(walk[:, 0]) < 3.5) & (np.abs(walk[:, 2]) < 3.5)).any()
    assert np.allclose(walk[:, 1], 0.05, atol=1e-3)
    assert cars is not None and np.allclose(cars[:, 1], 0.0, atol=1e-3)


def test_a_vehicle_is_ahead_of_and_below_its_camera():
    from heat3d_capture.locate.run import body

    game = PROFILES["bf6"].with_overrides(vehicle_offset=(6.0, 2.0))
    cam = np.array([10.0, 5.0, -3.0])
    # Looking along +X (yaw 0): the vehicle is 6 m further along X, 2 m lower.
    assert np.allclose(body(cam, 0.0, "vehicle", game, 1.0), [16.0, 3.0, -3.0])
    # Looking along -Z (yaw 90).
    assert np.allclose(body(cam, 90.0, "vehicle", game, 1.0), [10.0, 3.0, -9.0])
    # On foot and through a sight the camera is the eye.
    assert np.allclose(body(cam, 90.0, "foot", game, 1.0), cam)
    assert np.allclose(body(cam, 90.0, "zoomed", game, 1.0), cam)


@pytest.mark.skipif(not _models_cached(), reason="DINOv2 / ALIKED / LightGlue weights not downloaded")
def test_every_visual_fix_gets_a_check_picture(yard, tmp_path, renderer):
    """A folder of yard pictures through locate_frames: one check picture per visual row, named by its time."""
    cv2 = pytest.importorskip("cv2")
    import pyarrow.parquet as pq

    from heat3d_capture.locate.database import BuildOptions, build
    from heat3d_capture.locate.render import Light
    from heat3d_capture.locate.run import Options, locate_frames

    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    build(yard, tmp_path / "db", game, BuildOptions(spacing=5.0, yaw_step=45.0), on_progress=lambda s: None)
    shots = tmp_path / "shots"
    shots.mkdir()
    renderer.resize(640, 360)
    for k in range(4):
        pose = camera.Pose(np.array([-12.0 + 1.5 * k, 1.6, 17.0]), -60.0 + 5 * k, -3.0)
        cv2.imwrite(str(shots / f"{k:03d}.png"), renderer.render(pose, 90.0, Light(sun=(-0.4, 0.8, 0.3))).color[:, :, ::-1])
    files, summary = locate_frames(shots, tmp_path / "db", tmp_path / "run", game, Options(fps=1.0, width=640, hfov=90.0))
    table = pq.read_table(files[0]).to_pydict()
    visual = [t for t, s in zip(table["time"], table["source"]) if s == "visual"]
    pictures = sorted((tmp_path / "run.check").glob("*_visual.jpg"))
    assert visual and len(pictures) == len(visual) == summary["check_pictures"]
    assert all(c is not None for c, s in zip(table["cam_x"], table["source"]) if s == "visual")


def test_a_frame_read_back_by_its_time_is_the_frame_that_was_located(tmp_path):
    # Check pictures, the zoomed pass and training on real frames seek by a row's time; the run
    # must time each frame by its own timestamp, or they read back a different frame.
    cv2 = pytest.importorskip("cv2")
    from heat3d_capture.locate.run import frames, read_frames

    path = tmp_path / "clip.avi"
    out = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (64, 36))
    if not out.isOpened():
        pytest.skip("no video writer")
    for k in range(90):
        img = np.zeros((36, 64, 3), np.uint8)
        img[:, : (k % 64) + 1] = 200  # a bar as long as the frame's number
        out.write(img)
    out.release()
    got = list(frames(path, fps=4.0, start=0.5, seconds=1.5))
    assert len(got) >= 6 and abs(got[0][0] - 0.5) < 0.02
    back = dict(read_frames(path, [t for t, _ in got]))
    for t, rgb in got:
        assert np.abs(rgb.astype(int) - back[t].astype(int)).mean() < 2.0


def test_a_zoomed_view_is_solved_from_its_neighbours_seat(yard, tmp_path, renderer):
    """A frame through a 2x sight, from a seat a metre off and a direction 8 degrees off: direction and zoom are found."""
    pytest.importorskip("kornia")
    from heat3d_capture.locate.database import BuildOptions, build
    from heat3d_capture.locate.localize import Locator
    from heat3d_capture.locate.render import Light

    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    db = build(yard, tmp_path / "db", game, BuildOptions(spacing=6.0, yaw_step=60.0), on_progress=lambda s: None)
    locator = Locator(db, renderer.level, width=640, hfov=90.0)
    hfov = 2 * np.degrees(np.arctan(np.tan(np.radians(45.0)) / 2.0))  # 2x against 90 degrees
    pose = camera.Pose(np.array([-12.0, 1.6, 9.0]), -40.0, -3.0)
    locator.renderer.resize(640, 360)
    frame = locator.renderer.render(pose, hfov, Light(sun=(-0.4, 0.8, 0.3))).color
    fix, zoom = locator.locate_zoomed(frame, None, pose.position + np.array([0.8, 0.0, -0.6]), -32.0, 90.0, reach=2.0)
    locator.close()
    assert fix.pose is not None and fix.ok
    assert zoom is not None and abs(zoom - 2.0) < 0.2
    assert abs(fix.pose.yaw - pose.yaw) < 2.0 and abs(fix.pose.pitch - pose.pitch) < 2.0
    assert np.linalg.norm(fix.pose.position - pose.position) < 1.5


def test_neighbours_far_apart_in_time_do_not_vouch_for_a_fix():
    # At one frame in ten seconds a vehicle could be anywhere within hundreds of metres of its
    # neighbours: their agreeing says nothing, so it lends no support.
    from heat3d_capture.locate.sequence import decode

    times = [0.0, 10.0, 20.0]
    cands = [[(np.array([0.0, 0, 0]), 40)], [(np.array([120.0, 0, 0]), 40)], [(np.array([30.0, 0, 50.0]), 40)]]
    sparse = decode(times, cands, 30.0, 2.0)
    assert all(c.support == 0 for c in sparse)
    dense = decode([0.0, 1.0, 2.0], [[(np.array([0.0, 0, 0]), 40)], [(np.array([5.0, 0, 0]), 40)], [(np.array([10.0, 0, 0]), 40)]], 30.0, 2.0)
    assert dense[1].support == 2


def test_a_minimap_anchor_cuts_the_search_and_the_picture_still_places(yard, tmp_path, renderer):
    """With an anchored minimap the search is cut to a disc round it; the pose is the picture's, and says so."""
    cv2 = pytest.importorskip("cv2")
    import json

    import pyarrow as pa
    import pyarrow.parquet as pq

    from heat3d_capture.locate.database import BuildOptions, build
    from heat3d_capture.locate.render import Light
    from heat3d_capture.locate.run import Options, locate_frames

    game = PROFILES["generic"].with_overrides(hfov=90.0, eye_heights=(1.6,))
    build(yard, tmp_path / "db", game, BuildOptions(spacing=5.0, yaw_step=45.0), on_progress=lambda s: None)
    shots = tmp_path / "shots"
    shots.mkdir()
    renderer.resize(640, 360)
    poses = [camera.Pose(np.array([-12.0 + 1.5 * k, 1.6, 17.0]), -60.0 + 5 * k, -3.0) for k in range(3)]
    for k, pose in enumerate(poses):
        cv2.imwrite(str(shots / f"{k:03d}.png"), renderer.render(pose, 90.0, Light(sun=(-0.4, 0.8, 0.3))).color[:, :, ::-1])
    # The minimap: its own units (2 per metre), y north (= -z), 4 m off the truth; the anchor knows the scale and turn.
    xy = [((p.position[0] + 4.0) * 2.0, -(p.position[2] - 3.0) * 2.0) for p in poses]
    pq.write_table(pa.table({"time": [0.0, 1.0, 2.0], "x": [a for a, _ in xy], "y": [b for _, b in xy], "session": ["#01"] * 3}), tmp_path / "hud.parquet")
    (tmp_path / "anchor.json").write_text(json.dumps({"scale": 0.5, "rotation": [[1, 0], [0, -1]], "shift": [0.0, 0.0], "median": 3.0, "p90": 5.0, "pairs": 10}))
    alone, _ = locate_frames(shots, tmp_path / "db", tmp_path / "alone", game, Options(fps=1.0, width=640, hfov=90.0, checks=False))
    opts = Options(fps=1.0, width=640, hfov=90.0, minimap=str(tmp_path / "hud.parquet"), anchor=str(tmp_path / "anchor.json"), level_search=False)
    files, summary = locate_frames(shots, tmp_path / "db", tmp_path / "run", game, opts)
    table = pq.read_table(files[0]).to_pydict()
    free = pq.read_table(alone[0]).to_pydict()
    placed = [i for i, s in enumerate(table["source"]) if s == "visual+minimap-prior"]
    assert len(placed) >= 2 and summary["prior_radius_m"] == pytest.approx(35.0)
    # The prior only chose which views to try: where both runs placed a frame, they agree.
    for i in placed:
        if free["source"][i] == "visual":
            assert np.hypot(table["x_raw"][i] - free["x_raw"][i], table["z_raw"][i] - free["z_raw"][i]) < 0.5
    assert len(sorted((tmp_path / "run.check").glob("*_visual-prior.jpg"))) == len(placed)
    assert summary["minimap_share"] == 1.0


def _hud_events(path, events):
    import pyarrow as pa
    import pyarrow.parquet as pq

    pq.write_table(pa.table({"time": [t for t, _ in events], "event": [e for _, e in events]}), path)
    return path


def test_a_revive_keeps_the_life_and_a_deploy_starts_one(tmp_path):
    from heat3d_capture.locate.lives import frame_lives, read_lives

    lives = read_lives(str(_hud_events(tmp_path / "hud.parquet", [
        (0.0, "start"), (20.0, "downed"), (25.0, "revived"), (40.0, "death"), (55.0, "spawn"), (90.0, "end"),
    ])))
    assert len(lives.spans) == 2 and lives.downs == [(20.0, 25.0)]
    times = [10.0, 22.0, 30.0, 45.0, 60.0, 95.0]
    got = frame_lives(times, ["foot"] * len(times), lives)
    # Before and after the revive: one life; down, dead, deploying and after the end: no life.
    assert got[0] == got[2] == 0 and got[1] is None and got[3] is None and got[4] == 1 and got[5] is None
    # Long menus cut a life too.
    got = frame_lives([1.0, 2.0, 15.0, 30.0], ["foot", "screen", "screen", "foot"], lives)
    assert got[0] is not None and got[3] is not None and got[0] != got[3]


def test_a_jump_without_a_death_drops_the_weaker_fix_and_never_splits_the_life():
    times = np.arange(0, 10, 1.0)
    rows = []
    for i, t in enumerate(times):
        p = np.array([float(i), 1.6, 0.0])
        if i == 5:
            p = np.array([300.0, 1.6, 0.0])  # a look-alike far off, weaker than its neighbours
        rows.append(Row(float(t), True, p, 0.0, 0.0, 0.8, 40 if i == 5 else 120, play_life=0))
    out, report = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5))
    assert report["lives"] == 1
    assert not out[5].kept and all(out[i].kept for i in range(10) if i != 5)
    # A respawn in the footage's lives: the jump is free.
    rows = [Row(float(t), True, np.array([float(t) if t < 5 else 500.0 + t, 1.6, 0.0]), 0.0, 0.0, 0.8, 120, play_life=0 if t < 5 else 1)
            for t in times]
    out, report = build_track(rows, TrackOptions(max_speed=8.0, margin=1.5))
    assert report["lives"] == 2 and all(r.kept for r in out)


def test_two_strong_sides_of_a_jump_are_kept_and_marked():
    from heat3d_capture.locate.run import _decide_by_sequence

    rows, cands = [], []
    for i in range(12):
        t = float(i)
        p = np.array([t, 1.6, 0.0]) if i < 6 else np.array([400.0 + t, 1.6, 0.0])
        rows.append(Row(t, True, p.copy(), 0.0, 0.0, 0.95, 150, view="foot", cam=p.copy(), play_life=0))
        cands.append([(p.copy(), 150, 0.0, 0.0, 1.0, p.copy())])
    jumps = []
    _decide_by_sequence(rows, cands, TrackOptions(max_speed=8.0, margin=1.5), True, jumps)
    assert all(r.ok for r in rows)
    assert sum("jump without detected death" in (r.note or "") for r in rows) >= 4 and len(jumps) == 1


def test_foot_and_vehicle_frames_have_their_own_speed_limit():
    from heat3d_capture.locate.sequence import decode

    # 20 m in a second: a vehicle can, a player on foot cannot.
    times = [0.0, 1.0, 2.0]
    cands = [[(np.array([0.0, 0, 0]), 100)], [(np.array([20.0, 0, 0]), 100)], [(np.array([40.0, 0, 0]), 100)]]
    foot = decode(times, cands, [8.0, 8.0, 8.0], 1.5, lives=[0, 0, 0])
    car = decode(times, cands, [30.0, 30.0, 30.0], 1.5, lives=[0, 0, 0])
    assert sum(c.index is not None for c in foot) == 1
    assert all(c.index is not None for c in car)


def test_the_navigation_mesh_gives_the_floor_under_a_minimap_position(tmp_path):
    from heat3d_capture.locate.level import load

    level = load(write_yard(tmp_path / "yard.glb", extras=True))
    assert level.floors_at(-15.0, 15.0) == pytest.approx([0.05], abs=0.01)
    # The square round the middle has no navigation mesh: no floor to give.
    assert level.floors_at(0.0, 0.0) == []


def test_destructible_parts_are_known_to_the_render_and_can_be_knocked_down(tmp_path):
    """A part tagged destructible shows in the render's mask; training can replace it with rubble."""
    pytest.importorskip("moderngl")
    from heat3d_capture.locate.augment import destroyed
    from heat3d_capture.locate.level import _destructible, load
    from heat3d_capture.locate.render import Renderer

    # How an export tags it: by name, or in extras.
    assert _destructible("destructible:wall", {}, {}, {})
    assert _destructible("Wall_A (destructible)", {}, {}, {})
    assert _destructible("structure:wall", {"extras": {"destructible": True}}, {}, {})
    assert not _destructible("structure:wall", {}, {}, {})
    level = load(write_yard(tmp_path / "yard.glb"))
    assert not any(b.destructible for b in level.batches)
    crate = next(b.name for b in level.batches if not b.name.startswith("ground"))
    for b in level.batches:
        b.destructible = b.name == crate
    try:
        r = Renderer(level, 320, 180)
    except Exception as exc:
        pytest.skip(f"no OpenGL context: {exc}")
    img = r.render(camera.Pose(np.array([-10.0, 1.6, -10.0]), 45.0, -5.0), 90.0)
    r.release()
    assert img.destructible is not None and img.destructible.any() and not img.destructible.all()
    out = destroyed(img.color, img.destructible, np.random.default_rng(0), share=1.0)
    assert (out[img.destructible] != img.color[img.destructible]).any()
    assert (out[~img.destructible] == img.color[~img.destructible]).all()


def test_a_short_pause_in_play_is_not_a_new_life(tmp_path):
    from heat3d_capture.locate.lives import read_lives

    lives = read_lives(str(_hud_events(tmp_path / "hud.parquet", [(0.0, "start"), (50.0, "end"), (56.0, "spawn"), (90.0, "end"), (200.0, "start")])))
    assert lives.spans == [(0.0, 90.0), (200.0, np.inf)] and lives.life(60.0) == lives.life(10.0) == 0 and lives.life(150.0) is None


def test_anchor_warp_grid_and_local_corrections(tmp_path):
    """A grid places points inside it (bilinear), the similarity outside; corrections stay local in time."""
    import json

    from heat3d_capture.locate.track import read_anchor

    # Similarity: level = 2 * (x, -y). Grid over x, y in 0..20 (step 10): the same, plus 3 m east.
    xs, ys = np.arange(0, 30, 10.0), np.arange(0, 30, 10.0)
    gx, gy = np.meshgrid(xs, ys)
    d = {"scale": 2.0, "rotation": [[1, 0], [0, -1]], "shift": [0, 0], "median": 1.0, "p90": 2.0, "pairs": 10,
         "grid": {"x0": 0.0, "y0": 0.0, "step": 10.0, "nx": 3, "ny": 3, "x": (2 * gx + 3).tolist(), "z": (-2 * gy).tolist()}}
    (tmp_path / "a.json").write_text(json.dumps(d))
    an = read_anchor(str(tmp_path / "a.json"))
    assert np.allclose(an.to_level(np.array([5.0, 15.0])), [13.0, -30.0])
    assert np.allclose(an.to_level(np.array([50.0, 5.0])), [100.0, -10.0])  # off the grid: the similarity
    an.corrections += [(10.0, 4.0, 0.0), (12.0, 6.0, 0.0), (14.0, 5.0, 0.0)]
    shift, spread = an.correction(20.0)
    assert np.allclose(shift, [5.0, 0.0]) and spread is not None
    # Far off in time: no correction at all, not the whole clip's.
    shift, spread = an.correction(500.0)
    assert np.allclose(shift, 0.0) and spread is None


def _blob_world(seed: int = 3, n: int = 260, size: float = 600.0):
    """Discs and boxes standing on flat ground: (x, z, radius, height) in metres, level frame."""
    rng = np.random.default_rng(seed)
    return [(float(rng.uniform(20, size - 20)), float(rng.uniform(20, size - 20)), float(rng.uniform(3, 9)), float(rng.uniform(4, 12))) for _ in range(n)]


def test_refmap_places_a_drawn_map_on_the_level():
    """A north-up map drawn of the level's raised things at 0.5 m a pixel is placed to within a couple of metres."""
    cv2 = pytest.importorskip("cv2")
    from heat3d_capture.locate.refmap import TopDown, calibrate

    world = _blob_world()
    mpp = 0.656
    W = H = int(600 / mpp)
    height = np.full((H, W), 100.0, np.float32)
    for x, z, r, h in world:
        cv2.circle(height, (int(x / mpp), int(z / mpp)), int(r / mpp), 100.0 + h, -1)
    top = TopDown(np.zeros((H, W, 3), np.uint8), height, 0.0, 0.0, mpp)
    # The map: 0.5 m a pixel, showing x 100..500, z 120..420; raised things lighter than the ground.
    s, ox, oz = 0.5, 100.0, 120.0
    pic = np.full((int(300 / s), int(400 / s), 3), 60, np.uint8)
    for x, z, r, h in world:
        cv2.circle(pic, (int((x - ox) / s), int((z - oz) / s)), int(r / s), (120, 120, 120), -1)
    cal = calibrate(top, pic, scales=[0.48, 0.49, 0.50, 0.51, 0.52], turns=(0,))
    assert cal is not None and cal.inliers >= 6
    for u, v in ((0, 0), (800, 600), (400, 300)):
        want = np.array([ox + u * s, oz + v * s])
        assert np.linalg.norm(cal.apply(np.array([u, v]))[0] - want) < 2.5


def test_minimap_registered_to_the_reference_map():
    """A turned, zoomed crop of the reference map is placed back: position, heading and zoom."""
    cv2 = pytest.importorskip("cv2")
    from heat3d_capture.locate.refmap import MinimapRegistrar, RefMap, register_minimaps

    rng = np.random.default_rng(5)
    # A map-like picture: grey-blue ground with lighter roads and blocks, at 0.5 m a pixel.
    img = np.full((1400, 1400, 3), (70, 60, 50), np.uint8)
    for _ in range(900):
        x, y = rng.integers(0, 1400, 2)
        w, h = rng.integers(6, 40, 2)
        c = int(rng.integers(90, 170))
        cv2.rectangle(img, (int(x), int(y)), (int(x + w), int(y + h)), (c, c, c - 10), -1)
    for _ in range(60):
        p = rng.integers(0, 1400, 4)
        cv2.line(img, (int(p[0]), int(p[1])), (int(p[2]), int(p[3])), (150, 145, 140), 5)
    ref = RefMap(img, np.ones(img.shape[:2], bool), -300.0, -200.0, 0.5)
    reg = MinimapRegistrar(ref, (0.5, 0.5), None, work=296)

    def minimap(cx: float, cz: float, heading: float, zoom: float) -> np.ndarray:
        # Minimap pixel (u, v) -> reference pixel: turned so the heading points up, `zoom` m a pixel.
        k = zoom / ref.mpp
        th = math.radians(heading)
        R = k * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        c = ref.to_pixel(np.array([cx, cz]))[0]
        A = np.c_[R, c - R @ np.array([148.0, 148.0])]
        return cv2.warpAffine(img, cv2.invertAffineTransform(A), (296, 296), flags=cv2.INTER_AREA)

    frames = [(0.0, minimap(50.0, 80.0, 30.0, 0.6)), (0.5, minimap(52.0, 78.0, 35.0, 0.62)), (1.0, minimap(54.0, 76.0, 40.0, 0.8))]
    fixes = register_minimaps(frames, reg)
    assert len(fixes) == 3
    for f, (cx, cz, hd, zm) in zip(fixes, ((50, 80, 30, 0.6), (52, 78, 35, 0.62), (54, 76, 40, 0.8))):
        assert np.linalg.norm(f.position - [cx, cz]) < 1.5
        assert abs((f.heading - hd + 180) % 360 - 180) < 2.0
        assert abs(f.zoom - zm) < 0.03


def test_hud_fill_moves_the_mosaic_onto_reference_fixes():
    """Gaps in the reference-map reading are filled from the HUD track, shifted by the nearby fixes' offset."""
    from heat3d_capture.locate.refmap import MinimapFix, fill_from_hud
    from heat3d_capture.locate.track import Anchor, Minimap, Similarity

    t = np.arange(0.0, 60.0, 0.5)
    true = np.c_[t * 2.0, 100.0 - t]  # level x, z
    # The HUD's own track: x east, y north (= -z), off by 7 m east everywhere.
    hud = Minimap(t, np.c_[true[:, 0] - 7.0, -true[:, 1]], np.zeros(len(t)), np.zeros(len(t), int))
    anchor = Anchor(Similarity(1.0, np.array([[1.0, 0.0], [0.0, -1.0]]), np.zeros(2), 0.0, 1, 1), 1.0, 2.0, 1)
    fixes = [MinimapFix(float(ti), p.copy(), 0.0, 0.68, 30, 0.8) for ti, p in zip(t, true) if ti < 20.0]
    filled = fill_from_hud(fixes, hud, anchor, 0.5, within=60.0)
    assert len(filled) == int((t > 19.5 + 0.6).sum())  # within 0.6 s of a fix counts as placed
    for f in filled:
        assert f.source == "hud"
        assert np.linalg.norm(f.position - true[int(round(f.t / 0.5))]) < 1e-6
    # Beyond `within` of every fix: nothing.
    assert not [f for f in fill_from_hud(fixes, hud, anchor, 0.5, within=10.0) if f.t > 30.0]


def _search_world(frames=60, seed=0):
    """A square of views with random descriptors, a walk through it, and frames that resemble the right view only a little."""
    rng = np.random.default_rng(seed)
    side = 40
    x, z = np.meshgrid(np.arange(side) * 24.0, np.arange(side) * 24.0, indexing="ij")
    places = np.c_[x.ravel(), z.ravel()]
    d = rng.normal(size=(len(places), 64))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    walk = np.array([[10 + k // 2, 10 + k // 3] for k in range(frames)])
    truth = walk[:, 0] * side + walk[:, 1]
    q = 0.28 * d[truth] + rng.normal(size=(frames, 64)) / 8.0
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return d, q, places, truth


def test_a_run_of_frames_finds_a_place_no_single_frame_shows():
    from heat3d_capture.locate.search import SearchOptions, along_lives

    d, q, places, truth = _search_world()
    times = [2.0 * k for k in range(len(q))]
    lists = along_lives(d, q, places, None, times, ["foot"] * len(q), [0] * len(q), 8, SearchOptions(vehicle_speed=20.0))
    alone = sum(int(t in np.argsort(-(d @ f))[:8]) for f, t in zip(q, truth))
    along = sum(int(t in s) for s, t in zip(lists, truth))
    assert along > alone + 10 and along >= 0.8 * len(q)


def test_a_view_like_every_frame_does_not_take_the_shortlist():
    from heat3d_capture.locate.search import SearchOptions, along_lives

    d, q, places, truth = _search_world()
    # One view that resembles every frame more than the right one does.
    common = np.random.default_rng(1).normal(size=d.shape[1])
    common /= np.linalg.norm(common)
    q = q + 0.9 * common
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    d[5] = common
    assert all(int(np.argmax(d @ f)) == 5 for f in q)
    times = [2.0 * k for k in range(len(q))]
    lists = along_lives(d, q, places, None, times, ["foot"] * len(q), [0] * len(q), 4, SearchOptions())
    assert sum(5 in s[:1] for s in lists) == 0
    assert sum(int(t in s) for s, t in zip(lists, truth)) >= 0.7 * len(q)


def test_the_search_stays_in_its_class_and_its_life():
    from heat3d_capture.locate.search import SearchOptions, along_lives, merge

    d, q, places, _ = _search_world(frames=24)
    vehicle = np.arange(len(d)) % 2 == 0
    views = ["vehicle" if k % 2 else "foot" for k in range(len(q))]
    lives = [None if k < 2 else 0 if k < 12 else 1 for k in range(len(q))]
    lists = along_lives(d, q, places, vehicle, [2.0 * k for k in range(len(q))], views, lives, 6, SearchOptions())
    assert lists[0] == [] and lists[1] == []
    for s, v in zip(lists[2:], views[2:]):
        assert s and all(bool(vehicle[i]) == (v == "vehicle") for i in s)
    assert merge([1, 2, 3], [2, 9], 4) == [1, 2, 9, 3] and merge([1, 2, 3], [2, 9], 2) == [1, 2]


def _accept_rows(paths, life=0):
    rows, cands = [], []
    for k, frame in enumerate(paths):
        rows.append(Row(time=2.0 * k, ok=bool(frame), view="vehicle", play_life=life, speed_limit=15.0))
        cands.append([(np.array(p, float), inl, 0.0, 0.0, 2.0, np.array(p, float), spread) for p, inl, spread in frame])
        if frame:
            rows[-1].position = np.array(frame[0][0], float)
    return rows, cands


def test_a_look_alike_with_many_inliers_on_one_patch_is_not_believed():
    from heat3d_capture.locate.run import _accept_along_lives

    rows, cands = _accept_rows([[((10.0 * k, 0, 0), 120, 0.3)] for k in range(8)])
    # A stack of containers elsewhere: the frame's strongest solve by far, on a few cells of the frame.
    cands[4].insert(0, (np.array([500.0, 0, 500.0]), 600, 0.0, 0.0, 2.0, np.array([500.0, 0, 500.0]), 0.06))
    rows[4].position = cands[4][0][0].copy()
    report = _accept_along_lives(rows, cands, TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=15.0), True)
    assert report["believed"] == 8
    assert np.allclose(rows[4].position, [40.0, 0, 0])


def test_a_strong_fix_without_agreeing_neighbours_is_not_believed():
    from heat3d_capture.locate.run import _accept_along_lives

    # A lone covering fix, and two that contradict each other, far from anything else in the life.
    far = [[], [((0, 0, 0), 500, 0.4)], [], [], [], [], [], [], [((900, 0, 0), 500, 0.4)], [], [], [], [], [((0, 0, 900), 500, 0.4)]]
    rows, cands = _accept_rows(far)
    report = _accept_along_lives(rows, cands, TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=15.0), True)
    assert report["believed"] == 0 and not any(r.ok for r in rows)
    assert all("not believed" in r.note for r in rows if r.position is not None)


def test_candidates_below_the_inlier_floor_do_not_vouch():
    from heat3d_capture.locate.run import _accept_along_lives

    # Three frames in a row agree, but the outer two are weak: nothing vouches for the middle one.
    rows, cands = _accept_rows([[((0, 0, 0), 12, 0.3)], [((10, 0, 0), 300, 0.3)], [((20, 0, 0), 12, 0.3)]])
    report = _accept_along_lives(rows, cands, TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=15.0), True)
    assert report["believed"] == 0


def test_the_depth_test_sets_aside_a_fix_on_one_surface_and_keeps_a_lone_one_that_is_not():
    from heat3d_capture.locate.run import _accept_along_lives

    def rows_with(depth):
        rows, cands = _accept_rows([[((0, 0, 0), 500, 0.3)]])
        cands[0] = [c + (depth,) for c in cands[0]]
        return rows, cands

    opts = TrackOptions(max_speed=8.0, margin=1.5, vehicle_speed=15.0)
    rows, cands = rows_with(1.2)
    assert _accept_along_lives(rows, cands, opts, True, 0, 1.5)["believed"] == 0 and not rows[0].ok
    rows, cands = rows_with(4.0)
    assert _accept_along_lives(rows, cands, opts, True, 0, 1.5)["believed"] == 1 and rows[0].ok
    # As it was without the options: alone, it has no neighbours to agree with it.
    rows, cands = rows_with(4.0)
    assert _accept_along_lives(rows, cands, opts, True)["believed"] == 0


def test_a_grown_fit_on_one_surface_is_not_taken():
    from heat3d_capture.locate.camera import Pose
    from heat3d_capture.locate.localize import Fix
    from heat3d_capture.locate.profiles import profile
    from heat3d_capture.locate.run import _grown_body

    game = profile("bf6")
    fit = lambda depth: Fix(True, Pose(np.array([0.0, 2.0, 0.0]), 0.0, 0.0), inliers=500, spread=0.3, depth_range=depth)
    row = Row(time=0.0, ok=False, view="foot")
    near = np.zeros(3)
    assert _grown_body(fit(1.2), row, near, 50.0, game, 1.0, 25, 0.12, 1.5) is None
    assert _grown_body(fit(4.0), row, near, 50.0, game, 1.0, 25, 0.12, 1.5) is not None
    assert _grown_body(fit(1.2), row, near, 50.0, game, 1.0, 25, 0.12) is not None


def test_the_depth_range_of_a_solve():
    from heat3d_capture.locate.localize import _depth_range

    at = np.zeros(3)
    wall = np.array([[10.0, y, 0.0] for y in np.linspace(-1, 1, 50)])
    far_and_near = np.array([[d, 0.0, 0.0] for d in np.linspace(5, 200, 50)])
    assert _depth_range(wall, at) < 1.1
    assert _depth_range(far_and_near, at) > 5
    assert _depth_range(None, at) == 0.0


def test_a_job_gives_way_to_a_file_or_a_process(tmp_path, monkeypatch):
    from heat3d_capture.locate import run
    from heat3d_capture.locate.run import give_way

    flag = tmp_path / "wanted"
    assert give_way([str(flag)]) is None
    flag.write_text("")
    assert "exists" in give_way([str(flag)])
    assert give_way([], ["SomeGame"], names=["python.exe", "explorer.exe"]) is None
    assert "somegame_x64.exe" in give_way([], ["SomeGame"], names=["python.exe", "somegame_x64.exe"])
    # A process only counts by the start of its name.
    assert give_way([], ["game"], names=["mygame.exe"]) is None
    # Not knowing what runs is a reason to stop, not to carry on.
    monkeypatch.setattr(run, "_listed", None)
    monkeypatch.setattr(run, "_process_names", lambda: None)
    assert "cannot be listed" in give_way([], ["SomeGame"])
    assert give_way() is None


def test_the_process_list_is_kept_for_a_while_and_a_failure_is_not(monkeypatch):
    from heat3d_capture.locate import run
    from heat3d_capture.locate.run import give_way

    calls = []
    answers = [None, ["python.exe"], ["somegame.exe"]]

    def listed():
        calls.append(1)
        return answers[len(calls) - 1]

    now = [100.0]
    monkeypatch.setattr(run, "_listed", None)
    monkeypatch.setattr(run, "_process_names", listed)
    monkeypatch.setattr(run.time, "monotonic", lambda: now[0])
    assert "cannot be listed" in give_way([], ["somegame.exe"])
    assert give_way([], ["somegame.exe"]) is None
    assert len(calls) == 2
    # Within the time: not listed again, and a flag file is still read every time.
    now[0] += run.PROCESSES_FOR - 1
    assert give_way([], ["somegame.exe"]) is None
    assert len(calls) == 2
    now[0] += 2
    assert "somegame.exe" in give_way([], ["somegame.exe"])
    assert len(calls) == 3


def test_a_frame_can_be_stopped_between_its_renders():
    from types import SimpleNamespace

    from heat3d_capture.locate.camera import Pose
    from heat3d_capture.locate.localize import Locator

    class Stop(Exception):
        pass

    rendered = []
    ticks = []

    def between():
        ticks.append(1)
        if len(ticks) == 3:
            raise Stop

    fake = SimpleNamespace(
        width=64,
        hfov=90.0,
        light=None,
        normalisation="none",
        between=between,
        renderer=SimpleNamespace(resize=lambda w, h: None, render=lambda *a: rendered.append(a) or None),
        matcher=SimpleNamespace(detect=lambda rgb, mask: SimpleNamespace(xy=np.zeros((50, 2)))),
        _solve=lambda *a: None,
    )
    seeds = [Pose(np.zeros(3), 0.0, 0.0)] * 8
    with pytest.raises(Stop):
        Locator._locate(fake, np.zeros((36, 64, 3), np.uint8), None, None, None, seeds)
    assert len(rendered) == 2


def test_this_systems_process_list_holds_this_process():
    import sys
    from pathlib import Path

    from heat3d_capture.locate.run import _process_names

    names = _process_names()
    assert names and Path(sys.executable).name.lower() in {n.lower() for n in names}


def test_a_state_is_written_whole_and_read_back(tmp_path):
    from heat3d_capture.locate.run import _read_state, _write_state

    path = tmp_path / "run.checkpoint"
    assert _read_state(path) is None
    state = {"rows": [Row(time=2.0, ok=True, view="foot", position=np.array([1.0, 2.0, 3.0]))], "phase": "frames"}
    _write_state(path, state)
    back = _read_state(path)
    assert back["phase"] == "frames" and np.allclose(back["rows"][0].position, [1.0, 2.0, 3.0])
    assert not path.with_name(path.name + ".part").exists()
