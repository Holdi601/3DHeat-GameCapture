---
title: Qabel ma tibda
nav_order: 1.5
lang: "mt"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Qabel ma tibda {#before-you-start}

Ġdid mal-linja tal-kmandi? Din il-paġna tieħdok minn xejn sal-ewwel kmand li jaħdem. Tieħu
madwar għaxar minuti, darba biss.

## 1. Installa Python {#install-python}

GameCapture huwa programm ta' Python. Teħtieġ **Python 3.10 jew aktar ġdid**.

1. Mur fuq [python.org/downloads](https://www.python.org/downloads/) u niżżel l-aħħar
   Python għal Windows.
2. Ħaddem l-installer. Fl-ewwel skrin, **immarka "Add python.exe to PATH"**. Mingħajr il-marka,
   it-terminal ma jsibx Python.
3. Ikklikkja *Install Now*.

Jew, f'terminal: `winget install Python.Python.3.12`.

## 2. Installa Git {#install-git}

Git iniżżel l-għodda. Ġibu minn [git-scm.com](https://git-scm.com/download/win), jew ħaddem
`winget install Git.Git`. Jekk ma tridx Git, uża *Code > Download ZIP* fuq il-
[paġna ta' GitHub](https://github.com/Holdi601/3DHeat-GameCapture) u ħoll iż-zip.

## 3. Iftaħ terminal f'folder {#open-a-terminal-in-a-folder}

Terminal huwa tieqa fejn tittajpja l-kmandi. Dawn il-paġni jużaw **PowerShell**, li kull
PC b'Windows għandu.

- Iftaħ il-folder fil-File Explorer, ikklikkja l-bar tal-indirizz, ittajpja `powershell` u agħfas Enter.
  PowerShell jiftaħ **f'dak il-folder**.
- Jew iftaħ PowerShell mill-menu Start u mur f'folder b'`cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Aqra l-kmandi f'dawn il-paġni {#read-the-commands-on-these-pages}

- Ittajpja kull linja ta' kmand u agħfas Enter.
- Test bejn parentesi angolari huwa **placeholder**: poġġi l-valur tiegħek hemm, mingħajr il-parentesi.
  `<recording>.mp4` ifisser isem ta' fajl bħal `match1.mp4`.
- Test bejn parentesi kwadri, bħal `[--fps 5]`, huwa **fakultattiv**.
- Triq b'spazji teħtieġ virgoletti: `"C:\My Videos\match1.mp4"`.
- Linji li jibdew b'`#` huma kummenti. Ma tittajpjahomx.

## 5. Ġib l-għodda u l-pakketti tagħha {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` jagħmel folder privat għall-pakketti tal-għodda, biex ma jitħalltux ma'
xejn ieħor fuq il-PC tiegħek. Kull kmand imbagħad jibda b'`.venv\Scripts\python`.

**Għandek tara** l-aħħar linja tgħid `Successfully installed ...`. Iċċekkja li l-għodda taħdem:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Għandek tara** lista ta' kmandi, li tibda b'`usage: heat3d_capture`.

![Il-lista ta' kmandi li jistampa --help](../assets/img/cli-help.svg)

Tista' wkoll *tattiva* l-folder darba, u mbagħad tittajpja `python` biss:

| Terminal | Attiva | Imbagħad |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Jekk PowerShell jgħid *running scripts is disabled*, ħaddem
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` darba, jew aqbeż l-attivazzjoni.

## 6. Programmi żejda li jeħtieġu xi kmandi {#extra-programs-some-commands-need}

| Kmand | Jeħtieġ | Installa |
|---|---|---|
| `hud` | **ffmpeg** u **ffprobe** (jaqraw fajls tal-vidjo) | `winget install Gyan.FFmpeg`, imbagħad iftaħ terminal ġdid. Iċċekkja b'`ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installat qabel il-pakketti l-oħra | il-kmand minn [pytorch.org](https://pytorch.org/get-started/locally/) għall-GPU tiegħek |

## Meta xi ħaġa tmur ħażin {#when-something-goes-wrong}

| Tara | Tfisser | Agħmel dan |
|---|---|---|
| `'python' is not recognized` | Python mhuwiex fuq PATH | Erġa' installa Python bil-marka tal-PATH, imbagħad iftaħ terminal ġdid. |
| `No module named heat3d_capture` | it-terminal mhuwiex fil-folder tal-għodda | Mur b'`cd` fil-folder `3DHeat-GameCapture`. |
| `No module named numpy` (jew pakkett ieħor) | il-pakketti mhumiex installati, jew użajt Python differenti | Erġa' ħaddem il-linja `pip install -r requirements.txt`, b'`.venv\Scripts\python`. |
| `'.venv' is not recognized` | ittajpjajt `/` f'cmd | Uża backslashes: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nieqes | Ara pass 6, imbagħad iftaħ terminal ġdid. |

Li jmiss: [Dar](index.md) għandha l-ewwel eżempju għal kull xogħol.
