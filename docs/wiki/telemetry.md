
# Telemetry recorders

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` records every channel a game sends, splits the stream into laps or stages, and
writes one [`heat3d-lap`](lap-format) JSON file per lap into a folder. The viewer's Race
tab reads those files. Recording runs until you press **Ctrl+C**; whatever lap or stage is
open at that moment is written if it is long enough to keep (see
[Lap and stage splitting](lap-splitting)).

Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
and the modules in [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Options

| Option | Default | Meaning |
|---|---|---|
| `--game` | `forza` | One of `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Folder the lap files are written into. Created if missing. Ignored by `trackmania`, whose plugin writes the files itself. |
| `--port` | `5300` | UDP port to listen on. **For every game except Forza the value 5300 means "the game's own default"**: 20777 for `wrc` and the DiRT games, 6776 for `rbr`, 4460 for `beamng`. Give any other number to override. Not used by the Assetto Corsa games (shared memory) or Trackmania (files). |
| `--forward` | none | Forza only: `host:port` to pass every received packet on to, unchanged. `127.0.0.1:5301` for FH Companion. A bare `:5301` means `127.0.0.1:5301`. |
| `--install` | off | `beamng`: copy the protocol mod into BeamNG's unpacked mods first. `trackmania`: copy the Openplanet plugin into Openplanet's plugin folder. Ignored by the other games. |
| `--configure` | none | `wrc` only: path to EA SPORTS WRC's telemetry `config.json`; switches the default `wrc` packet on before recording (backed up first). |
| `--surface` | none | Rally games (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` or `mixed`, written to the lap file's `meta.surface`. Without it no surface is written. |

## The games at a glance

| `--game` | Game | Source | Default port | Splitting | `game` in the file | Page |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (incl. 2023) | Data Out UDP | 5300 | the game's lap counter (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, or `forza` | [Forza](telemetry-forza) |
| `ac` | Assetto Corsa | shared memory `acpmf_*` | - | lap counter (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa games](telemetry-assetto-corsa) |
| `acc` | Assetto Corsa Competizione | shared memory `acpmf_*` | - | lap counter (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa games](telemetry-assetto-corsa) |
| `acevo` | Assetto Corsa EVO | shared memory `acevo_pmf_*` | - | start line (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa games](telemetry-assetto-corsa) |
| `acrally` | Assetto Corsa Rally | shared memory `acpmf_*` | - | start line / stop (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa games](telemetry-assetto-corsa) |
| `wrc` | EA SPORTS WRC | UDP, `wrc` structure | 20777 | stage clock (`StageSplitter`) | `ea-sports-wrc` | [Rally games](telemetry-rally) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | stage clock (`StageSplitter`) | `dirt-rally-2` | [Rally games](telemetry-rally) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | stage clock (`StageSplitter`) | `dirt-rally` | [Rally games](telemetry-rally) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | stage clock (`StageSplitter`) | `dirt-4` | [Rally games](telemetry-rally) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | stage clock (`StageSplitter`) | `richard-burns-rally` | [Rally games](telemetry-rally) |
| `beamng` | BeamNG.drive | `heat3d` protocol mod, UDP | 4460 | start line (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng) |
| `trackmania` | Trackmania (2020) | Openplanet plugin, CSV files | - | per run, in the plugin | `trackmania` | [Trackmania](telemetry-trackmania) |
| - | iRacing | its own `.ibt` files, read by the viewer | - | the sim's lap counter | `iracing` | [iRacing](telemetry-iracing) |

## Status

The Forza recorder is the one exercised the most. The Kunos, rally, BeamNG and Trackmania
recorders are built against the published layouts and tested on synthetic packets and
pages built from those layouts (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`); **none of them has yet been run against the live game**. The
recorders that can check their input do so as packets arrive and print a `note:` once when
something does not match (EA WRC and DiRT compare the world velocity against the speed;
EA WRC also reports a packet shorter than the 237-byte default structure). [Games](games) lists the sources
and what is not yet confirmed per game.

## While it runs

- **Forza** prints a status line once a second: packets received, and the open lap's number,
  sample count and metres, or `waiting for a race`. Each finished lap prints `wrote <file>`.
- **Assetto Corsa games** print the name of each lap file as it is written.
- **Rally games** print `listening for <game> on port <port>`, then `stage written: <file>`;
  on Ctrl+C an open stage long enough to keep is written as `partial stage written: <file>`.
- **BeamNG** prints `lap written: <file>`, and on Ctrl+C `run written: <file>`.
- At the end every recorder prints how many files it wrote.

## File names

| Recorder | Pattern |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa games | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rally games, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, where `<game>` is the long name (`ea-sports-wrc`, `beamng`, ...), `stage` for rally and `lap` for BeamNG |
| Trackmania plugin | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` against `run` (Forza, Assetto Corsa) and the `_partial` suffix (rally, BeamNG) mark
whether the lap or stage was finished. The time stamp is when the file was written, not
when the lap began.

## Children of this page

- [Forza](telemetry-forza)
- [Assetto Corsa games](telemetry-assetto-corsa)
- [Rally games](telemetry-rally)
- [BeamNG.drive](telemetry-beamng)
- [Trackmania](telemetry-trackmania)
- [iRacing](telemetry-iracing)
- [Lap and stage splitting](lap-splitting)
- [Slip, drift and derived channels](slip-and-drift)
- [The heat3d-lap file](lap-format)
