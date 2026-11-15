---
title: La ventana de escaneo
nav_order: 1
lang: "es"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# La ventana de escaneo {#the-scan-window}

```bash
python -m heat3d_capture.ui        # o haz doble clic en scan.bat
```

Código: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
La ventana es una vista ligera sobre `scan/session.py` y `scan/reconstruct.py`; no tiene lógica propia de
escaneo ni de geometría.

La ventana solo tiene textos en inglés. Aquí, las etiquetas, botones y mensajes aparecen tal como se ven en ella, entre comillas; el resto se explica en español.

## Al arrancar {#starting-up}

1. **Comprobación de actualizaciones**: ver [Actualizaciones](updates.md).
2. **Comprobación de dependencias**: se verifica cada paquete que necesita el escáner antes de importar nada; los que faltan
   se listan con para qué sirven y su tamaño de descarga, y solo se instalan tras «Descargar e instalar». Cancelar sale sin
   cambiar nada. Ver [Ejecución y dependencias](runtime.md#first-run-preflight).
3. **Ventana**: «3DHeat — Level scanner», 1420 x 900, estilo Fusion de Qt.
4. **Comprobación de hardware**: se elige el mejor backend de inferencia, se carga el modelo de profundidad y se mide su
   rendimiento con 6 fotogramas; el cuadro de veredicto arriba a la izquierda indica cómo será el escaneo (ver
   [Ejecución](runtime.md#what-to-expect-from-this-machine)).
5. **Los atajos globales** se registran al final.

### Cuando todavía no hay modelo de profundidad {#when-there-is-no-depth-model-yet}

Si `models/` no tiene ningún `depth-*.onnx`, el veredicto dice **«One more thing to set up.»**, el botón **Start scanning**
queda desactivado y aparece un botón **Set up the depth model**. Este:

- comprueba PyTorch, `transformers` y `onnxscript` (unos 945 MB en total), y pregunta antes de instalarlos;
- ejecuta `tools/export_onnx.py --size small` como un proceso aparte (así PyTorch nunca queda en la memoria del escáner),
  con un límite de 30 minutos. La ventana no responde mientras se ejecuta;
- si tiene éxito, vuelve a hacer la comprobación de hardware; si falla, muestra los últimos 600 caracteres de la salida del
  convertidor.

Cuando hay varios modelos, la elección es **por licencia, no por nombre de archivo**: `depth-small-*` (Apache-2.0, uso
comercial permitido) siempre que exista uno, luego Base, luego Large (ambos no comerciales). El cuadro de veredicto y la línea
gris bajo los botones indican el archivo en uso, su licencia y cualquier otro modelo presente que no se usa, por ejemplo
`Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used: depth-base-518.onnx`.
Para escanear con Base, saca el archivo Small de `models/`.

## Columna izquierda: ajustes {#left-column-settings}

| Grupo | Control | Por defecto | Rango / valores | Qué hace |
|---|---|---|---|---|
| (arriba) | Cuadro de veredicto | «Comprobando tu tarjeta gráfica…» | verde, ámbar o rojo según el nivel | Titular, `<device> via <API> — N views per second`, una nota y `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | De dónde llegan los fotogramas |
| | Which | `1` | número de monitor / título de ventana / ruta a un vídeo | `monitor:<n>`, `window:<title>`, o una ruta de archivo |
| | Choose file… | visible para vídeo | `*.mp4 *.mkv *.avi *.mov` | Rellena la ruta |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Resolución de captura y lo selectivo que es el muestreo de fotogramas clave (abajo); bajo él se muestra un resumen de una línea |
| | Game field of view | 90° | 30-140° | El campo de visión **horizontal** del juego. Si es demasiado estrecho, el nivel se reconstruye más profundo de lo que es; si es demasiado ancho, se aplana. Los juegos de carreras están más cerca de 65° |
| | Surface detail | 0,25 m | 0,05-2,0 m, paso 0,05 | Tamaño del vóxel de la superficie. Más pequeño es más fino y más pesado |
| Stop after | Time | sin límite | 0-120 min | Termina el escaneo tras este tiempo (0 = sin límite) |
| | Views kept | 3000 | 0-100.000 | Termina el escaneo tras este número de fotogramas clave, como protección de memoria (0 = sin límite) |
| What to ignore | Ignore HUD and anything on the camera | activado | | Aprende y enmascara el HUD, la mira, el arma, el capó y la cabina ([Captura](reconstruction-capture.md#what-is-not-the-world)). La línea bajo él indica lo que decide ahora el detector |
| While you play | Show feedback over the game | activado | | Abre la superposición («Show feedback over the game») que deja pasar los clics mientras se escanea. La indicación bajo ella: ejecuta el juego en **ventana sin bordes**; nada puede dibujarse sobre la pantalla completa exclusiva |
| Racing telemetry (Forza) | Listen for position data | desactivado | | Toma la trayectoria de la cámara de los Datos de salida de Forza en lugar de estimarla a partir de la imagen ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (puerto) | 5300 | 1-65535 | El puerto de Datos de salida |
| | (línea de estado) | | | `N packets — poses come from the game, not from the picture`, o `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Inicia o detiene; muestra el atajo cuando se registró |
| | **Set up the depth model** | oculto | | Ver arriba |
| | **Save level…** | desactivado | | Se activa tras un escaneo que produjo voxels de superficie; pide un nombre de archivo (por defecto `scan.glb`) |
| | (línea gris) | | | `Model: <file> (<licence>) · Available: <backends>`, más notas de configuración como instalar `onnxruntime-gpu` |

### Los preajustes {#the-presets}

| Preajuste | Lado largo de la captura | Cuantil de conservación | Umbral inicial | Resumen mostrado |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Rápido y basto. Bueno para comprobar una ruta antes de un escaneo real. |
| Balanced | 960 px | 0,65 | 0,010 | La elección habitual. Camina a un ritmo normal. |
| Detailed | 1280 px | 0,40 | 0,004 | Lento y minucioso. Camina con deliberación y gira con suavidad. |

El cuantil de conservación significa «conservar un fotograma cuando cambió más que este cuantil de los cambios de los últimos
240 fotogramas»: Draft conserva más o menos el 15% más activo, Detailed el 60% más activo. Ver
[Fotogramas clave](reconstruction-capture.md#keyframes).

### Ajustes fijos en la ventana {#settings-that-are-fixed-in-the-window}

La ventana siempre reconstruye mientras escanea, usa una altura de cámara de **1,15 m** para la escala del plano del suelo (la
altura al andar, 1,70 m, no se puede elegir), y deja que la escalera de backends elija la GPU. Estos son los campos de
`ScanSettings` (`camera_height`, `prefer_backend`) que solo puede cambiar un script.

## Columna derecha: lo que está haciendo el escaneo {#right-column-what-the-scan-is-doing}

| Elemento | Muestra |
|---|---|
| **Lo que ve la cámara** | el último fotograma clave |
| **Forma que se está leyendo** | su profundidad predicha, coloreada con el mapa de color Turbo, normalizada entre el percentil 2 y el 98 de ese fotograma (así un píxel de cielo no aplana el rango) |
| **Cobertura: por dónde has estado, y con qué calidad** | una vista en planta (ver abajo) |
| **Worth another look** | los puntos débiles, numerados para coincidir con los anillos del mapa, cada uno con una instrucción; el peor (el más grande) primero, como máximo 8; después los puntos que marcaste tú (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Barra de velocidad al andar | `walk speed — N% of the way to the next view`: el cambio de imagen del último fotograma dividido entre el **umbral en uso**: el valor inicial del preajuste para los primeros 30 fotogramas, el ajustado después ([Fotogramas clave](reconstruction-capture.md#keyframes)) |
| Línea de estado de salud | salud del seguimiento, o una advertencia de captura (abajo) |
| Línea de tamaño | `Size: ...`, cómo se fijó la escala del nivel o por qué no se fijó ([Escala](reconstruction-pose.md#scale)) |
| Línea de estadísticas | `views  frames  dropped  depth-per-second  seconds`, y mientras reconstruye `placed  cells  % well seen  metres`, más `recovered` y `loops closed` cuando alguno no es cero |
| Línea de atajos | las teclas registradas, o por qué no pudieron registrarse |
| Línea de consejos (ámbar) | consejos en vivo (abajo), el mensaje final del escaneo y las marcas |

### El mapa de cobertura {#the-coverage-map}

Se vuelve a dibujar cada 900 ms en un hilo de fondo (nunca en el hilo de la interfaz), en 200 x 200 celdas escaladas a 420 px:

- cada columna de la rejilla de cobertura toma la **mejor** calidad de observación que tenga (así un suelo bien visto no se
  pinta de ámbar por un techo mal visto encima);
- la escala va de rojo (malo) a ámbar (fino) a amarillo (aceptable) a verde (bueno);
- las celdas nunca observadas son un gris oscuro distinto, para que una esquina sin explorar no parezca mal escaneada;
- el camino recorrido se dibuja como una línea clara y fina; la posición actual, como un punto blanco;
- los puntos débiles son anillos blancos con su número;
- los puntos que marcaste son cuadrados ámbar con la etiqueta `M1`, `M2`, …

Cómo se calculan la calidad y los puntos débiles: [Fusión, cobertura y color](reconstruction-fusion-and-texture.md#coverage).

### La línea de salud {#the-health-line}

| Salud del seguimiento (fotogramas ubicados / fotogramas) | Texto | Color |
|---|---|---|
| todavía no hay fotogramas | Esperando el primer fotograma. | gris |
| 90% o más | Seguimiento bien — N de M fotogramas ubicados. | verde |
| 60% o más | El seguimiento es irregular — N de M fotogramas no se pudieron ubicar. Gira más despacio. | ámbar |
| menos de 60% | Se pierde el seguimiento — solo N de M fotogramas ubicados. Muévete despacio y evita muros en blanco y el cielo. | rojo |

Una advertencia de captura de la rejilla de cobertura sustituye a esta línea (roja cuando se juzga que el escaneo no es
reconstruible, ámbar en los demás casos): casi nada de paralaje, todo visto desde más de 25 m, o paralaje escaso. Ver
[Cobertura](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### La línea de consejos {#the-hint-line}

| Condición | Consejo |
|---|---|
| más de la mitad de los fotogramas descartados, tras 6 s | Te estás retrasando — N fotogramas descartados ... Prueba la calidad Borrador, o un detalle de superficie más grueso. |
| menos de 0,3 vistas conservadas por segundo, tras 8 s | Se conserva muy poco — quizá estás quieto, o mirando algo sin rasgos. Muévete de lado en lugar de girar en el sitio. |
| más de 8 vistas conservadas por segundo, tras 8 s | Conservando mucho. Ve un poco más despacio para una geometría más limpia. |
| el escaneo terminó | el mensaje de la sesión: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` o `failed: <error>` |

## Atajos de teclado {#hotkeys}

Se registran en Windows (`RegisterHotKey`), así que funcionan mientras el juego tiene el foco. Cambiar con Alt+Tab fuera de un
juego a pantalla completa es justo lo que arruina una captura.

| Teclas | Acción |
|---|---|
| **Ctrl+Alt+F9** | Iniciar / detener el escaneo |
| **Ctrl+Alt+F10** | Marcar este punto para volver a él (mientras escanea) |
| **Ctrl+Alt+F11** | Mostrar / ocultar la superposición (alterna la casilla «Show feedback over the game») |

- Se registran una vez, al abrir la ventana, y se liberan al cerrarla; mientras están registradas, estas combinaciones de
  teclas se quitan a todos los demás programas, incluido el juego. Las combinaciones de teclas F con dos modificadores se
  eligieron porque los juegos rara vez las asignan.
- La repetición automática se suprime (`MOD_NOREPEAT`), así que mantener una tecla pulsada no alterna el escaneo docenas de veces.
- Si una tecla ya la tiene otro programa, se informa (`... unavailable: another program already has this key`) y las demás siguen
  funcionando. Un botón solo muestra una tecla que de verdad se registró.
- Las teclas están fijas en el código (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); el analizador acepta F1-F12 con `ctrl`,
  `alt` y `shift`. Fuera de Windows no hay atajos globales, y la ventana lo indica.
- **Marcar** registra la posición actual de la cámara (la del último fotograma ubicado) y muestra «Marked MN. Marked spots are on
  the map and saved with the level.». Antes de que se haya ubicado ningún fotograma, indica que no hay dónde marcar. Los puntos
  marcados se dibujan en el mapa de la ventana y en el de la superposición como cuadrados ámbar con la etiqueta `M1`, `M2`, …,
  aparecen en la lista bajo los puntos débiles, se cuentan en la línea de estadísticas de la superposición, y se guardan con el
  nivel (abajo).

## La superposición {#the-overlay}

Un pequeño panel fijado sobre el juego, para que la información esté donde ya están los ojos.

- Sin marco, siempre encima, una ventana de herramienta (no aparece en la barra de tareas ni en Alt+Tab), transparente a la entrada
  en Qt y que deja pasar los clics en Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), así que un clic dirigido al juego nunca se
  pierde. Se muestra sin tomar el foco.
- En la esquina superior derecha de la pantalla principal, a 18 px de los bordes; 214 x 358 px.
- Se abre cuando empieza un escaneo (si «Show feedback over the game» está activado), y se cierra cuando se detiene.
- **Necesita el modo ventana sin bordes**: nada puede dibujarse sobre la pantalla completa exclusiva; ni esto, ni la superposición
  de Steam, ni la de Discord.

De arriba abajo muestra:

| Elemento | Contenido |
|---|---|
| Mapa de cobertura | 190 px, el mismo mapa que la ventana pero en 120 x 120, con el camino, los anillos de puntos débiles y los puntos marcados |
| Salud | el mismo texto y color que la línea de salud de la ventana |
| Estadísticas | `N placed · M to revisit · X m`, con `· K marked` cuando hay alguno |
| barra de **movimiento** | la misma que la barra de velocidad al andar de la ventana: el cambio de imagen del último fotograma sobre el umbral en uso, llena cuando el siguiente fotograma se conservará |
| barra de **nitidez** | nitidez relativa a la mediana de esta propia captura: verde desde 0,75, ámbar desde 0,45, rojo por debajo |
| Consejo | una instrucción, en verde / ámbar / rojo (en negrita cuando no es «ok») - ver [calidad de fotograma](reconstruction-capture.md#frame-quality-and-advice) |
| Atajos | las teclas registradas |

Si alguna vez falla la actualización de la superposición, pasa a un panel rojo **«Feedback stopped»** que dice que todo lo mostrado
antes está desactualizado, que el escaneo sigue en marcha y la ventana principal sigue siendo correcta, junto con el error y un
contador. Un panel que se quedó congelado en verde seguiría leyéndose como confirmación.

## Guardar {#saving}

**Guardar nivel…** escribe la reconstrucción como un `.glb` (ver [La salida .glb](glb-output.md)). Si el volumen no produce
superficie, «Nothing to save» explica que el seguimiento probablemente se perdió durante la mayor parte del escaneo. Si sale bien:
«Written to <path> ... Load it in 3DHeat through the Level panel.», indicando también el archivo de marcas cuando hay puntos
marcados.

Los puntos marcados se escriben junto al nivel como **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` está en las coordenadas propias del nivel (con la escala del GLB aplicada, así que una marca queda sobre la malla que se
hizo), `metres` en metros; `number` coincide con `M1`, `M2`, … de la ventana. Cuando la escala se encontró en un fotograma clave
posterior ([Escala](reconstruction-pose.md#scale)), ambos incluyen ese factor.

Detener un escaneo conserva lo reunido; un nuevo **Iniciar** descarta el escaneo anterior.
**Al cerrar la ventana no se pregunta si guardar**: detiene el escaneo, libera los atajos y cierra la superposición.
