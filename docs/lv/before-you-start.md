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

Vai nekad neesat strādājis ar komandrindu? Šī lapa palīdzēs jums no nulles nonākt līdz pirmajai strādājošajai komandai. Tas aizņem apmēram desmit minūtes, vienu reizi.

## 1. Uzstādiet Python {#install-python}

GameCapture ir Python programma. Vajag **Python 3.10 vai jaunāku versiju**.

1. Dodieties uz [python.org/downloads](https://www.python.org/downloads/) un lejupielādējiet jaunāko
   Python Windows versijai.
2. Palaidiet instalētāju. Pirmajā ekrānā **atzīmējiet "Add python.exe to PATH"**. Bez šīs atzīmes
   termināls neatradīs Python.
3. Noklikšķiniet *Install Now*.

Vai termināli: `winget install Python.Python.3.12`.

## 2. Uzstādiet Git {#install-git}

Git lejupielādē rīku. Iegūstiet to no [git-scm.com](https://git-scm.com/download/win) vai palaidiet
`winget install Git.Git`. Ja Git nevēlaties, [GitHub lapā](https://github.com/Holdi601/3DHeat-GameCapture)
izvēlieties *Code > Download ZIP* un izpakojiet to.

## 3. Atveriet termināli mapē {#open-a-terminal-in-a-folder}

Termināls ir logs, kurā rakstāt komandas. Šajās lapās izmanto **PowerShell**, kas ir katrā Windows datorā.

- Failu pārlūkā atveriet mapi, noklikšķiniet adreses joslā, ierakstiet `powershell` un nospiediet Enter.
  PowerShell atveras **tajā mapē**.
- Vai atveriet PowerShell no izvēlnes Sākt un pārvietojieties uz mapi ar `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Kā lasīt komandas šajās lapās {#read-the-commands-on-these-pages}

- Ierakstiet katru komandas rindu un nospiediet Enter.
- Teksts leņķiekavās ir **vietturis**: ieliekiet tur savu vērtību, bez leņķiekavām.
  `<recording>.mp4` nozīmē faila nosaukumu, piemēram, `match1.mp4`.
- Teksts kvadrātiekavās, piemēram, `[--fps 5]`, ir **izvēles**.
- Ceļš ar atstarpēm vajag pēdiņas: `"C:\My Videos\match1.mp4"`.
- Rindas, kas sākas ar `#`, ir komentāri. Tās nerakstiet.

## 5. Iegūstiet rīku un tā pakotnes {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` izveido privātu mapi rīka pakotnēm, lai tās nesajauktos ar citām lietām jūsu datorā.
Tad katra komanda sākas ar `.venv\Scripts\python`.

**Jums vajadzētu redzēt**, ka pēdējā rindā ir `Successfully installed ...`. Pārbaudiet, ka rīks darbojas:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Jums vajadzētu redzēt** komandu sarakstu, sākot ar `usage: heat3d_capture`.

![Komandu saraksts, ko izdrukā --help](../assets/img/cli-help.svg)

Varat arī *aktivizēt* mapi vienreiz un tad rakstīt tikai `python`:

| Termināls | Aktivizēt | Tad |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ja PowerShell saka *running scripts is disabled*, palaidiet vienreiz
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, vai izlaidiet aktivizēšanu.

## 6. Papildu programmas, kas dažām komandām vajag {#extra-programs-some-commands-need}

| Komanda | Vajag | Uzstādīt |
|---|---|---|
| `hud` | **ffmpeg** un **ffprobe** (lasa video failus) | `winget install Gyan.FFmpeg`, tad atveriet jaunu termināli. Pārbaudiet ar `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, uzstādīts pirms pārējām pakotnēm | komanda no [pytorch.org](https://pytorch.org/get-started/locally/) jūsu GPU |

## Ja kaut kas noiet greizi {#when-something-goes-wrong}

| Jūs redzat | Tas nozīmē | Ko darīt |
|---|---|---|
| `'python' is not recognized` | Python nav PATH | Uzstādiet Python vēlreiz ar PATH atzīmi, tad atveriet jaunu termināli. |
| `No module named heat3d_capture` | termināls nav rīka mapē | Ar `cd` ieejiet mapē `3DHeat-GameCapture`. |
| `No module named numpy` (vai cita pakotne) | pakotnes nav uzstādītas, vai izmantojāt citu Python | Palaidiet rindu `pip install -r requirements.txt` vēlreiz, ar `.venv\Scripts\python`. |
| `'.venv' is not recognized` | cmd lieto `/` | Izmantojiet atpakaļsvītras: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg nav | Skatiet 6. soli, tad atveriet jaunu termināli. |

Tālāk: [Sākums](index.md) satur pirmo piemēru katram darbam.
