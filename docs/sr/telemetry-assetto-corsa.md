---
title: "Assetto Corsa игре"
nav_order: 2
lang: "sr"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO и AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Код: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Тестови: `tests/test_kunos.py` (синтетичке странице). Још није пуштено против живих игара.

## Одакле долазе подаци {#where-the-data-comes-from}

Kunos-ове игре објављују телеметрију за апликације као **именоване Windows странице дељене меморије** које игра пише а свако може да чита. Снимач их отвара само за читање (`mmap` са ознаком имена), па **мора да ради на рачунару на којем игра ради**, на Windows-у; другде излази уз поруку.

Странице се отварају једном, кад снимач почне. Прво покренути игру и ући у аутомобил је безбедан редослед; да ли покретање снимача пре игре ради, није проверено.

| `--game` | Страница физике | Графичка страница (бројач кругова) | Статичка страница (називи) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | не користи се | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | не користи се | `Local\acevo_pmf_static` |

Страница физике се чита 200 пута у секунди (`hz=200`); нови узорак се узима само кад се њен `packetId` промени и није нула. Првих 800 бајтова странице физике имају исти распоред у сва четири игре; страница прве игре је зајамчена само на 580 бајтова, па ако се мапирање од 800 бајтова не може отворити, снимач се враћа на 580 и поља иза тога нису присутна.

## Положај {#position}

Ниједна страница не носи положај аутомобила као такав, али страница физике држи **тачку додира сваке гуме са светом** у светским координатама (помак 420, четири XYZ тројке). Положај аутомобила је средина од четири. Страница чије су све тачке додира нуле (мени, гаража) не даје узорак.

## Канали {#channels}

| Канал | Из | Напомене |
|---|---|---|
| `time` | сопствени сат снимача | секунде од почетка снимања, поново постављене на први узорак круга |
| `x`, `y`, `z` | средина тачака додира гума | светски метри |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | јединице игре, скалиране по кругу на -1..1 највећом апсолутном вредношћу коју је круг користио, **само ако** та вредност прелази 1,05 (улаз који је већ у -1..1 се не мења) |
| `gear` | `gear - 1` | игра броји 0 назад, 1 неутрал, 2 прва; пише се као -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, пута 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | локална брзина на помаку 568 | оквир аутомобила; само кад није нула. Страна у коју показује x документована је на оба начина, па читајте величину угла заношења, не његов знак |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | помак 564 | само страница од 800 бајтова |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: помаци 204 и 252, пише се 1 кад је изнад 0; AC: `tcInAction`/`absInAction` са странице од 800 бајтова кад постоји | помоћни системи у раду |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | изведено | 0..1 пута који је овај круг користио (најмање до највеће вредности `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | помаци 640, 656 (страница од 800 бајтова) | подељено типичним врхом - видите испод |
| `slipRatioRaw.*`, `slipAngleRaw.*` | исто | физичке вредности, нескалиране |
| `padLife.*`, `discLife.*` | помаци 740, 756 | само страница од 800 бајтова |

AC Rally шаље своје температуре гума и кочница у келвинима: за `--game acrally`, од било које од тих вредности већих од 200 одузима се 273,15.

`wheelSlip` (помак 56) се декодира али се не пише.

## Скалирање клизања {#slip-scaling}

Forza шаље клизање нормализовано тако да је 1 ивица вуче. Kunos шаље физички однос клизања и угао клизања. Зато снимач дели их типичним врхом на асфалту - **0,12** за однос клизања и **0,14 rad (око 8 степени)** за угао клизања - да "преко 1 значи клизање" прегледача приближно важи, чува сирове вредности уз њих, и пише `"meta": {"slip": "scaled"}`. Где вуча стварно престаје, прегледач мери по аутомобилу из самих кругова. Видите [Клизање, заношење и изведени канали](slip-and-drift.md).

## Кругови {#laps}

- **AC и ACC** броје кругове на графичкој страници (`completedLaps` на помаку 132, време последњег круга у милисекундама на 144). `CounterSplitter` затвара круг кад се бројач промени; означава се као завршен, са временом игре, само ако је бројач порастао тачно за један.
- **AC EVO и AC Rally** се не читају за кругове (графичка страница EVO-а је другачији, већи распоред; AC Rally вози деонице). `LineSplitter` користи место где је снимање почело као линију: круг се затвара кад аутомобил следећи пут прође најближе њој идући истим смером, а деоница или било која вожња се затвара кад аутомобил стоји 8 секунди.

Детаљи и прагови: [Како се кругови и деонице деле](lap-splitting.md).

## Називи стаза и аутомобила {#track-and-car-names}

Чита се једном, са статичке странице, кад стигне први узорак: за AC, ACC и AC Rally аутомобил (UTF-16, помак 68) и стаза (помак 134); за AC EVO стаза и њена конфигурација (једнобајтни текст на помацима 136 и 169, спојени размаком) и без аутомобила. Иду у датотеку као `track` и `car: {"name": ...}`.

## Датотека круга {#the-lap-file}

`game` је `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` или `assetto-corsa-rally`; `meta` је `{"slip": "scaled", "discipline": "rally"}` за AC Rally и `{"slip": "scaled", "discipline": "circuit"}` за остале три. `surface` се не пише.

## Извори {#sources}

AC1 SDK за дељену меморију; документација ACC дељене меморије (v1.8); распоред AC EVO-а како је измерен у `albertowd/live-telemetry-evo`; распоред AC Rally-ја како га чита `LuizZak/AssettoCorsaRallyTelemetryReader`. Видите [Игре](games.md).
