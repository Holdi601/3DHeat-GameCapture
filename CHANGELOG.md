# Changelog

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
