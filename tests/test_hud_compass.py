"""
The compass strip: labels to a heading, and headings to the mosaic's north.

The strip is drawn here at a known heading; the solver has to get it back from
the labels' positions alone, without being told the strip's scale.
"""

from __future__ import annotations

import pytest

cv2 = pytest.importorskip("cv2")

from heat3d_capture.hud import compass  # noqa: E402
from heat3d_capture.hud.ocr import Text  # noqa: E402

from . import hud_synth as hs  # noqa: E402

LETTERS = {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0}


def test_two_labels_give_heading_and_scale():
    # 300 two degrees right of the mark, 330 thirty degrees further: 3 px per degree.
    found = [(966.0, 300.0), (1056.0, 330.0)]
    heading, k = compass.solve(found, 960.0)
    assert k == pytest.approx(3.0)
    assert heading == pytest.approx(298.0)


def test_headings_wrap_through_north():
    found = [(900.0, 330.0), (990.0, 0.0), (1080.0, 30.0)]
    heading, k = compass.solve(found, 960.0)
    assert heading == pytest.approx(350.0)


def test_one_label_is_not_enough_and_a_wrong_one_is_outvoted():
    assert compass.solve([(960.0, 90.0)], 960.0) is None
    found = [(900.0, 270.0), (980.0, 300.0), (1060.0, 330.0), (700.0, 60.0)]
    heading, k = compass.solve(found, 960.0)
    assert heading == pytest.approx(292.5)


def test_labels_from_text():
    texts = [Text(10, 0, 30, 10, "240", 0.9), Text(50, 0, 60, 10, "W", 0.5), Text(90, 0, 100, 10, "732", 0.9),
             Text(130, 0, 200, 10, "300 330", 0.8), Text(210, 0, 230, 10, "40", 0.9)]
    found = compass.labels(texts, LETTERS)
    # 732 is no bearing and 40 is not on the 15-degree grid; "300 330" is two labels.
    assert [b for _, b in found] == [240.0, 270.0, 300.0, 330.0]


def test_label_blobs_are_found_where_they_are():
    strip = hs.compass_strip(300.0, per_degree=4.0)
    boxes = compass.blobs(strip)
    centres = sorted((x0 + x1) / 2 for x0, _, x1, _ in boxes)
    # Every 30 degrees from 180 to 60 (through N), at 510 + 4 * (b - 300); ticks between are not labels.
    expect = [510 + 4 * d for d in range(-120, 121, 30)]
    assert len(centres) == len(expect)
    for c, e in zip(centres, expect):
        assert c == pytest.approx(e, abs=4)


def test_north_offset_from_pairs():
    # The mosaic's up is 40 degrees east of north: compass = mosaic + 40.
    pairs = [((m + 40.0) % 360, m) for m in (0.0, 35.0, 170.0, 300.0, 359.0)]
    pairs.append((10.0, 200.0))  # one misread
    off, spread, n = compass.north_offset(pairs)
    assert off == pytest.approx(40.0, abs=0.01)
    assert n == 5
