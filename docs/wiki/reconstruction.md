
# Level reconstruction from gameplay

Walk a level slowly, or drive a track, and the scanner turns what the screen showed into a
`.glb` that the 3DHeat viewer loads as context under the telemetry - the same file contract
the Unreal exporter writes. It is for the case where nobody exported the map and the game's
files cannot be read; an engine export or a game-file export is exact, this is an estimate.

## The pipeline

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Stage | Live scan (`heat3d_capture.ui`) | Offline (`reconstruct`) | Page |
|---|---|---|---|
| Frames | monitor, window or video, resized to the preset's longest side | video, sampled twice (solve plan and fuse interval) | [Capture](reconstruction-capture) |
| Keyframes | kept on how much the picture changed, threshold adapted to the capture | every `--fuse-interval` seconds | [Capture](reconstruction-capture#keyframes) |
| Masks | change-based `ScreenMask`, then flow-based `FlowMask` after 40 keyframes | `FlowMask` learned from four runs of the video; not applied to the solver | [Capture](reconstruction-capture#what-is-not-the-world) |
| Depth | ONNX model on the best GPU backend | PyTorch Depth Anything V2 Small | [Depth](reconstruction-depth) |
| Pose | visual odometry, or exact Forza telemetry | VGGT windows stitched into one path, interpolated | [Pose](reconstruction-pose), [Offline](reconstruction-offline) |
| Scale | camera height above the ground (1.15 m) once, or telemetry | the solved path's own units | [Pose](reconstruction-pose#scale) |
| Fusion | weighted occupancy, sparse voxels; coverage grid | the same | [Fusion](reconstruction-fusion-and-texture) |
| Output | `.glb`, ground/structure parts, vertex colour, centimetres | the same | [The .glb output](glb-output) |

Code: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - a scan's settings and pacing; `reconstruct.py` - keyframes into geometry;
`offline.py` - the offline path), with the stages in `capture/`, `depth/`, `pose/`, `fusion/`
and `geometry/`.

## Where accuracy comes from

Monocular depth is right only up to an unknown scale - a photo of a room and of a doll's house
are the same picture. So the network is left to do what it is good at (relative shape, edges,
thin structure), and scale and camera path come from somewhere that knows them:

| Game | Camera path | Scale |
|---|---|---|
| Forza Horizon / Motorsport with telemetry on | exact, from Data Out, interpolated to each frame's capture time | exact: depth is anchored by triangulating features between two known poses |
| Anything else, live | visual odometry, chained frame to frame | fixed once from an assumed camera height above the ground |
| A recording, offline | VGGT, solved over overlapping windows | the solve's own units (not metric) |

The one number the scanner is told rather than measures is the game's **horizontal field of
view** (90 degrees by default in the window; racing games are nearer 65). Too narrow and the
level reconstructs deeper than it is; too wide and it flattens.

## Telling the user early

A scan is a physical act - someone walks a level for several minutes - and the expensive
failure is finishing the walk and discovering it was no good. So the window measures this
machine's depth throughput before anything can start and says what the scan will be like
([Runtime](runtime#what-to-expect-from-this-machine)); during the scan it shows a coverage
map with numbered weak spots, tracking health, a walk-speed bar, a sharpness bar and one
instruction at a time, in the window and in a click-through overlay over the game
([The scan window](reconstruction-scan-ui)).

## Measured on synthetic ground truth

`tests/test_accuracy.py` renders a 12 x 8 m room (4 m high) from a known camera path, with
analytic (not network) depth, and reconstructs it at 0.2 m voxels. It asserts that more than
90% of frames are placed, the mean path error is under 0.35 m (worst under 1 m), the walked
distance is within 10% of the truth, the room comes out the right width to within 1.5 m, over
75% of the wall surface lies within 0.45 m of a real wall, a survey-style walk scores clearly
better coverage than walking straight ahead, and a featureless scene is refused rather than
invented. Analytic depth isolates pose, scale and
fusion from the network; how the network does on real gameplay is a separate question no
synthetic scene answers. `tests/test_track_width.py` checks that a lap driven off-centre on a
road of known width reconstructs the road's width, not just the driven line.

## Pages

- [The scan window](reconstruction-scan-ui) - every control, hotkey and overlay element
- [Capture, masks and frame quality](reconstruction-capture)
- [Depth](reconstruction-depth)
- [Camera pose and scale](reconstruction-pose)
- [Fusion, coverage and colour](reconstruction-fusion-and-texture)
- [The .glb output](glb-output)
- [Offline reconstruction](reconstruction-offline)
