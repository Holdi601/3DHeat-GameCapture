# Before you start

New to the command line? This page gets you from nothing to a first working command. It takes
about ten minutes, once.

## 1. Install Python

GameCapture is a Python program. You need **Python 3.10 or later**.

1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the newest
   Python for Windows.
2. Run the installer. On the first screen, **tick "Add python.exe to PATH"**. Without the tick,
   the terminal will not find Python.
3. Click *Install Now*.

Or, in a terminal: `winget install Python.Python.3.12`.

## 2. Install Git

Git downloads the tool. Get it from [git-scm.com](https://git-scm.com/download/win), or run
`winget install Git.Git`. If you do not want Git, use *Code > Download ZIP* on the
[GitHub page](https://github.com/Holdi601/3DHeat-GameCapture) and unzip it.

## 3. Open a terminal in a folder

A terminal is a window where you type commands. These pages use **PowerShell**, which every
Windows PC has.

- Open the folder in File Explorer, click the address bar, type `powershell` and press Enter.
  PowerShell opens **in that folder**.
- Or open PowerShell from the Start menu and move to a folder with `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Read the commands on these pages

- Type each command line and press Enter.
- Text in angle brackets is a **placeholder**: put your own value there, without the brackets.
  `<recording>.mp4` means a file name such as `match1.mp4`.
- Text in square brackets, such as `[--fps 5]`, is **optional**.
- A path with spaces needs quotes: `"C:\My Videos\match1.mp4"`.
- Lines starting with `#` are comments. You do not type them.

## 5. Get the tool and its packages

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` makes a private folder for the tool's packages, so they do not mix with
anything else on your PC. Every command then starts with `.venv\Scripts\python`.

**You should see** the last line say `Successfully installed ...`. Check the tool works:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**You should see** a list of commands, starting with `usage: heat3d_capture`.

![The list of commands that --help prints](https://raw.githubusercontent.com/Holdi601/3DHeat-GameCapture/main/docs/assets/img/cli-help.svg)

You can also *activate* the folder once, and then type just `python`:

| Terminal | Activate | Then |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

If PowerShell says *running scripts is disabled*, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip activating.

## 6. Extra programs some commands need

| Command | Needs | Install |
|---|---|---|
| `hud` | **ffmpeg** and **ffprobe** (read video files) | `winget install Gyan.FFmpeg`, then open a new terminal. Check with `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, installed before the other packages | the command from [pytorch.org](https://pytorch.org/get-started/locally/) for your GPU |

## When something goes wrong

| You see | It means | Do this |
|---|---|---|
| `'python' is not recognized` | Python is not on PATH | Reinstall Python with the PATH tick, then open a new terminal. |
| `No module named heat3d_capture` | the terminal is not in the tool's folder | `cd` into the `3DHeat-GameCapture` folder. |
| `No module named numpy` (or another package) | the packages are not installed, or you used a different Python | Run the `pip install -r requirements.txt` line again, with `.venv\Scripts\python`. |
| `'.venv' is not recognized` | you typed `/` in cmd | Use backslashes: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg is missing | See step 6, then open a new terminal. |

Next: [Home](Home) has a first example for each job.
