
# 3DHeat GameCapture

3DHeat GameCapture is one of the free tools around the 3DHeat telemetry viewer. It does two
separate jobs:

1. **Lap telemetry recorders.** It records every channel a racing game publishes - Forza's
   Data Out, the Assetto Corsa games' shared memory, the rally games' UDP feeds, a BeamNG
   protocol mod, a Trackmania Openplanet plugin - and writes one `heat3d-lap` file per lap
   or stage. The viewer's Race tab reads those files directly. iRacing needs no recorder:
   the viewer reads its own `.ibt` files.
2. **Level reconstruction from gameplay.** It turns what the screen showed while you walked
   or drove through a level into a `.glb` mesh that the viewer loads as 3D context under the
   telemetry. Frames come from Windows Graphics Capture, depth is estimated by a neural
   network, the camera path comes from visual odometry, from Forza's telemetry, or from an
   offline feed-forward solve.

Both follow one rule: **nothing is injected into a game and nothing is hooked**. Frames come
from the public screen-capture API, telemetry from interfaces the games publish for it. See
[The rules](rules).

The code is Python (package `heat3d_capture`), MIT licensed, in
[Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture). The depth and
pose models it can run carry their own licences - see
[Models and licences](models-and-licences).

## Quick start

### Record laps

Requirements: Python 3 (developed and tested on 3.13; `scan.bat` offers 3.12), and `numpy`
for the Forza `route` and `laps` commands. The `telemetry` recorders themselves use only the
standard library. The minimum Python version has not been pinned or checked.

```bash
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

# Forza: Settings -> HUD and Gameplay -> Data Out = ON, IP 127.0.0.1, port 5300
.venv/Scripts/python -m heat3d_capture telemetry -o laps
```

Drive; each lap is written to `laps/` as it finishes. Press Ctrl+C to stop. Drop the files
on the viewer's Race tab. Every other game is one `--game` away:

```bash
.venv/Scripts/python -m heat3d_capture telemetry --game acc -o laps
.venv/Scripts/python -m heat3d_capture telemetry --game dirtrally2 -o laps
```

See [Telemetry recorders](telemetry) for every game and option.

### Scan a level

Double-click **`scan.bat`** in the repository folder. It finds Python (and offers to install
Python 3.12 with winget if there is none), creates a private `.venv`, and starts the scan
window, `python -m heat3d_capture.ui`. The window checks what is missing, says what each
package is for and how large the download is, and installs nothing without a yes. On the
first run it also offers to convert the depth model once. See
[Runtime and dependencies](runtime) and [The scan window](reconstruction-scan-ui).

By hand:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m heat3d_capture.ui
```

To reconstruct a recording offline with the camera path solved all at once (needs PyTorch,
the `vggt` package and a GPU):

```bash
.venv/Scripts/python -m heat3d_capture reconstruct lap.mp4 -o lap.glb
```

## Map of the documentation

| Page | What it covers |
|---|---|
| [The rules](rules) | No injection, published interfaces only, and what that costs |
| [Telemetry recorders](telemetry) | The `telemetry` command and an overview of every game |
| [Forza](telemetry-forza) | Data Out, layout detection, the FH Companion relay and its `.tele.gz` |
| [Assetto Corsa games](telemetry-assetto-corsa) | AC, ACC, AC EVO, AC Rally from shared memory |
| [Rally games](telemetry-rally) | EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally |
| [BeamNG.drive](telemetry-beamng) | The `heat3d` protocol mod |
| [Trackmania](telemetry-trackmania) | The `Heat3dRecorder` Openplanet plugin |
| [iRacing](telemetry-iracing) | Reading `.ibt` files in the viewer |
| [Lap and stage splitting](lap-splitting) | `LapSplitter`, `CounterSplitter`, `LineSplitter`, `StageSplitter` |
| [Slip, drift and derived channels](slip-and-drift) | How slip is scaled, and what the viewer derives |
| [The heat3d-lap file](lap-format) | The lap file format, channels, units, `meta` |
| [Games](games) | Per game: how to record, what is sent, which courses can be exported |
| [Command reference](commands) | `route`, `telemetry`, `laps`, `reconstruct` and every option |
| [Level reconstruction](reconstruction) | The pipeline from frames to a `.glb` |
| [The scan window](reconstruction-scan-ui) | Every control, hotkey and overlay element |
| [Capture, masks and frame quality](reconstruction-capture) | Windows Graphics Capture, keyframes, HUD masks, quality advice |
| [Depth](reconstruction-depth) | Depth Anything V2, ONNX Runtime, building the model |
| [Camera pose and scale](reconstruction-pose) | Odometry, relocalisation, telemetry poses, ground scale, bundle adjustment |
| [Fusion, coverage and colour](reconstruction-fusion-and-texture) | The occupancy volume, the coverage grid, weak spots, vertex colour |
| [The .glb output](glb-output) | The file the viewer loads |
| [Offline reconstruction](reconstruction-offline) | `reconstruct`, VGGT windows and stitching |
| [Models and licences](models-and-licences) | Depth Anything V2 sizes, VGGT, the packages |
| [Runtime and dependencies](runtime) | Preflight, backends, performance tiers |
| [Limits and verification](limits) | What is not done, and what has not been checked |
| [Updates](updates) | The release check and `python -m heat3d_update` |
| [Development](development) | Tests, the virtual environment, repository layout |

## Part of 3DHeat

| Tool | What it does |
|---|---|
| [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) | courses and levels out of the archives games ship, as glTF |
| [3DHeat GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) | lap telemetry from racing games' published interfaces; levels reconstructed from gameplay video |
| [3DHeat Unreal Exporter](https://github.com/Holdi601/3DHeat-UnrealExporter) | an Unreal Editor plugin that exports a level as glTF |
| [3DHeat CS2](https://github.com/Holdi601/3DHeat-CS2) | Counter-Strike 2 demos into heatmap tables and match summaries; maps into geometry |
| [3DHeat Watcher](https://github.com/Holdi601/3DHeat-Watcher) | records your play in the background from what games publish, for your own statistics |

A developer with the game's project open should use the Unreal exporter, which reads the real
geometry and is exact. Where a game's own archives can be read, GameFiles extracts the exact
course. Reconstruction from gameplay is for the case where only the screen is available.
