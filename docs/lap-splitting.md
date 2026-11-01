---
title: Lap and stage splitting
parent: Telemetry recorders
nav_order: 7
---

# How laps and stages are split

A recorder sees one continuous stream of samples. Turning it into laps is done by one of four
splitters, chosen by what the game says about laps. All of them follow the same idea: use
the game's own count where there is one, and otherwise find the lap from the positions; never
write a fragment too short to compare.

| Splitter | Code | Used by |
|---|---|---|
| `LapSplitter` | [`fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py) | Forza |
| `CounterSplitter` | [`kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py) | Assetto Corsa, ACC |
| `LineSplitter` | [`kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py) | AC EVO, AC Rally, BeamNG |
| `StageSplitter` | [`rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py) | EA SPORTS WRC, DiRT Rally 2.0, DiRT Rally, DiRT 4, Richard Burns Rally |

Trackmania splits runs inside its plugin ([Trackmania](telemetry-trackmania.md)), and iRacing
files are split by the viewer on the sim's lap counter ([iRacing](telemetry-iracing.md)).

On **Ctrl+C** every recorder calls its splitter's `flush()`, so an open lap or stage is
written if it passes the same minimums as below.

## LapSplitter (Forza)

Parameters: `minimum_metres = 400`, `gap_seconds = 2.0`.

For each decoded packet:

1. If the game's `timestampMs` jumped forward by more than 2 seconds since the last packet,
   or went backwards, the open lap is flushed first.
2. If `isRaceOn` is 0 (the game is not in a race), the open lap is flushed and the packet is
   dropped.
3. If no lap is open, one opens with the packet's `lapNumber`.
4. If `lapNumber` differs from the open lap's, the open lap is **closed as complete**; its
   `seconds` is the game's `lastLap` when that is positive. A lap closed this way is written
   whatever its length. A new lap opens.
5. The packet is appended.

The recorder also flushes when no packet has arrived for 2 seconds of wall-clock time (the
game paused, or closed mid-lap).

**Flushing** keeps the open lap only if it has at least 2 samples and at least 400 m of
`distanceTravelled`; it is written as incomplete (a `run`). A point-to-point race never counts
a second lap, so it always ends this way.

## CounterSplitter (AC, ACC)

Parameter: `minimum_metres = 300`. Fed each sample with the graphics page's `completedLaps`
and last lap time.

- The first sample opens a lap numbered with the current `completedLaps`.
- When `completedLaps` changes, the open lap closes. It is **complete**, with
  `seconds = last lap ms / 1000` (if positive), only if the counter went up by exactly 1 - a
  jump back to 0 (a session restart) or by several closes it as incomplete.
- A closed lap is written only if it has samples and at least 300 m of driven path.
- Flush keeps the open lap if it has more than one sample and at least 300 m.

## LineSplitter (AC EVO, AC Rally, BeamNG)

Parameters: `radius = 15 m`, `minimum_metres = 300`, `stop_seconds = 8`.

These games either have no lap counter on a page the recorder reads, or drive stages. The
**line is wherever recording began**:

1. The first sample's horizontal position (`x`, `z`) becomes the line.
2. Once the car has travelled more than 5 m, the direction from the line to the car becomes
   the lap's direction.
3. **Stopping** ends a run: when `speed` stays below 1 m/s for 8 seconds, the open lap is
   flushed (this is how a rally stage ends: the car stops at the finish).
4. **Crossing the line**: after more than 300 m of travel, samples within 15 m of the line
   are collected. When the car leaves that radius again, the closest collected sample is
   the crossing. If the car was heading the same way as the lap's direction there (dot
   product of the local heading with the direction is positive), the lap closes at that
   sample; otherwise the pass is ignored (the car crossed the start going the other way).
5. A closed lap's `seconds` is the time from its first sample to the crossing. It is
   **complete only if its first sample was faster than 5 m/s**: a lap that began from a
   standstill is a launch, not a lap to compare. The first lap of a recording started on the
   grid is therefore always incomplete; recording started on a flying lap gives a complete
   first lap at the next crossing.
6. The next lap starts at the crossing sample (it belongs to both laps).

Laps shorter than 300 m are dropped. Flush (a stop, or Ctrl+C) keeps the open lap if it has
at least 2 samples and 300 m, as incomplete. BeamNG flushes the same way when the vehicle is
reset (its clock goes back), before starting a new splitter, so the run driven before the reset
is kept.

Distances are horizontal (`x`, `z`) for the travel counter and the line test, and full 3D
for the 300 m length test.

## StageSplitter (rally games)

Parameter: `minimum_metres = 300`. Fed each sample with the game's stage clock, whether the
game says the car has finished, and optionally the game's own time for it.

1. If the clock is 0 or less, or has gone back by more than 0.5 s, the open stage is
   **abandoned**: kept as a partial stage if it is not complete, has more than 10 samples and
   at least 300 m. A clock of 0 or less also drops the sample (the car is at the start).
2. If no stage is open, a new one opens (numbered 1, 2, ... for the recording).
3. Once a stage is complete, further samples are ignored until the clock goes back.
4. Each sample is stored with `time` set to the stage clock.
5. When the game says finished, the stage is complete; its `seconds` is the game's time when
   given and positive, otherwise the clock. It is written if it covered at least 300 m.

What "finished" means per game:

| Game | Finished when |
|---|---|
| EA SPORTS WRC | stage length > 0 and stage distance >= length - 0.5 m |
| DiRT games | laps completed rose above the stage's starting count, or (single-lap event) lap distance >= 99.9% of the track length |
| Richard Burns Rally | race clock > 0 and distance to the end <= 0 |

For RBR the up axis and the speed are fixed when a stage is written (see
[Rally games](telemetry-rally.md#richard-burns-rally-rsf--ngp)).

## Time and distance in the lap file

For every recorder except Forza, `time` is rebased so the lap's first sample is 0 and
`distance` is the cumulative 3D distance between consecutive positions. Forza uses the
game's own lap timer and distance counter, rebased the same way.
