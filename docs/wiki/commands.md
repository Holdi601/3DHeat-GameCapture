
# Command reference

All commands run from the repository folder, with the project's environment:

```bash
.venv/Scripts/python -m heat3d_capture <verb> [options]
```

| Command | Does |
|---|---|
| [`route`](#route) | Records a Forza lap's positions only, for finding the map in the game's files |
| [`telemetry`](#telemetry) | Records every channel, a lap file per lap, for the Race tab |
| [`laps`](#laps) | Reads an FH Companion lap library and writes one course's route and samples |
| [`reconstruct`](#reconstruct) | Solves a recording offline and writes a `.glb` |
| [`python -m heat3d_capture.ui`](#the-scan-window) | The scan window |
| [`python -m heat3d_update`](#updates) | Checks for and applies an update |
| [`python tools/export_onnx.py`](#the-model-converter) | Converts the depth model to ONNX |

When started as `python -m heat3d_capture`, the tool first checks for a newer release (see
[Updates](updates)). Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Listens for Forza Data Out and keeps the car's positions, nothing else: no depth model, no
GPU, no capture. Code: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Option | Default | Meaning |
|---|---|---|
| `-o`, `--out` | required | Output path; its suffix is replaced, so `-o lap` writes `lap.npz` and `lap.json`. |
| `--port` | `5300` | Port the game sends to (bound on 127.0.0.1). |
| `--seconds` | `0` | Stop after this many seconds; `0` runs until Ctrl+C. |

A position is kept only while the game reports a race (`isRaceOn`), the car moves faster than
0.5 m/s, and it is at least 0.5 m from the last kept position - otherwise sitting in a menu at
60 packets a second would fill the file with the start line. Each sample's time is the
game's race time, or the wall clock when that is 0. The layout is detected exactly as for
`telemetry` (the car must move first; see [Forza](telemetry-forza)).

Once a second it prints packets received, positions kept and the current position, or
`nothing on port 5300 yet - is Data Out on?`. The route is **saved while it is driven**: every
2 seconds once a new position has arrived (the gap grows to twenty times what the last save
took, so a very long session never spends more than a twentieth of its time writing), and once
more when the recorder stops for any reason - Ctrl+C, `--seconds`, or an exception. Each save
writes `lap.npz.partial` / `lap.json.partial` and then moves it over the real file, so the
files on disk are always whole; a crash or a killed process loses at most the last few
seconds. If nothing was kept it prints how to switch Data Out on and exits with code 1.

Output:

- `lap.npz` - NumPy arrays `positions` (n x 3, metres), `times`, `speeds` (m/s);
- `lap.json` - readable without this project:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

The positions are the game's own world coordinates, which is what makes them a handle for
finding the same ground in the game's files: the
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) `course` command takes this
JSON and exports the course the lap ran over.

## telemetry

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Every option and game is described on [Telemetry recorders](telemetry).

## laps

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Reads the lap library FH Companion keeps and writes two files for one course: a route that
says which piece of map to cut out of the game's archive, and a table of every sample of every
lap. They are written together so that they cannot end up out of step. Code:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Option | Default | Meaning |
|---|---|---|
| `course` | none | Course name, matched loosely. Omit to list the library. |
| `-o`, `--out` | the course name, lower case, spaces as `_` | Output path; `.json` and `.csv` are written beside each other. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Where the course folders are. |
| `--margin` | `80` | Metres added around the course's extent in x and z in the route's `bounds`. |

### Listing

Without a course it prints the number of course folders and, for each, the number of lap
files (`*.json` anywhere below it except `course.json`) and the course name, then
`Name one to write it out:  -o <file> <course>`.

### Finding a course

Course folders are named `<name> (course_<x>_<z>_to_<x>_<z>)` - the start and finish,
rounded. A course is found by, in order: the exact folder name; the name part of the folder
name, ignoring case; a unique folder whose name contains the text. Several matches is an
error that lists them.

### Reading it

- `course.json` in the folder, when readable, gives the name and the unrounded start and
  finish (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); otherwise they come from the
  folder name. A course is reported as a circuit when start and finish are less than 10 m
  apart.
- Every other `*.json` below the folder is a lap (laps sit several folders deep - by class,
  car, tune, tag - and the search is simply recursive). Files are read as UTF-8 with a byte
  order mark. An unreadable lap is skipped. Laps are sorted by their recording time.
- Per lap: `Lap.samples` (each with `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), and the car
  class, ordinal, performance index, lap seconds, length, recording time and standing start.

It prints a summary (laps, samples, best lap and its class, the x/y/z extent).

### Output

**`<out>.json`** - the same route shape `route` writes, so the map extractor takes either:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (expanded by `--margin` in x and
z), and `positions` of the **fastest** lap (one line rather than a smear of every lap).

**`<out>.csv`** - every sample of every lap, one row each:

| Column | Meaning |
|---|---|
| `course` | course name |
| `lap` | a label per lap: recording date and time to the minute, and the lap time |
| `car` | car ordinal |
| `car_class` | performance class letter |
| `pi` | performance index |
| `lap_seconds` | the lap's time |
| `speed_kmh` | speed in km/h |
| `x`, `y`, `z` | world position, metres, 3 decimals |
| `speed_ms` | speed, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | as FH Companion records them |
| `metres` | distance along the lap, 3 decimals |
| `elapsed` | seconds since the lap's own start, 3 decimals |

Non-position values are written to 4 significant figures; positions get fixed decimals because
4 significant figures would snap a course onto a one-metre grid. The column names are chosen
so the viewer maps the file without being told: `lap` becomes the session (two laps by one car
are never joined), `car` the thing that moves, `car_class` the group to colour by, `elapsed`
the time axis (every lap lines up at its own start).

Finally it prints a hint for cutting the map out of the game with GameFiles, with the route
file or an explicit box.

## reconstruct

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Reconstructs a recording offline, with the camera path solved all at once by VGGT. Slow:
minutes per window on a desktop GPU. Needs PyTorch, Hugging Face `transformers` and the `vggt`
package, which the scanner does not need: they are listed in `requirements-offline.txt`, and
the command checks for them after printing the licence line and offers to install whatever is
missing (exit code 1 if declined). Full description:
[Offline reconstruction](reconstruction-offline).

| Option | Default | Meaning |
|---|---|---|
| `video` | required | The recording. Exit code 2 if it does not exist. |
| `-o`, `--out` | required | The `.glb` to write. |
| `--solve-budget` | `260` | Most frames handed to the solver. They are spaced by how far the picture moves, not by the clock. More is more accurate and much slower. More than 400 planned frames is refused. |
| `--fuse-interval` | `0.4` | Seconds between frames fused into geometry. |
| `--model` | `vggt-1b` | Which VGGT weights to solve with: `vggt-1b` (`facebook/VGGT-1B`, non-commercial) or `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, gated; needs access granted by Meta). The licence line printed first is that model's. |

It prints the model's licence line first, then each stage (`masking`, `planning`, `solving`,
`fusing`, `exporting`) with elapsed seconds and progress, and finally a summary: cameras
solved, closure error, worst seam, notes, and the file written. The exit code is 0 only if a
file was written.

## The scan window

```bash
python -m heat3d_capture.ui
```

or double-click `scan.bat`. No options. See [The scan window](reconstruction-scan-ui).

## Updates

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

See [Updates](updates).

## The model converter

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Converts a Depth Anything V2 checkpoint to the ONNX file the scanner runs. Needs PyTorch,
`transformers` and `onnxscript`. See [Depth](reconstruction-depth#building-the-model).
