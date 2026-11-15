---
title: Rejestratory telemetrii
nav_order: 3
lang: "pl"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Rejestratory telemetrii {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` nagrywa każdy kanał, jaki wysyła gra, dzieli strumień na okrążenia lub odcinki i zapisuje jeden plik [`heat3d-lap`](lap-format.md) w formacie JSON na okrążenie do folderu. Zakładka Analiza wyścigowa przeglądarki czyta te pliki. Nagrywanie trwa, aż naciśniesz **Ctrl+C**; okrążenie lub odcinek otwarte w tej chwili jest zapisywane, jeśli jest wystarczająco długie, by je zachować (zob. [Podział okrążeń i odcinków](lap-splitting.md)).

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
oraz moduły w [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opcje {#options}

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `--game` | `forza` | Jedna z: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Folder, do którego zapisywane są pliki okrążeń. Tworzony, gdy go brak. Ignorowane przez `trackmania`, której wtyczka zapisuje pliki sama. |
| `--port` | `5300` | Port UDP do nasłuchu. **Dla każdej gry poza Forzą wartość 5300 oznacza „domyślny port gry”**: 20777 dla `wrc` i gier DiRT, 6776 dla `rbr`, 4460 dla `beamng`. Podaj inną liczbę, by nadpisać. Nieużywane przez gry Assetto Corsa (pamięć współdzielona) ani Trackmanię (pliki). |
| `--forward` | brak | Tylko Forza: `host:port`, do którego przekazywany jest każdy otrzymany pakiet bez zmian. `127.0.0.1:5301` dla FH Companion. Sam `:5301` oznacza `127.0.0.1:5301`. |
| `--install` | wyłączone | `beamng`: najpierw kopiuje mod protokołu do rozpakowanych modów BeamNG. `trackmania`: kopiuje wtyczkę Openplanet do folderu wtyczek Openplanet. Ignorowane przez pozostałe gry. |
| `--configure` | brak | Tylko `wrc`: ścieżka do `config.json` telemetrii EA SPORTS WRC; włącza domyślny pakiet `wrc` przed nagrywaniem (najpierw robiona jest kopia zapasowa). |
| `--surface` | brak | Gry rajdowe (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` lub `mixed`, zapisywane w `meta.surface` pliku okrążenia. Bez tego nawierzchnia nie jest zapisywana. |

## Gry w skrócie {#the-games-at-a-glance}

| `--game` | Gra | Źródło | Domyślny port | Podział | `game` w pliku | Strona |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (w tym 2023) | Data Out UDP | 5300 | licznik okrążeń gry (`LapSplitter`) | `forza-horizon`, `forza-motorsport` lub `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | pamięć współdzielona `acpmf_*` | - | licznik okrążeń (`CounterSplitter`) | `assetto-corsa` | [Gry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | pamięć współdzielona `acpmf_*` | - | licznik okrążeń (`CounterSplitter`) | `assetto-corsa-competizione` | [Gry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | pamięć współdzielona `acevo_pmf_*` | - | linia startu (`LineSplitter`) | `assetto-corsa-evo` | [Gry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | pamięć współdzielona `acpmf_*` | - | linia startu / zatrzymanie (`LineSplitter`) | `assetto-corsa-rally` | [Gry Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struktura `wrc` | 20777 | zegar odcinka (`StageSplitter`) | `ea-sports-wrc` | [Gry rajdowe](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | zegar odcinka (`StageSplitter`) | `dirt-rally-2` | [Gry rajdowe](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | zegar odcinka (`StageSplitter`) | `dirt-rally` | [Gry rajdowe](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | zegar odcinka (`StageSplitter`) | `dirt-4` | [Gry rajdowe](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | zegar odcinka (`StageSplitter`) | `richard-burns-rally` | [Gry rajdowe](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod protokołu `heat3d`, UDP | 4460 | linia startu (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | wtyczka Openplanet, pliki CSV | - | przejazd, we wtyczce | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | jego własne pliki `.ibt`, czytane przez przeglądarkę | - | licznik okrążeń symulatora | `iracing` | [iRacing](telemetry-iracing.md) |

## Status {#status}

Rejestrator Forzy jest najczęściej sprawdzany. Rejestratory Kunos, rajdowe, BeamNG i Trackmanii są zbudowane według opublikowanych układów i testowane na syntetycznych pakietach i stronach zbudowanych z tych układów (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **żaden z nich nie był jeszcze uruchomiony na działającej grze**. Rejestratory, które potrafią sprawdzić swoje dane wejściowe, robią to w miarę nadchodzenia pakietów i raz wypisują `note:`, gdy coś się nie zgadza (EA WRC i DiRT porównują prędkość świata z prędkością; EA WRC zgłasza też pakiet krótszy niż 237-bajtowa domyślna struktura). [Gry](games.md) wymienia źródła i to, czego jeszcze nie potwierdzono, dla każdej gry.

## Podczas działania {#while-it-runs}

- **Forza** wypisuje linię statusu raz na sekundę: otrzymane pakiety oraz numer otwartego okrążenia, liczbę próbek i metry albo `waiting for a race`. Każde zakończone okrążenie wypisuje `wrote <file>`.
- **Gry Assetto Corsa** wypisują nazwę każdego pliku okrążenia, gdy jest zapisywany.
- **Gry rajdowe** wypisują `listening for <game> on port <port>`, a potem `stage written: <file>`; na Ctrl+C otwarty odcinek wystarczająco długi, by go zachować, jest zapisywany jako `partial stage written: <file>`.
- **BeamNG** wypisuje `lap written: <file>`, a na Ctrl+C `run written: <file>`.
- **Trackmania** nic nie wypisuje na przejazd: wtyczka zapisuje swoje pliki CSV sama.
- Na końcu każdy rejestrator wypisuje, ile plików zapisał.

Nagranie Forzy, tutaj zasilane syntetycznymi pakietami Data Out z jazdy dwóch okrążeń po kole o średnicy 150 m (pliki okrążeń, surowy plik pomocniczy i plik samokontroli, który zostawia):

![Nagranie telemetrii Forzy z dwóch okrążeń syntetycznego strumienia](../assets/img/telemetry-run.svg)

## Nazwy plików {#file-names}

| Rejestrator | Wzór |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Gry Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Gry rajdowe, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, gdzie `<game>` to długa nazwa (`ea-sports-wrc`, `beamng`, ...), `stage` dla rajdów, a `lap` dla BeamNG |
| Wtyczka Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` a `run` (Forza, Assetto Corsa) oraz przyrostek `_partial` (rajdy, BeamNG) pokazują, czy okrążenie lub odcinek zostało skończone. Znacznik czasu to moment zapisania pliku, a nie moment rozpoczęcia okrążenia.

Obok plików okrążeń każdy rejestrator zapisuje `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - każdy pakiet albo stronę, które nadeszły, w całości, także w menu i między okrążeniami - oraz `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, samokontrolę: dla każdego typu pakietu, ile przyszło, ile trafiło do plików okrążeń i `lost`, które wynosi 0. Przeglądarka pomija oba, gdy wczytuje folder. Zob. [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) w README.

## Podstrony {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Gry Assetto Corsa](telemetry-assetto-corsa.md)
- [Gry rajdowe](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Podział okrążeń i odcinków](lap-splitting.md)
- [Poślizg, dryf i kanały pochodne](slip-and-drift.md)
- [Plik heat3d-lap](lap-format.md)
