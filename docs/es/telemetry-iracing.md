---
title: "iRacing"
nav_order: 6
lang: "es"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **no necesita grabador**. El simulador escribe sus propios archivos de telemetría, `.ibt`, cuando el registro de telemetría está activo (Alt+L en el coche): la sesión completa a 60 Hz, con todos los canales que expone el simulador, y la descripción YAML de la sesión junto a ellos. Arrastra el archivo `.ibt` a la pestaña **Análisis de carrera** del visor.

El lector está en el visor, no en este repositorio (`src/race/ibt.ts` en el visor de 3DHeat). Se prueba con un archivo sintético; se documenta aquí porque es la mitad de iRacing de la misma historia de grabación de vueltas.

## Qué contiene el archivo y cómo se lee {#what-the-file-holds-and-how-it-is-read}

El archivo es el diseño de memoria documentado del simulador escrito en disco:

| Parte | Tamaño | Contiene |
|---|---|---|
| Cabecera | 112 bytes | versión, frecuencia de muestreo, dónde están el YAML y la tabla de variables, la longitud de una fila de muestra, dónde empiezan las filas |
| Subcabecera de disco | 32 bytes | fecha y hora de inicio, número de vueltas, número de filas |
| Tabla de variables | 144 bytes por canal | tipo, desplazamiento en la fila, cantidad, nombre, descripción, unidad |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Filas | una por tick | |

Un archivo se rechaza cuando tiene menos de 144 bytes, cuando su cabecera no es coherente (sin variables, una tabla de variables fuera del archivo, una longitud de fila cero), cuando le falta alguno de `SessionTime`, `Lap`, `Lat`, `Lon`, o cuando ninguna muestra tiene una posición válida.

## Posición {#position}

iRacing informa de latitud, longitud y altitud, no de una posición en el marco propio del circuito. Las posiciones se expresan en metros sobre un plano tangente en la primera muestra con posición válida (radio de la Tierra 6.371.008,8 m): `x` hacia el este, `z` hacia el sur, `y` la altitud. Así, vista desde arriba con el rumbo por defecto de la cámara del visor, el norte queda hacia arriba en la pantalla.

## Vueltas {#laps}

La sesión se divide según el contador `Lap` del simulador. Una vuelta se conserva solo si tiene más de 60 muestras, empieza por debajo del 5 % de la distancia de vuelta (`LapDistPct`) y termina por encima del 95 %; es decir, vueltas de línea a línea. Si ninguna vuelta cumple, el archivo se rechaza con un mensaje que indica la longitud del circuito del YAML. `distance` es `LapDist` referido al inicio de la vuelta, o la distancia recorrida según las posiciones cuando falta `LapDist`; `time` es `SessionTime` desde el inicio de la vuelta.

## Canales {#channels}

| iRacing | Canal | Conversión |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | ninguna |
| `Clutch` | `clutch` | `1 - value` (iRacing cuenta el embrague como accionado; el canal es el pedal) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radianes, positivo en sentido antihorario, a -1..1 con positivo a la derecha; pi cuando falta el máximo) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | ninguna |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | ninguna |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | ajustes de ayudas |
| `dcBrakeBias` | `brakeBias` | se divide entre 100 cuando es superior a 1,5 (un porcentaje en algunos coches) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura de la carcasa en el centro |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa por 0,145038, a psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Cada otro canal con un valor por muestra (y que no sea un único byte) se pasa con su propio nombre, con el prefijo de rueda (`LF`, `RF`, `LR`, `RR`) convertido en sufijo (`.FL`, `.FR`, `.RL`, `.RR`), para que las gráficas del visor lo ofrezcan sin que nadie lo describa.

El coche sale de `DriverInfo`: la entrada cuyo `CarIdx` coincide con `DriverCarIdx` da `CarScreenName`, `CarID` y `CarClassShortName`. El circuito es `TrackDisplayName` (o `TrackName`).

## Lo que iRacing no da {#what-iracing-does-not-give}

No se registra deslizamiento de neumáticos, así que no hay canales de deslizamiento. El ángulo de deriva se deriva de la velocidad de guiñada frente a la trayectoria (véase [Deslizamiento, deriva y canales derivados](slip-and-drift.md)). Los modelos de circuito vienen en un formato protegido y no son un objetivo de extracción de archivos (véase [Juegos](games.md)).
