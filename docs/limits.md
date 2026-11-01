---
title: Limits and verification
nav_order: 9
---

# Limits and what is verified

An honest list: what the tools do not do, and what has not been checked against a running game.

## Telemetry

| Recorder | Status |
|---|---|
| Forza | Built on the official Data Out documentation; the layout is detected from the packets themselves. The viewer's FH Companion `.tele.gz` reader has been checked on real laps. |
| AC, ACC, AC EVO, AC Rally | Tested on synthetic pages built from the published layouts. **Not yet run against the live games.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Tested on packets built from the documented layouts. **Not yet run against the live games.** RBR's axes, attitude and speed units are undocumented and handled from the data. |
| BeamNG.drive | The recorder is tested on packets built from the mod's struct. **The mod has not been run in the game.** |
| Trackmania | The viewer's reader of the CSV is tested. **The plugin has not been run in the game.** It loads only in Openplanet's developer mode. |
| iRacing | The viewer's `.ibt` reader is tested on a synthetic file. |

Other telemetry limits:

- Forza's slip normalisation is undocumented; Kunos slip is scaled by a typical tarmac peak, an
  approximation.
- The sense of some car-frame lateral axes (Kunos, DiRT) is documented both ways; the drift
  angle's size is reliable, its sign is not.
- None of the rally games sends tyre slip; it is derived in the viewer. RBR sends no wheel speeds.
- A rally stage's surface is written only when `--surface` is given; otherwise the file names
  none and the viewer infers it (stage or event name, then driving style, loose by default).
- Lap detection without a lap counter (AC EVO, AC Rally, BeamNG) uses the point where recording
  began as the line, so start recording at the start line.
- A BeamNG vehicle reset closes the lap open at that moment: it is written as a partial run when
  it covered the minimum distance (300 m), and dropped otherwise.
- `route` saves every 2 seconds or so while driving; a crash or a killed process loses at most
  the positions since the last save.
- Forza Horizon sends no track name, so Forza lap files have `"track": null`; Forza Motorsport
  (2023) sends only a number, kept as `lap.trackOrdinal`.

## Reconstruction

- **Depth is estimated, not read.** The ceiling of the whole approach, and the price of never
  touching the game process.
- **Field of view is assumed, not measured.** Too narrow and the level reconstructs deeper than
  it is.
- **Global scale** comes from an assumed camera height (1.15 m in the window), or from
  telemetry. It is measured on the first keyframe; when that has no usable ground, the next
  keyframes are tried (up to 30 frames), and a scale found later is applied to the whole level
  when it is written. The window's "Size:" line says which happened; with no ground found at all
  the scan stays unit-less. The voxel size is in the first frame's units in that case, so its
  size in metres differs from the setting. Offline reconstructions are in the solve's own units.
- **Loop closure is off** and is not a pose graph when switched on in code; drift is bounded only
  by the quality of frame-to-frame tracking.
- **Windowed bundle adjustment exists but is not wired in**; it collapsed on real footage.
- **The surface is weighted occupancy, not a TSDF**: thin structures and free space are worse than
  a TSDF would get.
- **No texture atlas.** Colour is per vertex (`COLOR_0`), blended from the 4 best views among
  160 kept frames. The occlusion test is coarse: it tests against the mesh's own vertices in a
  2-pixel depth buffer, so an occluder the mesh does not contain (a passing car) is not caught.
- **Water is never labelled**; everything is ground or structure.
- **Feed-forward solving is not live**: it needs the recording first. The adaptive re-solve of
  difficult sections is not built.
- **Telemetry poses** place the camera at the car (a chase camera's offset is unknown). Positions
  are taken as Forza sends them (Y up, as in the lap files); the senses of yaw, pitch and roll
  were read off recorded laps (direction of travel, slope, which side's suspension compresses),
  not off the running game's camera.
- The overlay cannot draw over **exclusive fullscreen**; use borderless windowed.
- Global hotkeys, the click-through overlay and live capture are **Windows only**.
- Closing the window does not offer to save.

## What is measured

- `tests/test_accuracy.py`: a synthetic room with a known path and analytic depth - frames placed,
  path error, walked distance, room size, surface on the walls ([Level reconstruction](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: a road of known width driven off-centre reconstructs its width.
- `tests/test_track_scale.py`: surface extraction at racetrack scale, memory proportional to what
  was scanned, blocks joining into one surface.
- `tests/test_glb.py` plus the viewer's own tests: the `.glb` contract from both sides.
- How the depth network does on real gameplay is not something a synthetic scene can answer, and
  is not measured by the test suite.
