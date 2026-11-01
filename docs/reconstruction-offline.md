---
title: Offline reconstruction
parent: Level reconstruction
nav_order: 7
---

# Offline reconstruction

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4]
```

Code: [`scan/offline.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/offline.py),
[`pose/feedforward.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/feedforward.py),
[`pose/vggt_model.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/vggt_model.py),
[`pose/feedforward_source.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/feedforward_source.py),
[`pose/solveprep.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/solveprep.py).
Options: [Command reference](commands.md#reconstruct).

## Why a second path

Incremental tracking is live and cheap and works where there is structure to hold on to: an
interior, a street, a map with cover. A **racetrack is its worst case**: the road is a smooth
ribbon with little texture, the horizon barely moves, and once a few poses drift nothing later
pulls them back. A lap comes out as a curve that wanders instead of closing.

The offline path hands **windows of frames** to a model that predicts all their cameras together,
so every frame constrains every other directly instead of through a chain. It needs the whole
recording before it can answer, so it is not live, and it is slow: minutes per window on a desktop
GPU. Everything after the poses - fusion, coverage, colour, export - is the same code as the live
scan: the solved track is handed to the reconstructor as a pose source, exactly where Forza
telemetry goes.

## Requirements

- **PyTorch** matched to your GPU (not pinned by this project; install it before
  `requirements.txt`, see [Runtime](runtime.md)).
- **`vggt`** - the VGGT model code (`from vggt.models.vggt import VGGT`), from Meta's GitHub
  repository; it is not on the package index.
- **`transformers`**, because the offline path runs depth through the PyTorch
  `DepthEstimator` (Depth Anything V2 Small), not through the ONNX file.
- A CUDA GPU in practice; both models fall back to CPU, which is not practical.

None of these is in `requirements.txt`, because the scanner does not need them. They are in
**`requirements-offline.txt`**, with VGGT's own dependencies (`einops`, `safetensors`,
`huggingface_hub`, `Pillow`):

```bash
.venv/Scripts/python -m pip install -r requirements-offline.txt
.venv/Scripts/python -m pip install --no-deps "vggt @ git+https://github.com/facebookresearch/vggt.git"
```

VGGT goes in with `--no-deps` because its package metadata pins `numpy<2`, which pip would
honour by downgrading the numpy that scipy needs here. `reconstruct` checks for all of these
right after printing the licence line (the `OFFLINE` list in
[`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py)),
lists what is missing with sizes, and installs only on a yes - VGGT with `--no-deps`, as above.
Declining, or no terminal to ask at, exits with code 1.

## The model and its licence

**VGGT**, `facebook/VGGT-1B`: **CC-BY-NC-4.0, non-commercial only, and a reconstruction made with
it inherits that.** The command prints this before it starts (`describe_licence`). A separately
licensed `facebook/VGGT-1B-Commercial` exists but is a gated repository granted per account by
Meta, so it cannot be the default. `--model vggt-1b-commercial` solves with it (and prints its
licence line instead); without granted access the download fails. The `vggt` *code* is under
Meta's own "VGGT License", a research-materials agreement with an acceptable-use policy (read off
the package's `LICENSE.txt`). See [Models and licences](models-and-licences.md).

## The run, stage by stage

The stage names are what the command prints.

### masking

A `FlowMask` is learned from **4 runs of 90 consecutive frames**, centred at 1/8, 3/8, 5/8 and 7/8
of the video, at 960 x 540 grey (see [FlowMask](reconstruction-capture.md#flowmask-what-never-travels)).
Its note is printed and kept in the summary. A video shorter than 90 frames gets no mask.

#### The camera mask is learned, not applied

The mask is **not** applied to the frames given to the solver. Masking the cockpit looked right by
feature statistics (most detected corners sit on camera-attached pixels) - but that is a
statement about a feature detector, and the solver is a trained network. Measured by how far the
recovered path turns between consecutive steps (a car turns a few degrees; a random walk ninety),
raw frames gave the smallest turn, contrast-lifted frames a little more, masked frames clearly
more, and both together the most. So the solver gets raw frames. The mask is still used to
plan the frame spacing below, and the incremental tracker uses it in the live scan.
(`solveprep.enhance`, which masks and lifts local contrast with CLAHE, exists but is not used by
this command.)

### planning: frames spaced by motion

`plan_by_motion` picks the solver's frames by **how far the picture moved**, not by the clock: a
fixed interval gives slow sections frames they do not need and starves fast ones, where
consecutive frames stop overlapping enough to be related.

- Target displacement: **5% of a 960-pixel width** (48 px) median ORB feature displacement between
  consecutive chosen frames, measured on 960 x 540 grey frames with CLAHE contrast, features only on
  the mask.
- Start at a 0.3 s gap; after each step the next gap becomes
  `gap x (0.5 + 0.5 x target / measured)`, clamped to **0.15-2.0 s**, so one noisy measurement
  does not swing the plan.
- When nothing matched, the gap shrinks to 0.6 of itself (too far apart is the failure being
  avoided).
- Stops at the end of the video or at `--solve-budget` frames (default 260).

Fewer than 4 planned frames is an error.

### solving: windows and stitching

The planned frames are decoded at 960 px wide and solved in **overlapping windows of 16 frames,
6 shared** with the next (`plan_windows`; the last window is pulled back to end on the final frame,
so the end of a capture has as many neighbours as the middle). More than **400** frames in one run
is refused.

Each window: frames resized so the long side is **518** and both sides are multiples of **14**
(aspect ratio kept - squashing would misstate the field of view), scaled to 0..1, run through VGGT
under bfloat16 autocast (float16 runs out of exponent on far-away world coordinates). The camera
extrinsics are converted to world-from-camera rotations and camera centres. Point maps are not
kept by default.

Each window comes back in **its own arbitrary frame and its own arbitrary scale**, so windows are
**stitched** into the first one's frame by a similarity transform (rotation, translation, one
scale) fitted on the cameras they share with what is already placed:

- **Rotation from the cameras' orientations**, not their positions: the shared cameras sit along
  the path and are nearly collinear on a straight, which leaves a position-only fit unable to see
  the rotation - every window curves and the stitched result comes out straight. The rotation is
  the mean of `target_R x source_R^T` projected back onto a true rotation (with a reflection guard).
- **Scale and offset from the positions**, along the rotated source.
- At least **4** shared cameras are required; fewer is an error.
- The overlap is a third of the window so the scale is well determined; scale error compounding
  window over window is what makes a lap spiral.

For each seam the worst disagreement of the shared cameras after the fit is recorded, in units of
the mean spacing between them (`seam_error`).

### fusing

Frames every `--fuse-interval` seconds (default 0.4) are decoded at 960 px wide, given depth by
Depth Anything V2 Small (PyTorch), and fused with a pose **interpolated** from the solved track at
their timestamp (linear position, spherical rotation; `FeedForwardPoses`). Frames outside the
solved time span are skipped rather than extrapolated. The camera uses a **65 degree** horizontal
field of view. Feed-forward poses carry confidence 0.85 in fusion and coverage.

### exporting

The mesh is written as for a live scan ([The .glb output](glb-output.md)), named after the video.

## The summary

```text
140 cameras solved over 182s
closure error 3.1% of path length
worst seam 0.42 frame spacings
<mask note>
wrote lap.glb
```

| Line | Meaning |
|---|---|
| closure error | distance from the first to the last camera over the path length. For a single lap the honest measure of drift. Above 10%: "The lap does not close ... Treat the shape as unreliable." |
| worst seam | the largest stitch disagreement. Above 1.0: "Windows disagreed by up to N frame spacings at a seam, so part of the path is stitched on weak evidence." |
| no file | "Fusion produced no surface, so nothing was written." The exit code is then 1. |

## Scale

The stitched path is in the first window's arbitrary units. Depth is anchored by triangulating
between the interpolated poses (as for telemetry), so the geometry is consistent with the path -
but **the result is not in metres** unless the path is. Nothing in this command fixes the global
scale; the ground calibration is not applied when poses come from a pose source.

## State of this path

With frames at a fixed interval, windows solve into a coherent path on some sections of a lap and
a scribble on others; the failures are the tight corners, where the view swings hard between
frames, and sampling those corners more densely recovers them. No image statistic tried
(brightness, detail, feature count, inlier ratio, displacement) predicted in advance which
sections would fail. So the spacing cannot be fully planned
from the pictures in advance: it has to be chosen by solving, measuring the result, and re-solving
denser where the path is not one a car could have driven. Motion-based planning is built; **the
adaptive re-solve is not**.
