---
title: "Prije nego počnete"
nav_order: 1.5
lang: "bs"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Prije nego počnete {#before-you-start}

Komandna linija vam je nova? Ova stranica vas vodi od ničega do prve komande koja radi. Traje
oko deset minuta, jednom.

## 1. Instalirajte Python {#install-python}

GameCapture je Python program. Treba vam **Python 3.10 ili noviji**.

1. Idite na [python.org/downloads](https://www.python.org/downloads/) i preuzmite najnoviji
   Python za Windows.
2. Pokrenite instalacijski program. Na prvom ekranu **označite "Add python.exe to PATH"**. Bez te oznake
   terminal neće naći Python.
3. Kliknite *Install Now*.

Ili, u terminalu: `winget install Python.Python.3.12`.

## 2. Instalirajte Git {#install-git}

Git preuzima alat. Nabavite ga sa [git-scm.com](https://git-scm.com/download/win) ili pokrenite
`winget install Git.Git`. Ako ne želite Git, na
[GitHub stranici](https://github.com/Holdi601/3DHeat-GameCapture) koristite *Code > Download ZIP* i raspakujte ga.

## 3. Otvorite terminal u folderu {#open-a-terminal-in-a-folder}

Terminal je prozor u koji upisujete komande. Ove stranice koriste **PowerShell**, koji ima svaki
Windows računar.

- Otvorite folder u File Exploreru, kliknite u adresnu traku, upišite `powershell` i pritisnite Enter.
  PowerShell se otvara **u tom folderu**.
- Ili otvorite PowerShell iz Start izbornika i dođite do foldera pomoću `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Čitanje komandi na ovim stranicama {#read-the-commands-on-these-pages}

- Upišite svaki red komande i pritisnite Enter.
- Tekst u špicastim zagradama `< >` je **rezervirano mjesto**: stavite tamo vlastitu vrijednost, bez zagrada.
  `<recording>.mp4` znači naziv datoteke poput `match1.mp4`.
- Tekst u uglastim zagradama `[ ]`, kao `[--fps 5]`, je **neobavezan**.
- Putanja s razmacima treba navodnike: `"C:\My Videos\match1.mp4"`.
- Redovi koji počinju s `#` su komentari. Ne upisujete ih.

## 5. Nabavite alat i njegove pakete {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` pravi privatni folder za pakete alata, da se ne miješaju s
ničim drugim na vašem računaru. Svaka komanda zatim počinje s `.venv\Scripts\python`.

**Trebali biste vidjeti** da zadnji red kaže `Successfully installed ...`. Provjerite radi li alat:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Trebali biste vidjeti** popis komandi koji počinje s `usage: heat3d_capture`.

![Popis komandi koji ispisuje --help](../assets/img/cli-help.svg)

Možete i jednom *aktivirati* folder, pa upisivati samo `python`:

| Terminal | Aktivirajte | Zatim |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ako PowerShell kaže *running scripts is disabled*, jednom pokrenite
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ili preskočite aktiviranje.

## 6. Dodatni programi koje neke komande trebaju {#extra-programs-some-commands-need}

| Komanda | Treba | Instalacija |
|---|---|---|
| `hud` | **ffmpeg** i **ffprobe** (čitaju video datoteke) | `winget install Gyan.FFmpeg`, zatim otvorite novi terminal. Provjerite pomoću `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instaliran prije ostalih paketa | komanda sa [pytorch.org](https://pytorch.org/get-started/locally/) za vaš GPU |

## Kad nešto pođe po zlu {#when-something-goes-wrong}

| Vidite | Znači | Uradite ovo |
|---|---|---|
| `'python' is not recognized` | Python nije na PATH-u | Ponovo instalirajte Python s oznakom PATH, pa otvorite novi terminal. |
| `No module named heat3d_capture` | terminal nije u folderu alata | Uradite `cd` u folder `3DHeat-GameCapture`. |
| `No module named numpy` (ili drugi paket) | paketi nisu instalirani ili ste koristili drugi Python | Ponovo pokrenite red `pip install -r requirements.txt`, s `.venv\Scripts\python`. |
| `'.venv' is not recognized` | upisali ste `/` u cmd | Koristite obrnute kose crte: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nedostaje | Pogledajte korak 6, pa otvorite novi terminal. |

Dalje: [Početna](index.md) ima prvi primjer za svaki posao.
