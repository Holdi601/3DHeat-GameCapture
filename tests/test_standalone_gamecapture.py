"""The standalone app's description of GameCapture: the recorder tasks and the update shim (no game needed)."""

from __future__ import annotations

import json

import pytest

from heat3d_capture import standalone_spec
from heat3d_capture.app import entry, update


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "appdata"))
    monkeypatch.setenv("HEAT3D_LEVELS", str(tmp_path / "levels"))
    monkeypatch.setenv("HEAT3D_NO_UPDATE", "1")
    update.AUTO_THIS_RUN = False


def test_recorder_tasks(tmp_path):
    tasks = {t.id: t for t in standalone_spec.SPEC.tasks}
    assert tasks["forza"].argv({"out": "o"}, tmp_path) == ["heat3d-capture", "telemetry", "--game", "forza", "-o", "o"]
    assert tasks["rally"].argv({"game": " DiRT4 ", "out": "o"}, tmp_path)[3] == "dirt4"
    assert tasks["assetto"].argv({"game": "", "out": "o"}, tmp_path)[3] == "acc"
    out = tasks["beamng"].inputs[0].default(tmp_path)
    assert out.replace("\\", "/").endswith("laps/beamng")
    assert tasks["laps"].argv({"course": "c", "out": "o"}, tmp_path) == ["heat3d-capture", "laps", "c", "-o", "o"]


def test_the_recorders_options_are_the_tools(capsys):
    # Every game a task names is one the telemetry verb takes.
    assert entry.run_tool(standalone_spec.SPEC, "heat3d-capture", ["telemetry", "--game", "nope"]) == 2
    assert entry.run_tool(standalone_spec.SPEC, "heat3d-capture", ["telemetry", "--help"]) == 0
    text = capsys.readouterr().out
    for game in ("forza", "acc", "acrally", "wrc", "dirtrally2", "dirt4", "rbr", "beamng"):
        assert game in text


def test_status_lists_no_games(capsys):
    assert entry.main(standalone_spec.SPEC, ["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["games"] == []


def test_update_startup_asks_through_the_app(monkeypatch):
    import heat3d_update

    t = heat3d_update.target()
    assert t.tool_id == "heat3d-gamecapture" and t.repo == "Holdi601/3DHeat-GameCapture"
    seen = []
    monkeypatch.setattr(update, "startup", lambda target, ask=None: seen.append((target.tool_id, ask)))
    heat3d_update.startup("heat3d_capture", ask=False)
    assert seen == [("heat3d-gamecapture", False)]
