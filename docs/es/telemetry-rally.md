---
title: "Juegos de rally"
nav_order: 3
lang: "es"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # o dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Código: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Pruebas: `tests/test_rally.py`, con paquetes construidos según los diseños documentados. **Todavía no se ha
ejecutado contra los juegos reales.**

Todos envían UDP que el juego activa desde sus propios archivos de configuración. El grabador escucha en
todas las interfaces (`0.0.0.0`) en el puerto predeterminado del juego, salvo que `--port` indique otro:
**20777** para `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** para `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Activarlo {#switching-it-on}

El juego lee `Documents\My Games\WRC\telemetry\config.json`. El paquete `session_update` de la estructura
`wrc` predeterminada tiene que estar activado hacia este equipo:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<ruta a config.json>"
```

`--configure` (función `configure_wrc`):

- lee el JSON, busca `udp.packets` y la entrada con `"structure": "wrc"` y `"packet": "session_update"`;
- si ya está activada hacia `127.0.0.1` o `localhost` en el puerto que se usa, imprime `already on` y no cambia nada;
- si no, pone `"ip": "127.0.0.1"`, `"port": <puerto>`, `"bEnabled": true`, y conserva el `frequencyHz` de la
  entrada (o `-1` si no tiene); si no existe tal entrada, añade una;
- escribe el texto original en `config.json.bak` junto a él, y luego escribe el archivo nuevo (con sangría
  de 4 espacios).

Reinicia el juego tras cambiar el archivo si no recoge el cambio (no comprobado).

### Qué envía {#what-it-sends}

La estructura `wrc` predeterminada ocupa 237 bytes, little-endian, sin cabecera: posición del mundo,
velocidad y aceleración (X a la izquierda, Y arriba, Z hacia delante), los vectores unitarios izquierda /
delante / arriba del coche, por rueda (trasera izquierda, trasera derecha, delantera izquierda, delantera
derecha) la altura del buje y su velocidad vertical y la velocidad hacia delante del punto de contacto,
temperaturas de frenos, pedales tras las ayudas, dirección (-1 izquierda, +1 derecha), freno de mano, rpm,
marcha, y el reloj del tramo, la distancia y la longitud. Un paquete de menos de 237 bytes se ignora e
informa una sola vez.

| Canal | De |
|---|---|
| `x`, `y`, `z` | posición del mundo |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | velocidad del mundo proyectada sobre delante, sobre menos izquierda (así positivo es derecha), sobre arriba |
| `longAcc`, `latAcc`, `vertAcc` | aceleración del mundo proyectada igual |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | tal como se envían |
| `gear` | `gear_index`; -1 cuando es igual al índice de marcha atrás, 0 cuando es igual al de punto muerto |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | posición del buje |
| `wheelSurfaceSpeed.*` | velocidad hacia delante del punto de contacto |
| `brakeTemp.*` | temperatura de freno |

Comprobación: si `speed` es mayor que 10 y la longitud de la velocidad del mundo difiere de ella en más
de un 20 %, el grabador imprime una vez que el diseño puede no ser la estructura `wrc` predeterminada.

Un tramo está **terminado** cuando la longitud del tramo es positiva y la distancia ha alcanzado la
longitud menos 0,5 m. El reloj que se usa para dividir y para `time` es `stage_time`.

Fuentes: Guía de telemetría UDP de EA v1.3; la lista de canales que el juego escribe en
`readme/channels.json`; los desplazamientos decodificados por nobonobo/obs-codemasters-telemetry y
SpaceMonkey. El puerto predeterminado de fábrica no está documentado; el grabador usa el 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Activarlo {#switching-it-on-1}

Edita `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally y DiRT
4 también usan un `hardware_settings_config.xml`; su carpeta exacta para esos dos no está comprobada aquí)
para que el elemento `udp` diga:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` es lo que pone posiciones, ruedas y longitud del tramo en el paquete. El grabador no edita
este archivo.

### Qué envía {#what-it-sends-1}

66 flotantes little-endian (DiRT Rally: 64); los paquetes de menos de 64 flotantes se ignoran, y uno de 64
se rellena con ceros. Los índices usados:

| Índice | Campo | Canal |
|---|---|---|
| 1 | tiempo de vuelta (tramo) | el reloj de división y `time` |
| 2 | distancia de vuelta | `stageDistance` |
| 4-6 | posición del mundo | `x`, `y`, `z` |
| 7 | velocidad | `speed` |
| 8-10 | velocidad del mundo | `longVel` (sobre delante), `latVel` (sobre el vector lateral) |
| 11-13 | vector lateral | |
| 14-16 | vector hacia delante | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | posición de suspensión TI TD DI DD | `suspensionM.*` |
| 25-28 | velocidad del parche de rueda TI TD DI DD | `wheelSurfaceSpeed.*` |
| 29-33 | acelerador, dirección, freno, embrague, marcha | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 o más es marcha atrás, se escribe como -1) |
| 34, 35 | g lateral, longitudinal | `latAcc`, `longAcc` (por 9,80665) |
| 37 | rpm / 10 | `rpm` (por 10) |
| 51-54 | temperaturas de freno | `brakeTemp.*` |
| 59, 60, 61, 62 | vueltas completadas, vueltas totales, longitud del circuito, tiempo de la última vuelta | división |

**No hay canal de freno de mano**. El sentido del vector lateral está documentado en ambos sentidos, así
que no se puede confiar en el signo de `latVel` (el visor lee el tamaño del ángulo de deriva).

Un tramo está **terminado** cuando el número de vueltas completadas sube por encima de su valor al inicio
del tramo (una vuelta de rallycross cada vez que lo hace), o, en un evento de una sola vuelta, cuando la
distancia de la vuelta alcanza el 99,9 % de la longitud del circuito. El tiempo del tramo es el tiempo de
la última vuelta del juego cuando es positivo. Comprobación: velocidad frente a rapidez, como en EA WRC,
con el mensaje "is extradata set to 3?".

Fuentes: documento UDP de DiRT 4 de Codemasters; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Activarlo {#switching-it-on-2}

En `RichardBurnsRally.ini`, sección `[NGP]`: `udpTelemetry=1` y el destino (127.0.0.1, puerto 6776 salvo
que pases otro `--port`). El grabador no edita este archivo.

### Qué envía {#what-it-sends-2}

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): el reloj del tramo y la distancia hasta el
final, pedales, dirección, marcha, posición del mundo, actitud, las velocidades propias del coche (avance
hacia delante, deriva lateral, oscilación vertical), aceleraciones, rpm, y cuatro bloques de rueda de 128
bytes (LF, RF, LB, RB) con la deflexión y la fuerza del muelle. Sin velocidades de rueda.

| Canal | De |
|---|---|
| `x`, `y`, `z` | posición, ejes tal como se envían, y luego reordenados (abajo) |
| `longVel`, `latVel`, `vertVel` | avance, deriva lateral, oscilación vertical |
| `longAcc`, `latAcc` | aceleración x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | tal como se envían |
| `gear` | `gear - 1` (0 marcha atrás, 1 punto muerto, 2 primera) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | deflexión del muelle |
| `wheelLoad.*` | fuerza del muelle |
| `speed` | **calculada a partir de las posiciones** en ±2 muestras, no tomada del paquete |

Los ejes de posición, las unidades de actitud y la unidad de velocidad de RBR no están documentados, así que
al escribir un tramo: el eje en el que el tramo varía menos se toma como vertical y se intercambia con `y`
(`orient_up`, necesita al menos 10 muestras), y la velocidad se recalcula a partir de las posiciones
(`speed_from_positions`). La actitud se decodifica pero no se escribe, así que los archivos de RBR no tienen `yaw`.

Un tramo está **terminado** cuando el reloj de carrera está en marcha y la distancia hasta el final ha
llegado a cero. El reloj es `race_time`.

Fuentes: `rbr.telemetry.data.TelemetryData.h` de NGP, a través de mika-n/RBRUDPTelemetryLogger y
groybe/rbr-udp-telem.

## Tramos {#stages}

Los cinco usan `StageSplitter` sobre el reloj de tramo del juego: un tramo se abre cuando arranca el reloj,
se cierra completo cuando el juego dice que el coche ha terminado, y un reloj que retrocede (un reinicio, o el
siguiente tramo) abandona el tramo abierto - se conserva como archivo `_partial` si tiene más de 10 muestras y
al menos 300 m. Los tramos terminados de menos de 300 m no se escriben. Detalles:
[Cómo se dividen las vueltas y los tramos](lap-splitting.md).

## El archivo de vuelta {#the-lap-file}

`game` es `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` o `richard-burns-rally`. `meta` es
`{"discipline": "rally", "slip": null}`, más `"surface": "<valor>"` cuando se dio `--surface`. `slip` es null
porque ninguno de estos juegos envía deslizamiento de neumáticos. En su lugar, la velocidad del parche de
contacto de cada rueda (EA WRC, DiRT) va en el archivo, y el visor deriva de ella el deslizamiento y el
ángulo de deriva junto con los ejes del coche; ver [Deslizamiento, deriva y canales derivados](slip-and-drift.md).
Los canales `suspension.*` (0..1 del recorrido usado) se añaden a partir de `suspensionM.*`.

Cuando no se da `--surface`, el archivo no lleva ninguna superficie, a propósito: un valor predeterminado
escrito aquí anularía la inferencia propia del visor. El visor toma entonces la superficie del nombre del
tramo o del evento (rallies de asfalto, de invierno, Montecarlo como mixto), si no de cómo se condujo el coche
sobre ella (una conducción agresiva en curva con poco ángulo de deriva es asfalto), y suelo suelto cuando
nada lo indica - que es lo más habitual en un tramo de rally. Usa `--surface` cuando lo sepas mejor.
