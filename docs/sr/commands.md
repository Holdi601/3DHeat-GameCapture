---
title: Референца команди
nav_order: 5
lang: "sr"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Референца команди {#command-reference}

Све команде се покрећу из фасцикле репозиторијума, са окружењем пројекта:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Команда | Шта ради |
|---|---|
| [`route`](#route) | Снима само позиције Forza круга, да би се мапа нашла у игриним фајловима |
| [`telemetry`](#telemetry) | Снима сваки канал, по један фајл круга, за картицу Анализа трке |
| [`laps`](#laps) | Чита библиотеку кругова FH Companion и исписује руту и узорке једног курса |
| [`reconstruct`](#reconstruct) | Решава снимак ван мреже и исписује `.glb` |
| [`hud`](#hud) | Чита сопствене радње играча, смрти и мини-мапу, и ток убистава, из снимка |
| [`locate`](#locate) | Где је узет сваки кадар снимка, у односу на рендере нивоа |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Прозор за скенирање |
| [`python -m heat3d_update`](#updates) | Проверава и примењује ажурирање |
| [`python tools/export_onnx.py`](#the-model-converter) | Претвара модел дубине у ONNX |

Када се покрене као `python -m heat3d_capture`, алат прво проверава да ли постоји новије издање
(видети [Ажурирања](updates.md); `HEAT3D_NO_UPDATE=1` га искључује). `--help` после било које
команде исписује њене опције:

![heat3d_capture --help](../assets/img/cli-help.svg)

Код: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Слуша Forza Data Out и чува само позиције аутомобила, ништа друго: без модела дубине, без
GPU-а, без снимања. Код: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Опција | Подразумевано | Значење |
|---|---|---|
| `-o`, `--out` | обавезно | Путања излаза; њен наставак се мења, па `-o lap` пише `lap.npz` и `lap.json`. |
| `--port` | `5300` | Порт на који игра шаље податке (везан за 127.0.0.1). |
| `--seconds` | `0` | Заустави после толико секунди; `0` ради док не притиснете Ctrl+C. |

Позиција се задржава само док игра јавља да траје трка (`isRaceOn`), аутомобил се креће брже
од 0,5 m/s, и удаљена је најмање 0,5 m од последње задржане позиције. Иначе би стајање у
менију, при 60 пакета у секунди, напунило фајл почетном линијом. Време сваког узорка је
време трке из игре, или стварно време кад је оно 0. Распоред се открива исто као код
`telemetry` (аутомобил мора прво да се креће; видети [Forza](telemetry-forza.md)).

Сваке секунде исписује примљене пакете, задржане позиције и тренутну позицију, или поруку
`nothing on port 5300 yet - is Data Out on?`. Рута се **чува док се вози**: сваке 2 секунде
кад стигне нова позиција (размак расте до двадесеструког трајања последњег чувања, па ни врло
дуга сесија не троши више од двадесетине времена на писање), и још једном кад снимач стане из
било ког разлога: Ctrl+C, `--seconds` или грешка. Свако чување прво пише `lap.npz.partial` /
`lap.json.partial`, па их премешта преко правих фајлова, тако да су фајлови на диску увек
цели. Пад или убијени процес губи најтеже последњих неколико секунди. Ако ништа није
задржано, исписује како да се укључи Data Out и излази са кодом 1.

Излаз:

- `lap.npz` - NumPy низови `positions` (n x 3, метри), `times`, `speeds` (m/s);
- `lap.json` - читљив и без овог пројекта:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Позиције су светске координате из саме игре, и због тога су ручка за налажење истог тла у
игриним фајловима: команда `course` алата [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
узима овај JSON и извози курс преко кога је круг прошао.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Свака опција и свака игра описане су на [Снимачима телеметрије](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Чита библиотеку кругова коју чува FH Companion и за један курс пише два фајла: руту, која каже
који део мапе да се исече из игрине архиве, и табелу сваког узорка сваког круга. Пишу се
заједно, да не би могли да се раздвоје. Код:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Опција | Подразумевано | Значење |
|---|---|---|
| `course` | нема | Име курса, тражи се без строгог поклапања. Изостави га да би се библиотека исписала. |
| `-o`, `--out` | име курса малим словима, размаци као `_` | Путања излаза; `.json` и `.csv` се пишу један поред другог. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Где су фасцикле курсева. |
| `--margin` | `80` | Метри додати око простора курса по x и z у `bounds` руте. |

### Исписивање {#listing}

Без курса исписује број фасцикли курсева и, за сваку, број фајлова кругова (`*.json` било где
испод ње, осим `course.json`) и име курса, па поруку `Name one to write it out:  -o <file> <course>`.

### Налажење курса {#finding-a-course}

Фасцикле курсева се зову `<name> (course_<x>_<z>_to_<x>_<z>)`: почетак и циљ, заокружени. Курс
се налази овим редом: тачно име фасцикле; део имена пре заграде, без обзира на велика и мала
слова; јединствена фасцикла чије име садржи задати текст. Више погодака је грешка, која их
све наводи.

### Читање {#reading-it}

- `course.json` у фасцикли, кад се може прочитати, даје име и незаокружене почетак и циљ
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); иначе се они узимају из имена фасцикле.
  Курс се сматра стазом (circuit) кад су почетак и циљ ближи од 10 m.
- Сваки други `*.json` испод фасцикле је круг. Кругови леже неколико фасцикли дубоко (по класи,
  аутомобилу, подешавању, ознаци), а претрага је једноставно рекурзивна. Фајлови се читају као
  UTF-8 са BOM-ом. Нечитљив круг се прескаче. Кругови се сортирају по времену снимања.
- По кругу: `Lap.samples` (сваки са `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), и класа
  аутомобила, редни број, индекс перформанси, време круга, дужина, време снимања и да ли је
  почео из стајања.

Исписује сажетак (кругови, узорци, најбољи круг и његова класа, распон x/y/z).

### Излаз {#output}

**`<out>.json`** - иста облик руте који пише `route`, па екстрактор мапа прихвата било који:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (проширено за `--margin` по x и
z) и `positions` **најбржег** круга (једна линија, а не мрља свих кругова).

**`<out>.csv`** - сваки узорак сваког круга, по један ред:

| Колона | Значење |
|---|---|
| `course` | име курса |
| `lap` | ознака за сваки круг: датум и време снимања до минута, и време круга |
| `car` | редни број аутомобила |
| `car_class` | слово класе перформанси |
| `pi` | индекс перформанси |
| `lap_seconds` | време круга |
| `speed_kmh` | брзина у km/h |
| `x`, `y`, `z` | светска позиција, метри, 3 децимале |
| `speed_ms` | брзина, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | како их бележи FH Companion |
| `metres` | растојање дуж круга, 3 децимале |
| `elapsed` | секунде од почетка самог круга, 3 децимале |

Вредности које нису позиције пишу се са 4 значајне цифре. Позиције имају фиксне децимале, јер би
4 значајне цифре прилепиле курс на мрежу од једног метра. Имена колона су изабрана тако да
прегледач мапира фајл без упутства: `lap` постаје сесија (два круга једног аутомобила се
никад не спајају), `car` ствар која се креће, `car_class` група по којој се боји, а `elapsed`
временска оса (сваки круг почиње у свом почетку).

На крају исписује савет како да се мапа исече из игре помоћу GameFiles, са фајлом руте или
експлицитним правоугаоником.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Реконструише снимак ван мреже, са путањом камере решеном одједном помоћу VGGT. Спора је: минути
по прозору на десктоп GPU-у. Треба PyTorch, Hugging Face `transformers` и пакет `vggt`, које
скенер не треба. Наведени су у `requirements-offline.txt`, а команда их проверава после
исписивања линије лиценце и нуди да инсталира оно што недостаје (излазни код 1 ако се одбије).
Пун опис: [Реконструкција ван мреже](reconstruction-offline.md).

| Опција | Подразумевано | Значење |
|---|---|---|
| `video` | обавезно | Снимак. Излазни код 2 ако не постоји. |
| `-o`, `--out` | обавезно | `.glb` који се пише. |
| `--solve-budget` | `260` | Највише кадрова предатих решавачу. Размаци између њих зависе од тога колико се слика помера, а не од сата. Више је тачније и много спорије. Више од 400 планираних кадрова се одбија. |
| `--fuse-interval` | `0.4` | Секунде између кадрова стопљених у геометрију. |
| `--model` | `vggt-1b` | Којим VGGT тежинама да се решава: `vggt-1b` (`facebook/VGGT-1B`, некомерцијално) или `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, ограничено; потребан је приступ који одобри Meta). Линија лиценце која се прва исписује је лиценца тог модела. |

Прво исписује линију лиценце модела, па сваку фазу (`masking`, `planning`, `solving`, `fusing`,
`exporting`) са протеклим секундама и напретком, и на крају сажетак: решене камере, грешку
затварања, најгори шав, напомене и написан фајл. Излазни код је 0 само ако је фајл написан.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Чита HUD игре из играчевог снимка, после меча: сопствене радње играча из искачућег прозорчића
са поенима, смрти и оживљавања из екрана за пад и распоређивање, траг на мини-мапи и ток
убистава. Пише `<out>.parquet` (траг и догађаји, табела за 3DHeat), `<out>.events.jsonl`,
`<out>.summary.json`, и `<out>.map.png` + `.map.json` (мозаик мини-мапе и њена сидра за опцију
Слика мапе у прегледачу). Battlefield 6 (`bf6`) је за сада једини профил.

Треба **ffmpeg и ffprobe** у PATH-у (`winget install Gyan.FFmpeg`, па нови терминал).

| Опција | Подразумевано | Значење |
|---|---|---|
| `video` | обавезно | Снимак. |
| `-o`, `--out` | име видеа | Путања излаза без наставка. |
| `--game` | `bf6` | Чији HUD да се чита. |
| `--player` | погађа се | Име играча како га показује ток убистава, поклапање без строгости. |
| `--fps` | `5` | Узорци мини-мапе у секунди. |
| `--start`, `--seconds` | цео видео | Део снимка који се чита. |
| `--metres-per-pixel` | нема | Размера мини-мапе, кад је позната. Без ње су позиције у пикселима мини-мапе. |
| `--cpu` | искључено | Декодирај на процесору, и кад постоји NVIDIA картица. |

Потпун опис: [Читање HUD-а из снимка](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` исцрта ниво са сваког места на коме играч може да стане и индексира рендере; `frames`
одређује положај сваког узорковано кадра снимка према њима, по слици, а трагом мини-мапе из
команде `hud` као резервом; `eval` пореди резултат са познатим положајима камере; `train`
обучава модел места за сваку мапу, на рендерима нивоа (и на кадровима које је већ одредио
претходни пролаз), за `build --head`; `refmap` поставља сопствену мапу игре (њен екран
распоређивања) на ниво, а `minimap` чита мини-мапу снимка према њој, кадар по кадар, што
`locate frames --minimap` може да узме. Потребни су PyTorch и `requirements-locate.txt`.
**Експериментално:** на правим снимцима за сада одређује само мали део кадрова. Свака опција,
излази и метод: [Одређивање кадрова у нивоу](locate.md); комплетан списак опција:
[Референца команди](../cli-reference.md).

## Прозор за скенирање {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

или двоструки клик на `scan.bat`. Нема опција. Видети [Прозор за скенирање](reconstruction-scan-ui.md).

## Ажурирања {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Видети [Ажурирања](updates.md).

## Конвертор модела {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Претвара контролну тачку Depth Anything V2 у ONNX фајл који скенер покреће. Потребни су PyTorch,
`transformers` и `onnxscript`. Видети [Дубина](reconstruction-depth.md#building-the-model).
