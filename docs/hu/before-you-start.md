---
title: "Mielőtt elkezded"
nav_order: 1.5
lang: hu
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Mielőtt elkezded {#before-you-start}

Még nem használt parancssort? Ez az oldal a semmitől az első működő parancsig vezet, körülbelül tíz perc alatt,
egyszer.

## 1. Telepítsd a Pythont {#install-python}

A GameCapture egy Python-program. **Python 3.10 vagy újabb** kell.

1. Menj a [python.org/downloads](https://www.python.org/downloads/) oldalra, és töltsd le a legújabb
   Python-verziót Windowsra.
2. Futtasd a telepítőt. Az első képernyőn **pipáld be a „Add python.exe to PATH”** lehetőséget. Ennek
   bepipálása nélkül a terminál nem találja a Pythont.
3. Kattints az *Install Now* gombra.

Vagy terminálban: `winget install Python.Python.3.12`.

## 2. Telepítsd a Gitet {#install-git}

A Git tölti le az eszközt. Szerezd be a [git-scm.com](https://git-scm.com/download/win) oldalról, vagy futtasd a
`winget install Git.Git` parancsot. Ha nem kell a Git, használd a *Code > Download ZIP* lehetőséget a
[GitHub oldalon](https://github.com/Holdi601/3DHeat-GameCapture), és csomagold ki.

## 3. Nyiss terminált egy mappában {#open-a-terminal-in-a-folder}

A terminál egy ablak, ahová parancsokat gépel. Ezek az oldalak **PowerShellt** használnak, amely minden
Windows-gépen megvan.

- Nyisd meg a mappát a Fájlkezelőben, kattints a címsorba, gépeld be a `powershell`-t, és nyomj Entert.
  A PowerShell **abban a mappában** nyílik meg.
- Vagy nyisd meg a PowerShellt a Start menüből, és lépj egy mappába a `cd` paranccsal:

```powershell
cd "C:\Games\Tools"
```

## 4. Olvasd a parancsokat ezeken az oldalakon {#read-the-commands-on-these-pages}

- Minden parancssort gépelj be, és nyomj Entert.
- Az a szöveg, amely szögletes zárójelben van, egy **helyőrző**: írj oda a saját értéket, a zárójelek nélkül.
  A `<recording>.mp4` egy fájlnevet jelent, például `match1.mp4`-et.
- A szögletes zárójelben álló szöveg, például a `[--fps 5]`, **nem kötelező**.
- A szóközöket tartalmazó útvonalat idézőjelbe kell tenni: `"C:\My Videos\match1.mp4"`.
- A `#` karakterrel kezdődő sorok megjegyzések. Ezeket nem kell beírni.

## 5. Szerezd meg az eszközt és a csomagjait {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

A `python -m venv .venv` egy saját mappát hoz létre az eszköz csomagjainak, így nem keverednek a gépén lévő
többi dologgal. Ezután minden parancs `.venv\Scripts\python`-nal kezdődik.

**Ezt kell látnod:** az utolsó sor `Successfully installed ...`-val kezdődik. Ellenőrizd, hogy az eszköz működik:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Ezt kell látnod:** a parancsok listáját, amely `usage: heat3d_capture`-rel kezdődik.

![A parancsok listája, amelyet a --help kiír](../assets/img/cli-help.svg)

Egyszer *aktiválhatod* a mappát, utána már csak `python`-t kell gépelned:

| Terminál | Aktiválás | Utána |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ha a PowerShell azt mondja, hogy *a szkriptek futtatása le van tiltva*, futtasd egyszer a
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` parancsot, vagy hagyd ki az aktiválást.

## 6. Extra programok, amelyekre egyes parancsoknak szükségük van {#extra-programs-some-commands-need}

| Parancs | Szükséges | Telepítés |
|---|---|---|
| `hud` | **ffmpeg** és **ffprobe** (videófájlok olvasása) | `winget install Gyan.FFmpeg`, majd nyiss új terminált. Ellenőrzés: `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, a többi csomag előtt telepítve | a parancs a [pytorch.org](https://pytorch.org/get-started/locally/) oldalról, a saját GPU-dhoz |

## Ha valami nem jól működik {#when-something-goes-wrong}

| Amit lát | Mit jelent | Mit tegyél |
|---|---|---|
| `'python' is not recognized` | a Python nincs a PATH-ban | telepítsd újra a Pythont a PATH-pipával, majd nyiss új terminált. |
| `No module named heat3d_capture` | a terminál nincs az eszköz mappájában | lépj a `3DHeat-GameCapture` mappába a `cd` paranccsal. |
| `No module named numpy` (vagy más csomag) | a csomagok nincsenek telepítve, vagy másik Pythont használt | futtasd újra a `pip install -r requirements.txt` sort, a `.venv\Scripts\python`-nal. |
| `'.venv' is not recognized` | cmd-ben `/`-t gépelt | használj fordított perjeleket: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | az ffmpeg hiányzik | lásd a 6. lépést, majd nyiss új terminált. |

Következő: a [Főoldal](index.md) mindhárom feladathoz ad egy első példát.
