
# Trackmania (2020)

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Code: the Openplanet plugin
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **The plugin has not yet been run in the game**; the viewer's reader
of its CSV is tested.

## Why a plugin that writes files

Trackmania has no telemetry output of its own. Openplanet, the game's plugin platform,
exposes the viewed car's vehicle state to plugins, but Openplanet plugins cannot send UDP. So
the plugin writes one CSV file per run into its own storage folder, and the viewer reads those
files as they are. There is no recorder process: `telemetry --game trackmania` only installs
the plugin (with `--install`) and prints where the files will appear.

## Installing and loading

- `--install` copies `mods/trackmania/Heat3dRecorder` to
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, replacing an older copy. Without
  `--install` nothing is copied.
- In the game: **Openplanet > Developer > Load plugin**, and pick `3DHeat recorder`.
- The plugin depends on Openplanet's **VehicleState** plugin (`dependencies = ["VehicleState"]`
  in `info.toml`).
- Unsigned plugins load only in **Openplanet's developer mode**, which limits online play.
  The plugin can be signed on openplanet.dev; it is not signed here.

Runs are written to `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Load those
CSV files in the viewer's Race tab. `-o` and `--port` are ignored for Trackmania.

## What the plugin records

It reads only what Openplanet exposes - the viewed car's vehicle state
(`VehicleState::ViewingPlayerState()`) and the player's race time and respawn count
(`CSmScriptPlayer`) - sends nothing anywhere and changes nothing in the game. A row is
written on every frame (`Update`), so the sample rate is the game's frame rate.

| Column | Source |
|---|---|
| `time` | `CurrentRaceTime` / 1000, seconds |
| `x`, `y`, `z` | `Position` (world, Y up) |
| `speed` | length of `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 or 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | each wheel's `SlipCoef` (a 0..1 sliding measure) |
| `loose` | 1 when any wheel's ground material is Grass, Ice, Sand, Dirt, Green or RoadIce |
| `airborne` | 1 when the car has no ground contact |
| `respawns` | respawns since the run began |

## Runs

- A run **starts** on the first frame where the race time is not negative (the countdown is
  not recorded).
- It **finishes** when the playground's UI sequence is the finish sequence (value 11): the
  file is written as complete, with the last race time as its `seconds`.
- It is **abandoned** - written with `_partial` in the name and `"complete": false` - when the
  race clock goes back by more than half a second (a restart), or when the player leaves the
  playground.
- A run with fewer than 20 rows is not written.

## The file

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Named `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. The map name has formatting codes stripped
and double quotes replaced by single ones. Values are written with four decimals. The format
is described in [The heat3d-lap file](lap-format#the-csv-form).

The header's `meta` carries `"slip": "index"` - the `slipIndex.*` channels are Trackmania's own
0..1 sliding measure, not a physical slip - and `"discipline": "arcade"`.
