---
title: Prije nego što počnete
nav_order: 1.5
lang: "hr"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Prije nego što počnete {#before-you-start}

Ne znate ništa o naredbenom retku? Ova stranica vas vodi od nule do prve radne naredbe.
Traje oko deset minuta, samo jednom.

## 1. Instalirajte Python {#install-python}

GameCapture je program u Pythonu. Treba vam **Python 3.10 ili noviji**.

1. Idite na [python.org/downloads](https://www.python.org/downloads/) i preuzmite najnoviji
   Python za Windows.
2. Pokrenite instalaciju. Na prvom zaslonu **označite "Add python.exe to PATH"**. Bez te oznake
   terminal neće pronaći Python.
3. Kliknite *Install Now*.

Ili, u terminalu: `winget install Python.Python.3.12`.

## 2. Instalirajte Git {#install-git}

Git preuzima alat. Nabavite ga na [git-scm.com](https://git-scm.com/download/win), ili pokrenite
`winget install Git.Git`. Ako ne želite Git, koristite *Code > Download ZIP* na
[stranici na GitHubu](https://github.com/Holdi601/3DHeat-GameCapture) i raspakirajte ga.

## 3. Otvorite terminal u mapi {#open-a-terminal-in-a-folder}

Terminal je prozor u koji upisujete naredbe. Ove stranice koriste **PowerShell**, koji ima svako
Windows računalo.

- Otvorite mapu u File Exploreru, kliknite adresnu traku, upišite `powershell` i pritisnite Enter.
  PowerShell se otvara **u toj mapi**.
- Ili otvorite PowerShell iz izbornika Start i premjestite se u mapu naredbom `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Čitanje naredbi na ovim stranicama {#read-the-commands-on-these-pages}

- Upišite svaki redak naredbe i pritisnite Enter.
- Tekst u kutnim zagradama je **mjesto za upis**: upišite svoju vrijednost, bez zagrada.
  `<recording>.mp4` znači naziv datoteke, na primjer `match1.mp4`.
- Tekst u uglatim zagradama, kao `[--fps 5]`, je **izborno**.
- Put koji ima razmake treba navodnike: `"C:\My Videos\match1.mp4"`.
- Redci koji počinju s `#` su komentari. Ne upisujete ih.

## 5. Nabavite alat i njegove pakete {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` pravi privatnu mapu za pakete alata, pa se ne miješaju s
ničim drugim na vašem računalu. Svaka naredba zatim počinje s `.venv\Scripts\python`.

**Trebali biste vidjeti** da zadnji redak kaže `Successfully installed ...`. Provjerite radi li alat:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Trebali biste vidjeti** popis naredbi, koji počinje s `usage: heat3d_capture`.

![Popis naredbi koji ispisuje --help](../assets/img/cli-help.svg)

Mapu možete i *aktivirati* jednom, pa onda upisivati samo `python`:

| Terminal | Aktiviranje | Zatim |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ako PowerShell kaže *running scripts is disabled*, pokrenite jednom
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ili preskočite aktiviranje.

## 6. Dodatni programi koje neke naredbe trebaju {#extra-programs-some-commands-need}

| Naredba | Treba | Instalacija |
|---|---|---|
| `hud` | **ffmpeg** i **ffprobe** (čitanje video datoteka) | `winget install Gyan.FFmpeg`, zatim otvorite novi terminal. Provjerite s `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instaliran prije ostalih paketa | naredba s [pytorch.org](https://pytorch.org/get-started/locally/) za vašu grafičku karticu |

## Kad nešto pođe po zlu {#when-something-goes-wrong}

| Vidite | Znači | Učinite ovo |
|---|---|---|
| `'python' is not recognized` | Python nije u PATH-u | Ponovno instalirajte Python s oznakom PATH, zatim otvorite novi terminal. |
| `No module named heat3d_capture` | terminal nije u mapi alata | `cd` u mapu `3DHeat-GameCapture`. |
| `No module named numpy` (ili drugi paket) | paketi nisu instalirani, ili ste koristili drugi Python | Ponovno pokrenite redak `pip install -r requirements.txt`, s `.venv\Scripts\python`. |
| `'.venv' is not recognized` | u cmd-u ste upisali `/` | Koristite obrnute kose crte: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nedostaje | Pogledajte korak 6, zatim otvorite novi terminal. |

Dalje: [Početna](index.md) ima prvi primjer za svaki posao.
