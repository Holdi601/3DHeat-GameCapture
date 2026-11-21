# Changelog

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
