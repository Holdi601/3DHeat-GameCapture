---
title: "Las reglas"
nav_order: 2
lang: "es"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Las reglas bajo las que se construye esto {#the-rules-this-is-built-under}

Todas las partes de 3DHeat GameCapture siguen las mismas restricciones. Son decisiones de diseño, no advertencias legales, y varias de ellas cuestan precisión a propósito.

## Nada se inyecta, nada se engancha {#nothing-is-injected-nothing-is-hooked}

Ninguna parte de esto se adjunta a un proceso de juego, lee su memoria ni toca su API gráfica.

- **Los fotogramas** vienen de Windows Graphics Capture, la API pública que usan las grabadoras de pantalla (a través del paquete `windows-capture`), o de un archivo de vídeo. Véase [Captura, máscaras y calidad de fotograma](reconstruction-capture.md).
- **La telemetría** llega solo desde las interfaces que los juegos publican para ello:
  - el flujo UDP Data Out de Forza, activado en los ajustes del juego;
  - las páginas de memoria compartida con nombre que publican los juegos de Kunos para las aplicaciones (`Local\acpmf_physics` y similares). Se abren en modo de solo lectura con `mmap`; es la forma documentada en que las aplicaciones las leen, no lectura de memoria del proceso del juego;
  - la telemetría UDP que envían EA SPORTS WRC, los juegos DiRT y Richard Burns Rally (mediante el plugin RSF/NGP) cuando se activa en sus propios archivos de ajustes;
  - la interfaz de protocolo de BeamNG, a través de un pequeño mod Lua de "protocolo" que carga y envía el propio `lua/vehicle/protocols.lua` del juego;
  - la interfaz de plugin de Openplanet de Trackmania, mediante un plugin que solo lee lo que expone Openplanet y escribe archivos;
  - los propios archivos de telemetría `.ibt` de iRacing.

## Por qué importa {#why-it-matters}

El juego conoce la profundidad de cada píxel con exactitud, y un búfer de profundidad enganchado haría que la reconstrucción de niveles fuera casi perfecta y trivial. Pero también implicaría inyectarse en procesos que quizá estén protegidos por sistemas antitrampas, lo que pone en riesgo la cuenta de cualquiera que lo ejecute. Por eso la profundidad se *estima* a partir de la imagen ([Profundidad](reconstruction-depth.md)), y buena parte de la cadena de reconstrucción existe para recuperar cuanta precisión perdida sea posible a partir de fuentes libres de usar: poses de telemetría donde un juego las publique, una escala de plano de suelo donde no lo haga, y máscaras que mantienen el HUD y la cabina fuera de la solución.

Se consideró el búfer de profundidad de ReShade y no se usó. ReShade desactiva el acceso a la profundidad en las sesiones multijugador por diseño, así que solo ayudaría en títulos para un jugador (véase [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Cosas que la herramienta cambia en tu equipo, y solo si lo pides {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Acción | Cuándo | Qué exactamente |
|---|---|---|
| Instala paquetes de Python | la primera ejecución de la ventana de escaneo, tras un diálogo y un sí | `pip install` en el intérprete que ejecuta la herramienta; con `scan.bat`, el `.venv` privado junto a él. Nunca en todo el sistema por sí mismo. |
| Convierte el modelo de profundidad | botón «Set up the depth model», tras un segundo diálogo para PyTorch y similares | escribe `models/depth-small-518.onnx` |
| Edita el `config.json` de EA SPORTS WRC | `telemetry --game wrc --configure <file>` | activa el paquete `wrc` / `session_update` hacia 127.0.0.1; el archivo anterior se guarda como `config.json.bak` |
| Copia el mod de BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` a `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (sustituyendo una copia anterior) |
| Copia el plugin de Trackmania | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` a `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (sustituyendo una copia anterior) |
| Registra atajos globales | mientras la ventana de escaneo está abierta (Windows) | Ctrl+Alt+F9 / F10 / F11, liberados al cerrar la ventana |
| Actualiza la herramienta | tras responder sí al aviso de actualización, o ejecutando `python -m heat3d_update` | véase [Actualizaciones](updates.md) |

La herramienta **no** edita el `hardware_settings_config.xml` de los juegos DiRT ni el `RichardBurnsRally.ini` de Richard Burns Rally; tú mismo activas su salida UDP (véase [Juegos de rally](telemetry-rally.md)).

## Qué se lee y qué se queda en tu equipo {#what-is-read-and-what-stays-on-your-machine}

Las herramientas leen lo que el juego muestra en pantalla y la telemetría y los archivos que publica para ello, en tu propio ordenador. Nada de un juego se incluye ni se redistribuye: ningún recurso del juego, ningún código del juego, ninguna DLL. Los archivos de vuelta, las grabaciones, las reconstrucciones y los circuitos exportados se quedan en tu equipo; el `.gitignore` del repositorio deja fuera del control de versiones las grabaciones, los archivos de vuelta, las mallas, los pesos de los modelos y el vídeo, por carpeta y por tipo de archivo.

3DHeat GameCapture no está afiliado a ningún editor de juegos ni cuenta con su respaldo. Los nombres de los juegos y las marcas relacionadas pertenecen a sus propietarios. Titulares de derechos: abrid un issue en [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - respondemos rápido y retiramos lo que se pida.
