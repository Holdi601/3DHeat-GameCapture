"""
The minimap track, against a drawn level where the answer is known.

The tracker never sees the level: it gets the turning, overlaid minimaps a
walk through it produces, and has to say where the walk went. Its answer is in
its own mosaic's coordinates, which differ from the level's by a turn and a
shift (whatever the first minimap was), so the check fits that one similarity
and then asks how far each point is from the truth. A track that drifts, or a
loop that does not close, fails that however good each step looked.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from heat3d_capture.hud.minimap import MinimapTracker, key_present, overlay_mask  # noqa: E402

from . import hud_synth as hs  # noqa: E402


@pytest.fixture(scope="module")
def world() -> np.ndarray:
    return hs.level()


def fit(est: np.ndarray, true: np.ndarray) -> tuple[np.ndarray, float]:
    """Best similarity from estimated to true points (Umeyama); the residuals, and the scale."""
    me, mt = est.mean(0), true.mean(0)
    e, t = est - me, true - mt
    U, S, Vt = np.linalg.svd(t.T @ e / len(e))
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1, d])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (e ** 2).sum(1).mean()
    mapped = (s * (R @ e.T)).T + mt
    return np.hypot(*(mapped - true).T), float(s)


def run(views, **kw) -> MinimapTracker:
    tr = MinimapTracker(hs.PLAYER, hs.KEY, **kw)
    for i, v in enumerate(views):
        tr.add(i * 0.2, v.image)
    return tr


def test_a_loop_is_tracked_and_closes(world):
    # A square walk that ends where it began, the minimap turning at each corner.
    views = hs.walk(world, (1200, 1300), [(0, 240), (90, 240), (90, 240), (90, 240)])
    tr = run(views)
    assert tr.placed == len(views)
    assert len({p.island for p in tr.track}) == 1
    est = np.array([(p.x, p.y) for p in tr.track])
    true = np.array([(v.x, v.y) for v in views])
    err, scale = fit(est, true)
    # Within two level pixels everywhere: the minimap is drawn at one level pixel per pixel.
    assert err.max() < 2.0, err.max()
    assert scale == pytest.approx(1.0, abs=0.02)
    # The loop closes: the last fix lands where the first did.
    assert math.hypot(*(est[-1] - est[0])) < 2.5


def test_heading_follows_the_view(world):
    views = hs.walk(world, (900, 900), [(0, 60), (70, 60), (-140, 60)])
    tr = run(views)
    # Mosaic headings differ from the truth by one constant: the first minimap's turn.
    diffs = [((p.heading - v.heading + 180) % 360) - 180 for p, v in zip(tr.track, views)]
    offset = diffs[0]
    assert max(abs(((d - offset + 180) % 360) - 180) for d in diffs) < 1.5


def test_standing_still_stays_put(world):
    # The view turns on the spot and the overlays move; the position must not.
    views = [hs.View(hs.minimap(world, 1500, 1100, h, t=i * 0.2), 1500, 1100, h)
             for i, h in enumerate(np.linspace(0, 300, 40))]
    tr = run(views)
    est = np.array([(p.x, p.y) for p in tr.track])
    assert np.hypot(*(est - est.mean(0)).T).max() < 1.0


def test_zoom_changes_are_followed(world):
    # A vehicle zooms the minimap out: the track keeps its scale on the mosaic.
    near = hs.walk(world, (1000, 1400), [(0, 120)])
    far = hs.walk(world, (near[-1].x, near[-1].y), [(30, 160)], zoom=0.75)
    views = near + far
    tr = run(views)
    assert tr.placed == len(views)
    est = np.array([(p.x, p.y) for p in tr.track])
    true = np.array([(v.x, v.y) for v in views])
    err, _ = fit(est, true)
    assert err.max() < 3.0
    zooms = [p.scale for p in tr.track]
    assert zooms[-1] / zooms[0] == pytest.approx(1 / 0.75, rel=0.05)


def test_a_spawn_elsewhere_starts_an_island_that_joins_when_paths_meet(world):
    first = hs.walk(world, (700, 700), [(0, 200), (90, 200)])
    # Dead; back in play far away, on ground not seen yet.
    second = hs.walk(world, (1500, 700), [(-90, 0)])[:1]
    # ...and walking back towards where the first life went.
    x, y = second[0].x, second[0].y
    back = hs.walk(world, (x, y), [(-90, 0), (0, 600)])
    tr = MinimapTracker(hs.PLAYER, hs.KEY)
    t = 0.0
    for v in first:
        tr.add(t, v.image)
        t += 0.2
    tr.break_track()
    for v in second + back:
        tr.add(t, v.image)
        t += 0.2
    islands = {p.island for p in tr.track}
    assert len(islands) == 1, "the second life's island was not joined to the first"
    views = first + second + back
    est = np.array([(p.x, p.y) for p in tr.track])
    true = np.array([(v.x, v.y) for v in views])
    err, _ = fit(est, true)
    assert np.median(err) < 2.0 and err.max() < 4.0


def test_the_key_hint_says_in_play(world):
    on = hs.minimap(world, 1200, 1200, 30)
    assert key_present(on, hs.KEY)
    assert not key_present(hs.minimap(world, 1200, 1200, 30, overlays=False), hs.KEY)
    assert not key_present(np.zeros_like(on), hs.KEY)
    assert not key_present(np.full_like(on, 220), hs.KEY)


def test_overlays_are_masked():
    img = np.zeros((hs.SIZE, hs.SIZE, 3), np.uint8)
    img[:] = (58, 48, 40)
    cv2.rectangle(img, (50, 50), (70, 70), (40, 90, 230), -1)  # an orange marker
    cv2.rectangle(img, (200, 200), (220, 220), (250, 250, 250), -1)  # a white icon
    mask = overlay_mask(img, hs.PLAYER, hs.KEY)
    assert mask[60, 60] == 0 and mask[210, 210] == 0
    assert mask[120, 40] == 255
    # The player's own marker and the cone above it are always masked.
    px, py = int(hs.PLAYER[0] * hs.SIZE), int(hs.PLAYER[1] * hs.SIZE)
    assert mask[py, px] == 0 and mask[py - 60, px] == 0
