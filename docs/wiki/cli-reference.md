# Command reference

Generated from the program by `tools/gen_docs_reference.py`; do not edit by hand. The other
pages explain each command step by step; this page lists every option and column.

## Commands

### `python -m heat3d_capture`

```text
usage: heat3d_capture [-h] {route,telemetry,laps,reconstruct,hud,locate} ...

Reconstruct a level from a recording.

positional arguments:
  {route,telemetry,laps,reconstruct,hud,locate}
    route               record a lap's positions from the game's telemetry, and nothing else
    telemetry           record every telemetry channel, one file per lap, for the viewer's Race
                        tab
    laps                read a recorded lap library, and write out one course
    reconstruct         solve a recording offline and write a .glb
    hud                 read the player's own actions, deaths and minimap track, and the kill
                        feed, out of a recording, after the match
    locate              where each frame of a recording was taken, from the picture against the
                        level's geometry

options:
  -h, --help            show this help message and exit

For live scanning with the overlay and coverage map, run python -m heat3d_capture.ui instead.
```

### `python -m heat3d_capture route`

```text
usage: heat3d_capture route [-h] -o OUT [--port PORT] [--seconds SECONDS]

options:
  -h, --help         show this help message and exit
  -o, --out OUT
  --port PORT
  --seconds SECONDS  stop after this long; 0 means run until interrupted
```

### `python -m heat3d_capture telemetry`

```text
usage: heat3d_capture telemetry [-h] [-o OUT] [--port PORT] [--forward FORWARD]
                                [--game {forza,ac,acc,acevo,acrally,wrc,dirtrally2,dirtrally,dirt4,rbr,beamng,trackmania}]
                                [--install] [--configure CONFIGURE]
                                [--surface {tarmac,loose,snow,ice,mixed}]

options:
  -h, --help            show this help message and exit
  -o, --out OUT         folder for the lap files
  --port PORT           the port the game sends to
  --forward FORWARD     host:port to pass every packet on to, e.g. 127.0.0.1:5301 for FH Companion
  --game {forza,ac,acc,acevo,acrally,wrc,dirtrally2,dirtrally,dirt4,rbr,beamng,trackmania}
                        forza (Data Out over UDP, the default); an Assetto Corsa game from its
                        shared memory; wrc, dirtrally2, dirtrally, dirt4 or rbr from their UDP
                        telemetry; beamng from the heat3d protocol mod; trackmania from the
                        Openplanet plugin's files (see docs/games.md)
  --install             beamng / trackmania: copy the mod or plugin into the game's folder first
  --configure CONFIGURE
                        wrc: the game's telemetry config.json to switch the packet on in (backed
                        up first)
  --surface {tarmac,loose,snow,ice,mixed}
                        rally games: the stage's surface, written into each file; without it the
                        file names none and the viewer works it out
```

### `python -m heat3d_capture laps`

```text
usage: heat3d_capture laps [-h] [-o OUT] [--library LIBRARY] [--margin MARGIN] [course]

positional arguments:
  course             course name, loosely matched; omit to list what is there

options:
  -h, --help         show this help message and exit
  -o, --out OUT
  --library LIBRARY  where the laps live (default: %LOCALAPPDATA%/FHCompanion/laps)
  --margin MARGIN    metres of map to keep around the course (default 80)
```

### `python -m heat3d_capture reconstruct`

```text
usage: heat3d_capture reconstruct [-h] -o OUT [--solve-budget SOLVE_BUDGET]
                                  [--fuse-interval FUSE_INTERVAL]
                                  [--model {vggt-1b,vggt-1b-commercial}]
                                  video

positional arguments:
  video

options:
  -h, --help            show this help message and exit
  -o, --out OUT
  --solve-budget SOLVE_BUDGET
                        how many frames the solver may use (default 260). They are spaced by how
                        far the picture moves rather than by the clock, so a fast section gets
                        more of them. More is more accurate and much slower: cost is minutes per
                        window of 16.
  --fuse-interval FUSE_INTERVAL
                        seconds between frames fused into geometry (default 0.4)
  --model {vggt-1b,vggt-1b-commercial}
                        which weights to solve with (default vggt-1b, non-commercial)
```

### `python -m heat3d_capture hud`

```text
usage: heat3d_capture hud [-h] [-o OUT] [--game {bf6}] [--player PLAYER] [--fps FPS]
                          [--start START] [--seconds SECONDS]
                          [--metres-per-pixel METRES_PER_PIXEL] [--cpu]
                          video

positional arguments:
  video

options:
  -h, --help            show this help message and exit
  -o, --out OUT         output path without extension; the files are <out>.parquet, .events.jsonl,
                        .summary.json, .map.png, .map.json
  --game {bf6}          whose HUD to read (default bf6, Battlefield 6)
  --player PLAYER       the player's name as the kill feed shows it, matched loosely; without it
                        the squad list or the feed's own-name colour is used
  --fps FPS             minimap samples per second (default 5)
  --start START         seconds into the video to begin at
  --seconds SECONDS     how much of the video to read (default: all of it)
  --metres-per-pixel METRES_PER_PIXEL
                        the minimap's scale, if known: metres per minimap pixel at the usual zoom
                        (296 per minimap at 1080p); without it positions are in those pixels
  --cpu                 decode on the CPU even when an NVIDIA card is there
```

### `python -m heat3d_capture locate`

```text
usage: heat3d_capture locate [-h] {build,frames,train,refmap,minimap,eval} ...

positional arguments:
  {build,frames,train,refmap,minimap,eval}
    build               render a level from every place a player can stand, and index it
    frames              locate the frames of a recording (or a folder of pictures)
    train               train a per-map place model on renders of the level (and frames already
                        located)
    refmap              place the game's own map (its deploy screen) on the level: the reference
                        the minimap is read against
    minimap             read a recording's minimap against the reference map: the player's
                        position on the level, frame by frame
    eval                compare a located table with known camera poses

options:
  -h, --help            show this help message and exit
```

### `python -m heat3d_capture locate build`

```text
usage: heat3d_capture locate build [-h] -o OUT [--spacing SPACING] [--yaw-step YAW_STEP]
                                   [--pitch PITCH [PITCH ...]] [--positions POSITIONS]
                                   [--untextured] [--shadows] [--places {auto,nav,ground,floors}]
                                   [--head HEAD] [--box X0 Z0 X1 Z1] [--game {bf6,generic}]
                                   [--eye EYE [EYE ...]] [--fov FOV] [--vfov VFOV]
                                   [--vehicle-vfov VEHICLE_VFOV] [--settings SETTINGS]
                                   [--max-speed MAX_SPEED] [--mask MASK] [--no-hud-mask]
                                   level

positional arguments:
  level                 the level's .glb (or .gltf), textured, in the viewer's frame

options:
  -h, --help            show this help message and exit
  -o, --out OUT         the database folder to write
  --spacing SPACING     metres between the places views are taken from (default 2.5)
  --yaw-step YAW_STEP   degrees between the views' directions (default 30)
  --pitch PITCH [PITCH ...]
                        pitches to render at, degrees up (default 0)
  --positions POSITIONS
                        a table (Parquet or CSV with x, y, z in the level's frame, at the feet) to
                        take places from instead of every floor
  --untextured          render shape and light only (a level whose textures are missing)
  --shadows             cast the sun's shadows in the renders (the level's own sun when it names
                        one)
  --places {auto,nav,ground,floors}
                        where views are taken from: nav (players on the navigation mesh, vehicles
                        on the ground), ground, floors (every upward face); auto (default): nav
                        when the level has one
  --head HEAD           a per-map head from `locate train` for the descriptors
  --box X0 Z0 X1 Z1     only places inside this box, in the level's units: the part of the level
                        anyone plays in
  --game {bf6,generic}  the game's profile (default bf6)
  --eye EYE [EYE ...]   eye heights above the floor, metres, standing first
  --fov FOV             horizontal field of view of the recording, degrees
  --vfov VFOV           or the vertical one (Battlefield's slider), for a 16:9 recording
  --vehicle-vfov VEHICLE_VFOV
                        the vertical field of view of vehicle cameras (Battlefield's vehicle
                        slider)
  --settings SETTINGS   bf6: the game's settings file to read the field of view from (default: the
                        newest under Documents/Battlefield 6/settings); used when no --fov/--vfov
                        is given
  --max-speed MAX_SPEED
                        metres a second a player can move, for the outlier vote
  --mask MASK           another screen box that is not the level: x,y,w,h on 1920x1080; repeatable
  --no-hud-mask         drop the profile's HUD boxes (keep only --mask ones)
```

### `python -m heat3d_capture locate frames`

```text
usage: heat3d_capture locate frames [-h] --db DB [-o OUT] [--level LEVEL] [--fps FPS]
                                    [--start START] [--seconds SECONDS] [--width WIDTH]
                                    [--shortlist SHORTLIST] [--normalise {none,clahe,gray}]
                                    [--minimap MINIMAP] [--prior-radius PRIOR_RADIUS]
                                    [--minimap-anchor MINIMAP_ANCHOR] [--lives LIVES]
                                    [--no-level-search] [--check-every CHECK_EVERY]
                                    [--no-sequence] [--no-search]
                                    [--search-shortlist SEARCH_SHORTLIST]
                                    [--accept-depth ACCEPT_DEPTH]
                                    [--accept-support ACCEPT_SUPPORT] [--checkpoint CHECKPOINT]
                                    [--stop-file STOP_FILE] [--stop-process STOP_PROCESS]
                                    [--no-grow] [--no-zoomed] [--no-checks] [--fit-fov]
                                    [--game {bf6,generic}] [--eye EYE [EYE ...]] [--fov FOV]
                                    [--vfov VFOV] [--vehicle-vfov VEHICLE_VFOV]
                                    [--settings SETTINGS] [--max-speed MAX_SPEED] [--mask MASK]
                                    [--no-hud-mask]
                                    source

positional arguments:
  source                a video, a picture, or a folder of pictures

options:
  -h, --help            show this help message and exit
  --db DB               the database `locate build` wrote
  -o, --out OUT         output path without extension (default <source>.locate)
  --level LEVEL         the level's .glb, if it moved since the database was built
  --fps FPS             frames located per second of video (default 2)
  --start START         seconds into the video to begin at
  --seconds SECONDS     how much of the video to read (default: all of it)
  --width WIDTH         the width frames are matched at (default 1280)
  --shortlist SHORTLIST
                        database views tried per frame (default 8)
  --normalise {none,clahe,gray}
                        light normalisation before matching (default none)
  --minimap MINIMAP     the `hud` verb's table: the fallback where the picture gives no fix
  --prior-radius PRIOR_RADIUS
                        optional speed-up: search only database views this many metres from the
                        minimap's position (needs --minimap)
  --minimap-anchor MINIMAP_ANCHOR
                        a JSON file tying the minimap to the level (scale, rotation, shift, its
                        measured error; docs/locate.md): the minimap becomes a search prior from
                        the first frame (needs --minimap)
  --lives LIVES         the `hud` verb's table whose deaths, spawns and revives say when the
                        player was in play (default: the --minimap table); positions jump only
                        across a death
  --no-level-search     with a prior: when the search near it finds nothing, do not search the
                        whole level as well
  --check-every CHECK_EVERY
                        every N located frames, write <out>.check/<frame>.jpg: the frame beside
                        the level rendered at its fix, the frame's edges drawn over it
  --no-sequence         decide every frame on its own, not along the run
  --no-search           with no prior: search each frame on its own, and believe its fix without
                        its neighbours
  --search-shortlist SEARCH_SHORTLIST
                        with no prior: database views tried per frame (default 16)
  --accept-depth ACCEPT_DEPTH
                        with no prior: believe a fix only if its inliers' far distance is this
                        many times their near one (default 0: no such test)
  --accept-support ACCEPT_SUPPORT
                        with no prior: agreeing neighbours along the life a fix needs to be
                        believed (default 2)
  --checkpoint CHECKPOINT
                        keep the run's state here and carry on from it if it is there (default
                        with --stop-file or --stop-process: <out>.checkpoint)
  --stop-file STOP_FILE
                        stop by itself, state saved and exit code 75, when this file exists;
                        checked before every frame; may be repeated
  --stop-process STOP_PROCESS
                        the same, when a process runs whose name starts with this; may be repeated
  --no-grow             do not search again near each fix for the frames round it still without
                        one
  --no-zoomed           do not solve zoomed views (scopes, sights) from their neighbours' fixes
  --no-checks           do not write a check picture for every visual fix (<out>.check)
  --fit-fov             after the run, fit the field of view to the strongest fixes (per view) and
                        report it in the summary, for the next run's --fov
  --game {bf6,generic}  the game's profile (default bf6)
  --eye EYE [EYE ...]   eye heights above the floor, metres, standing first
  --fov FOV             horizontal field of view of the recording, degrees
  --vfov VFOV           or the vertical one (Battlefield's slider), for a 16:9 recording
  --vehicle-vfov VEHICLE_VFOV
                        the vertical field of view of vehicle cameras (Battlefield's vehicle
                        slider)
  --settings SETTINGS   bf6: the game's settings file to read the field of view from (default: the
                        newest under Documents/Battlefield 6/settings); used when no --fov/--vfov
                        is given
  --max-speed MAX_SPEED
                        metres a second a player can move, for the outlier vote
  --mask MASK           another screen box that is not the level: x,y,w,h on 1920x1080; repeatable
  --no-hud-mask         drop the profile's HUD boxes (keep only --mask ones)
```

### `python -m heat3d_capture locate train`

```text
usage: heat3d_capture locate train [-h] -o OUT [--spacing SPACING] [--box X0 Z0 X1 Z1]
                                   [--places {auto,nav,ground,floors}] [--steps STEPS]
                                   [--real TABLE VIDEO] [--real-confidence REAL_CONFIDENCE]
                                   [--game {bf6,generic}] [--eye EYE [EYE ...]] [--fov FOV]
                                   [--vfov VFOV] [--vehicle-vfov VEHICLE_VFOV]
                                   [--settings SETTINGS] [--max-speed MAX_SPEED] [--mask MASK]
                                   [--no-hud-mask]
                                   level

positional arguments:
  level                 the level's .glb

options:
  -h, --help            show this help message and exit
  -o, --out OUT         the head file to write (.pt)
  --spacing SPACING     metres between the floor points training views are taken from (default 4)
  --box X0 Z0 X1 Z1     only this part of the level
  --places {auto,nav,ground,floors}
                        where training views are taken from (as for build)
  --steps STEPS         training steps (default 600)
  --real TABLE VIDEO    a `locate frames` table and its recording: its confident fixes join as
                        real pairs (repeatable)
  --real-confidence REAL_CONFIDENCE
                        the confidence a fix needs to join as a real pair (default 0.85)
  --game {bf6,generic}  the game's profile (default bf6)
  --eye EYE [EYE ...]   eye heights above the floor, metres, standing first
  --fov FOV             horizontal field of view of the recording, degrees
  --vfov VFOV           or the vertical one (Battlefield's slider), for a 16:9 recording
  --vehicle-vfov VEHICLE_VFOV
                        the vertical field of view of vehicle cameras (Battlefield's vehicle
                        slider)
  --settings SETTINGS   bf6: the game's settings file to read the field of view from (default: the
                        newest under Documents/Battlefield 6/settings); used when no --fov/--vfov
                        is given
  --max-speed MAX_SPEED
                        metres a second a player can move, for the outlier vote
  --mask MASK           another screen box that is not the level: x,y,w,h on 1920x1080; repeatable
  --no-hud-mask         drop the profile's HUD boxes (keep only --mask ones)
```

### `python -m heat3d_capture locate refmap`

```text
usage: heat3d_capture locate refmap [-h] [--at AT] -o OUT [--mpp MPP] [--topdown TOPDOWN]
                                    [--topdown-mpp TOPDOWN_MPP] [--box X0 Z0 X1 Z1]
                                    [--whole-picture] [--game {bf6}]
                                    level deploy

positional arguments:
  level                 the level's .glb
  deploy                a picture of the deploy screen, or a recording (with --at)

options:
  -h, --help            show this help message and exit
  --at AT               seconds into the recording where the deploy screen shows the whole map
  -o, --out OUT         output path without extension (<out>.png, .valid.png, .json)
  --mpp MPP             metres a pixel of the reference map (default 0.5)
  --topdown TOPDOWN     where to keep (and reuse) the level seen from above, without extension
  --topdown-mpp TOPDOWN_MPP
                        metres a pixel of the level seen from above (default 0.656)
  --box X0 Z0 X1 Z1     only this part of the level, from above
  --whole-picture       use the whole picture, not the profile's map box
  --game {bf6}          the game's profile (default bf6)
```

### `python -m heat3d_capture locate minimap`

```text
usage: heat3d_capture locate minimap [-h] --refmap REFMAP -o OUT [--fps FPS] [--start START]
                                     [--seconds SECONDS] [--hud HUD] [--hud-anchor HUD_ANCHOR]
                                     [--hud-fill HUD_FILL] [--game {bf6}]
                                     video

positional arguments:
  video                 the recording

options:
  -h, --help            show this help message and exit
  --refmap REFMAP       `locate refmap`'s output, without extension
  -o, --out OUT         the table to write (.parquet); its anchor goes beside it
  --fps FPS             minimaps read per second (default 2)
  --start START         seconds into the video to begin at
  --seconds SECONDS     how much of the video to read (default: all of it)
  --hud HUD             the `hud` verb's table: its lives, and (with --hud-anchor) where to search
                        first
  --hud-anchor HUD_ANCHOR
                        an anchor for the --hud table: searched round its reading when nothing
                        recent is known
  --hud-fill HUD_FILL   with --hud and --hud-anchor: where no minimap matched, the HUD's track
                        moved onto reference-map fixes up to this many seconds away (default 120;
                        0: none)
  --game {bf6}          the game's HUD profile (default bf6)
```

### `python -m heat3d_capture locate eval`

```text
usage: heat3d_capture locate eval [-h] --truth TRUTH [--offset OFFSET] [--unit-metres UNIT_METRES]
                                  [--game {bf6,generic}] [--eye EYE [EYE ...]] [--fov FOV]
                                  [--vfov VFOV] [--vehicle-vfov VEHICLE_VFOV]
                                  [--settings SETTINGS] [--max-speed MAX_SPEED] [--mask MASK]
                                  [--no-hud-mask]
                                  located

positional arguments:
  located               the table `locate frames` wrote

options:
  -h, --help            show this help message and exit
  --truth TRUTH         a table of time, x, y, z, yaw, pitch in the level's frame
  --offset OFFSET       truth time = video time + this (default: searched for)
  --unit-metres UNIT_METRES
                        metres per level unit, for the errors (default 1)
  --game {bf6,generic}  the game's profile (default bf6)
  --eye EYE [EYE ...]   eye heights above the floor, metres, standing first
  --fov FOV             horizontal field of view of the recording, degrees
  --vfov VFOV           or the vertical one (Battlefield's slider), for a 16:9 recording
  --vehicle-vfov VEHICLE_VFOV
                        the vertical field of view of vehicle cameras (Battlefield's vehicle
                        slider)
  --settings SETTINGS   bf6: the game's settings file to read the field of view from (default: the
                        newest under Documents/Battlefield 6/settings); used when no --fov/--vfov
                        is given
  --max-speed MAX_SPEED
                        metres a second a player can move, for the outlier vote
  --mask MASK           another screen box that is not the level: x,y,w,h on 1920x1080; repeatable
  --no-hud-mask         drop the profile's HUD boxes (keep only --mask ones)
```

## Output columns

### Lap files: units every recorder writes (`units`)

| Channel | Unit |
|---|---|
| `time` | s |
| `distance` | m |
| `x` | m |
| `y` | m |
| `z` | m |
| `speed` | m/s |
| `latVel` | m/s, car frame, to the right |
| `longVel` | m/s, car frame, forwards |
| `vertVel` | m/s, car frame, up |
| `latAcc` | m/s2 |
| `longAcc` | m/s2 |
| `vertAcc` | m/s2 |
| `yaw` | rad |
| `throttle` | 0..1 |
| `brake` | 0..1 |
| `clutch` | 0..1 |
| `handbrake` | 0..1 |
| `steer` | -1..1, positive right |
| `wheelSurfaceSpeed` | m/s |
| `wheelSpeed` | rad/s |
| `suspensionM` | m |
| `suspension` | 0..1 of the lap's travel |
| `brakeTemp` | degC |
| `tireTemp` | degC |

Per-wheel channels end in `.FL`, `.FR`, `.RL`, `.RR`.

### Forza lap files: channel units

| Channel | Unit |
|---|---|
| `time` | s |
| `distance` | m |
| `x` | m |
| `y` | m |
| `z` | m |
| `speed` | m/s |
| `latVel` | m/s, car frame, to the right |
| `longVel` | m/s, car frame, forwards |
| `vertVel` | m/s, car frame, up |
| `rpm` | rpm |
| `power` | W |
| `torque` | N m |
| `latAcc` | m/s2 |
| `longAcc` | m/s2 |
| `vertAcc` | m/s2 |
| `yawRate` | rad/s |
| `yaw` | rad |
| `pitch` | rad |
| `roll` | rad |
| `tireTemp` | degC |
| `suspension` | 0..1 |
| `suspensionM` | m |
| `slipRatio` | normalised |
| `slipAngle` | normalised |
| `combinedSlip` | normalised |
| `wheelSpeed` | rad/s |
| `throttle` | 0..1 |
| `brake` | 0..1 |
| `steer` | -1..1 |

Taken once per lap, under `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`.
Not a channel: `isRaceOn`, `trackOrdinal` (`trackOrdinal` goes in once, as `lap.trackOrdinal`). Every other field of the packet is a channel.

### `hud` table columns, in order

`time`, `event`, `x`, `y`, `z`, `player`, `team`, `session`, `heading`, `dir_x`, `dir_y`, `dir_z`, `source`, `text`, `points`, `subject`, `killer`, `victim`, `weapon`, `headshot`, `marker`. Anything else a row carries follows them.
