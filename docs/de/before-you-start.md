---
title: "Bevor du anfängst"
nav_order: 1.5
lang: de
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Bevor du anfängst {#before-you-start}

Neu in der Kommandozeile? Diese Seite bringt dich von nichts zu einem ersten funktionierenden Befehl. Das
dauert einmalig etwa zehn Minuten.

## 1. Python installieren {#install-python}

GameCapture ist ein Python-Programm. Du brauchst **Python 3.10 oder neuer**.

1. Geh zu [python.org/downloads](https://www.python.org/downloads/) und lade das neueste
   Python für Windows herunter.
2. Starte das Installationsprogramm. Setze auf dem ersten Bildschirm den Haken bei **"Add python.exe to PATH"**.
   Ohne den Haken findet das Terminal Python nicht.
3. Klicke auf *Install Now*.

Oder in einem Terminal: `winget install Python.Python.3.12`.

## 2. Git installieren {#install-git}

Git lädt das Werkzeug herunter. Hol es von [git-scm.com](https://git-scm.com/download/win), oder führe
`winget install Git.Git` aus. Wenn du Git nicht willst, nimm *Code > Download ZIP* auf der
[GitHub-Seite](https://github.com/Holdi601/3DHeat-GameCapture) und entpacke es.

## 3. Ein Terminal in einem Ordner öffnen {#open-a-terminal-in-a-folder}

Ein Terminal ist ein Fenster, in das du Befehle tippst. Diese Seiten benutzen **PowerShell**, das jeder
Windows-PC hat.

- Öffne den Ordner im Explorer, klicke in die Adressleiste, tippe `powershell` und drücke Enter.
  PowerShell öffnet sich **in diesem Ordner**.
- Oder öffne PowerShell über das Startmenü und wechsle mit `cd` in einen Ordner:

```powershell
cd "C:\Games\Tools"
```

## 4. Die Befehle auf diesen Seiten lesen {#read-the-commands-on-these-pages}

- Tippe jede Befehlszeile und drücke Enter.
- Text in spitzen Klammern ist ein **Platzhalter**: Trage dort deinen eigenen Wert ein, ohne die Klammern.
  `<recording>.mp4` heißt ein Dateiname wie `match1.mp4`.
- Text in eckigen Klammern, wie `[--fps 5]`, ist **optional**.
- Ein Pfad mit Leerzeichen braucht Anführungszeichen: `"C:\My Videos\match1.mp4"`.
- Zeilen, die mit `#` beginnen, sind Kommentare. Du tippst sie nicht.

## 5. Das Werkzeug und seine Pakete holen {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` legt einen eigenen Ordner für die Pakete des Werkzeugs an, damit sie sich nicht mit
anderem auf deinem PC vermischen. Jeder Befehl beginnt danach mit `.venv\Scripts\python`.

**Du solltest sehen**, dass die letzte Zeile `Successfully installed ...` sagt. Prüfe, ob das Werkzeug läuft:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Du solltest sehen** eine Liste von Befehlen, die mit `usage: heat3d_capture` beginnt.

![Die Befehlsliste, die --help ausgibt](../assets/img/cli-help.svg)

Du kannst den Ordner auch einmal *aktivieren* und dann nur `python` tippen:

| Terminal | Aktivieren | Dann |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Wenn PowerShell sagt *running scripts is disabled*, führe einmal
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` aus, oder lass das Aktivieren weg.

## 6. Zusätzliche Programme, die manche Befehle brauchen {#extra-programs-some-commands-need}

| Befehl | Braucht | Installieren |
|---|---|---|
| `hud` | **ffmpeg** und **ffprobe** (Videodateien lesen) | `winget install Gyan.FFmpeg`, dann ein neues Terminal öffnen. Prüfen mit `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, vor den anderen Paketen installiert | der Befehl von [pytorch.org](https://pytorch.org/get-started/locally/) für deine GPU |

## Wenn etwas schiefgeht {#when-something-goes-wrong}

| Du siehst | Es bedeutet | Das tun |
|---|---|---|
| `'python' is not recognized` | Python ist nicht im PATH | Installiere Python mit dem PATH-Haken neu, dann öffne ein neues Terminal. |
| `No module named heat3d_capture` | das Terminal ist nicht im Ordner des Werkzeugs | `cd` in den Ordner `3DHeat-GameCapture`. |
| `No module named numpy` (oder ein anderes Paket) | die Pakete sind nicht installiert, oder du hast ein anderes Python benutzt | Führe die Zeile `pip install -r requirements.txt` noch einmal aus, mit `.venv\Scripts\python`. |
| `'.venv' is not recognized` | du hast in cmd `/` getippt | Benutze Backslashes: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg fehlt | Siehe Schritt 6, dann ein neues Terminal öffnen. |

Weiter: [Startseite](index.md) hat ein erstes Beispiel für jede Aufgabe.
