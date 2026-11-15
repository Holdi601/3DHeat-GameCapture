---
title: Пред да започнете
nav_order: 1.5
lang: "mk"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Пред да започнете {#before-you-start}

Нови сте со командната линија? Оваа страница ве води од нула до првата команда што работи. Потребни се
околу десет минути, еднаш.

## 1. Инсталирајте Python {#install-python}

GameCapture е програма на Python. Потребен ви е **Python 3.10 или понов**.

1. Одете на [python.org/downloads](https://www.python.org/downloads/) и преземете го најновиот
   Python за Windows.
2. Пуштете го инсталерот. На првиот екран **штиклирајте „Add python.exe to PATH“**. Без штиклирањето,
   терминалот нема да го најде Python.
3. Кликнете *Install Now*.

Или, во терминал: `winget install Python.Python.3.12`.

## 2. Инсталирајте Git {#install-git}

Git ја презема алатката. Преземете го од [git-scm.com](https://git-scm.com/download/win), или пуштете
`winget install Git.Git`. Ако не сакате Git, користете *Code > Download ZIP* на
[страницата на GitHub](https://github.com/Holdi601/3DHeat-GameCapture) и распакувајте го.

## 3. Отворете терминал во папка {#open-a-terminal-in-a-folder}

Терминалот е прозорец во кој пишувате команди. Овие страници користат **PowerShell**, кој го има секој
компјутер со Windows.

- Отворете ја папката во File Explorer, кликнете во адресната лента, напишете `powershell` и притиснете Enter.
  PowerShell се отвора **во таа папка**.
- Или отворете PowerShell од менито Start и преминете во папка со `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Прочитајте ги командите на овие страници {#read-the-commands-on-these-pages}

- Напишете ја секоја командна линија и притиснете Enter.
- Текстот во аголни загради е **место за пополнување**: ставете своја вредност таму, без заградите.
  `<recording>.mp4` значи име на датотека како `match1.mp4`.
- Текстот во средни загради, како `[--fps 5]`, е **по избор**.
- Патека со празни места бара наводници: `"C:\My Videos\match1.mp4"`.
- Линиите што почнуваат со `#` се коментари. Не ги пишувате.

## 5. Преземете ја алатката и нејзините пакети {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` прави приватна папка за пакетите на алатката, за да не се мешаат со
ништо друго на вашиот компјутер. Секоја команда потоа почнува со `.venv\Scripts\python`.

**Треба да видите** дека последната линија вели `Successfully installed ...`. Проверете дали алатката работи:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Треба да видите** список на команди, што почнува со `usage: heat3d_capture`.

![Списокот на команди што го печати --help](../assets/img/cli-help.svg)

Можете и еднаш да ја *активирате* папката, па потоа да пишувате само `python`:

| Терминал | Активирање | Потоа |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Ако PowerShell каже *running scripts is disabled*, пуштете еднаш
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, или прескокнете ја активацијата.

## 6. Дополнителни програми што ги бараат некои команди {#extra-programs-some-commands-need}

| Команда | Бара | Инсталирање |
|---|---|---|
| `hud` | **ffmpeg** и **ffprobe** (читаат видео датотеки) | `winget install Gyan.FFmpeg`, потоа отворете нов терминал. Проверете со `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, инсталиран пред другите пакети | командата од [pytorch.org](https://pytorch.org/get-started/locally/) за вашиот GPU |

## Кога нешто ќе тргне наопаку {#when-something-goes-wrong}

| Што гледате | Што значи | Направете го ова |
|---|---|---|
| `'python' is not recognized` | Python не е во PATH | Инсталирајте го Python повторно со штиклирањето за PATH, потоа отворете нов терминал. |
| `No module named heat3d_capture` | терминалот не е во папката на алатката | Со `cd` влезете во папката `3DHeat-GameCapture`. |
| `No module named numpy` (или друг пакет) | пакетите не се инсталирани, или сте користеле друг Python | Пуштете ја линијата `pip install -r requirements.txt` повторно, со `.venv\Scripts\python`. |
| `'.venv' is not recognized` | напишавте `/` во cmd | Користете обратни црти: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | недостасува ffmpeg | Видете чекор 6, потоа отворете нов терминал. |

Следно: [Почетна](index.md) има прв пример за секоја задача.
