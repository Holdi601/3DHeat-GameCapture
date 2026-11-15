---
title: "Deslizamiento, deriva y canales derivados"
nav_order: 8
lang: es
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Deslizamiento, deriva y canales derivados {#slip-drift-and-derived-channels}

El análisis de control del coche de la pestaña Análisis de carrera del visor necesita las mismas
pocas magnitudes de cada juego: cuánto desliza cada neumático, cuánto apunta el coche lejos de
hacia donde va (el ángulo de deriva), si está en el aire, si está sobre suelo suelto. Los juegos
las envían de formas muy distintas, o no las envían. Los grabadores de aquí escriben lo que envía
cada juego, con nombres canónicos, más una nota `meta.slip` que indica qué significan los números
de deslizamiento; después el visor deriva lo que falta, una vez, al cargar una vuelta. **El valor
propio de un juego siempre gana a uno derivado.**

## Lo que escriben los grabadores {#what-the-recorders-write}

| Juego | Canales de deslizamiento | `meta.slip` | Entradas del ángulo de deriva |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` por rueda, tal como se envían | `peak` (lo escribe el grabador; el lector `.tele.gz` del visor pone lo mismo) | `latVel`, `longVel` a partir de la velocidad en el marco del coche |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, más `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` a partir de la velocidad en el marco del coche |
| EA SPORTS WRC, juegos DiRT | ninguno; `wheelSurfaceSpeed` por rueda en su lugar | `null` | `latVel`, `longVel` = velocidad del mundo proyectada sobre los ejes del coche |
| Richard Burns Rally | ninguno; tampoco hay velocidades de rueda | ninguno | `latVel`, `longVel` = el balanceo y el avance propios del coche |
| BeamNG.drive | ninguno; `wheelSurfaceSpeed` y `wheelSpeed` por rueda | ninguno | `latVel`, `longVel` = velocidad del mundo proyectada sobre los ejes del coche |
| Trackmania | `slipIndex` por rueda (una medida de deslizamiento de 0..1) | `index` | `latVel` (velocidad lateral), `longVel` (velocidad frontal) |
| iRacing | ninguno (no se registra) | ninguno | `yaw` y la trayectoria, `yawRate` |

Los valores de `meta.slip` están definidos en [El archivo heat3d-lap](lap-format.md): `peak`
(normalizado, de modo que por encima de 1 el neumático pierde agarre), `scaled` (un deslizamiento
físico dividido por un pico típico de asfalto), `physical` (una fracción y radianes), `index` (una
medida de deslizamiento de 0..1).

### Por qué el deslizamiento de Kunos se escala {#why-kunos-slip-is-scaled}

El deslizamiento de Forza está normalizado para que 1 sea el borde del agarre; cómo lo normaliza no
está documentado. Kunos envía la relación de deslizamiento física (una fracción) y el ángulo de
deslizamiento (radianes). Dividirlos por un pico típico de asfalto - 0,12 para la relación y 0,14 rad
(unos 8 grados) para el ángulo - hace que "por encima de 1 significa deslizando" sea aproximadamente
cierto para ambas familias, lo que mantiene una sola lectura para las pantallas del visor. Es una
aproximación: los picos reales varían según el neumático y la superficie, por eso se guardan los
valores en bruto junto a los escalados, y por eso el visor mide, a partir de las vueltas, dónde se
pierde realmente el agarre de cada coche.

## Lo que deriva el visor (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Estas operaciones se ejecutan en el visor (`src/race/derive.ts` en el visor de 3DHeat), no en este
repositorio.

### Ángulo de deriva, `bodySlip` {#drift-angle-bodyslip}

- **A partir de la velocidad en el marco del coche** cuando hay `latVel` y `longVel`:
  `atan2(latVel, |longVel|)`, y 0 por debajo de 3 m/s (un coche parado de lado no está derivando).
  Su signo sigue a la velocidad lateral del juego, cuyo sentido está documentado en ambos sentidos
  para algunos juegos - fíjate en el tamaño.
- **Si no, a partir del rumbo frente a la trayectoria**: la dirección de marcha se toma de las
  posiciones a unos 2 m a cada lado de cada muestra (`atan2(dx, dz)`); la `yaw` del juego se ajusta
  a ella con un signo y un desplazamiento (cada juego tiene su propio cero y sentido de giro),
  usando muestras por encima de 10 m/s, y solo se confía si luego concuerda de cerca (dispersión
  circular como máximo 0,05, al menos 20 muestras). El ángulo de deriva es la diferencia, 0 por
  debajo de 3 m/s.

### Relación de deslizamiento a partir de las ruedas {#slip-ratio-from-the-wheels}

Cuando una vuelta no tiene `slipRatio.*` pero sí velocidades de rueda, la relación de deslizamiento
es `(rueda - coche) / coche` por rueda, a partir de:

- `wheelSurfaceSpeed.*` (la velocidad del punto de contacto, m/s) directamente, cuando se envía (EA
  WRC, DiRT, BeamNG);
- si no, `wheelSpeed.*` (rotación, rad/s) por un **radio de rodadura medido en la vuelta**: la
  mediana de `velocidad / |omega|` en las muestras donde el coche rueda sin acelerar en línea recta
  (por encima de 10 m/s, sin estar en el aire, acelerador por debajo de 0,3, freno por debajo de 0,05,
  aceleración longitudinal por debajo de 3 m/s²); con menos de 20 de esas muestras, todas las muestras
  por encima de 10 m/s. Un radio fuera de 0,1-1 m se rechaza.

Solo cuando se pueden derivar las cuatro ruedas; entonces el `meta.slip` de la vuelta pasa a
`physical`. Por debajo de 3 m/s el deslizamiento es 0.

### En el aire {#airborne}

`airborne` vale 1 donde todas las ruedas están fuera del suelo, juzgado por el primero de estos que
la vuelta tenga para las cuatro ruedas:

1. `groundContact.*` (BeamNG): ninguna rueda por encima de 0,5;
2. `wheelLoad.*` (juegos AC, RBR, BeamNG): ninguna rueda por encima del 5 % de su propia carga mediana;
3. `suspension.*` (0..1 del recorrido): ninguna rueda por encima de 0,02, es decir, todas totalmente
   extendidas.

Una única muestra aislada en el aire se borra. Trackmania escribe `airborne` por sí mismo.

### Suelo suelto {#loose-ground}

Cuando una vuelta tiene `surfaceRumble.*` (Forza), `loose` vale 1 donde al menos dos ruedas informan
de vibración durante al menos un tercio de segundo, con los huecos de menos de un segundo unidos (un
tramo liso en una pista de grava sigue siendo la pista de grava). Trackmania escribe `loose` por sí
mismo a partir de los materiales del suelo de las ruedas.

### Velocidad de guiñada {#yaw-rate}

Cuando una vuelta tiene `yaw` pero no `yawRate`, es el cambio de guiñada entre las muestras vecinas.

## Lo que derivan los propios grabadores {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): todo grabador salvo Forza (que la envía) la escribe a partir de
  `suspensionM.*` como la posición dentro del rango que usó esta vuelta (mínimo a máximo). Sirve para
  las barras de suspensión del coche y para detectar una rueda colgando en el aire; no es una fracción
  de recorrido absoluta.
- **`steer`** para los juegos Kunos, escalado por vuelta (ver [Juegos de Assetto Corsa](telemetry-assetto-corsa.md)).
- **Aceleraciones** para BeamNG, a partir del cambio de la velocidad del mundo
  ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** y el eje vertical para Richard Burns Rally, a partir de las posiciones
  ([Juegos de rally](telemetry-rally.md)).

## Lateralidad {#handedness}

Cuando el mundo de un juego es zurdo - el de Forza lo es - un recorrido sale reflejado en un visor
diestro; la dirección y la suspensión propias de las vueltas lo delatan. Los grabadores no cambian la
lateralidad: un mundo Z hacia arriba (BeamNG) se gira a Y hacia arriba con una rotación, que conserva
la lateralidad, y todo lo demás se escribe tal como se envía.
