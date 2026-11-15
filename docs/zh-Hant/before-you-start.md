---
title: "開始之前"
nav_order: 1.5
lang: zh-Hant
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# 開始之前 {#before-you-start}

第一次使用命令列？這一頁會帶你從零開始，約十分鐘內完成第一個可用的命令。

## 1. 安裝 Python {#install-python}

GameCapture 是一個 Python 程式。你需要 **Python 3.10 或更新版本**。

1. 前往 [python.org/downloads](https://www.python.org/downloads/)，下載適用於 Windows 的最新版 Python。
2. 執行安裝程式。在第一個畫面，**勾選 "Add python.exe to PATH"**。若不勾選，終端機將找不到 Python。
3. 點擊 *Install Now*。

或者在終端機中執行：`winget install Python.Python.3.12`。

## 2. 安裝 Git {#install-git}

Git 用來下載這個工具。可以從 [git-scm.com](https://git-scm.com/download/win) 取得，或執行
`winget install Git.Git`。若你不想使用 Git，請到 [GitHub 頁面](https://github.com/Holdi601/3DHeat-GameCapture)，
使用 *Code > Download ZIP*，然後解壓縮。

## 3. 在資料夾中開啟終端機 {#open-a-terminal-in-a-folder}

終端機是讓你輸入命令的視窗。這些頁面使用 **PowerShell**，每台 Windows 電腦都有它。

- 在檔案總管中開啟該資料夾，點一下網址列，輸入 `powershell` 再按 Enter。
  PowerShell 會**在該資料夾中**開啟。
- 或從開始功能表開啟 PowerShell，然後用 `cd` 前往某個資料夾：

```powershell
cd "C:\Games\Tools"
```

## 4. 閱讀這些頁面中的命令 {#read-the-commands-on-these-pages}

- 輸入每一行命令，然後按 Enter。
- 角括號中的文字是**佔位符**：請在那裡放入你自己的值，不要輸入括號。
  `<recording>.mp4` 表示像 `match1.mp4` 這樣的檔名。
- 方括號中的文字，例如 `[--fps 5]`，是**選用**的。
- 含有空格的路徑需要引號：`"C:\My Videos\match1.mp4"`。
- 以 `#` 開頭的行是註解，你不需要輸入。

## 5. 取得工具與其套件 {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` 會為工具的套件建立一個私人資料夾，讓它們不會與電腦上的其他東西混在一起。之後每個命令都以 `.venv\Scripts\python` 開頭。

**你應該會看到**最後一行顯示 `Successfully installed ...`。確認工具可以運作：

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**你應該會看到**以 `usage: heat3d_capture` 開頭的命令清單。

![--help 所印出的命令清單](../assets/img/cli-help.svg)

你也可以*啟用*該資料夾一次，之後只需輸入 `python`：

| 終端機 | 啟用 | 然後 |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

若 PowerShell 顯示 *running scripts is disabled*，請執行一次
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，或略過啟用這一步。

## 6. 部分命令需要的額外程式 {#extra-programs-some-commands-need}

| 命令 | 需要 | 安裝方式 |
|---|---|---|
| `hud` | **ffmpeg** 與 **ffprobe**（讀取影片檔） | `winget install Gyan.FFmpeg`，然後開啟新的終端機。以 `ffmpeg -version` 檢查。 |
| `reconstruct`、`locate` | **PyTorch**，需在其他套件之前安裝 | 到 [pytorch.org](https://pytorch.org/get-started/locally/) 取得適合你 GPU 的命令 |

## 出問題時 {#when-something-goes-wrong}

| 你看到的 | 代表什麼 | 該怎麼做 |
|---|---|---|
| `'python' is not recognized` | Python 不在 PATH 中 | 重新安裝 Python 並勾選 PATH，然後開啟新的終端機。 |
| `No module named heat3d_capture` | 終端機不在工具的資料夾中 | `cd` 進入 `3DHeat-GameCapture` 資料夾。 |
| `No module named numpy`（或其他套件） | 套件未安裝，或你使用了另一個 Python | 使用 `.venv\Scripts\python` 再執行一次 `pip install -r requirements.txt` 那一行。 |
| `'.venv' is not recognized` | 你在 cmd 中輸入了 `/` | 請使用反斜線：`.venv\Scripts\python`。 |
| `ffmpeg was not found on PATH` | 缺少 ffmpeg | 請見第 6 步，然後開啟新的終端機。 |

下一步：[首頁](index.md) 為每項工作提供了第一個範例。
