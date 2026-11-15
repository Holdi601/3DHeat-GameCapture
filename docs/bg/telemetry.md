---
title: Записвачи на телеметрия
nav_order: 3
lang: "bg"
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Записвачи на телеметрия {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` записва всеки канал, който играта изпраща, разделя потока на обиколки или етапи и записва по един JSON файл [`heat3d-lap`](lap-format.md) за всяка обиколка в папка. Раздел „Състезателен анализ“ на визуализатора чете тези файлове. Записът продължава, докато натиснете **Ctrl+C**; обиколката или етапът, който е отворен в този момент, се записва, ако е достатъчно дълъг, за да се запази (вижте [Разделяне на обиколки и етапи](lap-splitting.md)).

Код: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
и модулите в [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Опции {#options}

| Опция | По подразбиране | Значение |
|---|---|---|
| `--game` | `forza` | Едно от: `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Папката, в която се записват файловете на обиколките. Създава се, ако липсва. Пренебрегва се от `trackmania`, чиято приставка записва файловете сама. |
| `--port` | `5300` | UDP портът, на който да слуша. **При всяка игра, освен Forza, стойност 5300 означава „собствения стандартен порт на играта“**: 20777 за `wrc` и игрите DiRT, 6776 за `rbr`, 4460 за `beamng`. Дайте друго число, за да го промените. Не се ползва от игрите Assetto Corsa (споделена памет) или Trackmania (файлове). |
| `--forward` | няма | Само Forza: `host:port`, към който да се предава всеки получен пакет непроменен. `127.0.0.1:5301` за FH Companion. Само `:5301` означава `127.0.0.1:5301`. |
| `--install` | изключено | `beamng`: първо копира мода за протокола в разопакованите модове на BeamNG. `trackmania`: копира приставката за Openplanet в папката за приставки на Openplanet. Другите игри го пренебрегват. |
| `--configure` | няма | Само `wrc`: път до `config.json` за телеметрията на EA SPORTS WRC; включва стандартния пакет `wrc` преди записа (първо се архивира). |
| `--surface` | няма | Ралийните игри (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` или `mixed`, записва се в `meta.surface` на файла на обиколката. Без него не се записва повърхност. |

## Игрите накратко {#the-games-at-a-glance}

| `--game` | Игра | Източник | Порт по подразбиране | Разделяне | `game` във файла | Страница |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (вкл. 2023) | Data Out UDP | 5300 | броячът на обиколките на играта (`LapSplitter`) | `forza-horizon`, `forza-motorsport` или `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | споделена памет `acpmf_*` | - | брояч на обиколките (`CounterSplitter`) | `assetto-corsa` | [Игрите Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | споделена памет `acpmf_*` | - | брояч на обиколките (`CounterSplitter`) | `assetto-corsa-competizione` | [Игрите Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | споделена памет `acevo_pmf_*` | - | начална линия (`LineSplitter`) | `assetto-corsa-evo` | [Игрите Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | споделена памет `acpmf_*` | - | начална линия / спиране (`LineSplitter`) | `assetto-corsa-rally` | [Игрите Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, структура `wrc` | 20777 | часовник на етапа (`StageSplitter`) | `ea-sports-wrc` | [Ралийни игри](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | часовник на етапа (`StageSplitter`) | `dirt-rally-2` | [Ралийни игри](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | часовник на етапа (`StageSplitter`) | `dirt-rally` | [Ралийни игри](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | часовник на етапа (`StageSplitter`) | `dirt-4` | [Ралийни игри](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | NGP UDP | 6776 | часовник на етапа (`StageSplitter`) | `richard-burns-rally` | [Ралийни игри](telemetry-rally.md) |
| `beamng` | BeamNG.drive | мод за протокол `heat3d`, UDP | 4460 | начална линия (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | приставка за Openplanet, CSV файлове | - | по пускане, в приставката | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | собствените му `.ibt` файлове, четени от визуализатора | - | брояча на обиколките на симулатора | `iracing` | [iRacing](telemetry-iracing.md) |

## Състояние {#status}

Записвачът за Forza е най-използваният. Записвачите за Kunos, ралийните игри, BeamNG и Trackmania са изградени по публикуваните разположения и тествани върху синтетични пакети и страници, изградени по тези разположения (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **нито един от тях още не е пускан срещу живата игра**. Записвачите, които могат да проверят входа си, го правят, докато пакетите пристигат, и веднъж извеждат `note:`, когато нещо не съвпада (EA WRC и DiRT сравняват световната скорост със скоростта; EA WRC също докладва пакет по-къс от стандартната 237-байтова структура). [Игри](games.md) изброява източниците и какво още не е потвърдено за всяка игра.

## Докато работи {#while-it-runs}

- **Forza** извежда ред със състоянието веднъж в секунда: получени пакети и номера на отворената обиколка, броя проби и метрите ѝ, или `waiting for a race`. Всяка завършена обиколка извежда `wrote <file>`.
- **Игрите Assetto Corsa** извеждат името на всеки файл на обиколка, докато се записва.
- **Ралийните игри** извеждат `listening for <game> on port <port>`, после `stage written: <file>`; при Ctrl+C отворен етап, достатъчно дълъг, за да се запази, се записва като `partial stage written: <file>`.
- **BeamNG** извежда `lap written: <file>`, а при Ctrl+C `run written: <file>`.
- **Trackmania** не извежда нищо за всяко пускане: приставката записва CSV файловете сама.
- В края всеки записвач извежда колко файла е записал.

Запис на Forza, тук захранен със синтетични пакети Data Out на автомобил, карящ две обиколки на кръг от 150 m (файловете на обиколките, суровият помощен файл и обобщението на самопроверката, които оставя):

![запис на телеметрия с две обиколки от синтетичен поток на Forza](../assets/img/telemetry-run.svg)

## Имена на файловете {#file-names}

| Записвач | Шаблон |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Игрите Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Ралийни игри, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, където `<game>` е дългото име (`ea-sports-wrc`, `beamng`, ...), `stage` за ралитата и `lap` за BeamNG |
| Приставката за Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` срещу `run` (Forza, Assetto Corsa) и наставката `_partial` (ралитата, BeamNG) показват дали обиколката или етапът е завършен. Времевият отпечатък е моментът, в който файлът е записан, а не когато е започнала обиколката.

До файловете на обиколките всеки записвач пише `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - всеки пакет или страница, които са пристигнали, цели, включително в менютата и между обиколките - и `<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, самопроверката: за всеки вид пакет колко са дошли, колко са влезли във файлове на обиколки и `lost`, който е 0. Визуализаторът пропуска и двата, когато се зареди папка. Вижте [Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) в README.

## Подстраници {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Игрите Assetto Corsa](telemetry-assetto-corsa.md)
- [Ралийни игри](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Разделяне на обиколки и етапи](lap-splitting.md)
- [Приплъзване, дрифт и производни канали](slip-and-drift.md)
- [Файлът heat3d-lap](lap-format.md)
