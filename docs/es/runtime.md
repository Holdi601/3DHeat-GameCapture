---
title: "Runtime y dependencias"
nav_order: 8
lang: "es"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, dependencias y rendimiento {#runtime-dependencies-and-performance}

Código: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Haz doble clic. Hace solo dos cosas por sí mismo:

1. **Busca Python** (`python`, luego `py`). Si no hay ninguno, pregunta
   `Install it now with winget [Y,N]?`; con Y ejecuta
   `winget install -e --id Python.Python.3.12`, y luego te pide cerrar la ventana y ejecutar
   `scan.bat` de nuevo para que Windows recoja el nuevo PATH. Con N no se instala nada.
2. **Crea un entorno privado**, `.venv` junto a `scan.bat`, si no existe, y actualiza su pip -
   así que nada se instala en el Python del sistema.

Después ejecuta `.venv\Scripts\python.exe -m heat3d_capture.ui`. Todo lo demás - averiguar qué
falta, explicar para qué sirve, preguntar - ocurre en Python, en un cuadro de diálogo.

## Comprobación previa en el primer inicio {#first-run-preflight}

Antes de que la ventana importe nada pesado, se comprueba cada requisito (con
`importlib.util.find_spec`, así que un paquete a medio borrar cuenta como ausente). Las reglas:

- **Se comprueba todo primero.** Se reúne la lista completa antes de decir nada, así que
  arreglar un paquete nunca lleva directamente al siguiente error.
- **Preguntar, nunca suponer.** El cuadro de diálogo lista cada paquete que falta, para qué
  sirve, y el total a descargar, y no hace nada sin **Download and install**. Cancelar sale:
  "Nothing was installed and nothing was changed."
- **El silencio no es consentimiento.** Sin Qt, la comprobación recurre a la consola y pregunta
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` significan sí); sin terminal donde
  responder (fin de la entrada), no instala nada.
- **Dentro del entorno propio de la herramienta.** La instalación es `<python en ejecución> -m
  pip install ...` como subproceso - con `scan.bat`, el `.venv` privado. Si falla, el cuadro de
  diálogo muestra la última línea de la salida de pip y el comando para probar a mano.

| Paquete | Se importa como | Mostrado como para qué sirve | Descarga aprox. |
|---|---|---|---|
| numpy | `numpy` | la aritmética sobre la que se construye todo lo demás | 20 MB |
| opencv-python | `cv2` | leer archivos de vídeo y fotogramas de cámara | 40 MB |
| onnxruntime-directml en Windows, onnxruntime en otros | `onnxruntime` | ejecutar el modelo de profundidad en tu tarjeta gráfica | 120 MB |
| PySide6-Essentials | `PySide6` | la ventana y sus controles | 90 MB |
| scipy | `scipy` | suavizar la superficie reconstruida | 45 MB |
| scikit-image | `skimage` | convertir mediciones en una superficie 3D | 30 MB |
| windows-capture | `windows_capture` | capturar una ventana de juego en directo (opcional: sin él, los archivos de vídeo siguen funcionando) | 5 MB |

Convertir el modelo de profundidad necesita tres más, pedidos aparte y solo cuando pulsas
"Set up the depth model": `torch` (unos 900 MB), `transformers` (30 MB), `onnxscript` (15 MB).
El propio escáner nunca los importa.

El comando `reconstruct` sin conexión tiene una comprobación propia, que se ejecuta tras
imprimir la línea de licencia y solo en la terminal: `torch` (900 MB), `transformers` (30 MB),
`einops`, `safetensors`, `huggingface_hub`, `Pillow`, y `vggt` del repositorio de GitHub de Meta
(instalado con `--no-deps`, porque sus metadatos fijan numpy por debajo de 2). La misma lista está
en `requirements-offline.txt`; ver [Reconstrucción sin conexión](reconstruction-offline.md#requirements).

El paquete de ONNX Runtime que se ofrece es el que `requirements.txt` elige para la plataforma:
`onnxruntime-directml` en Windows, `onnxruntime` en otros. Si `onnxruntime` ya se puede importar
(por ejemplo `onnxruntime-gpu`), no se instala nada: la comprobación es por nombre de módulo.

## Instalar a mano {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fija: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(solo Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` en Windows y `onnxruntime>=1.19` en otros.

`requirements-offline.txt` añade lo que solo necesita `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` y `Pillow`, con la línea de instalación de `vggt` (`--no-deps`) y
la nota de licencia de VGGT en su cabecera. PyTorch tampoco está incluido, por la razón de abajo.

**PyTorch queda deliberadamente fuera.** La rueda correcta depende de la GPU y de la versión de
CUDA, y fijar una instalaría una versión solo de CPU en las máquinas que más necesitan la de GPU.
Si lo quieres (conversión del modelo, la ruta offline `reconstruct`), instálalo **antes** que
`requirements.txt`: las ruedas de torch pueden acabar con numpy 1.x, con el que scipy se niega a
funcionar, y el fallo aparece como `module numpy has no attribute long` desde dentro de scipy, lejos
de su causa.

`onnxruntime-directml` y `onnxruntime-gpu` entran en conflicto: instala solo uno.

Verificado por el desarrollador: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, en una
NVIDIA RTX 5080, y el mismo entorno sin ningún paquete específico de NVIDIA.

## Backends de inferencia {#inference-backends}

ONNX Runtime llega a las GPU mediante proveedores de ejecución, y cuáles existen depende de cómo
se instaló onnxruntime, no del hardware. Así que la disponibilidad se descubre, de mejor a peor:

| Rango | Proveedor | Mostrado como | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | cualquier GPU Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | cualquiera |

**DirectML es la instalación predeterminada** porque llega también a las GPU AMD e Intel, además de
a NVIDIA. NVIDIA va más rápida con sus propios proveedores - instalar `onnxruntime-gpu` añade CUDA,
y la ventana lo indica cuando ve una tarjeta NVIDIA funcionando con DirectML - pero no se permite
que NVIDIA sea la única opción. CPU siempre va la última, así que una máquina sin GPU útil obtiene un
escaneo lento en lugar de ninguno, y se añade como respaldo cuando se crea una sesión en GPU.

El nombre del adaptador se lee de la clave de clase de adaptadores de pantalla del registro de
Windows (no de una herramienta del fabricante como `nvidia-smi`, que solo existe en algunas
máquinas), omitiendo el Basic Render Driver. Los proveedores ligados a un fabricante nombran el
adaptador correspondiente; DirectML se muestra en el primer adaptador enumerado, que es el
predeterminado del sistema. El nombre es solo para mostrar.

`ScanSettings.prefer_backend` (solo scripts) puede nombrar un proveedor o un nombre corto.

## Qué esperar de esta máquina {#what-to-expect-from-this-machine}

La ventana mide el rendimiento real del modelo de profundidad en esta máquina al arrancar (6
fotogramas tras un calentamiento) en lugar de buscar la GPU en una tabla - el estado térmico, los
perfiles de energía de los portátiles y las versiones de los controladores lo mueven demasiado - y
dice cómo será un escaneo antes de que pueda empezar nada:

| Vistas medidas por segundo | Nivel | Titular | Consejo |
|---|---|---|---|
| 25 o más | tiempo real | Escaneo en directo a máximo detalle. | Camina a ritmo normal; la superposición seguirá el ritmo. |
| 12 a 25 | viable | Escaneo en directo, con menos vistas conservadas que a máxima velocidad. | Camina despacio y gira suavemente - los giros rápidos dejarán huecos. Borrador conserva menos vistas, lo que ayuda al modelo de profundidad a seguir el ritmo. |
| 2 a 12 | lento | Graba primero, reconstruye después. | Graba un vídeo del recorrido y reconstruye después desde el archivo. El resultado es idéntico; solo el feedback no es en directo. |
| menos de 2 | impracticable | Esta máquina es demasiado lenta para escanear de forma útil. | Un recorrido más corto, o un modelo más pequeño. **El inicio está desactivado.** |

En CPU, la nota añade que instalar `onnxruntime-directml` suele solucionarlo en Windows. Nada
cambia la resolución de captura por sí solo: no ayudaría, porque el modelo de profundidad funciona a
su tamaño de entrada fijo sea cual sea el que reciba; lo que mantiene a flote a una máquina más lenta
es conservar menos vistas, que es lo que hace Borrador.

### Medido por el desarrollador {#measured-by-the-developer}

Mismo archivo ONNX, misma salida, RTX 5080:

| Backend | Rendimiento de profundidad |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Un clip de prueba por la ruta ONNX incluida:

| Preajuste | Vistas conservadas | Rendimiento de profundidad |
|---|---|---|
| Borrador | aprox. 1 de cada 7 | aprox. 50 /s |
| Equilibrado | aprox. 1 de cada 4 | aprox. 50 /s |
| Detallado | aprox. 1 de cada 2 | aprox. 40 /s |

La profundidad es bastante más rápida que la captura, así que el escaneo en directo no está
limitado por la profundidad. El entorno de la aplicación ocupa unos 349 MiB sin PyTorch, frente a
unos 3,5 GB de torch con CUDA.

La ruta `reconstruct` sin conexión es otra cosa: minutos por ventana de 16 fotogramas en una GPU de
escritorio.

## Memoria {#memory}

- Los fotogramas no se conservan después de la fusión, salvo **160** para colorear la malla.
- Un escaneo se detiene tras **3000** vistas conservadas por defecto ("Views kept"), como guarda.
- La cola de captura en directo guarda 4 fotogramas; el búfer de poses de telemetría, 30 segundos.
- Las dos rejillas de vóxeles son dispersas, y la malla se extrae bloque a bloque, así que la
  memoria sigue a lo escaneado, no a la caja envolvente.

## Plataforma {#platform}

El escáner y los grabadores de Assetto Corsa son en la práctica solo para Windows: la captura en
directo usa Windows Graphics Capture, los atajos de teclado y la superposición sin clics usan la API
Win32, y las páginas de Kunos son memoria compartida de Windows. Los archivos de vídeo se pueden
escanear y los grabadores UDP funcionan en otros sistemas, pero eso no se ha comprobado.
