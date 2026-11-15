---
title: "Actualizaciones"
nav_order: 10
lang: "es"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Actualizaciones {#updates}

3DHeat GameCapture comprueba las versiones de GitHub de este repositorio al arrancar, avisa cuando hay una versión más reciente y ofrece actualizar. Código: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Cuándo se hace la comprobación {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - antes de ejecutar el comando.
- `python -m heat3d_capture.ui` (y `scan.bat`) - antes de abrir la ventana.
- `python -m heat3d_update` - cuando se pide, consultando siempre a GitHub de nuevo.

## Cómo funciona la comprobación {#how-the-check-works}

- La versión instalada es el archivo `VERSION` de la raíz del repositorio (por ejemplo `1.0.1`).
- La versión más reciente se pide a `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, con un tiempo de espera de **5 segundos**. Una red lenta nunca detiene la herramienta más de eso.
- La respuesta se guarda en caché durante **6 horas** en `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` sin `LOCALAPPDATA`). Cada herramienta de 3DHeat tiene su propio archivo de caché. «Todavía no hay versión» (HTTP 404) se guarda en caché como cualquier respuesta; los demás fallos no se guardan y simplemente significan que no hay aviso.
- Las versiones se comparan numéricamente (`v1.2.3` o `1.2.3`; lo que venga después de `-` o `+` se ignora).
- Sin conexión, con límite de peticiones o detrás de un proxy, la herramienta sigue con la versión que tiene.

## Qué pasa cuando hay una versión nueva {#what-happens-when-a-newer-release-is-out}

Al arrancar imprime, en el flujo de errores:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Con una terminal donde responder, pregunta `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` significan sí). Tras una actualización correcta **el mismo comando se vuelve a iniciar**, con el código nuevo.
- Sin terminal (una tubería, una ejecución programada), imprime `Run python -m heat3d_update in <folder> to update.` y sigue sin cambios.

## Cómo se aplica una actualización {#how-an-update-is-applied}

Depende de cómo se instalaron las herramientas:

- **Un clon de git** (una carpeta `.git` y `git` en el PATH): `git pull --ff-only`. Se rechaza mientras la copia de trabajo tenga cambios locales en archivos controlados; son trabajo de alguien, así que confírmalos o guárdalos antes (stash).
- **Una copia descargada**: se descarga el archivo de código fuente de la versión, se extrae en una carpeta temporal (las entradas fuera de la carpeta del propio archivo se omiten) y se **comprueba que es la versión que dice ser** según su archivo `VERSION`. Luego sus archivos se copian sobre esta carpeta. Dentro de los paquetes de Python de la versión (carpetas `heat3d_*` en la raíz del repositorio, y un nivel más abajo para la antigua estructura de monorepo), se borran los módulos `.py` que la versión ya no tiene, para que un módulo obsoleto no tape a su sustituto.

Tus propios archivos -grabaciones, archivos de vuelta, ajustes, exportaciones, el `.venv`- nunca se tocan: solo se escriben los archivos que forman parte de la versión.

## A mano {#by-hand}

```bash
python -m heat3d_update            # comprueba y actualiza
python -m heat3d_update --check    # solo indica si hay una versión más reciente
```

Imprime `Up to date: <version>.`, `No release found ... offline, or nothing published yet.`, o la nueva versión y lo que hizo. Código de salida 1 si la actualización no pudo aplicarse.

## Desactivarlo {#switching-it-off}

Define **`HEAT3D_NO_UPDATE=1`** (cualquier valor excepto vacío, `0`, `false`, `no`). Así se desactiva la comprobación y el aviso al arrancar. `python -m heat3d_update` sigue comprobando cuando se ejecuta a mano.
