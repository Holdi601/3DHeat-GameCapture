---
title: Innan du börjar
nav_order: 1.5
lang: sv
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Innan du börjar {#before-you-start}

Har du aldrig använt kommandoraden förut? Den här sidan tar dig från noll till ett första fungerande
kommando. Det tar ungefär tio minuter, en gång.

## 1. Installera Python {#install-python}

GameCapture är ett Python-program. Du behöver **Python 3.10 eller senare**.

1. Gå till [python.org/downloads](https://www.python.org/downloads/) och ladda ner den senaste
   Python för Windows.
2. Kör installationsprogrammet. På första skärmen, **kryssa i "Add python.exe to PATH"**. Utan kryssen
   hittar terminalen inte Python.
3. Klicka på *Install Now*.

Eller, i en terminal: `winget install Python.Python.3.12`.

## 2. Installera Git {#install-git}

Git hämtar verktyget. Hämta det från [git-scm.com](https://git-scm.com/download/win), eller kör
`winget install Git.Git`. Vill du inte använda Git, välj *Code > Download ZIP* på
[GitHub-sidan](https://github.com/Holdi601/3DHeat-GameCapture) och packa upp den.

## 3. Öppna en terminal i en mapp {#open-a-terminal-in-a-folder}

En terminal är ett fönster där du skriver kommandon. De här sidorna använder **PowerShell**, som
alla Windows-datorer har.

- Öppna mappen i Utforskaren, klicka i adressfältet, skriv `powershell` och tryck på Enter.
  PowerShell öppnas **i den mappen**.
- Eller öppna PowerShell från Start-menyn och flytta dig till en mapp med `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Läs kommandona på de här sidorna {#read-the-commands-on-these-pages}

- Skriv varje kommandorad och tryck på Enter.
- Text inom vinkelparenteser är en **platshållare**: skriv ditt eget värde där, utan parenteserna.
  `<recording>.mp4` betyder ett filnamn som `match1.mp4`.
- Text inom hakparenteser, som `[--fps 5]`, är **valfri**.
- En sökväg med mellanslag behöver citattecken: `"C:\My Videos\match1.mp4"`.
- Rader som börjar med `#` är kommentarer. Du skriver inte dem.

## 5. Hämta verktyget och dess paket {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` skapar en privat mapp för verktygets paket, så att de inte blandas med något
annat på din dator. Varje kommando börjar sedan med `.venv\Scripts\python`.

**Du bör se** att sista raden säger `Successfully installed ...`. Kontrollera att verktyget fungerar:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Du bör se** en lista med kommandon, som börjar med `usage: heat3d_capture`.

![Listan med kommandon som --help skriver ut](../assets/img/cli-help.svg)

Du kan också *aktivera* mappen en gång, och sedan skriva bara `python`:

| Terminal | Aktivera | Sedan |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Om PowerShell säger *running scripts is disabled*, kör
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` en gång, eller hoppa över aktiveringen.

## 6. Extra program som vissa kommandon behöver {#extra-programs-some-commands-need}

| Kommando | Behöver | Installera |
|---|---|---|
| `hud` | **ffmpeg** och **ffprobe** (läser videofiler) | `winget install Gyan.FFmpeg`, öppna sedan en ny terminal. Kontrollera med `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installerat före de andra paketen | kommandot från [pytorch.org](https://pytorch.org/get-started/locally/) för din GPU |

## När något går fel {#when-something-goes-wrong}

| Du ser | Det betyder | Gör så här |
|---|---|---|
| `'python' is not recognized` | Python finns inte på PATH | Installera om Python med PATH-kryssen, öppna sedan en ny terminal. |
| `No module named heat3d_capture` | terminalen står inte i verktygets mapp | `cd` till mappen `3DHeat-GameCapture`. |
| `No module named numpy` (eller ett annat paket) | paketen är inte installerade, eller du använde en annan Python | Kör raden `pip install -r requirements.txt` igen, med `.venv\Scripts\python`. |
| `'.venv' is not recognized` | du skrev `/` i cmd | Använd bakstreck: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg saknas | Se steg 6, öppna sedan en ny terminal. |

Nästa steg: [Startsidan](index.md) har ett första exempel för varje uppgift.
