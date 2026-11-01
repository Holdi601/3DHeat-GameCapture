---
title: Development
nav_order: 11
---

# Development

## Repository layout

| Path | Contents |
|---|---|
| `heat3d_capture/__main__.py` | the command line: `route`, `telemetry`, `laps`, `reconstruct` |
| `heat3d_capture/telemetry/` | `forza.py` (Data Out layout), `fulllap.py` (Forza lap files, relay), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (the shared lap document) |
| `heat3d_capture/capture/` | `sources.py` (live capture, video), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (what the scanner runs), `estimator.py` (PyTorch path, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (the writer), `reference.py` (synthetic reference level) |
| `heat3d_capture/scan/` | `session.py` (a scan), `reconstruct.py` (keyframes into geometry), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/ui/` | `__main__.py` (entry and dependency check), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | the release check and updater |
| `mods/beamng/heat3d/` | the BeamNG protocol mod |
| `mods/trackmania/Heat3dRecorder/` | the Openplanet plugin |
| `tools/export_onnx.py` | the depth model converter |
| `models/` | converted `.onnx` files (not versioned) |
| `tests/` | the test suite; `scene.py` and `track_scene.py` render synthetic scenes with known geometry |
| `docs/` | this documentation; `docs/wiki/` is generated from it |
| `scan.bat`, `requirements.txt`, `VERSION`, `LICENSE`, `LICENSES.md` | |

The scan logic has no Qt in it: `ScanSession` and `Reconstructor` take plain callables and can be
driven from a script or a test. Example:

```python
from heat3d_capture.depth.onnx_estimator import OnnxDepthEstimator
from heat3d_capture.scan.session import Quality, ScanSession, ScanSettings

settings = ScanSettings(source="walk.mp4", quality=Quality.BALANCED, field_of_view=90.0,
                        camera_height=1.70)
session = ScanSession(settings, estimator=OnnxDepthEstimator("models/depth-small-518.onnx"))
session.start()
session.wait()
print(session.progress.message, session.export("walk.glb"))
```

## The environment

The project uses a virtual environment in `.venv` (created by `scan.bat` or by hand). The tests
that touch the interface need **PySide6** in it, which `requirements.txt` installs as
`PySide6-Essentials`:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

For the model converter, the PyTorch depth tests and the offline path, install PyTorch (matched to
the GPU) **before** `requirements.txt`; then `requirements-offline.txt` and its `vggt` line for the
offline solver, and `onnxscript` for the converter. See
[Runtime and dependencies](runtime.md#installing-by-hand).

## Running the tests

```bash
.venv/Scripts/python -m pytest tests/ -q
```

`pytest.ini` sets `testpaths = tests` and silences `UserWarning`s from `huggingface_hub`. The
suite has several hundred checks; most need neither a game, a GPU nor capture hardware.

What skips itself, and why:

| Tests | Skip when |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, the window-driving tests in `test_ui_drives_a_scan.py` | no `models/depth-*.onnx` - run `tools/export_onnx.py` first |
| the GPU estimator tests in `test_depth.py` | PyTorch is not installed, or there is no CUDA device; the `fit_scale` and `AffineFit` tests run regardless |
| some `test_offline.py` and `test_solveprep.py` cases | OpenCV has no video encoder to write the synthetic clip |
| `test_hotkeys.py` | registration tests need Windows; the fallback test runs elsewhere |
| `test_course_ground.py` | `HEAT3D_COURSE` is not set |
| a few fusion tests | a synthetic case fused nothing |

### The launch test

`tests/test_launch.py` runs the real entry point, `python -m heat3d_capture.ui`, as a subprocess
(with `QT_QPA_PLATFORM=offscreen`) and checks that it reaches the event loop and stays up. It exists
because the first build crashed on every launch while every other test passed: they all construct
a `QApplication` themselves and then build the window, which skips the one sequence a user
performs - the dependency check creating an application first. A component test that builds its
own environment cannot see a fault in how the environment is built.

### Ground truth

- `tests/test_accuracy.py` - a synthetic room from a known path with analytic depth; see
  [Level reconstruction](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`,
  `tests/test_loop_closure_harm.py` - road width, track-scale extraction, the coverage grid read
  while being written, and why loop closure stays off.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`,
  `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - the telemetry layouts, on packets and
  pages built from the documented structures, and the lap files they write (canonical channel
  names, `meta`, no `NaN` in the JSON). `tests/test_trackmania_plugin.py` reads the Openplanet
  plugin's source for what it writes into each run's description.
- `tests/test_route_record.py` - the `route` file is on disk, whole, before the recorder stops.
- `tests/test_telemetry_pose.py` - Forza poses in the game's own coordinates, the senses of yaw,
  pitch and roll, and a telemetry gap bridged visually in the mirrored world.
- `tests/test_glb.py` - the GLB contract; the viewer's own tests parse a reference level written
  by this writer, so the format is tested on both sides.

### Checking an exported course against laps

`tests/test_course_ground.py` checks that a course exported by
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) really lies under the recorded
car - the car should sit a ride height above the surface directly beneath it. Point it at an
exported course's stem (the `.glb` and its `.json` beside it):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv/Scripts/python -m pytest tests/test_course_ground.py
```

A course with big jumps can fail by design: the car is in the air over ground that is there.

## Conventions

- Code under `heat3d_capture/` imports heavy dependencies (OpenCV, ONNX Runtime, PyTorch, Qt)
  lazily inside functions, so importing a module, running `--help` or running the telemetry
  recorders costs nothing.
- Worker threads never touch Qt widgets; results cross to the interface thread as Qt signals.
- Recordings, lap files, meshes, model weights and video are kept out of git by `.gitignore`, by
  folder and by file type.
- Commits and releases: the version is the `VERSION` file; releases are GitHub releases of
  [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), which the updater
  reads ([Updates](updates.md)).
