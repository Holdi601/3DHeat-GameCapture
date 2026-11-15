---
title: "始める前に"
nav_order: 1.5
lang: ja
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# 始める前に {#before-you-start}

コマンドラインは初めてですか？ このページは、ゼロから最初の動くコマンドまでを案内します。一度だけで、約10分かかります。

## 1. Pythonをインストール {#install-python}

GameCapture は Python のプログラムです。**Python 3.10 以降** が必要です。

1. [python.org/downloads](https://www.python.org/downloads/) を開き、Windows 向けの最新の Python をダウンロードします。
2. インストーラーを実行します。最初の画面で **「Add python.exe to PATH」にチェックを入れてください**。チェックがないと、ターミナルが Python を見つけられません。
3. *Install Now* をクリックします。

または、ターミナルで: `winget install Python.Python.3.12`。

## 2. Git をインストール {#install-git}

Git はツールをダウンロードするために使います。[git-scm.com](https://git-scm.com/download/win) から入手するか、`winget install Git.Git` を実行します。Git を使わない場合は、[GitHubのページ](https://github.com/Holdi601/3DHeat-GameCapture) で *Code > Download ZIP* を使い、展開してください。

## 3. フォルダーでターミナルを開く {#open-a-terminal-in-a-folder}

ターミナルとは、コマンドを入力するウィンドウのことです。このページは、どの Windows のPCにもある **PowerShell** を使います。

- エクスプローラーでフォルダーを開き、アドレスバーをクリックして `powershell` と入力し、Enterを押します。PowerShell が **そのフォルダーの中で** 開きます。
- または、スタートメニューから PowerShell を開き、`cd` でフォルダーに移動します:

```powershell
cd "C:\Games\Tools"
```

## 4. このページのコマンドの読み方 {#read-the-commands-on-these-pages}

- コマンドの行を入力し、Enterを押します。
- 山括弧の文字は **置き換え用の場所** です。山括弧を付けずに、自分の値を入れてください。`<recording>.mp4` は `match1.mp4` のようなファイル名を意味します。
- `[--fps 5]` のように角括弧の文字は **省略可能** です。
- スペースを含むパスには引用符が必要です: `"C:\My Videos\match1.mp4"`。
- `#` で始まる行はコメントです。入力しません。

## 5. ツールとそのパッケージを入手 {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` は、ツールのパッケージのための専用のフォルダーを作ります。そのため、PCの他のものと混ざりません。以後のコマンドはすべて `.venv\Scripts\python` で始まります。

**表示を確認:** 最後の行が `Successfully installed ...` になるはずです。ツールが動くか確かめます:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**次のような表示が出るはずです:** `usage: heat3d_capture` で始まるコマンドの一覧。

![--help が表示するコマンドの一覧](../assets/img/cli-help.svg)

フォルダーを一度 *有効化* しておけば、`python` と入力するだけで済みます:

| ターミナル | 有効化 | その後 |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

PowerShell が *running scripts is disabled*（スクリプトの実行は無効）と言う場合は、一度だけ `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` を実行するか、有効化を省いてください。

## 6. 一部のコマンドが必要とする追加のプログラム {#extra-programs-some-commands-need}

| コマンド | 必要なもの | インストール |
|---|---|---|
| `hud` | **ffmpeg** と **ffprobe**（動画ファイルを読む） | `winget install Gyan.FFmpeg` を実行し、新しいターミナルを開く。`ffmpeg -version` で確認。 |
| `reconstruct`、`locate` | **PyTorch**。ほかのパッケージより先に入れる | GPU に合わせた [pytorch.org](https://pytorch.org/get-started/locally/) のコマンド |

## うまくいかないとき {#when-something-goes-wrong}

| 表示 | 意味 | 対処 |
|---|---|---|
| `'python' is not recognized` | Python が PATH にない | PATH のチェックを入れて Python を入れ直し、新しいターミナルを開く。 |
| `No module named heat3d_capture` | ターミナルがツールのフォルダーにない | `3DHeat-GameCapture` フォルダーへ `cd` で移動する。 |
| `No module named numpy`（または別のパッケージ） | パッケージが入っていない、または別の Python を使った | `.venv\Scripts\python` で `pip install -r requirements.txt` の行をもう一度実行する。 |
| `'.venv' is not recognized` | cmd で `/` を入力した | バックスラッシュを使う: `.venv\Scripts\python`。 |
| `ffmpeg was not found on PATH` | ffmpeg がない | 手順6を見て、新しいターミナルを開く。 |

次へ: [ホーム](index.md) に、それぞれの仕事の最初の例があります。
