---
title: "Fusión, cobertura y color"
nav_order: 5
lang: "es"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusión, cobertura y color {#fusion-coverage-and-colour}

Código: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Cada fotograma clave colocado actualiza a la vez dos rejillas dispersas: el **volumen
de superficie**, que se convierte en la malla, y la **rejilla de cobertura**, que dice
cuánto creerle y adónde volver. Ambas se actualizan por fotograma clave, no al final,
porque el mapa de cobertura es lo que guía al jugador.

## De la profundidad a los puntos {#from-depth-to-points}

Para cada fotograma clave cuya pose es conocida **y** cuya profundidad tiene escala:

1. Se usa cada segundo píxel en cada dirección (`PIXEL_STRIDE = 2`; los píxeles vecinos
   de una misma superficie no son mediciones independientes).
2. La profundidad se convierte a metros con el ajuste afín del fotograma.
3. Se conserva solo entre **0,35 m** (más cerca está el arma, el HUD, el capó) y
   **60 m** (el error monocular crece aproximadamente con el cuadrado de la distancia,
   así que los puntos lejanos son ruido con forma de geometría), y solo en los píxeles
   del mundo de la máscara.
4. Se levanta a través del modelo de cámara y se lleva al mundo con la pose.
5. Cada punto lleva el color del píxel.

Un fotograma que está colocado pero no tiene escala de profundidad se cuenta como
*colocado* pero no *fusionado*.

## El volumen de superficie {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - el vóxel es el "Surface detail" de la ventana.

### Ocupación ponderada, no un TSDF {#weighted-occupancy-not-a-tsdf}

Un campo de distancia con signo truncado talla a lo largo del rayo de cada píxel y
acierta con las estructuras finas y el espacio libre limpio, porque sabe que el rayo
pasó *a través* del espacio vacío. Eso significa recorrer el rayo para cada uno de
cientos de millones de píxeles. Este volumen en cambio acumula una **ocupación
ponderada** por vóxel y aplica marching cubes al resultado suavizado: lo bastante rápido
para ejecutarse mientras se escanea, en una máquina sin una GPU útil, y la salida es una
superficie cerrada en lugar de una nube de puntos. El coste: las estructuras finas y el
espacio libre salen peor de lo que daría un TSDF.

### Integrar un fotograma {#integrating-a-frame}

- Los puntos se agrupan en vóxeles (`floor(punto / voxel)`).
- Cada vóxel tocado recibe `peso x sqrt(recuento / recuento_máximo)`, donde `recuento`
  es cuántos puntos del fotograma cayeron en él y `peso = max(0,1; confianza de la
  pose)`. Raíz cuadrada: a partir de cierto punto, más píxeles de la misma superficie
  desde el mismo sitio dejan de ser evidencia; ponderar por la confianza de la pose
  evita que una pose dudosa mueva la superficie.
- El color es una media ponderada en marcha por vóxel.

La rejilla es **dispersa**: un recorrido andado toca una fracción diminuta de su caja
envolvente. Las coordenadas de vóxel se empaquetan en una clave de 64 bits (21 bits por
eje, hasta ±1.048.575 vóxeles - a 0,25 m, unos ±262 km) y se buscan con un array
ordenado y búsqueda binaria, totalmente vectorizado.

### Extraer la malla {#extracting-the-mesh}

1. Se descartan los vóxeles con peso inferior a **0,35** (los puntos sueltos en los bordes
   de silueta se volverían picos).
2. Los pesos se escalan por el **percentil 75** de todo el escaneo y se recortan a 1.
3. El espacio ocupado se corta en **bloques de 64 vóxeles** por lado, cada uno con un
   **halo de 3 vóxeles** de los datos de sus vecinos (sin él, cada borde de bloque se
   cerraría en una pared y una carretera saldría como una fila de cajas).
4. El campo de cada bloque se suaviza con una gaussiana (sigma 0,8 vóxel) para quitar la
   arruga que deja el ruido de profundidad.
5. **Primera pasada**: el percentil 99 del campo suavizado, muestreado en todos los
   bloques (como máximo 2 millones de valores), fija una escala de nivel global. Normalizar
   bloque a bloque promovería un valor atípico aislado a superficie completa dentro de su
   bloque vacío.
6. **Segunda pasada**: el campo de cada bloque se divide por esa escala y se aplica marching
   cubes con **0,5**. Un triángulo pertenece al bloque en el que cae su **centroide**, así
   que los triángulos que cruzan una costura se emiten exactamente una vez.
7. Los vértices pasan a unidades del mundo en los centros de los vóxeles; cada vértice
   toma el color de su vóxel (gris medio donde cae fuera de un vóxel ocupado).

La extracción por bloques es lo que hace posible un escaneo del tamaño de un circuito:
un único array denso sobre una caja de un kilómetro cuadrado a 0,25 m tendría miles de
millones de celdas. `tests/test_track_scale.py` comprueba que funciona a esa escala con
una memoria proporcional a lo escaneado.

### Suelo y estructura {#ground-and-structure}

`classify` etiqueta cada triángulo según su normal (orientada con las normales de vértice
extraídas): a **35 grados de la vertical** es `ground` (suelo), todo lo demás `structure`
(estructura). El visor dibuja el suelo sólido y las estructuras casi transparentes.
**El agua nunca se identifica como tal**: no se distingue del suelo plano por la forma, y
una etiqueta equivocada pintaría un patio como un lago. Cada etiqueta se convierte en una
parte del `.glb` ([La salida .glb](glb-output.md)).

## Cobertura {#coverage}

`CoverageGrid(voxel=0.5)` registra, por celda de medio metro, cuatro cosas que no son lo
mismo:

| Término | Almacenado | Puntuación (cada una recortada a 0..1) | Por qué cuenta por separado |
|---|---|---|---|
| Cuántas veces se vio | número de fotogramas clave que vieron la celda | `recuento / 3` | verla una vez es una suposición sin nada con qué promediarla |
| Desde cuántas direcciones | suma de vectores unitarios de visión | `(1 - dispersión) / (1 - 0,93)`, donde dispersión = longitud de la suma / recuento | veinte fotogramas que caminan rectos hacia una pared no tienen paralaje entre ellos; dos vistas separadas treinta grados valen más |
| Desde qué distancia | distancia de visión más cercana | `1 - más_cercana / 40 m` | el error de profundidad crece aproximadamente con el cuadrado de la distancia |
| Qué tan bien se colocó la cámara | mejor confianza de pose | la confianza | la geometría fusionada con una pose dudosa cae en el sitio equivocado |

Los píxeles de un fotograma se agrupan primero por celda, de modo que diez mil píxeles de
una misma pared cuentan como una observación desde una dirección.

**Calidad = el producto de los cuatro términos**, no la media: son condiciones que tienen
que cumplirse todas. Un lugar visto doscientas veces desde una sola dirección a sesenta
metros está mal observado, y una media lo ocultaría detrás de un término excelente.

Cifras principales (`summary`): celdas ocupadas, la proporción con calidad de al menos
0,5 ("% bien visto" en la ventana), calidad media y volumen.

### Zonas débiles {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. las celdas con calidad por debajo de 0,35 son débiles;
2. las celdas débiles se agrupan por **conectividad** (vecindad de 26, union-find solo
   sobre las celdas ocupadas - no una trama sobre la caja envolvente, que en un recorrido
   largo son millones de celdas vacías);
3. se ignoran los grupos de menos de 8 celdas;
4. el motivo de cada grupo es el término *más débil* más frecuente de sus celdas, y su
   posición la media de sus celdas;
5. se ordenan del más grande al más pequeño (y después por peor calidad), como máximo 8.

| Motivo | Consejo mostrado |
|---|---|
| pocas vistas | Visto solo una o dos veces: vuelve a pasar por ahí. |
| una dirección | Visto solo desde un ángulo. Da un paso de lado y míralo otra vez. |
| lejano | Visto solo desde lejos. Acércate. |
| mal seguimiento | La cámara no estaba bien localizada aquí. Acércate más despacio. |

La conectividad importa: agrupar por una rejilla de bloques fija informa de una sala
lateral descuidada como muchos anillos separados, y nadie puede distinguir ocho lugares
de uno solo contado ocho veces.

### La vista en planta {#the-plan-view}

`top_down(resolution)` proyecta las celdas sobre x/z y conserva la **mejor** calidad por
columna (alguien de pie en una sala tiene mala cobertura del techo y excelente cobertura
del suelo; promediar pintaría la sala de ámbar). Las columnas nunca observadas se marcan
aparte. La ventana la dibuja a 200 x 200, la superposición a 120 x 120 ([El mapa de cobertura](reconstruction-scan-ui.md#the-coverage-map)).

### ¿Se puede reconstruir? {#is-this-reconstructable}

Cada 25 fotogramas fusionados, una vez que hay al menos 500 celdas:

| Conclusión | Veredicto | Mensaje (resumido) |
|---|---|---|
| menos del 2 % de las celdas tiene dispersión de visión por debajo de 0,93 | no reconstruible | Casi nada de paralaje. O la cámara nunca mira de lado, o el seguimiento deriva y la misma superficie nunca cae dos veces en el mismo sitio. Revisa el número de fotogramas colocados: si es alto, es deriva. |
| distancia mediana a la más cercana por encima de 25 m | no reconstruible | Todo se vio desde N m o más lejos... Acércate a lo que quieras. |
| menos del 6 % con buena dispersión | reconstruible, con aviso | Paralaje escaso: la geometría saldrá basta. Moverte de lado respecto a lo que miras ayuda más. |

El poco paralaje tiene dos causas que esto no puede distinguir, por eso el mensaje
nombra ambas.

## Color {#colour}

El color por vóxel de la fusión es barato y en directo, y borroso: cada píxel de una
celda de cuarto de metro se promedia, incluidos los vistos de canto desde treinta metros.
Así que en la exportación la malla se vuelve a colorear, una vez, a partir de los propios
fotogramas:

- **Fotogramas conservados**: hasta **160** fotogramas clave (imagen y pose), elegidos por
  muestreo de depósito para repartirse por todo el escaneo en lugar de por su cola.
- **Por vértice** (`project_colours`), cada fotograma conservado aporta si el vértice está
  delante de la cámara y dentro de la imagen, la superficie está girada no más de unos 70
  grados respecto a mirar de frente a la cámara (`|normal . vista| > 0,34`), está más cerca
  que **35 m**, y nada más cercano se interponía delante de él (ver abajo).
- Cada una de esas vistas se puntúa como `frontalidad x (1 - distancia / 35)`, así que una
  vista cercana y frontal vence a una lejana y oblicua. Se conservan las **4 vistas con
  mejor puntuación** de cada vértice - sea cual sea el orden de los fotogramas, una vista
  mejor reemplaza a la más débil de las cuatro - y se mezclan, ponderadas por esa misma
  puntuación.
- **Oclusión**: en cada fotograma, los vértices propios de la malla visibles se dibujan en un
  búfer de profundidad de celdas de 2 píxeles, conservando el más cercano por celda. Un
  vértice más de `0,3 m + 5 %` de su distancia detrás del más cercano de su celda estaba
  oculto en ese fotograma - una pared entre la cámara y la carretera del fondo - y esa vista
  no cuenta. La prueba solo conoce la malla: un oclusor que nunca se fusionó (un coche que
  pasa, un pilar de la cabina fuera de la máscara del HUD) no se detecta.
- Un vértice que ningún fotograma vio conserva su color de vóxel; uno que no tiene ninguno
  es gris medio (el negro se leería como un agujero).

El color se escribe como `COLOR_0` por vértice, no como un atlas de texturas. El aspecto
predeterminado del visor es un mapa gris bajo un calor saturado; el color sirve para
encontrar la carretera en un circuito escaneado, donde la geometría sola no separa el
asfalto del arcén, y se muestra tras el interruptor *Color capturado* del panel *Fondo / nivel*
del visor. Un atlas multiplicaría el tamaño del archivo y necesitaría un paso de desenrollado de
UV, para una vista que deliberadamente no es la predeterminada. Blender y otras
herramientas de glTF leen `COLOR_0`.
