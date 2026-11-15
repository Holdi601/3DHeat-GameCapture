---
title: "Перад пачаткам"
nav_order: 1.5
lang: be
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Перад пачаткам {#before-you-start}

Упершыню ў камандным радку? Гэтая старонка правядзе вас ад нуля да першай працоўнай каманды. Гэта займае
каля дзесяці хвілін, і толькі адзін раз.

## 1. Усталюйце Python {#install-python}

GameCapture — гэта праграма на Python. Вам патрэбен **Python 3.10 або навейшы**.

1. Перайдзіце на [python.org/downloads](https://www.python.org/downloads/) і спампуйце найновейшы
   Python для Windows.
2. Запусціце ўсталёўшчык. На першым экране **адзначце «Add python.exe to PATH»**. Без гэтай адзнакі
   тэрмінал не знойдзе Python.
3. Націсніце *Install Now*.

Або ў тэрмінале: `winget install Python.Python.3.12`.

## 2. Усталюйце Git {#install-git}

Git спампоўвае інструмент. Атрымайце яго на [git-scm.com](https://git-scm.com/download/win) або выканайце
`winget install Git.Git`. Калі Git вам не патрэбен, выкарыстайце *Code > Download ZIP* на
[старонцы GitHub](https://github.com/Holdi601/3DHeat-GameCapture) і распакуйце архіў.

## 3. Адкрыйце тэрмінал у папцы {#open-a-terminal-in-a-folder}

Тэрмінал — гэта акно, у якім друкуюць каманды. Гэтыя старонкі выкарыстоўваюць **PowerShell**, які ёсць
на кожным кампутары з Windows.

- Адкрыйце папку ў Правадыру, пстрыкніце ў адрасным радку, увядзіце `powershell` і націсніце Enter.
  PowerShell адкрыецца **у гэтай папцы**.
- Або адкрыйце PowerShell з меню «Пуск» і перайдзіце ў папку праз `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Як чытаць каманды на гэтых старонках {#read-the-commands-on-these-pages}

- Друкуйце кожны радок каманды і націскайце Enter.
- Тэкст у вуглавых дужках — гэта **запаўняльнік**: пастаўце туды сваё значэнне, без дужак.
  `<recording>.mp4` значыць імя файла накшталт `match1.mp4`.
- Тэкст у квадратных дужках, напрыклад `[--fps 5]`, — **неабавязковы**.
- Шлях з прабеламі патрабуе двукоссяў: `"C:\My Videos\match1.mp4"`.
- Радкі, што пачынаюцца з `#`, — гэта каментарыі. Іх не друкуюць.

## 5. Атрымайце інструмент і яго пакеты {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` стварае прыватную папку для пакетаў інструмента, каб яны не змешваліся
ні з чым іншым на вашым кампутары. Кожная каманда потым пачынаецца з `.venv\Scripts\python`.

**Вы ўбачыце**, што апошні радок кажа `Successfully installed ...`. Праверце, што інструмент працуе:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Вы ўбачыце** спіс каманд, які пачынаецца з `usage: heat3d_capture`.

![Спіс каманд, які друкуе --help](../assets/img/cli-help.svg)

Можна таксама адзін раз *актываваць* папку, а потым друкаваць толькі `python`:

| Тэрмінал | Актываваць | Потым |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Калі PowerShell кажа *running scripts is disabled*, выканайце адзін раз
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` або прапусціце актывацыю.

## 6. Дадатковыя праграмы, якія патрэбны некаторым камандам {#extra-programs-some-commands-need}

| Каманда | Што патрэбна | Як усталяваць |
|---|---|---|
| `hud` | **ffmpeg** і **ffprobe** (чытаюць відэафайлы) | `winget install Gyan.FFmpeg`, потым адкрыйце новы тэрмінал. Праверка: `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, усталяваны перад астатнімі пакетамі | каманда з [pytorch.org](https://pytorch.org/get-started/locally/) для вашага GPU |

## Калі нешта пайшло не так {#when-something-goes-wrong}

| Вы бачыце | Што гэта значыць | Што рабіць |
|---|---|---|
| `'python' is not recognized` | Python няма ў PATH | Пераўсталюйце Python з адзнакай PATH, потым адкрыйце новы тэрмінал. |
| `No module named heat3d_capture` | тэрмінал не ў папцы інструмента | Перайдзіце праз `cd` у папку `3DHeat-GameCapture`. |
| `No module named numpy` (або іншы пакет) | пакеты не ўсталяваны, або вы выкарыстоўвалі іншы Python | Паўтарыце радок `pip install -r requirements.txt` з `.venv\Scripts\python`. |
| `'.venv' is not recognized` | вы ўвялі `/` у cmd | Выкарыстоўвайце адваротныя касыя рыскі: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | няма ffmpeg | Гл. крок 6, потым адкрыйце новы тэрмінал. |

Далей: [Галоўная](index.md) мае першы прыклад для кожнай задачы.
