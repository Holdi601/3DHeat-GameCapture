---
title: "Prije nego počneš"
nav_order: 1.5
lang: bs
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Prije nego počneš {#before-you-start}

Komandna linija ti je nova? Ova stranica te vodi od ničega do prve naredbe koja radi. Traje
oko deset minuta, jednom.

## 1. Instaliraj Python {#install-python}

GameCapture je Python program. Treba ti **Python 3.10 ili noviji**.

1. Idi na [python.org/downloads](https://www.python.org/downloads/) i preuzmi najnoviji
   Python za Windows.
2. Pokreni instalacijski program. Na prvom ekranu **označi "Add python.exe to PATH"**. Bez te oznake
   terminal neće naći Python.
3. Klikni *Install Now*.

Ili, u terminalu: `winget install Python.Python.3.12`.

## 2. Instaliraj Git {#install-git}

Git preuzima alat. Nabavi ga sa [git-scm.com](https://git-scm.com/download/win) ili pokreni
`winget install Git.Git`. Ako ne želiš Git, na
[GitHub stranici](https://github.com/Holdi601/3DHeat-GameCapture) koristi *Code > Download ZIP* i raspakuj ga.

## 3. Otvori terminal u folderu {#open-a-terminal-in-a-folder}

Terminal je prozor u koji upisuješ naredbe. Ove stranice koriste **PowerShell**, koji ima svaki
Windows računar.

- Otvori folder u File Exploreru, klikni u adresnu traku, upiši `powershell` i pritisni Enter.
  PowerShell se otvara **u tom folderu**.
- Ili otvori PowerShell iz Start izbornika i dođi do foldera pomoću `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Čitanje naredbi na ovim stranicama {#read-the-commands-on-these-pages}

- Upiši svaki red naredbe i pritisni Enter.
- Tekst u špicastim zagradama `< >` je **rezervirano mjesto**: stavi tamo vlastitu vrijednost, bez zagrada.
  `<recording>.mp4` znači naziv datoteke poput `match1.mp4`.
- Tekst u uglastim zagradama `[ ]`, kao `[--fps 5]`, je **neobavezan**.
- Putanja s razmacima treba navodnike: `"C:\My Videos\match1.mp4"`.
- Redovi koji počinju s `#` su komentari. Ne upisuješ ih.

## 5. Nabavi alat i njegove pakete {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` pravi privatni folder za pakete alata, da se ne miješaju s
ničim drugim na tvom računaru. Svaka naredba zatim počinje s `.venv\Scripts\python`.

**Trebao bi vidjeti** da zadnji red kaže `Successfully installed ...`. Provjeri radi li alat:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Trebao bi vidjeti** popis naredbi koji počinje s `usage: heat3d_capture`.

![Popis naredbi koji ispisuje --help](../assets/img/cli-help.svg)

Možeš i jednom *aktivirati* folder, pa upisivati samo `python`:

| Terminal | Aktiviraj | Zatim |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ako PowerShell kaže *running scripts is disabled*, jednom pokreni
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ili preskoči aktiviranje.

## 6. Dodatni programi koje neke naredbe trebaju {#extra-programs-some-commands-need}

| Naredba | Treba | Instalacija |
|---|---|---|
| `hud` | **ffmpeg** i **ffprobe** (čitaju video datoteke) | `winget install Gyan.FFmpeg`, zatim otvori novi terminal. Provjeri pomoću `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instaliran prije ostalih paketa | naredba sa [pytorch.org](https://pytorch.org/get-started/locally/) za tvoj GPU |

## Kad nešto pođe po zlu {#when-something-goes-wrong}

| Vidiš | Znači | Uradi ovo |
|---|---|---|
| `'python' is not recognized` | Python nije na PATH-u | Ponovo instaliraj Python s oznakom PATH, pa otvori novi terminal. |
| `No module named heat3d_capture` | terminal nije u folderu alata | Uradi `cd` u folder `3DHeat-GameCapture`. |
| `No module named numpy` (ili drugi paket) | paketi nisu instalirani ili si koristio drugi Python | Ponovo pokreni red `pip install -r requirements.txt`, s `.venv\Scripts\python`. |
| `'.venv' is not recognized` | upisao si `/` u cmd | Koristi obrnute kose crte: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nedostaje | Vidi korak 6, pa otvori novi terminal. |

Dalje: [Početna](index.md) ima prvi primjer za svaki posao.
