---
title: "EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally"
nav_order: 3
lang: "sr"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # или dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Код: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Тестови: `tests/test_rally.py`, на пакетима састављеним од документованих распореда. **Још није пуштено против живих игара.**

Све оне шаљу UDP који игра укључује из својих сопствених датотека подешавања. Снимач слуша на свим интерфејсима (`0.0.0.0`) на подразумеваном порту игре, осим ако `--port` не даје други: **20777** за `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** за `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Укључивање {#switching-it-on}

Игра чита `Documents\My Games\WRC\telemetry\config.json`. Подразумевани `wrc` структуре `session_update` пакет мора бити укључен према овом рачунару:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (функција `configure_wrc`):

- чита JSON, налази `udp.packets` и унос са `"structure": "wrc"` и `"packet": "session_update"`;
- ако је већ укључен на `127.0.0.1` или `localhost` на порту који се користи, исписује `already on` и ништа не мења;
- иначе поставља `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, и задржава `frequencyHz` уноса (или `-1` ако га нема); ако таквог уноса нема, додаје га;
- пише првобитни текст у `config.json.bak` поред ње, па затим нову датотеку (увучену за 4 размака).

Поново покрените игру после измене датотеке ако је не покупи (није проверено).

### Шта шаље {#what-it-sends}

Подразумевана `wrc` структура је 237 бајтова, little-endian, без заглавља: светски положај, брзина и убрзање (X лево, Y горе, Z напред), јединични вектори аутомобила лево / напред / горе, по точку (задњи лево, задњи десно, предњи лево, предњи десно) висина осовине и вертикална брзина и уздужна брзина контактне површине, температуре кочница, педале после помоћи, управљање (-1 лево, +1 десно), ручна кочница, rpm, брзина и сат деонице, растојање и дужина. Пакет краћи од 237 бајтова се занемарује и пријављује једном.

| Канал | Из |
|---|---|
| `x`, `y`, `z` | светски положај |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | светска брзина пројектована на напред, на минус лево (тако да је позитивно десно), на горе |
| `longAcc`, `latAcc`, `vertAcc` | светско убрзање пројектовано на исти начин |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | како су послати |
| `gear` | `gear_index`; -1 кад је једнак индексу назад, 0 кад је једнак индексу неутрала |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | положај осовине |
| `wheelSurfaceSpeed.*` | уздужна брзина контактне површине |
| `brakeTemp.*` | температура кочнице |

Провера: ако је `speed` изнад 10 и дужина светске брзине се разликује од ње за више од 20%, снимач једном исписује да распоред можда није подразумевана `wrc` структура.

Деоница је **завршена** кад је дужина деонице позитивна и растојање је стигло до дужине минус 0,5 m. Сат који се користи за поделу и за `time` је `stage_time`.

Извори: EA-ов UDP Telemetry Guide v1.3; списак канала које игра пише у `readme/channels.json`; помаци како их декодују nobonobo/obs-codemasters-telemetry и SpaceMonkey. Подразумевани порт игре није документован; снимач користи 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Укључивање {#switching-it-on-1}

Уредите `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally и DiRT 4 такође користе `hardware_settings_config.xml`; њихова тачна фасцикла за та два није проверена овде) тако да `udp` елемент гласи:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` је оно што ставља положаје, точкове и дужину деонице у пакет. Снимач не уређује ову датотеку.

### Шта шаље {#what-it-sends-1}

66 little-endian децималних бројева (DiRT Rally: 64); пакети краћи од 64 броја се занемарују, а пакет од 64 броја се попуњава нулама. Коришћени индекси:

| Индекс | Поље | Канал |
|---|---|---|
| 1 | време деонице (круга) | сат поделе и `time` |
| 2 | растојање круга | `stageDistance` |
| 4-6 | светски положај | `x`, `y`, `z` |
| 7 | брзина | `speed` |
| 8-10 | светска брзина | `longVel` (на напред), `latVel` (на бочни вектор) |
| 11-13 | бочни вектор | |
| 14-16 | вектор напред | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | положај ослонца ЗЛ ЗД ПЛ ПД | `suspensionM.*` |
| 25-28 | брзина контактне закрпе ЗЛ ЗД ПЛ ПД | `wheelSurfaceSpeed.*` |
| 29-33 | гас, управљање, кочница, квачило, брзина | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 или више значи назад, пише се као -1) |
| 34, 35 | бочна, уздужна g-сила | `latAcc`, `longAcc` (пута 9,80665) |
| 37 | rpm / 10 | `rpm` (пута 10) |
| 51-54 | температуре кочница | `brakeTemp.*` |
| 59, 60, 61, 62 | прейђени кругови, укупни кругови, дужина стазе, време последњег круга | подела |

Нема **канала ручне кочнице**. Смер бочног вектора је документован на оба начина, па се знак `latVel` не сме ослањати на (прегледач чита величину угла заношења).

Деоница је **завршена** кад број прейђених кругова порасте изнад своје вредности на почетку деонице (један ралиаркос круг сваки пут кад се то деси), или, за догађај са једним кругом, кад растојање круга стигне 99,9% дужине стазе. Време деонице је последње време круга игре кад је позитивно. Провера: брзина у односу на брзину возила као за EA WRC, са поруком "is extradata set to 3?".

Извори: Codemasters-ов документ за DiRT 4 UDP; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Укључивање {#switching-it-on-2}

У `RichardBurnsRally.ini`, одељак `[NGP]`: `udpTelemetry=1` и крајња тачка (127.0.0.1, порт 6776 осим ако не проследите други `--port`). Снимач не уређује ову датотеку.

### Шта шаље {#what-it-sends-2}

664 бајта (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): сат деонице и растојање до краја, педале, управљање, брзина, светски положај, ставови, сопствене брзине аутомобила (уздужно напред, бочно, вертикално), убрзања, rpm, и четири 128-бајтна блока точкова (LF, RF, LB, RB) са отклоном и силом опруге. Нема брзина точкова.

| Канал | Из |
|---|---|
| `x`, `y`, `z` | положај, осе како су послате, па преуређене (испод) |
| `longVel`, `latVel`, `vertVel` | уздужно, бочно, вертикално |
| `longAcc`, `latAcc` | убрзање x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | како су послати |
| `gear` | `gear - 1` (0 назад, 1 неутрал, 2 прва) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | отклон опруге |
| `wheelLoad.*` | сила опруге |
| `speed` | **израчунато из положаја** преко ±2 узорка, не узето из пакета |

Осе положаја, јединице ставова и јединица брзине RBR-а нису документоване, па се кад се деоница упише: оса по којој деоница најмање варира узима се као вертикална и замењује се у `y` (`orient_up`, потребно најмање 10 узорака), а брзина се поново израчунава из положаја (`speed_from_positions`). Ставови се декодирају али се не пишу, па RBR датотеке немају `yaw`.

Деоница је **завршена** кад сат трке тече и растојање до краја стигне до нуле. Сат је `race_time`.

Извори: NGP-ов `rbr.telemetry.data.TelemetryData.h` преко mika-n/RBRUDPTelemetryLogger и groybe/rbr-udp-telem.

## Деонице {#stages}

Сва пет користе `StageSplitter` на сату деонице игре: деоница се отвара кад сат почне, затвара се као завршена кад игра каже да је аутомобил завршио, а сат који се врати уназад (поновно покретање, или следећа деоница) напушта отворену деоницу - задржава се као датотека `_partial` ако има више од 10 узорака и најмање 300 m. Завршене деонице краће од 300 m се не пишу. Детаљи: [Како се кругови и деонице деле](lap-splitting.md).

## Датотека круга {#the-lap-file}

`game` је `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` или `richard-burns-rally`. `meta` је `{"discipline": "rally", "slip": null}`, плус `"surface": "<value>"` кад је дат `--surface`. `slip` је null јер ниједна од ових игара не шаље клизање гума. Уместо тога, брзина контактне закрпе сваког точка (EA WRC, DiRT) стоји у датотеци, па прегледач из ње и осе аутомобила изводи клизање и угао заношења; видите [Клизање, заношење и изведени канали](slip-and-drift.md). Канали `suspension.*` (0..1 пута који је коришћен) додају се из `suspensionM.*`.

Кад није дат `--surface`, датотека уопште не носи подлогу, намерно: подразумевана вредност која би се овде написала преписала би закључивање прегледача. Прегледач тада узима подлогу из назива деонице или догађаја (асфалтни рели, зимски, Monte као мешовити), иначе из тога како се возило по њој (оштро скретање при малом углу заношења је асфалт), а растресито кад ништа не каже - што рели деоница најчешће јесте. Дајте `--surface` кад знате боље.
