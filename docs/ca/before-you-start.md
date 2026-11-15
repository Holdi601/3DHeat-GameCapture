---
title: Abans de començar
nav_order: 1.5
lang: ca
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Abans de començar {#before-you-start}

Si és nou amb la línia d'ordres, aquesta pàgina el porta de no tenir res a una primera
ordre que funciona. Triga uns deu minuts, una sola vegada.

## 1. Instal·lar Python {#install-python}

GameCapture és un programa de Python. Necessita **Python 3.10 o posterior**.

1. Vagi a [python.org/downloads](https://www.python.org/downloads/) i descarregui la versió
   més nova de Python per a Windows.
2. Executi l'instal·lador. A la primera pantalla, **marqui «Add python.exe to PATH»**. Sense aquesta
   marca, la terminal no trobarà Python.
3. Faci clic a *Install Now*.

O, en una terminal: `winget install Python.Python.3.12`.

## 2. Instal·lar Git {#install-git}

Git descarrega l'eina. Obtingui'l a [git-scm.com](https://git-scm.com/download/win), o executi
`winget install Git.Git`. Si no vol Git, faci servir *Code > Download ZIP* a la
[pàgina de GitHub](https://github.com/Holdi601/3DHeat-GameCapture) i descomprimeixi-la.

## 3. Obrir una terminal en una carpeta {#open-a-terminal-in-a-folder}

Una terminal és una finestra on escriu ordres. Aquestes pàgines fan servir **PowerShell**, que té
qualsevol PC amb Windows.

- Obri la carpeta a l'Explorador de fitxers, faci clic a la barra d'adreces, escrigui `powershell` i premi
  Intro. PowerShell s'obre **en aquesta carpeta**.
- O obri PowerShell des del menú Inici i es mou a una carpeta amb `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Llegir les ordres d'aquestes pàgines {#read-the-commands-on-these-pages}

- Escrigui cada línia d'ordre i premi Intro.
- El text entre angles és un **marcador de posició**: posi-hi el seu propi valor, sense els angles.
  `<recording>.mp4` vol dir un nom de fitxer com `match1.mp4`.
- El text entre claudàtors, com `[--fps 5]`, és **opcional**.
- Una ruta amb espais necessita cometes: `"C:\My Videos\match1.mp4"`.
- Les línies que comencen amb `#` són comentaris. No les escrigui.

## 5. Obtenir l'eina i els seus paquets {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` crea una carpeta privada per als paquets de l'eina, perquè no es barregin amb
res més del vostre PC. Després, cada ordre comença amb `.venv\Scripts\python`.

**Hauria de veure** que l'última línia diu `Successfully installed ...`. Comprovi que l'eina funciona:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Hauria de veure** una llista d'ordres, que comença amb `usage: heat3d_capture`.

![La llista d'ordres que imprimeix --help](../assets/img/cli-help.svg)

També pot *activar* la carpeta una vegada, i després escriure només `python`:

| Terminal | Activar | Després |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Si PowerShell diu *running scripts is disabled*, executi una vegada
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o deixi d'activar.

## 6. Programes extra que necessiten algunes ordres {#extra-programs-some-commands-need}

| Ordre | Necessita | Instal·lació |
|---|---|---|
| `hud` | **ffmpeg** i **ffprobe** (per llegir fitxers de vídeo) | `winget install Gyan.FFmpeg`, i després obri una terminal nova. Comprovi amb `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instal·lat abans que els altres paquets | l'ordre de [pytorch.org](https://pytorch.org/get-started/locally/) per a la seva GPU |

## Quan alguna cosa va malament {#when-something-goes-wrong}

| Veu | Què vol dir | Què fer |
|---|---|---|
| `'python' is not recognized` | Python no és al PATH | Torni a instal·lar Python amb la marca del PATH, i després obri una terminal nova. |
| `No module named heat3d_capture` | la terminal no és a la carpeta de l'eina | Feu `cd` a la carpeta `3DHeat-GameCapture`. |
| `No module named numpy` (o un altre paquet) | els paquets no estan instal·lats, o ha fet servir un altre Python | Executi de nou la línia `pip install -r requirements.txt`, amb `.venv\Scripts\python`. |
| `'.venv' is not recognized` | ha escrit `/` a cmd | Faci servir barres inverses: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | falta ffmpeg | Vegi el pas 6, i després obri una terminal nova. |

Següent: [Inici](index.md) té un primer exemple per a cada tasca.
