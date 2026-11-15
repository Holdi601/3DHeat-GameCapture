---
title: "Forza"
nav_order: 1
lang: es
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon y Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # juego -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # y FH Companion sigue funcionando
```

Código: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(detección del diseño),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(todos los canales, archivos de vuelta, reenvío).

## Activarlo en el juego {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, puerto `5300` (o el que pases
como `--port`). Forza Motorsport también ofrece un formato de paquete: debe ser **Dash**, no Sled. Sled
no lleva ninguna posición, y el grabador lo rechaza.

El grabador se enlaza a `127.0.0.1`, así que el juego tiene que correr en el mismo PC.

## Qué envía el juego, y cómo se encuentra el diseño {#what-the-game-sends-and-how-the-layout-is-found}

Data Out es un paquete UDP por cada tick de simulación (unos 60 por segundo), una estructura C plana
little-endian de estos tamaños:

| Longitud | Variante |
|---|---|
| 232 bytes | Motorsport "Sled": sin posición. Se rechaza con un mensaje que te pide cambiar a Dash. |
| 311 bytes | Motorsport "Dash": el bloque Sled más el bloque dash de 79 bytes |
| 324 bytes | Horizon "Dash": lo mismo con relleno entre los dos bloques |
| 331 bytes | Forza Motorsport (2023): Dash más 20 bytes de desgaste de neumáticos y el id del circuito |

El bloque Sled (desplazamientos 0-231) es estable. Dónde empieza el bloque dash en la variante Horizon
se describe de forma inconsistente en las fuentes publicadas, y adivinar mal no falla - produce
flotantes plausibles de los campos equivocados. Así que el inicio se **descubre**:

1. Los inicios candidatos se prueban en orden: `longitud - 79` (el bloque dash llega al último byte en
   todas las variantes documentadas), 232, 244, y de 232 a 260 en pasos de 4.
2. Cada candidato se puntúa con paquetes de un coche en movimiento (una componente de velocidad por
   encima de 1 m/s): el vector de velocidad del bloque Sled y el escalar `Speed` del bloque dash son la
   misma magnitud en dos sitios, así que `| |velocidad| - Speed |` está cerca de cero solo para el
   inicio correcto.
3. Gana el candidato con la menor discrepancia en el peor caso, si esa discrepancia es como máximo de
   **1 m/s**. Si no, la detección sigue esperando.

Mientras el coche está aparcado, todos los candidatos leen cero y coinciden, lo que no demuestra nada,
así que **la detección espera a que el coche se mueva**: conduce unos metros antes de esperar salida.
Mientras espera se retienen hasta 600 paquetes (recortados a los últimos 300). Una vez conocido el
diseño, también se decodifican los paquetes retenidos, así que no se pierde el inicio de la primera
vuelta. Los paquetes de una longitud distinta del diseño detectado, los paquetes de menos de 311 bytes
y los paquetes con una posición o velocidad no finita se ignoran para los archivos de vuelta.

Qué Forza es se deduce del diseño: un diseño Horizon da `"game": "forza-horizon"`, un diseño Motorsport
o de 331 bytes da `"forza-motorsport"`, cualquier otro `"forza"`. El nombre del diseño detectado
(`Horizon dash`, `Motorsport dash`, `331-byte dash`) se escribe como `layout`.

## Canales grabados {#channels-recorded}

Cada campo del paquete se decodifica (`decode_full`) y se convierte:

- los pedales `throttle`, `brake`, `clutch`, `handbrake` pasan de 0..255 a 0..1;
- `steer` pasa de -127..127 a -1..1; `drivingLine` y `aiBrakeDifference` igual, divididos por 127;
- `tireTemp.FL` ... `.RR` pasan de Fahrenheit a Celsius;
- `latAcc`, `longAcc`, `vertAcc` y `yawRate` son copias de `accelX`, `accelZ`, `accelY` y `angVelY` con
  los nombres canónicos (marco del coche: x a la derecha, y arriba, z hacia delante);
- la velocidad del Sled, que está en el marco propio del coche (x a la derecha, y arriba, z hacia
  delante - no el del mundo), se escribe directamente bajo los nombres canónicos `latVel`, `vertVel` y
  `longVel`, para que el visor lea el ángulo de deriva de ahí en lugar de estimarlo a partir del rumbo y
  la trayectoria.

Los canales del archivo de vuelta son todos estos salvo los campos por vuelta:

| Grupo | Canales |
|---|---|
| Tiempo y lugar | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Movimiento | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Conductor | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Por rueda (`.FL .FR .RL .RR`) | `suspension` (0 estirada .. 1 comprimida), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizados: por encima de 1 el neumático pierde agarre), `wheelSpeed` (rad/s), `rumble` (sobre una banda sonora), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Solo Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` es el cronómetro de vuelta del juego menos su valor en la primera muestra de la vuelta; `distance`
es la distancia recorrida del juego menos su primer valor. Las posiciones son las coordenadas del mundo de
Forza en metros, sin cambios (y es hacia arriba; el mundo es zurdo).

Una vez por vuelta, y no por muestra, bajo `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`,
`cylinders`, `rpmMax`, `rpmIdle`. El id del circuito de FM2023 también se guarda una vez, como
`lap.trackOrdinal`. No se guarda por muestra `isRaceOn` (1 en cada fotograma de una vuelta). `timestampMs`,
`raceTime`, `bestLap` y `lastLap` sí se guardan como canales.

El resto del documento se rellena como en cualquier otro grabador:

- `"track": null` - Forza Horizon no nombra el recorrido, y Forza Motorsport solo le pone un número;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - los canales de deslizamiento están normalizados
  para que por encima de 1 el neumático pierda agarre;
- `units` lista solo los canales que tiene el archivo (los de por rueda, por su nombre base);
- un valor que no es un número finito se escribe como `null`, nunca como `NaN`.

Ver [El archivo heat3d-lap](lap-format.md).

## Cómo se dividen las vueltas {#how-laps-are-split}

`LapSplitter` (ver [Cómo se dividen las vueltas y los tramos](lap-splitting.md)): una vuelta se cierra
cuando el contador de vueltas del juego avanza, y su tiempo es entonces el `lastLap` propio del juego
(lo que muestra el juego). Una carrera de punto a punto o una sesión que termina a mitad de vuelta se
cierra cuando el juego sale de la carrera (cae `isRaceOn`), cuando los paquetes se paran durante 2
segundos, o cuando el sello de tiempo del juego retrocede; se guarda como `run` si cubrió al menos 400 m.

## Reenvío a FH Companion {#relaying-to-fh-companion}

El juego envía Data Out a una sola dirección. Con `--forward host:port`, el grabador pasa **cada paquete
que recibe sin cambios**, antes de decodificar nada (también mientras todavía espera a detectar el diseño),
para que otra aplicación que lea el flujo siga funcionando: pon el juego en 5300, la otra aplicación en
5301, y ejecuta con `--forward 127.0.0.1:5301`.

FH Companion es una aplicación aparte, no parte de 3DHeat. Mantiene una biblioteca de vueltas en
`%LOCALAPPDATA%\FHCompanion\laps`: una carpeta por recorrido, un archivo de vuelta por vuelta muestreado
cada cinco metros aproximadamente, y junto a cada archivo de vuelta `<lap>.json.tele.gz`, todo el Data Out
de la vuelta a la velocidad del juego. 3DHeat lee ambos:

- **El visor lee `.tele.gz` directamente** cuando lo sueltas (con o sin su archivo de vuelta) en la pestaña
  Análisis de carrera. Asigna los nombres de campo propios de Forza (`PositionX`, `VelocityX`, `TireSlipRatio`
  + rueda, ...) a los canales canónicos, convierte las `VelocityX/Y/Z` locales del coche en `latVel`,
  `vertVel`, `longVel`, convierte las temperaturas de neumáticos desde Fahrenheit, descarta las filas que
  repiten la anterior salvo por el reloj del grabador, y marca el deslizamiento como `peak`. Si además se
  le da el archivo de vuelta, la vuelta toma de él el coche y el tiempo. Este lector está en el visor
  (`src/race/adapters.ts`, `readForzaTelemetry`), no en este repositorio.
- **El comando `laps`** lee la biblioteca de vueltas y escribe la ruta de un recorrido y un CSV con cada
  muestra; ver [Referencia de comandos](commands.md#laps).

## Otros usos del mismo flujo {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` graba solo las posiciones, guardadas cada un par de segundos mientras
  se conduce; ver [Referencia de comandos](commands.md#route).
- La opción "Racing telemetry (Forza)" de la ventana de escaneo usa el flujo como poses exactas de la
  cámara para la reconstrucción; ver [Pose de la cámara y escala](reconstruction-pose.md#telemetry-poses).

## Notas y advertencias {#notes-and-caveats}

- Cómo normaliza Forza su deslizamiento no está documentado. Se lee `1` como el borde del agarre, pero el
  visor mide dónde pierde agarre realmente cada coche.
- La velocidad del Sled es local al coche, como dice la documentación de Data Out de Forza y confirman las
  vueltas grabadas (su componente hacia delante lleva la velocidad, la lateral se queda cerca de cero). La
  detección del diseño usa solo su longitud, que es la misma en cualquier marco.
- Las posiciones son el mundo del juego, Y hacia arriba y zurdo. Los sentidos de `yaw`, `pitch` y `roll` se
  comprobaron en vueltas grabadas: la guiñada es igual a la dirección de marcha `atan2(dx, dz)`, un cabeceo
  positivo es morro abajo, y un alabeo positivo baja el lado derecho.
