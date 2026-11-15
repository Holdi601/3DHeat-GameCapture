---
title: Pirms sākat
nav_order: 1.5
lang: lv
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Pirms sākat {#before-you-start}

Vai nekad neesi strādājis ar komandrindu? Šī lapa palīdzēs tev no nulles nonākt līdz pirmajai strādājošajai komandai. Tas aizņem apmēram desmit minūtes, vienu reizi.

## 1. Uzstādi Python {#install-python}

GameCapture ir Python programma. Vajag **Python 3.10 vai jaunāku versiju**.

1. Ej uz [python.org/downloads](https://www.python.org/downloads/) un lejupielādē jaunāko
   Python Windows versijai.
2. Palaid instalētāju. Pirmajā ekrānā **atzīmē "Add python.exe to PATH"**. Bez šīs atzīmes
   terminālis neatradīs Python.
3. Noklikšķini *Install Now*.

Vai terminālī: `winget install Python.Python.3.12`.

## 2. Uzstādi Git {#install-git}

Git lejupielādē rīku. Iegūsti to no [git-scm.com](https://git-scm.com/download/win) vai palaid
`winget install Git.Git`. Ja Git nevēlies, [GitHub lapā](https://github.com/Holdi601/3DHeat-GameCapture)
izvēlies *Code > Download ZIP* un izpako to.

## 3. Atver terminali mapē {#open-a-terminal-in-a-folder}

Terminālis ir logs, kurā raksti komandas. Šīs lapas izmanto **PowerShell**, ko ir katrā Windows datorā.

- Failu pārlūkā atver mapi, noklikšķini adreses joslā, ieraksti `powershell` un nospied Enter.
  PowerShell atveras **tajā mapē**.
- Vai atver PowerShell no izvēlnes Sākt un pārvietojies uz mapi ar `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Kā lasīt komandas šajās lapās {#read-the-commands-on-these-pages}

- Ieraksti katru komandas rindu un nospied Enter.
- Teksts leņķiekavās ir **vietturis**: ieliec tur savu vērtību, bez leņķiekavām.
  `<recording>.mp4` nozīmē faila nosaukumu, piemēram, `match1.mp4`.
- Teksts kvadrātiekavās, piemēram, `[--fps 5]`, ir **izvēles**.
- Ceļš ar atstarpēm vajag pēdiņas: `"C:\My Videos\match1.mp4"`.
- Rindas, kas sākas ar `#`, ir komentāri. Tās nerakstīt.

## 5. Iegūsti rīku un tā pakotnes {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` izveido privātu mapi rīka pakotnēm, lai tās nesajauktos ar citām lietām tavā datorā.
Tad katra komanda sākas ar `.venv\Scripts\python`.

**Tev vajadzētu redzēt**, ka pēdējā rindā ir `Successfully installed ...`. Pārbaudi, ka rīks darbojas:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Tev vajadzētu redzēt** komandu sarakstu, sākot ar `usage: heat3d_capture`.

![Komandu saraksts, ko izdrukā --help](../assets/img/cli-help.svg)

Tu vari arī *aktivizēt* mapi vienreiz un tad rakstīt tikai `python`:

| Terminālis | Aktivizēt | Tad |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ja PowerShell saka *running scripts is disabled*, palaid vienreiz
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, vai izlaid aktivizēšanu.

## 6. Papildu programmas, kas dažām komandām vajag {#extra-programs-some-commands-need}

| Komanda | Vajag | Uzstādīt |
|---|---|---|
| `hud` | **ffmpeg** un **ffprobe** (lasa video failus) | `winget install Gyan.FFmpeg`, tad atver jaunu terminali. Pārbaudi ar `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, uzstādīts pirms pārējām pakotnēm | komanda no [pytorch.org](https://pytorch.org/get-started/locally/) tavai GPU |

## Ja kaut kas noiet greizi {#when-something-goes-wrong}

| Tu redzi | Tas nozīmē | Dari šo |
|---|---|---|
| `'python' is not recognized` | Python nav PATH | Uzstādi Python vēlreiz ar PATH atzīmi, tad atver jaunu terminali. |
| `No module named heat3d_capture` | terminālis nav rīka mapē | `cd` ieej mapē `3DHeat-GameCapture`. |
| `No module named numpy` (vai cita pakotne) | pakotnes nav uzstādītas, vai izmantoji citu Python | Palaid rindu `pip install -r requirements.txt` vēlreiz, ar `.venv\Scripts\python`. |
| `'.venv' is not recognized` | cmd ieraksti `/` | Izmanto atpakaļsvītras: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nav | Skat. 6. soli, tad atver jaunu terminali. |

Tālāk: [Sākums](index.md) satur pirmo piemēru katram darbam.
