---
title: Før du går i gang
nav_order: 1.5
lang: "da"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Før du går i gang {#before-you-start}

Ny til kommandolinjen? Denne side fører dig fra ingenting til en første fungerende kommando. Det tager
cirka ti minutter, én gang.

## 1. Installer Python {#install-python}

GameCapture er et Python-program. Du har brug for **Python 3.10 eller nyere**.

1. Gå til [python.org/downloads](https://www.python.org/downloads/) og hent den nyeste
   Python til Windows.
2. Kør installationsprogrammet. På den første skærm **sætter du flueben i "Add python.exe to PATH"**. Uden
   flueben finder terminalen ikke Python.
3. Klik på *Install Now*.

Eller i en terminal: `winget install Python.Python.3.12`.

## 2. Installer Git {#install-git}

Git henter værktøjet. Hent det fra [git-scm.com](https://git-scm.com/download/win), eller kør
`winget install Git.Git`. Vil du ikke bruge Git, så brug *Code > Download ZIP* på
[GitHub-siden](https://github.com/Holdi601/3DHeat-GameCapture) og pak den ud.

## 3. Åbn en terminal i en mappe {#open-a-terminal-in-a-folder}

En terminal er et vindue, hvor du skriver kommandoer. Disse sider bruger **PowerShell**, som enhver
Windows-pc har.

- Åbn mappen i Stifinder, klik i adresselinjen, skriv `powershell` og tryk Enter.
  PowerShell åbner **i den mappe**.
- Eller åbn PowerShell fra startmenuen og flyt til en mappe med `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Læs kommandoerne på disse sider {#read-the-commands-on-these-pages}

- Skriv hver kommandolinje og tryk Enter.
- Tekst i spidse parenteser er en **pladsholder**: skriv din egen værdi der, uden parenteserne.
  `<recording>.mp4` betyder et filnavn som `match1.mp4`.
- Tekst i firkantede parenteser, såsom `[--fps 5]`, er **valgfri**.
- En sti med mellemrum skal have anførselstegn: `"C:\My Videos\match1.mp4"`.
- Linjer, der starter med `#`, er kommentarer. Du skriver dem ikke.

## 5. Hent værktøjet og dets pakker {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` laver en privat mappe til værktøjets pakker, så de ikke blander sig med
noget andet på din pc. Hver kommando starter derefter med `.venv\Scripts\python`.

**Du bør se**, at den sidste linje siger `Successfully installed ...`. Kontroller, at værktøjet virker:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Du bør se** en liste over kommandoer, der starter med `usage: heat3d_capture`.

![Listen over kommandoer, --help udskriver](../assets/img/cli-help.svg)

Du kan også *aktivere* mappen én gang og derefter kun skrive `python`:

| Terminal | Aktiver | Derefter |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Siger PowerShell *running scripts is disabled*, så kør
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` én gang, eller spring aktiveringen over.

## 6. Ekstra programmer, nogle kommandoer har brug for {#extra-programs-some-commands-need}

| Kommando | Har brug for | Installer |
|---|---|---|
| `hud` | **ffmpeg** og **ffprobe** (læser videofiler) | `winget install Gyan.FFmpeg`, og åbn derefter en ny terminal. Kontrollér med `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installeret før de andre pakker | kommandoen fra [pytorch.org](https://pytorch.org/get-started/locally/) til din GPU |

## Når noget går galt {#when-something-goes-wrong}

| Du ser | Det betyder | Gør dette |
|---|---|---|
| `'python' is not recognized` | Python står ikke på PATH | Installer Python igen med PATH-flueben, og åbn derefter en ny terminal. |
| `No module named heat3d_capture` | terminalen er ikke i værktøjets mappe | `cd` ind i mappen `3DHeat-GameCapture`. |
| `No module named numpy` (eller en anden pakke) | pakkerne er ikke installeret, eller du brugte en anden Python | Kør linjen `pip install -r requirements.txt` igen, med `.venv\Scripts\python`. |
| `'.venv' is not recognized` | du skrev `/` i cmd | Brug skråstreger med bagud: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg mangler | Se trin 6, og åbn derefter en ny terminal. |

Næste: [Start](index.md) har et første eksempel for hver opgave.
