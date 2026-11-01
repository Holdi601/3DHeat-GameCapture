---
title: Slip, drift and derived channels
parent: Telemetry recorders
nav_order: 8
---

# Slip, drift and derived channels

The car-control analysis in the viewer's Race tab wants the same few quantities from every
game: how far each tyre slips, how far the car points away from where it is going (the drift
angle), whether it is in the air, whether it is on loose ground. Games send these in very
different forms, or not at all. The recorders here write what each game sends, under
canonical names, plus a `meta.slip` note saying what the slip numbers mean; the viewer then
derives what is missing, once, when it loads a lap. **A game's own value always wins over a
derived one.**

## What the recorders write

| Game | Slip channels | `meta.slip` | Drift angle inputs |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` per wheel, as sent | `peak` (written by the recorder; the viewer's `.tele.gz` reader sets the same) | `latVel`, `longVel` from the car-local velocity |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0.12, `slipAngle` / 0.14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` from the car-frame velocity |
| EA SPORTS WRC, DiRT games | none; `wheelSurfaceSpeed` per wheel instead | `null` | `latVel`, `longVel` = world velocity projected on the car's axes |
| Richard Burns Rally | none; no wheel speeds either | none | `latVel`, `longVel` = the car's own sway and surge |
| BeamNG.drive | none; `wheelSurfaceSpeed` and `wheelSpeed` per wheel | none | `latVel`, `longVel` = world velocity projected on the car's axes |
| Trackmania | `slipIndex` per wheel (a 0..1 sliding measure) | `index` | `latVel` (side speed), `longVel` (front speed) |
| iRacing | none (not logged) | none | `yaw` and the path, `yawRate` |

The `meta.slip` values are defined in [The heat3d-lap file](lap-format.md): `peak`
(normalised so past 1 the tyre lets go), `scaled` (a physical slip divided by a typical tarmac
peak), `physical` (a fraction and radians), `index` (a 0..1 sliding measure).

### Why Kunos slip is scaled

Forza's slip is normalised so that 1 is the edge of grip; what it normalises against is not
documented. Kunos sends the physical slip ratio (a fraction) and slip angle (radians). Dividing
by a typical tarmac peak - 0.12 for the ratio, 0.14 rad (about 8 degrees) for the angle -
makes "past 1 means sliding" approximately true for both families, which keeps one reading
for the viewer's displays. It is an approximation: real peaks vary by tyre and surface, which
is why the raw values are kept beside the scaled ones and why the viewer measures where each
car's grip actually falls away from the laps themselves.

## What the viewer derives (`deriveChannels`)

These run in the viewer (`src/race/derive.ts` in the 3DHeat viewer), not in this repository.

### Drift angle, `bodySlip`

- **From the car-frame velocity** when `latVel` and `longVel` are present:
  `atan2(latVel, |longVel|)`, and 0 below 3 m/s (a car stopped sideways is not drifting).
  Its sign follows the game's lateral velocity, whose sense is documented both ways for some
  games - read the size.
- **Otherwise from the heading against the path**: the direction of travel is taken from
  positions about 2 m either side of each sample (`atan2(dx, dz)`); the game's `yaw` is fitted
  to it with a sign and an offset (every game has its own zero and sense of rotation) using
  samples above 10 m/s, and trusted only if it then agrees closely (circular spread at most
  0.05, at least 20 samples). The drift angle is the difference, 0 below 3 m/s.

### Slip ratio from the wheels

Where a lap has no `slipRatio.*` but has wheel speeds, the slip ratio is
`(wheel - car) / car` per wheel, from:

- `wheelSurfaceSpeed.*` (the contact patch's speed, m/s) directly, when sent (EA WRC, DiRT,
  BeamNG);
- otherwise `wheelSpeed.*` (rotation, rad/s) times a **rolling radius measured on the lap**:
  the median of `speed / |omega|` over samples where the car coasts in a straight line (above
  10 m/s, not airborne, throttle below 0.3, brake below 0.05, longitudinal acceleration below
  3 m/s²); with fewer than 20 such samples, every sample above 10 m/s. A radius outside
  0.1-1 m is rejected.

Only when all four wheels can be derived; the lap's `meta.slip` then becomes `physical`. Below
3 m/s the slip is 0.

### Airborne

`airborne` is 1 where every wheel is off the ground, judged by the first of these the lap has
for all four wheels:

1. `groundContact.*` (BeamNG): no wheel above 0.5;
2. `wheelLoad.*` (AC games, RBR, BeamNG): no wheel above 5% of its own median load;
3. `suspension.*` (0..1 of travel): no wheel above 0.02, i.e. all fully extended.

A single isolated airborne sample is cleared. Trackmania writes `airborne` itself.

### Loose ground

Where a lap has `surfaceRumble.*` (Forza), `loose` is 1 where at least two wheels report
rumble for at least a third of a second, with gaps shorter than one second bridged (a
smooth patch on a gravel road is still the gravel road). Trackmania writes `loose` itself from
the wheels' ground materials.

### Yaw rate

Where a lap has `yaw` but no `yawRate`, it is the change in yaw over the neighbouring samples.

## What the recorders derive themselves

- **`suspension.*`** (0..1): every recorder except Forza (which sends it) writes it from
  `suspensionM.*` as the position within the range this lap used (minimum to maximum). It is
  for the car's suspension bars and for spotting a wheel hanging in the air; it is not an
  absolute travel fraction.
- **`steer`** for the Kunos games, scaled per lap (see
  [Assetto Corsa games](telemetry-assetto-corsa.md)).
- **Accelerations** for BeamNG, from the change in world velocity
  ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** and the up axis for Richard Burns Rally, from the positions
  ([Rally games](telemetry-rally.md)).

## Handedness

Where a game's world is left-handed - Forza's is - a course comes out mirrored in a
right-handed viewer; the laps' own steering and suspension give it away. The recorders do not
change handedness: a Z-up world (BeamNG) is turned to Y-up by a rotation, which keeps it, and
everything else is written as sent.
