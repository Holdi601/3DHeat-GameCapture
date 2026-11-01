---
title: BeamNG.drive
parent: Telemetry recorders
nav_order: 4
---

# BeamNG.drive

```bash
python -m heat3d_capture telemetry --game beamng --install    # copy the mod, then record
python -m heat3d_capture telemetry --game beamng -o laps      # record
```

Then in the game: **Options > Other > Protocols**, switch on **"others"**.

Code: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
and the mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Tests: `tests/test_beamng.py`, on packets built from the mod's struct. **The mod has not yet
been run in the game.**

## Why a mod

BeamNG sends telemetry through "protocols": Lua modules in the vehicle that the game's own
`lua/vehicle/protocols.lua` packs and sends over UDP from the car the player drives. The
stock ones do not carry what a car-control analysis needs - OutGauge has no position,
MotionSim no wheels, and OutSim is a stub in current versions. So this project ships its own
protocol, `heat3d`. It touches nothing outside the vehicle's own Lua.

## Installing

`--install` copies `mods/beamng/heat3d` to
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 and later keep
user mods there), deleting an older copy first, and prints where it went. Without
`LOCALAPPDATA` it falls back to the home folder. You can also copy the folder by hand.

`--install` then carries straight on into recording.

## The mod

| Setting (in `heat3d.lua`) | Value |
|---|---|
| Address | `127.0.0.1` |
| Port | `4460` - change it here and pass the same `--port` to the recorder |
| Maximum update rate | 100 Hz |
| Physics step | used (`isPhysicsStepUsed` returns true) |

Each packet is the 4-byte magic `H3D1` followed by 39 little-endian floats (160 bytes in
all):

| Field | Count | Source in the vehicle Lua |
|---|---|---|
| `time` | 1 | the mod's own clock: sum of physics steps, reset when the vehicle resets |
| position | 3 | `obj:getPositionXYZ()` |
| velocity | 3 | `obj:getVelocityXYZ()` (world) |
| forward | 3 | `obj:getDirectionVector()` |
| up | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, and 1/0 from `absActive` and `tcsActive` |
| `wheelSpeed` | 4 | each wheel's surface speed (m/s) |
| `wheelAngular` | 4 | angular velocity times the wheel's direction (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 when off the ground |

The four wheels are chosen by **where they sit on the car**, not by name (names differ between
vehicles): front or rear by the node's position along the car, left or right across it
(vehicle frame +X left, -Y forwards), taking for each corner the wheel furthest from the
centre. A missing corner is sent as zeros with material -1.

## What the recorder does with it

BeamNG's world has Z up; the viewer's has Y up. Positions and vectors are turned about X,
`(x, y, z) -> (x, z, -y)`, which keeps the world's handedness. Then:

| Channel | Derived as |
|---|---|
| `x`, `y`, `z` | turned position |
| `speed` | length of the turned velocity |
| `longVel`, `latVel`, `vertVel` | velocity projected on forward, on right = forward x up, on up |
| `longAcc`, `latAcc`, `vertAcc` | the change in world velocity over +-2 samples, projected on the same axes (the car's own sensors' frame is undocumented, so they are not used) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | as sent |
| `absActive`, `tcActive` | the ABS and TC lamps, where the car has them |
| `wheelSurfaceSpeed.*` | absolute value of the wheel's surface speed |
| `wheelSpeed.*` | rotation |
| `wheelLoad.*` | load |
| `groundContact.*` | 0 when the material is negative, else 1 |

Packets without the magic or shorter than 160 bytes are ignored.

## Laps

`LineSplitter`, as for AC EVO: the point where recording began is the line; a lap closes
where the car next passes closest to it heading the same way, at least 300 m later; a run
closes when the car stands still for 8 seconds. A lap counts as complete only if it began at
more than 5 m/s, so the first lap from a standing start is a partial one. When the mod's
clock goes back by more than half a second (the car was reset), the run open at that moment is
closed first - written as a partial run when it covered at least 300 m, as at the end of a
recording - and then the splitter starts over. See [Lap and stage splitting](lap-splitting.md).

## The lap file

`game` is `beamng`, `meta` is `{"discipline": "circuit"}`, files are named
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. No slip is written; the viewer derives it
from the wheel surface speeds (see [Slip, drift and derived channels](slip-and-drift.md)).
The positions are in the same frame the GameFiles BeamNG course export writes, so a recorded
lap sits on an exported course.
