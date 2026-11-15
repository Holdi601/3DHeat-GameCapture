---
title: "Датотека `heat3d-lap`"
nav_order: 9
lang: "sr"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# Датотека `heat3d-lap` {#the-heat3d-lap-file}

Сваки снимач телеметрије у овом репозиторијуму записује по једну датотеку за круг или деоницу, истог облика без обзира на игру. Извоз стазе у [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) чита је да би нашао игру, ниво и возну линију. Све што чита JSON може да је прочита.

![Поља и канали датотеке круга записане из синтетичког Forza тока](../assets/img/lap-file.svg)

## Документ {#the-document}

Један JSON објекат. Канали се чувају као колоне: по један низ за сваки канал, сви исте дужине, по један унос за сваки узорак.

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

| Поље | Значење |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | из које је игре круг; видите списак испод |
| `track` | назив стазе, деонице или мапе, кад игра то пошаље |
| `layout` | само Forza: који распоред Data Out пакета је декодован |
| `car` | све што игра каже о аутомобилу; слободан облик |
| `lap` | број круга, његово време како га је игра бројала (или распон узорака), да ли је завршен и његова дужина |
| `meta` | како се читају бројеви; видите испод |
| `units` | јединица сваког присутног канала, за читач који не зна табелу испод |
| `channels` | узорци |
| `unparsed` | само Forza, кад пакет има бајтове без назива поља: `ranges` (њихови помаци `[почетак, крај)` у пакету) и `hex` (по узорку, ти бајтови као хекс), па датотека сама садржи цео пакет |

`game` је једна од вредности `forza-horizon`, `forza-motorsport`, `forza` (распоред пакета није разликован), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` каже шта значе бројеви тамо где се игре разликују:

- `slip`: шта канали клизања садрже, тамо где игра шаље било шта - `peak` (нормализовано, па је пређено 1 гума пушта: Forza), `scaled` (физичко клизање подељено типичним вршним вредностима на асфалту: игре Assetto Corsa), `physical` (део и радијани), `index` (мера клизања од 0..1: Trackmania);
- `discipline`: `circuit` (стаза), `rally` (рели) или `arcade` (аркада);
- `surface`: `tarmac` (асфалт), `loose` (растресено), `snow` (снег), `ice` (лед) или `mixed` (мешовито), кад је познато (рели снимачи га узимају из `--surface`).

## Канали {#channels}

Канал који игра не шаље је одсутан, никад попуњен нулама. Канали по точку носе точак иза тачке: `.FL`, `.FR`, `.RL`, `.RR`.

Положаји су светски систем игре, у метрима, са `y` горе. Игра чији је светски систем Z-горе окреће је на Y-горе њен снимач; ништа друго се не мења, па леворуки свет (Forza-ин) остаје леворуки.

| Канал | Јединица | Значење |
|---|---|---|
| `time` | s | од првог узорка круга |
| `distance` | m | дуж пређене путање од првог узорка |
| `x`, `y`, `z` | m | положај; `y` је висина |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | педале и полуга |
| `steer` | -1..1 | позитивно десно |
| `gear` | | како их игра броји |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | оквир аутомобила |
| `yaw`, `pitch`, `roll` | rad | правац и став |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | брзина у оквиру аутомобила: десно, напред, горе |
| `bodySlip` | rad | угао заношења, тамо где игра шаље |
| `loose` | 0/1 | на растреситом тлу (Trackmania) |
| `airborne` | 0/1 | ниједан точак не додирује тло |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | како их игра шаље |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | помоћни системи у раду, укључени |
| `absLevel`, `tcLevel` | | подешавања помоћи |
| `brakeBias` | 0..1 | предњи удео |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | по точку |
| `tirePressure` | psi | по точку |
| `tireWear` | 0..1 | по точку |
| `slipRatio`, `slipAngle`, `combinedSlip` | видите `meta.slip` | по точку |
| `slipIndex` | 0..1 | по точку, мера клизања (Trackmania) |
| `camber` | rad | по точку |
| `brakeTemp` | °C | по точку |
| `padLife`, `discLife` | | по точку |
| `suspensionM` | m | по точку, пут ослонца |
| `suspension` | 0..1 | по точку, пут ослонца, у опсегу који је овај круг користио |
| `wheelLoad` | N | по точку |
| `wheelSpeed` | rad/s | по точку, ротација |
| `wheelSurfaceSpeed` | m/s | по точку, брзина контактне површине |
| `groundContact` | 0/1 | по точку |
| `rumble`, `surfaceRumble` | | по точку: на траци за ударање; рижање површине |
| `puddle` | | по точку, дубина стајаће воде |

Снимач може да дода сопствене канале под другим називима; читач задржава оно што не познаје.

Ниједна рели игра не шаље клизање гума. Читач га може израчунати из брзине контактне површине или точка у односу на брзину аутомобила, `(точак - аутомобил) / аутомобил`, или из ротације и полупречника котрљања измереног на самом кругу где се шаље само ротација. Угао заношења долази из сопствене брзине аутомобила (`latVel`, `longVel`) где се шаље, или из светске брзине пројектоване на осе аутомобила.

## CSV облик {#the-csv-form}

Trackmania додатак уместо тога пише `heat3d-lap-csv`: први ред је `# ` и JSON објекат (`format`, `version`, `game`, `track`, `complete`, `seconds`, `meta`), ред са називима канала, па по један ред за сваки узорак. Називи канала су исти као горе.

## Шта сваки снимач заиста записује {#what-each-recorder-actually-writes}

Облик изнад је уговор; снимачи га попуњавају помало различито, а читач треба да поднесе све ово (проверено према коду):

| Снимач | `track` | `layout` | `meta` | `units` | Канали изван табеле |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (број стазе Forza Motorsport 2023 је `lap.trackOrdinal`) | откривени распоред пакета | `slip: peak`, `discipline: circuit` | само јединице присутних канала | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, игров сат `timestampMs`, `raceTime`, `bestLap`, `lastLap`; брзина у оквиру аутомобила је под каноничким `latVel`, `vertVel`, `longVel`; `unparsed` уз канале |
| Игре Assetto Corsa (`kunos.py`) | са статичке странице, или `null` | нема | `slip: scaled`, `discipline: circuit` или `rally` | фиксна листа | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (како је послат), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Рели игре (`rally.py` преко `lapfile.py`) | `null` | нема | `discipline: rally`, `slip: null`, `surface` само кад је дат `--surface` (иначе га прегледач закључује) | само јединице присутних канала | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` за бројеве без устаљеног назива; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` преко `lapfile.py`) | `null` | нема | `discipline: circuit` | само јединице присутних канала | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania додатак (CSV) | назив мапе | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` је блок аутомобила Forza-е (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` за игре Kunos кад статичка страница назове аутомобил, а иначе `{}`. `lap.metres` је за Forza разлика пређене дистанце коју јавља игра, а за остале збир 3D растојања између узорака. Вредности се заокружују при уписивању: `time` на 4 децимале, `distance` на 3, остали децимални бројеви на 5. JSON се пише збијено (без размака).

Сваки пакет или страница коју је снимач примио - не само они од кругова - чува се цела уз датотеке круга, у `<stamp>_<game>.raw.parquet`, са самопровером у `<stamp>_<game>.summary.json` (одељак "Completeness" у README-у).

Узорак за који канал нема вредност - недостаје у том кадру или није коначан број како га је игра послала - записује сваки снимач као `null` (`lapfile.clean`), а део ослонца изведен из њега је такође `null`. `NaN` и `Infinity` се никад не записују: нису JSON, а `JSON.parse` у прегледачу одбија целу датотеку због једног од њих. Читач треба да очекује `null` унутар низа канала.

Forza датотеке носе `"game": "forza-horizon"`, `"forza-motorsport"` или `"forza"` према откривеном распореду. Читач прегледача за `.tele.gz` датотеке FH Companion-а прави кругове са `"game": "forza-horizon"` и `meta.slip = "peak"`; тај читач је у прегледачу, не овде. iRacing кругови (читају се из `.ibt` у прегледачу) носе `"game": "iracing"`, што није на списку вредности `game` снимача горе, јер га ниједан снимач не пише.

Видите [Подела на кругове и деонице](lap-splitting.md) за то како се одлучују `lap.number`, `lap.seconds` и `lap.complete`, и [Клизање, заношење и изведени канали](slip-and-drift.md) за оно што прегледач изводи из ових канала.
