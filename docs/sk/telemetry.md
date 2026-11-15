---
title: "Telemetrické nahrávače"
nav_order: 3
lang: "sk"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetrické nahrávače {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` zaznamenáva každý kanál, ktorý hra posiela, rozdelí prúd na kolá
alebo etapy a zapíše jeden [`heat3d-lap`](lap-format.md) JSON súbor na kolo do
priečinka. Karta Analýza pretekov v prehliadači číta tieto súbory. Nahrávanie
beží, kým nestlačíte **Ctrl+C**; kolo alebo etapa, ktorá je v tom momente
otvorená, sa zapíše, ak je dosť dlhá na uchovanie (pozrite
[Delenie kôl a etáp](lap-splitting.md)).

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
a moduly v [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Voľby {#options}

| Voľba | Predvolené | Význam |
|---|---|---|
| `--game` | `forza` | Jedna z hodnôt `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Priečinok, do ktorého sa zapisujú súbory kôl. Vytvorí sa, ak chýba. Ignoruje ho `trackmania`, ktorého plugin zapisuje súbory sám. |
| `--port` | `5300` | UDP port na počúvanie. **Pre každú hru okrem Forzy hodnota 5300 znamená „predvolený port hry“**: 20777 pre `wrc` a hry DiRT, 6776 pre `rbr`, 4460 pre `beamng`. Zadajte iné číslo na prepísanie. Nepoužíva sa pre hry Assetto Corsa (zdieľaná pamäť) ani Trackmania (súbory). |
| `--forward` | žiadne | Len Forza: `host:port`, kam sa posiela každý prijatý paket nezmenený. `127.0.0.1:5301` pre FH Companion. Samotné `:5301` znamená `127.0.0.1:5301`. |
| `--install` | vypnuté | `beamng`: najprv skopíruje mod protokolu do rozbalených modov BeamNG. `trackmania`: skopíruje plugin Openplanet do priečinka pluginov Openplanet. Ostatné hry ho ignorujú. |
| `--configure` | žiadne | Len `wrc`: cesta k `config.json` telemetrie EA SPORTS WRC; zapne predvolený paket `wrc` pred nahrávaním (najprv sa zálohuje). |
| `--surface` | žiadne | Rally hry (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` alebo `mixed`, zapísané do `meta.surface` súboru kola. Bez neho sa žiadny povrch nezapíše. |

## Hry na prvý pohľad {#the-games-at-a-glance}

| `--game` | Hra | Zdroj | Predvolený port | Delenie | `game` v súbore | Stránka |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (vrátane 2023) | Data Out UDP | 5300 | počítadlo kôl hry (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, alebo `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | zdieľaná pamäť `acpmf_*` | - | počítadlo kôl (`CounterSplitter`) | `assetto-corsa` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | zdieľaná pamäť `acpmf_*` | - | počítadlo kôl (`CounterSplitter`) | `assetto-corsa-competizione` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | zdieľaná pamäť `acevo_pmf_*` | - | štartovacia čiara (`LineSplitter`) | `assetto-corsa-evo` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | zdieľaná pamäť `acpmf_*` | - | štartovacia čiara / zastavenie (`LineSplitter`) | `assetto-corsa-rally` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, štruktúra `wrc` | 20777 | hodiny etapy (`StageSplitter`) | `ea-sports-wrc` | [Rallye hry](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-rally-2` | [Rallye hry](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-rally` | [Rallye hry](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-4` | [Rallye hry](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | hodiny etapy (`StageSplitter`) | `richard-burns-rally` | [Rallye hry](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod protokolu `heat3d`, UDP | 4460 | štartovacia čiara (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanet, súbory CSV | - | jazda, v plugine | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | jeho vlastné súbory `.ibt`, čítané prehliadačom | - | počítadlo kôl simulátora | `iracing` | [iRacing](telemetry-iracing.md) |

## Stav {#status}

Nahrávač Forzy je ten, ktorý sa používal najviac. Nahrávače Kunos, rally,
BeamNG a Trackmania sú postavené podľa zverejnených rozložení a testované na
syntetických paketoch a stránkach zostavených podľa týchto rozložení
(`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **žiadny
z nich sa zatiaľ nespustil proti živej hre**. Nahrávače, ktoré dokážu skontrolovať
vstup, to robia pri príchode paketov a raz vypíšu `note:`, keď niečo nesedí
(EA WRC a DiRT porovnávajú rýchlosť sveta s rýchlosťou; EA WRC tiež hlási paket
kratší ako 237-bajtová predvolená štruktúra). [Hry](games.md) uvádzajú zdroje
a to, čo ešte nie je potvrdené, pre každú hru.

## Počas behu {#while-it-runs}

- **Forza** vypisuje raz za sekundu stavový riadok: prijaté pakety a číslo
  otvoreného kola, počet vzoriek a metre, alebo `waiting for a race`. Každé
  dokončené kolo vypíše `wrote <file>`.
- **Hry Assetto Corsa** vypisujú názov každého súboru kola pri jeho zápise.
- **Rally hry** vypisujú `listening for <game> on port <port>`, potom `stage written: <file>`;
  pri Ctrl+C sa otvorená etapa, ktorá je dosť dlhá na uchovanie, zapíše ako `partial stage written: <file>`.
- **BeamNG** vypisuje `lap written: <file>`, a pri Ctrl+C `run written: <file>`.
- **Trackmania** nevypisuje nič pre každú jazdu: plugin zapisuje svoje súbory CSV sám.
- Na konci každý nahrávač vypíše, koľko súborov zapísal.

Záznam Forzy, tu napájaný syntetickými paketmi Data Out z jazdy dvoch kôl
okolo kruhu s dĺžkou 150 m (súbory kôl, surový pomocný súbor a súhrn samokontroly,
ktorý zanechá):

![Telemetrický záznam dvoch kôl zo syntetického kanála Forzy](../assets/img/telemetry-run.svg)

## Názvy súborov {#file-names}

| Nahrávač | Vzor |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Hry Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rally hry, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, kde `<game>` je dlhý názov (`ea-sports-wrc`, `beamng`, ...), `stage` pre rally a `lap` pre BeamNG |
| Plugin Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` oproti `run` (Forza, Assetto Corsa) a prípona `_partial` (rally, BeamNG)
označujú, či bolo kolo alebo etapa dokončené. Časová pečiatka je čas zápisu
súboru, nie čas začiatku kola.

Vedľa súborov kôl každý nahrávač zapisuje `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` –
každý paket alebo stránku, ktoré prišli, celé, aj v menu a medzi kolami – a
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, samokontrolu: pre každý typ paketu,
koľko prišlo, koľko sa dostalo do súborov kôl, a `lost`, ktoré je 0. Prehliadač
ich pri načítaní priečinka preskočí. Pozrite [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness)
v README.

## Podstránky tejto stránky {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Hry Assetto Corsa](telemetry-assetto-corsa.md)
- [Rallye hry](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Delenie kôl a etáp](lap-splitting.md)
- [Prešmyk, drift a odvodené kanály](slip-and-drift.md)
- [Súbor heat3d-lap](lap-format.md)
