---
title: "Snemalniki telemetrije"
nav_order: 3
lang: "sl"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Snemalniki telemetrije {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` posname vsak kanal, ki ga igra pošlje, tok razdeli na kroge ali etape in v mapo zapiše po eno [`heat3d-lap`](lap-format.md) JSON datoteko na krog. Zavihek Analiza dirke v pregledovalniku bere te datoteke. Snemanje teče, dokler ne pritisneš **Ctrl+C**; krog ali etapa, ki je tedaj odprta, se zapiše, če je dovolj dolga, da se ohrani (glejte [Razdeljevanje krogov in etap](lap-splitting.md)).

Koda: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py) in moduli v [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Možnosti {#options}

| Možnost | Privzeto | Pomen |
|---|---|---|
| `--game` | `forza` | Ena od vrednosti: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Mapa, v katero se zapisujejo datoteke krogov. Ustvari se, če ne obstaja. Ignorira jo `trackmania`, čigar vtičnik datoteke zapiše sam. |
| `--port` | `5300` | UDP vrata, na katera se posluša. **Za vse igre razen Forze vrednost 5300 pomeni "privzeta vrata igre"**: 20777 za `wrc` in igre DiRT, 6776 za `rbr`, 4460 za `beamng`. Za drugo število to nadomesti. Ne uporabljajo jo igre Assetto Corsa (deljeni pomnilnik) ali Trackmania (datoteke). |
| `--forward` | ni | Samo Forza: `host:port`, kamor se vsak prejet paket nespremenjen posreduje naprej. `127.0.0.1:5301` za FH Companion. Samo `:5301` pomeni `127.0.0.1:5301`. |
| `--install` | izklopljeno | `beamng`: najprej kopira modul protokola v razpakirane modifikacije BeamNG. `trackmania`: kopira vtičnik Openplanet v mapo Openplanetovih vtičnikov. Druge igre ga ignorirajo. |
| `--configure` | ni | Samo `wrc`: pot do `config.json` telemetrije EA SPORTS WRC; pred snemanjem vklopi privzeti paket `wrc` (prej se varnostno kopira). |
| `--surface` | ni | Relijske igre (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` ali `mixed`, zapisano v `meta.surface` datoteke kroga. Brez tega se podlaga ne zapiše. |

## Igre na kratko {#the-games-at-a-glance}

| `--game` | Igra | Vir | Privzeta vrata | Razdeljevanje | `game` v datoteki | Stran |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (vključno z 2023) | Data Out UDP | 5300 | igrin števec krogov (`LapSplitter`) | `forza-horizon`, `forza-motorsport` ali `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | deljeni pomnilnik `acpmf_*` | - | števec krogov (`CounterSplitter`) | `assetto-corsa` | [Igre Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | deljeni pomnilnik `acpmf_*` | - | števec krogov (`CounterSplitter`) | `assetto-corsa-competizione` | [Igre Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | deljeni pomnilnik `acevo_pmf_*` | - | štartna črta (`LineSplitter`) | `assetto-corsa-evo` | [Igre Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | deljeni pomnilnik `acpmf_*` | - | štartna črta / ustavitev (`LineSplitter`) | `assetto-corsa-rally` | [Igre Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, struktura `wrc` | 20777 | ura etape (`StageSplitter`) | `ea-sports-wrc` | [Relijske igre](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | ura etape (`StageSplitter`) | `dirt-rally-2` | [Relijske igre](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | ura etape (`StageSplitter`) | `dirt-rally` | [Relijske igre](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | ura etape (`StageSplitter`) | `dirt-4` | [Relijske igre](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | ura etape (`StageSplitter`) | `richard-burns-rally` | [Relijske igre](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod protokola `heat3d`, UDP | 4460 | štartna črta (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | vtičnik Openplanet, CSV datoteke | - | po vožnji, v vtičniku | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | lastne datoteke `.ibt`, bere jih pregledovalnik | - | števec krogov simulatorja | `iracing` | [iRacing](telemetry-iracing.md) |

## Stanje {#status}

Snemalnik Forze je najbolj preizkušen. Snemalniki Kunos, relijskih iger, BeamNG in Trackmanie so zgrajeni po objavljenih postavitvah in preizkušeni na sintetičnih paketih in straneh, zgrajenih iz teh postavitev (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **še nobeden ni bil zagnan proti živi igri**. Snemalniki, ki lahko preverijo vhod, to naredijo, ko paketi prihajajo, in enkrat izpišejo `note:`, kadar se kaj ne ujema (EA WRC in DiRT primerjata svetovno hitrost s hitrostjo; EA WRC tudi javi paket, krajši od privzete 237-bajtne strukture). [Igre](games.md) navajajo vire in kaj še ni potrjeno za vsako igro.

## Med snemanjem {#while-it-runs}

- **Forza** vsako sekundo izpiše statusno vrstico: prejete pakete ter številko odprtega kroga, število vzorcev in metre ali `waiting for a race`. Vsak končan krog izpiše `wrote <file>`.
- **Igre Assetto Corsa** izpišejo ime vsake datoteke kroga, ko se zapiše.
- **Relijske igre** izpišejo `listening for <game> on port <port>`, nato `stage written: <file>`; ob Ctrl+C se odprta etapa, dovolj dolga za ohranitev, zapiše kot `partial stage written: <file>`.
- **BeamNG** izpiše `lap written: <file>`, ob Ctrl+C pa `run written: <file>`.
- **Trackmania** ne izpiše ničesar za vsako vožnjo: vtičnik zapisuje svoje CSV datoteke sam.
- Na koncu vsak snemalnik izpiše, koliko datotek je zapisal.

Posnetek Forze, tukaj napajan s sintetičnimi paketi Data Out, ki prihajajo iz vožnje dveh krogov po krogu s 150 m (datoteke krogov, surova priloga in samopreverjanje, ki ga pusti):

![posnetek telemetrije, ki beleži dva kroga iz sintetičnega vira Forze](../assets/img/telemetry-run.svg)

## Imena datotek {#file-names}

| Snemalnik | Vzorec |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Igre Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Relijske igre, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, kjer je `<game>` dolgo ime (`ea-sports-wrc`, `beamng` ...), `stage` za relijske igre in `lap` za BeamNG |
| Vtičnik Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` nasproti `run` (Forza, Assetto Corsa) in pripona `_partial` (relijske igre, BeamNG) povesta, ali je bil krog ali etapa končana. Časovni žig je čas, ko je bila datoteka zapisana, ne čas začetka kroga.

Poleg datotek krogov vsak snemalnik zapiše `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` – vsak prejeti paket ali stran, celo, tudi v menijih in med krogi – ter `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, samopreverjanje: za vsako vrsto paketa, koliko jih je prišlo, koliko jih je šlo v datoteke krogov in `lost`, ki je 0. Pregledovalnik ob nalaganju mape oba preskoči. Glejte [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) v README-ju.

## Podstrani {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Igre Assetto Corsa](telemetry-assetto-corsa.md)
- [Relijske igre](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Razdeljevanje krogov in etap](lap-splitting.md)
- [Zdrs, drift in izpeljani kanali](slip-and-drift.md)
- [Datoteka `heat3d-lap`](lap-format.md)
