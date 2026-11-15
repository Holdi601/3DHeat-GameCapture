---
title: "La salida .glb"
nav_order: 6
lang: "es"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# La salida .glb {#the-glb-output}

Una reconstrucción se escribe como un archivo glTF 2.0 binario (`.glb`) que el visor de 3DHeat carga desde su panel Fondo / nivel sin ningún tratamiento especial: el mismo contrato que escribe el exportador de Unreal. Código: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Se escribe a mano en lugar de con una biblioteca de glTF: la salida es un subconjunto reducido (un solo búfer, empaquetado sin huecos, sin animación ni skinning), y una dependencia que sabe escribir todo glTF traería sus propios conflictos de versiones, a cambio de ahorrar unos pocos cientos de líneas.

## Qué contiene el archivo de un escaneo {#what-is-in-a-scans-file}

| Parte (nombre del nodo y de la malla) | Contenido |
|---|---|
| `ground:<name>` | triángulos a menos de 35 grados de mirar hacia arriba |
| `structure:<name>` | todo lo demás |

`<name>` es el nombre del archivo sin extensión al guardar desde la ventana, o el nombre del vídeo para `reconstruct`. Una parte sin triángulos se omite. Un escaneo nunca escribe una parte `water:`. `asset.generator` es `heat3d-capture-scan`.

## El contrato {#the-contract}

- **Un nodo por parte**, con el nombre de la parte como etiqueta; la malla repite el nombre. El visor lee primero el nombre del *nodo*, así que nombrar solo las mallas perdería la clasificación.
- La etiqueta es `<class>:<name>`, con clase `ground`, `structure` o `water`: el prefijo que el visor reconoce (`^(ground|structure|water)\s*[:|]`) para tomar la clase tal cual en lugar de adivinarla a partir de la geometría. El suelo se dibuja sólido y las estructuras casi transparentes.
- **Las coordenadas están en el espacio del visor**: Y hacia arriba, sistema diestro, y **escaladas a centímetros** (metros x 100) para coincidir con el exportador de Unreal, de modo que una captura y una exportación del motor del mismo lugar se cargan con el mismo tamaño y la misma cámara por defecto. El `extras.unit_metres` de nivel superior del archivo es `0.01` (una unidad es un centímetro), así que un lector que trabaje en metros, como [`locate`](locate.md), lo toma a su tamaño real. Un escaneo colocado con la telemetría de Forza es la excepción en cuanto a lateralidad: se queda en el mundo propio del juego, Y hacia arriba y sistema zurdo, exactamente como los archivos de vuelta, para que las vueltas grabadas sobre él caigan encima. Cuando la escala de un escaneo se halló en un fotograma clave posterior ([Escala](reconstruction-pose.md#scale)), ese factor se incorpora a la escala escrita.
- `COLOR_0` lo lee el visor, que sombrea el suelo con él cuando el interruptor *Color capturado* del panel Fondo / nivel está activado (desactivado por defecto).
- Un escaneo con puntos marcados a mano recibe un `<name>.marks.json` junto a él; véase [Guardar](reconstruction-scan-ui.md#saving).
- Por primitiva: `POSITION` (VEC3 float, con `min` y `max`, desde los que el visor encuadra la cámara), `NORMAL` (VEC3 float), `COLOR_0` opcional (VEC3 float, 0..1), `TEXCOORD_0` opcional; índices de 16 bits cuando todos son menores que 65.536, y de 32 bits en caso contrario; modo triangles.
- Cada vista de búfer empieza alineada a 4 bytes; el fragmento JSON se rellena con espacios y el fragmento BIN con ceros hasta 4 bytes.

## Comprobaciones antes de escribir {#checks-before-writing}

Cada parte se valida y se rechaza, indicando su nombre en el mensaje, cuando no tiene vértices, cuando el número de índices no forma triángulos completos, cuando un índice está fuera de rango o es negativo, cuando las posiciones no son finitas, o cuando las normales o los colores no coinciden con el número de vértices. Las normales se calculan si faltan, **ponderadas por área** (el marching cubes deja astillas junto a las caras grandes, y un promedio sin ponderar deja que los triángulos diminutos decidan por la cara sobre la que están); un vértice degenerado recibe "arriba". No escribir ninguna parte es un error.

La exportación no devuelve nada -y la ventana muestra "Nada que guardar"- cuando el volumen no produce ninguna superficie, en lugar de escribir un archivo vacío que parecería un escaneo correcto.

## Texturas {#textures}

El escritor admite una textura PNG de color base por parte (con UV, de doble cara, no metálica y totalmente rugosa). Los escaneos no la usan; llevan color por vértice. Véase [color](reconstruction-fusion-and-texture.md#colour).

## El nivel de referencia {#the-reference-level}

`geometry/reference.py` construye un nivel sintético de tamaño exactamente conocido con el mismo escritor: un suelo subdividido de 400 m, tres edificios de 20 x 20 x 12 m y un estanque de 50 m a 1,5 m bajo el suelo, cada clase en un color plano distinto. Las pruebas del propio visor lo generan y lo analizan con su analizador real, así que el formato del archivo se prueba en ambos lados sin juego ni hardware de captura.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
