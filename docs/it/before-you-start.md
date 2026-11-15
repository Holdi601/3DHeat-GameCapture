---
title: Prima di iniziare
nav_order: 1.5
lang: it
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Prima di iniziare {#before-you-start}

Non hai mai usato la riga di comando? Questa pagina ti porta dal nulla al primo comando funzionante.
Richiede circa dieci minuti, una volta sola.

## 1. Installa Python {#install-python}

GameCapture è un programma Python. Ti serve **Python 3.10 o successivo**.

1. Vai su [python.org/downloads](https://www.python.org/downloads/) e scarica la versione più recente
   di Python per Windows.
2. Esegui il programma di installazione. Nella prima schermata, **spunta "Add python.exe to PATH"**.
   Senza questa spunta, il terminale non troverà Python.
3. Clicca su *Install Now*.

Oppure, in un terminale: `winget install Python.Python.3.12`.

## 2. Installa Git {#install-git}

Git scarica lo strumento. Prendilo da [git-scm.com](https://git-scm.com/download/win), oppure esegui
`winget install Git.Git`. Se non vuoi Git, usa *Code > Download ZIP* sulla
[pagina GitHub](https://github.com/Holdi601/3DHeat-GameCapture) e decomprimi il file.

## 3. Apri un terminale in una cartella {#open-a-terminal-in-a-folder}

Un terminale è una finestra in cui digiti i comandi. Queste pagine usano **PowerShell**, che ogni PC
Windows ha.

- Apri la cartella in Esplora file, clicca nella barra degli indirizzi, digita `powershell` e premi
  Invio. PowerShell si apre **in quella cartella**.
- Oppure apri PowerShell dal menu Start e spostati in una cartella con `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Leggi i comandi di queste pagine {#read-the-commands-on-these-pages}

- Scrivi ogni riga di comando e premi Invio.
- Il testo tra parentesi angolari è un **segnaposto**: scrivi lì il tuo valore, senza le parentesi.
  `<recording>.mp4` significa un nome di file come `match1.mp4`.
- Il testo tra parentesi quadre, come `[--fps 5]`, è **facoltativo**.
- Un percorso con spazi richiede le virgolette: `"C:\My Videos\match1.mp4"`.
- Le righe che iniziano con `#` sono commenti. Non le digiti.

## 5. Procurati lo strumento e i suoi pacchetti {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` crea una cartella privata per i pacchetti dello strumento, così non si mescolano
con nient'altro sul tuo PC. Ogni comando poi inizia con `.venv\Scripts\python`.

**Dovresti vedere** che l'ultima riga dice `Successfully installed ...`. Verifica che lo strumento
funzioni:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Dovresti vedere** un elenco di comandi, che inizia con `usage: heat3d_capture`.

![L'elenco dei comandi che stampa --help](../assets/img/cli-help.svg)

Puoi anche *attivare* la cartella una volta, e poi digitare solo `python`:

| Terminale | Attivazione | Poi |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Se PowerShell dice *running scripts is disabled*, esegui una volta
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, oppure salta l'attivazione.

## 6. Programmi extra che alcuni comandi richiedono {#extra-programs-some-commands-need}

| Comando | Richiede | Installazione |
|---|---|---|
| `hud` | **ffmpeg** e **ffprobe** (per leggere i file video) | `winget install Gyan.FFmpeg`, poi apri un nuovo terminale. Verifica con `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installato prima degli altri pacchetti | il comando da [pytorch.org](https://pytorch.org/get-started/locally/) per la tua GPU |

## Quando qualcosa non va {#when-something-goes-wrong}

| Vedi | Significa | Fai questo |
|---|---|---|
| `'python' is not recognized` | Python non è nel PATH | Reinstalla Python con la spunta del PATH, poi apri un nuovo terminale. |
| `No module named heat3d_capture` | il terminale non è nella cartella dello strumento | Fai `cd` nella cartella `3DHeat-GameCapture`. |
| `No module named numpy` (o un altro pacchetto) | i pacchetti non sono installati, oppure hai usato un altro Python | Esegui di nuovo la riga `pip install -r requirements.txt` con `.venv\Scripts\python`. |
| `'.venv' is not recognized` | hai scritto `/` in cmd | Usa le barre rovesciate: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg manca | Vedi il passo 6, poi apri un nuovo terminale. |

Avanti: [Home](index.md) ha un primo esempio per ciascun compito.
