---
title: "Než začnete"
nav_order: 1.5
lang: cs
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Než začnete {#before-you-start}

Nikdy jste nepracovali s příkazovým řádkem? Tato stránka vás provede od nuly až k prvnímu funkčnímu
příkazu. Zabere to jednou asi deset minut.

## 1. Nainstalujte Python {#install-python}

GameCapture je program v Pythonu. Potřebujete **Python 3.10 nebo novější**.

1. Přejděte na [python.org/downloads](https://www.python.org/downloads/) a stáhněte nejnovější
   Python pro Windows.
2. Spusťte instalátor. Na první obrazovce **zaškrtněte „Add python.exe to PATH“**. Bez tohoto
   zaškrtnutí terminál Python nenajde.
3. Klikněte na *Install Now*.

Nebo v terminálu: `winget install Python.Python.3.12`.

## 2. Nainstalujte Git {#install-git}

Git stáhne nástroj. Získejte ho na [git-scm.com](https://git-scm.com/download/win), nebo spusťte
`winget install Git.Git`. Pokud Git nechcete, použijte *Code > Download ZIP* na
[stránce GitHubu](https://github.com/Holdi601/3DHeat-GameCapture) a rozbalte ho.

## 3. Otevřete terminál ve složce {#open-a-terminal-in-a-folder}

Terminál je okno, do kterého píšete příkazy. Tyto stránky používají **PowerShell**, který má každý
počítač s Windows.

- Otevřete složku v Průzkumníkovi, klikněte do adresního řádku, napište `powershell` a stiskněte Enter.
  PowerShell se otevře **přímo v té složce**.
- Nebo otevřete PowerShell z nabídky Start a přejděte do složky příkazem `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Jak číst příkazy na těchto stránkách {#read-the-commands-on-these-pages}

- Napište každý řádek příkazu a stiskněte Enter.
- Text v lomených závorkách je **zástupný text**: sem napište svou vlastní hodnotu, bez závorek.
  `<recording>.mp4` znamená název souboru, například `match1.mp4`.
- Text v hranatých závorkách, například `[--fps 5]`, je **volitelný**.
- Cesta s mezerami potřebuje uvozovky: `"C:\My Videos\match1.mp4"`.
- Řádky začínající na `#` jsou poznámky. Nepište je.

## 5. Získejte nástroj a jeho balíčky {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` vytvoří soukromou složku pro balíčky nástroje, aby se nemíchaly s ničím
jiným v počítači. Každý další příkaz pak začíná `.venv\Scripts\python`.

**Měli byste vidět**, že poslední řádek končí `Successfully installed ...`. Ověřte, že nástroj funguje:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Měli byste vidět** seznam příkazů, který začíná `usage: heat3d_capture`.

![Seznam příkazů, který vypíše --help](../assets/img/cli-help.svg)

Složku můžete také jednou *aktivovat* a pak psát jen `python`:

| Terminál | Aktivace | Potom |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Pokud PowerShell řekne *running scripts is disabled*, spusťte jednou
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, nebo aktivaci přeskočte.

## 6. Další programy, které některé příkazy potřebují {#extra-programs-some-commands-need}

| Příkaz | Potřebuje | Instalace |
|---|---|---|
| `hud` | **ffmpeg** a **ffprobe** (čtení video souborů) | `winget install Gyan.FFmpeg`, pak otevřete nový terminál. Ověřte `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, nainstalovaný před ostatními balíčky | příkaz z [pytorch.org](https://pytorch.org/get-started/locally/) pro vaši grafickou kartu |

## Když se něco pokazí {#when-something-goes-wrong}

| Zobrazí se | Co to znamená | Co dělat |
|---|---|---|
| `'python' is not recognized` | Python není v PATH | Nainstalujte Python znovu se zaškrtnutím PATH, pak otevřete nový terminál. |
| `No module named heat3d_capture` | terminál není ve složce nástroje | `cd` do složky `3DHeat-GameCapture`. |
| `No module named numpy` (nebo jiný balíček) | balíčky nejsou nainstalované, nebo jste použili jiný Python | Spusťte znovu řádek `pip install -r requirements.txt` s `.venv\Scripts\python`. |
| `'.venv' is not recognized` | v cmd jste napsali `/` | Použijte zpětná lomítka: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | chybí ffmpeg | Viz krok 6, pak otevřete nový terminál. |

Dále: [Domů](index.md) obsahuje první příklad pro každou úlohu.
