---
title: "Áður en þú byrjar"
nav_order: 1.5
lang: is
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Áður en þú byrjar {#before-you-start}

Hefurðu aldrei notað skipanalínu? Þessi síða kemur þér frá engu að fyrstu virku skipuninni. Það tekur
um tíu mínútur, einu sinni.

## 1. Settu upp Python {#install-python}

GameCapture er Python-forrit. Þú þarft **Python 3.10 eða nýrra**.

1. Farðu á [python.org/downloads](https://www.python.org/downloads/) og sæktu nýjasta
   Python fyrir Windows.
2. Keyrðu uppsetningarforritið. Á fyrsta skjánum skaltu **haka við "Add python.exe to PATH"**. Án þess
   finnur skipanalínan ekki Python.
3. Smelltu á *Install Now*.

Eða, í skipanalínu: `winget install Python.Python.3.12`.

## 2. Settu upp Git {#install-git}

Git sækir verkfærið. Náðu í það á [git-scm.com](https://git-scm.com/download/win), eða keyrðu
`winget install Git.Git`. Ef þú vilt ekki Git, notaðu *Code > Download ZIP* á
[GitHub-síðunni](https://github.com/Holdi601/3DHeat-GameCapture) og pakkaðu skránni upp.

## 3. Opnaðu skipanalínu í möppu {#open-a-terminal-in-a-folder}

Skipanalína er gluggi þar sem þú skrifar skipanir. Þessar síður nota **PowerShell**, sem hver
Windows-tölva hefur.

- Opnaðu möppuna í File Explorer, smelltu í vistfangastikuna, skrifaðu `powershell` og ýttu á Enter.
  PowerShell opnast **í þeirri möppu**.
- Eða opnaðu PowerShell úr Start-valmyndinni og farðu í möppu með `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Lestu skipanirnar á þessum síðum {#read-the-commands-on-these-pages}

- Skrifaðu hverja skipanalínu og ýttu á Enter.
- Texti í oddklofum er **staðgengill**: settu þitt eigið gildi þar, án oddklofanna.
  `<recording>.mp4` þýðir skráarnafn eins og `match1.mp4`.
- Texti í hornklofum, eins og `[--fps 5]`, er **valkvæður**.
- Slóð með bilum þarf gæsalappir: `"C:\My Videos\match1.mp4"`.
- Línur sem byrja á `#` eru athugasemdir. Þú skrifar þær ekki.

## 5. Náðu í verkfærið og pakkana þess {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` býr til einkamöppu fyrir pakka verkfærisins, svo þeir blandist ekki við
neitt annað á tölvunni þinni. Hver skipun byrjar þá á `.venv\Scripts\python`.

**Þú ættir að sjá** síðustu línuna segja `Successfully installed ...`. Athugaðu að verkfærið virki:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Þú ættir að sjá** lista yfir skipanir, sem byrjar á `usage: heat3d_capture`.

![Skipanalistinn sem --help prentar](../assets/img/cli-help.svg)

Þú getur líka *virkjað* möppuna einu sinni og skrifað síðan bara `python`:

| Skipanalína | Virkja | Síðan |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ef PowerShell segir *running scripts is disabled*, keyrðu
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` einu sinni, eða slepptu því að virkja.

## 6. Aukaforrit sem sumar skipanir þurfa {#extra-programs-some-commands-need}

| Skipun | Þarf | Uppsetning |
|---|---|---|
| `hud` | **ffmpeg** og **ffprobe** (lesa myndskrár) | `winget install Gyan.FFmpeg`, opnaðu síðan nýja skipanalínu. Athugaðu með `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, sett upp á undan hinum pökkunum | skipunin frá [pytorch.org](https://pytorch.org/get-started/locally/) fyrir skjákortið þitt |

## Þegar eitthvað fer úrskeiðis {#when-something-goes-wrong}

| Þú sérð | Það þýðir | Gerðu þetta |
|---|---|---|
| `'python' is not recognized` | Python er ekki á PATH | Settu Python upp aftur með PATH-haki, opnaðu síðan nýja skipanalínu. |
| `No module named heat3d_capture` | skipanalínan er ekki í möppu verkfærisins | Farðu með `cd` í `3DHeat-GameCapture` möppuna. |
| `No module named numpy` (eða annar pakki) | pakkarnir eru ekki uppsettir, eða þú notaðir annað Python | Keyrðu `pip install -r requirements.txt` línuna aftur, með `.venv\Scripts\python`. |
| `'.venv' is not recognized` | þú skrifaðir `/` í cmd | Notaðu bakstrik: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg vantar | Sjá skref 6, opnaðu síðan nýja skipanalínu. |

Næst: [Heim](index.md) hefur fyrsta dæmi fyrir hvert verkefni.
