---
title: "Ier Dir ufänkt"
nav_order: 1.5
lang: lb
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Ier Dir ufänkt {#before-you-start}

Nei op der Kommandozeil? Dës Säit bréngt Iech vun Null bis bei e éischte funktionéierende Kommando. Et dauert
ongeféier zéng Minutten, eemol.

## 1. Python installéieren {#install-python}

GameCapture ass e Python-Programm. Dir braucht **Python 3.10 oder méi nei**.

1. Gitt op [python.org/downloads](https://www.python.org/downloads/) a luet dat neist
   Python fir Windows erof.
2. Startt den Installer. Um éischte Bildschierm **"Add python.exe to PATH" ukräizen**. Ouni d'Kräiz
   fënnt d'Terminal Python net.
3. Klickt op *Install Now*.

Oder, an engem Terminal: `winget install Python.Python.3.12`.

## 2. Git installéieren {#install-git}

Git lued d'Tool erof. Hollt et vu [git-scm.com](https://git-scm.com/download/win), oder féiert
`winget install Git.Git` aus. Wann Dir Git net wëllt, benotzt *Code > Download ZIP* op der
[GitHub-Säit](https://github.com/Holdi601/3DHeat-GameCapture) an entzippt et.

## 3. E Terminal an engem Dossier opmaachen {#open-a-terminal-in-a-folder}

E Terminal ass e Fënster, wou Dir Kommandoe tippt. Dës Säite benotzen **PowerShell**, dat all
Windows-PC huet.

- Mécht den Dossier am File Explorer op, klickt an d'Adressleist, tippt `powershell` an dréckt Enter.
  PowerShell geet **an deem Dossier** op.
- Oder mécht PowerShell vum Startmenü op a gitt mat `cd` an en Dossier:

```powershell
cd "C:\Games\Tools"
```

## 4. D'Kommandoe op dëse Säite liesen {#read-the-commands-on-these-pages}

- Tippt all Kommandozeil an dréckt Enter.
- Text an spëtze Klammeren ass e **Platzhalter**: setzt Äre Wäert dohinner, ouni d'Klammeren.
  `<recording>.mp4` heescht en Dateinumm wéi `match1.mp4`.
- Text an eckege Klammeren, wéi `[--fps 5]`, ass **optional**.
- E Wee mat Espacen brauch Ureechnungszeechen: `"C:\My Videos\match1.mp4"`.
- Zeilen, déi mat `#` ufänken, si Kommentarer. Dir tippt se net.

## 5. D'Tool a seng Packagen kréien {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` mécht en privaten Dossier fir d'Packagen vum Tool, sou datt se sech net mat
iergendengem anere vun Ärem PC vermëschen. All Kommando fänkt dann mat `.venv\Scripts\python` un.

**Dir sollt gesinn**, datt déi lescht Zeil `Successfully installed ...` seet. Préift, ob d'Tool funktionéiert:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Dir sollt** eng Lëscht vu Kommandoen gesinn, déi mat `usage: heat3d_capture` ufänkt.

![D'Lëscht vun de Kommandoen, déi --help ausgëtt](../assets/img/cli-help.svg)

Dir kënnt den Dossier och eemol *aktivéieren* an dann just `python` tippen:

| Terminal | Aktivéieren | Dann |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Wann PowerShell *running scripts is disabled* seet, féiert eemol
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` aus, oder spuert Iech d'Aktivéieren.

## 6. Extra Programmer, déi e puer Kommandoe brauchen {#extra-programs-some-commands-need}

| Kommando | Brauch | Installéieren |
|---|---|---|
| `hud` | **ffmpeg** an **ffprobe** (liesen Videodateien) | `winget install Gyan.FFmpeg`, dann en neit Terminal opmaachen. Mat `ffmpeg -version` préiwen. |
| `reconstruct`, `locate` | **PyTorch**, virun deenen aneren Packagen installéiert | de Kommando vun [pytorch.org](https://pytorch.org/get-started/locally/) fir Är GPU |

## Wann eppes falsch geet {#when-something-goes-wrong}

| Dir gesitt | Et heescht | Maacht dat |
|---|---|---|
| `'python' is not recognized` | Python ass net um PATH | Python nach eemol mat der PATH-Kräiz installéieren, dann en neit Terminal opmaachen. |
| `No module named heat3d_capture` | d'Terminal ass net am Dossier vum Tool | Mat `cd` an den `3DHeat-GameCapture`-Dossier goen. |
| `No module named numpy` (oder en anere Package) | d'Packagen sinn net installéiert, oder Dir hutt en anert Python benotzt | D'`pip install -r requirements.txt`-Zeil nach eemol ausféieren, mat `.venv\Scripts\python`. |
| `'.venv' is not recognized` | Dir hutt `/` an cmd getippt | Backslashes benotzen: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg feelt | Kuckt Schrëtt 6, dann en neit Terminal opmaachen. |

Als Nächst: D'[Startsäit](index.md) huet e éischt Beispill fir all Aarbecht.
