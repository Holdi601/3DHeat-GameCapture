---
title: "Ennen aloittamista"
nav_order: 1.5
lang: fi
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Ennen aloittamista {#before-you-start}

Uusi komentorivin kanssa? Tämä sivu vie sinut nollasta ensimmäiseen toimivaan komentoon.
Se vie noin kymmenen minuuttia, kerran.

## 1. Asenna Python {#install-python}

GameCapture on Python-ohjelma. Tarvitset **Python 3.10:n tai uudemman**.

1. Mene osoitteeseen [python.org/downloads](https://www.python.org/downloads/) ja lataa uusin
   Python Windowsille.
2. Suorita asennusohjelma. Ensimmäisellä näytöllä **rastita "Add python.exe to PATH"**. Ilman rastia
   pääte ei löydä Pythonia.
3. Napsauta *Install Now*.

Tai päätteessä: `winget install Python.Python.3.12`.

## 2. Asenna Git {#install-git}

Git lataa työkalun. Hae se osoitteesta [git-scm.com](https://git-scm.com/download/win), tai suorita
`winget install Git.Git`. Jos et halua gitiä, käytä *Code > Download ZIP* -toimintoa
[GitHub-sivulla](https://github.com/Holdi601/3DHeat-GameCapture) ja pura zip.

## 3. Avaa pääte kansiossa {#open-a-terminal-in-a-folder}

Pääte on ikkuna, johon kirjoitat komentoja. Nämä sivut käyttävät **PowerShellia**, jonka jokaisella
Windows-koneella on.

- Avaa kansio File Explorerissa, napsauta osoitepalkkiin, kirjoita `powershell` ja paina Enter.
  PowerShell aukeaa **siihen kansioon**.
- Tai avaa PowerShell Käynnistä-valikosta ja siirry kansioon komennolla `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Lue sivujen komennot {#read-the-commands-on-these-pages}

- Kirjoita jokainen komentorivi ja paina Enter.
- Kulmasulkeissa oleva teksti on **paikanpitäjä**: kirjoita oma arvosi sen tilalle ilman sulkeita.
  `<recording>.mp4` tarkoittaa tiedostonimeä, kuten `match1.mp4`.
- Hakasulkeissa oleva teksti, kuten `[--fps 5]`, on **valinnainen**.
- Välilyöntejä sisältävä polku tarvitsee lainausmerkit: `"C:\My Videos\match1.mp4"`.
- Rivit, jotka alkavat `#`-merkillä, ovat kommentteja. Et kirjoita niitä.

## 5. Hae työkalu ja sen paketit {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` tekee yksityisen kansion työkalun paketeille, jotta ne eivät sekoitu muuhun
koneellasi. Jokainen komento alkaa sen jälkeen `.venv\Scripts\python`.

**Pitäisi näkyä**, että viimeinen rivi sanoo `Successfully installed ...`. Tarkista, että työkalu toimii:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Pitäisi näkyä** komentojen luettelo, joka alkaa `usage: heat3d_capture`.

![Komentoluettelo, jonka --help tulostaa](../assets/img/cli-help.svg)

Voit myös *aktivoida* kansion kerran ja kirjoittaa sen jälkeen pelkän `python`:

| Pääte | Aktivoi | Sitten |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Jos PowerShell sanoo *running scripts is disabled*, suorita kerran
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, tai ohita aktivointi.

## 6. Muut ohjelmat, joita jotkin komennot tarvitsevat {#extra-programs-some-commands-need}

| Komento | Tarvitsee | Asenna |
|---|---|---|
| `hud` | **ffmpeg** ja **ffprobe** (videotiedostojen lukemiseen) | `winget install Gyan.FFmpeg`, sitten avaa uusi pääte. Tarkista komennolla `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, asennettuna ennen muita paketteja | komento osoitteesta [pytorch.org](https://pytorch.org/get-started/locally/) omalle GPU:lle |

## Kun jokin menee pieleen {#when-something-goes-wrong}

| Näet | Se tarkoittaa | Tee näin |
|---|---|---|
| `'python' is not recognized` | Python ei ole PATH:ssa | Asenna Python uudelleen PATH-rastilla, avaa sitten uusi pääte. |
| `No module named heat3d_capture` | pääte ei ole työkalun kansiossa | `cd` kansioon `3DHeat-GameCapture`. |
| `No module named numpy` (tai muu paketti) | paketteja ei ole asennettu, tai käytit toista Pythonia | Suorita rivi `pip install -r requirements.txt` uudelleen, komennolla `.venv\Scripts\python`. |
| `'.venv' is not recognized` | kirjoitit `/` cmd-ikkunassa | Käytä kenoviivoja: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg puuttuu | Katso vaihe 6, avaa sitten uusi pääte. |

Seuraavaksi: [Etusivu](index.md) näyttää ensimmäisen esimerkin jokaisesta tehtävästä.
