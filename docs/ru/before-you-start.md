---
title: С чего начать
nav_order: 1.5
lang: "ru"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# С чего начать {#before-you-start}

Впервые в командной строке? Эта страница проведёт вас от нуля до первой рабочей команды. Это
займёт около десяти минут, один раз.

## 1. Установите Python {#install-python}

GameCapture — это программа на Python. Нужен **Python 3.10 или новее**.

1. Перейдите на [python.org/downloads](https://www.python.org/downloads/) и скачайте самую новую
   версию Python для Windows.
2. Запустите установщик. На первом экране **отметьте «Add python.exe to PATH»**. Без этой отметки
   терминал не найдёт Python.
3. Нажмите *Install Now*.

Или в терминале: `winget install Python.Python.3.12`.

## 2. Установите Git {#install-git}

Git скачивает инструмент. Возьмите его на [git-scm.com](https://git-scm.com/download/win) или
выполните `winget install Git.Git`. Если Git вам не нужен, используйте *Code > Download ZIP* на
[странице GitHub](https://github.com/Holdi601/3DHeat-GameCapture) и распакуйте архив.

## 3. Откройте терминал в папке {#open-a-terminal-in-a-folder}

Терминал — это окно, в которое вы вводите команды. На этих страницах используется **PowerShell**,
который есть на каждом ПК с Windows.

- Откройте папку в Проводнике, щёлкните в адресной строке, введите `powershell` и нажмите Enter.
  PowerShell откроется **в этой папке**.
- Или откройте PowerShell из меню «Пуск» и перейдите в нужную папку командой `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Как читать команды на этих страницах {#read-the-commands-on-these-pages}

- Вводите каждую строку команды и нажимайте Enter.
- Текст в угловых скобках — **заполнитель**: вместо него введите своё значение, без скобок.
  `<recording>.mp4` означает имя файла, например `match1.mp4`.
- Текст в квадратных скобках, например `[--fps 5]`, — **необязательный**.
- Путь с пробелами нужно брать в кавычки: `"C:\My Videos\match1.mp4"`.
- Строки, которые начинаются с `#`, — комментарии. Их не вводят.

## 5. Получите инструмент и его пакеты {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` создаёт отдельную папку для пакетов инструмента, чтобы они не смешивались
ни с чем другим на вашем ПК. Каждая команда дальше начинается с `.venv\Scripts\python`.

**Вы должны увидеть**, что последняя строка говорит `Successfully installed ...`. Проверьте, что
инструмент работает:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Вы должны увидеть** список команд, начинающийся с `usage: heat3d_capture`.

![Список команд, который печатает --help](../assets/img/cli-help.svg)

Можно также *активировать* папку один раз, и тогда достаточно набирать `python`:

| Терминал | Активация | Затем |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Если PowerShell пишет *running scripts is disabled*, выполните один раз
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` или просто не активируйте папку.

## 6. Дополнительные программы, которые нужны некоторым командам {#extra-programs-some-commands-need}

| Команда | Нужно | Установка |
|---|---|---|
| `hud` | **ffmpeg** и **ffprobe** (чтение видеофайлов) | `winget install Gyan.FFmpeg`, затем откройте новый терминал. Проверка: `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, устанавливается до остальных пакетов | команда с [pytorch.org](https://pytorch.org/get-started/locally/) для вашей видеокарты |

## Если что-то пошло не так {#when-something-goes-wrong}

| Вы видите | Что это значит | Что делать |
|---|---|---|
| `'python' is not recognized` | Python не в PATH | Переустановите Python с отметкой PATH, затем откройте новый терминал. |
| `No module named heat3d_capture` | терминал не в папке инструмента | Выполните `cd` в папку `3DHeat-GameCapture`. |
| `No module named numpy` (или другой пакет) | пакеты не установлены или вы используете другой Python | Повторите строку `pip install -r requirements.txt` с `.venv\Scripts\python`. |
| `'.venv' is not recognized` | в cmd введён `/` | Используйте обратные слеши: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg не установлен | См. шаг 6, затем откройте новый терминал. |

Дальше: [Главная](index.md) содержит первый пример для каждой задачи.
