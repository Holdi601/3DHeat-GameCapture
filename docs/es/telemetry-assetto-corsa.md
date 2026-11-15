---
title: "Juegos de Assetto Corsa"
nav_order: 2
lang: es
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO y AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Código: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Pruebas: `tests/test_kunos.py` (páginas sintéticas). Todavía no se ha ejecutado contra los juegos reales.

## De dónde vienen los datos {#where-the-data-comes-from}

Los juegos de Kunos publican telemetría para aplicaciones como **páginas de memoria compartida de
Windows con nombre** que el juego escribe y que cualquiera puede leer. El grabador las abre en modo
de solo lectura (`mmap` con un nombre de etiqueta), así que debe ejecutarse **en el PC donde corre
el juego**, en Windows; en otro sitio sale con un mensaje. Las páginas se abren una sola vez, al
arrancar el grabador. El orden seguro es arrancar el juego y entrar primero en el coche; no se ha
comprobado si arrancar el grabador antes que el juego funciona.

| `--game` | Página de física | Página gráfica (contador de vueltas) | Página estática (nombres) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | no se usa | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | no se usa | `Local\acevo_pmf_static` |

La página de física se lee 200 veces por segundo (`hz=200`); se toma una muestra nueva solo cuando
su `packetId` ha cambiado y no es cero. Los primeros 800 bytes de la página de física comparten un
mismo diseño en los cuatro juegos; la página de física de AC1 solo garantiza 580 bytes, así que si
no se puede abrir una asignación de 800 bytes, el grabador recurre a 580 y los campos más allá de
ellos faltan.

## Posición {#position}

Ninguna de las páginas lleva una posición del coche como tal, pero la página de física guarda **el
punto de contacto de cada neumático en coordenadas del mundo** (desplazamiento 420, cuatro ternas
XYZ). La posición del coche es la media de los cuatro. Una página cuyos puntos de contacto son todos
cero (menú, garaje) no produce ninguna muestra.

## Canales {#channels}

| Canal | De | Notas |
|---|---|---|
| `time` | el reloj propio del grabador | segundos desde que empezó la grabación, rebasados a la primera muestra de la vuelta |
| `x`, `y`, `z` | media del punto de contacto de los neumáticos | metros del mundo |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | las unidades del juego, escaladas por vuelta a -1..1 según el mayor valor absoluto que usó la vuelta, **solo si** ese valor supera 1,05 (una entrada que ya está en -1..1 se deja como está) |
| `gear` | `gear - 1` | el juego cuenta 0 marcha atrás, 1 punto muerto, 2 primera; se escribe como -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, por 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | velocidad local en el desplazamiento 568 | marco del coche; solo cuando no es cero. Hacia qué lado apunta x está documentado en ambos sentidos, así que fíjate en el tamaño del ángulo de deriva, no en su signo |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | desplazamiento 564 | solo página de 800 bytes |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: desplazamientos 204 y 252, se escriben como 1 cuando es mayor que 0; AC: `tcInAction`/`absInAction` de la página de 800 bytes cuando está | ayudas actuando |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | derivado | 0..1 del recorrido usado en esta vuelta (mínimo a máximo de `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | desplazamientos 640, 656 (página de 800 bytes) | divididos por un pico típico - ver abajo |
| `slipRatioRaw.*`, `slipAngleRaw.*` | lo mismo | los valores físicos, sin escalar |
| `padLife.*`, `discLife.*` | desplazamientos 740, 756 | solo página de 800 bytes |

AC Rally envía sus temperaturas de neumáticos y frenos en kelvin: para `--game acrally`, a cualquiera
de esos valores por encima de 200 se le resta 273,15.

`wheelSlip` (desplazamiento 56) se decodifica pero no se escribe.

## Escalado del deslizamiento {#slip-scaling}

Forza envía el deslizamiento normalizado para que 1 sea el borde del agarre. Kunos envía la relación
de deslizamiento física y el ángulo de deslizamiento. Así que el grabador los divide por un pico típico
de asfalto - **0,12** para la relación de deslizamiento y **0,14 rad (unos 8 grados)** para el ángulo -
para que la lectura del visor "más de 1 significa deslizando" siga siendo aproximadamente válida, guarda
los valores en bruto junto a ellos, y escribe `"meta": {"slip": "scaled"}`. Dónde termina realmente el
agarre lo mide el visor por coche, a partir de las vueltas. Ver [Deslizamiento, deriva y canales derivados](slip-and-drift.md).

## Vueltas {#laps}

- **AC y ACC** cuentan las vueltas en la página gráfica (`completedLaps` en el desplazamiento 132, el
  tiempo de la última vuelta en milisegundos en 144). `CounterSplitter` cierra una vuelta cuando cambia
  el contador; se marca como completa, con el tiempo del juego, solo si el contador subió exactamente en uno.
- **AC EVO y AC Rally** no se leen para las vueltas (la página gráfica de EVO es un diseño distinto y
  más grande; AC Rally conduce tramos). `LineSplitter` usa como línea el punto donde empezó la grabación:
  una vuelta se cierra cuando el coche vuelve a pasar lo más cerca posible de ella en el mismo sentido,
  y un tramo o cualquier tanda se cierra cuando el coche está parado durante 8 segundos.

Detalles y umbrales: [Cómo se dividen las vueltas y los tramos](lap-splitting.md).

## Nombres de circuito y coche {#track-and-car-names}

Se leen una vez, de la página estática, cuando llega la primera muestra: para AC, ACC y AC Rally, el
coche (UTF-16, desplazamiento 68) y el circuito (desplazamiento 134); para AC EVO, el circuito y su
configuración (texto de un byte en los desplazamientos 136 y 169, unidos por un espacio) y ningún
coche. Se guardan en el archivo como `track` y `car: {"name": ...}`.

## El archivo de vuelta {#the-lap-file}

`game` es `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` o `assetto-corsa-rally`;
`meta` es `{"slip": "scaled", "discipline": "rally"}` para AC Rally y
`{"slip": "scaled", "discipline": "circuit"}` para los otros tres. No se escribe `surface`.

## Fuentes {#sources}

El SDK de memoria compartida de AC1; la documentación de memoria compartida de ACC (v1.8); el diseño de
AC EVO tal como se midió en `albertowd/live-telemetry-evo`; el de AC Rally tal como lo lee
`LuizZak/AssettoCorsaRallyTelemetryReader`. Ver [Juegos](games.md).
