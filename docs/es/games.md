---
title: "Juegos: grabación y recorridos"
nav_order: 4
lang: es
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Juegos: grabación y recorridos {#games-recording-and-courses}

Cómo se graba cada juego compatible, qué envía y cuáles de sus recorridos
pueden exportarse desde los propios archivos del juego.

Las reglas son las mismas para todos los juegos: un recorrido sale de archivos
que el usuario posee, o se reconstruye a partir de su propia partida. Los
archivos cifrados solo se abren con una clave que el usuario ya tiene; aquí no
se incluye ninguna clave, no se recupera ninguna y nada se inyecta en el
proceso de un juego. La telemetría procede solo de las interfaces que los
juegos publican para ello (salidas UDP, memoria compartida, sus propias
interfaces de mods y complementos). Lo que el usuario apunte con las
herramientas sigue sujeto a la licencia de ese juego.

## Telemetría {#telemetry}

Todos los juegos acaban en archivos `heat3d-lap` ([`lap-format.md`](lap-format.md)),
con nombres de canal canónicos y un bloque `meta` que indica qué significan sus
números: cómo se escala su deslizamiento, si es circuito, rally o arcade, y la
superficie cuando se conoce. Así, un lector los trata a todos por igual. Todos
los comandos son `python -m heat3d_capture ...` dentro de este repositorio.

| Juego | Cómo grabar | Posición | Neumáticos y deslizamiento | Ángulo de deriva | Estado |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out por UDP: `heat3d_capture telemetry` (reenvía a FH Companion) - o el `.tele.gz` de FH Companion junto a cada vuelta, cargado con el archivo de vuelta | XYZ del mundo | relación de deslizamiento, ángulo de deslizamiento, deslizamiento combinado por rueda, normalizados; rugosidad de la superficie | velocidad en el marco del coche | grabador probado; lector de `.tele.gz` comprobado con vueltas reales |
| Forza Motorsport (incl. 2023) | lo mismo; se distingue por la longitud del paquete | XYZ del mundo | lo mismo | lo mismo | grabador probado |
| Assetto Corsa, ACC, AC EVO | memoria compartida: `telemetry --game ac / acc / acevo` | media de los puntos de contacto de los neumáticos | relación y ángulo de deslizamiento (físicos, escalados por un pico de asfalto); ABS y control de tracción actuando (ACC, EVO) | velocidad en el marco del coche | grabador probado con páginas sintéticas |
| Assetto Corsa Rally | `telemetry --game acrally` | lo mismo | lo mismo; cargas de las ruedas; temperaturas convertidas de kelvin | velocidad en el marco del coche | grabador probado con páginas sintéticas |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documentos>/My Games/WRC/telemetry/config.json"` activa el paquete `wrc` predeterminado (el archivo se respalda antes) | XYZ del mundo | velocidad del punto de contacto por rueda; deslizamiento derivado | a partir de los ejes del coche y su velocidad | grabador probado con paquetes construidos según el diseño documentado |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: poner `<udp enabled="true" extradata="3" port="20777" delay="1" />` en `hardware_settings_config.xml`, y luego `telemetry --game dirtrally2` (o `dirtrally`, `dirt4`) | XYZ del mundo | velocidad del punto de contacto por rueda; deslizamiento derivado. No hay canal de freno de mano | a partir de los ejes del coche y su velocidad | lo mismo |
| Richard Burns Rally (RSF/NGP) | telemetría UDP de NGP (`udpTelemetry=1`): `telemetry --game rbr` | mundo, eje vertical hallado en el tramo | deflexión y fuerza del muelle por rueda; sin velocidades de rueda | las velocidades propias del coche | lo mismo; los ejes y las unidades de velocidad no están documentados y se deducen de los datos |
| BeamNG.drive | el mod de protocolo `heat3d`: `telemetry --game beamng --install`, y luego Opciones > Otros > Protocolos > "others" | mundo, girado a Y hacia arriba | velocidad superficial de la rueda, rotación, carga y contacto con el suelo; deslizamiento derivado | a partir de los ejes del coche y su velocidad | grabador probado con paquetes construidos según la estructura del mod; el mod no se ha probado en el juego |
| Trackmania (2020) | el complemento de Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, cargado en el modo desarrollador de Openplanet; un CSV por carrera en su carpeta de almacenamiento | XYZ del mundo | coeficiente de deslizamiento de Trackmania por rueda; suelo suelto a partir de los materiales de las ruedas; en el aire | velocidad frontal y lateral | lector probado; el complemento no se ha probado en el juego |
| iRacing | sus propios archivos `.ibt`; no hace falta grabador | latitud/longitud/altitud, proyectadas sobre un plano tangente | sin deslizamiento (no se registra); velocidad de guiñada y aceleración lateral | a partir de la velocidad de guiñada frente a la trayectoria | lector probado con un archivo sintético |

Lo que ningún juego de rally envía, el deslizamiento de los neumáticos, lo
calcula un lector: a partir de la velocidad del punto de contacto o de la
superficie de cada rueda frente a la velocidad del coche donde el juego la
envía (`(rueda - coche) / coche`), o a partir de su rotación y de un radio de
rodadura medido en la propia vuelta cuando solo envía la rotación. El ángulo de
deriva sale de la velocidad propia del coche (Forza, los juegos AC, Trackmania,
RBR), de la velocidad del mundo proyectada sobre los ejes del coche (EA WRC,
DiRT, BeamNG), o del rumbo frente a la trayectoria. Que el coche esté en el aire
se deduce del contacto, de las cargas o de la suspensión de sus ruedas.

Cuando el mundo de un juego es zurdo, como el de Forza, el recorrido sale
reflejado en un visor diestro; la dirección y la suspensión propias de las
vueltas lo delatan. Los juegos cuya lateralidad no está documentada (RBR,
BeamNG, Trackmania) se tratan del mismo modo: se mide, no se supone.

Más allá de los canales de conducción, los grabadores guardan lo que cada juego
añade: en los juegos AC, la actuación del ABS y del control de tracción, el
reparto de frenada, el DRS, el limitador de pits, el turbo y la vida de las
pastillas y los discos de freno; en iRacing, los ajustes de ayudas, el reparto
de frenada, la temperatura de combustible, aceite y agua, y cada otro canal que
registra con su propio nombre.

### Fuentes y lo que aún no está confirmado {#sources-and-what-is-not-yet-confirmed}

- **Forza:** la documentación oficial de Data Out (Forza Motorsport; Forza
  Horizon 6) para los campos, sus unidades y el marco del coche (x a la derecha,
  y arriba, z hacia delante: zurdo). Cómo normaliza Forza su deslizamiento no
  está documentado: hay que medir dónde pierde agarre cada coche, en lugar de
  suponer que 1 es el límite.
- **Kunos:** el SDK de AC1, la documentación de la memoria compartida de ACC
  v1.8.12, `albertowd/live-telemetry-evo` (EVO, medido; AC Rally usa el diseño de
  ACC, "confirmado mediante una sonda byte a byte"),
  `LuizZak/AssettoCorsaRallyTelemetryReader`. El lado hacia el que apunta el eje
  x del coche está documentado en ambos sentidos: usa el tamaño del ángulo de
  deriva, no su signo.
- **EA SPORTS WRC:** la Guía de telemetría UDP de EA v1.3 y la lista de canales
  que el juego escribe en `readme/channels.json`; los desplazamientos del paquete
  `wrc` predeterminado según los decodificó nobonobo/obs-codemasters-telemetry.
  El puerto predeterminado de fábrica no está documentado; el grabador activa el
  paquete en el 20777.
- **DiRT:** el documento UDP de DiRT 4 de Codemasters, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. El sentido del vector lateral y la
  unidad de la posición de la suspensión están documentados en ambos sentidos;
  ninguno decide una conclusión.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` de NGP (a través de
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Los ejes de posición, las
  unidades de actitud y la unidad de velocidad no están documentados: el
  grabador toma el eje vertical del tramo y la velocidad a partir de las posiciones.
- **BeamNG:** documentation.beamng.com (protocolos; refNodes: vehículo +X a la
  izquierda, -Y hacia delante, Z hacia arriba), y los propios archivos del juego
  `lua/vehicle/protocols.lua` y `wheels.lua`. OutSim es un esbozo en las versiones
  actuales; OutGauge no tiene posición y MotionSim no tiene ruedas, de ahí el mod.
- **Trackmania:** el `CSceneVehicleVisState` de Openplanet y el complemento
  VehicleState, el tiempo de carrera de `CSmScriptPlayer`. Los complementos de
  Openplanet no pueden enviar UDP, así que el complemento escribe archivos. Los
  complementos sin firmar solo se cargan en el modo desarrollador, lo que limita
  el juego en línea; el complemento puede firmarse en openplanet.dev.

Ninguno de los grabadores se ha ejecutado todavía contra los juegos reales; la
primera sesión real de cada uno es la prueba que cuenta, y `tests/test_kunos.py`,
`test_rally.py` y `test_beamng.py` fijan los diseños para los que se
construyeron. Cada grabador comprueba sus paquetes según llegan (la velocidad
frente a la rapidez, el tamaño de la estructura) y avisa cuando un diseño no
coincide.

## Recorridos: qué se exporta, por juego {#courses-what-is-exported-per-game}

Un recorrido añade los bordillos, muros y zonas de escape que explican una
trazada. Los recorridos los exporta
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_capture course <lap>`), a partir de los archivos propios del
juego, donde eso se ha construido y comprobado en una copia instalada. Los
detalles están en la [documentación de GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Juego | Recorrido a partir de una vuelta |
|---|---|
| Forza Horizon | sí |
| BeamNG.drive | sí |
| Assetto Corsa Rally | sí |
| Assetto Corsa EVO | no: su contenido no se puede leer como archivos |
| iRacing | no: los modelos de circuito se distribuyen en un formato protegido |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | todavía no: cada uno necesita una copia instalada para construirlo y comprobarlo |

Mientras tanto, la ruta por jugabilidad de abajo funciona para todos ellos.

## La ruta que funciona para cualquier juego {#the-route-that-works-for-every-game}

GameCapture reconstruye un nivel a partir del vídeo de la partida. Su parte
difícil es la trayectoria de la cámara, y en Forza es exacta porque la
telemetría da la pose del coche en cada fotograma. Ahora todos los juegos de
arriba tienen lo mismo: posición y actitud, en directo, desde una interfaz
documentada. Si se introducen en `pose/telemetry_pose.py` en lugar de los de
Forza, se consigue que la ruta por jugabilidad sea exacta para todos ellos: el
resto de la canalización (profundidad, fusión, texturizado) no depende del juego
que dibujó los fotogramas.
