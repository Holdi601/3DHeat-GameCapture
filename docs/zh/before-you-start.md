---
title: 开始之前
nav_order: 1.5
lang: "zh"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# 开始之前 {#before-you-start}

第一次使用命令行？本页带你从零开始，用大约十分钟完成第一条可以正常运行的命令。

## 1. 安装 Python {#install-python}

GameCapture 是一个 Python 程序。你需要 **Python 3.10 或更高版本**。

1. 前往 [python.org/downloads](https://www.python.org/downloads/)，下载适用于 Windows 的最新版 Python。
2. 运行安装程序。在第一个界面，**勾选 “Add python.exe to PATH”**。如果不勾选，终端将找不到 Python。
3. 点击 *Install Now*。

或者在终端中运行：`winget install Python.Python.3.12`。

## 2. 安装 Git {#install-git}

Git 用于下载本工具。可以从 [git-scm.com](https://git-scm.com/download/win) 获取，也可以运行 `winget install Git.Git`。如果你不想使用 Git，可以在 [GitHub 页面](https://github.com/Holdi601/3DHeat-GameCapture) 上使用 *Code > Download ZIP*，然后解压。

## 3. 在一个文件夹中打开终端 {#open-a-terminal-in-a-folder}

终端是一个用来输入命令的窗口。这些页面使用 **PowerShell**，每台 Windows 电脑都自带它。

- 在文件资源管理器中打开该文件夹，点击地址栏，输入 `powershell` 并按回车。PowerShell 会**在该文件夹中**打开。
- 或者从开始菜单打开 PowerShell，然后用 `cd` 切换到某个文件夹：

```powershell
cd "C:\Games\Tools"
```

## 4. 阅读这些页面上的命令 {#read-the-commands-on-these-pages}

- 输入每一行命令，然后按回车。
- 尖括号中的文字是**占位符**：请在那里填入你自己的值，并去掉尖括号。`<recording>.mp4` 表示类似 `match1.mp4` 这样的文件名。
- 方括号中的文字，例如 `[--fps 5]`，是**可选项**。
- 包含空格的路径需要加引号：`"C:\My Videos\match1.mp4"`。
- 以 `#` 开头的行是注释，你不需要输入它们。

## 5. 获取工具及其软件包 {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` 会为本工具的软件包创建一个私有文件夹，使它们不会与你电脑上的其他东西混在一起。此后每条命令都以 `.venv\Scripts\python` 开头。

**你应该看到**最后一行显示 `Successfully installed ...`。检查工具是否正常工作：

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**你应该看到**一个命令列表，开头是 `usage: heat3d_capture`。

![--help 输出的命令列表](../assets/img/cli-help.svg)

你也可以先*激活*该文件夹，之后只需输入 `python`：

| 终端 | 激活 | 然后 |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

如果 PowerShell 提示 *running scripts is disabled*（禁止运行脚本），请运行一次
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`，或者跳过激活这一步。

## 6. 某些命令需要的额外程序 {#extra-programs-some-commands-need}

| 命令 | 需要 | 安装方法 |
|---|---|---|
| `hud` | **ffmpeg** 和 **ffprobe**（读取视频文件） | `winget install Gyan.FFmpeg`，然后打开一个新的终端。用 `ffmpeg -version` 检查。 |
| `reconstruct`、`locate` | **PyTorch**，需在其他软件包之前安装 | 从 [pytorch.org](https://pytorch.org/get-started/locally/) 获取适合你 GPU 的安装命令 |

## 出现问题时 {#when-something-goes-wrong}

| 你看到的 | 它的含义 | 怎么做 |
|---|---|---|
| `'python' is not recognized` | Python 不在 PATH 中 | 重新安装 Python 并勾选 PATH 选项，然后打开一个新的终端。 |
| `No module named heat3d_capture` | 终端不在工具的文件夹中 | `cd` 进入 `3DHeat-GameCapture` 文件夹。 |
| `No module named numpy`（或其他软件包） | 软件包未安装，或者你用了另一个 Python | 使用 `.venv\Scripts\python` 重新运行 `pip install -r requirements.txt` 这一行。 |
| `'.venv' is not recognized` | 你在 cmd 中输入了 `/` | 使用反斜杠：`.venv\Scripts\python`。 |
| `ffmpeg was not found on PATH` | 缺少 ffmpeg | 参见第 6 步，然后打开一个新的终端。 |

下一步：[首页](index.md) 中为每项工作提供了第一个示例。
