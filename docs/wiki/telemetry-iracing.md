
# iRacing

iRacing needs **no recorder**. The sim writes its own telemetry files, `.ibt`, when telemetry
logging is on (Alt+L in the car): the whole session at 60 Hz, every channel the sim exposes,
with the session's YAML description alongside. Drop the `.ibt` file on the viewer's Race tab.

The reader lives in the viewer, not in this repository (`src/race/ibt.ts` in the 3DHeat
viewer). It is tested on a synthetic file; it is documented here because it is the iRacing
half of the same lap-recording story.

## What the file holds, and how it is read

The file is the sim's documented memory layout written to disk:

| Part | Size | Holds |
|---|---|---|
| Header | 112 bytes | version, tick rate, where the YAML and the variable table are, the length of one sample row, where the rows start |
| Disk sub-header | 32 bytes | start date and time, lap count, row count |
| Variable table | 144 bytes per channel | type, offset in the row, count, name, description, unit |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rows | one per tick | |

A file is refused when it is shorter than 144 bytes, when its header is not sane (no
variables, a variable table outside the file, a zero row length), when it lacks any of
`SessionTime`, `Lap`, `Lat`, `Lon`, or when no sample has a position fix.

## Position

iRacing reports latitude, longitude and altitude, not a position in the track's own frame.
Positions are laid out in metres on a plane tangent at the first sample with a fix (Earth
radius 6,371,008.8 m): `x` east, `z` south, `y` the altitude - so that from above, with the
viewer camera's default heading, north is up the screen.

## Laps

The session is split on the sim's `Lap` counter. A lap is kept only if it has more than 60
samples, starts below 5% of the lap distance (`LapDistPct`) and ends above 95% - that is, laps
driven from line to line. If no lap qualifies, the file is refused with a message naming the
track length from the YAML. `distance` is `LapDist` rebased to the lap's start, or the
driven distance from the positions when `LapDist` is missing; `time` is `SessionTime` from
the lap's start.

## Channels

| iRacing | Channel | Conversion |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | none |
| `Clutch` | `clutch` | `1 - value` (iRacing counts the clutch as engaged; the channel is the pedal) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radians, anticlockwise positive, to -1..1 right positive; pi when the maximum is missing) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | none |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | none |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | aid settings |
| `dcBrakeBias` | `brakeBias` | divided by 100 when above 1.5 (a percentage on some cars) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | carcass temperature across the middle |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa times 0.145038, to psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Every other channel with one value per sample (and not a single byte) is passed through under
its own name, with a wheel prefix (`LF`, `RF`, `LR`, `RR`) turned into a suffix
(`.FL`, `.FR`, `.RL`, `.RR`), so the viewer's graphs offer it without anyone describing it.

The car comes from `DriverInfo`: the entry whose `CarIdx` matches `DriverCarIdx` gives
`CarScreenName`, `CarID` and `CarClassShortName`. The track is `TrackDisplayName` (or
`TrackName`).

## What iRacing does not give

No tyre slip is logged, so there are no slip channels. The drift angle is derived from the
yaw rate against the path (see [Slip, drift and derived channels](slip-and-drift)). Track
models ship in a protected format and are not a file-extraction target (see [Games](games)).
