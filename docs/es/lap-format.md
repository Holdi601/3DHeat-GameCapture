---
title: "El archivo heat3d-lap"
nav_order: 9
lang: "es"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# El archivo `heat3d-lap` {#the-heat3d-lap-file}

Cada grabador de telemetría de este repositorio escribe un archivo por vuelta o
tramo, con la misma forma sea cual sea el juego. La exportación de recorridos de
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) lo lee para
encontrar el juego, el nivel y la trazada. Cualquier cosa que lea JSON puede
leerlo.

![Los campos y canales de un archivo de vuelta escrito a partir de una señal sintética de Forza](../assets/img/lap-file.svg)

## El documento {#the-document}

Un objeto JSON. Los canales se guardan como columnas: un array por canal, todos
de la misma longitud, una entrada por muestra.

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

| Campo | Significado |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | de qué juego es la vuelta; ver la lista de abajo |
| `track` | el nombre del circuito, tramo o mapa, cuando el juego lo envía |
| `layout` | solo Forza: qué diseño de paquete Data Out se decodificó |
| `car` | lo que el juego diga del coche; de forma libre |
| `lap` | el número de la vuelta, su tiempo tal como lo contó el juego (o la duración de las muestras), si se terminó y su longitud |
| `meta` | cómo leer los números; ver más abajo |
| `units` | la unidad de cada canal presente, para un lector que no conozca la tabla de abajo |
| `channels` | las muestras |
| `unparsed` | solo Forza, cuando el paquete tiene bytes que ningún campo nombra: `ranges` (sus desplazamientos `[inicio, fin)` en bytes dentro del paquete) y `hex` (por muestra, esos bytes en hexadecimal), de modo que el archivo por sí solo contiene el paquete entero |

`game` es uno de `forza-horizon`, `forza-motorsport`, `forza` (diseño de paquete
no distinguido), `assetto-corsa`, `assetto-corsa-competizione`,
`assetto-corsa-evo`, `assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`,
`dirt-rally`, `dirt-4`, `richard-burns-rally`, `beamng`, `trackmania`.

`meta` indica qué significan los números cuando los juegos difieren:

- `slip`: qué contienen los canales de deslizamiento, cuando el juego envía alguno:
  `peak` (normalizado, así que por encima de 1 el neumático pierde agarre: Forza),
  `scaled` (un deslizamiento físico dividido por un pico típico de asfalto: los
  juegos de Assetto Corsa), `physical` (una fracción y radianes), `index` (una
  medida de deslizamiento de 0..1: Trackmania);
- `discipline`: `circuit`, `rally` o `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` o `mixed`, cuando se conoce (los
  grabadores de rally la toman de `--surface`).

## Canales {#channels}

Un canal que el juego no envía está ausente, nunca se rellena con ceros. Los
canales por rueda llevan la rueda tras un punto: `.FL`, `.FR`, `.RL`, `.RR`.

Las posiciones son el mundo del juego, en metros, con `y` hacia arriba. Un juego
cuyo mundo es Z hacia arriba lo gira a Y hacia arriba su grabador; no se cambia
nada más, así que un mundo zurdo (el de Forza) sigue siendo zurdo.

| Canal | Unidad | Significado |
|---|---|---|
| `time` | s | desde la primera muestra de la vuelta |
| `distance` | m | a lo largo de la trayectoria recorrida desde la primera muestra |
| `x`, `y`, `z` | m | posición; `y` es la altura |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedales y palanca |
| `steer` | -1..1 | positivo a la derecha |
| `gear` | | como lo cuenta el juego |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | marco del coche |
| `yaw`, `pitch`, `roll` | rad | rumbo y actitud |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | velocidad en el marco del coche: derecha, adelante, arriba |
| `bodySlip` | rad | ángulo de deriva, cuando el juego lo envía |
| `loose` | 0/1 | sobre suelo suelto (Trackmania) |
| `airborne` | 0/1 | ninguna rueda en el suelo |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | como los envía el juego |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | ayudas actuando, sistemas activos |
| `absLevel`, `tcLevel` | | ajustes de ayudas |
| `brakeBias` | 0..1 | parte delantera |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | por rueda |
| `tirePressure` | psi | por rueda |
| `tireWear` | 0..1 | por rueda |
| `slipRatio`, `slipAngle`, `combinedSlip` | ver `meta.slip` | por rueda |
| `slipIndex` | 0..1 | medida de deslizamiento por rueda (Trackmania) |
| `camber` | rad | por rueda |
| `brakeTemp` | °C | por rueda |
| `padLife`, `discLife` | | por rueda |
| `suspensionM` | m | recorrido de la suspensión por rueda |
| `suspension` | 0..1 | recorrido de la suspensión por rueda, del rango que usó esta vuelta |
| `wheelLoad` | N | por rueda |
| `wheelSpeed` | rad/s | rotación de la rueda |
| `wheelSurfaceSpeed` | m/s | velocidad del punto de contacto de la rueda |
| `groundContact` | 0/1 | por rueda |
| `rumble`, `surfaceRumble` | | por rueda: sobre una banda sonora; la banda sonora de la superficie |
| `puddle` | | por rueda: profundidad del agua encharcada |

Un grabador puede añadir canales propios con otros nombres; un lector conserva
los que no conoce.

Ninguno de los juegos de rally envía deslizamiento de neumáticos. Un lector
puede calcularlo a partir de la velocidad del punto de contacto o de la
superficie de cada rueda frente a la velocidad del coche,
`(rueda - coche) / coche`, o a partir de su rotación y de un radio de rodadura
medido en la propia vuelta cuando solo se envía la rotación. El ángulo de deriva
sale de la velocidad propia del coche (`latVel`, `longVel`) cuando se envía, o de
la velocidad del mundo proyectada sobre los ejes del coche.

## El formato CSV {#the-csv-form}

El complemento de Trackmania escribe en cambio `heat3d-lap-csv`: una primera
línea con `# ` y un objeto JSON (`format`, `version`, `game`, `track`,
`complete`, `seconds`, `meta`), una línea con los nombres de los canales y luego
una línea por muestra. Los nombres de los canales son los mismos de arriba.

## Lo que escribe cada grabador {#what-each-recorder-actually-writes}

El formato de arriba es el contrato; los grabadores lo rellenan de forma algo
distinta, y un lector debe tolerar todas estas variantes (comprobado con el código):

| Grabador | `track` | `layout` | `meta` | `units` | Canales más allá de la tabla |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (el número de circuito de Forza Motorsport 2023 es `lap.trackOrdinal`) | el diseño de paquete detectado | `slip: peak`, `discipline: circuit` | solo las unidades de los canales presentes | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, el reloj del juego `timestampMs`, `raceTime`, `bestLap`, `lastLap`; la velocidad local del coche va en los canónicos `latVel`, `vertVel`, `longVel`; `unparsed` junto a los canales |
| Juegos de Assetto Corsa (`kunos.py`) | de la página estática, o `null` | ausente | `slip: scaled`, `discipline: circuit` o `rally` | una lista fija | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (como se envía), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Juegos de rally (`rally.py` vía `lapfile.py`) | `null` | ausente | `discipline: rally`, `slip: null`, `surface` solo cuando se dio `--surface` (si no, el visor lo deduce) | solo las unidades de los canales presentes | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` para los flotantes sin nombre fijo; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` vía `lapfile.py`) | `null` | ausente | `discipline: circuit` | solo las unidades de los canales presentes | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Complemento de Trackmania (CSV) | el nombre del mapa | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` es el bloque de coche de Forza (`carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`), `{"name": ...}` para los juegos
Kunos cuando la página estática nombra un coche, y `{}` en otro caso.
`lap.metres` es la diferencia de distancia recorrida del contador de Forza, y en
los demás la suma de las distancias 3D entre muestras. Los valores se redondean
al escribir: `time` a 4 decimales, `distance` a 3, los demás flotantes a 5. El
JSON se escribe compacto (sin espacios).

Cada paquete o página que recibe el grabador, no solo los de las vueltas, se
guarda completo junto a los archivos de vuelta en `<stamp>_<game>.raw.parquet`,
con una autocomprobación en `<stamp>_<game>.summary.json` (la sección
"Completeness" del README).

Una muestra para la que un canal no tiene valor (que falta en ese fotograma, o
que no es un número finito tal como lo envió el juego) la escribe como `null`
todo grabador (`lapfile.clean`), y la fracción de suspensión derivada de ella
también es `null`. `NaN` e `Infinity` nunca se escriben: no son JSON, y el
`JSON.parse` de un navegador rechaza el archivo entero por culpa de uno de ellos.
Un lector debe esperar `null` dentro del array de un canal.

Los archivos de Forza llevan `"game": "forza-horizon"`, `"forza-motorsport"` o
`"forza"` según el diseño detectado. El lector del visor para los archivos
`.tele.gz` de FH Companion produce vueltas con `"game": "forza-horizon"` y
`meta.slip = "peak"`; ese lector está en el visor, no aquí. Las vueltas de
iRacing (leídas de `.ibt` en el visor) llevan `"game": "iracing"`, que no está en
la lista de valores de `game` de los grabadores porque ningún grabador lo escribe.

Ver [División de vueltas y tramos](lap-splitting.md) para saber cómo se deciden
`lap.number`, `lap.seconds` y `lap.complete`, y
[Deslizamiento, deriva y canales derivados](slip-and-drift.md) para lo que el
visor deriva de estos canales.
