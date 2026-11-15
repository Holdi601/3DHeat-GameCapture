---
title: "Преди да започнете"
nav_order: 1.5
lang: "bg"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Преди да започнете {#before-you-start}

Нов ли сте в командния ред? Тази страница ви води от нищо до първа работеща команда. Отнема
около десет минути, веднъж.

## 1. Инсталирайте Python {#install-python}

GameCapture е програма на Python. Нужен е **Python 3.10 или по-нов**.

1. Отидете на [python.org/downloads](https://www.python.org/downloads/) и изтеглете най-новия
   Python за Windows.
2. Стартирайте инсталатора. На първия екран **отметнете „Add python.exe to PATH“**. Без отметката
   терминалът няма да намери Python.
3. Щракнете *Install Now*.

Или в терминал: `winget install Python.Python.3.12`.

## 2. Инсталирайте Git {#install-git}

Git изтегля инструмента. Вземете го от [git-scm.com](https://git-scm.com/download/win) или пуснете
`winget install Git.Git`. Ако не искате Git, използвайте *Code > Download ZIP* на
[страницата в GitHub](https://github.com/Holdi601/3DHeat-GameCapture) и разархивирайте.

## 3. Отворете терминал в папка {#open-a-terminal-in-a-folder}

Терминалът е прозорец, в който въвеждате команди. Тези страници използват **PowerShell**, който има
всеки компютър с Windows.

- Отворете папката във File Explorer, щракнете в адресния ред, напишете `powershell` и натиснете Enter.
  PowerShell се отваря **в същата папка**.
- Или отворете PowerShell от менюто „Старт“ и се преместете в папка с `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Прочетете командите на тези страници {#read-the-commands-on-these-pages}

- Напишете всеки ред с команда и натиснете Enter.
- Текст в ъглови скоби е **място за попълване**: сложете там своя стойност, без скобите.
  `<recording>.mp4` означава име на файл, например `match1.mp4`.
- Текст в квадратни скоби, например `[--fps 5]`, е **по желание**.
- Път с интервали се пише в кавички: `"C:\My Videos\match1.mp4"`.
- Редовете, които започват с `#`, са коментари. Не ги пишете.

## 5. Вземете инструмента и пакетите му {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` създава своя папка за пакетите на инструмента, за да не се смесват с нищо друго на компютъра ви. Всяка команда после започва с `.venv\Scripts\python`.

**Трябва да видите** последният ред да казва `Successfully installed ...`. Проверете, че инструментът работи:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Трябва да видите** списък с команди, започващ с `usage: heat3d_capture`.

![Списъкът с команди, който извежда --help](../assets/img/cli-help.svg)

Можете и веднъж да *активирате* папката и после да пишете само `python`:

| Терминал | Активиране | После |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ако PowerShell каже *running scripts is disabled*, пуснете веднъж
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` или пропуснете активирането.

## 6. Допълнителни програми, които някои команди изискват {#extra-programs-some-commands-need}

| Команда | Нужно е | Инсталиране |
|---|---|---|
| `hud` | **ffmpeg** и **ffprobe** (четат видеофайлове) | `winget install Gyan.FFmpeg`, после отворете нов терминал. Проверете с `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, инсталиран преди останалите пакети | командата от [pytorch.org](https://pytorch.org/get-started/locally/) за вашата видеокарта |

## Когато нещо се обърка {#when-something-goes-wrong}

| Виждате | Какво означава | Направете това |
|---|---|---|
| `'python' is not recognized` | Python не е в PATH | Инсталирайте Python отново с отметката за PATH, после отворете нов терминал. |
| `No module named heat3d_capture` | терминалът не е в папката на инструмента | `cd` до папката `3DHeat-GameCapture`. |
| `No module named numpy` (или друг пакет) | пакетите не са инсталирани или използвате друг Python | Пуснете отново реда `pip install -r requirements.txt` с `.venv\Scripts\python`. |
| `'.venv' is not recognized` | написали сте `/` в cmd | Използвайте обратни наклонени черти: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg липсва | Вижте стъпка 6, после отворете нов терминал. |

Следва: [Начало](index.md) има първ пример за всяка задача.
