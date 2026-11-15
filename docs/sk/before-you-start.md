---
title: "Ako začať"
nav_order: 1.5
lang: "sk"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Ako začať {#before-you-start}

Nikdy ste nepracovali s príkazovým riadkom? Táto stránka vás od nuly dostane k prvému
funkčnému príkazu. Trvá to asi desať minút, a len raz.

## 1. Nainštalujte Python {#install-python}

GameCapture je program v Pythone. Potrebujete **Python 3.10 alebo novší**.

1. Choďte na [python.org/downloads](https://www.python.org/downloads/) a stiahnite si najnovší
   Python pre Windows.
2. Spustite inštalátor. Na jeho prvej obrazovke **zaškrtnite „Add python.exe to PATH“**. Bez tohto zaškrtnutia
   terminál Python nenájde.
3. Kliknite na *Install Now*.

Alebo v termináli: `winget install Python.Python.3.12`.

## 2. Nainštalujte Git {#install-git}

Git stiahne nástroj. Získajte ho na [git-scm.com](https://git-scm.com/download/win), alebo spustite
`winget install Git.Git`. Ak Git nechcete, použite *Code > Download ZIP* na
[stránke GitHub](https://github.com/Holdi601/3DHeat-GameCapture) a rozbaľte ho.

## 3. Otvorte terminál v priečinku {#open-a-terminal-in-a-folder}

Terminál je okno, do ktorého píšete príkazy. Tieto stránky používajú **PowerShell**, ktorý má každý
počítač so systémom Windows.

- Otvorte priečinok v Prieskumníkovi, kliknite na panel s adresou, napíšte `powershell` a stlačte Enter.
  PowerShell sa otvorí **v tomto priečinku**.
- Alebo otvorte PowerShell z ponuky Štart a presuňte sa do priečinka príkazom `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Čítajte príkazy na týchto stránkach {#read-the-commands-on-these-pages}

- Napíšte každý riadok príkazu a stlačte Enter.
- Text v uhlových zátvorkách je **zástupný znak**: napíšte tam vlastnú hodnotu, bez zátvoriek.
  `<recording>.mp4` znamená názov súboru, napríklad `match1.mp4`.
- Text v hranatých zátvorkách, napríklad `[--fps 5]`, je **voliteľný**.
- Cesta s medzerami potrebuje úvodzovky: `"C:\My Videos\match1.mp4"`.
- Riadky začínajúce na `#` sú komentáre. Nepíšete ich.

## 5. Získajte nástroj a jeho balíky {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` vytvorí súkromný priečinok pre balíky nástroja, aby sa nemiešali
s ničím iným v počítači. Každý ďalší príkaz potom začína `.venv\Scripts\python`.

**Mali by ste vidieť**, že posledný riadok hovorí `Successfully installed ...`. Overte, že nástroj funguje:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Mali by ste vidieť** zoznam príkazov, ktorý začína `usage: heat3d_capture`.

![Zoznam príkazov, ktorý vypisuje --help](../assets/img/cli-help.svg)

Priečinok môžete aj *aktivovať* raz a potom písať len `python`:

| Terminál | Aktivácia | Potom |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ak PowerShell povie *running scripts is disabled*, spustite raz
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, alebo aktiváciu preskočte.

## 6. Ďalšie programy, ktoré niektoré príkazy potrebujú {#extra-programs-some-commands-need}

| Príkaz | Potrebuje | Inštalácia |
|---|---|---|
| `hud` | **ffmpeg** a **ffprobe** (čítajú video súbory) | `winget install Gyan.FFmpeg`, potom otvorte nový terminál. Overte príkazom `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, nainštalovaný pred ostatnými balíkmi | príkaz z [pytorch.org](https://pytorch.org/get-started/locally/) pre vašu GPU |

## Keď niečo nevyjde {#when-something-goes-wrong}

| Vidíte | Čo to znamená | Čo robiť |
|---|---|---|
| `'python' is not recognized` | Python nie je v PATH | Nainštalujte Python znova so zaškrtnutím PATH a potom otvorte nový terminál. |
| `No module named heat3d_capture` | terminál nie je v priečinku nástroja | `cd` do priečinka `3DHeat-GameCapture`. |
| `No module named numpy` (alebo iný balík) | balíky nie sú nainštalované, alebo ste použili iný Python | Spustite riadok `pip install -r requirements.txt` znova, s `.venv\Scripts\python`. |
| `'.venv' is not recognized` | v cmd ste napísali `/` | Použite spätné lomky: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg chýba | Pozrite krok 6 a potom otvorte nový terminál. |

Ďalej: [Domov](index.md) má prvý príklad pre každú úlohu.
