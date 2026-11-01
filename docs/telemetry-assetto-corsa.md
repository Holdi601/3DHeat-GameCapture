---
title: Assetto Corsa games
parent: Telemetry recorders
nav_order: 2
---

# Assetto Corsa, ACC, AC EVO and AC Rally

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Code: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tests: `tests/test_kunos.py` (synthetic pages). Not yet run against the live games.

## Where the data comes from

Kunos's games publish telemetry for apps as **named Windows shared-memory pages** that the
game writes and anyone may read. The recorder opens them read-only (`mmap` with a tag name),
so it must run **on the PC the game runs on**, on Windows; elsewhere it exits with a message.
The pages are opened once, when the recorder starts. Starting the game and getting into the
car first is the safe order; whether starting the recorder before the game works has not
been checked.

| `--game` | Physics page | Graphics page (lap counter) | Static page (names) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | not used | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | not used | `Local\acevo_pmf_static` |

The physics page is read 200 times a second (`hz=200`); a new sample is taken only when its
`packetId` has changed and is non-zero. The first 800 bytes of the physics page share one
layout in all four games; the first game's page is only guaranteed 580 bytes, so if an
800-byte mapping cannot be opened the recorder falls back to 580 and the fields beyond it
are absent.

## Position

None of the pages carries a car position as such, but the physics page holds **each tyre's
contact point in world coordinates** (offset 420, four XYZ triples). The car's position is
the mean of the four. A page whose contact points are all zero (menu, garage) produces no
sample.

## Channels

| Channel | From | Notes |
|---|---|---|
| `time` | the recorder's own clock | seconds since recording began, rebased to the lap's first sample |
| `x`, `y`, `z` | mean tyre contact point | world metres |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | the game's units, scaled per lap to -1..1 by the largest absolute value the lap used, **only if** that value exceeds 1.05 (an input already in -1..1 is left alone) |
| `gear` | `gear - 1` | the game counts 0 reverse, 1 neutral, 2 first; written as -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, times 9.80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | local velocity at offset 568 | car frame; only when non-zero. Which side x points to is documented both ways, so read the drift angle's size, not its sign |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | offset 564 | 800-byte page only |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: offsets 204 and 252, written as 1 when above 0; AC: `tcInAction`/`absInAction` from the 800-byte page when present | aids acting |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | derived | 0..1 of the travel this lap used (min to max of `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | offsets 640, 656 (800-byte page) | divided by a typical peak - see below |
| `slipRatioRaw.*`, `slipAngleRaw.*` | the same | the physical values, unscaled |
| `padLife.*`, `discLife.*` | offsets 740, 756 | 800-byte page only |

AC Rally sends its tyre and brake temperatures in kelvin: for `--game acrally`, any of those
values above 200 has 273.15 subtracted.

`wheelSlip` (offset 56) is decoded but not written.

## Slip scaling

Forza sends slip normalised so that 1 is the edge of grip. Kunos sends the physical slip
ratio and slip angle. So the recorder divides them by a typical tarmac peak - **0.12** for
the slip ratio and **0.14 rad (about 8 degrees)** for the slip angle - so the viewer's "past 1
means sliding" reading holds approximately, keeps the raw values beside them, and writes
`"meta": {"slip": "scaled"}`. Where grip actually ends, the viewer measures per car from the
laps. See [Slip, drift and derived channels](slip-and-drift.md).

## Laps

- **AC and ACC** count laps on the graphics page (`completedLaps` at offset 132, the last
  lap's time in milliseconds at 144). `CounterSplitter` closes a lap when the counter
  changes; it is marked complete, with the game's lap time, only if the counter went up by
  exactly one.
- **AC EVO and AC Rally** are not read for laps (EVO's graphics page is a different, larger
  layout; AC Rally drives stages). `LineSplitter` uses the point where recording began as
  the line: a lap closes when the car next passes closest to it heading the same way, and a
  stage or any run closes when the car stands still for 8 seconds.

Details and thresholds: [Lap and stage splitting](lap-splitting.md).

## Track and car names

Read once, from the static page, when the first sample arrives: for AC, ACC and AC Rally the
car (UTF-16, offset 68) and track (offset 134); for AC EVO the track and its configuration
(single-byte text at offsets 136 and 169, joined by a space) and no car. They go into the
file as `track` and `car: {"name": ...}`.

## The lap file

`game` is `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` or
`assetto-corsa-rally`; `meta` is `{"slip": "scaled", "discipline": "rally"}` for AC Rally and
`{"slip": "scaled", "discipline": "circuit"}` for the other three. No `surface` is written.

## Sources

The AC1 shared memory SDK; the ACC shared memory documentation (v1.8); AC EVO's layout as
measured in `albertowd/live-telemetry-evo`; AC Rally's as read by
`LuizZak/AssettoCorsaRallyTelemetryReader`. See [Games](games.md).
