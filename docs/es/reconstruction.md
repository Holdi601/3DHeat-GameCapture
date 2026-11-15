---
title: "Reconstrucción de niveles"
nav_order: 6
lang: es
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Reconstrucción de niveles a partir de la partida {#level-reconstruction-from-gameplay}

Camina despacio por un nivel, o conduce un circuito, y el escáner convierte lo que mostró la pantalla en un `.glb` que el visor de 3DHeat carga como contexto bajo la telemetría: el mismo contrato de archivo que escribe el exportador de Unreal. Sirve para cuando nadie exportó el mapa y no se pueden leer los archivos del juego; una exportación del motor o de los archivos del juego es exacta, esto es una estimación.

## La cadena de proceso {#the-pipeline}

```text
 fotogramas          fotogramas clave     profundidad          pose                 fusión              salida
 ----------          ----------------     -----------          ----                 ------              ------
 Windows Graphics -> umbral de cambio  -> Depth Anything V2 -> odometría visual  -> volumen de        -> marching cubes
 Capture, o un         de imagen          (ONNX Runtime,        (ORB + PnP), o      ocupación           -> suelo/estructura
 archivo de vídeo     (adaptativo)        con relleno)          telemetría de       + cuadrícula de     -> color por vértice
                                                                Forza, o una        cobertura (mapa     -> .glb
                                                                solución VGGT       en vivo, puntos
                                                                                    débiles)
                     máscaras HUD / cabina, consejos de calidad de fotograma, escala del plano del suelo
```

| Etapa | Escaneo en vivo (`heat3d_capture.ui`) | Sin conexión (`reconstruct`) | Página |
|---|---|---|---|
| Fotogramas | monitor, ventana o vídeo, redimensionado al lado mayor del preajuste | vídeo, muestreado dos veces (plan de resolución e intervalo de fusión) | [Captura](reconstruction-capture.md) |
| Fotogramas clave | se conservan según cuánto cambió la imagen, con umbral adaptado a la captura | cada `--fuse-interval` segundos | [Captura](reconstruction-capture.md#keyframes) |
| Máscaras | `ScreenMask` basada en cambios, luego `FlowMask` basada en flujo después de 40 fotogramas clave | `FlowMask` aprendida de cuatro pasadas del vídeo; no se aplica al solucionador | [Captura](reconstruction-capture.md#what-is-not-the-world) |
| Profundidad | modelo ONNX en el mejor backend de GPU | Depth Anything V2 Small en PyTorch | [Profundidad](reconstruction-depth.md) |
| Pose | odometría visual, o telemetría exacta de Forza | ventanas de VGGT unidas en una sola trayectoria, interpolada | [Pose](reconstruction-pose.md), [Sin conexión](reconstruction-offline.md) |
| Escala | altura de la cámara sobre el suelo (1,15 m) una vez, o telemetría | las unidades de la trayectoria resuelta | [Pose](reconstruction-pose.md#scale) |
| Fusión | ocupación ponderada, vóxeles dispersos; cuadrícula de cobertura | lo mismo | [Fusión](reconstruction-fusion-and-texture.md) |
| Salida | `.glb`, partes suelo/estructura, color por vértice, en centímetros | lo mismo | [La salida .glb](glb-output.md) |

Código: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - la configuración y el ritmo de un escaneo; `reconstruct.py` - fotogramas clave convertidos en geometría;
`offline.py` - la ruta sin conexión), con las etapas en `capture/`, `depth/`, `pose/`, `fusion/`
y `geometry/`.

## De dónde viene la precisión {#where-accuracy-comes-from}

La profundidad monocular solo es correcta salvo una escala desconocida: una foto de una habitación y de una casa de muñecas son la misma imagen. Así que la red se encarga de lo que hace bien (forma relativa, bordes, estructuras finas), y la escala y la trayectoria de la cámara vienen de algún sitio que las conoce:

| Juego | Trayectoria de la cámara | Escala |
|---|---|---|
| Forza Horizon / Motorsport con telemetría activada | exacta, desde Data Out, interpolada al instante de captura de cada fotograma | exacta: la profundidad se ancla triangulando características entre dos poses conocidas |
| Cualquier otro, en vivo | odometría visual, encadenada fotograma a fotograma | fijada una vez a partir de una altura de cámara supuesta sobre el suelo |
| Una grabación, sin conexión | VGGT, resuelta en ventanas solapadas | las unidades de la solución (no métricas) |

El único número que el escáner recibe en lugar de medirlo es el **campo de visión horizontal** del juego (90 grados por defecto en la ventana; en juegos de carreras suele ser cercano a 65). Si es demasiado estrecho, el nivel se reconstruye más profundo de lo que es; si es demasiado ancho, se aplana.

## Avisar al usuario pronto {#telling-the-user-early}

Un escaneo es un acto físico: alguien camina por un nivel durante varios minutos, y el fallo caro es terminar la caminata y descubrir que no sirvió. Por eso la ventana mide el rendimiento de profundidad de esta máquina antes de que pueda empezar nada y dice cómo será el escaneo ([Entorno de ejecución](runtime.md#what-to-expect-from-this-machine)); durante el escaneo muestra un mapa de cobertura con puntos débiles numerados, el estado del seguimiento, una barra de velocidad al caminar, una barra de nitidez y una sola instrucción cada vez, tanto en la ventana como en una superposición sin bloqueo sobre el juego ([La ventana de escaneo](reconstruction-scan-ui.md)).

## Medido sobre verdad de referencia sintética {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` dibuja una habitación de 12 x 8 m (4 m de alto) desde una trayectoria de cámara conocida, con profundidad analítica (no de la red), y la reconstruye con vóxeles de 0,2 m. Comprueba que más del 90 % de los fotogramas quedan colocados, que el error medio de la trayectoria es menor de 0,35 m (el peor, menor de 1 m), que la distancia recorrida está dentro del 10 % de la real, que la anchura de la habitación sale bien con un margen de 1,5 m, que más del 75 % de la superficie de las paredes queda a menos de 0,45 m de una pared real, que un recorrido tipo inspección puntúa claramente mejor en cobertura que caminar en línea recta, y que una escena sin rasgos se rechaza en lugar de inventarla. La profundidad analítica aísla la pose, la escala y la fusión de la red; cómo se comporta la red con partidas reales es otra pregunta que ninguna escena sintética responde. `tests/test_track_width.py` comprueba que una vuelta conducida fuera del centro de una carretera de anchura conocida reconstruye la anchura de la carretera, y no solo la línea conducida.

## Páginas {#pages}

- [La ventana de escaneo](reconstruction-scan-ui.md) - cada control, atajo de teclado y elemento de superposición
- [Captura, máscaras y calidad de fotograma](reconstruction-capture.md)
- [Profundidad](reconstruction-depth.md)
- [Pose de la cámara y escala](reconstruction-pose.md)
- [Fusión, cobertura y color](reconstruction-fusion-and-texture.md)
- [La salida .glb](glb-output.md)
- [Reconstrucción sin conexión](reconstruction-offline.md)
