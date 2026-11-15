---
title: "Grabadores de telemetría"
nav_order: 3
lang: es
source: telemetry.md
source_hash: "58d0440321a3"
nav_exclude: true
search_exclude: true
---
# Grabadores de telemetría {#telemetry-recorders}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o FOLDER] [--port PORT]
                                   [--forward HOST:PORT] [--install]
                                   [--configure CONFIG_JSON] [--surface SURFACE]
```

`telemetry` graba cada canal que envía un juego, divide el flujo en vueltas o tramos, y escribe un archivo
JSON [`heat3d-lap`](lap-format.md) por vuelta en una carpeta. La pestaña Análisis de carrera del visor lee esos archivos.
La grabación sigue hasta que pulsas **Ctrl+C**; la vuelta o tramo que esté abierto en ese momento se escribe
si es lo bastante largo para conservarlo (ver [Cómo se dividen las vueltas y los tramos](lap-splitting.md)).

Código: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py)
y los módulos de [`heat3d_capture/telemetry/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/telemetry).

## Opciones {#options}

| Opción | Predeterminado | Significado |
|---|---|---|
| `--game` | `forza` | Uno de `forza`, `ac`, `acc`, `acevo`, `acrally`, `wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`, `beamng`, `trackmania`. |
| `-o`, `--out` | `laps` | Carpeta donde se escriben los archivos de vuelta. Se crea si falta. Lo ignora `trackmania`, cuyo complemento escribe los archivos por sí mismo. |
| `--port` | `5300` | Puerto UDP en el que escuchar. **Para todos los juegos salvo Forza, el valor 5300 significa "el puerto predeterminado del juego"**: 20777 para `wrc` y los juegos DiRT, 6776 para `rbr`, 4460 para `beamng`. Indica otro número para cambiarlo. No se usa con los juegos de Assetto Corsa (memoria compartida) ni con Trackmania (archivos). |
| `--forward` | ninguno | Solo Forza: `host:port` al que reenviar cada paquete recibido, sin cambios. `127.0.0.1:5301` para FH Companion. Un simple `:5301` significa `127.0.0.1:5301`. |
| `--install` | desactivado | `beamng`: copia primero el mod de protocolo en las mods desempaquetadas de BeamNG. `trackmania`: copia el complemento de Openplanet en su carpeta de complementos. Lo ignoran los demás juegos. |
| `--configure` | ninguno | Solo `wrc`: ruta al `config.json` de telemetría de EA SPORTS WRC; activa el paquete `wrc` predeterminado antes de grabar (se respalda antes). |
| `--surface` | ninguno | Juegos de rally (`wrc`, `dirtrally2`, `dirtrally`, `dirt4`, `rbr`): `tarmac`, `loose`, `snow`, `ice` o `mixed`, que se escribe en `meta.surface` del archivo de vuelta. Sin esta opción no se escribe ninguna superficie. |

## Los juegos de un vistazo {#the-games-at-a-glance}

| `--game` | Juego | Origen | Puerto predeterminado | División | `game` en el archivo | Página |
|---|---|---|---|---|---|---|
| `forza` | Forza Horizon 4/5/6, Forza Motorsport (incl. 2023) | UDP de Data Out | 5300 | el contador de vueltas del juego (`LapSplitter`) | `forza-horizon`, `forza-motorsport`, o `forza` | [Forza](telemetry-forza.md) |
| `ac` | Assetto Corsa | memoria compartida `acpmf_*` | - | contador de vueltas (`CounterSplitter`) | `assetto-corsa` | [Juegos de Assetto Corsa](telemetry-assetto-corsa.md) |
| `acc` | Assetto Corsa Competizione | memoria compartida `acpmf_*` | - | contador de vueltas (`CounterSplitter`) | `assetto-corsa-competizione` | [Juegos de Assetto Corsa](telemetry-assetto-corsa.md) |
| `acevo` | Assetto Corsa EVO | memoria compartida `acevo_pmf_*` | - | línea de salida (`LineSplitter`) | `assetto-corsa-evo` | [Juegos de Assetto Corsa](telemetry-assetto-corsa.md) |
| `acrally` | Assetto Corsa Rally | memoria compartida `acpmf_*` | - | línea de salida / parada (`LineSplitter`) | `assetto-corsa-rally` | [Juegos de Assetto Corsa](telemetry-assetto-corsa.md) |
| `wrc` | EA SPORTS WRC | UDP, estructura `wrc` | 20777 | reloj de tramo (`StageSplitter`) | `ea-sports-wrc` | [Juegos de rally](telemetry-rally.md) |
| `dirtrally2` | DiRT Rally 2.0 | UDP, extradata 3 | 20777 | reloj de tramo (`StageSplitter`) | `dirt-rally-2` | [Juegos de rally](telemetry-rally.md) |
| `dirtrally` | DiRT Rally | UDP, extradata 3 | 20777 | reloj de tramo (`StageSplitter`) | `dirt-rally` | [Juegos de rally](telemetry-rally.md) |
| `dirt4` | DiRT 4 | UDP, extradata 3 | 20777 | reloj de tramo (`StageSplitter`) | `dirt-4` | [Juegos de rally](telemetry-rally.md) |
| `rbr` | Richard Burns Rally (RSF / NGP) | UDP de NGP | 6776 | reloj de tramo (`StageSplitter`) | `richard-burns-rally` | [Juegos de rally](telemetry-rally.md) |
| `beamng` | BeamNG.drive | mod de protocolo `heat3d`, UDP | 4460 | línea de salida (`LineSplitter`) | `beamng` | [BeamNG.drive](telemetry-beamng.md) |
| `trackmania` | Trackmania (2020) | complemento de Openplanet, archivos CSV | - | por carrera, en el complemento | `trackmania` | [Trackmania](telemetry-trackmania.md) |
| - | iRacing | sus propios archivos `.ibt`, leídos por el visor | - | el contador de vueltas del simulador | `iracing` | [iRacing](telemetry-iracing.md) |

## Estado {#status}

El grabador de Forza es el más probado. Los grabadores de Kunos, rally, BeamNG y Trackmania están
construidos según los diseños publicados y probados con paquetes y páginas sintéticos construidos a partir
de esos diseños (`tests/test_kunos.py`, `tests/test_rally.py`, `tests/test_beamng.py`); **ninguno se ha
ejecutado todavía contra el juego real**. Los grabadores que pueden comprobar lo que reciben lo hacen según
llegan los paquetes, e imprimen una vez una `note:` cuando algo no coincide (EA WRC y DiRT comparan la
velocidad del mundo con la rapidez; EA WRC además informa de un paquete más corto que la estructura
predeterminada de 237 bytes). [Juegos](games.md) lista las fuentes y lo que no está confirmado por juego.

## Mientras se ejecuta {#while-it-runs}

- **Forza** imprime una línea de estado cada segundo: paquetes recibidos, y el número de la vuelta abierta,
  el número de muestras y los metros, o `waiting for a race`. Cada vuelta terminada imprime `wrote <file>`.
- **Los juegos de Assetto Corsa** imprimen el nombre de cada archivo de vuelta al escribirlo.
- **Los juegos de rally** imprimen `listening for <game> on port <port>`, y luego `stage written: <file>`;
  con Ctrl+C, un tramo abierto lo bastante largo para conservarlo se escribe como `partial stage written: <file>`.
- **BeamNG** imprime `lap written: <file>`, y con Ctrl+C `run written: <file>`.
- **Trackmania** no imprime nada por carrera: el complemento escribe sus archivos CSV por sí mismo.
- Al final, cada grabador imprime cuántos archivos escribió.

Una grabación de Forza, aquí alimentada con paquetes sintéticos de Data Out de un coche que da dos vueltas a
un círculo de 150 m (los archivos de vuelta, el archivo auxiliar en bruto y el resumen de autocomprobación que deja):

![grabación de telemetría de dos vueltas con una señal sintética de Forza](../assets/img/telemetry-run.svg)

## Nombres de archivo {#file-names}

| Grabador | Patrón |
|---|---|
| Forza | `<YYYY-MM-DD_HH-MM-SS>_car<ordinal>_<lap|run><number>_<seconds>s.lap.json` |
| Juegos de Assetto Corsa | `<YYYY-MM-DD_HH-MM-SS>_<ac|acc|acevo|acrally>_<lap|run><number>_<seconds>s.lap.json` |
| Juegos de rally, BeamNG | `<game>_<YYYY-MM-DD_HH-MM-SS>_<stage|lap><number>_<seconds>s[_partial].json`, donde `<game>` es el nombre largo (`ea-sports-wrc`, `beamng`, ...), `stage` para rally y `lap` para BeamNG |
| Complemento de Trackmania | `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv` |

`lap` frente a `run` (Forza, Assetto Corsa) y el sufijo `_partial` (rally, BeamNG) indican si la vuelta o el
tramo se terminó. La marca de tiempo es cuando se escribió el archivo, no cuando empezó la vuelta.

Junto a los archivos de vuelta, cada grabador escribe `<YYYY-MM-DD_HH-MM-SS>_<game>.raw.parquet` - cada paquete
o página que llegó, completo, también en los menús y entre vueltas - y
`<YYYY-MM-DD_HH-MM-SS>_<game>.summary.json`, la autocomprobación: por tipo de paquete, cuántos llegaron, cuántos
entraron en archivos de vuelta, y `lost`, que es 0. El visor omite ambos al cargar una carpeta. Ver
[Completeness](https://github.com/Holdi601/3DHeat-GameCapture#completeness) en el README.

## Páginas hijas de esta {#children-of-this-page}

- [Forza](telemetry-forza.md)
- [Juegos de Assetto Corsa](telemetry-assetto-corsa.md)
- [Juegos de rally](telemetry-rally.md)
- [BeamNG.drive](telemetry-beamng.md)
- [Trackmania](telemetry-trackmania.md)
- [iRacing](telemetry-iracing.md)
- [Cómo se dividen las vueltas y los tramos](lap-splitting.md)
- [Deslizamiento, deriva y canales derivados](slip-and-drift.md)
- [El archivo heat3d-lap](lap-format.md)
