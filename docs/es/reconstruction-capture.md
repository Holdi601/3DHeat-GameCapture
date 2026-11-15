---
title: "Captura, máscaras y calidad de fotograma"
nav_order: 2
lang: "es"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Captura, máscaras y calidad de fotograma {#capture-masks-and-frame-quality}

Código: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## De dónde vienen los fotogramas {#where-frames-come-from}

Un destino de origen es uno de estos:

| Destino | Origen | Notas |
|---|---|---|
| `monitor:<n>` | un monitor completo, en directo | "Whole screen" de la ventana, con el número en "Which" |
| `window:<título>` | una ventana, en directo | "A window" de la ventana, con su título |
| una ruta de archivo | un archivo de vídeo | "A video file" de la ventana; cualquier formato que OpenCV pueda leer |

### Captura en directo: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` usa el paquete `windows-capture`, que envuelve **Windows Graphics
Capture**, la API pública que usan las grabadoras de pantalla. No se inyecta nada
en el juego. El cursor no se captura y no se dibuja ningún borde amarillo de captura.

La biblioteca de captura entrega los fotogramas a una función de devolución en el
hilo del compositor y espera que retorne enseguida, así que la función solo copia
el fotograma (el búfer se reutiliza), convierte BGRA a RGB, lo redimensiona, le
pone sello de tiempo y lo mete en una cola de **4 fotogramas**. Cuando la cola está
llena se **descarta el fotograma más antiguo** y sube un contador: ir por detrás
debe costar fotogramas, no memoria ni corrección, y la vista en directo debe mostrar
dónde está el jugador ahora. Los fotogramas descartados aparecen en la línea de
estadísticas de la ventana, y si se descarta más de la mitad se muestra una sugerencia.

Cada fotograma lleva `t` (segundos desde que empezó la captura) y `monotonic` (el
`time.monotonic()` sin procesar en el momento de la captura), el mismo reloj con el
que se marcan los paquetes de telemetría, lo que permite alinear las poses de Forza
con los fotogramas.

`windows-capture` es opcional en la comprobación de dependencias: sin él, un archivo
de vídeo puede escanearse igualmente.

### Archivos de vídeo {#video-files}

`VideoSource` lee con OpenCV, convierte a RGB y redimensiona. Un contenedor sin
velocidad de fotogramas se trata como 30 fps. Las marcas de tiempo son el índice del
fotograma dividido por la velocidad; un archivo no tiene hora de reloj, así que la
telemetría no puede alinearse con un vídeo.

### Resolución {#resolution}

Los fotogramas se redimensionan en origen para que el lado más largo sea el lado de
captura del preajuste (Draft 640, Balanced 960, Detailed 1280 px), con
interpolación por área. Un fotograma 4K tiene treinta veces los píxeles que usa el
modelo de profundidad.

## Fotogramas clave {#keyframes}

Casi todos los fotogramas de una captura son redundantes: estar quieto produce
cientos de vistas de una misma cosa. Lo que quiere la reconstrucción es *paralaje*.
Así que un fotograma se conserva según **cuánto cambió la imagen desde el último
fotograma conservado**, no según un temporizador.

`picture_change(a, b)`:

1. ambos fotogramas a gris y a una rejilla de 16 x 16 de medias de bloque (las
   medias de bloque responden al movimiento de la imagen, no al grano, al follaje,
   al parpadeo ni al HUD);
2. la diferencia absoluta media, como fracción de 255;
3. cuando se conoce una máscara del mundo, cada bloque se pondera según la parte que
   es mundo y no cabina, de modo que un bloque medio salpicado de salpicadero cuenta
   la mitad (se usa cuando la máscara cubre más del 5 % del peso de la rejilla).

El umbral **se adapta a la captura**: durante los primeros 30 fotogramas es el valor
inicial del preajuste (0,020 / 0,010 / 0,004); después es el cuantil del preajuste
(0,85 / 0,65 / 0,40) de los últimos 240 cambios medidos, sin bajar nunca de 0,0001.
Un fotograma se conserva cuando su cambio alcanza el umbral; el primer fotograma
siempre se conserva. Un umbral fijo no sirve entre escenas: el cambio entre
fotogramas en una vuelta con cabina oscura es una pequeña fracción del de una sala
brillante y texturizada, mientras que "conservar el tercio más activo" significa lo
mismo en ambas. El umbral en uso sale con cada actualización de progreso
(`ScanProgress.threshold`), y las barras de velocidad al caminar de la ventana y de
la superposición miden el último cambio frente a él (`ScanProgress.toward_next_view`).

Solo los fotogramas conservados pasan por el modelo de profundidad y la
reconstrucción. Los fotogramas no se guardan salvo que alguien lo pida
(`keep_frames`); se conservan 160 para colorear la malla (ver
[color](reconstruction-fusion-and-texture.md#colour)).

Un escaneo termina cuando se detiene, cuando se acaba un vídeo, o al llegar al
límite de tiempo o de fotogramas clave.

## Lo que no es el mundo {#what-is-not-the-world}

Dos cosas de un fotograma de juego no son geometría del nivel, y ambas estropean
una reconstrucción:

- **El HUD.** La mira es el rasgo más repetible de cualquier fotograma. Un buscador
  de puntos la adora: coincide perfectamente entre cada par de fotogramas, y cada
  coincidencia es una prueba de que la cámara no se movió, lo que comprime toda la
  reconstrucción.
- **Lo que va sujeto a la cámara.** Un arma, el capó, el marco de la cabina, un
  salpicadero. Es geometría real en un sistema de coordenadas equivocado: fusionada,
  se corre a lo largo de todo el camino recorrido.

Dos detectores los encuentran. Ambos producen una máscara (255 = mundo, 0 = no
mundo) o `None` mientras no haya pruebas suficientes; `None` significa siempre "usar
todo", nunca "no usar nada".

La máscara se aplica:

- a la **detección de rasgos** en la odometría visual (enmascarar la mira de la salida
  mientras se deja que vote la pose arregla el síntoma visible y conserva el daño real);
- a los **píxeles fusionados**, de modo que no se fusiona geometría de cabina;
- a la medida de **nitidez y brillo**, porque una cabina siempre está perfectamente nítida;
- al **cambio de imagen** que decide los fotogramas clave.

**No** se aplica a los fotogramas que recibe el solucionador VGGT sin conexión (ver
[Reconstrucción sin conexión](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: lo que no cambia {#screenmask-what-does-not-change}

Se usa desde el primer fotograma clave hasta que FlowMask está listo.

- Cada fotograma se pasa a gris, se reduce a la mitad y se difumina (gaussiano 3 x 3)
  para que un temblor de un píxel en un elemento estático del HUD no parezca movimiento.
- La diferencia absoluta por píxel respecto al fotograma anterior se acumula en una
  media exponencial (decaimiento 0,9), de modo que la máscara sigue a un HUD que
  aparece o desaparece a mitad de escaneo.
- Solo aprende de fotogramas en los que se sabe que la cámara se mueve (en el
  escaneo: una vez que al menos un fotograma se ha seguido) - una cámara parada hace
  que todo sea estático.
- Tras **12** fotogramas de aprendizaje, un píxel es estático cuando su cambio medio
  está por debajo de **0,22** del cambio mediano del fotograma: es relativo, así que
  el umbral sigue a la velocidad del jugador.
- Si más del **45 %** del fotograma se lee como estático, la premisa ha fallado (un
  menú, una escena de corte) y no se enmascara nada.
- La máscara se erosiona un píxel (los bordes del HUD con antialiasing no pertenecen a
  ninguno de los dos lados) y se vuelve a escalar al tamaño completo.

Su nota en la ventana: `learning what is HUD (n/12 frames)`, `no HUD or attached
geometry detected`, o `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: lo que nunca se desplaza {#flowmask-what-never-travels}

Una cabina no es estática: las agujas se mueven, el cuentarrevoluciones tiembla, el
minimapa gira, así que un detector de cambios toma esos píxeles por mundo, y son los
peores rasgos que darle a un solucionador de pose. FlowMask se hace la pregunta mejor:
**¿qué rasgos persisten sin desplazarse?**

- En el escaneo en directo aprende una sola vez, de los primeros **40 fotogramas
  clave** (en gris); después sustituye a ScreenMask durante el resto del escaneo.
- Los fotogramas se cortan en ventanas de **30** fotogramas, solapadas a la mitad. En
  cada ventana se siembran hasta 800 esquinas (`goodFeaturesToTrack`, calidad 0,01,
  separadas 8 px) y se siguen con Lucas-Kanade piramidal (21 x 21, 4 niveles) con una
  **comprobación hacia delante y hacia atrás**: una pista cuyo flujo hacia atrás no
  cae a menos de 1 px de donde empezó se descarta, porque un seguidor que deriva hacia
  un patrón vecino fabricaría justo la firma de "persistente pero estático" que se
  busca. Las ventanas de menos de 20 fotogramas se omiten. Las ventanas cortas
  importan: en un recorrido largo casi todos los rasgos del mundo salen del encuadre y
  la evidencia se reduce a nada.
- El desplazamiento neto de cada rasgo que sobrevive se compara con el **2 % del ancho
  del fotograma**: por debajo, es "parado"; por encima, "en movimiento". Los recuentos
  se acumulan en una rejilla de **24 x 24** celdas de pantalla según dónde empezó cada
  rasgo.
- Una celda se bloquea cuando tiene al menos 2 rasgos parados y más parados que en
  movimiento, **y** al menos 3 de sus 8 vecinas también están bloqueadas (una celda
  aislada es ruido; el material oscuro produce muchas).
- Solo se conservan las regiones bloqueadas **conectadas al borde del fotograma**. Todo
  lo sujeto a la cámara llega a un borde de la pantalla; lo que está en el centro y no
  se desplaza es el punto de fuga: conduciendo hacia delante, la carretera recta
  delante no tiene flujo y es la geometría más deseada.
- La región superviviente crece una celda (el borde de un panel de instrumentos es un
  gradiente).
- Si más del **60 %** del fotograma quedaría enmascarado, no se enmascara nada: con
  imágenes nocturnas, la mayoría de las celdas no tienen ningún rasgo seguible, lo que
  se lee igual que un cuadrante.

Su nota: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the
frame — it never travels`, o, por encima del 60 %, un mensaje que explica que no
enmascara nada.

La ruta sin conexión aprende el mismo FlowMask a partir de 4 tandas de 90 fotogramas
consecutivos repartidas por el vídeo, a 960 x 540 ([Sin conexión](reconstruction-offline.md)).

## Calidad de fotograma y consejos {#frame-quality-and-advice}

`QualityWatcher` juzga cada fotograma clave y elige **una** instrucción, para que la
superposición pueda decir "ve más despacio" mientras todavía hay tiempo.

Por fotograma mide, solo en los píxeles del mundo (todos los píxeles si la máscara deja
menos del 5 %):

- **nitidez**: varianza del Laplaciano - la medida estándar de una sola pasada, y
  responde justo a lo que destruye el desenfoque por movimiento;
- **luminancia**: nivel de gris medio, 0-255.

La nitidez no tiene escala absoluta (una etapa nocturna y una calle soleada difieren
en un orden de magnitud, ambas enfocadas), así que se juzga frente a la **mediana
corriente de esta captura**: los últimos 90 fotogramas, y se necesitan 20 antes de
emitir ningún juicio. Cada fotograma se compara con el historial *anterior* a él, de
modo que un tramo largo borroso no arrastre la mediana hasta igualarse consigo mismo.

| Condición | Prueba |
|---|---|
| plano | nitidez de 1,0 o menos (una pantalla de carga, una pared, el cielo) |
| oscuro | luminancia por debajo de 26 |
| borroso | nitidez por debajo de 0,55 de la mediana, y no plano |

Los consejos aparecen en inglés, como en la ventana. El consejo, la primera coincidencia gana (ordenado por lo que más bloquea el escaneo):

| Situación | Consejo | Nivel |
|---|---|---|
| menos de 20 fotogramas | Getting a feel for the picture… | ok |
| plano | Nothing to measure — point the camera at the level, not at the sky. | stop |
| oscuro | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| borroso | Blurred — slow down. | warn |
| menos de la mitad de los fotogramas seguidos | Losing track — slow down and keep more of the level in view. | warn |
| menos del 40 % de los fotogramas seguidos fusionados | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| hay zonas débiles | N thin spots — the map marks them. | ok |
| en otro caso | Good — keep going. | ok |

El nivel da color al consejo de la superposición (verde / ámbar / rojo). La barra de
**nitidez** de la superposición es la nitidez del fotograma en relación con la mediana.
(El código también tiene "Blurred, and the camera is not moving. Check the capture." para
una cámara parada; el escaneo siempre informa de que la cámara se mueve, así que no se muestra.)
