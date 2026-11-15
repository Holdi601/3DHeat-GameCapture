---
title: Límites y verificación
nav_order: 9
lang: "es"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Límites y lo que está verificado {#limits-and-what-is-verified}

Una lista sincera: lo que las herramientas no hacen, y lo que no se ha comprobado con un juego en marcha.

## Telemetría {#telemetry}

| Grabador | Estado |
|---|---|
| Forza | Construido según la documentación oficial de Data Out; el diseño se detecta a partir de los propios paquetes. El lector de `.tele.gz` de FH Companion del visor se ha comprobado con vueltas reales. |
| AC, ACC, AC EVO, AC Rally | Probado con páginas sintéticas construidas a partir de los diseños publicados. **Todavía no se ha ejecutado con los juegos en vivo.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Probado con paquetes construidos a partir de los diseños documentados. **Todavía no se ha ejecutado con los juegos en vivo.** Los ejes, la actitud y las unidades de velocidad de RBR no están documentados y se manejan a partir de los datos. |
| BeamNG.drive | El grabador está probado con paquetes construidos a partir de la estructura del mod. **El mod no se ha ejecutado en el juego.** |
| Trackmania | El lector del CSV del visor está probado. **El plugin no se ha ejecutado en el juego.** Solo se carga en el modo de desarrollador de Openplanet. |
| iRacing | El lector `.ibt` del visor está probado con un archivo sintético. |

Otros límites de la telemetría:

- La normalización del deslizamiento de Forza no está documentada; el deslizamiento de Kunos se escala con un pico típico
  de asfalto, una aproximación.
- El sentido de algunos ejes laterales del coche (Kunos, DiRT) está documentado en ambos sentidos; el tamaño del ángulo de
  deriva es fiable, su signo no.
- Ninguno de los juegos de rally envía el deslizamiento de las ruedas; se deriva en el visor. RBR no envía velocidades de
  rueda.
- La superficie de un tramo de rally solo se escribe cuando se da `--surface`; si no, el archivo no nombra ninguna y el
  visor la infiere (nombre del tramo o del evento, luego el estilo de conducción, flexible por defecto).
- La detección de vueltas sin contador de vueltas (AC EVO, AC Rally, BeamNG) usa como línea el punto en el que empezó la
  grabación, así que empieza a grabar en la línea de salida.
- Un reinicio del vehículo en BeamNG cierra la vuelta abierta en ese momento: se escribe como un tramo parcial si cubrió la
  distancia mínima (300 m), y se descarta si no.
- `route` guarda cada 2 segundos más o menos mientras se conduce; un fallo o un proceso terminado pierde como mucho las
  posiciones desde el último guardado.
- Forza Horizon no envía el nombre del circuito, así que los archivos de vuelta de Forza tienen `"track": null`; Forza
  Motorsport (2023) envía solo un número, que se guarda como `lap.trackOrdinal`.

## Reconstrucción {#reconstruction}

- **La profundidad se estima, no se lee.** Es el techo de todo el enfoque, y el precio de no tocar nunca el proceso del juego.
- **El campo de visión se supone, no se mide.** Si es demasiado estrecho, el nivel se reconstruye más profundo de lo que es.
- **La escala global** sale de una altura de cámara supuesta (1,15 m en la ventana), o de la telemetría. Se mide en el primer
  fotograma clave; cuando ese no tiene suelo utilizable, se prueban los siguientes fotogramas clave (hasta 30), y una escala
  encontrada más tarde se aplica a todo el nivel al escribirlo. La línea «Size:» de la ventana indica qué ocurrió; si no se
  encuentra suelo en absoluto, el escaneo queda sin unidades. El tamaño del vóxel está en las unidades del primer fotograma
  en ese caso, así que su tamaño en metros difiere del ajuste. Las reconstrucciones sin conexión están en las unidades propias
  de la resolución.
- **El cierre de bucle está desactivado** y no es un grafo de poses cuando se activa en el código; la deriva solo se acota
  por la calidad del seguimiento de un fotograma al siguiente.
- **El ajuste de haces por ventanas existe pero no está conectado**; se colapsó con imágenes reales.
- **La superficie es una ocupación ponderada, no un TSDF**: las estructuras finas y el espacio libre salen peor de lo que
  daría un TSDF.
- **Sin atlas de texturas.** El color es por vértice (`COLOR_0`), mezclado a partir de las 4 mejores vistas entre 160
  fotogramas conservados. La prueba de oclusión es basta: se compara con los vértices propios de la malla en un búfer de
  profundidad de 2 píxeles, así que un obstáculo que la malla no contiene (un coche que pasa) no se detecta.
- **El agua nunca se etiqueta**; todo es suelo o estructura.
- **La resolución por propagación hacia delante no es en vivo**: necesita primero la grabación. No está construida la
  re-resolución adaptativa de secciones difíciles.
- **Las poses de telemetría** colocan la cámara en el coche (se desconoce el desplazamiento de una cámara de persecución).
  Las posiciones se toman tal como las envía Forza (Y hacia arriba, como en los archivos de vuelta); los sentidos de guiñada,
  cabeceo y alabeo se leyeron de vueltas grabadas (sentido de marcha, pendiente, qué lado de la suspensión se comprime), no de
  la cámara del juego en ejecución.
- La superposición no puede dibujarse sobre **pantalla completa exclusiva**; usa ventana sin bordes.
- Los atajos globales, la superposición que deja pasar los clics y la captura en vivo son **solo de Windows**.
- Al cerrar la ventana no se pregunta si guardar.

## Lo que se mide {#what-is-measured}

- `tests/test_accuracy.py`: una habitación sintética con una trayectoria conocida y una profundidad analítica: fotogramas
  ubicados, error de trayectoria, distancia recorrida, tamaño de la habitación, superficie en las paredes
  ([Reconstrucción del nivel](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: una carretera de ancho conocido recorrida descentrada se reconstruye con ese ancho.
- `tests/test_track_scale.py`: extracción de superficie a escala de circuito de carreras, memoria proporcional a lo escaneado,
  bloques que se unen en una sola superficie.
- `tests/test_glb.py` más las pruebas propias del visor: el contrato `.glb` desde ambos lados.
- Cómo se comporta la red de profundidad con jugabilidad real no es algo que pueda responder una escena sintética, y no lo
  mide el conjunto de pruebas.
