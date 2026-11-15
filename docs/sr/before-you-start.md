---
title: Пре почетка
nav_order: 1.5
lang: "sr"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Пре почетка {#before-you-start}

Први пут у командној линији? Ова страница вас води од нуле до прве радне команде. Траје
око десет минута, једном.

## 1. Инсталирајте Python {#install-python}

GameCapture је Python програм. Треба вам **Python 3.10 или новији**.

1. Идите на [python.org/downloads](https://www.python.org/downloads/) и преузмите најновији
   Python за Windows.
2. Покрените инсталер. На његовом првом екрану **штиклирајте „Add python.exe to PATH“**. Без штиклирања,
   терминал неће наћи Python.
3. Кликните *Install Now*.

Или, у терминалу: `winget install Python.Python.3.12`.

## 2. Инсталирајте Git {#install-git}

Git преузима алат. Набавите га са [git-scm.com](https://git-scm.com/download/win), или покрените
`winget install Git.Git`. Ако не желите Git, користите *Code > Download ZIP* на
[GitHub страници](https://github.com/Holdi601/3DHeat-GameCapture) и распакујте га.

## 3. Отворите терминал у фасцикли {#open-a-terminal-in-a-folder}

Терминал је прозор у који куцате команде. Ове странице користе **PowerShell**, који има
сваки Windows рачунар.

- Отворите фасциклу у File Explorer-у, кликните у адресну траку, укуцајте `powershell` и притисните Enter.
  PowerShell се отвара **у тој фасцикли**.
- Или отворите PowerShell из Start менија и пређите у фасциклу помоћу `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Читајте команде на овим страницама {#read-the-commands-on-these-pages}

- Укуцајте сваки ред команде и притисните Enter.
- Текст у угластим заградама је **место за попуњавање**: ту ставите своју вредност, без заграда.
  `<recording>.mp4` значи име датотеке као `match1.mp4`.
- Текст у угластим заградама, као `[--fps 5]`, је **необавезан**: изоставите га ако не треба.
- Путања са размацима треба наводнике: `"C:\My Videos\match1.mp4"`.
- Редови који почињу са `#` су коментари. Не куцате их.

## 5. Набави алат и његове пакете {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` прави приватну фасциклу за пакете алата, да се не мешају са
ничим другим на вашем рачунару. Свака команда онда почиње са `.venv\Scripts\python`.

**Требало би да видите** да последњи ред каже `Successfully installed ...`. Проверите да алат ради:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Требало би да видите** списак команди, који почиње са `usage: heat3d_capture`.

![Списак команди који исписује --help](../assets/img/cli-help.svg)

Можете и једном *активирати* фасциклу, па онда куцати само `python`:

| Терминал | Активирање | Затим |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ако PowerShell каже *running scripts is disabled*, покрените
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` једном, или прескочите активирање.

## 6. Додатни програми које неке команде траже {#extra-programs-some-commands-need}

| Команда | Треба | Инсталација |
|---|---|---|
| `hud` | **ffmpeg** и **ffprobe** (читају видео датотеке) | `winget install Gyan.FFmpeg`, па отворите нови терминал. Проверите са `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, инсталиран пре осталих пакета | команда са [pytorch.org](https://pytorch.org/get-started/locally/) за ваш GPU |

## Кад нешто није у реду {#when-something-goes-wrong}

| Видите | Значи | Урадите ово |
|---|---|---|
| `'python' is not recognized` | Python није у PATH-у | Инсталирајте Python поново са штиклираним PATH-ом, па отворите нови терминал. |
| `No module named heat3d_capture` | терминал није у фасцикли алата | `cd` у фасциклу `3DHeat-GameCapture`. |
| `No module named numpy` (или неки други пакет) | пакети нису инсталирани, или сте користили други Python | Покрените ред `pip install -r requirements.txt` поново, са `.venv\Scripts\python`. |
| `'.venv' is not recognized` | у cmd-у сте укуцали `/` | Користите косе црте уназад: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg недостаје | Видите корак 6, па отворите нови терминал. |

Следеће: [Почетна](index.md) има први пример за сваки посао.
