"""
The Trackmania plugin, read as text: it runs inside Openplanet, not here.

What can be checked without the game is what it writes into each run's
description line, which the viewer reads to interpret the numbers.
"""

from __future__ import annotations

from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "mods" / "trackmania" / "Heat3dRecorder" / "main.as"


def test_the_run_says_what_its_slip_channels_mean():
    # slipIndex is Trackmania's 0..1 sliding measure, `index` in lap-format.md.
    # Without meta.slip the viewer has to guess.
    source = PLUGIN.read_text(encoding="utf-8")
    assert '\\"meta\\":{\\"slip\\":\\"index\\",\\"discipline\\":\\"arcade\\"}' in source


def test_the_columns_include_the_slip_channels_it_describes():
    source = PLUGIN.read_text(encoding="utf-8")
    assert "slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR" in source
