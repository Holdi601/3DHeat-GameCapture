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
Tests: `tests/test_kunos.py` (synthetic pages, and the whole recording loop on pages that change
between reads). Not yet run against the live games.

**One session, one file.** Each session (practice, qualifying, a race: one track, layout and
car) is written as one `heat3d-session` file, `<date>_<time>_<game>_session.json`, holding every
lap of it and the runs between them, and for ACC and AC EVO the other cars' positions. The
file is rewritten after every lap, so a session cut short keeps what was driven. With
`--per-lap` the recorder writes one `heat3d-lap` file per lap instead, as before.

## Record a lap, step by step

1. Start the game and drive out of the pits (the car on track, not in a menu).
2. In a terminal on the same PC: `python -m heat3d_capture telemetry --game ac -o laps`
   (`acc` or `acevo` for the other two). It prints `reading ac's shared memory, one file per
   session, into laps`.
3. Drive. Each finished lap prints a line such as `lap 2: 104.521 s -> ..._session.json`.
4. Press **Ctrl+C** when done. The session file is in `laps`.
5. In the 3DHeat viewer: **Race analysis** tab, **Load lap files...**, pick the session file.
   Every lap of it loads, and the other cars of an ACC or AC EVO session with them.

## Where the data comes from

Kunos's games publish telemetry for apps as **named Windows shared-memory pages** that the
game writes and anyone may read. The recorder opens them read-only (`mmap` with a tag name),
so it must run **on the PC the game runs on**, on Windows; elsewhere it exits with a message.
The pages are opened once, when the recorder starts. Starting the game and getting into the
car first is the safe order; whether starting the recorder before the game works has not
been checked.

| `--game` | Physics page | Graphics page (laps, sectors, other cars) | Static page (names) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics`, 300 bytes | `Local\acpmf_static`, 688 bytes |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics`, 1412 bytes | `Local\acpmf_static`, 688 bytes |
| `acrally` | `Local\acpmf_physics` | not used | `Local\acpmf_static`, 256 bytes |
| `acevo` | `Local\acevo_pmf_physics` | `Local\acevo_pmf_graphics`, 4904 bytes | `Local\acevo_pmf_static`, 208 bytes |

Each graphics and static page is opened at the largest of the sizes the recorder knows for
that game; a game whose page is shorter (an older build) is opened at the next size that fits
(ACC 1240 or 256, AC 256, AC EVO 3944 - before its 2026-04 build added `car_ids`; AC and ACC
static 256), and the fields past it are absent.

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
| `lapFraction` | AC, ACC: `normalizedCarPosition` (graphics 248); AC EVO: `npos` (1244) | 0..1 along the lap, the game's own |
| `sector` | AC, ACC: `currentSectorIndex` (164) | 0-based |
| `lapTimeMs` | AC, ACC: `iCurrentTime` (140); AC EVO: `current_lap_time_ms` (188) | ms into the lap |
| `racePosition` | AC, ACC: `position` (136); AC EVO: `current_pos` (2388) | |
| `inPit`, `inPitLane` | AC: `isInPit` (160), `isInPitLane` (276); ACC: 160, 1236; AC EVO: `is_in_pit_box` (3119), `is_in_pit_lane` (3120) | 1 or 0 |
| `lapValid` | ACC: `isValidLap` (1408); AC EVO: `is_valid_lap` (3121) | 1 or 0; a lap with any 0 is written `"valid": false` |
| `steerDegrees` | AC EVO: `steer_degrees` (156) | the steering wheel's angle |

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
- **AC EVO** has no lap counter on its pages, but its own position along the lap (`npos`).
  `PositionSplitter` closes a lap where `npos` falls from above 0.9 to below 0.1, which is
  where the game's line is; the lap is complete if it began within 0.05 of the line, and its
  time is the game's last-lap time when that changes within 3 seconds of the line (the
  samples' span otherwise). An EVO page too short for `npos` falls back to `LineSplitter`.
- **AC Rally** drives stages. `LineSplitter` uses the point where recording began as the
  line: a lap closes when the car next passes closest to it heading the same way, and a
  stage or any run closes when the car stands still for 8 seconds.
- A lap the game counted but that was joined part-way round (its first `lapFraction` between
  0.05 and 0.95) is written as a run, not a complete lap.

Details and thresholds: [Lap and stage splitting](lap-splitting.md).

## Track, layout and car

From the static page: for AC, ACC and AC Rally the car (UTF-16, offset 68) and track (offset
134); for AC and ACC also the track's layout (`trackConfiguration`, 524), its length
(`trackSPlineLength`, 520), the sector count (400), the car's top rpm (412), fuel capacity
(416), tyre radii (436), skin (604) and whether the session is online (684). For AC EVO the
track (136), its configuration (169) and length (204) from the static page, and the car's
model id from the graphics page (3086). The player's name is on the static page too and is
not read.

They go into the file as `track`, `layout`, `trackLength`, `sectorCount`, `online` and
`car: {"name", "skin", "maxRpm", "maxFuel", "tyreRadius"}`. `layout` is empty for a track
with one layout. A track export is matched by the track and its layout.

## Sessions

A new session begins when the track, the layout, the car, the session type (graphics
`session` at offset 8 in AC and ACC) or ACC's session index (1320) changes; what was being
driven closes the old session's file. The file:

```json
{
  "format": "heat3d-session",
  "version": 1,
  "game": "assetto-corsa-competizione",
  "track": "monza", "layout": "", "car": {"name": "..."},
  "session": 2, "sessionType": "race",
  "recordedAt": "2026-11-22T18:20:30+01:00",
  "laps": [{"format": "heat3d-lap", "...": "one heat3d-lap document per lap or run"}],
  "others": [{"id": "7", "channels": {"time": [], "x": [], "y": [], "z": []}}]
}
```

`sessionType` names AC's and ACC's session numbers (practice, qualify, race, hotlap,
time-attack, drift, drag; ACC: practice, qualify, race, hotlap, hotstint, superpole); AC EVO's
is written as its number only.

## Other cars

ACC's graphics page lists every car on track (`activeCars` 252, `carCoordinates` 256, `carID`
976, `playerCarID` 1216); AC EVO's too (`active_cars` 3852, `car_coordinates` 3124, `car_ids`
3944 against `player_car_id` 24). The recorder samples them 10 times a second into `others`,
one entry per car by its id, positions only. The table is believed only if the player's own
entry is within 8 m of where the physics page puts the player's car in at least four of five
samples (and five or more): a page whose layout is not what the recorder expects writes no
other cars rather than wrong ones. AC's graphics page holds the player's car only, so an AC
session has no `others`. The games' pages name no other driver.

## The lap file

Each lap in a session file, and each file `--per-lap` writes, is a `heat3d-lap` document.
`game` is `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` or
`assetto-corsa-rally`; `meta` is `{"slip": "scaled", "discipline": "rally"}` for AC Rally and
`{"slip": "scaled", "discipline": "circuit"}` for the other three. No `surface` is written.

## Sources

The AC1 shared memory SDK; the ACC shared memory documentation (v1.8); AC EVO's physics
layout as measured in `albertowd/live-telemetry-evo`, its graphics and static pages from the
published `SharedFileOut.h` documentation (2026-04-28, natural C alignment, the inner structures
at their stated sizes); AC Rally's as read by
`LuizZak/AssettoCorsaRallyTelemetryReader`. See [Games](games.md).
