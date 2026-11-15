---
title: "Pose de la cámara y escala"
nav_order: 4
lang: es
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Pose de la cámara y escala {#camera-pose-and-scale}

Un mapa de profundidad dice a qué distancia está cada cosa de *un* punto de vista.
Para convertir muchos de ellos en un solo nivel hay que saber dónde estaba cada punto de
vista, y en qué unidades. Esta página cubre las rutas en directo; la resolución
sin conexión en avance está en [Reconstrucción sin conexión](reconstruction-offline.md).

Código: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## El modelo de cámara {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` construye una cámara estenopeica a partir del
**campo de visión horizontal** que fijas en la ventana: `fx = (ancho / 2) / tan(fov / 2)`,
píxeles cuadrados (`fy = fx`), el punto principal en el centro del fotograma. Un juego no
publica su proyección, así que este es el único número supuesto: si es demasiado estrecho,
la escena parece más profunda de lo que es. La ruta sin conexión usa 65 grados.

Una `Pose` se guarda **mundo-desde-cámara**: `rotation` (3 x 3) y `translation` = el centro
de la cámara en el mundo, que es lo que quieren la trayectoria, el mapa de cobertura y la
superposición.

## Odometría visual (la predeterminada) {#visual-odometry-the-default}

`VisualOdometry` sigue cada fotograma clave respecto al anterior:

1. **Rasgos**: ORB, hasta 1500 por fotograma, detectados solo sobre la máscara del mundo
   (ver [Captura](reconstruction-capture.md#what-is-not-the-world)).
2. **Coincidencias** con el fotograma clave anterior: fuerza bruta, distancia de Hamming,
   con validación cruzada (solo pares mutuamente mejores).
3. **Elevar a 3D**: la profundidad del fotograma anterior ya está en unidades del mundo, así
   que sus píxeles emparejados se convierten en puntos del mundo.
4. **Colocar la cámara**: `solvePnPRansac` entre esos puntos (error de reproyección 3 px,
   confianza 0,999, 200 iteraciones). La traslación sale en las mismas unidades, así que **la
   escala cruza el hueco**.
5. **Anclar la profundidad de este fotograma**: su propia inversa de profundidad predicha se
   ajusta (`fit_scale`) contra las profundidades de los inliers de PnP, y el ciclo se repite.

El **primer fotograma** es el origen: pose identidad, y su afín de profundidad es la
calibración del suelo de abajo o, sin ella, la identidad (la reconstrucción queda entonces
autoconsistente pero sin unidades).

Una pose necesita al menos **18 inliers de RANSAC** - claramente más que el mínimo de PnP,
que es seis, ya que una solución con apenas los puntos necesarios es justo la que se equivoca
con confianza.

### Confianza {#confidence}

Cada fotograma colocado recibe una confianza entre 0 y 1 que pondera su fusión y su
cobertura:

| Pose procedente de | Confianza |
|---|---|
| telemetría | 1,0 |
| una resolución de alimentación directa | 0,85 |
| seguimiento visual | `inliers / coincidencias x min(1, inliers / 60)` |

### Cuando el seguimiento se rompe {#when-tracking-breaks}

Un fotograma que no se puede colocar se informa, nunca se adivina: `no features in the frame
(N found)`, `too few matches to place the camera`, `could not relocalise`. No se registra
ninguna pose, y no se fusiona nada. Continuar desde la última pose, o empezar un origen nuevo,
pondría el siguiente tramo de nivel en un desplazamiento arbitrario - una costura que parece
geometría real.

Tras una ruptura, cada fotograma nuevo se **relocaliza** frente a una base de datos de
fotogramas clave pasados (se añade cada 4.º fotograma seguido, hasta 120, descartando el más
antiguo), empezando por el más reciente, con el mismo paso de coincidencia y PnP. Hasta que
una funciona, los fotogramas se descartan. Un fotograma recuperado continúa en el mismo marco
de coordenadas. Las recuperaciones se cuentan y se muestran en la ventana (`N recovered`).

### Cierre de bucle: desactivado {#loop-closure-off}

La misma base de datos admite el cierre de bucle: comparar con fotogramas clave de mucho antes
para detectar que se vuelve a un lugar y encajar la trayectoria de nuevo en él. **Está
desactivado por defecto, y el escáner nunca lo activa** (`Reconstructor(loop_closure=False)`).
En escenarios repetitivos - un tramo de rally, un pasillo, una fila de árboles - cada tramo se
parece a cualquier otro, y la coincidencia de rasgos confirma revisitas falsas, lo que fija la
cámara cerca de donde empezó mientras sigue conduciendo. Hacerlo bien necesita reconocimiento
de lugar (un vocabulario de bolsa de palabras o un descriptor aprendido) y verificación
geométrica contra un mapa, que no está construida.

Cuando se activa desde código, un cierre necesita: un fotograma clave de al menos 60
fotogramas clave de antigüedad, a menos de 6 m de la pose actual, emparejado con al menos 90
inliers, que mueva la pose más de 0,02 m y menos de 6 m. Aun así, solo reemplaza la pose
actual; no es un grafo de poses y no mueve los fotogramas anteriores ni la geometría ya fusionada.

## Poses de telemetría {#telemetry-poses}

Con **Racing telemetry (Forza) -> Listen for position data** activado, la trayectoria de la
cámara viene de Data Out de Forza en lugar de las imágenes (`ForzaPoseSource`):

- Un hilo escucha en `127.0.0.1:<puerto>` (5300 por defecto) con la misma detección de diseño
  que los grabadores ([Forza](telemetry-forza.md)); los paquetes se usan mientras `isRaceOn`
  esté activo. Un puerto ocupado se informa, no se lanza: la telemetría es una mejora y el
  escaneo continúa visualmente.
- Cada paquete se marca con el **tiempo monótono en que llegó** - el mismo reloj con el que la
  captura marca los fotogramas. El sello de tiempo propio del juego cuenta desde algo sin
  relación, así que no se usa para alinear. Un retardo de bucle local de uno o dos milisegundos
  son unos 6 cm a 200 km/h.
- Se guarda un búfer continuo de 30 segundos. La pose de un fotograma se **interpola** a partir
  de las muestras a ambos lados de su momento de captura: la posición linealmente, la rotación
  por interpolación esférica (una matriz mezclada no es una rotación y deformaría cada punto).
  A través de un hueco de más de **0,35 s**, o fuera del búfer, no hay pose.
- `pose_from_forza`: la cámara se coloca en el coche (el desplazamiento de una cámara de
  persecución no se publica). **Las posiciones se conservan exactamente como las envía el
  juego**: el mundo de Forza ya es Y hacia arriba (x y z sobre el mapa, y la altura), que es
  como lo escriben los archivos de vuelta y de ruta, así que la superficie cae en las mismas
  coordenadas que las vueltas grabadas sobre ella. (Una versión anterior intercambiaba y y z
  para un mundo "Z hacia arriba" y tumbaba el circuito de lado.)
- La rotación es guiñada, luego cabeceo, luego alabeo, con los sentidos leídos de vueltas
  grabadas: la dirección de marcha `atan2(dx, dz)` es igual a la guiñada, la pendiente subida
  es igual a menos el cabeceo (positivo es morro abajo), y el alabeo es positivo cuando la
  suspensión derecha está comprimida (positivo baja el lado derecho). Los ejes del coche (x a la
  derecha, y arriba, z hacia delante) se convierten en los de la cámara (x a la derecha, y hacia
  abajo, z hacia delante) invirtiendo y.
- El mundo de Forza es **zurdo** y el marco de la cámara no, así que la matriz resultante
  mundo-desde-cámara es un reflejo (determinante -1), y el escaneo sale zurdo como los archivos
  de vuelta. La interpolación no se ve afectada (el giro entre dos de estas poses es una
  rotación propia).
- Cuando un fotograma no tiene pose de telemetría (un hueco), el reconstructor recurre al
  **seguimiento visual** para ese fotograma, partiendo de la última pose de telemetría, y vuelve
  a las poses de la fuente en cuanto esta responde. PnP solo devuelve rotaciones, así que en un
  mundo reflejado se resuelve con el mundo reflejado a través de z y el reflejo se vuelve a
  aplicar al final; el fotograma cae en las coordenadas del juego. Solo si el seguimiento visual
  también falla, el fotograma queda sin seguimiento.

### Escala de profundidad a partir de la telemetría {#depth-scale-from-telemetry}

El juego dice dónde está la cámara, no a qué distancia está nada, así que la profundidad de
cada fotograma todavía necesita anclarse - pero no encadenando desde el fotograma cero, cuya
unidad es arbitraria mientras las poses están en metros. En su lugar, los rasgos emparejados
entre el fotograma anterior y el actual (al menos 8) se **triangulan directamente desde las dos
poses conocidas**, en metros, y el mapa de profundidad se ajusta a los puntos delante de la
cámara. Cada fotograma se ancla contra la telemetría, así que no hay cadena que derive.

Si las dos poses están a menos de **0,05 m** la una de la otra, los rayos son casi paralelos y la
triangulación es ruido, así que el fotograma queda sin anclar: posicionado exactamente, pero no
fusionado ("positioned, but its depth has no scale yet"). Por eso la ventana cuenta por
separado los fotogramas *colocados* y los *fusionados*.

## Escala {#scale}

La odometría visual encadena bien la escala relativa, pero todo el nivel sigue flotando sobre
un factor desconocido. La salida relativa de Depth Anything sale en unidades arbitrarias, así
que dejar el primer fotograma en la identidad pone el mundo a metros de la cámara en un tamaño
arbitrario.

`GroundCalibrator` fija ese factor a partir de **la altura de la cámara sobre el suelo**, medida
en el **primer fotograma clave** y, si ese no tiene suelo utilizable, en los siguientes:

- Altura de la cámara: **1,15 m** (la línea de visión de un conductor) - la ventana siempre usa
  este valor; los scripts pueden pasar 1,70 m (`WALKING_HEIGHT`, un jugador de pie) o `None`
  (sin calibración).
- Muestra del suelo: filas entre el 62 % y el 92 % desde arriba (bajo el horizonte, sobre el
  capó o el arma) y columnas entre el 30 % y el 70 % de ancho (lejos de los arcenes).
- Cada píxel de ahí con una predicción utilizable se eleva con profundidad `1 / predicho` en las
  unidades de la red; los puntos bajo el eje óptico dan una altura por debajo de la cámara. Su
  mediana es la altura de la cámara en unidades de la red, así que `metros por unidad = 1,15 /
  mediana`, y el afín del fotograma es `escala = 1 / metros_por_unidad`, desplazamiento 0.
- Solo se confía con al menos 200 muestras de suelo y una **dispersión** (desviación absoluta
  mediana dividida por la mediana) por debajo de **0,60**.
- En el primer fotograma clave el ajuste se convierte en la unidad del origen, así que el escaneo
  está en metros desde el principio. Cuando el primer fotograma clave no tiene suelo utilizable,
  el escaneo empieza sin unidades y se prueba cada fotograma seguido posterior, hasta **30
  fotogramas** en total. El primero que se calibra da *metros por unidad*: la mediana, sobre la
  banda del suelo, de la profundidad que implica su suelo dividida por la profundidad que dio la
  cadena para ese fotograma. Todo lo ya fusionado está en la unidad del primer fotograma, así
  que el factor no se realimenta a la cadena; se aplica a todo el nivel (y a los puntos marcados)
  cuando se escribe, y a la distancia que se muestra mientras tanto. El tamaño del vóxel está
  entonces en unidades del primer fotograma, así que su tamaño en metros difiere del ajuste en
  ese factor.
- Tras 30 fotogramas sin suelo, el escaneo se queda sin unidades, y lo dice.
- Con telemetría, no se prueban más fotogramas clave: la profundidad se ancla a los metros de la
  telemetría.

Estar dentro del diez por ciento del tamaño real es mejor que estar fuera por un factor de mil;
la telemetría, cuando está disponible, lo hace innecesario. La nota se muestra en la ventana
bajo la línea de seguimiento, como `Size: ...`: `measuring the ground`, `no flat ground in view
yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (con `found on
frame N, so the level is scaled by F when it is written` cuando llegó más tarde), `no usable
ground in the first N frames - sizes are relative, not metres`, o `in metres, from the
telemetry's positions`.

## Ajuste de haces y trayectorias largas (no conectado) {#bundle-adjustment-and-long-tracks-not-wired-in}

Hay dos piezas para un solucionador por ventanas futuro que **el escáner no usa**:

- **`FeatureTracks`** mantiene la identidad de los rasgos a lo largo de cientos de fotogramas
  con seguimiento Lucas-Kanade (600 rasgos, se vuelven a sembrar por debajo del 60 %, tolerancia
  directa-inversa de 1 px, rasgos nuevos a 10 px de los existentes), que es lo que necesita el
  ajuste de haces - la coincidencia de descriptores entre fotogramas consecutivos solo da pares.
- **`bundle_adjust`** refina una ventana de poses y puntos a la vez con
  `scipy.optimize.least_squares` (región de confianza, pérdida soft-L1 con escala de 2 px, un
  patrón de dispersión del jacobiano explícito, cámaras fijas restauradas exactamente). Probado
  contra verdad conocida en `tests/test_bundle.py`.

`WindowedOdometry` combina ambos (ventanas de 12 fotogramas clave, una resolución cada 3 fotogramas
clave, las dos primeras cámaras fijas, puntos con más de 6 px de error descartados, saltos de más
de 6 veces el paso reciente rechazados). Su docstring deja constancia de que, con imágenes reales,
**colapsó la trayectoria y fue mucho más lenta** que el seguimiento fotograma a fotograma, con la
libertad de escala y un arranque basado en profundidad como causas conocidas, y una tercera causa
sin identificar. Así que la odometría fotograma a fotograma sigue siendo la predeterminada; la
corrección probable que anota el código es un arranque de dos vistas con matriz esencial y la
línea base fijada a partir de la calibración del plano del suelo.
