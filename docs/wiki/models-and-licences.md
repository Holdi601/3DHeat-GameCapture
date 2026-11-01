
# Models and licences

Everything written for this repository is under the **MIT licence**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). What MIT cannot
cover is what the tools run with: the packages they import, the models reconstruction uses, and
the games they read. The full record, with sources, is
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); its
licences were read off package metadata and model cards in September 2026. Where a component's
terms changed since, the source counts, not this page. Nothing here is legal advice.

## The depth model - the one that decides commercial use

Depth Anything V2 is **not licensed alike across its sizes**, and a reconstruction inherits the
licence of the model that made it:

| Model | Licence | Commercial use | Used by |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **permitted** | the default: the scanner's converted model (`tools/export_onnx.py` defaults to it, and the window's "Set up the depth model" always builds it), and the offline `reconstruct` path |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | non-commercial only | only if you convert it yourself (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | non-commercial only | only if you convert it yourself (`--size large`) |

Base and Large give better depth. Converting them is permitted; it makes that model file, and
every reconstruction made with it, non-commercial. That is a decision for whoever runs it, not a
default to inherit. The scanner chooses among the `models/depth-*.onnx` files **by licence, not by
name**: `depth-small-*` whenever there is one, then Base, then Large (`choose_model` in
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
The window names the file it took, its licence, and any other model files it found and did not
use; to scan with Base, move the Small file out of `models/`.

## VGGT - offline reconstruction only

| Model | Licence | Availability |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - non-commercial only**; reconstructions made with it inherit that | public; the default |
| `facebook/VGGT-1B-Commercial` | separately licensed; check the terms you were granted | gated: access is requested from Meta and granted per account; without it the download fails. Chosen with `reconstruct --model vggt-1b-commercial` |

VGGT is used only by `python -m heat3d_capture reconstruct`; the live scanner never loads it. The
command prints the licence line before it starts. Reconstruction from video is the part of this
project a player would run, and non-commercial terms fit that; for commercial work an engine export
or the game-file exporter is the route, and both are exact anyway.

## Python packages

| Package | Licence | Role |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | arithmetic, smoothing, marching cubes |
| opencv-python | Apache-2.0 | video, features, optical flow |
| onnxruntime, onnxruntime-directml | MIT | depth inference |
| windows-capture | MIT | live capture through Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | the window |
| pytest | MIT | development only |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | one-off model conversion; the offline path |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | the offline path (`requirements-offline.txt`) |
| vggt | Meta's "VGGT License" (research-materials agreement with an acceptable-use policy) | the offline path; installed from GitHub with `--no-deps` |

**PySide6 has conditions.** LGPL-3.0 permits proprietary and commercial use provided Qt stays a
*replaceable* library. It is used here as an ordinary dynamically linked import, which satisfies
that, and its licence notice must travel with any distribution. Bundling the tool into a single
executable would have to keep Qt replaceable.

The `vggt` package's own licence was read off its `LICENSE.txt` and is recorded in `LICENSES.md`;
it covers the code, separately from the weights' CC-BY-NC-4.0.

## The games

Telemetry comes only from interfaces the games publish; frames come from the screen. See
[The rules](rules). What a user points the tools at remains subject to that game's licence and
EULA, and that obligation sits with whoever runs the tool.
