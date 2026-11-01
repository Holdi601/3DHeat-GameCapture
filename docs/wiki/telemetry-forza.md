
# Forza Horizon and Forza Motorsport

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Code: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(layout detection),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(every channel, lap files, relay).

## Switching it on in the game

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (or whatever
you pass as `--port`). Forza Motorsport also offers a packet format: it must be **Dash**, not
Sled. Sled carries no position at all, and the recorder refuses it.

The recorder binds to `127.0.0.1`, so the game has to run on the same PC.

## What the game sends, and how the layout is found

Data Out is one UDP packet per simulation tick (about 60 a second), a flat little-endian C
struct in these sizes:

| Length | Variant |
|---|---|
| 232 bytes | Motorsport "Sled": no position. Rejected with a message telling you to switch to Dash. |
| 311 bytes | Motorsport "Dash": Sled block plus the 79-byte dash block |
| 324 bytes | Horizon "Dash": the same with padding between the two blocks |
| 331 bytes | Forza Motorsport (2023): Dash plus 20 bytes of tyre wear and the track id |

The Sled block (offsets 0-231) is stable. Where the dash block starts in the Horizon variant
is described inconsistently in published sources, and guessing wrong does not fail - it
yields plausible floats from the wrong fields. So the start is **discovered**:

1. Candidate starts are tried in order: `length - 79` (the dash block runs to the last
   byte in every documented variant), 232, 244, and 232 to 260 in steps of 4.
2. Each candidate is scored on packets from a moving car (a velocity component above
   1 m/s): the Sled block's velocity vector and the dash block's scalar `Speed` are the same
   quantity in two places, so `| |velocity| - Speed |` is near zero only for the right start.
3. The candidate with the smallest worst-case disagreement wins, if that disagreement is at
   most **1 m/s**. Otherwise detection keeps waiting.

While the car is parked every candidate reads zero and agrees, which proves nothing, so
**detection waits until the car moves**: drive a few metres before expecting output. Up to
600 packets are held while waiting (trimmed to the latest 300). Once the layout is known,
the held packets are decoded too, so the start of the first lap is not lost. Packets of a
different length from the detected layout, packets shorter than 311 bytes, and packets
with a non-finite position or speed are ignored for the lap files.

Which Forza it is follows from the layout: a Horizon layout gives `"game": "forza-horizon"`,
a Motorsport or 331-byte layout gives `"forza-motorsport"`, anything else `"forza"`. The
detected layout's name (`Horizon dash`, `Motorsport dash`, `331-byte dash`) is written as
`layout`.

## Channels recorded

Every field of the packet is decoded (`decode_full`) and converted:

- pedals `throttle`, `brake`, `clutch`, `handbrake` from 0..255 to 0..1;
- `steer` from -127..127 to -1..1; `drivingLine` and `aiBrakeDifference` likewise divided by 127;
- `tireTemp.FL` ... `.RR` from Fahrenheit to Celsius;
- `latAcc`, `longAcc`, `vertAcc` and `yawRate` are copies of `accelX`, `accelZ`, `accelY` and
  `angVelY` under the canonical names (car frame: x right, y up, z forward);
- the Sled velocity, which is in the car's own frame (x right, y up, z forward - not the
  world's), is written straight under the canonical names `latVel`, `vertVel` and `longVel`, so
  the viewer reads the drift angle off it rather than estimating it from heading and path.

The lap file's channels are all of these except the per-lap and bookkeeping fields:

| Group | Channels |
|---|---|
| Time and place | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition` |
| Motion | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Engine | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Driver | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Per wheel (`.FL .FR .RL .RR`) | `suspension` (0 stretched .. 1 compressed), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalised: past 1 the tyre lets go), `wheelSpeed` (rad/s), `rumble` (on a rumble strip), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Forza Motorsport 2023 only | `tireWear.FL` ... `.RR` |

`time` is the game's current-lap timer minus its value at the lap's first sample; `distance`
is the game's distance travelled minus its first value. Positions are Forza's world
coordinates in metres, unchanged (y is up; the world is left-handed).

Taken once per lap rather than per sample, under `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. FM2023's track id goes in once too, as
`lap.trackOrdinal`. Not kept at all: `isRaceOn`, `timestampMs`, `bestLap`, `lastLap`,
`raceTime`.

The rest of the document is filled like every other recorder's:

- `"track": null` - Forza Horizon does not name the course, and Forza Motorsport only numbers it;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - the slip channels are normalised so that
  past 1 the tyre lets go;
- `units` lists only the channels the file has (per-wheel ones by their base name);
- a value that is not a finite number is written as `null`, never `NaN`.

See [The heat3d-lap file](lap-format).

## How laps are split

`LapSplitter` (see [Lap and stage splitting](lap-splitting)): a lap closes when the
game's lap counter moves on, and its time is then the game's own `lastLap` (what the game
shows). A point-to-point race or a session that ends mid-lap closes when the game leaves the
race (`isRaceOn` drops), when the packets stop for 2 seconds, or when the game's timestamp
jumps back; it is kept as a `run` if it covered at least 400 m.

## Relaying to FH Companion

The game sends Data Out to one address only. With `--forward host:port`, the recorder passes
**every packet it receives on unchanged**, before it decodes anything (also while it is still
waiting to detect the layout), so another app reading the feed keeps working: set the game
to 5300, the other app to 5301, and run with `--forward 127.0.0.1:5301`.

FH Companion is a separate app, not part of 3DHeat. It keeps a lap library under
`%LOCALAPPDATA%\FHCompanion\laps`: a folder per course, one lap file per lap sampled about
every five metres, and beside each lap file `<lap>.json.tele.gz`, the lap's whole Data Out at
the game's rate. 3DHeat reads both:

- **The viewer reads `.tele.gz` directly** when you drop it (with or without its lap file) on
  the Race tab. It maps Forza's own field names (`PositionX`, `VelocityX`, `TireSlipRatio`
  + wheel, ...) to the canonical channels, turns the car-local `VelocityX/Y/Z` into `latVel`,
  `vertVel`, `longVel`, converts tyre temperatures from Fahrenheit, drops rows that repeat the
  previous one but for the recorder's clock, and marks the slip as `peak`. Given the lap file
  too, the lap takes its car and lap time from there. This reader lives in the viewer
  (`src/race/adapters.ts`, `readForzaTelemetry`), not in this repository.
- **The `laps` command** reads the lap library and writes a course's route and a CSV of every
  sample; see [Command reference](commands#laps).

## Other uses of the same feed

- `python -m heat3d_capture route` records only the positions, saved every couple of seconds
  while driving; see [Command reference](commands#route).
- The scan window's "Racing telemetry (Forza)" option uses the feed as exact camera poses
  for reconstruction; see [Camera pose and scale](reconstruction-pose#telemetry-poses).

## Notes and caveats

- What Forza normalises its slip against is not documented. `1` is read as the edge of grip,
  but the viewer measures where each car's grip actually falls away.
- The Sled velocity is car-local, as Forza's Data Out documentation says and recorded laps
  confirm (its forward component carries the speed, its sideways one stays near zero). Layout
  detection uses only its length, which is the same in any frame.
- Positions are the game's world, Y up and left-handed. The senses of `yaw`, `pitch` and `roll`
  were checked on recorded laps: the yaw equals the direction of travel `atan2(dx, dz)`, a
  positive pitch is nose down, and a positive roll drops the right side.
