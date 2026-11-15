---
title: Файлът heat3d-lap
nav_order: 9
lang: "bg"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Файлът `heat3d-lap` {#the-heat3d-lap-file}

Всеки записвач на телеметрия в това хранилище записва по един файл за обиколка или етап, в една и съща форма, каквато и да е играта. Изнасянето на трасето в [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) го чете, за да намери играта, нивото и изминатата линия. Всяка програма, която чете JSON, може да го прочете.

![Полетата и каналите на файл с обиколка, записан от синтетичен поток на Forza](../assets/img/lap-file.svg)

## Документът {#the-document}

Един JSON обект. Каналите се пазят като колони: по един масив за всеки канал, всички с еднаква дължина, по един елемент за всяка проба.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Поле | Значение |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | коя игра е обиколката; вижте списъка по-долу |
| `track` | името на трасето, етапа или картата, когато играта го изпраща |
| `layout` | само при Forza: кое разположение на пакета Data Out е декодирано |
| `car` | каквото играта казва за автомобила; свободна форма |
| `lap` | номерът на обиколката, времето ѝ, както го е отчела играта (или разстоянието между пробите), дали е завършена, дължината ѝ |
| `meta` | как да се четат числата; вижте по-долу |
| `units` | мерната единица на всеки присъстващ канал, за четец, който не познава таблицата по-долу |
| `channels` | пробите |
| `unparsed` | само при Forza, когато пакетът има байтове, които нямат име на поле: `ranges` (техните отмествания `[start, end)` в байтове от пакета) и `hex` (за всяка проба - тези байтове в шестнадесетичен вид), така че самият файл съдържа целия пакет |

`game` е едно от: `forza-horizon`, `forza-motorsport`, `forza` (разположението на пакета не е различено), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` казва какво означават числата там, където игрите се различават:

- `slip`: какво съдържат каналите за приплъзване, където играта ги изпраща - `peak` (нормирано, така че над 1 гумата губи сцепление: Forza), `scaled` (физическо приплъзване, разделено на типичен асфалтов връх: игрите Assetto Corsa), `physical` (част и радиани), `index` (0..1 мярка за плъзгане: Trackmania);
- `discipline`: `circuit` (писта), `rally` (рали) или `arcade` (аркада);
- `surface`: `tarmac` (асфалт), `loose` (рохкава почва), `snow` (сняг), `ice` (лед) или `mixed` (смесена), когато е известна (ралийните записвачи я взимат от `--surface`).

## Канали {#channels}

Канал, който играта не изпраща, липсва и никога не се запълва с нули. Каналите за всяко колело носят колелото след точка: `.FL`, `.FR`, `.RL`, `.RR`.

Позициите са светът на играта, в метри, с `y` нагоре. Игра, чийто свят е с Z нагоре, се завърта до Y нагоре от записвача си; нищо друго не се променя, така че лявата координатна система (тази на Forza) остава лява.

| Канал | Мерна единица | Значение |
|---|---|---|
| `time` | s | от първата проба на обиколката |
| `distance` | m | по изминатия път от първата проба |
| `x`, `y`, `z` | m | позиция; `y` е височината |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | педалите и ръчката |
| `steer` | -1..1 | положително надясно |
| `gear` | | както я брои играта |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | в рамката на автомобила |
| `yaw`, `pitch`, `roll` | rad | посока и ориентация |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | скорост в рамката на автомобила: надясно, напред, нагоре |
| `bodySlip` | rad | ъгъл на дрифта, където играта го изпраща |
| `loose` | 0/1 | на рохкава почва (Trackmania) |
| `airborne` | 0/1 | никое колело не е на земята |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | както ги изпраща играта |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | помощите работят, системите са включени |
| `absLevel`, `tcLevel` | | настройки на помощите |
| `brakeBias` | 0..1 | дял на предната ос |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | за всяко колело |
| `tirePressure` | psi | за всяко колело |
| `tireWear` | 0..1 | за всяко колело |
| `slipRatio`, `slipAngle`, `combinedSlip` | вижте `meta.slip` | за всяко колело |
| `slipIndex` | 0..1 | за всяко колело, мярка за плъзгане (Trackmania) |
| `camber` | rad | за всяко колело |
| `brakeTemp` | °C | за всяко колело |
| `padLife`, `discLife` | | за всяко колело |
| `suspensionM` | m | ход на колелото |
| `suspension` | 0..1 | ход на колелото, от диапазона, който обиколката е използвала |
| `wheelLoad` | N | за всяко колело |
| `wheelSpeed` | rad/s | за всяко колело, въртене |
| `wheelSurfaceSpeed` | m/s | за всяко колело, скорост на контактното петно |
| `groundContact` | 0/1 | за всяко колело |
| `rumble`, `surfaceRumble` | | за всяко колело: на неравна лента; неравността на повърхността |
| `puddle` | | за всяко колело: дълбочина на стояща вода |

Записвачът може да добави собствени канали под други имена; четецът запазва това, което не познава.

Нито една ралийна игра не изпраща приплъзване на гумите. Четецът може да го изчисли от скоростта на контактното петно или на повърхността на всяко колело спрямо скоростта на автомобила, `(wheel - car) / car`, или от въртенето и ефективния радиус на търкаляне, измерен върху самата обиколка там, където се изпраща само въртене. Ъгълът на дрифта идва от собствената скорост на автомобила (`latVel`, `longVel`), когато е изпратена, или от световната скорост, проектирана върху осите на автомобила.

## Формата CSV {#the-csv-form}

Приставката за Trackmania пише вместо това `heat3d-lap-csv`: първият ред започва с `# ` и съдържа JSON обект (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), следва ред с имената на каналите и после по един ред за всяка проба. Имената на каналите са същите като по-горе.

## Какво всеки записвач всъщност пише {#what-each-recorder-actually-writes}

Форматът по-горе е договорът; записвачите го попълват малко по различен начин и четецът трябва да понася всички тези (проверено по кода):

| Записвач | `track` | `layout` | `meta` | `units` | Канали извън таблицата |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (номерът на трасето на Forza Motorsport 2023 е `lap.trackOrdinal`) | откритото разположение на пакета | `slip: peak`, `discipline: circuit` | само мерните единици на присъстващите канали | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, часовникът на играта `timestampMs`, `raceTime`, `bestLap`, `lastLap`; скоростта в рамката на автомобила е под каноничните `latVel`, `vertVel`, `longVel`; `unparsed` до каналите |
| Игрите Assetto Corsa (`kunos.py`) | от статичната страница, или `null` | липсва | `slip: scaled`, `discipline: circuit` или `rally` | фиксиран списък | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (както е изпратен), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Ралийни игри (`rally.py` през `lapfile.py`) | `null` | липсва | `discipline: rally`, `slip: null`, `surface` само когато е даден `--surface` (иначе визуализаторът го заключава) | само мерните единици на присъстващите канали | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` за числата с плаваща запетая, които още нямат утвърдено име; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` през `lapfile.py`) | `null` | липсва | `discipline: circuit` | само мерните единици на присъстващите канали | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Приставката за Trackmania (CSV) | името на картата | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` е блокът на автомобила при Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` при игрите Kunos, когато статичната страница назове такъв, и `{}` иначе. `lap.metres` е разликата в изминатото разстояние, което играта брои, при Forza, а при останалите - сборът от 3D разстоянията между пробите. Стойностите се закръглят при записа: `time` до 4 знака след десетичната запетая, `distance` до 3, останалите числа с плаваща запетая до 5. JSON се записва компактно (без интервали).

Всеки пакет или страница, които записвачът е получил - не само тези на обиколките - се пази цял до файловете на обиколките в `<stamp>_<game>.raw.parquet`, със самопроверка в `<stamp>_<game>.summary.json` (разделът „Completeness“ в README).

Проба, за която канал няма стойност - липсва в този кадър или не е крайно число, каквото го е изпратила играта - се записва като `null` от всеки записвач (`lapfile.clean`), а делът на окачването, изчислен от нея, е също `null`. `NaN` и `Infinity` никога не се записват: те не са JSON, а `JSON.parse` в браузъра отхвърля целия файл заради едно от тях. Четецът трябва да очаква `null` в масива на канала.

Файловете на Forza носят `"game": "forza-horizon"`, `"forza-motorsport"` или `"forza"` според откритото разположение. Четецът на файловете `.tele.gz` на FH Companion във визуализатора създава обиколки с `"game": "forza-horizon"` и `meta.slip = "peak"`; този четец е във визуализатора, не тук. Обиколките на iRacing (четени от `.ibt` във визуализатора) носят `"game": "iracing"`, което не е в списъка със стойности на `game` на записвачите по-горе, защото никой записвач не го пише.

Вижте [Разделяне на обиколки и етапи](lap-splitting.md) за това как се решават `lap.number`, `lap.seconds` и `lap.complete`, и [Приплъзване, дрифт и производни канали](slip-and-drift.md) за това какво извежда визуализаторът от тези канали.
