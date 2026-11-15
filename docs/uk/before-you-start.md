---
title: Перш ніж почати
nav_order: 1.5
lang: uk
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Перш ніж почати {#before-you-start}

Ви лише починаєте працювати з командним рядком? Ця сторінка проведе вас від нуля до першої
робочої команди. Це займе близько десяти хвилин, один раз.

## 1. Встановіть Python {#install-python}

GameCapture - це програма на Python. Потрібен **Python 3.10 або новіший**.

1. Перейдіть на [python.org/downloads](https://www.python.org/downloads/) і завантажте
   найновіший Python для Windows.
2. Запустіть інсталятор. На першому екрані **позначте "Add python.exe to PATH"**. Без цієї
   позначки термінал не знайде Python.
3. Натисніть *Install Now*.

Або в терміналі: `winget install Python.Python.3.12`.

## 2. Встановіть Git {#install-git}

Git завантажує інструмент. Отримайте його на [git-scm.com](https://git-scm.com/download/win)
або виконайте `winget install Git.Git`. Якщо Git вам не потрібен, скористайтеся *Code > Download ZIP*
на [сторінці GitHub](https://github.com/Holdi601/3DHeat-GameCapture) і розпакуйте архів.

## 3. Відкрийте термінал у папці {#open-a-terminal-in-a-folder}

Термінал - це вікно, в яке ви вводите команди. Ці сторінки використовують **PowerShell**, який
є на кожному ПК з Windows.

- Відкрийте папку в Провіднику файлів, клацніть рядок адреси, введіть `powershell` і
  натисніть Enter. PowerShell відкриється **в цій папці**.
- Або відкрийте PowerShell із меню Пуск і перейдіть до папки командою `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Читайте команди на цих сторінках {#read-the-commands-on-these-pages}

- Вводьте кожен рядок команди і натискайте Enter.
- Текст у кутових дужках - це **заповнювач**: введіть там власне значення, без дужок.
  `<recording>.mp4` означає назву файлу на кшталт `match1.mp4`.
- Текст у квадратних дужках, наприклад `[--fps 5]`, - **необов'язковий**.
- Шлях із пробілами потребує лапок: `"C:\My Videos\match1.mp4"`.
- Рядки, що починаються з `#`, - це коментарі. Їх не вводять.

## 5. Отримайте інструмент і його пакети {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` створює приватну папку для пакетів інструмента, щоб вони не змішувалися
з усім іншим на вашому ПК. Далі кожна команда починається з `.venv\Scripts\python`.

**Ви маєте побачити**, що останній рядок каже `Successfully installed ...`. Перевірте, що
інструмент працює:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Ви маєте побачити** список команд, що починається з `usage: heat3d_capture`.

![Список команд, який виводить --help](../assets/img/cli-help.svg)

Ви також можете *активувати* папку один раз, і тоді вводити просто `python`:

| Термінал | Активація | Потім |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Якщо PowerShell каже *running scripts is disabled*, виконайте один раз
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` або пропустіть активацію.

## 6. Додаткові програми, які потрібні деяким командам {#extra-programs-some-commands-need}

| Команда | Потребує | Встановлення |
|---|---|---|
| `hud` | **ffmpeg** і **ffprobe** (читання відеофайлів) | `winget install Gyan.FFmpeg`, потім відкрийте новий термінал. Перевірте командою `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, встановлюється перед іншими пакетами | команда з [pytorch.org](https://pytorch.org/get-started/locally/) для вашої GPU |

## Якщо щось пішло не так {#when-something-goes-wrong}

| Ви бачите | Що це означає | Що робити |
|---|---|---|
| `'python' is not recognized` | Python немає в PATH | Перевстановіть Python з позначкою PATH, потім відкрийте новий термінал. |
| `No module named heat3d_capture` | термінал не в папці інструмента | Виконайте `cd` до папки `3DHeat-GameCapture`. |
| `No module named numpy` (або інший пакет) | пакети не встановлено, або ви використали інший Python | Виконайте рядок `pip install -r requirements.txt` знову, з `.venv\Scripts\python`. |
| `'.venv' is not recognized` | ви ввели `/` у cmd | Використовуйте зворотні слеші: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg відсутній | Див. крок 6, потім відкрийте новий термінал. |

Далі: [Головна](index.md) має перший приклад для кожного завдання.
