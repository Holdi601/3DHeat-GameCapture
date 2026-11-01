---
title: The rules
nav_order: 2
---

# The rules this is built under

Every part of 3DHeat GameCapture follows the same constraints. They are design decisions,
not disclaimers, and several of them cost accuracy on purpose.

## Nothing is injected, nothing is hooked

No part of this attaches to a game process, reads its memory, or touches its graphics API.

- **Frames** come from Windows Graphics Capture, the public API screen recorders use
  (through the `windows-capture` package), or from a video file. See
  [Capture, masks and frame quality](reconstruction-capture.md).
- **Telemetry** comes only from interfaces the games publish for it:
  - Forza's Data Out UDP feed, switched on in the game's settings;
  - the named shared-memory pages Kunos games publish for apps (`Local\acpmf_physics` and
    friends). They are opened read-only with `mmap`; this is the documented way apps read
    them, not memory reading of the game process;
  - the UDP telemetry EA SPORTS WRC, the DiRT games and Richard Burns Rally (through the
    RSF/NGP plugin) send when switched on in their own settings files;
  - BeamNG's protocol interface, through a small Lua "protocol" mod that the game's own
    `lua/vehicle/protocols.lua` loads and sends;
  - Trackmania's Openplanet plugin interface, through a plugin that only reads what
    Openplanet exposes and writes files;
  - iRacing's own `.ibt` telemetry files.

## Why it matters

The game knows the depth of every pixel exactly, and a hooked depth buffer would make level
reconstruction near-perfect and trivial. It would also mean injecting into processes that
may be protected by anti-cheat, which risks the account of anyone who runs it. So depth is
*estimated* from the picture instead ([Depth](reconstruction-depth.md)), and much of the
reconstruction pipeline exists to recover as much of that lost accuracy as possible from
sources that are free to use: telemetry poses where a game publishes them, a ground-plane
scale where it does not, and masks that keep the HUD and the cockpit out of the solve.

ReShade's depth buffer was considered and not used. ReShade disables depth access in
multiplayer sessions by design, so it would help single-player titles only (see
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Things the tool changes on your machine, and only when asked

| Action | When | What exactly |
|---|---|---|
| Installs Python packages | the scan window's first run, after a dialog and a yes | `pip install` into the interpreter running the tool - with `scan.bat`, the private `.venv` next to it. Never system-wide by itself. |
| Converts the depth model | "Set up the depth model" button, after a second dialog for PyTorch and friends | writes `models/depth-small-518.onnx` |
| Edits EA SPORTS WRC's `config.json` | `telemetry --game wrc --configure <file>` | switches the `wrc` / `session_update` packet on to 127.0.0.1; the old file is kept as `config.json.bak` |
| Copies the BeamNG mod | `telemetry --game beamng --install` | `mods/beamng/heat3d` to `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (replacing an older copy) |
| Copies the Trackmania plugin | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` to `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (replacing an older copy) |
| Registers global hotkeys | while the scan window is open (Windows) | Ctrl+Alt+F9 / F10 / F11, released when the window closes |
| Updates the tool | after you answer yes to the update prompt, or run `python -m heat3d_update` | see [Updates](updates.md) |

The DiRT games' `hardware_settings_config.xml` and Richard Burns Rally's
`RichardBurnsRally.ini` are **not** edited by the tool; you switch their UDP output on
yourself (see [Rally games](telemetry-rally.md)).

## What stays the user's responsibility

What a user points the tools at remains subject to that game's licence and EULA. Lap files,
recordings, reconstructions and exported courses belong to whoever owns the game and the
data; the repository's `.gitignore` keeps recordings, lap files, meshes, model weights and
video out of version control by folder and by file type.
