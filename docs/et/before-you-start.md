---
title: "Enne alustamist"
nav_order: 1.5
lang: "et"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Enne alustamist {#before-you-start}

Pole sul käsurealt kogemust? See leht viib sind nullist esimese töökäsuni. See võtab umbes kümme minutit, ainult üks kord.

## 1. Paigalda Python {#install-python}

GameCapture on Pythoni programm. Vajad **Python 3.10 või uuemat**.

1. Mine lehele [python.org/downloads](https://www.python.org/downloads/) ja laadi alla uusim
   Python Windowsi jaoks.
2. Käivita installer. Esimesel ekraanil **märgi "Add python.exe to PATH"**. Ilma selle märketa
   terminal Pythonit ei leia.
3. Klõpsa *Install Now*.

Või terminalis: `winget install Python.Python.3.12`.

## 2. Paigalda Git {#install-git}

Git laadib tööriista alla. Hangi see lehelt [git-scm.com](https://git-scm.com/download/win) või käsuga
`winget install Git.Git`. Kui Gitti ei soovi, kasuta *Code > Download ZIP* lehel
[GitHubi leht](https://github.com/Holdi601/3DHeat-GameCapture) ja paki lahti.

## 3. Ava terminal kaustas {#open-a-terminal-in-a-folder}

Terminal on aken, kuhu kirjutad käske. Need lehed kasutavad **PowerShelli**, mis on igas Windowsi arvutis.

- Ava kaust Exploreris, klõpsa aadressiribale, kirjuta `powershell` ja vajuta Enter.
  PowerShell avaneb **selles kaustas**.
- Või ava PowerShell Starti menüüst ja liigu kausta `cd`-ga:

```powershell
cd "C:\Games\Tools"
```

## 4. Loe nende lehtede käske {#read-the-commands-on-these-pages}

- Kirjuta iga käsurida ja vajuta Enter.
- Tekst nurksulgudes on **kohatäide**: pane sinna oma väärtus, ilma sulgudeta.
  `<recording>.mp4` tähendab failinime nagu `match1.mp4`.
- Tekst ruutsulgudes, nagu `[--fps 5]`, on **valikuline**.
- Tee tühikutega vajab jutumärke: `"C:\My Videos\match1.mp4"`.
- Read, mis algavad `#`-iga, on kommentaarid. Neid ei kirjuta.

## 5. Hangi tööriist ja selle paketid {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` teeb tööriista pakettidele eraldi kausta, et need ei seguneks
sinu arvuti teiste asjadega. Iga järgnev käsk algab siis `.venv\Scripts\python`-ga.

**Peaksid nägema**, et viimane rida ütleb `Successfully installed ...`. Kontrolli, et tööriist töötab:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Peaksid nägema** käskude loendit, mis algab `usage: heat3d_capture`.

![Käskude loend, mida --help prindib](../assets/img/cli-help.svg)

Kausta saab ka *aktiveerida* üks kord ja siis kirjutada ainult `python`:

| Terminal | Aktiveeri | Seejärel |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Kui PowerShell ütleb *running scripts is disabled*, käivita üks kord
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, või jäta aktiveerimine vahele.

## 6. Lisaprogrammid, mida mõned käsud vajavad {#extra-programs-some-commands-need}

| Käsk | Vajab | Paigaldus |
|---|---|---|
| `hud` | **ffmpeg** ja **ffprobe** (videofailide lugemiseks) | `winget install Gyan.FFmpeg`, seejärel ava uus terminal. Kontrolli käsuga `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, paigaldatud enne teisi pakette | käsk lehelt [pytorch.org](https://pytorch.org/get-started/locally/) sinu GPU jaoks |

## Kui midagi läheb valesti {#when-something-goes-wrong}

| Näed | See tähendab | Tee nii |
|---|---|---|
| `'python' is not recognized` | Python pole PATH-is | Paigalda Python uuesti PATH-linnukesega, seejärel ava uus terminal. |
| `No module named heat3d_capture` | terminal ei ole tööriista kaustas | `cd` kausta `3DHeat-GameCapture`. |
| `No module named numpy` (või mõni muu pakett) | paketid pole paigaldatud või kasutasid teist Pythonit | Käivita rida `pip install -r requirements.txt` uuesti, koos `.venv\Scripts\python`-ga. |
| `'.venv' is not recognized` | kirjutasid cmd-s `/` | Kasuta kaldkriipse õigesti: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg puudub | Vaata samm 6 ja ava siis uus terminal. |

Järgmine: [Avaleht](index.md) annab esimese näite iga töö kohta.
