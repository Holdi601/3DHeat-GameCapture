---
title: Capture, masks and frame quality
parent: Level reconstruction
nav_order: 2
---

# Capture, masks and frame quality

Code: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Where frames come from

A source target is one of:

| Target | Source | Notes |
|---|---|---|
| `monitor:<n>` | a whole monitor, live | the window's "Whole screen" with the number in "Which" |
| `window:<title>` | one window, live | the window's "A window" with its title |
| a file path | a video file | the window's "A video file"; any format OpenCV can read |

### Live capture: Windows Graphics Capture

`WindowSource` uses the `windows-capture` package, which wraps **Windows Graphics Capture** -
the public API screen recorders use. Nothing is injected into the game. The cursor is not
captured and no yellow capture border is drawn.

The capture library delivers frames to a callback on the compositor's thread and expects it to
return at once, so the callback only copies the frame (the buffer is reused), converts BGRA to
RGB, resizes it, stamps it, and puts it in a queue of **4 frames**. When the queue is full the
**oldest frame is dropped** and a counter goes up: falling behind should cost frames, not
memory or correctness, and the live view should show where the player is now. Dropped frames
are shown in the window's statistics line, and more than half dropped triggers a hint.

Each frame carries `t` (seconds since the capture started) and `monotonic` (the raw
`time.monotonic()` at capture), the clock telemetry packets are stamped with too - which is
what lets Forza poses be lined up with frames.

`windows-capture` is optional in the dependency check: without it a video file can still be
scanned.

### Video files

`VideoSource` reads with OpenCV, converts to RGB and resizes. A container without a frame rate
is treated as 30 fps. Timestamps are the frame index divided by the frame rate; a file has no
wall-clock time, so telemetry cannot be aligned to a video.

### Resolution

Frames are resized at the source so the longest side is the preset's capture side (Draft 640,
Balanced 960, Detailed 1280 px), with area interpolation. A 4K frame is thirty times the pixels
the depth model uses.

## Keyframes

Almost every frame of a capture is redundant: standing still produces hundreds of views of one
thing. What reconstruction wants is *parallax*. So a frame is kept on **how much the picture
changed since the last kept frame**, not on a timer.

`picture_change(a, b)`:

1. both frames to grey and down to a 16 x 16 grid of block means (block means respond to the
   picture moving, not to grain, foliage, flicker or the HUD);
2. the mean absolute difference, as a fraction of 255;
3. when a world mask is known, each block is weighted by the share of it that is world rather
   than cockpit, so a half-dashboard block counts half (used once the mask covers more than 5%
   of the grid's weight).

The threshold **adapts to the capture**: for the first 30 frames it is the preset's starting
value (0.020 / 0.010 / 0.004), then it is the preset's quantile (0.85 / 0.65 / 0.40) of the
last 240 measured changes, never below 0.0001. A frame is kept when its change reaches the
threshold; the first frame is always kept. A fixed threshold cannot work across scenes - the
frame-to-frame change of a dark cockpit lap is a small fraction of a bright textured room's -
while "keep the busiest third" means the same in both. The threshold in use goes out with
every progress update (`ScanProgress.threshold`), and the walk-speed bars in the window and the
overlay measure the last change against it (`ScanProgress.toward_next_view`).

Only kept frames go through the depth model and the reconstruction. Frames are not stored
unless a caller asks (`keep_frames`); 160 of them are kept for colouring the mesh (see
[colour](reconstruction-fusion-and-texture.md#colour)).

A scan ends when it is stopped, when a video runs out, or at the time or keyframe limit.

## What is not the world

Two things in a game frame are not level geometry, and both wreck a reconstruction:

- **The HUD.** A crosshair is the most repeatable feature in any frame. A feature matcher
  loves it, it matches perfectly between every pair of frames, and every match is evidence
  that the camera did not move - which compresses the whole reconstruction.
- **Things bolted to the camera.** A weapon, a bonnet, a cockpit frame, a dashboard. Real
  geometry in the wrong coordinate system: fused, it smears along the whole path walked.

Two detectors find them. Both produce a mask (255 = world, 0 = not world) or `None` while there
is not enough evidence, and `None` always means "use everything", never "use nothing".

The mask is applied:

- at **feature detection** in visual odometry (masking a crosshair out of the output while
  letting it vote on the pose would fix the visible symptom and keep the damaging one);
- to the **fused pixels**, so no cockpit geometry is fused;
- to the **sharpness and brightness** measure, because a cockpit is always perfectly sharp;
- to the **picture change** that decides keyframes.

It is **not** applied to the frames given to the offline VGGT solver (see
[Offline reconstruction](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: what does not change

Used from the first keyframe until FlowMask is ready.

- Each frame is converted to grey, halved, and blurred (3 x 3 Gaussian) so a one-pixel jitter in
  a static HUD element does not read as motion.
- The per-pixel absolute difference from the previous frame is folded into an exponential
  average (decay 0.9), so the mask follows a HUD that appears or disappears mid-scan.
- It learns only from frames where the camera is known to move (in the scan: once at least one
  frame has been tracked) - a parked camera makes everything static.
- After **12** learning frames a pixel is static when its average change is below **0.22** of
  the frame's median change - relative, so the threshold follows how fast the player moves.
- If more than **45%** of the frame reads static, the premise has failed (a menu, a cutscene)
  and nothing is masked.
- The mask is eroded by one pixel (antialiased HUD edges belong to neither side) and scaled
  back to full size.

Its note in the window: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, or `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: what never travels

A cockpit is not static: needles sweep, the rev counter twitches, the minimap rotates, so a
change detector calls those pixels world - and they are the worst features to hand a pose
solver. FlowMask asks the better question: **which features persist without travelling?**

- In the live scan it learns once, from the first **40 keyframes** (greyscale); then it replaces
  ScreenMask for the rest of the scan.
- The frames are cut into windows of **30** frames, overlapping by half. In each window up to
  800 corners are seeded (`goodFeaturesToTrack`, quality 0.01, 8 px apart) and followed with
  pyramidal Lucas-Kanade (21 x 21, 4 levels) with a **forward-backward check**: a track whose
  backward flow does not land within 1 px of where it started is dropped, because a tracker that
  drifts onto a neighbouring pattern would manufacture exactly the "persistent but stationary"
  signature being looked for. Windows shorter than 20 frames are skipped. Short windows matter:
  over a long run almost every world feature leaves the frame and the evidence thins to nothing.
- Each surviving feature's net travel is compared with **2% of the frame width**: below, it is
  "stuck"; above, "moving". Counts are accumulated on a **24 x 24** grid of screen cells by
  where each feature started.
- A cell is blocked when it holds at least 2 stuck features and more stuck than moving ones,
  **and** at least 3 of its 8 neighbours are blocked too (a lone cell is noise; dark footage
  produces plenty).
- Only blocked regions **connected to the frame edge** are kept. Everything bolted to the
  camera reaches an edge of the screen; what sits in the middle and does not travel is the
  vanishing point - driving forwards, the road straight ahead has no flow and is the geometry
  most wanted.
- The surviving region is grown by one cell (an instrument panel's edge is a gradient).
- If more than **60%** of the frame would be masked, nothing is masked: on night footage most
  cells hold no trackable feature, which reads the same as a dial.

Its note: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, or, past 60%, a message explaining that it masks nothing.

The offline path learns the same FlowMask from 4 runs of 90 consecutive frames spread across
the video, at 960 x 540 ([Offline](reconstruction-offline.md)).

## Frame quality and advice

`QualityWatcher` judges every keyframe and picks **one** instruction, so the overlay can say
"slow down" while there is still time to.

Per frame it measures, on the world pixels only (all pixels if the mask leaves less than 5%):

- **sharpness**: variance of the Laplacian - the standard one-pass measure, and it responds to
  exactly what motion blur destroys;
- **luminance**: mean grey level, 0-255.

Sharpness has no absolute scale (a night stage and a bright street differ by an order of
magnitude, both in focus), so it is judged against the **running median of this capture**:
the last 90 frames, needing 20 before any judgement. Each frame is compared with the history
*before* it is added, so a long blurred stretch cannot drag the median down to meet itself.

| Condition | Test |
|---|---|
| flat | sharpness at most 1.0 (a loading screen, a wall, sky) |
| dark | luminance below 26 |
| blurred | sharpness below 0.55 of the median, and not flat |

The advice, first match wins (ordered by what blocks the scan hardest):

| Situation | Advice | Level |
|---|---|---|
| fewer than 20 frames | Getting a feel for the picture… | ok |
| flat | Nothing to measure — point the camera at the level, not at the sky. | stop |
| dark | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| blurred | Blurred — slow down. | warn |
| fewer than half the frames tracked | Losing track — slow down and keep more of the level in view. | warn |
| fewer than 40% of tracked frames fused | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| weak spots exist | N thin spots — the map marks them. | ok |
| otherwise | Good — keep going. | ok |

The level colours the overlay's advice (green / amber / red). The overlay's **sharpness** bar
is the frame's sharpness relative to the median. (The code also has "Blurred, and the camera is
not moving. Check the capture." for a stationary camera; the scan always reports the camera as
moving, so it is not shown.)
