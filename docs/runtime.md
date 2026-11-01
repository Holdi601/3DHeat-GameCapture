---
title: Runtime and dependencies
nav_order: 8
---

# Runtime, dependencies and performance

Code: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat

Double-click it. It does only two things itself:

1. **Finds Python** (`python`, then `py`). If there is none it asks
   `Install it now with winget [Y,N]?`; on Y it runs
   `winget install -e --id Python.Python.3.12`, then asks you to close the window and run
   `scan.bat` again so Windows picks up the new PATH. On N nothing is installed.
2. **Creates a private environment**, `.venv` next to `scan.bat`, if there is none, and upgrades
   its pip - so nothing is installed into the system Python.

Then it runs `.venv\Scripts\python.exe -m heat3d_capture.ui`. Everything else - working out what
is missing, saying what it is for, asking - happens in Python, as a dialog.

## First-run preflight

Before the window imports anything heavy, every requirement is checked (with
`importlib.util.find_spec`, so a half-removed package counts as missing). The rules:

- **Everything is checked first.** The full list is gathered before anything is said, so fixing
  one package never leads straight into the next error.
- **Ask, never assume.** The dialog lists each missing package, what it is for, and the total
  download, and does nothing without **Download and install**. Cancel exits: "Nothing was
  installed and nothing was changed."
- **Silence is not consent.** Without Qt the check falls back to the console and asks
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` mean yes); with no terminal to answer
  at (end of input), it installs nothing.
- **Into this tool's own environment.** Installation is `<running python> -m pip install ...` as
  a subprocess - with `scan.bat`, the private `.venv`. If it fails, the dialog shows the last line
  of pip's output and the command to try by hand.

| Package | Imported as | Shown as what it is for | Approx. download |
|---|---|---|---|
| numpy | `numpy` | the arithmetic everything else is built on | 20 MB |
| opencv-python | `cv2` | reading video files and camera frames | 40 MB |
| onnxruntime-directml on Windows, onnxruntime elsewhere | `onnxruntime` | running the depth model on your graphics card | 120 MB |
| PySide6-Essentials | `PySide6` | the window and its controls | 90 MB |
| scipy | `scipy` | smoothing the reconstructed surface | 45 MB |
| scikit-image | `skimage` | turning measurements into a 3D surface | 30 MB |
| windows-capture | `windows_capture` | capturing a game window live (optional: without it, video files still work) | 5 MB |

Converting the depth model needs three more, asked for separately and only when you press "Set up
the depth model": `torch` (about 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). The scanner
itself never imports them.

The offline `reconstruct` command has a check of its own, run after it prints the licence line
and only in the terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, and `vggt` from Meta's GitHub repository (installed with `--no-deps`,
because its metadata pins numpy below 2). The same list is `requirements-offline.txt`; see
[Offline reconstruction](reconstruction-offline.md#requirements).

The ONNX Runtime package offered is the one `requirements.txt` picks for the platform:
`onnxruntime-directml` on Windows, `onnxruntime` elsewhere. If `onnxruntime` is already
importable (for instance `onnxruntime-gpu`), nothing is installed: the check is by module name.

## Installing by hand

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m heat3d_capture.ui
```

`requirements.txt` pins: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(Windows only), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` on Windows and `onnxruntime>=1.19` elsewhere.

`requirements-offline.txt` adds what only `reconstruct` needs: `transformers`, `einops`,
`safetensors`, `huggingface_hub` and `Pillow`, with the `vggt` install line (`--no-deps`) and the
VGGT licence note in its header. PyTorch is not in it either, for the reason below.

**PyTorch is deliberately absent.** The right wheel depends on the GPU and CUDA version, and pinning
one would install a CPU build on the machines that most need the GPU one. If you want it (model
conversion, the offline `reconstruct` path), install it **before** `requirements.txt`: the torch
wheels can settle on numpy 1.x, which scipy then refuses to run against, and the failure shows up as
`module numpy has no attribute long` from inside scipy, nowhere near its cause.

`onnxruntime-directml` and `onnxruntime-gpu` conflict: install only one.

Verified by the developer: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, on an NVIDIA
RTX 5080, and the same environment with no NVIDIA-specific package in it.

## Inference backends

ONNX Runtime reaches GPUs through execution providers, and which ones exist depends on how
onnxruntime was installed, not on the hardware. So availability is discovered, best first:

| Rank | Provider | Shown as | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | any Direct3D 12 GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | anything |

**DirectML is the default install** because it reaches AMD and Intel GPUs as well as NVIDIA.
NVIDIA is faster with its own providers - installing `onnxruntime-gpu` adds CUDA, and the window
says so when it sees an NVIDIA card running on DirectML - but NVIDIA is not allowed to be the only
option. CPU is always last, so a machine with no usable GPU gets a slow scan rather than none, and
it is appended as a fallback when a GPU session is created.

The adapter's name is read from the Windows display-adapter class key in the registry (not from a
vendor tool such as `nvidia-smi`, which exists on only some machines), skipping the Basic Render
Driver. Vendor-locked providers name the matching adapter; DirectML is shown on the first
enumerated adapter, which is the system default. The name is for display only.

`ScanSettings.prefer_backend` (scripts only) can name a provider or a short name.

## What to expect from this machine

The window measures the depth model's actual throughput on this machine at start-up (6 frames after
a warm-up) rather than looking the GPU up in a table - thermal state, laptop power profiles and
driver versions move it too much - and states what a scan will be like before anything can start:

| Measured views per second | Tier | Headline | Advice |
|---|---|---|---|
| 25 or more | realtime | Live scanning at full detail. | Walk at a normal pace; the overlay will keep up. |
| 12 to 25 | workable | Live scanning, with fewer views kept than at full speed. | Walk slowly and turn gently — fast turns will leave gaps. Draft keeps fewer views, which helps the depth model keep up. |
| 2 to 12 | slow | Record first, reconstruct afterwards. | Record a video of the walk and reconstruct from the file afterwards. The result is identical; only the feedback is not live. |
| below 2 | impractical | This machine is too slow to scan usefully. | A shorter route, or a smaller model. **Start is disabled.** |

On CPU the note adds that installing `onnxruntime-directml` usually fixes it on Windows. Nothing
changes the capture resolution on its own: it would not help, because the depth model runs at its
fixed input size whatever it is handed; what keeps a slower machine up is keeping fewer views,
which is what Draft does.

### Measured by the developer

Same ONNX file, same output, RTX 5080:

| Backend | Depth throughput |
|---|---|
| DirectML | 54 fps |
| CPU | 3.5 fps |

A 120-frame clip through the shipped ONNX path:

| Preset | Views kept | Depth throughput |
|---|---|---|
| Draft | 17 of 120 | 49 /s |
| Balanced | 31 of 120 | 50 /s |
| Detailed | 58 of 120 | 42 /s |

Depth is comfortably faster than capture, so live scanning is not depth-bound. The app's
environment is about 349 MiB with no PyTorch, against roughly 3.5 GB for torch with CUDA.

The offline `reconstruct` path is different: minutes per 16-frame window on a desktop GPU.

## Memory

- Frames are not kept after fusion, except **160** for colouring the mesh.
- A scan stops at **3000** kept views by default ("Views kept"), as a guard.
- The live capture queue holds 4 frames; the telemetry pose buffer 30 seconds.
- Both voxel grids are sparse, and the mesh is extracted block by block, so memory follows what
  was scanned, not the bounding box.

## Platform

The scanner and the Assetto Corsa recorders are Windows-only in practice: live capture uses Windows
Graphics Capture, the hotkeys and the click-through overlay use the Win32 API, and the Kunos pages
are Windows shared memory. Video files can be scanned and the UDP recorders run elsewhere, but that
has not been checked.
