---
title: "Înainte de a începe"
nav_order: 1.5
lang: "ro"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Înainte de a începe {#before-you-start}

Nu ați mai lucrat în linia de comandă? Această pagină vă duce de la zero la prima comandă care
funcționează. Durează vreo zece minute, o singură dată.

## 1. Instalați Python {#install-python}

GameCapture este un program Python. Aveți nevoie de **Python 3.10 sau mai nou**.

1. Mergeți la [python.org/downloads](https://www.python.org/downloads/) și descărcați cel mai nou
   Python pentru Windows.
2. Rulați programul de instalare. Pe primul ecran, **bifați „Add python.exe to PATH”**. Fără această
   bifă, terminalul nu va găsi Python.
3. Apăsați *Install Now*.

Sau, într-un terminal: `winget install Python.Python.3.12`.

## 2. Instalați Git {#install-git}

Git descarcă instrumentul. Luați-l de la [git-scm.com](https://git-scm.com/download/win), sau rulați
`winget install Git.Git`. Dacă nu vreți Git, folosiți *Code > Download ZIP* pe
[pagina GitHub](https://github.com/Holdi601/3DHeat-GameCapture) și dezarhivați-l.

## 3. Deschideți un terminal într-un dosar {#open-a-terminal-in-a-folder}

Un terminal este o fereastră în care scrieți comenzi. Aceste pagini folosesc **PowerShell**, pe care
îl are orice calculator Windows.

- Deschideți dosarul în File Explorer, faceți clic în bara de adrese, scrieți `powershell` și apăsați
  Enter. PowerShell se deschide **în acel dosar**.
- Sau deschideți PowerShell din meniul Start și mergeți într-un dosar cu `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Citiți comenzile din aceste pagini {#read-the-commands-on-these-pages}

- Scrieți fiecare rând de comandă și apăsați Enter.
- Textul între paranteze unghiulare este un **loc rezervat**: scrieți acolo propria valoare, fără
  paranteze. `<recording>.mp4` înseamnă un nume de fișier, cum ar fi `match1.mp4`.
- Textul între paranteze pătrate, cum ar fi `[--fps 5]`, este **opțional**.
- O cale cu spații are nevoie de ghilimele: `"C:\My Videos\match1.mp4"`.
- Rândurile care încep cu `#` sunt comentarii. Nu le scrieți.

## 5. Obțineți instrumentul și pachetele sale {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` face un dosar privat pentru pachetele instrumentului, ca ele să nu se
amestece cu alte lucruri de pe calculator. Fiecare comandă începe apoi cu `.venv\Scripts\python`.

**Ar trebui să vedeți** ca ultimul rând să spună `Successfully installed ...`. Verificați că instrumentul
funcționează:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Ar trebui să vedeți** o listă de comenzi, care începe cu `usage: heat3d_capture`.

![Lista de comenzi pe care o afișează --help](../assets/img/cli-help.svg)

Puteți și *activa* dosarul o dată, și apoi scrieți doar `python`:

| Terminal | Activare | Apoi |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Dacă PowerShell spune că *rularea scripturilor este dezactivată*, rulați o dată
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, sau săriți peste activare.

## 6. Programe suplimentare de care au nevoie unele comenzi {#extra-programs-some-commands-need}

| Comandă | Are nevoie de | Instalare |
|---|---|---|
| `hud` | **ffmpeg** și **ffprobe** (citesc fișierele video) | `winget install Gyan.FFmpeg`, apoi deschideți un terminal nou. Verificați cu `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instalat înaintea celorlalte pachete | comanda de pe [pytorch.org](https://pytorch.org/get-started/locally/) pentru placa dumneavoastră grafică |

## Când apare o problemă {#when-something-goes-wrong}

| Ce vedeți | Ce înseamnă | Ce să faceți |
|---|---|---|
| `'python' is not recognized` | Python nu este în PATH | Reinstalați Python cu bifa PATH, apoi deschideți un terminal nou. |
| `No module named heat3d_capture` | terminalul nu este în dosarul instrumentului | `cd` în dosarul `3DHeat-GameCapture`. |
| `No module named numpy` (sau alt pachet) | pachetele nu sunt instalate, sau ați folosit alt Python | Rulați din nou linia `pip install -r requirements.txt`, cu `.venv\Scripts\python`. |
| `'.venv' is not recognized` | ați scris `/` în cmd | Folosiți bare inverse: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg lipsește | Vedeți pasul 6, apoi deschideți un terminal nou. |

Mai departe: [Acasă](index.md) are un prim exemplu pentru fiecare sarcină.
