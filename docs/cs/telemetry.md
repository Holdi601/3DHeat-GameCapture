---
title: "Záznamníky telemetrie"
nav_order: 3
lang: "cs"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Záznamníky telemetrie {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` nahrává každý kanál, který hra posílá, rozdělí proud na kola nebo etapy a do složky
zapíše jeden soubor [`heat3d-lap`](lap-format.md) JSON na kolo. Karta Analýza závodu v prohlížeči
tyto soubory čte. Nahrávání běží, dokud nestisknete **Ctrl+C**; kolo nebo etapa, která je v tu
chvíli otevřená, se zapíše, pokud je dost dlouhá, aby se zachovala (viz
[Jak se rozdělují kola a etapy](lap-splitting.md)).

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
a moduly v [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Volby {#options}

| Volba | Výchozí | Význam |
|---|---|---|
| `--game` | `forza` | Jedna z hodnot `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Složka, do které se zapisují soubory kol. Vytvoří se, pokud chybí. Ignoruje ji `trackmania`, jehož plugin soubory zapisuje sám. |
| `--port` | `5300` | Port UDP, na kterém se poslouchá. **U každé hry kromě Forzy znamená hodnota 5300 „výchozí port hry“**: 20777 pro `wrc` a hry DiRT, 6776 pro `rbr`, 4460 pro `beamng`. Zadejte jiné číslo, chcete-li přepsat. Nepoužívá se u her Assetto Corsa (sdílená paměť) ani u Trackmanie (soubory). |
| `--forward` | žádné | Jen Forza: `host:port`, kam předat každý přijatý paket beze změny. `127.0.0.1:5301` pro FH Companion. Samotné `:5301` znamená `127.0.0.1:5301`. |
| `--install` | vypnuto | `beamng`: zkopíruje mod protokolu do rozbalených modů BeamNGu. `trackmania`: zkopíruje plugin Openplanetu do složky pluginů Openplanetu. Ostatní hry ji ignorují. |
| `--configure` | žádné | Jen `wrc`: cesta k `config.json` telemetrie EA SPORTS WRC; zapne výchozí paket `wrc` před nahráváním (předem se zálohuje). |
| `--surface` | žádné | Rallye hry (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` nebo `mixed`, zapsané do `meta.surface` souboru kola. Bez něj se žádný povrch nezapíše. |

## Hry na první pohled {#the-games-at-a-glance}

| `--game` | Hra | Zdroj | Výchozí port | Dělení | `game` v souboru | Stránka |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (včetně 2023) | Data Out UDP | 5300 | počítadlo kol hry (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, nebo `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | sdílená paměť `acpmf_*` | - | počítadlo kol (`CounterSplitter`) | `assetto-corsa` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | sdílená paměť `acpmf_*` | - | počítadlo kol (`CounterSplitter`) | `assetto-corsa-competizione` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | sdílená paměť `acevo_pmf_*` | - | startovní čára (`LineSplitter`) | `assetto-corsa-evo` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | sdílená paměť `acpmf_*` | - | startovní čára / zastavení (`LineSplitter`) | `assetto-corsa-rally` | [Hry Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struktura `wrc` | 20777 | hodiny etapy (`StageSplitter`) | `ea-sports-wrc` | [Rallye hry](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-rally-2` | [Rallye hry](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-rally` | [Rallye hry](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | hodiny etapy (`StageSplitter`) | `dirt-4` | [Rallye hry](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | hodiny etapy (`StageSplitter`) | `richard-burns-rally` | [Rallye hry](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod protokolu `heat3d`, UDP | 4460 | startovní čára (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | plugin Openplanetu, soubory CSV | - | podle běhu, v pluginu | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | jeho vlastní soubory `.ibt`, čte je prohlížeč | - | počítadlo kol simulátoru | `iracing` | [iRacing](telemetry-iracing.md) |

## Stav {#status}

Nahrávač Forzy je ten, který se používá nejvíc. Nahrávače Kunos, rallye, BeamNG a Trackmanie
jsou postaveny podle publikovaných rozložení a otestovány na syntetických paketech a stránkách
sestavených z těchto rozložení (`tests/test_kunos.py`, `tests/test_rally.py`,
`tests/test_beamng.py`); **žádný z nich zatím neběžel proti živé hře**. Nahrávače, které dokážou
kontrolovat svůj vstup, to dělají, jak pakety přicházejí, a když něco neodpovídá, jednou vypíší
`note:` (EA WRC a DiRT porovnávají světovou rychlost s rychlostí; EA WRC také nahlásí paket
kratší než 237bajtová výchozí struktura). [Hry](games.md) uvádí zdroje a to, co u každé hry
ještě není potvrzeno.

## Během běhu {#while-it-runs}

- **Forza** každou sekundu vypisuje řádek stavu: přijaté pakety a číslo otevřeného kola, počet
  vzorků a metry, nebo `waiting for a race`. Každé dokončené kolo vypíše `wrote <file>`.
- **Hry Assetto Corsa** vypisují název každého souboru kola při jeho zápisu.
- **Rallye hry** vypisují `listening for <game> on port <port>`, pak `stage written: <file>`;
  při Ctrl+C se otevřená etapa dost dlouhá na zachování zapíše jako `partial stage written: <file>`.
- **BeamNG** vypisuje `lap written: <file>` a při Ctrl+C `run written: <file>`.
- **Trackmania** nevypisuje nic na běh: plugin zapisuje své soubory CSV sám.
- Na konci každý nahrávač vypíše, kolik souborů zapsal.

Záznam Forzy, zde krmený syntetickými daty Data Out z auta, které jede dvě kola kruhu o délce
150 m (soubory kol, surový pomocný soubor a souhrn sebekontroly, který zanechá):

![záznam telemetrie se dvěma koly ze syntetického feedu Forzy](../assets/img/telemetry-run.svg)

## Názvy souborů {#file-names}

| Nahrávač | Vzor |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| hry Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| rallye hry, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, kde `<game>` je dlouhý název (`ea-sports-wrc`, `beamng`, ...), `stage` u rallye a `lap` u BeamNGu |
| plugin Trackmanie | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` proti `run` (Forza, Assetto Corsa) a přípona `_partial` (rallye, BeamNG) říkají, zda bylo
kolo nebo etapa dokončena. Časové razítko je, kdy byl soubor zapsán, ne kdy kolo začalo.

Vedle souborů kol zapisuje každý nahrávač `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - každý
paket nebo stránka, které přišly, celé, i v menu a mezi koly - a
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, sebekontrolu: pro každý typ paketu, kolik jich
přišlo, kolik jich šlo do souborů kol, a `lost`, což je 0. Prohlížeč oba přeskočí, když se načte
složka. Viz [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) v README.

## Podstránky této stránky {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Hry Assetto Corsa](telemetry-assetto-corsa.md)
- [Rallye hry](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Jak se rozdělují kola a etapy](lap-splitting.md)
- [Skluz, driftový úhel a odvozené kanály](slip-and-drift.md)
- [Soubor heat3d-lap](lap-format.md)
