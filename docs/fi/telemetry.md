---
title: "Telemetriatallentimet"
nav_order: 3
lang: "fi"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Telemetriatallentimet {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` tallentaa jokaisen kanavan, jonka peli lähettää, jakaa virran kierroksiin tai osuuksiin ja kirjoittaa yhden
[`heat3d-lap`](lap-format.md)-JSON-tiedoston kierrosta kohden kansioon. Katselimen Kisa-analyysi-välilehti lukee nuo tiedostot.
Tallennus jatkuu, kunnes painat **Ctrl+C**; juuri silloin auki oleva kierros tai osuus kirjoitetaan, jos se on riittävän pitkä
säilytettäväksi (katso [Kierrosten ja osuuksien jakaminen](lap-splitting.md)).

Koodi: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
ja moduulit kansiossa [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Valinnat {#options}

| Valinta | Oletus | Merkitys |
|---|---|---|
| `--game` | `forza` | Yksi seuraavista: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Kansio, johon kierrostiedostot kirjoitetaan. Luodaan, jos puuttuu. Ei vaikuta `trackmania`-tilaan, jonka liitännäinen kirjoittaa tiedostot itse. |
| `--port` | `5300` | UDP-portti, johon kuunnellaan. **Kaikille muille peleille kuin Forzalle arvo 5300 tarkoittaa "pelin oma oletus"**: 20777 `wrc`:lle ja DiRT-peleille, 6776 `rbr`:lle, 4460 `beamng`:lle. Anna mikä tahansa muu luku ohittaaksesi. Ei käytössä Assetto Corsa -peleille (jaettu muisti) eikä Trackmanialle (tiedostot). |
| `--forward` | ei mitään | Vain Forza: `host:port`, jonne kaikki vastaanotetut paketit välitetään muuttumattomina. `127.0.0.1:5301` FH Companionille. Pelkkä `:5301` tarkoittaa `127.0.0.1:5301`. |
| `--install` | pois | `beamng`: kopioi protokollamodin BeamNG:n purettuihin modeihin ensin. `trackmania`: kopioi Openplanet-liitännäisen Openplanetin liitännäiskansioon. Muut pelit jättävät sen huomiotta. |
| `--configure` | ei mitään | Vain `wrc`: polku EA SPORTS WRC:n telemetria-tiedostoon `config.json`; kytkee oletus-`wrc`-paketin päälle ennen tallennusta (varmuuskopio ensin). |
| `--surface` | ei mitään | Rallipelit (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` tai `mixed`, kirjoitetaan kierrostiedoston kenttään `meta.surface`. Ilman sitä pintaa ei kirjoiteta. |

## Pelit yhdellä silmäyksellä {#the-games-at-a-glance}

| `--game` | Peli | Lähde | Oletusportti | Jakaminen | `game` tiedostossa | Sivu |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (2023 mukaan lukien) | Data Out UDP | 5300 | pelin kierroslaskuri (`LapSplitter`) | `forza-horizon`, `forza-motorsport` tai `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | jaettu muisti `acpmf_*` | - | kierroslaskuri (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa -pelit](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | jaettu muisti `acpmf_*` | - | kierroslaskuri (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa -pelit](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | jaettu muisti `acevo_pmf_*` | - | lähtölinja (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa -pelit](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | jaettu muisti `acpmf_*` | - | lähtölinja / pysähdys (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa -pelit](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, `wrc`-rakenne | 20777 | osuuskello (`StageSplitter`) | `ea-sports-wrc` | [Rallipelit](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | osuuskello (`StageSplitter`) | `dirt-rally-2` | [Rallipelit](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | osuuskello (`StageSplitter`) | `dirt-rally` | [Rallipelit](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | osuuskello (`StageSplitter`) | `dirt-4` | [Rallipelit](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | osuuskello (`StageSplitter`) | `richard-burns-rally` | [Rallipelit](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d`-protokollamodi, UDP | 4460 | lähtölinja (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet-liitännäinen, CSV-tiedostot | - | ajo kerrallaan, liitännäisessä | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | sen omat `.ibt`-tiedostot, katselin lukee | - | simulaattorin kierroslaskuri | `iracing` | [iRacing](telemetry-iracing.md) |

## Tila {#status}

Forza-tallennin on se, jota on käytetty eniten. Kunos-, rally-, BeamNG- ja Trackmania-tallentimet on rakennettu julkaistuja
asetteluja vastaan ja testattu synteettisillä paketeilla ja sivuilla, jotka on tehty näistä asetteluista (`tests/test_kunos.py`,
`tests/test_rally.py`, `tests/test_beamng.py`); **mitään niistä ei ole vielä ajettu oikeaa peliä vastaan**. Tallentimet, jotka
pystyvät tarkistamaan syötteensä, tekevät sen paketteja saapuessa ja tulostavat kerran `note:`-rivin, kun jokin ei täsmää (EA WRC
ja DiRT vertaavat maailman nopeutta nopeuteen; EA WRC ilmoittaa myös paketista, joka on lyhyempi kuin 237 tavun oletusrakenne).
[Pelit](games.md) listaa lähteet ja sen, mitä kustakin ei ole vielä varmistettu.

## Ajon aikana {#while-it-runs}

- **Forza** tulostaa tilarivin kerran sekunnissa: vastaanotetut paketit ja avoimen kierroksen numero, näytemäärä ja metrit tai
  `waiting for a race`. Jokainen valmis kierros tulostaa `wrote <file>`.
- **Assetto Corsa -pelit** tulostavat kunkin kierrostiedoston nimen sen kirjoittuessa.
- **Rallipelit** tulostavat `listening for <game> on port <port>`, sitten `stage written: <file>`; Ctrl+C:llä auki oleva osuus, joka on
  riittävän pitkä säilytettäväksi, kirjoitetaan muodossa `partial stage written: <file>`.
- **BeamNG** tulostaa `lap written: <file>`, ja Ctrl+C:llä `run written: <file>`.
- **Trackmania** ei tulosta mitään ajoa kohden: liitännäinen kirjoittaa CSV-tiedostonsa itse.
- Lopussa jokainen tallennin tulostaa, kuinka monta tiedostoa se kirjoitti.

Forza-tallennus, tässä syötettynä synteettisillä Data Out -paketeilla auton ajaessa kaksi kierrosta 150 m:n ympyrällä (kierrostiedostot,
raakasivutiedosto ja itsetarkistuksen yhteenveto, jonka se jättää):

![Telemetriatallennus, jossa on kaksi kierrosta synteettisestä Forza-syötteestä](../assets/img/telemetry-run.svg)

## Tiedostonimet {#file-names}

| Tallennin | Malli |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Assetto Corsa -pelit | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Rallipelit, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, missä `<game>` on pitkä nimi (`ea-sports-wrc`, `beamng` jne.), `stage` rallille ja `lap` BeamNG:lle |
| Trackmania-liitännäinen | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` vastaan `run` (Forza, Assetto Corsa) ja `_partial`-pääte (rally, BeamNG) kertovat, oliko kierros tai osuus päätetty.
Aikaleima on tiedoston kirjoitushetki, ei kierroksen alkamishetki.

Kierrostiedostojen vieressä jokainen tallennin kirjoittaa tiedoston `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - jokainen saapunut paketti
tai sivu kokonaisena, myös valikoissa ja kierrosten välissä - ja tiedoston `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, itsetarkistuksen:
paketti- tai sivutyypeittäin, kuinka monta tuli ja kuinka monta meni kierrostiedostoihin, ja `lost`, joka on 0. Katselin ohittaa molemmat,
kun kansio ladataan. Katso [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) README:stä.

## Tämän sivun alasivut {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa -pelit](telemetry-assetto-corsa.md)
- [Rallipelit](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Kierrosten ja osuuksien jakaminen](lap-splitting.md)
- [Luisto, sivuliuku ja johdetut kanavat](slip-and-drift.md)
- [heat3d-lap-tiedosto](lap-format.md)
