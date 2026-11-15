---
title: "Desarrollo"
nav_order: 11
lang: es
source: development.md
source_hash: "385ac89e4df3"
nav_exclude: true
search_exclude: true
---
# Desarrollo {#development}

## Estructura del repositorio {#repository-layout}

| Ruta | Contenido |
|---|---|
| `heat3d_capture/__main__.py` | la línea de comandos: `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate` |
| `heat3d_capture/telemetry/` | `forza.py` (diseño de Data Out), `fulllap.py` (archivos de vuelta de Forza, retransmisión), `record.py` (`route`), `fhcompanion.py` (`laps`), `kunos.py`, `rally.py`, `beamng.py`, `lapfile.py` (el documento de vuelta compartido) |
| `heat3d_capture/capture/` | `sources.py` (captura en vivo, vídeo), `screenmask.py`, `flowmask.py`, `quality.py` |
| `heat3d_capture/depth/` | `onnx_estimator.py` (lo que ejecuta el escáner), `estimator.py` (ruta de PyTorch, `fit_scale`) |
| `heat3d_capture/pose/` | `odometry.py`, `telemetry_pose.py`, `groundscale.py`, `feedforward.py`, `vggt_model.py`, `feedforward_source.py`, `solveprep.py`, `bundle.py`, `tracks.py`, `windowed.py` |
| `heat3d_capture/fusion/` | `volume.py`, `voxelindex.py`, `coverage.py`, `texture.py` |
| `heat3d_capture/geometry/` | `glb.py` (el escritor), `reference.py` (nivel de referencia sintético) |
| `heat3d_capture/scan/` | `session.py` (un escaneo), `reconstruct.py` (fotogramas clave convertidos en geometría), `offline.py` |
| `heat3d_capture/runtime/` | `preflight.py`, `device.py` |
| `heat3d_capture/hud/` | `hud`: el HUD de una grabación: ventana de puntos, pantallas de muerte, minimapa del circuito, registro de eliminaciones (`profiles.py` por juego) |
| `heat3d_capture/locate/` | `locate`: los renderizados del nivel, la base de datos, la comparación, el modelo por mapa, el minimapa |
| `heat3d_capture/ui/` | `__main__.py` (entrada y comprobación de dependencias), `app.py`, `overlay.py`, `hotkeys.py`, `preview.py` |
| `heat3d_update/` | la comprobación de versiones y el actualizador |
| `mods/beamng/heat3d/` | el mod de protocolo de BeamNG |
| `mods/trackmania/Heat3dRecorder/` | el plugin de Openplanet |
| `tools/export_onnx.py` | el convertidor del modelo de profundidad |
| `tools/gen_docs_reference.py` | escribe `docs/cli-reference.md` a partir de `--help`; `--check` indica si está desactualizado |
| `tools/docs_diagrams.py` | dibuja los diagramas de `docs/assets/img/` (por idioma con `--lang`) |
| `tools/sync_wiki.py` | regenera `docs/wiki/` a partir de `docs/` |
| `models/` | archivos `.onnx` convertidos (no van bajo control de versiones) |
| `tests/` | el conjunto de pruebas; `scene.py` y `track_scene.py` dibujan escenas sintéticas con geometría conocida |
| `docs/` | esta documentación; `docs/wiki/` se genera a partir de ella |
| `scan.bat`, `requirements.txt`, `requirements-offline.txt`, `requirements-locate.txt`, `VERSION`, `CHANGELOG.md`, `LICENSE`, `LICENSES.md` | |

La lógica de escaneo no usa Qt: `ScanSession` y `Reconstructor` aceptan funciones simples y pueden manejarse desde un script o una prueba. Ejemplo:

```python
from heat3d_capture.depth.onnx_estimator import OnnxDepthEstimator
from heat3d_capture.scan.session import Quality, ScanSession, ScanSettings

settings = ScanSettings(source="walk.mp4", quality=Quality.BALANCED, field_of_view=90.0,
                        camera_height=1.70)
session = ScanSession(settings, estimator=OnnxDepthEstimator("models/depth-small-518.onnx"))
session.start()
session.wait()
print(session.progress.message, session.export("walk.glb"))
```

## El entorno {#the-environment}

El proyecto usa un entorno virtual en `.venv` (creado por `scan.bat` o a mano). Las pruebas que tocan la interfaz necesitan **PySide6** en él, que `requirements.txt` instala como `PySide6-Essentials`:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Para el convertidor del modelo, las pruebas del estimador de PyTorch y la ruta sin conexión, instala PyTorch (acorde con la GPU) **antes** de `requirements.txt`; después `requirements-offline.txt` y su línea `vggt` para el solucionador sin conexión, y `onnxscript` para el convertidor. Véase [Entorno de ejecución y dependencias](runtime.md#installing-by-hand).

## Ejecutar las pruebas {#running-the-tests}

```bash
.venv\Scripts\python -m pytest tests/ -q
```

`pytest.ini` define `testpaths = tests` y silencia los `UserWarning` de `huggingface_hub`. El conjunto tiene varios cientos de comprobaciones; la mayoría no necesita juego, GPU ni hardware de captura.

Qué se omite y por qué:

| Pruebas | Se omiten cuando |
|---|---|
| `test_onnx_estimator.py`, `test_launch.py`, las pruebas de ventana de `test_ui_drives_a_scan.py` | no hay `models/depth-*.onnx`: ejecuta `tools/export_onnx.py` primero |
| las pruebas del estimador GPU de `test_depth.py` | PyTorch no está instalado, o no hay dispositivo CUDA; las pruebas de `fit_scale` y `AffineFit` se ejecutan siempre |
| algunos casos de `test_offline.py` y `test_solveprep.py` | OpenCV no tiene codificador de vídeo para escribir el clip sintético |
| `test_hotkeys.py` | las pruebas de registro necesitan Windows; la prueba de respaldo se ejecuta en otros sistemas |
| `test_course_ground.py` | `HEAT3D_COURSE` no está definida |
| algunas pruebas de fusión | un caso sintético no fusionó nada |

### La prueba de arranque {#the-launch-test}

`tests/test_launch.py` ejecuta el punto de entrada real, `python -m heat3d_capture.ui`, como subproceso (con `QT_QPA_PLATFORM=offscreen`) y comprueba que llega al bucle de eventos y se mantiene en marcha. Existe porque la primera versión se cerraba al arrancar en todas las ejecuciones mientras todas las demás pruebas pasaban: todas crean su propio `QApplication` y luego construyen la ventana, lo que omite la única secuencia que realiza un usuario: la comprobación de dependencias, que crea primero una aplicación. Una prueba de componente que monta su propio entorno no puede ver un fallo en cómo se monta el entorno.

### Verdad de referencia {#ground-truth}

- `tests/test_accuracy.py` - una habitación sintética con una trayectoria conocida y profundidad analítica; véase [Reconstrucción de niveles](reconstruction.md#measured-on-synthetic-ground-truth).
- `tests/test_track_width.py`, `tests/test_track_scale.py`, `tests/test_coverage_race.py`, `tests/test_loop_closure_harm.py` - ancho de la carretera, extracción de la escala del circuito, la cuadrícula de cobertura leída mientras se escribe, y por qué el cierre de bucles sigue desactivado.
- `tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`, `tests/test_forza.py`, `tests/test_fulllap.py`, `tests/test_fhcompanion.py` - los diseños de telemetría, con paquetes y páginas construidos a partir de las estructuras documentadas, y los archivos de vuelta que escriben (nombres de canal canónicos, `meta`, sin `NaN` en el JSON). `tests/test_trackmania_plugin.py` lee el código fuente del plugin de Openplanet para ver qué escribe en la descripción de cada ejecución.
- `tests/test_route_record.py` - el archivo `route` está completo en disco antes de que el grabador se detenga.
- `tests/test_telemetry_pose.py` - poses de Forza en las coordenadas propias del juego, los sentidos de yaw, pitch y roll, y un hueco de telemetría cubierto visualmente en el mundo reflejado.
- `tests/test_glb.py` - el contrato GLB; las pruebas propias del visor leen un nivel de referencia escrito por este escritor, así que el formato se prueba en ambos lados.

### Comprobar un circuito exportado frente a vueltas {#checking-an-exported-course-against-laps}

`tests/test_course_ground.py` comprueba que un circuito exportado por [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) está de verdad bajo el coche grabado: el coche debe estar a una altura de suspensión sobre la superficie que tiene justo debajo. Apunta al nombre base de un circuito exportado (el `.glb` y su `.json` al lado):

```bash
HEAT3D_COURSE=.out/courses/my_course .venv\Scripts\python -m pytest tests/test_course_ground.py
```

Un circuito con saltos grandes puede fallar por diseño: el coche está en el aire sobre un terreno que sí existe.

## Convenciones {#conventions}

- El código bajo `heat3d_capture/` importa dependencias pesadas (OpenCV, ONNX Runtime, PyTorch, Qt) de forma diferida, dentro de funciones, así que importar un módulo, ejecutar `--help` o ejecutar los grabadores de telemetría no cuesta nada.
- Los hilos de trabajo nunca tocan widgets de Qt; los resultados pasan al hilo de la interfaz como señales de Qt.
- Las grabaciones, los archivos de vuelta, las mallas, los pesos de los modelos y el vídeo quedan fuera de git gracias a `.gitignore`, por carpeta y por tipo de archivo.
- Confirmaciones y publicaciones: la versión es el archivo `VERSION`; las publicaciones son versiones de GitHub de [Holdi601/3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture), que lee el actualizador ([Actualizaciones](updates.md)).
