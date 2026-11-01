
# Reading the HUD from a recording

`hud` reads a game's on-screen HUD out of the player's **own recording**, after the match: the
kill feed as timed events, and the player's **own** track from the minimap, written as a 3DHeat
table with the minimap's mosaic as a map image to lay under it.

```bash
.venv/Scripts/python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match
```

Battlefield 6 is the first game profile.

## What it does and does not touch

- It reads a **video file**: a ShadowPlay / Instant Replay clip, an OBS recording, anything
  ffmpeg decodes. It never touches the game, its memory, its files or its network, and it runs
  after the match is over. See [The rules](rules).
- It derives **only the player's own position**, from the player's own minimap. Other players'
  markers on the minimap are masked out and never read. The kill feed is kept in full, but only as
  what it says on screen (who, whom, with what, when); no position is attached to anyone but the
  player.
- The OCR runs locally (RapidOCR with the PaddleOCR models through ONNX Runtime). No frame or
  crop leaves the machine.
- A recording shows other players' names, and the mosaic is a picture of the level. The outputs
  are for the player's own use; keep them local.

## Requirements

- **ffmpeg and ffprobe** on `PATH`. An NVIDIA card is used for decoding when there is one
  (`-hwaccel cuda`); otherwise the CPU decodes, several times slower.
- The packages in `requirements.txt`, and the OCR without its own dependencies (it asks for the
  CPU `onnxruntime`, which clashes with the DirectML one the project uses):

```bash
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pip install --no-deps rapidocr_onnxruntime==1.2.3
```

- A **16:9** recording at any resolution (1080p, 1440p, 4K). Other aspect ratios are refused,
  because the profile's boxes would land on the wrong parts of the screen.
- The game's **default HUD layout**. A moved or scaled HUD element is read in the wrong place.

## Options

| Option | Default | Meaning |
|---|---|---|
| `video` | | The recording. |
| `-o`, `--out` | the video's name, in the current folder | Output path **without** extension; the files are `<out>.parquet`, `.events.jsonl`, `.summary.json`, `.map.png`, `.map.json`. |
| `--game` | `bf6` | Whose HUD to read. `bf6` (Battlefield 6) is the only profile so far. |
| `--player` | none | The player's name as the kill feed shows it. Compared loosely (OCR confuses `l`/`I`/`1`, `O`/`0`, `rn`/`m`). Without it the name is guessed (below). |
| `--fps` | 5 | Minimap samples per second. The kill feed is sampled at half that, the compass every 3 s, the squad list every 15 s. |
| `--start` | 0 | Seconds into the video to begin at. |
| `--seconds` | all | How much of the video to read. |
| `--metres-per-pixel` | none | The minimap's scale, if known: metres per minimap pixel at the usual zoom (the minimap is 296 pixels wide on a 1080p screen). Without it positions are in those pixels; see [Units](#units). |
| `--cpu` | off | Decode on the CPU even when an NVIDIA card is there. |

Progress is printed every five seconds; at the end the player, kills, deaths, lives and the files
written.

## Outputs

### `<out>.parquet` - the player's track and events

One row per sample the player was in play and the minimap could be placed, plus one per event of
theirs. The footer carries the viewer's reading instructions (`heat3d` key, `kind: heat3d-hud`), so
the viewer maps every column without asking.

| Column | Meaning |
|---|---|
| `time` | Seconds from the start of the video. |
| `event` | `position`; `start` (the video began mid-life), `spawn` (back in play after a death or a long gap), `revive` (still in play long after a feed death), `death`, `end` (a life ended with no feed line to say how), `kill`, `teamkill`, `suicide`, `squadwipe` (the player's kill finished off a squad). |
| `x`, `y`, `z` | Position on the mosaic: `x` east, `y` north, `z` 0 (the footer says `z` is up). North is real north when the compass allowed it (see `north_up` in the summary). |
| `player` | Always `me`. Only the player's own rows have positions. |
| `team` | `own`. |
| `session` | `<video name>#NN`, one per life. Line heat routes never cross a session. |
| `heading` | Degrees clockwise from north (from the mosaic's up when north is unknown): where the view pointed. |
| `dir_x`, `dir_y`, `dir_z` | The same as a direction vector, for the viewer's look direction. |
| `zoom` | How far the minimap was zoomed out against its usual zoom (above 1 in vehicles). |
| `killer`, `victim`, `weapon`, `headshot`, `marker` | On kill and death rows: the feed line (below). |

Kill and death rows take the player's position at the feed line's time (for a death, the last
position before it). The rows fit the viewer's [line heat](https://holdi601.github.io/3DHeat-Docs/line-heat.html) directly: its
suggestion picks `event`, starts at `start`, `spawn` and `revive`, ends at `death` and `end`, and
`position` rows lie along the route; `kill` is not an end.

A clip with two rounds on two maps gives two mosaics that cannot be related. The largest is
`<out>.parquet`; each other one with at least 30 s of track is written beside it as
`<out>.map2.parquet`, `<out>.map2.map.png`, and so on.

### `<out>.events.jsonl` - the kill feed

Every line the feed showed, everyone's, one JSON object per line, in order of first appearance:

| Field | Meaning |
|---|---|
| `time`, `last` | First and last sample the line was read in (seconds from the start of the video). `time` is when the kill appeared, to within one feed sample (0.4 s at the default rate). |
| `kind` | From the player's side: `kill`, `death`, `teamkill`, `suicide`, `squadwipe`; for other players' lines `kill`, `squadwipe`, or `death` for a line with no killer. |
| `killer`, `victim` | The names, as the most frequent read across all the samples showing the line (a longer read wins when the common one is its start: a name partly hidden). `killer` is empty for a line that showed only an icon and a victim - a death to the world, or a line whose killer had already faded. |
| `killer_side`, `victim_side` | From the name's colour: `friendly` (the player's team, blue), `enemy` (orange), `squad` (the pale green the game uses for the player and their squad), `neutral` (none of these). |
| `weapon` | The weapon icon's class within this run: `icon01`, `icon02`... Lines whose icons look alike share a class. The icons are not named; there is no list to name them from. |
| `marker` | The small icon between the weapon and the victim: `skull`, `arrow`, `chevrons`, `crosses` or empty. |
| `headshot` | `marker == "skull"` - an assumption, see [Limits](#limits). |
| `seen` | How many feed samples showed the line. |
| `me` | `killer`, `victim` or null. |
| `x`, `y` (, `map`) | For the player's own lines: where they were. |

### `<out>.summary.json`

Player (and how it was found), kills, deaths, K/D, teamkills, suicides, squad wipes, lives,
seconds in play, distance travelled (in the table's units), feed lines, per map whether it is north
up and how many compass reads agreed, the track's counts (samples, in play, placed, not placed,
islands), the assumptions made, and the timing.

### `<out>.map.png` and `<out>.map.json` - the map under the track

The mosaic of every minimap of the run, averaged, overlays removed, turned and scaled exactly like
the table. The JSON sidecar holds the two anchors the viewer's **Map image** placement asks for
([Map images](https://holdi601.github.io/3DHeat-Docs/map-images.html) in the viewer's documentation): load the PNG with
**Map image...**, keep **Flip north/south** on, and type anchor 1 and anchor 2 (`px`, `py`,
`worldX`, `worldZ`) from the sidecar. The image then lies exactly under the track.

Only the parts of the level the player's minimap showed are in the picture.

## Method

### Decoding

ffmpeg decodes on the GPU, drops to the sampling rate while the frames are still on the card, cuts
out the profile's regions (minimap, kill feed, two compass strips, squad list), scales each to a
fixed size and stacks them into one small picture per sample. Only that picture crosses the pipe
into Python. Decoding every frame of the H.264 stream is the floor on the run time.

Two worker threads take the samples: one registers minimaps (OpenCV), one reads text (ONNX Runtime).

### In play or not

The minimap's key-hint square (the light square with the map key in it, bottom left of the
minimap) is drawn whenever the minimap is, and not on death, kill-cam, deploy, menu or scoreboard
screens. Its presence - a light, colourless square, with a dark letter in its middle, clearly
lighter than what is round it - searched a few pixels round its place, is the in-play test. A
single sample that disagrees with both neighbours is ignored.

A gap in play is a death or a round change (the next stretch starts with `spawn`) when it lasts at
least 6 s or a feed line names the player as victim within 40 s before it; a shorter gap with no
death (the big map opened) continues the life.

### The track

The minimap turns with the view and keeps the player at a fixed point (measured: the middle, 49.7%
down). Each sample:

1. **Mask** what is not the level: strongly coloured or near-white pixels (objective markers, squad
   and vehicle icons, pings, the play-area boundary, route lines, text), the faint yellow-green of
   the view cone, a disc round the player's marker, the cone's wedge above it, the key hint, and a
   thin rim.
2. **Features**: SIFT keypoints on the contrast-equalised grey minimap, inside the mask.
3. **Register to the mosaic**, not to the previous sample: the keypoints are matched against the
   features stored so far, in mosaic coordinates, near where the player last was; a similarity
   (turn, zoom, shift) is fitted with RANSAC. A fit needs enough inliers, a zoom within a third of
   the last one and a shift of less than a third of the minimap per sample; a fit searched
   anywhere on the mosaic (after a death) needs twice the inliers.
4. **Grow the mosaic**: features the mosaic does not have yet are added (at most every few tenths
   of a second of movement), and the masked minimap is averaged into the picture.
5. The player's point carried through the fit is their **position**; the minimap's up carried
   through it is their **heading** on the mosaic.

Afterwards a point that jumps more than 10 pixels away from both the two samples before it and the
two after it (which agree among themselves) is dropped: a minimap now and then matches at a wrong
zoom for one sample. The summary counts them (`dropped_as_jumps`).

Registering to the mosaic is what keeps errors from adding up: coming back to a place matches the
features stored the first time. A spawn somewhere not yet seen starts a separate **island**; every
tenth placed sample is tried against the other islands, and the first good match joins them (the
smaller moves into the larger, with its track). Islands never joined (another map, or ground never
shared) are written separately as above.

### North and units

The compass strip is read every 3 s: its labels are found by their ink (bright, colourless,
grouped across small gaps, ticks dropped), each is read on its own, and two or more labels fix both
the strip's scale and the bearing under the centre mark - a single label fixes nothing. Each
compass reading is paired with the mosaic heading of the same sample; the circular median of the
differences, over the readings within 10 degrees of it, is the turn that puts the mosaic north up.
It is applied when at least three readings and half of all of them agree.

<a id="units"></a>The minimap's ground scale is not printed anywhere on screen, so positions are in
**minimap pixels at the usual zoom**: the median zoom of the run is scaled to one table unit per
pixel of a 296-pixel minimap (its size on a 1080p screen). The vehicle zoom-out is taken out by the
registration, so a unit is the same on foot and in a vehicle. `--metres-per-pixel` multiplies
everything into metres when the scale is known (from a known distance on the map, measured once).

### The kill feed

The feed is read at 2.5 samples a second, but only when its coloured pixels changed noticeably or
2 s passed. Text lines are found by the OCR's detector; a line whose picture matches one read in the
previous sample (rows scroll, so it may have moved) takes that text instead of being read again.
Lines too small for a name, or with a slash (an fps counter in that corner), are dropped.

Lines are grouped into rows by height; in a row the leftmost name is the killer and the rightmost
the victim. Neighbouring pieces of the same colour join (a name with a space). A single line that
ran across the icon from one name into the other is cut at its widest gap when the halves differ in
colour, and each half read again. A single name in the victims' column with an icon just left of it
is a line without a killer. Two pieces in one colour with no icon between them are one name whose
killer has faded, not a kill.

**Sides** come from colour. Names are drawn with some transparency, so the test is on how far the
text is from its own background: the sign of red minus blue in that difference is orange (enemy)
or blue (friendly) on any background; neither, with green above the other two, is the squad colour.

**Icons**: between the names, the pixels in the killer's colour make the weapon's silhouette; a
small separate icon right before the victim is the marker, named by its shape (a blob with eye holes
is a skull; a small triangle an arrow; several pieces crosses).

**Events**: a row read again with both names alike (similarity 0.7 after folding the usual OCR
confusions, one of them 0.8; a read cut short matches the start of the full name) is the same
event, as long as the event was last read under 5 s before and is under 14 s old - no row stays up
longer, so the same pair later is a new kill. A row without a killer matches on the victim alone.
An event's time is its first sighting; its names, sides and marker are the majority across
sightings; rows read only once are dropped.

**The player**: `--player`, else the squad list's highlighted (brightest) row when at least three
reads and 60% of them agree, else the name the feed drew most often in the squad colour. Otherwise
the summary says the player is unknown, and no kills or deaths are attributed.

## What is verified

Measured on three Battlefield 6 recordings of 20 minutes each at 4K, 60 fps (the player's own,
not part of the repository): tanks, infantry, a helicopter, two maps, 25 lives in all.

**Run time.** 243 s and 247 s for two 20-minute clips run one at a time, on an RTX 5080 with a
desktop CPU (decoding, at about 5 times real time, is most of it); all three at once took 363 s.

**Kill feed**, checked by eye on 24 random feed samples (12 from each of two recordings), against
every row on screen in each:

| | |
|---|---|
| Rows with a killer and a victim on screen | 99 |
| ...found as an event with both names right (small OCR slips such as `Tex` for `TeX` allowed) | 96 (97%) |
| ...found with the victim only (the killer's name in glyphs the game itself draws as boxes) | 2 |
| ...missed (the victim's name in such glyphs) | 1 |
| Rows with only an icon and a victim (a death to the world, or a killer already faded) | 4, not reported by the version checked on the first recording; reported now, with an empty killer |
| Events shown for those samples that were not a row on screen | 2 (a duplicate of a row whose end was hidden; one victim name split in two, since fixed) |
| Sides (colours) wrong among the names checked | about 2% |

A row's time is its first sighting, within one feed sample (0.4 s) of it appearing. The player's
own kills and deaths in the samples were all found.

**In play.** 72 random moments across the three recordings, compared with the frame: the key-hint
test was right on all of them after one fix (a minimap over a light-tinted sector read as "not in
play" for 33 s in one recording). One moment was in play but left out of the table by the death
rule (a downed player revived and killed again within 40 s).

**Track.** There is no ground truth for where the player was, so the track is checked against the
recording itself: two minimaps are registered **directly to each other**, and the offset that gives
is compared with the offset between the two table positions. Pairs are drawn at random.

| | Revisits (same place, 30 s or more apart, often different lives) | 10-second windows |
|---|---|---|
| Tank and infantry, recording 1 | median 1.0, 90% under 4.4, max 6.4 | median 1.2, 90% under 4.1, max 11.6 |
| Tanks and a helicopter, recording 2, map 1 | median 1.1, 90% under 3.4, max 5.2 | median 1.0, 90% under 8.2; one window in the helicopter 65 off |
| Infantry, recording 2, map 2 (crowded, zoomed-out minimap) | median 3.4, 90% under 12.7, max 18 | median 3.2, max 15 |
| Tanks and infantry, recording 3 | median 1.5, 90% under 8.4, max 10.6 | median 1.1, 90% under 4.4, max 7.3 |

Units are pixels of a 296-pixel minimap at the usual zoom: an error of 1.5 is half a percent of the
minimap's width. Over 16 windows where the player did not move (the direct offset under 3), the
table moved at most 3.4. North: 86 of 86, 147 of 149, 41 of 41 and 200 of 202 compass reads
agreed with the mosaic within 10 degrees, with a median disagreement of 1 to 2 degrees.

Looked at by eye: every mosaic has continuous roads and buildings across the lives that built it,
and the routes of different lives driven along the same road lie on top of each other. One
10-second stretch in an earlier run (not in the random samples above) had its distance about
twice too long, with the minimap's zoom changing - see [Limits](#limits).

The tests (`tests/test_hud_*.py`) draw everything they read: a made-up level of roads, buildings and
contours, minimaps of walks through it with the overlays a real one has, compass strips, kill-feed
rows with made-up names. They check that a loop is tracked to within two pixels and closes, that a
standing player stays put while the view turns, that zoom changes are followed, that a spawn
elsewhere is joined back when the paths meet, that the north turn and the y flip put the track
where it truly went, that the map image's anchors line it up under the track, and the feed's
parsing, sides, markers and de-duplication.

## Limits

- **Units are minimap pixels**, not metres, unless `--metres-per-pixel` is given. Nothing on the
  game's screen states the minimap's ground scale.
- **Only what the minimap showed is mapped.** The mosaic covers the ground within half a minimap
  of where the player went; two mosaics that never shared ground (two rounds on two maps, or two
  lives in far-apart corners of a large map) stay separate files with unrelated coordinates.
- **The track is the minimap's, at 5 samples a second**, smoothed by nothing. A minimap zoomed far
  out (a helicopter in the test recordings zoomed it out to 2.3 times) shows less detail per pixel,
  and outside the play area it shows almost none, so registration there is coarser. Jets, and the
  player as a passenger, were not in the test recordings.
- **Registration errors are local and do not accumulate**, but a mosaic built while exploring new
  ground can carry a small bend that is fixed only when the ground is seen again. Where the
  minimap's zoom changes continuously (a vehicle speeding up) the fitted zoom can drift, and one
  such stretch was seen with its distance about twice the true one. A mosaic built from a crowded,
  zoomed-out infantry minimap is the least accurate (errors around 3 pixels typical, up to 18).
- **No pose-graph optimisation.** A loop closes by matching stored features, not by spreading
  the correction over the loop.
- **Weapon classes do not work yet.** The icon's silhouette is taken from a translucent icon over
  a moving background, and it varies too much from sample to sample: the test recordings came out
  with 220 to 340 classes for 550 to 670 lines, where a match has a few dozen weapons. Treat
  `weapon` as experimental. Classes are per run in any case, and are not names.
- **The markers' meanings are not all known.** The arrow (`▸`) is drawn before the player's own
  name, in lines about them; it is not a kind of kill. The skull is taken to mean a headshot; that
  is an assumption, not something the game says. `chevrons` and `crosses` (squad wipes) are
  reported as seen.
- **Names in scripts other than Latin** (Cyrillic, for one) come out as the nearest Latin
  look-alike letters: the recogniser reads Latin and Chinese. The same player reads the same way
  each time, so they still match up, but the text is not their name.
- **Overlays in the kill feed's corner** (an fps counter) can hide the end of the top row's
  victim. Counter text is recognised and dropped, and a name cut short is matched to its full
  reads, but a name only ever seen cut short stays cut short.
- **A death not shown in the feed** (out of the feed's view, or in a mode without a feed) still
  ends the route, as `end`, when the player leaves play for 6 s or more.
- **Revives** are inferred: a feed death after which the player stays in play for over 40 s. A
  quick revive (under 40 s, then a death) is not told apart.
- **Assists are not read**: they are not in the kill feed.
- **The HUD layout is BF6's default at 16:9.** A changed HUD scale, a colour-blind palette or a
  different minimap size would need a profile of its own.
