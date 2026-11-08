---
title: Locating frames in a level
nav_order: 91
---

# Locating frames in a level

`locate` works out where each frame of a gameplay recording was taken - the camera's 3D position
and view direction - by matching the picture against renders of the level's own geometry. It is
for games that keep no record of where the player was: no demo, no replay file, no telemetry.
Battlefield 6 is the first.

```bash
# Once per level: render it from every place a player can stand, and index the renders.
.venv/Scripts/python -m heat3d_capture locate build level.glb -o level.db

# Per recording: where was each frame taken?
.venv/Scripts/python -m heat3d_capture locate frames "<recording>.mp4" --db level.db -o out/match
```

The position comes **from the picture**, against the whole level, with no prior. The minimap track
of the [HUD reader](hud-video.md) is only a fallback for frames the picture cannot place, and every
row says which of the two it came from.

## What it does and does not touch

- It reads the player's **own recording** and a level file the player exported from their **own
  copy** of the game. It never touches the game, its memory, its files while it runs, or its
  network, and it runs after the match. See [The rules](rules.md).
- It places **only the player's own camera**: the frame is the player's own view.
- The level, the database built from it and everything rendered from it belong to the game's
  publisher. Keep them local.

## Requirements

- What `requirements.txt` lists, PyTorch (from pytorch.org, for the GPU), and
  `requirements-locate.txt`:

```bash
.venv/Scripts/python -m pip install -r requirements-locate.txt
```

- A GPU with OpenGL 3.3 (4.3 is faster) for the renders, and preferably CUDA for the models. On a
  CPU it works, slowly.
- The models are fetched on first use (about 450 MB): DINOv2 from Hugging Face, ALIKED and
  LightGlue through kornia. All are licensed for commercial use; see [Licences](#licences).
- The **level** as a `.glb` (or `.gltf`) in the viewer's frame, Y up, **with its base colour
  textures**, as the 3DHeat exporters write it (`ground:` / `structure:` parts; the part names are
  not needed). One unit is one metre unless the file's `extras.unit_metres` says otherwise. An
  untextured level works much less well; see [Limits](#limits).

## Commands

### `locate build <level> -o <db>`

Renders the level from every place a player could stand and stores, per render, its pose and one
global descriptor.

| Option | Default | Meaning |
|---|---|---|
| `level` | | The level's `.glb` / `.gltf`. |
| `-o`, `--out` | | The database folder to write. |
| `--game` | `bf6` | The game profile: eye heights, field of view, HUD boxes, speed (below). `generic` for any first-person game. |
| `--eye` | the profile's | Eye heights above the floor in metres, standing first. One database view per height. |
| `--fov` / `--vfov` | the profile's | The recording's horizontal field of view, or the vertical one (Battlefield's slider) for a 16:9 recording. |
| `--spacing` | 2.5 | Metres between the places views are taken from. |
| `--yaw-step` | 30 | Degrees between the views' directions. |
| `--pitch` | 0 | Pitches to render at, degrees up. |
| `--positions` | none | A table (Parquet or CSV with `x`, `y`, `z` at the feet, in the level's frame) to take places from instead of every floor: a previous run's output, say. |
| `--shadows` | off | Cast the sun's shadows in the renders (the level's own sun when its file names one in `extras.sun`). |
| `--untextured` | off | Render shape and light only. |
| `--box X0 Z0 X1 Z1` | the whole file | Only places inside this box (level units): the play area. |
| `--places` | `auto` | Where views are taken from: `nav` - players at eye height over the level's navigation mesh (`nav:` parts: exactly where the game lets them walk), vehicle cameras at their height over the `ground:` parts (terrain and roads) within 50 m of it; `ground` - both over `ground:`; `floors` - over every upward face (roofs and crates too); `auto` - `nav` when the level has a navigation mesh, else `floors`. |
| `--head` | none | A per-map head from `locate train` for the descriptors. |

Writes `<db>/db.json` (what it was built from and with) and `<db>/views.npz` (poses, descriptors).

### `locate frames <recording> --db <db>`

| Option | Default | Meaning |
|---|---|---|
| `source` | | A video, a picture, or a folder of pictures (taken in name order, `--fps` apart). |
| `--db` | | The database `build` wrote. Its level file must still be where it was (or `--level`). |
| `-o`, `--out` | `<source>.locate` | Output path without extension. |
| `--fps` | 2 | Frames located per second of video. |
| `--start`, `--seconds` | all | The part of the video to read. |
| `--width` | 1280 | The width frames are matched at. |
| `--shortlist` | 8 | Database views tried per frame near a prior or a fix. |
| `--search-shortlist` | 16 | With no prior: database views tried per frame ([searched together](#with-no-prior-frames-searched-together)). |
| `--no-search` | off | With no prior: search each frame on its own and believe its fix without its neighbours. |
| `--checkpoint` | none | Keep the run's state here and carry on from it if it is there. |
| `--stop-file`, `--stop-process` | none | Stop by itself, state saved, exit code 75, when this file exists or a process runs whose name starts with this (checked before every frame; may be repeated), so that a long run frees the machine for a game. The same command carries on. |
| `--normalise` | none | Light normalisation before matching: `clahe`, `gray`. |
| `--minimap` | none | The `hud` verb's table: the **fallback** for frames the picture cannot place. |
| `--prior-radius` | none | **Optional speed-up**, off by default: search only database views this many metres from the minimap's position (needs `--minimap`). |
| `--minimap-anchor` | none | A JSON file tying the minimap to the level ([the minimap as a search prior](#the-minimap-as-a-search-prior)): the minimap cuts the search from the first frame; fixes found so are `visual+minimap-prior`. |
| `--no-level-search` | off | With a prior: when nothing near it fits, do not search the whole level as well (faster). |
| `--lives` | the `--minimap` table | The `hud` verb's table whose deaths, deploys and revives say when the player was in play: positions jump only across a death ([lives from the footage](#lives-from-the-footage)). |
| `--no-sequence` | off | Decide every frame on its own, not along the run (below). |
| `--fit-fov` | off | After the run, fit the field of view to the strongest fixes, per view, and report it. |
| `--check-every` | 0 | Also every N frames, placed or not, a picture into `<out>.check`. |
| `--no-checks` | off | Do not write the check pictures of the visual fixes (below). |
| `--no-zoomed` | off | Do not solve zoomed views from their neighbours' fixes (below). |
| `--game`, `--eye`, `--fov`, `--vfov`, `--mask`, `--no-hud-mask`, `--max-speed` | the profile's | As above; `--mask x,y,w,h` adds a screen box (on a 1920x1080 screen) that is not the level. |
| `--vehicle-vfov` | the profile's | The vertical field of view of vehicle cameras (Battlefield's vehicle slider). |
| `--settings` | the newest settings file | `bf6`: the game's settings file the fields of view are read from (read only) when no `--fov`/`--vfov` is given; by default the newest `PROFSAVE*_profile` under `Documents/Battlefield 6/settings`. It holds the settings as they are now, which may not be how an older recording was made. |

### `locate refmap <level> <deploy screen> -o <refmap>`

Places the game's own map on the level: the reference the minimap is read against
([the minimap, read against the level](#the-minimap-read-against-the-level)). `<deploy screen>` is
a picture of the deploy screen showing the whole map, or a recording with `--at <seconds>` at such
a moment; the profile's map box is cut out of it (`--whole-picture` keeps all of it). Writes
`<refmap>.png` (the map resampled onto the level's own frame, `--mpp` metres a pixel, default 0.5),
`<refmap>.valid.png` (where it is the map, not a marker or label) and `<refmap>.json` (the frame and
the calibration, with how far the map's tiles were from it). `--topdown <prefix>` keeps the level
rendered from above for the next run (`--topdown-mpp`, default 0.656 m; `--box` limits it).

### `locate minimap <recording> --refmap <refmap> -o <table>.parquet`

Reads the recording's minimap against the reference map, frame by frame (`--fps`, default 2):
position, heading and zoom of every minimap that matches, in the level's frame, written as a
minimap table with an anchor beside it (`<table>.anchor.json`) that `locate frames` takes as
`--minimap <table>.parquet --minimap-anchor <table>.anchor.json`. With the `hud` verb's table
(`--hud`) its lives are carried over; with an anchor for that table too (`--hud-anchor`) the first
search is round where it puts the player, and where no minimap matches the HUD's own track fills
in, moved onto the nearest reference-map fixes (`--hud-fill`, seconds, default 120; 0 turns it off).
The table's `source` says which (`refmap`, `hud`).

### `locate eval <out>.parquet --truth <poses>`

Compares a result with known camera poses: a table of `time`, `x`, `y`, `z` (the eye), `yaw`,
`pitch` in the level's frame. `--offset` is the clock offset (truth time = video time + offset);
without it the offset is searched for. `--unit-metres` turns the errors into metres.

## Game profiles

| | `bf6` | `generic` |
|---|---|---|
| Eye heights | 1.6 m standing, 1.05 m crouched (not yet measured in the game) | 1.65, 1.1 m |
| Field of view | 55 degrees vertical, about 86 horizontal at 16:9: **pass the player's own** with `--vfov` | 90 horizontal |
| HUD masked | minimap and squad list, kill feed, compass, ammunition, the player's weapon, the pop-ups, the crosshair | the crosshair |
| Fastest on foot | 8 m/s | 8 m/s |
| Views told apart | on foot, vehicle, zoomed (below) | every frame on foot |
| Vehicle cameras | the vehicle slider (from the settings file), the vehicle masked, the camera up to 8 m over the floor, 30 m/s | - |

The field of view matters most: a frame solved with the wrong one is solved with the wrong focal
length, and its position slides along the view.

## Outputs

### `<out>.parquet`

One row per located frame, in the **level's frame** (Y up, the level's units), with the viewer's
reading instructions in the footer (`kind: heat3d-locate`). The footer names every column that has
no role of its own as an extra, so the viewer keeps them all (its inspect card shows them).

| Column | Meaning |
|---|---|
| `time` | Seconds from the start of the video. |
| `event` | `start` on the first row of a life, `position` on the rest. |
| `x`, `y`, `z` | The eye, smoothed within the life. Empty where neither source placed the frame. |
| `yaw`, `pitch` | Degrees: yaw about the up axis (0 along +X, growing towards -Z, which is a game's own yaw in the viewer's frame), pitch up from the horizontal. `pitch` is empty for minimap rows. |
| `dir_x`, `dir_y`, `dir_z` | The view direction. |
| `player`, `team`, `session` | `me`, `own`, and `<video>#NN`, one per life. |
| `life` | The life the footage showed the frame in (from the HUD's deaths; 1 = the first). Empty when out of play (dead, down, deploying) or when the lives were not read. `session` is the track's life, which can also split at a jump. |
| `source` | `visual` (from the picture), `visual+minimap-prior` (from the picture, the search cut to the minimap prior), `minimap` (the fallback), `minimap+nav-floor` (indoors: the minimap and the navigation mesh's floor) or `none`. |
| `view` | `foot`, `vehicle`, `zoomed` or `screen` (below). |
| `cam_x`, `cam_y`, `cam_z` | The camera that saw the frame. On foot and through a sight it is the eye, and `x`, `y`, `z` are the same; in a vehicle's third-person view `x`, `y`, `z` are the vehicle (the offset model below) and the camera rides behind and above it. |
| `hfov`, `zoom` | The horizontal field of view the frame was solved with, and for a zoomed view its zoom against the normal view. |
| `confidence` | 0..1: how far to trust the row (below). |
| `uncertainty` | The row's typical error, level units: for a visual fix from its inliers and its neighbours, for a minimap row from the fit (below). |
| `inliers`, `rmse` | The visual solve's PnP inliers and reprojection error (pixels at the working width). |
| `x_raw` ... `pitch_raw` | The visual solve before smoothing (also for outliers that were voted out). |
| `kept` | The visual fix survived the outlier vote. |
| `note` | Why a frame was not placed, or was voted out. |

### `<out>.summary.json`

Frames, visual fixes, outliers, lives, rows per source, the minimap fit (pairs, inliers, residual),
time per frame.

## Method

### The database

Places are points on every upward-facing triangle of the level, spread evenly (one per `--spacing`
on a 3D grid, so the floors of a building each get theirs). Each is checked from its eye with six
small depth renders: a camera inside geometry sees mostly back faces, a crawl space has something
solid over the eye; both are dropped. From each place the level is rendered at every eye height,
every `--yaw-step` and every `--pitch`, and each render is described by **DINOv2** (its patch tokens
pooled by generalised mean, joined with the class token).

The local features and 3D points that a frame is finally solved against are **not stored**: they are
made again when needed by rendering the few views retrieval picked, which takes milliseconds. That
keeps a database at a few hundred megabytes rather than tens of gigabytes, and it is what allows the
refinement below. The cost is that `frames` needs the level file and a GPU, not only the database.

### One frame

1. **Mask** what is not the level: the profile's HUD boxes and the crosshair, plus any `--mask`.
2. **Retrieval** over the **whole level**: the frame's descriptor against every database view; the
   most similar few dozen, thinned so they hold different places and directions, are the shortlist.
3. **Matching**: each shortlisted view is rendered again at the frame's size and field of view, with
   its depth. ALIKED keypoints of frame and render are matched with LightGlue. A matched render
   pixel plus its depth is a 3D point of the level, so each match is a 2D-3D correspondence;
   keypoints on a depth edge (whose depth may belong to what is behind them) are dropped.
4. **Pose**: PnP with RANSAC (SQPnP), then a robust refinement that keeps the camera level - a
   first-person view does not roll - and minimises the reprojection error of the inliers.
5. **Is it possible?** A pose must be at a player's eye height over a floor and outside geometry
   (a depth render straight down). A look-alike texture elsewhere - a tiled floor matched to a wall
   of the same material - can give hundreds of inliers at a pose no player could have; those are set
   aside, however many inliers they have.
6. **Render and compare**: the level is rendered at the solved pose and matched again, which
   replaces a database view up to a few metres and tens of degrees away with one that nearly
   coincides with the frame. Repeated while it gains inliers (at most twice).
7. **Choosing**: the strongest three places (more than about 3 m apart) are each refined before one
   is chosen. A look-alike can lead before refinement; the right place gains far more from it.
8. **Verdict**: `confidence` combines the inlier count, the best other place (`runner_up`) and the
   reprojection error. A fix is `ok` with at least 25 inliers, no other place within 80% of its
   inliers, and a confidence of at least 0.85 - the threshold the measurements below put at 97.5-99%
   right.

### Views

A frame is not always the player's eyes. The profile's detector reads which view it is from the
HUD, and the frame is solved accordingly:

- **On foot**: the infantry field of view and eye heights.
- **Vehicle** (Battlefield 6: the seat diagram's key prompts, `C CAMERA` and `E EXIT`, at the bottom
  centre): the vehicle field of view, the vehicle itself masked (the lower middle of the screen in
  its third-person view), and a camera allowed up to 8 m over the floor. The fix is the camera's.
- **Screen** (dark edges round a dark middle: the deploy map, a menu, the scoreboard): not a view
  of the level; skipped.
- **Zoomed** (a scope, a gunner's sight, a vehicle's own first-person view: one screen edge black,
  both dark, round a bright picture): not searched for over the level - a scope's sliver of the
  level resembles none of the database's wide views - but solved after the run from the nearest fix
  within 6 s, below. Off with `--no-zoomed`.

### Zoomed views

A narrow view pins its position poorly: a step back with a little more zoom looks almost the same.
So a zoomed frame starts from where its neighbour says the sight is - on foot that fix's eye, in a
vehicle 2.5 m over the ground under the vehicle's middle (a turret's sight) - and how far it may
have moved since: 2 m, plus 4 m a second on foot or 8 in a vehicle, at most 12 m (`reach`).

1. **Direction and zoom, the position held.** For each zoom of 1, 1.2 (a vehicle's own view,
   narrower than on foot), 1.5, 2, 3, 4, 6 and 8, the level is rendered at the seat in directions
   within 30 degrees of the neighbour's (and, from 3x, a few pitches). The frame's keypoints matched
   to a render, with the level points under them, are rays from the seat; a rotation is fitted to
   them two at a time (RANSAC) for focal lengths from 0.75 to 1.3 times that zoom's, a point
   agreeing within an angle that allows for the seat being `reach` off at its distance. The zoom,
   direction and focal length most points agree with win.
2. **Settled.** Those points then fit position, direction and focal length together, by their
   reprojection error, the position held to the seat by a cost of two pixels per `reach` moved;
   rendered once more at the answer and fitted again. Inliers and error are counted in pixels, and
   the fix is `ok` by the same confidence as any other.

The zoom written (`zoom`) is against the run's field of view on foot; `hfov` is the solved one. In
a vehicle the position written is the vehicle's, 2.5 m below the sight, as for its third-person
view.

### Vehicles: the camera and the vehicle

In a vehicle's third-person view the solved pose is the chase camera's, which rides behind and
above the vehicle and swings round it as the player looks about. The position written (`x`, `y`,
`z`) is the vehicle's - the ground under its middle: the camera's plus the profile's
`vehicle_offset`, so many metres ahead along the camera's horizontal view direction and so many
down. The camera stays in `cam_x`, `cam_y`, `cam_z`. The conversion is made before the sequence and
the track, so a camera swinging round a standing vehicle is not taken for movement. The table's
footer carries the offset used and whether it was measured (`vehicleOffset`). On foot and through
a sight there is no offset.

How the Battlefield 6 offset was measured: on eleven right fixes of real third-person frames of a
main battle tank, the middle of the tank was marked by eye on the frame, and the level rendered
at the fix gave the ground at that pixel (its depth). The ground under the tank's middle lies
7.9-11.7 m ahead of the camera (median 9.6) and 3.3-4.8 m below it (median 3.7), within a couple
of metres to the side; the profile takes (9.6, 3.7). The marking is good to a metre or so, and it
is one vehicle type: a car or a helicopter rides its camera differently. A minimap cannot measure
it - one of its pixels is about two thirds of a metre, and too few vehicle fixes had a minimap
beside them to fit an offset to.

### With no prior: frames searched together

One frame's global descriptor against a whole level is a weak signal, and one frame's inliers do
not tell a right place from a look-alike. So with no prior the frames of a recording are described
first and searched together (`search.py`), and a fix is believed only with the frames around it:

- **Shortlist.** Each view's similarities are measured against its own mean and spread over the
  recording, so that a view resembling every frame stops winning everywhere. Each frame scores the
  cells of a 24 m grid by the rank of their best view; the best path through the cells along each
  life, within what the player can cover between frames, gives a belief per cell, and the best view
  of each cell, best believed first, is one list. Plain retrieval is the other, and the two are
  taken in turn: measuring views against the recording punishes a place the player hardly leaves,
  which is where plain retrieval does well.
- **Believing.** A candidate counts only if its inliers cover at least 12% of an 8 x 8 grid over the
  frame: a look-alike is a repeated object, a stack of containers, with hundreds of inliers on a
  few cells of the frame. A fix is believed when it lies on the best path through the counting
  candidates (below) with at least two neighbours within 6 s that agree with it. A frame out of
  play is not searched at all.
- **Growing.** Only what is believed is grown from, and a grown fix must cover the frame in the same way.

### Along the run

Each frame keeps every physically possible pose it found, one per place (`candidates`), not just
the strongest. The run then picks one per frame - or none - so that the chosen poses form a path a
player could have walked or driven, and as many inliers as possible lie on it: a hidden Markov
model, decoded at once (Viterbi). A look-alike that wins one frame on its own loses to the place
its neighbours agree with; a weak candidate the path runs through, with at least two agreeing
neighbours, becomes a fix (`note`: chosen along the sequence); a confident fix its neighbours all
contradict stops being one. A neighbour counts as agreeing only within 6 s: further apart, the
distance a player - let alone a vehicle - could have covered is so large that agreeing says
nothing. Off with `--no-sequence`.

### Frame times

A row's `time` is the frame's own timestamp in the recording, not its count over the nominal frame
rate. Recordings drift from their nominal rate (by up to 0.37 s within a clip, on the ones
measured), and everything that reads a frame back by its time -
the check pictures, the zoomed pass, `locate train --real`, the minimap from the `hud` verb - seeks
by timestamp. Counted frames would put the check picture's frame up to that far away from the one
located.

### The field of view, from the frames

`--fit-fov` keeps the strongest fixes of a run (per view) and refines each one's pose and focal
length together on its inliers; the median over them is the field of view the recording was made
with, reported in the summary (`hfov_fitted`) for the next run's `--fov`. Near and far points move
differently under a change of focal length than under a change of position, which is what pins
it down; it needs fixes with depth in them, not a flat wall.

### A per-map model

`locate train` trains a small head on top of DINOv2 for one level, on renders of it, so that the
global descriptor finds the right views of real frames rather than of renders alone:

- **Head**: each patch token through a two-layer projection, pooled by generalised mean over the
  patches that show the level, joined with the projected class token. DINOv2 stays frozen. All of
  it written here (MIT).
- **Pairs**: a place on the walkable ground and a direction, rendered twice from poses up to a
  metre or two and a dozen degrees apart, at fields of view up to 10 degrees apart, under
  different light (sun, shadows, ambient), each through a game-like look: grading, haze by depth,
  bloom, vignette, smoke, people in the way, the player's own vehicle in vehicle views, motion
  blur, noise, JPEG (`augment.py`). Masked like a frame. Places within a few metres facing the same
  way are not counted as negatives.
- **Real frames**: frames with a pose the pipeline found itself (pseudo-labels: fixes chosen along
  a sequence) can join as pairs - the frame and a render at its pose - in a second round.
- **Loss**: contrastive (InfoNCE) over the batch.

`locate build --head <head.pt>` builds the database with it; `frames` then uses it for the frames.

### Checking by eye

Every visual fix gets a picture in `<out>.check` - `<time>s_<view>_visual.jpg`: the frame, and
beside it the level rendered at the fix's camera with the frame's edges drawn over the render.
Where they line up, the fix is right. Written after the sequence and the track have decided, so
the pictures are exactly the rows the table calls visual. Off with `--no-checks`.

### The minimap, read against the level

A minimap stitched into one mosaic (the `hud` verb's) is not flat: its scale drifts with the zoom
each minimap was registered at, a place seen twice can be drawn twice, and each clip's mosaic is
its own. A similarity fitted to a few fixes then holds near them and is tens of metres off away
from them. So the minimap is placed by the level itself, in two steps, and nothing is stitched:

- **The reference map** (`locate refmap`). The deploy screen draws the whole map north up, flat, at
  one scale. The level rendered from straight above shows the same things standing up from the
  ground (tanks, buildings, walls): on the level, their height over the ground 15 m round; on the
  map, what is drawn lighter than the ground round it. The map is laid on the level by normalised
  cross-correlation of the two over scale and a small turn, refined by matching tiles of it one by
  one, and last by all of the map at once round that answer (a few dozen tiles leave the scale
  loose by a percent, metres at the map's ends). The result is one similarity, map pixel to level.
- **The minimap, frame by frame** (`locate minimap`). Each sampled minimap - the HUD reader's crop
  and overlay mask - is matched (SIFT) to the reference map round where the player last was, or
  anywhere when nowhere is known, and a similarity (turn, zoom, shift) is fitted. The player's point
  carried through it is the position, the minimap's up (the view cone) the heading, its scale the
  zoom - measured, not assumed.
- **Where it does not match.** The deploy screen draws nothing outside the play area; a minimap
  that shows mostly what lies outside it - a player at the edge of the map - has nothing to match.
  There the HUD's own track stands in, moved by the offset the nearest reference-map fixes measured
  (`--hud-fill`); it is as good as the mosaic is near those fixes.

On the test level (Battlefield 6, ten clips) the minimap read this way was 3.2 m (median) and
6.5 m (90th percentile) from 960 confident picture fixes of seven clips - the same inside the area
the old fitted anchor had fixes in (2.9 / 6.2 m) as outside it (3.4 / 6.6 m), where the anchor was
10.7 / 24.5 m off. Of those fixes 5 were more than 15 m from it, against 117 for the anchor. The
fixes still sat about 2.5 m west of it on average: what is left of the reference map's placement.
The minimap's zoom, measured on every matched minimap, was the same in every view: 0.68 m of the
level a pixel of a 1080p minimap on foot, in a vehicle and through a sight (10th-90th percentile
0.65-0.73) - the minimap does not zoom out in vehicles; the varying zoom the mosaic showed was the
mosaic's own drift. On the held-out clip, with this as the prior, the run placed 117 frames from
the picture against 50 with the fitted anchor, its own corrections fell from 9.5 m to 2.5 m, and it
ran a third faster (the disc is smaller).

### The minimap as a search prior

The `hud` verb's minimap track says, for most frames of play, roughly where the player is and which
way they look - in its own units (minimap pixels, north up). Tied to the level once, it cuts the
search to a small part of it; the pose itself still comes from the picture, by the same rules.

- **The anchor** (`--minimap-anchor <anchor.json>`): one similarity per map, minimap to level -
  scale, turn (with the mirror between north-up pixels and the level's axes), shift - fitted on the
  confident visual fixes (confidence 0.7 and up) of several clips. Each clip's minimap is a mosaic
  the HUD reader stitched on its own, so each sits somewhere else in minimap units; two mosaics of
  one map differ only by a shift, found by matching keypoints between them (the shift most matches
  agree on), and every mosaic is tied to one reference through all the pairs that agree well. The
  anchor file carries the map's similarity, the clip's shift (`clip_shift`), and the error the
  anchor showed against fixes of clips left out of its fit (`median`, `p90`, metres).
- **Where and which way.** The minimap's heading is the camera's yaw: on the clips measured it
  agreed with the solved yaw within 2-5 degrees. So a frame is first matched against renders made
  where the minimap puts the camera - on foot an eye over the ground there, in a vehicle the chase
  camera behind and above it (the vehicle offset) - looking along the heading: the point and 4 m to
  each side, at two pitches (`seeds`). Only when none of those gives a fix are the database's own
  views within the disc tried (30 m plus the anchor's 90th-percentile error).
- **Corrected as the run goes.** Every confident fix near the prior says how far off the anchor is
  there; the median of those within 2 minutes corrects the prior, and their spread (at least 5 m)
  replaces the anchor's error in the disc's radius - up to 10 m: fixes that disagree more say the
  minimap is off with place, not that anything 50 m away will do. With no fix within 2 minutes the
  prior is not corrected at all (the error elsewhere in the clip says nothing about here).
- **Anchors with a grid.** An anchor may also carry `grid`: level x and z on a regular grid over
  the clip's minimap units, read bilinearly; inside it the grid places the point, outside it the
  similarity. A `locate minimap` table's anchor is the identity (its table is in the level's frame
  already).
- **Weak fits.** With a prior, a fit that is weak (25 inliers or more, but not confident enough on
  its own) and lies within the disc is kept - with its lower confidence - for the sequence and the
  track to judge, not dropped: smoke, rubble and destroyed walls leave real frames fewer matches.
- **Sources.** `visual` - the picture placed it, no prior; `visual+minimap-prior` - the picture
  placed it, the search cut to the prior; `minimap` - the picture did not, the minimap stands in;
  `minimap+nav-floor` - indoors, below.
- **Indoors** the minimap leads. A frame the picture did not place, on foot, where an eye at the
  minimap's position sees the level close all round (median distance under 8 m four ways) and no
  sky, is indoors: it gets the minimap's x and z and the height of the navigation mesh's floor
  there - of several floors, the one nearest the last fix - with `source = minimap+nav-floor`, so
  that it is clear the picture did not fix it.

### Lives from the footage

A position may jump only where the player died. The lives are not guessed from the positions - a
single wrong fix would open a new one - but read from the footage: the HUD reader's table records
the deaths the down and deploy screens showed (`death`), the downs a teammate revived (`downed`,
`revived`), the deploys (`spawn`) and where play started and stopped (`start`, `end`); `lives.py`
turns them into lives. A death closes a life, the first frame of play after the deploy screen
opens the next; a revive does not cut it (the player is where they went down), and the frames
while down are not placed; a stretch of menus or loading longer than 10 s cuts it too. Frames out
of play (dead, deploying, down) are never placed.

Within a life continuity is a hard rule: each step at most the speed times the time between, plus
1.5 m. The speed is the frame's: on foot the profile's, in a vehicle the speed the vehicle's own
readout showed within 3 s (a third again, and 2 m/s, for speeding up) or, where it shows none, its
class's limit. Along the run (Viterbi) a step across a death is free at any distance, every other
step bounded; a frame that would need a jump is left out - the weaker side of a contradiction
loses (fewer inliers, less support) - and the life is never split on it. Where the left-out side
is itself strong (confidence 0.9 and up, two or more fixes agreeing with each other), the run does
not guess: both sides are kept and marked `jump without detected death` (a missed death, or a real
teleport), and listed in the summary. The minimap fallback follows the same lives.

Battlefield 6: the tanks' first-person view shows the speed (`<n> KPH`, right of the sight; read
with the HUD reader's OCR); the third-person view does not. The fastest reading on the clips was
36 km/h, so ground vehicles are allowed 15 m/s where nothing is read. Boats, helicopters and jets
get generous limits (20, 90 and 280 m/s) that are not measured: no clip shows one being driven or
flown, and the view classifier does not tell air from ground - a stretch faster than a ground
vehicle shows up as a jump, flagged, not trusted.

### Destruction

The level files are the intact level; in a match walls, houses and rocks are shot away, rubble
and smoke hang about, and it gets worse as the match goes on.

- **Matching trusts the static level.** A part the export tags as destructible (its name starts
  `destructible:`, or `extras.destructible` on its node, mesh or primitive) is drawn into the
  render's `destructible` mask. Matches whose level point lies on it are dropped when 40 or more
  matches on static parts remain - terrain, roads, the large structures carry the solve.
- **Training sees it gone.** The training renders (`locate train`) replace patches of the
  destructible parts by rubble-coloured noise, and add dust low over the ground, on top of the
  smoke and the rest of the game look (`augment.py`), so the per-map model learns not to lean on
  them.
- **Missing geometry is not a wrong place**: with a prior, weak fits within its disc are kept (above).

Until the exports carry the tags, nothing is marked destructible, and these do nothing.

### The track

- **Outliers**: a fix is compared with the fixes in the 3 s before it and, separately, the 3 s after
  it; consistent means no further apart than the profile's speed allows, plus 1.5 m. A fix that
  disagrees with most of its neighbours on **both** sides is voted out (kept in the `_raw` columns,
  `kept` false). Requiring both sides keeps the first fix after a respawn.
- **Lives**: with the footage's lives (above) the track follows them, and within a life drops the
  weaker side of a step that breaks the speed. Without them it breaks where two consecutive kept
  fixes are further apart than the speed allows, where there is a gap of more than 8 s, and where
  the minimap table starts a new life.
- **Smoothing**: inside a life, each fix is fused with a straight line through the fixes round it
  (a weighted local linear fit, sigma 0.5 s), each weighted by its uncertainty: a strong fix - good
  to centimetres - stays where it is, a weak one is pulled towards its strong neighbours. A line
  rather than an average, because an average drags a running player behind: averaging was tried
  first and turned a 3 mm track into a 0.3 m one at 2 frames a second. The view angles are not
  smoothed; a turn of the view is real, and fast.

### The minimap fallback

The minimap table is in its own mosaic's frame (pixels, x east, y north). It is tied to the level by
one similarity - turn, scale, shift, and a mirror if that fits better - fitted robustly on the
frames where both have a position. Where the picture gave nothing, or its fix was voted out, the
minimap's position stands in with `source = minimap`, a confidence of at most 0.5 and an uncertainty
of twice the fit's residual plus 1.5 m. The minimap has no height: it is carried over from the
nearest visual fix. A minimap-only run (no visual fixes) cannot be tied to the level and places
nothing.

`--prior-radius` uses the same fit the other way round: once eight visual fixes have tied the
minimap to the level, retrieval looks only at database views within that radius of the minimap's
position, and falls back to the whole level when that finds nothing. It is faster; it is also only
as right as the minimap, which is why it is off by default.

## Accuracy

Measured on **Counter-Strike 2**, because there the truth is exact: a match demo records every
player's position and view every tick, and the maps can be exported with their textures. CS2 is
only the bench - its demos already say where everyone was, so `locate` is not for CS2. Nothing of
the bench (maps, demos, renders) is part of this repository.

**The bench.** One competitive map, exported with its base colour textures (4.5 million
triangles, 243 textures at up to 512 px), in game units (1 unit = 2.54 cm). Two databases of it:

| Database | Places | Views | Size | Built in |
|---|---|---|---|---|
| **every floor** - the default | 4,490 (of 7,136 floor points; the rest inside geometry or without headroom) | 107,760 | 319 MB | 23 min |
| where players stood in recorded matches | 2,637 | 63,288 | 187 MB | 33 min |

Both at 2.5 m spacing, standing and crouched eye height, 12 directions, pitch 0, on an RTX 5080
that other work was using at the same time (the times are upper bounds).

**Frames.** Poses where players really stood (taken from other moments of the matches), 80%
standing and 20% crouched, any direction, pitch -30 to +20 degrees, the game's 106.26-degree
field of view, 960x540. Each is rendered *to look like the game, not like the database*: the map's
own sun with cast shadows, harder contrast, a random colour grade, vignette and bloom, up to three
dark player-sized shapes, smoke in one frame of five, the HUD drawn into the masked boxes, blur,
noise and JPEG. Each frame is located against the **whole map, with no prior**. Right means within
1 m and 5 degrees.

| 199 frames, no prior | every floor (default) | player places |
|---|---|---|
| right | **80.4%** | **88.9%** |
| `ok` (confidence at least 0.85) | 79.4% | 84.4% |
| of the `ok` fixes, right | **97.5%** | **98.8%** |
| error of the right fixes, median / 90% | 3 mm / 1.0 cm; 0.03 / 0.07 degrees | the same |
| time per frame, median / 90% | 1.0 / 1.4 s | 0.9 / 1.2 s |

On frames rendered exactly like the database (no change of light, nothing in the way, no mask), 91%
are right (99 frames, player places). Confidence is a usable measure of trust: of the fixes at 0.9
or above, 99% were right on both databases; of those between 0.7 and 0.85, 2 of 6 (every floor)
and 7 of 8 (player places) - hence the 0.85 threshold for `ok`.

Where it fails (every floor, 199 frames): retrieval finds no matching view (12), too few inliers
(9 - a wall a step away, mostly sky, mostly an occluder), ambiguous between two places (3). The
default database does worse than the player-places one mostly in retrieval: a third more views,
many of them on roofs and ledges nobody stands on, compete for the shortlist.

**A track.** 80 s of one player's real camera path from a match demo - a round's end, the
respawn, a death - rendered as above into a 30 fps MP4, with a minimap table made from the same
path (its own turned, scaled, mirrored frame, 2-pixel noise), then run through `locate frames` at
2 frames a second and scored with `locate eval`, which also had to find the clock offset:

| 80 s, 160 frames at 2 a second, 127 in play | every floor (default) | player places |
|---|---|---|
| frames in play placed | 127 of 127: 125 from the picture, 2 from the minimap | 127 of 127: 126 and 1 |
| clock offset found (true: 180 s) | 179.996 s | 179.996 s |
| visual rows, median / 90% error, known offset | 4 mm / 7 mm; 0.03 / 0.06 degrees | 4 mm / 9 mm; 0.03 / 0.06 degrees |
| the same, offset as found | 1.0 / 2.7 cm | 1.2 / 2.8 cm |
| visual rows within 1 m | 100% | 96% |
| minimap rows, median error | 0.79 m | 0.75 m |
| time per frame | 0.55 s | 0.51 s |

The 4% on the right are five consecutive frames of a player standing still, all one building
module (3.25 m) off - see below. The minimap rows are where the picture had too few inliers; their
error is the fit's, from a minimap table with 2-pixel noise.

**What made a difference** (100 frames each, player places; right / `ok` precision):

| Change | Right | Precision | Note |
|---|---|---|---|
| none (the setup above) | 82.8% | 95% | |
| matching against renders lit with the map's own sun and shadows | 84.8% | 96% | a small gain; `--shadows` at build |
| shortlist of 16 instead of 8 | 84.8% | 95% | 3x the time |
| shortlist of 4 | 74.7% | 99% | |
| field of view 3 degrees off | 82.8% | 87% | the error of right fixes grows from 3 mm to 28 cm, and only 30% stay `ok`: pass the real FOV |
| CLAHE light normalisation | 82.8% | 91% | no gain, worse precision - not the default |
| heavier occlusion (up to five shapes, smoke in half the frames) | 71.7% | 99% | |
| matching against renders without textures | 66.7% | 100% | only 26% of frames confident enough to be `ok` |

**What the level file has to carry** (100 frames, databases at 4 m spacing, everything else
the same; the game-like frames are always rendered from the full textured map):

| Level | Right | `ok` | Precision |
|---|---|---|---|
| textured | 75.8% | 74.7% | 96% |
| cut-out materials (fences, foliage) drawn solid | 75.8% | 74.7% | 96% |
| floor materials reduced to one flat colour each | 70.7% | 51.5% | 100% |
| both | 70.7% | 51.5% | 100% |
| no textures at all | 46.5% | 19.2% | 100% |

Textures are what the matching lives on: without them a fifth of the frames are placed. The floor's
own texture matters - a flat floor colour costs a third of the confident fixes, because a frame
often holds more floor than anything else. Solid cut-outs cost nothing measurable here (this map
has few of them; a level of trees and fences may differ).

Look-alike places are the main source of confident mistakes. Before the strongest three places
were refined before choosing, and before impossible poses were set aside, 80% of the `ok` fixes
were right on a small database; after, 93% (same frames). What remains: a pose exactly one
building module over (128 units, 3.25 m, on this map) along a wall of repeated modules, solved
consistently over several frames of a player standing still - neither the outlier vote nor the
confidence sees it.

Two further checks were tried and dropped because they did not separate right fixes from wrong
ones: the global descriptor of the frame against a render at the solved pose, and whether the
map's depth edges at the solved pose fall on the frame's edges (10% of right fixes scored as low as
the wrong ones).

### Battlefield 6: the first real frames

The bench above is renders against renders. The first run on real recordings - the player's own
Battlefield 6 clips, 4K, on one map exported from the installed game - **does not work yet**,
and the numbers say where it breaks:

| What | Result |
|---|---|
| Database of the play area (1.2 x 1.0 km, 12 m spacing, eye heights 1.6 and 3.5 m, 8 directions) | 183,984 views, about 540 MB, 19 min |
| Whole level, no prior: sampled frames placed | **0 of 10** |
| A denser database round one stretch (300 m square, 4 m spacing) | 111,632 views, about 330 MB, 12 min |
| The same, a 36 s stretch at 2 frames a second, no prior | **0 of 63** (37 on foot, 26 vehicle; 10 more zoomed and skipped) |
| The same frames searched only within 30 m of the true place (what a minimap tied to the level would give) | 6 of 10 on-foot frames solved with 32-121 inliers, the strongest right by eye, but scattered over 20-30 m and none confident enough to be `ok` |
| A frame matched against a render at its true pose (found by searching the whole area by brute force) | 76-142 matches, 15-59 inliers |

- **Retrieval is what fails.** The views that show the frame's place rank 52nd to 83rd of 184,000
  by the global descriptor: close, but outside the shortlist. The game's light, its effects and
  the export's coarse textures move the frame further from the renders than the bench's imitation
  did.
- **Matching starts only very close to the true pose.** The database views 3-5 m away give 12-44
  matches, mostly too few to start the refinement that would close the gap; on the bench, a view
  that far away gave hundreds.
- **The real frames' reprojection error** is 2-3 pixels against 1 on renders, so `confidence`,
  calibrated on renders, is too strict for them.
- **The level file**: this export's terrain had no colour at all (white); it was run with one
  flat sand colour instead (see [What the level file has to carry](#accuracy)). Textures were at
  256 pixels.
- **The field of view**: the settings file gives 69 degrees vertical (101.4 horizontal) on foot and
  53 (83.1) in vehicles; at the true pose the inliers peak at 90-94 degrees horizontal, so the
  setting may have been different when the clips were recorded.

#### With a per-map model

The same map, places only on the walkable ground (the `ground:` parts: 175,360 views at 12 m, 20 min),
and a head trained on its renders (`locate train`, 600 steps, 29 min; frozen DINOv2); then a
second head with the six real pseudo-labelled frames added as pairs (28 min). The reference is a
handful of real frames with a known pose: one found by searching the whole area by brute force,
and five more the pipeline found itself near it and chose along the sequence (pseudo-labels,
consistent with each other at walking pace).

| Real frames, whole level, no prior | DINOv2 alone | Head, renders only | Head, + real pairs |
|---|---|---|---|
| Rank of the right view among 175,360 (six labelled frames), median | 474 | **57** | 3 (in-sample: trained on these frames) |
| Right view within the shortlist's reach (top 192) | 2 of 6 | 4 of 6 | 6 of 6 (in-sample) |
| 36 s stretch on foot and in a vehicle (63 frames not zoomed): placed | 0 | **3** (1 on foot, 2 vehicle) | **7** (5 on foot, 2 vehicle; 4 of them frames it was not trained on) |
| The same, rows the minimap filled once tied to those fixes | - | - | 60 (fit: 6 of 7 pairs, 2.2 m residual, 0.66 m a minimap pixel) |
| 130 s stretch in a tank, another clip (72 vehicle frames, 59 zoomed and skipped): placed | 0 | 2 (plausible by eye, 26 inliers) | 0 |

Every fix in the table was checked by eye against the level rendered at its pose: the container,
the pallets, the portacabins, the barrier walls and the guard tower line up. These are the first
frames of real Battlefield 6 footage placed from the picture alone. They are also few: a tenth of
the frames at best, on the stretch the real pairs came from, and nothing yet on another clip. The
second round's gain is mostly on the frames round it was trained on, which is what six real pairs
can teach; it needs pseudo-labels from many clips.

What else was measured on the same frames:

- **The field of view, from the frames** (`--fit-fov`): four solid fixes give 94, 96, 96 and 102
  degrees horizontal, median 96 (64 vertical). The settings file says 101 (69): the clips were
  probably recorded with a different setting than the one saved now.
- **Reprojection error**: right fixes of real frames show 2-3 pixels; the Battlefield 6 profile
  takes 3 as normal (`pixel_noise`). With a handful of labelled frames this is a working value,
  not a calibration.
- **Zoomed views** are the largest share of a tank player's frames (59 of 131 on the tank stretch)
  and are not located.

What it needs next: many more real pseudo-labels, from many clips, to train on and to calibrate the
confidence on (each round's confident fixes feed the next: `locate train --real <table> <video>`);
a level with its ground colour and 512-pixel textures; places from the game's own navigation mesh;
and a way to handle the zoomed views.

#### At scale: three maps, eleven clips, two rounds

Three maps exported from the player's own install, each with its navigation mesh (`nav:` parts) and
its ground; places from the navigation mesh for players and from the ground for vehicles
(`--places auto`). Map A has ten clips: nine to bootstrap on, one held out that never feeds
training. Maps B and C have one clip each. Every number below is from the picture alone, over the
whole play area, no prior; every visual fix was looked at on its check picture.

| Map A, ten clips, a frame every 5 s | Round 1 | Round 2 |
|---|---|---|
| Head | renders only (600 steps) | + the 11 round-1 fixes of confidence 0.7 and up as real pairs |
| Database | 220,432 views (players and vehicles, 12 m) | 366,920 views (vehicles at the players' spacing) |
| Views tried per frame (`--shortlist`) | 8 | 24 |
| Nine training clips: on foot | 1 of 271 | 0 of 273 |
| Nine training clips: vehicle | 14 of 906 | 12 of 892 |
| Nine training clips: zoomed, screen | not run (`--no-zoomed`), skipped | the same |
| Wrong by eye | 2 of 15 | 0 of 12 |
| Held-out clip | 0 of 241 (57 on foot, 83 vehicle) | 0 of 241 |

- **The two wrong fixes** of round 1 were both weak fixes made `ok` by the sequence (confidence
  0.59 and 0.69): one a frame of the death camera, one a vehicle frame half hidden by a wall. Both
  drew their support from neighbours too far apart in time to say anything (the rule then had no
  time limit; it now counts neighbours within 6 s). Every fix of confidence 0.7 and up, in both
  rounds, was right.
- **The real pairs did not move the placed share.** Eleven real frames among 200,000 rendered
  ones are too few to teach the head the game's look; the bootstrap would need its first round to
  place far more than it does at a frame every 5 s.
- **The same clips at 2 frames a second** (one 75 s stretch in a tank, round-1 database): 37 of 112
  vehicle frames placed and 4 of 26 zoomed, all 41 right by eye. Frames close together support each
  other along the sequence; one frame in five seconds stands alone. Where the vehicle moves
  through a known part of the map, a third of its frames are placed.
- **The held-out clip at a frame every 2 s** (round-1 database): 2 of 601 frames placed, both
  wrong, both sequence-supported weak fixes from neighbours 16 s apart: what led to the 6 s rule.
- **On foot** almost nothing is placed: the player looks at walls and the ground from close by,
  and the views of a database 12 m apart are never close enough.
- **Vehicles are placed far more often than players on foot**: the third-person camera sees more
  of the level from higher up.

Zoomed views, on the 2-frames-a-second stretch: 22 of 26 had a fix within 6 s to start from, 4
were placed - two through the tank's own view at 1.33 and 1.41 times the field of view on foot,
two through its sight at 3.49 and 3.47 - all four right by eye (the level's lettering on a wall
lines up at 3.5x). The rest found too few matches: the sight's black surround, the barrel and
smoke leave little of the level.

**Map B**: 0 of 151 frames placed (133 on foot, 1 vehicle, 17 menus). The best frames solve to the
right place by eye - the buildings, a truck and the mountains line up - but with 75
inliers and a reprojection error too large to be `ok`. The export's ground is untextured grey.

**Map C**: its one clip is mostly the desktop and menus; of about 40 frames of
play, none was placed (16 inliers at best), with the database rebuilt on the re-export whose
foliage is cut out (alpha `MASK`, below). Its frames are mostly trees and lawns.

The level files matter: the re-export of map C draws its foliage as cut-outs instead of black
cards (34 materials with `alphaMode: MASK`). The renderer honours it: a texel whose alpha is below
the material's `alphaCutoff` (0.5 when not given) is discarded - neither colour nor depth written -
so the background shows through (`render.py`).

## Renders against frames

The renders the database is made of are not the game's frames. On the bench the gap was imitated
(light, shadows, grade, players, smoke, HUD) and costs about 10 points of right fixes against
frames rendered like the database (91% to 80-89%); the right fixes stay at millimetres. What helped:
the map's own sun and shadows in the renders matched against (small), a longer shortlist (small,
slow). What did not: CLAHE light normalisation.

What the bench cannot imitate is the rest of a real frame: baked and bounced light, ambient
occlusion, fog, particles, foliage that moves, the game's own post-processing. To measure it,
record the playback of something whose camera poses are exact - a game's demo or replay - and
compare with `locate eval`; it finds the clock offset between the recording and the poses itself,
or takes it with `--offset`.

## Limits

- **Real frames are barely placed yet.** With DINOv2 alone no real Battlefield 6 frame was placed
  without a prior; with a per-map model a few percent are, right when looked at (see
  [Battlefield 6: the first real frames](#battlefield-6-the-first-real-frames)). Every
  accuracy number above is on renders of the level, made to look like the game (its sun, shadows,
  grading, bloom, noise, players, HUD), against renders of the same level. A real frame differs in ways a render cannot imitate: baked and bounced light,
  ambient occlusion, fog, particles, decals that change, animated foliage. How much that costs is
  the open question; see [Renders against frames](#renders-against-frames) for how to measure it.
- **The level must be the one that was played**, at the same version, with its textures,
  including the floor's: see [What the level file has to carry](#accuracy).
- **Look-alike places.** Levels reuse buildings, props and tiled materials. Two places that look
  the same give two good solves; the second is reported (`runner_up`), the fix is not `ok`, and the
  track or the minimap has to decide. A fix that is right but marked ambiguous is lost, not
  wrong.
- **Frames with little level in them**: a wall a step away, the sky, a smoke grenade, a scope's
  black surround, a death or menu screen. They give no fix and are said to give none.
- **Zoom.** Aiming down sights and scopes narrow the field of view. Zoomed frames are solved only
  from a neighbouring fix (above); a long stretch through a scope with no fix round it is not.
- **Vehicles and third-person cameras.** The camera is then not at eye height and not where the
  vehicle is; the offset between them (above) was measured for one vehicle type, a main battle
  tank. Other vehicles ride their camera differently, and their positions are off by the
  difference - a few metres. The vehicle itself is masked (the profile's `vehicle_hud`).
- **What the level does not hold**: destruction, vehicles, players, doors that moved. Masked where
  it is the HUD; otherwise RANSAC has to see past it.
- **Speed.** A frame costs 0.5-1.5 s on an RTX 5080 (more while other work shares the GPU): the
  renders of a shortlist, the matching, and the render-and-compare. Two frames a second of a
  20-minute match is 2,400 frames, 20 minutes to an hour. The database is built once per level:
  about 20-30 minutes for a level the size of a competitive shooter map at 2.5 m spacing; a
  Battlefield-sized play area needs `--box` and a coarser spacing, or several boxes.
- **Large levels.** A level file can hold kilometres of backdrop: `--box` limits the places to the
  play area. Shadows (`--shadows`) are cast from one shadow map over the whole file, which gets
  coarse on very large ones.

## Licences

| Component | Licence |
|---|---|
| DINOv2 ViT-B/14 weights (`facebook/dinov2-base`) | Apache-2.0 |
| ALIKED (`aliked-n16`) | BSD-3-Clause |
| LightGlue, ALIKED variant | Apache-2.0 |
| kornia, kornia-rs | Apache-2.0 |
| moderngl, glcontext | MIT |
| transformers, huggingface_hub, safetensors | Apache-2.0 |

All permit commercial use. Two common alternatives were left out because their terms would pass
on to every result: SuperPoint's weights (non-commercial) and scene-coordinate-regression code under
non-commercial licences. See [Models and licences](models-and-licences.md).

## Running it on Battlefield 6

What is needed, in order:

1. **The level, textured**, from the player's own installed copy, as a `.glb` in metres, Y up, in
   the frame the HUD reader's and the viewer's tables use. `extras.unit_metres` (1) and, if known,
   `extras.sun` (the direction towards the sun) in the file's top-level `extras`. A level without
   textures loads and renders, but see [Limits](#limits).
2. **The play area** as a box (`--box X0 Z0 X1 Z1`, metres): Battlefield level files carry the
   backdrop for kilometres round it, and a database of all of it is mostly views nobody sees.
3. **The player's FOV**: Battlefield's slider is vertical; pass it as `--vfov` (the profile's 55
   degrees is a placeholder). Recordings at 16:9.
4. **The eye heights** (`--eye`, standing then crouched) - the profile's 1.6 and 1.05 m are not
   measured. Measure them on the first good run: `y` of the fixes of a player standing still on
   flat ground, minus the floor's height there.
5. **The HUD boxes** were checked on 4K recordings with the default layout (minimap, squad list,
   kill feed, compass and sight compass, score bar and objective flags, chat, ammunition, prompts,
   the weapon). A moved or scaled HUD needs `--mask`.
6. Build, then locate with the HUD reader's table as the fallback, and look at a sample of the fixes:

```bash
.venv/Scripts/python -m heat3d_capture locate build level.glb -o level.db --game bf6 --box X0 Z0 X1 Z1 --shadows
.venv/Scripts/python -m heat3d_capture hud "<recording>.mp4" --game bf6 -o out/match
.venv/Scripts/python -m heat3d_capture locate frames "<recording>.mp4" --db level.db --game bf6 --vfov <yours> --minimap out/match.parquet -o out/match.locate --check-every 20
```

Every visual fix gets a check picture (`<out>.check`; `--check-every 20` adds every 20th frame,
placed or not): the frame next to the level rendered at its fix, with the frame's edges drawn over
the render. Where they line up, the fix is right. There is no truth to compare
with in Battlefield, so that picture, the share of frames placed from the picture
(`summary.json`), and how well the minimap's fit agrees with the visual fixes (its `residual`)
are the checks.
