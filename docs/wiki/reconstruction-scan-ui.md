
# The scan window

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Code: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
The window is a thin view over `scan/session.py` and `scan/reconstruct.py`; it owns no
scanning or geometry logic.

## Starting up

1. **Update check** - see [Updates](updates).
2. **Dependency check** - every package the scanner needs is checked before anything is
   imported; missing ones are listed with what they are for and the download size, and
   installed only after "Download and install". Cancel exits without changing anything. See
   [Runtime and dependencies](runtime#first-run-preflight).
3. **Window** - "3DHeat — Level scanner", 1420 x 900, Qt's Fusion style.
4. **Hardware check** - the best inference backend is chosen, the depth model is loaded and
   its throughput is measured on 6 frames; the verdict box at the top left says what the scan
   will be like (see [Runtime](runtime#what-to-expect-from-this-machine)).
5. **Global hotkeys** are registered last.

### When there is no depth model yet

If `models/` holds no `depth-*.onnx`, the verdict reads **"One more thing to set up."**, Start
is disabled, and a **Set up the depth model** button appears. It:

- checks for PyTorch, `transformers` and `onnxscript` (about 945 MB together), and asks before
  installing them;
- runs `tools/export_onnx.py --size small` as a separate process (so PyTorch never stays in the
  scanner's memory), with a 30-minute limit. The window does not respond while it runs;
- on success re-runs the hardware check; on failure shows the last 600 characters of the
  converter's output.

When several models are present, the choice is **by licence, not by file name**: `depth-small-*`
(Apache-2.0, commercial use permitted) whenever there is one, then Base, then Large (both
non-commercial). The verdict box and the grey line under the buttons name the file in use, its
licence, and any other model files present and not used - for example `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. To scan with Base, move the Small file out of `models/`.

## Left column: settings

| Group | Control | Default | Range / values | What it does |
|---|---|---|---|---|
| (top) | Verdict box | "Checking your graphics card…" | coloured green, amber or red by tier | Headline, `<device> via <API> — N views per second`, one note, and `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Where frames come from |
| | Which | `1` | monitor number / window title / path to a video | `monitor:<n>`, `window:<title>`, or a file path |
| | Choose file… | shown for video | `*.mp4 *.mkv *.avi *.mov` | Fills in the path |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Capture resolution and how selective keyframing is (below); a one-line summary is shown under it |
| | Game field of view | 90° | 30-140° | The game's **horizontal** field of view. Too narrow and the level reconstructs deeper than it is; too wide and it flattens. Racing games are nearer 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, step 0.05 | Voxel size of the surface. Smaller is finer and heavier |
| Stop after | Time | no limit | 0-120 min | Ends the scan after this long (0 = no limit) |
| | Views kept | 3000 | 0-100,000 | Ends the scan after this many keyframes, as a memory guard (0 = no limit) |
| What to ignore | Ignore HUD and anything on the camera | on | | Learns and masks the HUD, crosshair, weapon, bonnet, cockpit ([Capture](reconstruction-capture#what-is-not-the-world)). The line under it says what the detector currently decides |
| While you play | Show feedback over the game | on | | Opens the click-through overlay while scanning. The hint below it: run the game in **borderless windowed**; exclusive fullscreen cannot be drawn over by anything |
| Racing telemetry (Forza) | Listen for position data | off | | Takes the camera path from Forza's Data Out instead of estimating it ([Pose](reconstruction-pose#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | The Data Out port |
| | (status line) | | | `N packets — poses come from the game, not from the picture`, or `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Starts or stops; shows the hotkey when it was registered |
| | **Set up the depth model** | hidden | | See above |
| | **Save level…** | disabled | | Enabled after a scan that produced surface voxels; asks for a file name (default `scan.glb`) |
| | (grey line) | | | `Model: <file> (<licence>) · Available: <backends>`, plus setup notes such as installing `onnxruntime-gpu` |

### The presets

| Preset | Capture longest side | Keep quantile | Starting threshold | Summary shown |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Fast and rough. Good for checking a route before a real scan. |
| Balanced | 960 px | 0.65 | 0.010 | The usual choice. Walk at a normal pace. |
| Detailed | 1280 px | 0.40 | 0.004 | Slow and thorough. Walk deliberately and turn gently. |

The keep quantile means "keep a frame when it changed more than this quantile of the last 240
frames' changes" - Draft keeps roughly the busiest 15%, Detailed the busiest 60%. See
[Keyframes](reconstruction-capture#keyframes).

### Settings that are fixed in the window

The window always reconstructs while scanning, uses a camera height of **1.15 m** for the
ground-plane scale (the walking value 1.70 m is not selectable), and lets the backend ladder
pick the GPU. These are `ScanSettings` fields (`camera_height`, `prefer_backend`) that only a
script can change.

## Right column: what the scan is doing

| Element | Shows |
|---|---|
| **What the camera sees** | the last keyframe |
| **Shape it is reading** | its predicted depth, coloured with the Turbo colour map, normalised between the 2nd and 98th percentile of that frame (so one sky pixel does not flatten the range) |
| **Coverage — where you have been, and how well** | a plan view (see below) |
| **Worth another look** | the weak spots, numbered to match rings on the map, each with an instruction; worst (largest) first, at most 8; then the spots you marked (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Walk-speed bar | `walk speed — N% of the way to the next view`: the last frame's picture change divided by the **threshold in use** - the preset's starting value for the first 30 frames, the adapted one after that ([Keyframes](reconstruction-capture#keyframes)) |
| Health line | tracking health, or a capture warning (below) |
| Size line | `Size: ...`, how the level's scale was fixed or why it was not ([Scale](reconstruction-pose#scale)) |
| Statistics line | `views  frames  dropped  depth-per-second  seconds`, and while reconstructing `placed  cells  % well seen  metres`, plus `recovered` and `loops closed` when either is non-zero |
| Hotkey line | the registered keys, or why they could not be registered |
| Hint line (amber) | live advice (below), the scan's final message, and marks |

### The coverage map

Redrawn every 900 ms on a background thread (never on the interface thread), at 200 x 200
cells scaled to 420 px:

- each column of the coverage grid takes the **best** observation quality in it (so a
  well-seen floor is not painted amber by a poorly seen ceiling above it);
- the ramp runs red (bad) - amber (thin) - yellow (acceptable) - green (good);
- never-observed cells are a distinct dark grey, so an unexplored corner does not read as a
  badly scanned one;
- the walked path is drawn as a thin light line, the current position as a white dot;
- weak spots are white rings with their number;
- spots you marked are amber squares labelled `M1`, `M2`, …

How quality and weak spots are computed: [Fusion, coverage and colour](reconstruction-fusion-and-texture#coverage).

### The health line

| Tracking health (frames placed / frames) | Text | Colour |
|---|---|---|
| no frames yet | Waiting for the first frame. | grey |
| 90% or more | Tracking well — N of M frames placed. | green |
| 60% or more | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | amber |
| below 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | red |

A capture warning from the coverage grid replaces it (red when the scan is judged not
reconstructable, amber otherwise): almost no parallax, everything seen from more than 25 m,
or thin parallax. See [Coverage](reconstruction-fusion-and-texture#is-this-reconstructable).

### The hint line

| Condition | Hint |
|---|---|
| more than half the frames dropped, after 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| fewer than 0.3 views kept per second, after 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| more than 8 views kept per second, after 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| scan ended | the session's message: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, or `failed: <error>` |

## Hotkeys

Registered with Windows (`RegisterHotKey`), so they work while the game has focus. Alt-tabbing
out of a full-screen game is exactly what ruins a capture.

| Keys | Action |
|---|---|
| **Ctrl+Alt+F9** | Start / stop scanning |
| **Ctrl+Alt+F10** | Mark this spot to revisit (while scanning) |
| **Ctrl+Alt+F11** | Show / hide the overlay (toggles the "Show feedback over the game" box) |

- They are registered once, when the window opens, and released when it closes; while
  registered, these key combinations are taken away from every other program, including the
  game. F-keys with two modifiers were chosen because games rarely bind them.
- Auto-repeat is suppressed (`MOD_NOREPEAT`), so holding a key does not toggle the scan
  dozens of times.
- A key another program already holds is reported (`... unavailable: another program already
  has this key`) and the others still work. A button only advertises a key that was actually
  registered.
- The keys are fixed in the code (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); the parser
  accepts F1-F12 with `ctrl`, `alt` and `shift`. Outside Windows there are no global hotkeys
  and the window says so.
- **Mark** records the current camera position (the last placed frame's) and shows "Marked MN.
  Marked spots are on the map and saved with the level." Before any frame has been placed it
  says there is nowhere to mark. Marked spots are drawn on the window's map and the overlay's as
  amber squares labelled `M1`, `M2`, …, listed under the weak spots, counted in the overlay's
  stats line, and saved with the level (below).

## The overlay

A small panel pinned over the game so the feedback is where the eyes already are.

- Frameless, always on top, a tool window (not in the taskbar or alt-tab), transparent to
  input in Qt and made click-through in Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), so a
  click meant for the game is never swallowed. Shown without taking focus.
- Top-right corner of the primary screen, 18 px from the edges; 214 x 358 px.
- Opens when a scan starts (if "Show feedback over the game" is on), closes when it stops.
- **Needs borderless windowed mode**: nothing can draw over exclusive fullscreen - not this,
  not Steam's overlay, not Discord's.

From top to bottom it shows:

| Element | Content |
|---|---|
| Coverage map | 190 px, the same map as the window at a coarser 120 x 120, with the path, weak-spot rings and marked spots |
| Health | the same text and colour as the window's health line |
| Stats | `N placed · M to revisit · X m`, with `· K marked` when any are |
| **movement** bar | the same as the window's walk-speed bar: the last frame's picture change over the threshold in use, full when the next frame will be kept |
| **sharpness** bar | sharpness relative to this capture's own median: green from 0.75, amber from 0.45, red below |
| Advice | one instruction, green / amber / red (bold when not "ok") - see [frame quality](reconstruction-capture#frame-quality-and-advice) |
| Hotkeys | the registered keys |

If updating the overlay ever throws, it switches to a red **"Feedback stopped"** panel saying
that anything shown before is out of date, that the scan is still running and the main window
still correct, with the error and a count. A panel that froze while green would otherwise go on
reading as confirmation.

## Saving

**Save level…** writes the reconstruction as a `.glb` (see [The .glb output](glb-output)).
If the volume produces no surface, "Nothing to save" explains that tracking was probably lost
for most of the scan. On success: "Written to <path> ... Load it in 3DHeat through the Level
panel.", naming the marks file too when there are marked spots.

Marked spots are written beside the level as **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` is in the level's own coordinates (the GLB's scale applied, so a mark sits on the mesh
it was made over), `metres` in metres; `number` matches `M1`, `M2`, … in the window. When the
scale was found on a later keyframe ([Scale](reconstruction-pose#scale)), both include that
factor.

Stopping a scan keeps what was gathered; a new **Start** discards the previous scan.
**Closing the window does not ask to save**: it stops the scan, releases the hotkeys and
closes the overlay.
