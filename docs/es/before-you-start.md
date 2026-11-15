---
title: Antes de empezar
nav_order: 1.5
lang: es
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Antes de empezar {#before-you-start}

¿Nuevo en la línea de comandos? Esta página te lleva de cero a tu primer comando que funciona.
Tarda unos diez minutos, una sola vez.

## 1. Instalar Python {#install-python}

GameCapture es un programa de Python. Necesitas **Python 3.10 o posterior**.

1. Ve a [python.org/downloads](https://www.python.org/downloads/) y descarga la versión más reciente
   de Python para Windows.
2. Ejecuta el instalador. En la primera pantalla, **marca "Add python.exe to PATH"**. Sin esa marca,
   la terminal no encontrará Python.
3. Haz clic en *Install Now*.

O, en una terminal: `winget install Python.Python.3.12`.

## 2. Instalar Git {#install-git}

Git descarga la herramienta. Consíguelo en [git-scm.com](https://git-scm.com/download/win), o ejecuta
`winget install Git.Git`. Si no quieres Git, usa *Code > Download ZIP* en la
[página de GitHub](https://github.com/Holdi601/3DHeat-GameCapture) y descomprímelo.

## 3. Abrir una terminal en una carpeta {#open-a-terminal-in-a-folder}

Una terminal es una ventana donde escribes comandos. Estas páginas usan **PowerShell**, que tiene
cualquier PC con Windows.

- Abre la carpeta en el Explorador de archivos, haz clic en la barra de direcciones, escribe
  `powershell` y pulsa Intro. PowerShell se abre **en esa carpeta**.
- O abre PowerShell desde el menú Inicio y cambia de carpeta con `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Leer los comandos de estas páginas {#read-the-commands-on-these-pages}

- Escribe cada línea de comando y pulsa Intro.
- El texto entre corchetes angulares es un **marcador**: pon ahí tu propio valor, sin los corchetes.
  `<recording>.mp4` significa un nombre de archivo como `match1.mp4`.
- El texto entre corchetes, como `[--fps 5]`, es **opcional**.
- Una ruta con espacios necesita comillas: `"C:\My Videos\match1.mp4"`.
- Las líneas que empiezan por `#` son comentarios. No las escribes.

## 5. Conseguir la herramienta y sus paquetes {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` crea una carpeta privada para los paquetes de la herramienta, para que no se
mezclen con nada más de tu PC. Desde ahí, cada comando empieza por `.venv\Scripts\python`.

**Deberías ver** que la última línea dice `Successfully installed ...`. Comprueba que la herramienta
funciona:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Deberías ver** una lista de comandos, que empieza por `usage: heat3d_capture`.

![La lista de comandos que imprime --help](../assets/img/cli-help.svg)

También puedes *activar* la carpeta una vez, y luego escribir solo `python`:

| Terminal | Activar | Después |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Si PowerShell dice *running scripts is disabled*, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o prescinde de activar.

## 6. Programas extra que necesitan algunos comandos {#extra-programs-some-commands-need}

| Comando | Necesita | Instalar |
|---|---|---|
| `hud` | **ffmpeg** y **ffprobe** (leer archivos de vídeo) | `winget install Gyan.FFmpeg`, y luego abre una terminal nueva. Compruébalo con `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instalado antes que los demás paquetes | el comando de [pytorch.org](https://pytorch.org/get-started/locally/) para tu GPU |

## Cuando algo sale mal {#when-something-goes-wrong}

| Ves | Significa | Haz esto |
|---|---|---|
| `'python' is not recognized` | Python no está en PATH | Reinstala Python con la marca de PATH y abre una terminal nueva. |
| `No module named heat3d_capture` | la terminal no está en la carpeta de la herramienta | haz `cd` a la carpeta `3DHeat-GameCapture`. |
| `No module named numpy` (u otro paquete) | los paquetes no están instalados, o usaste otro Python | Vuelve a ejecutar la línea `pip install -r requirements.txt`, con `.venv\Scripts\python`. |
| `'.venv' is not recognized` | escribiste `/` en cmd | Usa barras invertidas: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | falta ffmpeg | Mira el paso 6 y abre una terminal nueva. |

Siguiente: [Inicio](index.md) tiene un primer ejemplo para cada tarea.
