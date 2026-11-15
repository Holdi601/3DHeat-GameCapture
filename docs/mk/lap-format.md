---
title: "Датотеката heat3d-lap"
nav_order: 9
lang: "mk"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Датотеката `heat3d-lap` {#the-heat3d-lap-file}

Секој снимач на телеметрија во ова складиште пишува по една датотека за круг
или рели етапа, во ист облик, без разлика на играта. Извозот на патеки во
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) ја чита назад за
да ја најде играта, нивото и возената линија. Секој што чита JSON може да ја прочита.

![Полињата и каналите на датотека за круг напишана од синтетички Forza извор](../assets/img/lap-file.svg)

## Документот {#the-document}

Еден JSON објект. Каналите се чуваат како колони: по една низа за канал, сите со
иста должина, по еден запис за примерок.

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

| Поле | Значење |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | од која игра е кругот; видете го списокот подолу |
| `track` | името на патеката, етапата или мапата, кога играта го испраќа |
| `layout` | само Forza: кој распоред на пакетот Data Out е декодиран |
| `car` | што и да каже играта за возилото; слободна форма |
| `lap` | бројот на кругот, неговото време како го броела играта (или опсегот на примероците), дали е завршен, неговата должина |
| `meta` | како да се читаат броевите; видете подолу |
| `units` | единицата на секој присутен канал, за читач што не ја знае табелата подолу |
| `channels` | примероците |
| `unparsed` | само Forza, кога пакетот има бајти што ниедно поле не ги именува: `ranges` (нивните `[start, end)` поместувања на бајти во пакетот) и `hex` (по примерок, тие бајти како хекс), така што датотеката сама го држи целиот пакет |

`game` е едно од `forza-horizon`, `forza-motorsport`, `forza` (распоредот на
пакетот не е разликуван), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` кажува што значат броевите таму каде што игрите се разликуваат:

- `slip`: што држат каналите за лизгање, таму каде што играта испраќа некои -
  `peak` (нормализирано, па над 1 гумата попушта: Forza), `scaled` (физичко
  лизгање поделено со типичен врв за асфалт: игрите Assetto Corsa), `physical`
  (дропка и радијани), `index` (мерка за лизгање од 0..1: Trackmania);
- `discipline`: `circuit`, `rally` или `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` или `mixed`, кога е познато
  (снимачите за рели ја земаат од `--surface`).

## Канали {#channels}

Каналот што играта не го испраќа отсуствува, никогаш не се пополнува со нули.
Каналите по тркало го носат тркалото по точка: `.FL`, `.FR`, `.RL`, `.RR`.

Позициите се светот на играта, во метри, со `y` нагоре. Играта чиј свет има Z
нагоре, нејзиниот снимач ја врти на Y нагоре; ништо друго не се менува, па
лево-насочениот свет (на Forza) останува лево-насочен.

| Канал | Единица | Значење |
|---|---|---|
| `time` | s | од првиот примерок на кругот |
| `distance` | m | по возената патека од првиот примерок |
| `x`, `y`, `z` | m | позиција; `y` е висина |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | педали и рачка |
| `steer` | -1..1 | позитивно десно |
| `gear` | | како го брои играта |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | рамка на возилото |
| `yaw`, `pitch`, `roll` | rad | насока и положба |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | брзина во рамката на возилото: десно, напред, нагоре |
| `bodySlip` | rad | агол на дрифт, таму каде што играта го испраќа |
| `loose` | 0/1 | на лабава подлога (Trackmania) |
| `airborne` | 0/1 | ниедно тркало не е на земја |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | како ги испраќа играта |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | помошни системи што дејствуваат, системи вклучени |
| `absLevel`, `tcLevel` | | поставки на помошните системи |
| `brakeBias` | 0..1 | предниот дел |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | по тркало |
| `tirePressure` | psi | по тркало |
| `tireWear` | 0..1 | по тркало |
| `slipRatio`, `slipAngle`, `combinedSlip` | видете `meta.slip` | по тркало |
| `slipIndex` | 0..1 | мерка за лизгање по тркало (Trackmania) |
| `camber` | rad | по тркало |
| `brakeTemp` | °C | по тркало |
| `padLife`, `discLife` | | по тркало |
| `suspensionM` | m | пат на суспензијата по тркало |
| `suspension` | 0..1 | пат на суспензијата по тркало, од опсегот што го искористил овој круг |
| `wheelLoad` | N | по тркало |
| `wheelSpeed` | rad/s | вртење по тркало |
| `wheelSurfaceSpeed` | m/s | брзина на допирната површина по тркало |
| `groundContact` | 0/1 | по тркало |
| `rumble`, `surfaceRumble` | | по тркало: на рабник со вибрации; вибрациите на подлогата |
| `puddle` | | длабочина на стоечка вода по тркало |

Снимачот може да додаде свои канали под други имиња; читачот го задржува она што
не го познава.

Ниту една рели игра не испраќа лизгање на гумите. Читачот може да го пресмета од
допирната површина или површинската брзина на секое тркало спрема брзината на
возилото, `(wheel - car) / car`, или од неговото вртење и радиус на тркалање
измерен на самиот круг, таму каде што се испраќа само вртење. Аголот на дрифт
доаѓа од сопствената брзина на возилото (`latVel`, `longVel`) таму каде што се
испраќа, или од светската брзина проектирана на оските на возилото.

## CSV формата {#the-csv-form}

Додатокот за Trackmania пишува `heat3d-lap-csv`: прва линија од `# ` и JSON
објект (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`),
линија со имиња на канали, па по една линија за примерок. Имињата на каналите се
исти како погоре.

## Што навистина пишува секој снимач {#what-each-recorder-actually-writes}

Форматот погоре е договорот; снимачите го пополнуваат малку различно, а читачот
треба да ги толерира сите овие (проверено спрема кодот):

| Снимач | `track` | `layout` | `meta` | `units` | Канали надвор од табелата |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (бројот на патеката на Forza Motorsport 2023 е `lap.trackOrdinal`) | откриениот распоред на пакетот | `slip: peak`, `discipline: circuit` | само единици на присутните канали | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, часовникот на играта `timestampMs`, `raceTime`, `bestLap`, `lastLap`; брзината во рамката на возилото е под каноничните `latVel`, `vertVel`, `longVel`; `unparsed` покрај каналите |
| Игри Assetto Corsa (`kunos.py`) | од статичната страница, или `null` | отсутно | `slip: scaled`, `discipline: circuit` или `rally` | фиксен список | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (како е испратен), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Рели игри (`rally.py` преку `lapfile.py`) | `null` | отсутно | `discipline: rally`, `slip: null`, `surface` само кога е даден `--surface` (инаку прегледувачот ја заклучува) | само единици на присутните канали | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` за децималните броеви без утврдено име; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` преку `lapfile.py`) | `null` | отсутно | `discipline: circuit` | само единици на присутните канали | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Додаток за Trackmania (CSV) | името на мапата | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` е блокот за возилото на Forza (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), `{"name": ...}` за игрите на Kunos кога статичната страница именува едно, и
`{}` инаку. `lap.metres` е разликата на поминатото растојание на играта за Forza и
збирот на 3D растојанијата меѓу примероците на другите места. Вредностите се заокружуваат при пишување: `time` на 4
децимали, `distance` на 3, другите децимални броеви на 5. JSON се пишува збиено (без празни места).

Секој пакет или страница што снимачот ја примил - не само оние од круговите - се
чува цел покрај датотеките за кругови во `<stamp>_<game>.raw.parquet`, со самопроверка во
`<stamp>_<game>.summary.json` (делот „Completeness“ во README).

Примерок за кој каналот нема вредност - недостасува од таа слика, или не е конечен број
како што го испратила играта - го пишува како `null` секој снимач (`lapfile.clean`), а
дропката за суспензијата изведена од него е исто така `null`. `NaN` и `Infinity` никогаш не
се пишуваат: тие не се JSON, а `JSON.parse` на прегледувачот ја одбива целата датотека поради
еден од нив. Читачот треба да очекува `null` во низата на каналот.

Датотеките на Forza носат `"game": "forza-horizon"`, `"forza-motorsport"` или `"forza"` според
откриениот распоред. Читачот на `.tele.gz` датотеките на FH Companion во прегледувачот создава кругови
со `"game": "forza-horizon"` и `meta.slip = "peak"`; тој читач е во прегледувачот, не
тука. Круговите на iRacing (читани од `.ibt` во прегледувачот) носат `"game": "iracing"`, што не е во
списокот на вредности на `game` од снимачите погоре, бидејќи ниту еден снимач не го пишува.

Видете [Поделба на кругови и етапи](lap-splitting.md) за тоа како се одлучуваат `lap.number`, `lap.seconds` и
`lap.complete`, и [Лизгање, дрифт и изведени канали](slip-and-drift.md) за
тоа што прегледувачот го изведува од овие канали.
