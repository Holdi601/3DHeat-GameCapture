"""
Kill-feed rows, drawn here with made-up names, read back into events.

Most of these give the parser the text boxes an OCR would have found, so they
test the parts that are this package's own - sides from colours, killer and
victim from layout, the marker, de-duplication across samples - without
depending on how a recogniser reads a drawn font. One test runs the real OCR
over a drawn row and is skipped where it is not installed.
"""

from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from heat3d_capture.hud.killfeed import (  # noqa: E402
    ENEMY,
    FRIENDLY,
    SQUAD,
    Feed,
    Gate,
    Row,
    classify_icons,
    parse_rows,
    text_colour,
)
from heat3d_capture.hud.ocr import Text, clean_name, similarity  # noqa: E402

from . import hud_synth as hs  # noqa: E402

PITCH, TEXT_H = 60.0, 28.0


def boxes(found) -> list[Text]:
    return [Text(x0, y0, x1, y1, text, 0.9) for x0, y0, x1, y1, text in found]


def test_sides_from_colours_on_dark_and_bright_backgrounds():
    for bg in ((40, 34, 30), (235, 232, 228), (120, 140, 160)):
        img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN, background=bg)
        k, v = boxes(found)
        assert text_colour(img, k)[0] == ENEMY, bg
        assert text_colour(img, v)[0] == FRIENDLY, bg
    img, found = hs.feed_row("Someone", "Me_Myself", hs.ORANGE, hs.PALE)
    assert text_colour(img, boxes(found)[1])[0] == SQUAD


def test_a_row_has_killer_victim_and_sides():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN)
    rows = parse_rows(img, boxes(found), pitch=PITCH, text_h=TEXT_H)
    assert len(rows) == 1
    r = rows[0]
    assert (r.killer, r.victim) == ("Made Up Name", "Other_Player7")
    assert (r.killer_side, r.victim_side) == (ENEMY, FRIENDLY)
    assert r.icon is not None and r.marker == ""


def test_the_skull_is_found():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN, skull=True)
    r = parse_rows(img, boxes(found), pitch=PITCH, text_h=TEXT_H)[0]
    assert r.marker == "skull"
    assert r.icon is not None


def test_small_lines_and_counters_are_not_names():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN)
    extra = [Text(800, 2, 900, 12, "cpu 150/6.3", 0.9), Text(10, 10, 60, 50, "gpu 1/2", 0.9)]
    rows = parse_rows(img, boxes(found) + extra, pitch=PITCH, text_h=TEXT_H)
    assert len(rows) == 1


def test_a_name_with_a_space_read_in_two_pieces_is_one_name():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN)
    (x0, y0, x1, y1, _), victim = found
    # The recogniser split the killer at its spaces.
    third = (x1 - x0) / 3
    pieces = [
        (x0, y0, x0 + third - 6, y1, "Made"),
        (x0 + third, y0, x0 + 2 * third - 6, y1, "Up"),
        (x0 + 2 * third, y0, x1, y1, "Name"),
    ]
    r = parse_rows(img, boxes(pieces + [victim]), pitch=PITCH, text_h=TEXT_H)[0]
    assert r.killer == "Made Up Name"


def _row(k, v, ks=ENEMY, vs=FRIENDLY, marker="") -> Row:
    return Row(y=0, killer=k, victim=v, killer_side=ks, victim_side=vs, marker=marker)


def test_rows_seen_again_are_one_event_named_by_the_majority():
    feed = Feed(window=12.0)
    reads = ["Made Up Name", "Made Up Narne", "Made Up Name", "Made Up Name"]
    for i, k in enumerate(reads):
        feed.add(10.0 + i * 0.4, [_row(k, "Other_Player7")])
    # A different kill between the same two, much later, is a new event.
    feed.add(40.0, [_row("Made Up Name", "Other_Player7")])
    feed.add(40.4, [_row("Made Up Name", "Other_Player7")])
    events = feed.finish()
    assert len(events) == 2
    assert events[0].t == 10.0 and events[0].killer == "Made Up Name" and events[0].seen == 4
    assert events[1].t == 40.0


def test_a_read_seen_once_is_dropped():
    feed = Feed()
    feed.add(1.0, [_row("Garbled", "Nonsense")])
    feed.add(1.4, [_row("Made Up Name", "Other_Player7")])
    feed.add(1.8, [_row("Made Up Name", "Other_Player7")])
    assert [e.killer for e in feed.finish(min_seen=2)] == ["Made Up Name"]


def test_old_events_do_not_stop_new_ones():
    # Regression: an event outside the window used to end the search before a new event was made.
    feed = Feed(window=5.0)
    feed.add(0.0, [_row("A_Name", "B_Name")])
    feed.add(0.4, [_row("A_Name", "B_Name")])
    for t in (20.0, 20.4):
        feed.add(t, [_row("C_Name", "D_Name")])
    assert len(feed.finish()) == 2


def test_alike_icons_share_a_class():
    a = np.zeros((16, 48), np.float32)
    a[6:10, 2:46] = 1
    b = a.copy()
    b[10:15, 10:14] = 1
    c = np.zeros((16, 48), np.float32)
    c[2:14, 18:30] = 1
    feed = Feed()
    names = {0: ("Alpha_One", "Bravo_Two"), 10: ("Charlie3", "DeltaFour"), 20: ("Echo_Five", "Foxtrot6"), 30: ("GolfSeven", "Hotel_8")}
    for t, icon in ((0, a), (10, a + 0.05), (20, c), (30, b)):
        r = _row(*names[t])
        r.icon = icon
        feed.add(t, [r])
        feed.add(t + 0.4, [r])
    events = feed.finish()
    classify_icons(events)
    assert events[0].weapon == events[1].weapon
    assert events[2].weapon != events[0].weapon


def test_the_gate_reads_on_change_and_now_and_then():
    gate = Gate(change=0.12, every=2.0)
    blank = np.zeros((384, 912, 3), np.uint8)
    one, _ = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN, height=384)
    two, _ = hs.feed_row("Someone_Else", "Another_One", hs.CYAN, hs.ORANGE, height=384)
    assert not gate.due(0.0, blank)
    assert gate.due(0.4, one)
    assert not gate.due(0.8, one)
    assert gate.due(1.2, two)
    assert not gate.due(1.6, two)
    assert gate.due(3.3, two)


def test_names_are_cleaned_and_compared_loosely():
    assert clean_name("Madeupname·一") == "Madeupname"
    assert clean_name("-Made_Up-") == "Made_Up"
    assert similarity("lmra2024", "Imra2024") > 0.9
    assert similarity("Made Up Name", "Other_Player7") < 0.5


def test_real_ocr_reads_a_drawn_row():
    pytest.importorskip("rapidocr_onnxruntime")
    from heat3d_capture.hud.killfeed import FeedReader
    from heat3d_capture.hud.ocr import Reader

    img, _ = hs.feed_row("MadeUpName", "OtherPlayer7", hs.ORANGE, hs.CYAN)
    img = cv2.copyMakeBorder(img, 40, 40, 0, 0, cv2.BORDER_CONSTANT, value=(40, 34, 30))
    reader = Reader(gpu=False)
    fr = FeedReader(reader)
    rows = parse_rows(img, fr.read(img), pitch=PITCH, text_h=TEXT_H, reader=reader)
    assert len(rows) == 1
    assert similarity(rows[0].killer, "MadeUpName") > 0.8
    assert similarity(rows[0].victim, "OtherPlayer7") > 0.8
    # The same picture again is not read again.
    fr.read(img)
    assert fr.reused_lines >= 2


def test_a_name_cut_short_is_the_same_event_and_named_in_full():
    # The end of a victim's name hidden under something else in some samples.
    feed = Feed()
    for i, v in enumerate(["Other_Player7", "Other_Pl", "Other_Player7", "Other_P1a9", "Other_Player7"]):
        feed.add(i * 0.4, [_row("Made Up Name", v)])
    events = feed.finish()
    assert len(events) == 1
    assert events[0].victim == "Other_Player7"


def test_the_same_pair_later_is_a_new_kill():
    # Read continuously, but for longer than a row stays up: the second is a new line.
    feed = Feed(window=5.0, life=14.0)
    for i in range(60):
        feed.add(i * 0.4, [_row("Made Up Name", "Other_Player7")])
    events = feed.finish()
    assert len(events) == 2
    assert events[1].t == pytest.approx(14.4)
    # And after a gap with no reads, likewise.
    feed = Feed(window=5.0)
    for t in (0.0, 0.4, 0.8, 11.6, 12.0):
        feed.add(t, [_row("Made Up Name", "Other_Player7")])
    assert [e.t for e in feed.finish()] == [0.0, 11.6]


def test_one_name_in_two_pieces_with_nothing_between_is_not_a_kill():
    # A victim with a two-word name whose killer has faded out: same colour, no weapon between.
    img2 = np.zeros((60, 912, 3), np.uint8)
    img2[:] = (40, 34, 30)
    cv2.putText(img2, "Two Words", (400, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, hs.ORANGE, 2, cv2.LINE_AA)
    (w1, _), _ = cv2.getTextSize("Two", cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
    pieces = [Text(398, 16, 402 + w1, 46, "Two", 0.9), Text(400 + w1 + 14, 16, 560, 46, "Words", 0.9)]
    # Read as two pieces whose gap is too wide to be joined as one name, yet nothing is between them.
    pieces[1].x0 = pieces[0].x1 + 0.7 * TEXT_H
    assert parse_rows(img2, pieces, pitch=PITCH, text_h=TEXT_H) == []


def test_a_victim_with_an_icon_and_no_killer_is_kept():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN)
    (kx0, ky0, kx1, ky1, _), victim = found
    # The killer's name gone (faded out, or a death to the world): only the icon and the victim.
    img[int(ky0) : int(ky1) + 1, int(kx0) : int(kx1) + 1] = (40, 34, 30)
    rows = parse_rows(img, boxes([victim]), pitch=PITCH, text_h=TEXT_H)
    assert len(rows) == 1 and rows[0].killer == "" and rows[0].victim == "Other_Player7"
    # Seen first without its killer, then with: one event, killed by them, timed at the first.
    feed = Feed()
    feed.add(1.0, rows)
    feed.add(1.4, rows)
    feed.add(1.8, [_row("Made Up Name", "Other_Player7")])
    events = feed.finish()
    assert len(events) == 1
    assert events[0].t == 1.0 and events[0].killer == "Made Up Name"


def test_a_lone_name_away_from_the_victims_column_is_not_a_row():
    img, found = hs.feed_row("Made Up Name", "Other_Player7", hs.ORANGE, hs.CYAN)
    killer, _ = found
    assert parse_rows(img, boxes([killer]), pitch=PITCH, text_h=TEXT_H) == []
