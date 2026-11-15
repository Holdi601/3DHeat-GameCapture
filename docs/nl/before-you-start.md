---
title: Voordat je begint
nav_order: 1.5
lang: nl
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Voordat je begint {#before-you-start}

Nog nooit met de opdrachtregel gewerkt? Deze pagina brengt je van niets tot een eerste werkend commando. Het kost
ongeveer tien minuten, eenmalig.

## 1. Installeer Python {#install-python}

GameCapture is een Python-programma. Je hebt **Python 3.10 of later** nodig.

1. Ga naar [python.org/downloads](https://www.python.org/downloads/) en download de nieuwste
   Python voor Windows.
2. Start het installatieprogramma. Vink op het eerste scherm **"Add python.exe to PATH"** aan. Zonder dit vinkje
   vindt de terminal Python niet.
3. Klik op *Install Now*.

Of, in een terminal: `winget install Python.Python.3.12`.

## 2. Installeer Git {#install-git}

Git downloadt het hulpmiddel. Haal het op via [git-scm.com](https://git-scm.com/download/win), of voer
`winget install Git.Git` uit. Wil je Git niet, gebruik dan *Code > Download ZIP* op de
[GitHub-pagina](https://github.com/Holdi601/3DHeat-GameCapture) en pak het uit.

## 3. Open een terminal in een map {#open-a-terminal-in-a-folder}

Een terminal is een venster waarin je opdrachten typt. Deze pagina's gebruiken **PowerShell**, dat elke
Windows-pc heeft.

- Open de map in Verkenner, klik in de adresbalk, typ `powershell` en druk op Enter.
  PowerShell opent **in die map**.
- Of open PowerShell via het Startmenu en ga met `cd` naar een map:

```powershell
cd "C:\Games\Tools"
```

## 4. Lees de commando's op deze pagina's {#read-the-commands-on-these-pages}

- Typ elke commandoregel en druk op Enter.
- Tekst tussen punthaken is een **plaatsaanduiding**: zet er je eigen waarde neer, zonder de haken.
  `<recording>.mp4` betekent een bestandsnaam zoals `match1.mp4`.
- Tekst tussen vierkante haken, zoals `[--fps 5]`, is **optioneel**.
- Een pad met spaties heeft aanhalingstekens nodig: `"C:\My Videos\match1.mp4"`.
- Regels die met `#` beginnen zijn opmerkingen. Die typ je niet.

## 5. Haal het hulpmiddel en zijn pakketten op {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` maakt een eigen map voor de pakketten van het hulpmiddel, zodat ze niet door elkaar lopen met
iets anders op je pc. Elk commando begint daarna met `.venv\Scripts\python`.

**Je ziet** dat de laatste regel `Successfully installed ...` zegt. Controleer of het hulpmiddel werkt:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Je ziet** een lijst met commando's, beginnend met `usage: heat3d_capture`.

![De lijst met commando's die --help afdrukt](../assets/img/cli-help.svg)

Je kunt de map ook één keer *activeren*, en daarna alleen `python` typen:

| Terminal | Activeren | Daarna |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Zegt PowerShell *running scripts is disabled*, voer dan eenmalig
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` uit, of sla het activeren over.

## 6. Extra programma's die sommige commando's nodig hebben {#extra-programs-some-commands-need}

| Commando | Heeft nodig | Installeren |
|---|---|---|
| `hud` | **ffmpeg** en **ffprobe** (videobestanden lezen) | `winget install Gyan.FFmpeg`, open daarna een nieuwe terminal. Controleer met `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, vóór de andere pakketten geïnstalleerd | het commando van [pytorch.org](https://pytorch.org/get-started/locally/) voor jouw GPU |

## Als er iets misgaat {#when-something-goes-wrong}

| Je ziet | Betekent | Doe dit |
|---|---|---|
| `'python' is not recognized` | Python staat niet in PATH | Installeer Python opnieuw met het PATH-vinkje, en open daarna een nieuwe terminal. |
| `No module named heat3d_capture` | de terminal staat niet in de map van het hulpmiddel | Ga met `cd` naar de map `3DHeat-GameCapture`. |
| `No module named numpy` (of een ander pakket) | de pakketten zijn niet geïnstalleerd, of je gebruikte een andere Python | Voer de regel `pip install -r requirements.txt` opnieuw uit, met `.venv\Scripts\python`. |
| `'.venv' is not recognized` | je typte `/` in cmd | Gebruik backslashes: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg ontbreekt | Zie stap 6, en open daarna een nieuwe terminal. |

Volgende: [Startpagina](index.md) heeft een eerste voorbeeld voor elke taak.
