---
title: "Снимачи телеметрије"
nav_order: 3
lang: "sr"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Снимачи телеметрије {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` снима сваки канал који игра шаље, дели ток на кругове или деонице, и пише по једну [`heat3d-lap`](lap-format.md) JSON датотеку по кругу у фасциклу. Картица Race прегледача чита те датотеке. Снимање траје док не притиснете **Ctrl+C**; круг или деоница који су отворени у том тренутку се упишу ако су довољно дугачки да се задрже (видите [Како се кругови и деонице деле](lap-splitting.md)).

Код: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
и модули у [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Опције {#options}

| Опција | Подразумевано | Значење |
|---|---|---|
| `--game` | `forza` | Једна од вредности `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Фасцикла у коју се пишу датотеке кругова. Прави се ако не постоји. Не важи за `trackmania`, чији додатак сам пише датотеке. |
| `--port` | `5300` | UDP порт на којем се слуша. **За сваку игру осим Forza вредност 5300 значи "подразумевани порт игре"**: 20777 за `wrc` и DiRT игре, 6776 за `rbr`, 4460 за `beamng`. Дајте било који други број да то промените. Не користи се за игре Assetto Corsa (дељена меморија) или Trackmania (датотеке). |
| `--forward` | нема | Само Forza: `host:port` коме се сваки примљени пакет прослеђује непромењен. `127.0.0.1:5301` за FH Companion. Голо `:5301` значи `127.0.0.1:5301`. |
| `--install` | искључено | `beamng`: прво копира мод протокола у распаковане модове BeamNG-а. `trackmania`: копира Openplanet додатак у фасциклу додатака Openplanet-а. Остале игре то занемарују. |
| `--configure` | нема | Само `wrc`: путања до телеметријског `config.json` EA SPORTS WRC-а; укључује подразумевани `wrc` пакет пре снимања (прво се резервно копира). |
| `--surface` | нема | Рели игре (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` или `mixed`, уписано у `meta.surface` датотеке круга. Без њега се подлога не уписује. |

## Игре на први поглед {#the-games-at-a-glance}

| `--game` | Игра | Извор | Подразумевани порт | Подела | `game` у датотеци | Страница |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (укључујући 2023) | Data Out UDP | 5300 | бројач кругова игре (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, или `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | дељена меморија `acpmf_*` | - | бројач кругова (`CounterSplitter`) | `assetto-corsa` | [Assetto Corsa игре](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | дељена меморија `acpmf_*` | - | бројач кругова (`CounterSplitter`) | `assetto-corsa-competizione` | [Assetto Corsa игре](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | дељена меморија `acevo_pmf_*` | - | старт линија (`LineSplitter`) | `assetto-corsa-evo` | [Assetto Corsa игре](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | дељена меморија `acpmf_*` | - | старт линија / заустављање (`LineSplitter`) | `assetto-corsa-rally` | [Assetto Corsa игре](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, структура `wrc` | 20777 | сат деонице (`StageSplitter`) | `ea-sports-wrc` | [Рели игре](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | сат деонице (`StageSplitter`) | `dirt-rally-2` | [Рели игре](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | сат деонице (`StageSplitter`) | `dirt-rally` | [Рели игре](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | сат деонице (`StageSplitter`) | `dirt-4` | [Рели игре](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | сат деонице (`StageSplitter`) | `richard-burns-rally` | [Рели игре](telemetry-rally.md) |
| `beamng` | BeamNG.drive | `heat3d` мод протокола, UDP | 4460 | старт линија (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | Openplanet додатак, CSV датотеке | - | по вожњи, у додатку | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | сопствене `.ibt` датотеке, чита их прегледач | - | бројач кругова симулатора | `iracing` | [iRacing](telemetry-iracing.md) |

## Статус {#status}

Снимач за Forza је онај који се највише користи. Снимачи за Kunos, рели, BeamNG и Trackmania су изграђени према објављеним распоредима и тестирани на синтетичким пакетима и страницама састављеним од тих распореда (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **ниједан још није пуштен против живе игре**. Снимачи који могу да провере свој улаз то раде кад пакети стижу и исписују `note:` једном кад нешто не одговара (EA WRC и DiRT пореде светску брзину са брзином; EA WRC такође пријављује пакет краћи од 237-бајтне подразумеване структуре). [Игре](games.md) наводи изворе и шта није потврђено по игри.

## Док ради {#while-it-runs}

- **Forza** исписује ред статуса сваке секунде: примљени пакети, и број отвореног круга, број узорака и метри, или `waiting for a race`. Сваки завршени круг исписује `wrote <file>`.
- **Игре Assetto Corsa** исписују назив сваке датотеке круга кад се упише.
- **Рели игре** исписују `listening for <game> on port <port>`, па `stage written: <file>`; на Ctrl+C отворена деоница довољно дугачка да се задржи пише се као `partial stage written: <file>`.
- **BeamNG** исписује `lap written: <file>`, а на Ctrl+C `run written: <file>`.
- **Trackmania** не исписује ништа по вожњи: додатак сам пише своје CSV датотеке.
- На крају сваки снимач исписује колико је датотека написао.

Снимање Forza-е, овде храњено синтетичким Data Out пакетима аутомобила који вози два круга круга од 150 m (датотеке кругова, сирови прилог и сажетак самопровере који оставља):

![телеметријско снимање два круга из синтетичког Forza тока](../assets/img/telemetry-run.svg)

## Називи датотека {#file-names}

| Снимач | Шаблон |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Игре Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Рели игре, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, где је `<game>` дуго име (`ea-sports-wrc`, `beamng`, ...), `stage` за рели и `lap` за BeamNG |
| Trackmania додатак | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` наспрам `run` (Forza, Assetto Corsa) и суфикс `_partial` (рели, BeamNG) означавају да ли је круг или деоница завршена. Временски жиг је кад је датотека написана, а не кад је круг почео.

Уз датотеке кругова сваки снимач пише `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - сваки пакет или страница која је стигла, цела, и у менију и између кругова - и `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, самопроверу: по врсти пакета колико их је стигло, колико их је ушло у датотеке кругова, и `lost`, који је 0. Прегледач их прескаче кад се учита фасцикла. Видите [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) у README-у.

## Поддокументи ове странице {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Assetto Corsa игре](telemetry-assetto-corsa.md)
- [Рели игре](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Како се кругови и деонице деле](lap-splitting.md)
- [Клизање, заношење и изведени канали](slip-and-drift.md)
- [Датотека heat3d-lap](lap-format.md)
