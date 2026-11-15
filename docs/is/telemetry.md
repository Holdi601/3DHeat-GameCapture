---
title: "Mælingagagna-upptökutæki"
nav_order: 3
lang: "is"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Mælingagagna-upptökutæki {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` skráir hverja rás sem leikur sendir, skiptir straumnum í hringi eða leiðir, og
skrifar eina [`heat3d-lap`](lap-format.md) JSON skrá á hring í möppu. Flipinn Kappakstursgreining í áhorfandanum
les þessar skrár. Upptakan keyrir þar til þú ýtir á **Ctrl+C**; hringur eða leið sem
er opin á þeirri stundu er skrifuð ef hún er nógu löng til að geyma (sjá
[Hring- og leiðaskipting](lap-splitting.md)).

Kóði: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
og einingarnar í [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Valkostir {#options}

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `--game` | `forza` | Eitt af `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mappan sem hringskrárnar eru skrifaðar í. Búin til ef hún vantar. Hunsað af `trackmania`, þar sem viðbótin skrifar skrárnar sjálf. |
| `--port` | `5300` | UDP gátt til að hlusta á. **Fyrir alla leiki nema Forza þýðir gildið 5300 „sjálfgefin gátt leiksins“**: 20777 fyrir `wrc` og DiRT leikina, 6776 fyrir `rbr`, 4460 fyrir `beamng`. Gefðu hvaða aðra tölu sem er til að yfirskrifa. Ekki notað af Assetto Corsa leikjunum (sameiginlegt minni) eða Trackmania (skrár). |
| `--forward` | engin | Aðeins Forza: `host:port` til að senda hvern mótteknan pakka áfram á, óbreyttan. `127.0.0.1:5301` fyrir FH Companion. Eintómt `:5301` þýðir `127.0.0.1:5301`. |
| `--install` | af | `beamng`: afritar samskiptareglu-módið fyrst í óuppþjöppuð mót BeamNG. `trackmania`: afritar Openplanet viðbótina í viðbótamöppu Openplanet. Hunsað af hinum leikjunum. |
| `--configure` | engin | Aðeins `wrc`: slóð að telemetry `config.json` EA SPORTS WRC; kveikir á sjálfgefna `wrc` pakkanum áður en upptaka hefst (afritað fyrst). |
| `--surface` | engin | Ralllíleikir (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` eða `mixed`, skrifað í `meta.surface` hringskrárinnar. Án þess er ekkert undirlag skrifað. |

## Leikirnir í hnotskurn {#the-games-at-a-glance}

| `--game` | Leikur | Uppspretta | Sjálfgefin gátt | Skipting | `game` í skránni | Síða |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (líka 2023) | Data Out UDP | 5300 | hringateljari leiksins (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, eða `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | sameiginlegt minni `acpmf_*` | - | hringateljari (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa leikir](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | sameiginlegt minni `acpmf_*` | - | hringateljari (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa leikir](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | sameiginlegt minni `acevo_pmf_*` | - | ráslína (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa leikir](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | sameiginlegt minni `acpmf_*` | - | ráslína / stopp (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa leikir](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc` bygging | 20777 | leiðarklukka (`StageSplitter`) | `ea-sports-wrc` | [Ralllíleikir](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | leiðarklukka (`StageSplitter`) | `dirt-rally-2` | [Ralllíleikir](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | leiðarklukka (`StageSplitter`) | `dirt-rally` | [Ralllíleikir](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | leiðarklukka (`StageSplitter`) | `dirt-4` | [Ralllíleikir](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | leiðarklukka (`StageSplitter`) | `richard-burns-rally` | [Ralllíleikir](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d` samskiptareglu-mód, UDP | 4460 | ráslína (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet viðbót, CSV skrár | - | á hverja ferð, í viðbótinni | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | eigin `.ibt` skrár, lesnar af áhorfandanum | - | hringateljari hermisins | `iracing` | [iRacing](telemetry-iracing.md) |

## Staða {#status}

Forza upptökutækið er það sem er mest reynt. Upptökutæki Kunos, ralllíleikja, BeamNG og Trackmania
eru smíðuð eftir útgefnum uppsetningum og prófuð á gervipökkum og
blöðum smíðuðum eftir þeim uppsetningum (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`); **ekkert þeirra hefur enn verið keyrt gegn raunverulegum leik**. Þau
upptökutæki sem geta athugað inntak sitt gera það jafnóðum og pakkar berast og prenta `note:` einu sinni þegar
eitthvað stemmir ekki (EA WRC og DiRT bera heimshraðann saman við hraðamælinn;
EA WRC tilkynnir líka pakka styttri en 237 bæta sjálfgefnu bygginguna). [Leikir](games.md) telur upp heimildir
og hvað er ekki enn staðfest fyrir hvern leik.

## Meðan það keyrir {#while-it-runs}

- **Forza** prentar stöðulínu einu sinni á sekúndu: pakkar mótteknir, og númer opna hringsins, fjöldi sýna
  og metrar, eða `waiting for a race`. Hver kláraður hringur prentar `wrote <file>`.
- **Assetto Corsa leikir** prenta heiti hverrar hringskrár þegar hún er skrifuð.
- **Ralllíleikir** prenta `listening for <game> on port <port>`, svo `stage written: <file>`;
  við Ctrl+C er opin leið nógu löng til að geyma skrifuð sem `partial stage written: <file>`.
- **BeamNG** prentar `lap written: <file>`, og við Ctrl+C `run written: <file>`.
- **Trackmania** prentar ekkert á ferð: viðbótin skrifar CSV skrárnar sjálf.
- Í lokin prentar hvert upptökutæki hversu margar skrár það skrifaði.

Forza upptaka, hér mötuð með gervi Data Out pökkum af bíl sem ekur tvo hringi á
150 m hring (hringskrárnar, hráa hliðarskráin og sjálfsprófssamantektin sem það skilur eftir):

![telemetry upptaka á tveimur hringjum úr gervi Forza straumi](../assets/img/telemetry-run.svg)

## Skráarheiti {#file-names}

| Upptökutæki | Mynstur |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa leikir | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Ralllíleikir, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, þar sem `<game>` er langa heitið (`ea-sports-wrc`, `beamng`, ...), `stage` fyrir ralllí og `lap` fyrir BeamNG |
| Trackmania viðbót | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` á móti `run` (Forza, Assetto Corsa) og viðskeytið `_partial` (ralllí, BeamNG) sýna
hvort hringurinn eða leiðin var kláruð. Tímastimpillinn er þegar skráin var skrifuð, ekki
þegar hringurinn hófst.

Við hlið hringskránna skrifar hvert upptökutæki `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - hver
pakki eða blað sem barst, geymt heilt, líka í valmyndum og milli hringja - og
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, sjálfsprófið: fyrir hverja pakkategund hversu margir komu, hversu
margir fóru í hringskrár, og `lost`, sem er 0. Áhorfandinn sleppir hvoru tveggja þegar mappa er hlaðin.
Sjá [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) í README.

## Undirsíður þessarar síðu {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa leikir](telemetry-assetto-corsa.md)
- [Ralllíleikir](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Hring- og leiðaskipting](lap-splitting.md)
- [Skrið, rek og afleiddar rásir](slip-and-drift.md)
- [heat3d-lap skráin](lap-format.md)
