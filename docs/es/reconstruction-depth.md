---
title: "Profundidad"
nav_order: 3
lang: "es"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Profundidad {#depth}

Lo único que la captura externa no puede dar es la geometría. El juego conoce la
profundidad de cada píxel y está en un búfer que este proyecto deliberadamente no
toca, así que la profundidad se **infiere de la imagen**. Ese es el límite de
precisión de todo el enfoque.

Código: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(lo que ejecuta el escáner),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(la ruta de PyTorch y el ajuste de escala),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## El modelo {#the-model}

**Depth Anything V2**, variante relativa. Predice la *inversa de profundidad
relativa*: un campo tipo disparidad correcto solo hasta una transformación afín
desconocida, `disparidad_métrica = a * predicho + b`, distinta para cada fotograma.
La red es buena en lo que es difícil a partir de una sola imagen (forma relativa,
bordes, estructura fina) y no sabe nada de lo que no puede saber (la escala). La
escala viene de otro sitio: ver [Pose de la cámara y escala](reconstruction-pose.md).

| Tamaño | Id en Hugging Face | Licencia |
|---|---|---|
| **Pequeño** (predeterminado) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - uso comercial permitido |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - solo no comercial |
| Grande | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - solo no comercial |

Una reconstrucción hereda la licencia del modelo que la hizo. Pequeño es el
predeterminado en todas partes precisamente para que un escaneo no lleve ninguna
restricción salvo que alguien elija otra cosa. Las variantes métricas
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) están nombradas
en el código pero el escáner no las usa. Ver [Modelos y licencias](models-and-licences.md).

## Construir el modelo {#building-the-model}

El escáner ejecuta un archivo ONNX y nunca importa PyTorch. El archivo hay que
hacerlo una vez:

- **Desde la ventana**: "Set up the depth model" (ver [La ventana de escaneo](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)),
  que ejecuta el comando de abajo con `--size small`.
- **A mano**, en un entorno con PyTorch, `transformers` y `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opción | Predeterminado | Significado |
|---|---|---|
| `--size` | `small` | `small`, `base` o `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | archivo de salida |
| `--side` | `518` | tamaño cuadrado de entrada; debe ser múltiplo de 14 (el tamaño de parche del ViT); 518 = 14 x 37 es la resolución de entrenamiento |
| `--opset` | `17` | opset de ONNX; 17 tiene amplio soporte en DirectML y CUDA |

Lo que hace el convertidor:

- Descarga el punto de control de Hugging Face (`AutoModelForDepthEstimation`).
- Lo envuelve para que la **normalización de ImageNet esté dentro del grafo**: el
  modelo recibe RGB en el rango 0-255 como float (`pixels`, forma
  `lote x 3 x lado x lado`) y saca `inverse_depth`. Hay exactamente una copia de la
  media y la desviación típica, así que no pueden desviarse del punto de control.
- **Tamaño espacial fijo**, lote dinámico. DirectML y TensorRT compilan por forma; un
  alto y ancho dinámicos recompilarían en el primer fotograma de cada nueva
  resolución, una parada visible en una captura en directo.
- Exporta por la **ruta TorchScript** (`dynamo=False`): el grafo dynamo falló en
  DirectML en un nodo Reshape, y escribe los pesos en un archivo `.onnx.data` aparte.
  La ruta TorchScript produce un único archivo autocontenido.
- Imprime el archivo y su tamaño. Las advertencias del trazador sobre formas fijas
  en el grafo son esperadas.

El escáner busca `models/depth-*.onnx` y elige por licencia, no por nombre de archivo: el modelo
Small siempre que esté, un tamaño mayor solo cuando es el único. La línea de la ventana de
escaneo nombra el archivo, su licencia y cualquier otro modelo que dejó sin usar.

## Ejecutarlo: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` crea una sola sesión de ONNX Runtime, de forma perezosa, con
optimización completa del grafo, en el backend que eligió la escalera, con CPU añadida
como respaldo para que un proveedor que falle al crear la sesión (un controlador
antiguo) signifique un escaneo lento, no un fallo. Ver
[Runtime y dependencias](runtime.md#inference-backends).

- `warm_up()` crea la sesión y ejecuta un fotograma en blanco (la primera inferencia
  sobre un grafo recién creado es varias veces más lenta que el estado estable).
- `measure_throughput(frames)` cronometra esa cantidad de fotogramas en blanco tras el
  calentamiento; la ventana usa 6 y muestra el resultado como vistas por segundo.

### Letterbox, no estirar {#letterboxing-not-stretching}

El grafo recibe un cuadrado fijo; el juego es 16:9. Aplastar un fotograma en un
cuadrado cambiaría la forma aparente de todo, y como la salida es una estimación
geométrica, se fusionaría como geometría real incorrecta. Así que cada fotograma:

1. se escala para caber en el cuadrado, manteniendo su relación de aspecto
   (interpolación por área al reducir, cúbica al ampliar);
2. se rellena con **gris medio (114)** - el negro o el blanco se leen como un borde
   fuerte y filtran una discontinuidad de profundidad falsa al contenido vecino;
3. pasa por el modelo;
4. el relleno se recorta de la predicción **antes** de volver a escalarla (cúbica) a
   la resolución del fotograma, de modo que el margen nunca se filtra a los píxeles reales.

El resultado es un `DepthMap` con `metric=False` al tamaño del fotograma de origen.

## La ruta PyTorch {#the-pytorch-path}

`DepthEstimator` ejecuta directamente el modelo de Hugging Face (fp16 en CUDA, fp32 en
CPU), por lotes según el tamaño del fotograma, y cada predicción vuelve a escalarse de
forma cúbica. El escáner no la usa; el comando `reconstruct` sin conexión sí (ver
[Reconstrucción sin conexión](reconstruction-offline.md)), y es una de las razones por
las que ese comando necesita PyTorch y `transformers`.

## De relativa a métrica: `fit_scale` y `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Convertir la inversa de profundidad predicha en metros necesita el afín
`escala * predicho + desplazamiento`. Cuando hay anclas de profundidad conocida (puntos
de características triangulados entre poses conocidas, o la profundidad anclada del
fotograma anterior), `fit_scale` lo resuelve:

- mínimos cuadrados **en disparidad**, no en profundidad: el error de la red es más o
  menos uniforme en disparidad, mientras que en profundidad unas pocas anclas lejanas
  (donde un píxel de disparidad son decenas de metros) dominarían;
- **reponderado iterativamente** (12 iteraciones, pesos tipo Cauchy
  `1 / (1 + (r / 3 MAD)^2)`), porque las anclas traen valores atípicos groseros (una
  coincidencia sobre un coche en movimiento, un fallo de seguimiento) y una sola ancla
  así en un ajuste simple arrastra todo el fotograma;
- necesita al menos 2 anclas útiles; informa del residuo absoluto mediano y del número
  de inliers (residuo dentro de 3 veces la mediana).

`AffineFit.apply` devuelve la profundidad en metros con **+inf** para el cielo. Comprueba
también el valor predicho además del anclado: un píxel de cielo que predice cero saldría
en `shift` - pequeño, positivo y finito - y en otro caso pondría todos los píxeles de
cielo en una capa fantasma a una distancia. Todo lo que se predice en o por debajo de
`1e-4` es cielo, diga lo que diga el ajuste.

La fusión conserva después solo profundidades entre 0,35 m y 60 m (ver
[Fusión](reconstruction-fusion-and-texture.md#from-depth-to-points)).
