---
title: Før du starter
nav_order: 1.5
lang: no
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Før du starter {#before-you-start}

Ny til kommandolinjen? Denne siden tar deg fra null til en første fungerende kommando. Det tar
omtrent ti minutter, én gang.

## 1. Installer Python {#install-python}

GameCapture er et Python-program. Du trenger **Python 3.10 eller nyere**.

1. Gå til [python.org/downloads](https://www.python.org/downloads/) og last ned den nyeste
   Python for Windows.
2. Kjør installasjonen. På første skjerm, **kryss av «Add python.exe to PATH»**. Uten avkrysningen
   finner ikke terminalen Python.
3. Klikk *Install Now*.

Eller, i en terminal: `winget install Python.Python.3.12`.

## 2. Installer Git {#install-git}

Git laster ned verktøyet. Skaff det fra [git-scm.com](https://git-scm.com/download/win), eller kjør
`winget install Git.Git`. Vil du ikke ha Git, bruk *Code > Download ZIP* på
[GitHub-siden](https://github.com/Holdi601/3DHeat-GameCapture) og pakk den ut.

## 3. Åpne en terminal i en mappe {#open-a-terminal-in-a-folder}

En terminal er et vindu der du skriver kommandoer. Disse sidene bruker **PowerShell**, som
alle Windows-PC-er har.

- Åpne mappen i Filutforsker, klikk i adressefeltet, skriv `powershell` og trykk Enter.
  PowerShell åpnes **i den mappen**.
- Eller åpne PowerShell fra Start-menyen og gå til en mappe med `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Les kommandoene på disse sidene {#read-the-commands-on-these-pages}

- Skriv inn hver kommandolinje og trykk Enter.
- Tekst i vinkelparenteser er en **plassholder**: sett inn din egen verdi der, uten parentesene.
  `<recording>.mp4` betyr et filnavn som `match1.mp4`.
- Tekst i hakeparenteser, som `[--fps 5]`, er **valgfri**.
- En sti med mellomrom trenger anførselstegn: `"C:\My Videos\match1.mp4"`.
- Linjer som starter med `#` er kommentarer. Du skriver dem ikke.

## 5. Skaff verktøyet og pakkene {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` lager en privat mappe for verktøyets pakker, så de ikke blandes med
noe annet på PC-en din. Hver kommando starter deretter med `.venv\Scripts\python`.

**Du bør se** at siste linje sier `Successfully installed ...`. Sjekk at verktøyet virker:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Du bør se** en liste over kommandoer, som starter med `usage: heat3d_capture`.

![Listen over kommandoer som --help skriver ut](../assets/img/cli-help.svg)

Du kan også *aktivere* mappen én gang, og deretter skrive bare `python`:

| Terminal | Aktiver | Deretter |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Hvis PowerShell sier *running scripts is disabled*, kjør
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` én gang, eller hopp over aktiveringen.

## 6. Ekstra programmer noen kommandoer trenger {#extra-programs-some-commands-need}

| Kommando | Trenger | Installer |
|---|---|---|
| `hud` | **ffmpeg** og **ffprobe** (leser videofiler) | `winget install Gyan.FFmpeg`, åpne deretter en ny terminal. Sjekk med `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installert før de andre pakkene | kommandoen fra [pytorch.org](https://pytorch.org/get-started/locally/) for din GPU |

## Når noe går galt {#when-something-goes-wrong}

| Du ser | Det betyr | Gjør dette |
|---|---|---|
| `'python' is not recognized` | Python er ikke på PATH | Installer Python på nytt med PATH-avkrysningen, og åpne deretter en ny terminal. |
| `No module named heat3d_capture` | terminalen står ikke i verktøyets mappe | `cd` inn i mappen `3DHeat-GameCapture`. |
| `No module named numpy` (eller en annen pakke) | pakkene er ikke installert, eller du brukte en annen Python | Kjør linjen `pip install -r requirements.txt` igjen, med `.venv\Scripts\python`. |
| `'.venv' is not recognized` | du skrev `/` i cmd | Bruk skråstreker bakover: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg mangler | Se steg 6, og åpne deretter en ny terminal. |

Neste: [Hjem](index.md) har et første eksempel for hver jobb.
