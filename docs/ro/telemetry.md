---
title: "Înregistratoare de telemetrie"
nav_order: 3
lang: "ro"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Înregistratoare de telemetrie {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` înregistrează fiecare canal pe care îl trimite un joc, împarte fluxul în ture sau etape și scrie un fișier [`heat3d-lap`](lap-format.md) JSON pentru fiecare tură, într-un dosar. Fila Race a vizualizatorului citește aceste fișiere. Înregistrarea rulează până apăsați **Ctrl+C**; orice tură sau etapă deschisă în acel moment este scrisă dacă este suficient de lungă ca să fie păstrată (vezi [Cum se împart turele și etapele](lap-splitting.md)).

Cod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
și modulele din [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opțiuni {#options}

| Opțiune | Implicit | Înțeles |
|---|---|---|
| `--game` | `forza` | Unul dintre `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Dosarul în care se scriu fișierele de ture. Se creează dacă lipsește. Ignorată de `trackmania`, al cărui plugin scrie singur fișierele. |
| `--port` | `5300` | Portul UDP pe care se ascultă. **Pentru fiecare joc în afara Forza, valoarea 5300 înseamnă „portul implicit al jocului"**: 20777 pentru `wrc` și jocurile DiRT, 6776 pentru `rbr`, 4460 pentru `beamng`. Dați orice alt număr ca să-l suprascrieți. Nu este folosit de jocurile Assetto Corsa (memorie partajată) sau de Trackmania (fișiere). |
| `--forward` | niciunul | Doar Forza: `host:port` către care se trimite fiecare pachet primit, neschimbat. `127.0.0.1:5301` pentru FH Companion. Un simplu `:5301` înseamnă `127.0.0.1:5301`. |
| `--install` | oprit | `beamng`: copiază mai întâi modul de protocol în modurile dezarhivate ale BeamNG. `trackmania`: copiază pluginul Openplanet în dosarul de plugin-uri al Openplanet. Ignorată de celelalte jocuri. |
| `--configure` | niciunul | Doar `wrc`: calea către `config.json` de telemetrie al EA SPORTS WRC; pornește pachetul implicit `wrc` înainte de înregistrare (salvat întâi). |
| `--surface` | niciunul | Jocuri de raliu (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` sau `mixed`, scrise în `meta.surface` al fișierului de tură. Fără el nu se scrie nicio suprafață. |

## Jocurile pe scurt {#the-games-at-a-glance}

| `--game` | Joc | Sursă | Port implicit | Împărțire | `game` în fișier | Pagina |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (inclusiv 2023) | Data Out UDP | 5300 | contorul de ture al jocului (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, sau `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | memorie partajată `acpmf_*` | - | contorul de ture (`CounterSplitter`) | `assetto-corsa` | [Jocurile Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | memorie partajată `acpmf_*` | - | contorul de ture (`CounterSplitter`) | `assetto-corsa-competizione` | [Jocurile Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | memorie partajată `acevo_pmf_*` | - | linia de start (`LineSplitter`) | `assetto-corsa-evo` | [Jocurile Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | memorie partajată `acpmf_*` | - | linia de start / oprire (`LineSplitter`) | `assetto-corsa-rally` | [Jocurile Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, structura `wrc` | 20777 | ceasul de etapă (`StageSplitter`) | `ea-sports-wrc` | [Jocuri de raliu](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | ceasul de etapă (`StageSplitter`) | `dirt-rally-2` | [Jocuri de raliu](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | ceasul de etapă (`StageSplitter`) | `dirt-rally` | [Jocuri de raliu](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | ceasul de etapă (`StageSplitter`) | `dirt-4` | [Jocuri de raliu](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | UDP NGP | 6776 | ceasul de etapă (`StageSplitter`) | `richard-burns-rally` | [Jocuri de raliu](telemetry-rally.md) |
| `beamng` | BeamNG.drive | modul de protocol `heat3d`, UDP | 4460 | linia de start (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanet, fișiere CSV | - | pe rulare, în plugin | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | fișierele proprii `.ibt`, citite de vizualizator | - | contorul de ture al simulatorului | `iracing` | [iRacing](telemetry-iracing.md) |

## Stare {#status}

Înregistratorul Forza este cel mai mult exersat. Înregistratoarele Kunos, de raliu, BeamNG și Trackmania sunt construite după structurile publicate și testate pe pachete și pagini sintetice construite din aceste structuri (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **niciunul nu a fost încă rulat pe jocul live**. Înregistratoarele care își pot verifica intrarea o fac pe măsură ce sosesc pachetele și afișează un `note:` o dată când ceva nu se potrivește (EA WRC și DiRT compară viteza lumii cu viteza indicată; EA WRC raportează și un pachet mai scurt decât structura implicită de 237 de octeți). [Jocuri](games.md) listează sursele și ce nu este confirmat pe fiecare joc.

## În timpul rulării {#while-it-runs}

- **Forza** afișează o linie de stare pe secundă: pachetele primite și numărul turei deschise, numărul de eșantioane și metrii, sau `waiting for a race`. Fiecare tură terminată afișează `wrote <file>`.
- **Jocurile Assetto Corsa** afișează numele fiecărui fișier de tură pe măsură ce este scris.
- **Jocurile de raliu** afișează `listening for <game> on port <port>`, apoi `stage written: <file>`; la Ctrl+C, o etapă deschisă suficient de lungă pentru a fi păstrată este scrisă ca `partial stage written: <file>`.
- **BeamNG** afișează `lap written: <file>`, iar la Ctrl+C `run written: <file>`.
- **Trackmania** nu afișează nimic pe rulare: pluginul își scrie singur fișierele CSV.
- La final, fiecare înregistrator afișează câte fișiere a scris.

O înregistrare Forza, alimentată aici cu pachete Data Out sintetice ale unei mașini care conduce două ture pe un cerc de 150 m (fișierele de ture, fișierul brut de alături și rezumatul de autoverificare pe care îl lasă):

![înregistrare de telemetrie Forza cu două ture dintr-un flux sintetic](../assets/img/telemetry-run.svg)

## Nume de fișiere {#file-names}

| Înregistrator | Model |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Jocurile Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Jocurile de raliu, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, unde `<game>` este numele lung (`ea-sports-wrc`, `beamng`, ...), `stage` pentru raliu și `lap` pentru BeamNG |
| Pluginul Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` față de `run` (Forza, Assetto Corsa) și sufixul `_partial` (raliu, BeamNG) arată dacă tura sau etapa a fost terminată. Marca de timp este momentul în care a fost scris fișierul, nu când a început tura.

Alături de fișierele de ture, fiecare înregistrator scrie `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - fiecare pachet sau pagină care a sosit, păstrat întreg, și în meniuri și între ture - și `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, autoverificarea: pe tip de pachet, câte au venit, câte au intrat în fișierele de ture și `lost`, care este 0. Vizualizatorul le sare când se încarcă un dosar. Vezi [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) în README.

## Copiii acestei pagini {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Jocurile Assetto Corsa](telemetry-assetto-corsa.md)
- [Jocuri de raliu](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Cum se împart turele și etapele](lap-splitting.md)
- [Alunecare, derapaj și canale derivate](slip-and-drift.md)
- [Fișierul heat3d-lap](lap-format.md)
