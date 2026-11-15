---
title: "Снимачи на телеметрија"
nav_order: 3
lang: "mk"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Снимачи на телеметрија {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` го снима секој канал што го испраќа играта, го дели текот на кругови или етапи и пишува
по една [`heat3d-lap`](lap-format.md) JSON датотека за круг во папка. Табот Анализа на трка во
прегледувачот ги чита тие датотеки. Снимањето трае додека не притиснете **Ctrl+C**; кругот или етапата
што е отворена во тој момент се пишува ако е доволно долга за да се задржи (видете
[Поделба на кругови и етапи](lap-splitting.md)).

Код: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
и модулите во [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Опции {#options}

| Опција | Стандардно | Значење |
|---|---|---|
| `--game` | `forza` | Една од `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Папката во која се пишуваат датотеките за кругови. Се создава ако недостасува. Го игнорира `trackmania`, чиј додаток ги пишува датотеките сам. |
| `--port` | `5300` | UDP порт на кој се слуша. **За секоја игра освен Forza вредноста 5300 значи „сопствениот стандарден порт на играта“**: 20777 за `wrc` и игрите DiRT, 6776 за `rbr`, 4460 за `beamng`. Дајте кој било друг број за да го замените. Не се користи од игрите Assetto Corsa (споделена меморија) или Trackmania (датотеки). |
| `--forward` | нема | Само Forza: `host:port` на кој се пренесува секој примен пакет, непроменет. `127.0.0.1:5301` за FH Companion. Голо `:5301` значи `127.0.0.1:5301`. |
| `--install` | исклучено | `beamng`: најпрво го копира модот за протокол во распакуваните модови на BeamNG. `trackmania`: го копира додатокот Openplanet во папката за додатоци на Openplanet. Другите игри го игнорираат. |
| `--configure` | нема | Само `wrc`: патека до `config.json` за телеметрија на EA SPORTS WRC; го вклучува стандардниот пакет `wrc` пред снимањето (најпрво се прави резервна копија). |
| `--surface` | нема | Рели игри (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` или `mixed`, запишано во `meta.surface` на датотеката за круг. Без него не се пишува подлога. |

## Игрите накратко {#the-games-at-a-glance}

| `--game` | Игра | Извор | Стандарден порт | Поделба | `game` во датотеката | Страница |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (вкл. 2023) | Data Out UDP | 5300 | бројачот на кругови на играта (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, или `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | споделена меморија `acpmf_*` | - | бројач на кругови (`CounterSplitter`) | `assetto-corsa` | [Игри Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | споделена меморија `acpmf_*` | - | бројач на кругови (`CounterSplitter`) | `assetto-corsa-competizione` | [Игри Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | споделена меморија `acevo_pmf_*` | - | стартна линија (`LineSplitter`) | `assetto-corsa-evo` | [Игри Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | споделена меморија `acpmf_*` | - | стартна линија / запирање (`LineSplitter`) | `assetto-corsa-rally` | [Игри Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, структура `wrc` | 20777 | часовник на етапата (`StageSplitter`) | `ea-sports-wrc` | [Рели игри](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | часовник на етапата (`StageSplitter`) | `dirt-rally-2` | [Рели игри](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | часовник на етапата (`StageSplitter`) | `dirt-rally` | [Рели игри](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | часовник на етапата (`StageSplitter`) | `dirt-4` | [Рели игри](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | часовник на етапата (`StageSplitter`) | `richard-burns-rally` | [Рели игри](telemetry-rally.md) |
| `beamng` | BeamNG.drive | мод за протокол `heat3d`, UDP | 4460 | стартна линија (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | додаток Openplanet, CSV датотеки | - | по возење, во додатокот | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | сопствени `.ibt` датотеки, ги чита прегледувачот | - | бројачот на кругови на симулаторот | `iracing` | [iRacing](telemetry-iracing.md) |

## Статус {#status}

Снимачот за Forza е оној што е најмногу испробан. Снимачите за Kunos, рели, BeamNG и Trackmania се
изградени според објавените распореди и тестирани на синтетички пакети и страници изградени од тие
распореди (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **ниту еден од
нив сè уште не е пуштен против вистинската игра**. Снимачите што можат да го проверат својот влез
тоа го прават додека пристигнуваат пакетите и печатат `note:` еднаш кога нешто не се совпаѓа (EA WRC
и DiRT ја споредуваат светската брзина со брзината; EA WRC јавува и пакет пократок од стандардната
структура од 237 бајти). [Игри](games.md) ги наведува изворите и што уште не е потврдено по игра.

## Додека работи {#while-it-runs}

- **Forza** печати статусна линија секоја секунда: примени пакети, и бројот, бројот на примероци и
  метрите на отворениот круг, или `waiting for a race`. Секој завршен круг печати `wrote <file>`.
- **Игрите Assetto Corsa** го печатат името на секоја датотека за круг додека се пишува.
- **Рели игрите** печатат `listening for <game> on port <port>`, потоа `stage written: <file>`;
  на Ctrl+C отворена етапа доволно долга за да се задржи се пишува како `partial stage written: <file>`.
- **BeamNG** печати `lap written: <file>`, а на Ctrl+C `run written: <file>`.
- **Trackmania** не печати ништо по возење: додатокот сам ги пишува своите CSV датотеки.
- На крајот секој снимач печати колку датотеки напишал.

Снимање на Forza, овде хранета со синтетички Data Out пакети од возило што вози два круга по кружница
од 150 m (датотеките за кругови, суровата пратечка датотека и резимето за самопроверка што ги остава):

![телеметрија што снима два круга од синтетички Forza извор](../assets/img/telemetry-run.svg)

## Имиња на датотеки {#file-names}

| Снимач | Образец |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Игри Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Рели игри, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, каде `<game>` е долгото име (`ea-sports-wrc`, `beamng`, ...), `stage` за рели и `lap` за BeamNG |
| Додаток за Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` наспроти `run` (Forza, Assetto Corsa) и наставката `_partial` (рели, BeamNG) означуваат дали
кругот или етапата била завршена. Временската ознака е кога била напишана датотеката, не кога почнал
кругот.

Покрај датотеките за кругови секој снимач пишува `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - секој
пакет или страница што пристигнала, чувана цела, и во менијата и меѓу круговите - и
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, самопроверката: по тип на пакет колку дошле, колку
влегле во датотеки за кругови, и `lost`, што е 0. Прегледувачот ги прескокнува двете кога се вчитува
папка. Видете [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) во README.

## Подстраници {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Игри Assetto Corsa](telemetry-assetto-corsa.md)
- [Рели игри](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Поделба на кругови и етапи](lap-splitting.md)
- [Лизгање, дрифт и изведени канали](slip-and-drift.md)
- [Датотеката heat3d-lap](lap-format.md)
