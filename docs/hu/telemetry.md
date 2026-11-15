---
title: "Telemetriai rögzítők"
nav_order: 3
lang: "hu"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetriai rögzítők {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

A `telemetry` minden csatornát rögzít, amelyet egy játék küld, a folyamot körökre vagy szakaszokra darabolja, és egy [`heat3d-lap`](lap-format.md) JSON-fájlt ír körönként egy mappába. A nézegető Versenyelemzés fülön olvassa ezeket a fájlokat. A rögzítés addig fut, amíg meg nem nyomod a **Ctrl+C**-t; az a kör vagy szakasz, amely éppen nyitva van, kiíródik, ha elég hosszú ahhoz, hogy megmaradjon (lásd [Kör- és szakaszdarabolás](lap-splitting.md)).

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
és a modulok a [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry) mappában.

## Opciók {#options}

| Opció | Alapértelmezés | Jelentése |
|---|---|---|
| `--game` | `forza` | Az egyik: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Az a mappa, amelybe a körfájlok íródnak. Ha nincs, létrejön. A `trackmania` figyelmen kívül hagyja, mert a bővítménye maga írja a fájlokat. |
| `--port` | `5300` | Az UDP-port, amelyen hallgatunk. **A Forza kivételével minden játéknál az 5300 azt jelenti: „a játék saját alapértelmezett portja”**: 20777 a `wrc`-nél és a DiRT-játékoknál, 6776 az `rbr`-nél, 4460 a `beamng`-nél. Más számmal felülírható. Az Assetto Corsa-játékoknál (megosztott memória) és a Trackmaniánál (fájlok) nem használt. |
| `--forward` | nincs | Csak Forza: `host:port`, ahová minden fogadott csomagot változatlanul továbbít. `127.0.0.1:5301` az FH Companionhoz. A puszta `:5301` jelentése `127.0.0.1:5301`. |
| `--install` | ki | `beamng`: először a protokollmodot másolja a kicsomagolt BeamNG-modok közé. `trackmania`: az Openplanet bővítményét másolja az Openplanet bővítménymappájába. A többi játék figyelmen kívül hagyja. |
| `--configure` | nincs | Csak `wrc`: az EA SPORTS WRC telemetria `config.json` fájljának elérési útja; az alapértelmezett `wrc` csomagot bekapcsolja a rögzítés előtt (előbb biztonsági mentés készül). |
| `--surface` | nincs | Ralijátékok (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` vagy `mixed`, a körfájl `meta.surface` mezőjébe írva. Nélküle nem íródik felület. |

## A játékok áttekintése {#the-games-at-a-glance}

| `--game` | Játék | Forrás | Alapértelmezett port | Darabolás | `game` a fájlban | Oldal |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (a 2023-as is) | Data Out UDP | 5300 | a játék köridő-számlálója (`LapSplitter`) | `forza-horizon`, `forza-motorsport` vagy `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | megosztott memória `acpmf_*` | - | köridő-számláló (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa játékok](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | megosztott memória `acpmf_*` | - | köridő-számláló (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa játékok](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | megosztott memória `acevo_pmf_*` | - | rajtvonal (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa játékok](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | megosztott memória `acpmf_*` | - | rajtvonal / megállás (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa játékok](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc` struktúra | 20777 | szakaszóra (`StageSplitter`) | `ea-sports-wrc` | [Ralijátékok](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | szakaszóra (`StageSplitter`) | `dirt-rally-2` | [Ralijátékok](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | szakaszóra (`StageSplitter`) | `dirt-rally` | [Ralijátékok](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | szakaszóra (`StageSplitter`) | `dirt-4` | [Ralijátékok](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | szakaszóra (`StageSplitter`) | `richard-burns-rally` | [Ralijátékok](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d` protokollmod, UDP | 4460 | rajtvonal (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-bővítmény, CSV-fájlok | - | futásonként, a bővítményben | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | saját `.ibt` fájljai, a nézegető olvassa | - | a szimulátor köridő-számlálója | `iracing` | [iRacing](telemetry-iracing.md) |

## Állapot {#status}

A Forza-rögzítő a legtöbbet használt. A Kunos-, rali-, BeamNG- és Trackmania-rögzítőket a közzétett elrendezésekre építették, és szintetikus csomagokon és a belőlük épített oldalakon tesztelték (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **egyiket sem futtatták még az élő játékon**. Azok a rögzítők, amelyek ellenőrizni tudják a bemenetüket, ezt a csomagok érkezése közben teszik, és egyszer `note:` figyelmeztetést írnak, ha valami nem stimmel (az EA WRC és a DiRT összeveti a világsebességet a sebességgel; az EA WRC jelzi azt is, ha a csomag rövidebb a 237 bájtos alapértelmezett struktúránál). A [Játékok](games.md) felsorolja a forrásokat és játékonként azt, ami még nincs megerősítve.

## Futás közben {#while-it-runs}

- A **Forza** másodpercenként egy állapotsort ír: hány csomag érkezett, és a nyitott kör száma, mintaszáma és métere, vagy `waiting for a race` (várakozás versenyre). Minden befejezett kör kiírja: `wrote <file>`.
- Az **Assetto Corsa-játékok** minden kör fájlnevét kiírják, ahogy íródik.
- A **ralijátékok** kiírják: `listening for <game> on port <port>`, majd `stage written: <file>`; Ctrl+C-nél a nyitott, elég hosszú szakasz mint `partial stage written: <file>` íródik ki.
- A **BeamNG** kiírja: `lap written: <file>`, Ctrl+C-nél pedig `run written: <file>`.
- A **Trackmania** futásonként semmit nem ír: a bővítménye maga írja a CSV-fájlokat.
- A végén minden rögzítő kiírja, hány fájlt írt.

Egy Forza-rögzítés, amelyet két kört futó, 150 m-es kör szintetikus Data Out csomagjaival tápláltak (a körfájlok, a nyers mellékfájl és az önellenőrző összefoglaló, amelyet hagy maga után):

![Telemetriarögzítés, amely két kört rögzít egy szintetikus Forza-feedből](../assets/img/telemetry-run.svg)

## Fájlnevek {#file-names}

| Rögzítő | Minta |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa-játékok | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Ralijátékok, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, ahol a `<game>` a hosszú név (`ea-sports-wrc`, `beamng`, ...), a `stage` a ralinál, a `lap` a BeamNG-nél |
| Trackmania-bővítmény | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

A `lap` és a `run` (Forza, Assetto Corsa) és a `_partial` utótag (rali, BeamNG) jelzi, hogy a kör vagy szakasz be lett-e fejezve. Az időbélyeg azt az időpontot mutatja, amikor a fájl íródott, nem azt, amikor a kör kezdődött.

A körfájlok mellett minden rögzítő ír egy `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` fájlt – minden csomagot vagy oldalt, amely érkezett, teljes egészében, a menükben és a körök között is –, és egy `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json` fájlt, az önellenőrzést: csomagtípusonként, hány érkezett, hány került körfájlba, és a `lost` (elveszett), amely 0. A nézegető kihagyja mindkettőt, amikor egy mappát betölt. Lásd a README [Teljesség](https://github.com/Holdi601/3DHeat-GameCapture#completeness) szakaszát.

## Ennek az oldalnak az alszakaszai {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa játékok](telemetry-assetto-corsa.md)
- [Ralijátékok](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Kör- és szakaszdarabolás](lap-splitting.md)
- [Csúszás, driftszög és származtatott csatornák](slip-and-drift.md)
- [A heat3d-lap fájl](lap-format.md)
