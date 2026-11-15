---
title: "Preden začneš"
nav_order: 1.5
lang: sl
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Preden začneš {#before-you-start}

Še nisi vajen ukazne vrstice? Ta stran te v približno desetih minutah, enkrat, vodi od nič do prvega
delujočega ukaza.

## 1. Namesti Python {#install-python}

GameCapture je program v Pythonu. Potrebuješ **Python 3.10 ali novejši**.

1. Pojdi na [python.org/downloads](https://www.python.org/downloads/) in prenesi najnovejši
   Python za Windows.
2. Zaženi namestitev. Na prvem zaslonu **obkljukaj »Add python.exe to PATH«**. Brez obkljukanega polja
   terminal Pythona ne bo našel.
3. Klikni *Install Now*.

Ali v terminalu: `winget install Python.Python.3.12`.

## 2. Namesti Git {#install-git}

Git prenese orodje. Dobiš ga na [git-scm.com](https://git-scm.com/download/win) ali z ukazom
`winget install Git.Git`. Če Git ne želiš, uporabi *Code > Download ZIP* na
[strani GitHub](https://github.com/Holdi601/3DHeat-GameCapture) in ga razpakiraj.

## 3. Odpri terminal v mapi {#open-a-terminal-in-a-folder}

Terminal je okno, v katerem vtipkaš ukaze. Te strani uporabljajo **PowerShell**, ki ga ima vsak računalnik
z Windows.

- Odpri mapo v Raziskovalcu, klikni v vrstico z naslovom, vtipkaj `powershell` in pritisni Enter.
  PowerShell se odpre **v tej mapi**.
- Ali odpri PowerShell iz menija Start in se premakni v mapo z `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Kako brati ukaze na teh straneh {#read-the-commands-on-these-pages}

- Vtipkaj vsako vrstico ukaza in pritisni Enter.
- Besedilo v kotnih oklepajih je **nadomestilo**: na to mesto vpiši svojo vrednost, brez oklepajev.
  `<posnetek>.mp4` pomeni ime datoteke, na primer `tekma1.mp4`.
- Besedilo v oglatih oklepajih, na primer `[--fps 5]`, je **izbirno**.
- Pot s presledki potrebuje narekovaje: `"C:\Moji videi\tekma1.mp4"`.
- Vrstice, ki se začnejo s `#`, so komentarji. Ne vtipkaš jih.

## 5. Pridobi orodje in njegove pakete {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` ustvari zasebno mapo za pakete orodja, da se ne pomešajo z ničimer drugim na
računalniku. Vsak nadaljnji ukaz se nato začne z `.venv\Scripts\python`.

**Videti bi moral**, da zadnja vrstica piše `Successfully installed ...`. Preveri, da orodje deluje:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Videti bi moral** seznam ukazov, ki se začne z `usage: heat3d_capture`.

![Seznam ukazov, ki ga izpiše --help](../assets/img/cli-help.svg)

Mapo lahko tudi *aktiviraš* enkrat, nato pa vtipkaš samo `python`:

| Terminal | Aktiviraj | Nato |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Če PowerShell reče *running scripts is disabled*, zaženi enkrat
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ali pa aktiviranje preskoči.

## 6. Dodatni programi, ki jih nekateri ukazi potrebujejo {#extra-programs-some-commands-need}

| Ukaz | Potrebuje | Namestitev |
|---|---|---|
| `hud` | **ffmpeg** in **ffprobe** (za branje video datotek) | `winget install Gyan.FFmpeg`, nato odpri nov terminal. Preveri z `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, nameščen pred ostalimi paketi | ukaz s [pytorch.org](https://pytorch.org/get-started/locally/) za tvojo grafično kartico |

## Ko nekaj ne gre prav {#when-something-goes-wrong}

| Kar vidiš | Pomeni | Kaj storiti |
|---|---|---|
| `'python' is not recognized` | Python ni na PATH | Ponovno namesti Python z obkljukanim PATH, nato odpri nov terminal. |
| `No module named heat3d_capture` | terminal ni v mapi orodja | `cd` v mapo `3DHeat-GameCapture`. |
| `No module named numpy` (ali drug paket) | paketi niso nameščeni ali si uporabil drug Python | Ponovno zaženi vrstico `pip install -r requirements.txt`, z `.venv\Scripts\python`. |
| `'.venv' is not recognized` | v cmd si vtipkal `/` | Uporabi poševnice nazaj: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg manjka | Glej korak 6, nato odpri nov terminal. |

Naprej: [Začetna stran](index.md) ima prvi primer za vsako nalogo.
