---
title: "Para se të fillosh"
nav_order: 1.5
lang: sq
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Para se të fillosh {#before-you-start}

Je i ri me vijën e komandës? Kjo faqe të çon nga zero te një komandë e parë që funksionon. Duhen
rreth dhjetë minuta, vetëm një herë.

## 1. Instalo Python {#install-python}

GameCapture është një program Python. Të duhet **Python 3.10 ose më i ri**.

1. Shko te [python.org/downloads](https://www.python.org/downloads/) dhe shkarko
   Python-in më të ri për Windows.
2. Nis instaluesin. Në ekranin e parë, **zgjidh "Add python.exe to PATH"**. Pa këtë shenjë,
   terminali nuk do ta gjejë Python.
3. Kliko *Install Now*.

Ose, në një terminal: `winget install Python.Python.3.12`.

## 2. Instalo Git {#install-git}

Git e shkarkon mjetin. Merre nga [git-scm.com](https://git-scm.com/download/win), ose ekzekuto
`winget install Git.Git`. Nëse nuk do Git, përdor *Code > Download ZIP* te
[faqja e GitHub](https://github.com/Holdi601/3DHeat-GameCapture) dhe çzipoje.

## 3. Hap një terminal në një dosje {#open-a-terminal-in-a-folder}

Terminali është një dritare ku shkruan komanda. Këto faqe përdorin **PowerShell**, që e ka çdo
PC me Windows.

- Hap dosjen në File Explorer, kliko te shiriti i adresës, shkruaj `powershell` dhe shtyp Enter.
  PowerShell hapet **në atë dosje**.
- Ose hap PowerShell nga menuja Start dhe shko te një dosje me `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Lexo komandat në këto faqe {#read-the-commands-on-these-pages}

- Shkruaj çdo rresht komande dhe shtyp Enter.
- Teksti në kllapa këndore është një **vendmbajtës**: vendos vlerën tënde aty, pa kllapat.
  `<recording>.mp4` do të thotë një emër skedari si `match1.mp4`.
- Teksti në kllapa katrore, si `[--fps 5]`, është **opsional**.
- Një shteg me hapësira ka nevojë për thonjëza: `"C:\My Videos\match1.mp4"`.
- Rreshtat që nisin me `#` janë komente. Nuk i shkruan.

## 5. Merr mjetin dhe paketat e tij {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` krijon një dosje private për paketat e mjetit, që të mos përzihen me
asgjë tjetër në PC-në tënde. Pastaj çdo komandë nis me `.venv\Scripts\python`.

**Duhet të shohësh** që rreshti i fundit thotë `Successfully installed ...`. Kontrollo që mjeti funksionon:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Duhet të shohësh** një listë komandash, që nis me `usage: heat3d_capture`.

![Lista e komandave që shtyp --help](../assets/img/cli-help.svg)

Mund ta *aktivizosh* edhe dosjen një herë, dhe pastaj të shkruash vetëm `python`:

| Terminali | Aktivizimi | Pastaj |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Nëse PowerShell thotë *running scripts is disabled*, ekzekuto
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` një herë, ose anashkalo aktivizimin.

## 6. Programe shtesë që i duhen disa komandave {#extra-programs-some-commands-need}

| Komanda | Ka nevojë për | Instalimi |
|---|---|---|
| `hud` | **ffmpeg** dhe **ffprobe** (lexojnë skedarë videoje) | `winget install Gyan.FFmpeg`, pastaj hap një terminal të ri. Kontrollo me `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, i instaluar para paketave të tjera | komanda nga [pytorch.org](https://pytorch.org/get-started/locally/) për GPU-në tënde |

## Kur diçka shkon keq {#when-something-goes-wrong}

| Çfarë sheh | Çfarë do të thotë | Çfarë të bësh |
|---|---|---|
| `'python' is not recognized` | Python nuk është në PATH | Instalo përsëri Python me shenjën PATH, pastaj hap një terminal të ri. |
| `No module named heat3d_capture` | terminali nuk është në dosjen e mjetit | Bëj `cd` në dosjen `3DHeat-GameCapture`. |
| `No module named numpy` (ose paketë tjetër) | paketat nuk janë instaluar, ose ke përdorur një Python tjetër | Ekzekuto përsëri rreshtin `pip install -r requirements.txt`, me `.venv\Scripts\python`. |
| `'.venv' is not recognized` | shkrove `/` në cmd | Përdor vijat e pjerrëta mbrapsht: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg mungon | Shih hapin 6, pastaj hap një terminal të ri. |

Më pas: [Kryefaqja](index.md) ka një shembull të parë për çdo punë.
