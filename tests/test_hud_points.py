"""
The points popup and the death screens, drawn here with made-up texts, read back into the player's own events.

Most of these hand the parser the text boxes an OCR would have found, so they
test what is this package's own - the table of tags and its tolerance of the
recogniser's slips, the popup's rows, counting actions as a popup grows,
telling one popup from the next, deaths from revives - without depending on
how a recogniser reads a drawn font. One test runs the real OCR over a drawn
popup and is skipped where it is not installed.
"""

from __future__ import annotations

import pytest

cv2 = pytest.importorskip("cv2")

from heat3d_capture.hud import screens  # noqa: E402
from heat3d_capture.hud.killfeed import ENEMY, FRIENDLY  # noqa: E402
from heat3d_capture.hud.ocr import Text  # noqa: E402
from heat3d_capture.hud.points import PopupRead, Popups, Tag, parse, read_tags, read_title  # noqa: E402

from . import hud_synth as hs  # noqa: E402


def tags(raw: str) -> list[tuple[str, int | None]] | None:
    found = read_tags(raw)
    return None if found is None else [(t.event, t.count) for t in found]


def test_tags_and_their_counts():
    assert tags("KILL") == [("kill", 1)]
    assert tags("KILL x3") == [("kill", 3)]
    assert tags("SUPPLYX2") == [("resupply", 2)]
    assert tags("CAPTURING x5") == [("capturing", 5)]
    assert tags("VEHICLE DESTROYED") == [("vehicle_destroyed", 1)]
    assert tags("VEHICLE DESTROYED SUPPORT") == [("vehicle_destroyed_assist", 1)]
    assert tags("SQUAD DAMAGE ASSIST") == [("assist", 1)]
    # A headshot kill shows HEADSHOT where KILL would be.
    assert tags("HEADSHOT") == [("kill", 1)]


def test_the_recognisers_slips_are_forgiven():
    # Q read as O, letters lost at an edge, I for L, a stray sign before the count.
    assert tags("SOUAD REVIVE") == [("reviving", 1)]
    assert tags("EHICLE DESTROYED") == [("vehicle_destroyed", 1)]
    assert tags("KILI") == [("kill", 1)]
    assert tags("SUPPLY#2") == [("resupply", 2)]
    assert tags("SUPPLXX2") == [("resupply", 2)]


def test_tags_run_together_are_taken_apart():
    assert tags("CAPTUREDORDERCOMPLETED") == [("capture", 1), ("order", 1)]
    assert tags("KILL X2VEHICLE DESTROYED") == [("kill", 2), ("vehicle_destroyed", 1)]
    assert tags("DAMAGE ASSISTOFFENSIVE") == [("assist", 1), ("offensive", 1)]


def test_other_text_is_not_mistaken_for_a_tag():
    # Names, tank-sight labels, words in other languages: not tags, and not guessed.
    for raw in ("Made_Up_Foe", "SNP", "ABSCHUSS", "UNTERSTUETZUNG", "ELIMINATION", "HELLO WORLD", "BALLISTIC"):
        assert read_tags(raw) is None, raw


def test_titles():
    assert read_title("DOUBLEKILL") == ("multi_kills", "DOUBLE KILL", 2)
    assert read_title("TANKBUSTER") == ("ribbon", "TANK BUSTER", None)
    assert read_title("MADE UP RIBBON7") == ("ribbon", "MADE UP RIBBON 7", None)


def read(t, img_boxes) -> PopupRead:
    img, boxes = img_boxes
    return parse(t, img, [Text(*b, 0.9) for b in boxes], origin=hs.POPUP_ORIGIN, scale=hs.POPUP_SCALE)


def test_a_popup_is_read_by_its_rows():
    r = read(1.0, hs.popup(["KILL x2", "VEHICLE DESTROYED"], 300, name="Made_Up_Foe", title="DOUBLE KILL", icons=3))
    assert sorted((g.event, g.count) for g in r.tags) == [("kill", 2), ("vehicle_destroyed", 1)]
    assert r.total == 300 and r.name == "Made_Up_Foe" and r.side == ENEMY
    assert r.titles == ["DOUBLE KILL"]
    r = read(1.0, hs.popup(["SUPPLY x3", "REVIVE"], 80, name="Made_Up_Mate", name_colour=hs.CYAN, background=(200, 200, 205)))
    assert r.side == FRIENDLY and r.total == 80


def test_an_unknown_tag_is_kept_with_its_text():
    r = read(1.0, hs.popup(["KILL", "MADE UP BONUS"], 150, name="Made_Up_Foe"))
    assert sorted((g.event, g.text) for g in r.tags) == [("kill", "KILL"), ("points", "MADE UP BONUS")]


def test_text_without_a_popup_is_not_read_as_one():
    img, boxes = hs.popup([], None, name="Made_Up_Foe")
    boxes.append((400, 60, 470, 90, "SNP"))
    assert read(1.0, (img, boxes)).empty


def test_the_total_run_into_the_name_is_split_off():
    img, boxes = hs.popup(["SUPPLY"], None, name="Made_Up_Mate", name_colour=hs.CYAN)
    # The recogniser read the name and the total as one line.
    x0, _, _, _, _ = boxes[0]
    boxes.append((x0, 102, 900, 140, "Made_Up_Mate10"))
    r = read(1.0, (img, boxes))
    assert r.total == 10


def P(t, tags, total, name="", side=""):
    return PopupRead(t=t, tags=[Tag(e, x, c) for e, x, c in tags], total=total, name=name, side=side)


K = ("kill", "KILL")
VD = ("vehicle_destroyed", "VEHICLE DESTROYED")


def test_a_growing_popup_gives_each_action_once_when_it_came():
    p = Popups()
    reads = [
        P(10.0, [(*K, 1)], 100, "Foe_One", ENEMY),
        P(10.4, [(*K, 1)], 100, "Foe_One", ENEMY),
        P(10.8, [(*K, 2)], 200, "Foe_Two", ENEMY),
        P(11.2, [(*K, 2)], 200, "Foe_Two", ENEMY),
        # Lost for a moment (blur): the popup carries on, nothing counted twice.
        P(12.4, [(*K, 2), (*VD, 1)], 400),
        P(12.8, [(*K, 2), (*VD, 1)], 400),
        P(13.2, [(*K, 2), (*VD, 1)], 400),
        # Folded to one line, then gone.
        P(13.6, [(*VD, 1)], 400),
        P(14.0, [(*VD, 1)], 400),
    ]
    for r in reads:
        p.add(r)
    # A new popup later.
    for t in (30.0, 30.4, 30.8):
        p.add(P(t, [(*K, 1)], 100, "Foe_Three", ENEMY))
    events = p.finish()
    got = [(e.t, e.event, e.points, e.name) for e in events]
    assert got == [
        (10.0, "kill", 100, "Foe_One"),
        (10.8, "kill", 100, "Foe_Two"),
        (12.4, "vehicle_destroyed", 200, ""),
        (30.0, "kill", 100, "Foe_Three"),
    ]
    assert len(p.popups) == 2
    assert [p.total(x) for x in p.popups] == [400, 100]


def test_a_count_read_once_is_not_trusted():
    p = Popups()
    for t, c in ((1.0, 1), (1.4, 3), (1.8, 1), (2.2, 1)):
        p.add(P(t, [(*K, c)], 100))
    assert [e.event for e in p.finish()] == ["kill"]
    # Kept apart as weak, for another source to vouch for.
    assert [(e.t, e.weak) for e in p.finish(weak=True)] == [(1.0, False), (1.4, True), (1.4, True)]


def test_a_name_in_an_odd_colour_is_not_an_unknown_tag():
    img, boxes = hs.popup(["ENEMY SUPPRESSION"], 155, name="Made-Up", name_colour=hs.GREY)
    boxes = [b if b[4] != "Made-Up" else (*b[:4], "MADEUP") for b in boxes]
    r = read(1.0, (img, boxes))
    assert [g.event for g in r.tags] == ["suppression"]


def test_a_kind_that_comes_back_keeps_counting():
    # The tag row shows the last few kinds: SUPPLY slides out and comes back as x3.
    S = ("resupply", "SUPPLY")
    R = ("reviving", "REVIVE")
    p = Popups()
    for t, tags_, total in (
        (0.0, [(*S, 1)], 10), (0.4, [(*S, 1)], 10),
        (1.2, [(*S, 2)], 20), (1.6, [(*S, 2)], 20),
        (2.4, [(*R, 1), ("capturing", "CAPTURING", 1)], 120), (2.8, [(*R, 1), ("capturing", "CAPTURING", 1)], 120),
        (3.6, [(*S, 3), (*R, 1)], 130), (4.0, [(*S, 3), (*R, 1)], 130),
    ):
        p.add(P(t, tags_, total))
    events = p.finish()
    assert [e.event for e in events].count("resupply") == 3
    assert [(e.t, e.points) for e in events if e.event == "resupply"][-1] == (3.6, 10)


def test_unknown_tags_are_kept_and_cut_reads_of_known_ones_are_not():
    p = Popups()
    for t in (0.0, 0.4, 0.8):
        p.add(P(t, [(*VD, 1), ("points", "DESTROYED", 1), ("points", "MADE UP BONUS", 1)], 250))
    assert sorted((e.event, e.text) for e in p.finish()) == [("points", "MADE UP BONUS"), ("vehicle_destroyed", "VEHICLE DESTROYED")]


def test_titles_become_events_once():
    p = Popups()
    for t in (0.0, 0.4, 0.8, 1.2, 1.6):
        r = P(t, [(*K, 2)], 200)
        r.titles = ["DOUBLE KILL"] if t < 1.0 else ["TANKBUSTER"]
        p.add(r)
    got = sorted((e.event, e.text) for e in p.finish() if e.event != "kill")
    assert got == [("multi_kills", "DOUBLE KILL"), ("ribbon", "TANK BUSTER")]


def test_the_death_screens_words():
    assert screens.kinds(["REOUEST REVIVE", "SKIP (HOLD]", "MAN DOWN"]) == {screens.DOWN}
    assert screens.kinds(["F DAMAGE LOG"]) == {screens.CARD}
    assert screens.kinds(["YOU 1", "2 FOE"]) == {screens.CARD}
    assert screens.kinds(["DEPLOY"]) == {screens.DEPLOY}
    assert screens.kinds(["6/24", "KILL", "Made_Up_Name"]) == set()


def test_down_then_deploy_is_a_death_and_down_then_play_a_revive():
    D, C, Y = screens.DOWN, screens.CARD, screens.DEPLOY
    reads = []
    for i in range(150):
        t = round(i * 0.8, 1)
        ks: set[str] = set()
        if 10 <= t <= 16:
            ks = {D, C}  # down, then revived: play goes on
        elif 40 <= t <= 50:
            ks = {D, C}  # down, bled out
        elif 52 <= t <= 60:
            ks = {Y}
        elif 80 <= t <= 84:
            ks = {C}  # killed outright, then a long time out of play
        reads.append((t, ks))
    play = [(0.0, 51.0), (62.0, 85.0), (100.0, 119.0)]
    eps = screens.episodes(reads)
    screens.outcomes(eps, reads, play)
    assert [(round(e.start), e.outcome) for e in eps] == [(10, "revived"), (40, "death"), (80, "death")]
    assert eps[0].back == pytest.approx(16.8)


def test_real_ocr_reads_a_drawn_popup():
    pytest.importorskip("rapidocr_onnxruntime")
    from heat3d_capture.hud.killfeed import FeedReader
    from heat3d_capture.hud.ocr import Reader
    from heat3d_capture.hud.profiles import BF6
    from heat3d_capture.hud.run import _popup_filter

    img, _ = hs.popup(["KILL x2", "VEHICLE DESTROYED"], 300, name="MadeUpFoe", icons=2)
    region = BF6.region("points")
    reader = FeedReader(Reader(gpu=False))
    texts = reader.read(img, keep=_popup_filter(BF6.popup, region.box.x, region.box.y, region.scale))
    r = parse(1.0, img, texts, origin=hs.POPUP_ORIGIN, scale=hs.POPUP_SCALE, layout=BF6.popup)
    assert sorted((g.event, g.count) for g in r.tags) == [("kill", 2), ("vehicle_destroyed", 1)]
    assert r.total == 300


def test_the_own_lane_reads_popup_and_screens_in_one_pass():
    pytest.importorskip("rapidocr_onnxruntime")
    from collections import Counter

    import numpy as np

    from heat3d_capture.hud.ocr import Reader
    from heat3d_capture.hud.profiles import BF6
    from heat3d_capture.hud.run import OwnLane

    def words(text: str, size: tuple[int, int]) -> np.ndarray:
        img = np.full((size[1], size[0], 3), 50, np.uint8)
        if text:
            cv2.putText(img, text, (20, size[1] // 2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (235, 235, 235), 2, cv2.LINE_AA)
        return img

    down_size, card_size = BF6.region("down").size, BF6.region("card").size
    blank, _ = hs.popup([], None)
    shown, _ = hs.popup(["KILL"], 100, name="MadeUpFoe")
    lane = OwnLane(Reader(gpu=False), BF6, Counter())
    quiet = (words("", down_size), words("", card_size))
    lane.take(0.0, blank, *quiet, False)
    lane.take(0.4, blank, *quiet, False)
    # Nothing up: the first sample held back, the second read.
    assert [r.t for r in lane.reads.popups] == [0.4]
    lane.take(0.8, blank, *quiet, False)
    lane.take(1.2, shown, *quiet, False)
    # A popup: the held sample is read first.
    assert [r.t for r in lane.reads.popups] == [0.4, 0.8, 1.2]
    assert [(g.event, g.count) for g in lane.reads.popups[-1].tags] == [("kill", 1)]
    lane.take(1.6, blank, words("MAN DOWN", down_size), words("DAMAGE LOG", card_size), True)
    assert lane.reads.screens[-1] == (1.6, {screens.DOWN, screens.CARD})
