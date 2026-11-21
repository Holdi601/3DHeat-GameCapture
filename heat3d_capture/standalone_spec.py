"""
The standalone app's description of this tool (app/spec.py): the lap
recorders. Each game's recorder is a task that runs until it is stopped and
writes one file per lap for the viewer's Race tab; a recorded FH Companion lap
library is converted by another. The scanner (`python -m heat3d_capture.ui`)
and the offline reconstruction need the GPU stack of a source install and are
not part of this program. `python -m heat3d_capture.standalone_spec` runs the
app from a checkout; the release executables run the same.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import __version__
from .app import paths
from .app.spec import Input, Spec, Task

TOOL = "heat3d-capture"


def _laps(game: str):
    return lambda levels: str(paths.data_dir() / "laps" / game)


def _record(game_key: str):
    def argv(v: dict, levels: Path) -> list[str]:
        game = (v.get("game") or game_key).strip().lower()
        return [TOOL, "telemetry", "--game", game, "-o", v["out"]]

    return argv


def _apply_source(release) -> str:
    """A checkout or source copy updates the way it always did (heat3d_update in the repository root)."""
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.append(root)
    import heat3d_update

    return heat3d_update.apply(release)


SPEC = Spec(
    id="heat3d-gamecapture",
    name="3DHeat GameCapture",
    repo="Holdi601/3DHeat-GameCapture",
    version=__version__,
    tools={TOOL: "heat3d_capture.__main__:main"},
    default_tool=TOOL,
    description="lap recorders: every telemetry channel, one file per lap, for the 3DHeat Race tab",
    module="heat3d_capture.standalone_spec",
    games=[],
    tasks=[
        Task(
            "forza", "Record Forza laps",
            [Input("out", "Where the laps go", "folder", default=_laps("forza"))],
            _record("forza"),
            help="Data Out on, IP 127.0.0.1, port 5300; drive, then Stop",
        ),
        Task(
            "assetto", "Record Assetto Corsa laps (Windows)",
            [Input("game", "Which game: ac, acc, acevo or acrally", "text", default="acc"),
             Input("out", "Where the laps go", "folder", default=_laps("assetto"))],
            _record("acc"),
            help="read from the game's shared memory while it runs; drive, then Stop",
        ),
        Task(
            "rally", "Record rally stages (EA WRC, DiRT, RBR)",
            [Input("game", "Which game: wrc, dirtrally2, dirtrally, dirt4 or rbr", "text", default="wrc"),
             Input("out", "Where the stages go", "folder", default=_laps("rally"))],
            _record("wrc"),
            help="the game's UDP telemetry switched on; drive, then Stop",
        ),
        Task(
            "beamng", "Record BeamNG.drive laps",
            [Input("out", "Where the laps go", "folder", default=_laps("beamng"))],
            _record("beamng"),
            help="the heat3d protocol mod on (see docs/telemetry-beamng.md); drive, then Stop",
        ),
        Task(
            "laps", "Convert a course from an FH Companion lap library",
            [Input("course", "The course's name (loosely matched)", "text"),
             Input("out", "Where the route and table go", "folder", default=_laps("forza"))],
            lambda v, levels: [TOOL, "laps", v["course"], "-o", v["out"]],
            help="the route and a table of every sample of every lap",
        ),
    ],
    min_free_gb=1.0,
    notice="Not affiliated with or endorsed by any game's makers or publishers.",
)

if __name__ == "__main__":
    from .app.entry import main

    raise SystemExit(main(SPEC, apply_source=_apply_source))
