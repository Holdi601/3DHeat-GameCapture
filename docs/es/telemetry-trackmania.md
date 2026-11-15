---
title: "Trackmania"
nav_order: 5
lang: "es"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Código: el plugin de Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **El plugin todavía no se ha ejecutado en el juego**; el lector de su CSV del visor sí está probado.

## Por qué un plugin que escribe archivos {#why-a-plugin-that-writes-files}

Trackmania no tiene salida de telemetría propia. Openplanet, la plataforma de plugins del juego, expone el estado del vehículo del coche que se ve a los plugins, pero los plugins de Openplanet no pueden enviar UDP. Así que el plugin escribe un archivo CSV por ejecución en su propia carpeta de almacenamiento, y el visor lee esos archivos tal cual. No hay proceso grabador: `telemetry --game trackmania` solo instala el plugin (con `--install`) e imprime dónde aparecerán los archivos.

## Instalación y carga {#installing-and-loading}

- `--install` copia `mods/trackmania/Heat3dRecorder` a
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, sustituyendo una copia anterior. Sin `--install` no se copia nada.
- En el juego: **Openplanet > Developer > Load plugin**, y elige `3DHeat recorder`.
- El plugin depende del plugin **VehicleState** de Openplanet (`dependencies = ["VehicleState"]` en `info.toml`).
- Los plugins sin firmar solo se cargan en el **modo desarrollador de Openplanet**, que limita el juego en línea. El plugin puede firmarse en openplanet.dev; aquí no está firmado.

Las ejecuciones se escriben en `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Carga esos archivos CSV en la pestaña **Análisis de carrera** del visor. `-o` y `--port` se ignoran en Trackmania.

## Qué graba el plugin {#what-the-plugin-records}

Solo lee lo que expone Openplanet -el estado del vehículo del coche que se ve (`VehicleState::ViewingPlayerState()`) y el tiempo de carrera del jugador y su número de reinicios (`CSmScriptPlayer`)- no envía nada a ningún sitio y no cambia nada en el juego. Se escribe una fila en cada fotograma (`Update`), así que la frecuencia de muestreo es la tasa de fotogramas del juego.

| Columna | Origen |
|---|---|
| `time` | `CurrentRaceTime` / 1000, segundos |
| `x`, `y`, `z` | `Position` (mundo, Y hacia arriba) |
| `speed` | longitud de `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 o 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` de cada rueda (medida de deslizamiento de 0 a 1) |
| `loose` | 1 cuando el material del suelo de alguna rueda es Grass, Ice, Sand, Dirt, Green o RoadIce |
| `airborne` | 1 cuando el coche no tiene contacto con el suelo |
| `respawns` | reinicios desde el inicio de la ejecución |

## Ejecuciones {#runs}

- Una ejecución **empieza** en el primer fotograma donde el tiempo de carrera no es negativo (la cuenta atrás no se graba).
- **Termina** cuando la secuencia de interfaz del playground es la de meta (valor 11): el archivo se escribe como completo, con el último tiempo de carrera como `seconds`.
- Se **abandona** -se escribe con `_partial` en el nombre y `"complete": false`- cuando el reloj de carrera retrocede más de medio segundo (un reinicio), o cuando el jugador sale del playground.
- Una ejecución con menos de 20 filas no se escribe.

## El archivo {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Se llama `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Del nombre del mapa se quitan los códigos de formato y las comillas dobles se sustituyen por simples. Los valores se escriben con cuatro decimales. El formato se describe en [El archivo de vuelta heat3d](lap-format.md#the-csv-form).

El `meta` de la cabecera incluye `"slip": "index"` -los canales `slipIndex.*` son la medida propia de Trackmania de deslizamiento de 0 a 1, no un deslizamiento físico- y `"discipline": "arcade"`.
