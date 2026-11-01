
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # or dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Code: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tests: `tests/test_rally.py`, on packets built from the documented layouts. **Not yet run
against the live games.**

All of them send UDP that the game switches on from its own settings files. The recorder
listens on all interfaces (`0.0.0.0`) on the game's default port unless `--port` gives
another one: **20777** for `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** for `rbr`.

## EA SPORTS WRC

### Switching it on

The game reads `Documents\My Games\WRC\telemetry\config.json`. The default `wrc` structure's
`session_update` packet has to be enabled towards this machine:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (function `configure_wrc`):

- reads the JSON, finds `udp.packets` and the entry with `"structure": "wrc"` and
  `"packet": "session_update"`;
- if it is already enabled to `127.0.0.1` or `localhost` on the port being used, prints
  `already on` and changes nothing;
- otherwise sets `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, and keeps the
  entry's `frequencyHz` (or `-1` if none); if there is no such entry it appends one;
- writes the original text to `config.json.bak` beside it, then writes the new file
  (indented 4 spaces).

Restart the game after changing the file if it does not pick the change up (not checked).

### What it sends

The default `wrc` structure is 237 bytes, little-endian, no header: world position,
velocity and acceleration (X left, Y up, Z forwards), the car's left / forward / up unit
vectors, per wheel (back-left, back-right, front-left, front-right) the hub's height and
vertical speed and the contact patch's forward speed, brake temperatures, pedals after
assists, steering (-1 left, +1 right), handbrake, rpm, gear, and the stage clock, distance and
length. A packet shorter than 237 bytes is ignored and reported once.

| Channel | From |
|---|---|
| `x`, `y`, `z` | world position |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | world velocity projected on forward, on minus left (so positive is right), on up |
| `longAcc`, `latAcc`, `vertAcc` | world acceleration projected the same way |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | as sent |
| `gear` | `gear_index`; -1 when it equals the reverse index, 0 when it equals the neutral index |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | hub position |
| `wheelSurfaceSpeed.*` | contact patch forward speed |
| `brakeTemp.*` | brake temperature |

Check: if `speed` is above 10 and the world velocity's length differs from it by more than
20%, the recorder prints once that the layout may not be the default `wrc` structure.

A stage is **finished** when the stage length is positive and the distance has reached the
length minus 0.5 m. The clock used for splitting and for `time` is `stage_time`.

Sources: EA's UDP Telemetry Guide v1.3; the channel list the game writes to
`readme/channels.json`; offsets as decoded by nobonobo/obs-codemasters-telemetry and
SpaceMonkey. The stock default port is not documented; the recorder uses 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4

### Switching it on

Edit `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally and DiRT 4 use a `hardware_settings_config.xml` too; its exact folder for those two is
not checked here) so that the `udp` element reads:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` is what puts positions, wheels and the stage length into the packet. The
recorder does not edit this file.

### What it sends

66 little-endian floats (DiRT Rally: 64); packets shorter than 64 floats are ignored and a
64-float packet is padded with zeros. The indices used:

| Index | Field | Channel |
|---|---|---|
| 1 | lap (stage) time | the splitting clock and `time` |
| 2 | lap distance | `stageDistance` |
| 4-6 | world position | `x`, `y`, `z` |
| 7 | speed | `speed` |
| 8-10 | world velocity | `longVel` (on forward), `latVel` (on the side vector) |
| 11-13 | side vector | |
| 14-16 | forward vector | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | suspension position RL RR FL FR | `suspensionM.*` |
| 25-28 | wheel patch speed RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | throttle, steer, brake, clutch, gear | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 or more means reverse, written as -1) |
| 34, 35 | lateral, longitudinal g | `latAcc`, `longAcc` (times 9.80665) |
| 37 | rpm / 10 | `rpm` (times 10) |
| 51-54 | brake temperatures | `brakeTemp.*` |
| 59, 60, 61, 62 | laps completed, total laps, track length, last lap time | splitting |

There is **no handbrake channel**. The side vector's sense is documented both ways, so the
sign of `latVel` is not to be relied on (the viewer reads the drift angle's size).

A stage is **finished** when the laps-completed count rises above its value at the stage's
start (a rallycross lap each time it does), or, for a single-lap event, when the lap distance
reaches 99.9% of the track length. The stage's time is the game's last lap time when it is
positive. Check: velocity against speed as for EA WRC, with the message "is extradata set
to 3?".

Sources: Codemasters' DiRT 4 UDP document; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP)

### Switching it on

In `RichardBurnsRally.ini`, section `[NGP]`: `udpTelemetry=1` and the endpoint (127.0.0.1,
port 6776 unless you pass another `--port`). The recorder does not edit this file.

### What it sends

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): stage clock and distance
to the end, pedals, steering, gear, world position, attitude, the car's own velocities
(surge forwards, sway sideways, heave), accelerations, rpm, and four 128-byte wheel blocks
(LF, RF, LB, RB) with spring deflection and spring force. No wheel speeds.

| Channel | From |
|---|---|
| `x`, `y`, `z` | position, axes as sent, then reordered (below) |
| `longVel`, `latVel`, `vertVel` | surge, sway, heave |
| `longAcc`, `latAcc` | acceleration x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | as sent |
| `gear` | `gear - 1` (0 reverse, 1 neutral, 2 first) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | spring deflection |
| `wheelLoad.*` | spring force |
| `speed` | **computed from the positions** over +-2 samples, not taken from the packet |

RBR's position axes, attitude units and speed unit are not documented, so when a stage is
written: the axis the stage varies least along is taken as up and swapped into `y`
(`orient_up`, needs at least 10 samples), and speed is recomputed from the positions
(`speed_from_positions`). Attitude is decoded but not written, so RBR files have no `yaw`.

A stage is **finished** when the race clock is running and the distance to the end has
reached zero. The clock is `race_time`.

Sources: NGP's `rbr.telemetry.data.TelemetryData.h` via mika-n/RBRUDPTelemetryLogger and
groybe/rbr-udp-telem.

## Stages

All five use `StageSplitter` on the game's stage clock: a stage opens when the clock starts,
closes complete when the game says the car finished, and a clock that goes back (a restart,
or the next stage) abandons the open stage - kept as a `_partial` file if it has more than 10
samples and at least 300 m. Finished stages shorter than 300 m are not written. Details:
[Lap and stage splitting](lap-splitting).

## The lap file

`game` is `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` or `richard-burns-rally`.
`meta` is `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"` when `--surface`
was given. `slip` is null because none of these games sends tyre slip. Each wheel's contact patch speed
(EA WRC, DiRT) is in the file instead, and the viewer derives slip and the drift angle from
it and the car's axes; see [Slip, drift and derived channels](slip-and-drift). The
`suspension.*` channels (0..1 of the travel used) are added from `suspensionM.*`.

When no `--surface` is given the file carries no surface at all, on purpose: a default written
here would override the viewer's own inference. The viewer then takes the surface from the
stage's or event's name (tarmac rallies, winter ones, the Monte as mixed), else from how the car
was driven on it (hard cornering at small drift angles is tarmac), and loose when nothing tells
- what a rally stage most often is. Give `--surface` when you know better.
