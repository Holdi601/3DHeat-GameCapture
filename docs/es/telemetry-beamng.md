---
title: "BeamNG.drive"
nav_order: 4
lang: "es"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copia el mod y luego graba
python -m heat3d_capture telemetry --game beamng -o laps      # graba
```

Luego, en el juego: **Opciones > Otros > Protocolos**, activa **"others"**.

Código: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
y el mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Pruebas: `tests/test_beamng.py`, con paquetes construidos a partir de la estructura del mod. **El mod todavía no se ha ejecutado en el juego.**

## Por qué un mod {#why-a-mod}

BeamNG envía telemetría mediante «protocolos»: módulos Lua en el vehículo que el propio `lua/vehicle/protocols.lua` del juego empaqueta y envía por UDP desde el coche que conduce el jugador. Los protocolos de serie no traen lo que necesita un análisis del control del coche: OutGauge no tiene posición, MotionSim no tiene ruedas, y OutSim es un esqueleto en las versiones actuales. Por eso este proyecto incluye su propio protocolo, `heat3d`. No toca nada fuera del Lua del propio vehículo.

## Instalación {#installing}

`--install` copia `mods/beamng/heat3d` a
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 y posteriores guardan ahí los mods de usuario), borrando antes una copia anterior, e imprime a dónde fue. Sin `LOCALAPPDATA` recurre a la carpeta personal. También puedes copiar la carpeta a mano.

`--install` sigue directamente con la grabación.

## El mod {#the-mod}

| Ajuste (en `heat3d.lua`) | Valor |
|---|---|
| Dirección | `127.0.0.1` |
| Puerto | `4460` - cámbialo aquí y pasa el mismo `--port` al grabador |
| Frecuencia máxima de actualización | 100 Hz |
| Paso de física | usado (`isPhysicsStepUsed` devuelve verdadero) |

Cada paquete es la cabecera de 4 bytes `H3D1` seguida de 39 floats en little-endian (160 bytes en total):

| Campo | Cantidad | Origen en el Lua del vehículo |
|---|---|---|
| `time` | 1 | el reloj propio del mod: suma de pasos de física, se reinicia al reiniciar el vehículo |
| posición | 3 | `obj:getPositionXYZ()` |
| velocidad | 3 | `obj:getVelocityXYZ()` (mundo) |
| hacia delante | 3 | `obj:getDirectionVector()` |
| arriba | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, y 1/0 desde `absActive` y `tcsActive` |
| `wheelSpeed` | 4 | velocidad de superficie de cada rueda (m/s) |
| `wheelAngular` | 4 | velocidad angular por la dirección de la rueda (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 cuando no toca el suelo |

Las cuatro ruedas se eligen por **dónde están en el coche**, no por nombre (los nombres cambian entre vehículos): delante o detrás según la posición del nodo a lo largo del coche, izquierda o derecha a través de él (marco del vehículo +X a la izquierda, -Y hacia delante), tomando en cada esquina la rueda más alejada del centro. Una esquina que falta se envía con ceros y material -1.

## Qué hace el grabador con ello {#what-the-recorder-does-with-it}

El mundo de BeamNG tiene Z hacia arriba; el del visor tiene Y hacia arriba. Posiciones y vectores se giran alrededor de X, `(x, y, z) -> (x, z, -y)`, lo que conserva la lateralidad del mundo. Después:

| Canal | Se deriva como |
|---|---|
| `x`, `y`, `z` | posición girada |
| `speed` | longitud de la velocidad girada |
| `longVel`, `latVel`, `vertVel` | velocidad proyectada sobre adelante, sobre derecha = adelante x arriba, y sobre arriba |
| `longAcc`, `latAcc`, `vertAcc` | el cambio de la velocidad del mundo en ±2 muestras, proyectado sobre los mismos ejes (el marco de los sensores del propio coche no está documentado, así que no se usan) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | tal como se envían |
| `absActive`, `tcActive` | las luces de ABS y TC, donde el coche las tiene |
| `wheelSurfaceSpeed.*` | valor absoluto de la velocidad de superficie de la rueda |
| `wheelSpeed.*` | rotación |
| `wheelLoad.*` | carga |
| `groundContact.*` | 0 cuando el material es negativo, si no 1 |

Los paquetes sin la cabecera o más cortos de 160 bytes se ignoran.

## Vueltas {#laps}

`LineSplitter`, como en AC EVO: el punto donde empezó la grabación es la línea; una vuelta se cierra donde el coche vuelve a pasar más cerca de ella con el mismo sentido, al menos 300 m después; una tanda se cierra cuando el coche está parado 8 segundos. Una vuelta cuenta como completa solo si empezó a más de 5 m/s, así que la primera vuelta desde parado es parcial. Cuando el reloj del mod retrocede más de medio segundo (el coche se reinició), la tanda abierta en ese momento se cierra antes -escrita como tanda parcial si cubrió al menos 300 m, como al final de una grabación- y luego el divisor empieza de nuevo. Véase [División por vueltas y tramos](lap-splitting.md).

## El archivo de vuelta {#the-lap-file}

`game` es `beamng`, `meta` es `{"discipline": "circuit"}`, los archivos se llaman `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. No se escribe deslizamiento; el visor lo deriva de las velocidades de superficie de las ruedas (véase [Deslizamiento, deriva y canales derivados](slip-and-drift.md)). Las posiciones están en el mismo marco que escribe la exportación de circuitos de GameFiles para BeamNG, así que una vuelta grabada encaja sobre un circuito exportado.
