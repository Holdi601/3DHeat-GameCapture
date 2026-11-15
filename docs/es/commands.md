---
title: Referencia de comandos
nav_order: 5
lang: es
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Referencia de comandos {#command-reference}

Todos los comandos se ejecutan desde la carpeta del repositorio, con el entorno del proyecto:

```bash
.venv\Scripts\python -m heat3d_capture <verbo> [opciones]
```

| Comando | Qué hace |
|---|---|
| [`route`](#route) | Graba solo las posiciones de una vuelta de Forza, para encontrar el mapa en los archivos del juego |
| [`telemetry`](#telemetry) | Graba todos los canales, un archivo de vuelta por vuelta, para la pestaña Análisis de carrera |
| [`laps`](#laps) | Lee una biblioteca de vueltas de FH Companion y escribe la ruta y las muestras de un circuito |
| [`reconstruct`](#reconstruct) | Resuelve una grabación sin conexión y escribe un `.glb` |
| [`hud`](#hud) | Lee las acciones del propio jugador, sus muertes, el recorrido del minimapa y el registro de eliminaciones, a partir de una grabación |
| [`locate`](#locate) | Dónde se tomó cada fotograma de una grabación, comparado con renderizados del nivel |
| [`python -m heat3d_capture.ui`](#the-scan-window) | La ventana de escaneo |
| [`python -m heat3d_update`](#updates) | Busca y aplica una actualización |
| [`python tools/export_onnx.py`](#the-model-converter) | Convierte el modelo de profundidad a ONNX |

Cuando se inicia como `python -m heat3d_capture`, la herramienta primero busca una versión más nueva
(ver [Actualizaciones](updates.md); `HEAT3D_NO_UPDATE=1` la desactiva). `--help` después de cualquier verbo
muestra sus opciones:

![Salida de heat3d_capture --help](../assets/img/cli-help.svg)

Código: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Escucha los Datos de salida de Forza y guarda solo las posiciones del coche, nada más: sin modelo de
profundidad, sin GPU, sin captura. Código: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opción | Por defecto | Significado |
|---|---|---|
| `-o`, `--out` | obligatorio | Ruta de salida; se cambia su extensión, así que `-o lap` escribe `lap.npz` y `lap.json`. |
| `--port` | `5300` | Puerto al que envía el juego (escucha solo en 127.0.0.1). |
| `--seconds` | `0` | Se detiene tras esta cantidad de segundos; `0` sigue hasta Ctrl+C. |

Una posición se guarda solo mientras el juego informa de una carrera (`isRaceOn`), el coche se mueve a más
de 0,5 m/s y está al menos a 0,5 m de la última posición guardada. Si no, estar parado en un menú con
60 paquetes por segundo llenaría el archivo con la línea de salida. El tiempo de cada muestra es el
tiempo de carrera del juego, o el reloj de pared si ese es 0. El trazado se detecta igual que en
`telemetry` (el coche tiene que moverse primero; ver [Forza](telemetry-forza.md)).

Una vez por segundo imprime los paquetes recibidos, las posiciones guardadas y la posición actual, o
`nothing on port 5300 yet - is Data Out on?`. La ruta se **guarda mientras se conduce**: cada 2 segundos
una vez ha llegado una nueva posición (el intervalo crece hasta veinte veces lo que tardó el último
guardado, así que una sesión muy larga nunca dedica más de una veinteava parte de su tiempo a escribir),
y una vez más cuando la grabadora se detiene por cualquier motivo: Ctrl+C, `--seconds` o una excepción.
Cada guardado escribe `lap.npz.partial` / `lap.json.partial` y luego lo sustituye por el archivo real, así
que los archivos en disco siempre están completos; un fallo o un proceso terminado pierde como mucho los
últimos segundos. Si no se guardó nada, imprime cómo activar Data Out y sale con el código 1.

Salida:

- `lap.npz` - matrices de NumPy `positions` (n x 3, metros), `times`, `speeds` (m/s);
- `lap.json` - legible sin este proyecto:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Las posiciones son las coordenadas mundiales propias del juego, lo que las convierte en un punto de
referencia para encontrar el mismo terreno en los archivos del juego: el comando `course` de
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) toma este JSON y exporta el circuito
que recorrió la vuelta.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Cada opción y cada juego se describen en [Grabadores de telemetría](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Lee la biblioteca de vueltas que guarda FH Companion y escribe dos archivos para un circuito: una ruta que
indica qué parte del mapa recortar del archivo del juego, y una tabla con cada muestra de cada vuelta. Se
escriben juntos para que no puedan desincronizarse. Código:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opción | Por defecto | Significado |
|---|---|---|
| `course` | ninguno | Nombre del circuito, con coincidencia flexible. Si se omite, lista la biblioteca. |
| `-o`, `--out` | el nombre del circuito en minúsculas, espacios como `_` | Ruta de salida; se escriben `.json` y `.csv` uno junto al otro. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Dónde están las carpetas de los circuitos. |
| `--margin` | `80` | Metros que se añaden alrededor de la extensión del circuito en x y z, en los `bounds` de la ruta. |

### Listado {#listing}

Sin circuito imprime el número de carpetas de circuitos y, para cada una, el número de archivos de vuelta
(`*.json` en cualquier nivel por debajo, excepto `course.json`) y el nombre del circuito; después,
`Name one to write it out:  -o <file> <course>`.

### Buscar un circuito {#finding-a-course}

Las carpetas de circuito se llaman `<nombre> (course_<x>_<z>_to_<x>_<z>)`: la salida y la llegada,
redondeadas. Un circuito se busca, en este orden: por el nombre exacto de la carpeta; por la parte del
nombre de la carpeta, sin distinguir mayúsculas; por una carpeta única cuyo nombre contenga el texto.
Si hay varias coincidencias, es un error que las enumera.

### Lectura {#reading-it}

- `course.json` en la carpeta, si se puede leer, da el nombre y la salida y la llegada sin redondear
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); si no, se toman del nombre de la carpeta. Un circuito
  se considera de vuelta cuando la salida y la llegada están a menos de 10 m.
- Cada otro `*.json` por debajo de la carpeta es una vuelta (las vueltas están varias carpetas más abajo, por
  clase, coche, puesta a punto o etiqueta, y la búsqueda es simplemente recursiva). Los archivos se leen en
  UTF-8 con marca de orden de bytes. Una vuelta que no se puede leer se omite. Las vueltas se ordenan por su
  hora de grabación.
- Por vuelta: `Lap.samples` (cada una con `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), y la clase del coche, su
  orden, el índice de rendimiento, los segundos de la vuelta, la longitud, la hora de grabación y la salida
  parada.

Imprime un resumen (vueltas, muestras, mejor vuelta y su clase, y la extensión en x/y/z).

### Salida {#output}

**`<out>.json`** - la misma forma de ruta que escribe `route`, para que el extractor de mapas acepte
cualquiera de los dos: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (ampliados con
`--margin` en x y z) y `positions` de la vuelta **más rápida** (una línea en lugar de una mancha con todas
las vueltas).

**`<out>.csv`** - cada muestra de cada vuelta, una fila por muestra:

| Columna | Significado |
|---|---|
| `course` | nombre del circuito |
| `lap` | una etiqueta por vuelta: fecha y hora de grabación hasta el minuto, y el tiempo de vuelta |
| `car` | código del coche |
| `car_class` | letra de la clase de rendimiento |
| `pi` | índice de rendimiento |
| `lap_seconds` | el tiempo de la vuelta |
| `speed_kmh` | velocidad en km/h |
| `x`, `y`, `z` | posición mundial, metros, con 3 decimales |
| `speed_ms` | velocidad, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | tal como los registra FH Companion |
| `metres` | distancia a lo largo de la vuelta, con 3 decimales |
| `elapsed` | segundos desde el inicio propio de la vuelta, con 3 decimales |

Los valores que no son posiciones se escriben con 4 cifras significativas; las posiciones tienen decimales
fijos porque 4 cifras significativas encajarían un circuito en una cuadrícula de un metro. Los nombres de
columna están elegidos para que el visor mapee el archivo sin que se le indique: `lap` se convierte en la
sesión (dos vueltas del mismo coche nunca se unen), `car` en lo que se mueve, `car_class` en el grupo por el
que colorear, y `elapsed` en el eje de tiempo (todas las vueltas se alinean en su propio inicio).

Por último imprime una sugerencia para recortar el mapa del juego con GameFiles, con el archivo de ruta o una
caja explícita.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Reconstruye una grabación sin conexión, con la trayectoria de la cámara resuelta toda de una vez por VGGT.
Es lento: minutos por ventana en una GPU de escritorio. Necesita PyTorch, `transformers` de Hugging Face y el
paquete `vggt`, que el escáner no necesita: están listados en `requirements-offline.txt`, y el comando los
comprueba después de imprimir la línea de licencia y ofrece instalar lo que falte (código de salida 1 si se
rechaza). Descripción completa: [Reconstrucción sin conexión](reconstruction-offline.md).

| Opción | Por defecto | Significado |
|---|---|---|
| `video` | obligatorio | La grabación. Código de salida 2 si no existe. |
| `-o`, `--out` | obligatorio | El `.glb` que se escribe. |
| `--solve-budget` | `260` | Número máximo de fotogramas que se entregan al solver. Se espacian según cuánto se mueve la imagen, no según el reloj. Más es más preciso y mucho más lento. Más de 400 fotogramas planificados se rechaza. |
| `--fuse-interval` | `0.4` | Segundos entre fotogramas fusionados en la geometría. |
| `--model` | `vggt-1b` | Con qué pesos de VGGT resolver: `vggt-1b` (`facebook/VGGT-1B`, no comercial) o `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, restringido; Meta debe conceder el acceso). La línea de licencia que se imprime primero es la de ese modelo. |

Primero imprime la línea de licencia del modelo, luego cada etapa (`masking`, `planning`, `solving`,
`fusing`, `exporting`) con los segundos transcurridos y el progreso, y al final un resumen: cámaras
resueltas, error de cierre, peor costura, notas y el archivo escrito. El código de salida es 0 solo si se
escribió un archivo.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Lee el HUD del juego en la grabación del propio jugador, después de la partida: las acciones del propio
jugador a partir del aviso de puntos, las muertes y reanimaciones a partir de las pantallas de caída y de
despliegue, el recorrido por el minimapa y el registro de muertes. Escribe `<out>.parquet` (recorrido y
eventos, una tabla de 3DHeat), `<out>.events.jsonl`, `<out>.summary.json`, y `<out>.map.png` + `.map.json`
(el mosaico del minimapa y sus anclas para la imagen de mapa del visor). Battlefield 6 (`bf6`) es, de
momento, el único perfil.

Necesita **ffmpeg y ffprobe** en PATH (`winget install Gyan.FFmpeg`, y después una terminal nueva).

| Opción | Por defecto | Significado |
|---|---|---|
| `video` | obligatorio | La grabación. |
| `-o`, `--out` | el nombre del vídeo | Ruta de salida sin extensión. |
| `--game` | `bf6` | De qué juego se lee el HUD. |
| `--player` | adivinado | El nombre del jugador tal como lo muestra el registro de eliminaciones, con coincidencia flexible. |
| `--fps` | `5` | Muestras del minimapa por segundo. |
| `--start`, `--seconds` | el vídeo entero | La parte de la grabación que se lee. |
| `--metres-per-pixel` | ninguno | La escala del minimapa, cuando se conoce; sin ella las posiciones van en píxeles del minimapa. |
| `--cpu` | desactivado | Decodificar en la CPU aunque haya una tarjeta NVIDIA. |

Descripción completa: [Leer el HUD de una grabación](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderiza un nivel desde cada lugar en el que puede estar un jugador e indexa los renderizados;
`frames` ubica cada fotograma muestreado de una grabación frente a él, a partir de la imagen, con el recorrido
del minimapa de la orden `hud` como alternativa; `eval` compara un resultado con poses de cámara conocidas;
`train` entrena un modelo de lugares por mapa con renderizados del nivel (y con fotogramas que una ejecución ya
ubicó), para `build --head`; `refmap` coloca el mapa propio del juego (su pantalla de despliegue) sobre el
nivel, y `minimap` lee el minimapa de una grabación contra él, fotograma a fotograma, que es la información
previa que puede tomar `frames --minimap`. Necesita PyTorch y `requirements-locate.txt`. **Experimental:** con
grabaciones reales, por ahora ubica solo una pequeña parte de los fotogramas. Todas las opciones, las salidas
y el método: [Ubicar fotogramas en un nivel](locate.md); la lista completa de opciones:
[Referencia de comandos](../cli-reference.md).

## La ventana de escaneo {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

o haz doble clic en `scan.bat`. Sin opciones. Ver [La ventana de escaneo](reconstruction-scan-ui.md).

## Actualizaciones {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Ver [Actualizaciones](updates.md).

## El convertidor de modelos {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Convierte un punto de control de Depth Anything V2 al archivo ONNX que ejecuta el escáner. Necesita PyTorch,
`transformers` y `onnxscript`. Ver [Profundidad](reconstruction-depth.md#building-the-model).
