# Changelog

## 1.2.0

- The Assetto Corsa games (`--game ac`, `acc`, `acevo`) write one `heat3d-session` file per session: every lap
  and the runs between them, rewritten after each lap; `--per-lap` keeps one `heat3d-lap` file per lap.
- AC and ACC: the graphics page's position along the lap, sector, lap time so far, race position and pit flags
  are written per sample (`lapFraction`, `sector`, `lapTimeMs`, `racePosition`, `inPit`, `inPitLane`), ACC's
  valid-lap flag too (`lapValid`); the static page's track layout, track length, sector count, the car's skin,
  top rpm, fuel capacity and tyre radii go into the file.
- ACC and AC EVO: the other cars' positions from the graphics page's table of every car, 10 times a second,
  in the session file's `others`; written only when the table's entry for the player matches the player's own
  position.
- AC EVO: its own graphics page is read, after the published SharedFileOut.h layout (2026-04-28): laps close where
  the game's position along the lap passes the line, with the game's lap time; the track's layout and length
  and the car's model id are written.
- A lap the game counted but that was joined part-way round is written as a run, not a complete lap.
- Its own icon: the 3DHeat cube with a text badge for its game (letters in 3DHeat's colours), as the
  program, window, taskbar and docs icon.
- A new window: the 3DHeat look in dark and light (follows the system, switchable), the logo and
  icon, sharp at any display scaling. Four steps: find the game (each requirement with its fix),
  choose (maps ticked when there is something to do, filters, search; jobs with their fields
  inline), work (progress, time left, cancel), done (open in 3DHeat, open the output folder, and
  for a failure what went wrong and what to do, copy details, report a problem).
- No console window on Windows: the program is a window program. From a terminal it still prints
  as before; `heat3d-gamecapture-cli.cmd` beside it waits for it in a terminal and passes its exit code.
- The update offer in the same look: Update now / Later / Skip this version, and "Update
  automatically" from the dialog.
- CI draws every page and dialog of the window (on Linux under a virtual display) and checks the
  Windows build is a window program.
- Recording runs until you press Stop, with a pulsing record mark, the time it has run and the
  last lap line; the game is picked from a list (no typing of short names).

## 1.1.0

- A standalone lap recorder for Windows, Linux and macOS (no Python needed), built by CI with a `SHA256SUMS`
  file. Without arguments it opens a window that starts and stops the recorder for a game (Forza, the Assetto
  Corsa games, EA WRC / DiRT / RBR, BeamNG.drive), converts a course from an FH Companion lap library, and
  checks for updates. `heat3d-gamecapture <command>` runs the tool's commands unchanged; `--check --json` for
  scripts. The scanner and the offline reconstruction stay with a source install.
- A `pyproject.toml` with the recorders' own needs (numpy, pyarrow) and the `heat3d-capture` command;
  `heat3d_capture.__version__` is set. Tests that need a library only the scanner or the reconstruction uses
  skip where it is not installed.
- Updates ask first (update now / later / skip this version) unless automatic updates were chosen
  (`--auto-update`, the window's checkbox, or `HEAT3D_AUTO_UPDATE=1`); `heat3d_update.startup` asks through the
  same code.

## 1.0.4

- The depth estimator answers an empty batch with nothing before it needs PyTorch, so the test
  suite passes on an install without it.

## 1.0.3

- `locate`: where each frame of the player's own recording was taken, against renders of the level
  (experimental).
- Completeness self-check and raw sidecars: every recorder keeps every packet whole.
- Scan `.glb` files say their unit (`extras.unit_metres: 0.01`), so `locate` reads a scan at its
  true size instead of 100 times too big.
- Documentation: Before you start, generated command reference, maintaining checklist.
- README: a quick start for new users.

## 1.0.2

- `hud`: the player's own actions, deaths, minimap track and kill feed from a recording.
- The documentation site.

## 1.0.1

- Updates: each tool remembers its own release check.

## 1.0.0

- GameCapture on its own: lap telemetry recorders, level reconstruction, licence, updates.

## Docs

Where each feature is documented (pages under [docs/](docs/), published at
[holdi601.github.io/3DHeat-GameCapture](https://holdi601.github.io/3DHeat-GameCapture/)):

| Feature | Page |
|---|---|
| First steps: Python, a terminal, the first command | [before-you-start.md](docs/before-you-start.md) |
| Every command and option, every output column (generated) | [cli-reference.md](docs/cli-reference.md) |
| Commands, step by step | [commands.md](docs/commands.md) |
| `telemetry`: lap files from every game | [telemetry.md](docs/telemetry.md) and the `telemetry-*.md` pages |
| The `heat3d-lap` file | [lap-format.md](docs/lap-format.md) |
| Lap and stage splitting | [lap-splitting.md](docs/lap-splitting.md) |
| Slip and derived channels | [slip-and-drift.md](docs/slip-and-drift.md) |
| Completeness self-check, raw sidecars | [telemetry.md](docs/telemetry.md) |
| `route`, `laps` | [commands.md](docs/commands.md), [games.md](docs/games.md) |
| The scan window | [reconstruction-scan-ui.md](docs/reconstruction-scan-ui.md) |
| Level reconstruction | [reconstruction.md](docs/reconstruction.md) and the `reconstruction-*.md` pages |
| `reconstruct` (offline) | [reconstruction-offline.md](docs/reconstruction-offline.md) |
| The `.glb` output, its unit | [glb-output.md](docs/glb-output.md) |
| `hud` | [hud-video.md](docs/hud-video.md) |
| `locate` | [locate.md](docs/locate.md) |
| Updates | [updates.md](docs/updates.md) |
| Releasing, keeping the docs current | [maintaining.md](docs/maintaining.md) |
