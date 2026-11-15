---
title: 시작하기 전에
nav_order: 1.5
lang: ko
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# 시작하기 전에 {#before-you-start}

명령줄이 처음입니까? 이 페이지는 약 10분 만에 아무것도 없는 상태에서 첫 명령이 작동하기까지 안내합니다. 한 번만 하면 됩니다.

## 1. Python 설치 {#install-python}

GameCapture는 Python 프로그램입니다. **Python 3.10 이상**이 필요합니다.

1. [python.org/downloads](https://www.python.org/downloads/)에 가서 Windows용 최신 Python을 내려받으세요.
2. 설치 프로그램을 실행하세요. 첫 화면에서 **"Add python.exe to PATH"를 체크하세요**. 체크하지 않으면 터미널이 Python을 찾지 못합니다.
3. *Install Now*를 누르세요.

또는 터미널에서: `winget install Python.Python.3.12`.

## 2. Git 설치 {#install-git}

Git은 도구를 내려받는 데 씁니다. [git-scm.com](https://git-scm.com/download/win)에서 받거나, `winget install Git.Git`을 실행하세요. Git을 쓰지 않으려면 [GitHub 페이지](https://github.com/Holdi601/3DHeat-GameCapture)에서 *Code > Download ZIP*을 누르고 압축을 푸세요.

## 3. 폴더에서 터미널 열기 {#open-a-terminal-in-a-folder}

터미널은 명령을 입력하는 창입니다. 이 페이지들은 **PowerShell**을 씁니다. 모든 Windows PC에 있습니다.

- 파일 탐색기에서 폴더를 열고, 주소창을 클릭한 뒤 `powershell`을 입력하고 Enter를 누르세요. PowerShell이 **그 폴더에서** 열립니다.
- 또는 시작 메뉴에서 PowerShell을 열고 `cd`로 폴더를 옮기세요:

```powershell
cd "C:\Games\Tools"
```

## 4. 이 페이지들의 명령 읽는 법 {#read-the-commands-on-these-pages}

- 명령 줄을 입력하고 Enter를 누르세요.
- 꺾쇠괄호 안의 글은 **자리 표시자**입니다. 괄호 없이 본인의 값을 넣으세요. `<recording>.mp4`는 `match1.mp4` 같은 파일 이름을 뜻합니다.
- `[--fps 5]`처럼 대괄호 안의 글은 **선택 사항**입니다.
- 공백이 있는 경로에는 따옴표가 필요합니다: `"C:\My Videos\match1.mp4"`.
- `#`으로 시작하는 줄은 주석입니다. 입력하지 않습니다.

## 5. 도구와 패키지 받기 {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv`는 도구의 패키지를 위한 전용 폴더를 만듭니다. 그래서 PC의 다른 것과 섞이지 않습니다. 이후의 모든 명령은 `.venv\Scripts\python`으로 시작합니다.

**이렇게 보여야 합니다** 마지막 줄이 `Successfully installed ...`입니다. 도구가 작동하는지 확인하세요:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**이렇게 보여야 합니다** `usage: heat3d_capture`로 시작하는 명령 목록입니다.

![--help가 출력하는 명령 목록](../assets/img/cli-help.svg)

폴더를 *활성화*해 두고 `python`만 입력할 수도 있습니다:

| 터미널 | 활성화 | 그다음 |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

PowerShell이 *running scripts is disabled*(스크립트 실행이 비활성화됨)라고 하면, `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 실행하거나, 활성화를 건너뛰세요.

## 6. 일부 명령이 필요로 하는 추가 프로그램 {#extra-programs-some-commands-need}

| 명령 | 필요한 것 | 설치 |
|---|---|---|
| `hud` | **ffmpeg**과 **ffprobe**(영상 파일 읽기) | `winget install Gyan.FFmpeg`을 실행한 뒤 새 터미널을 여세요. `ffmpeg -version`으로 확인합니다. |
| `reconstruct`, `locate` | **PyTorch**, 다른 패키지보다 먼저 설치 | 본인의 GPU에 맞는 명령을 [pytorch.org](https://pytorch.org/get-started/locally/)에서 받으세요 |

## 문제가 생겼을 때 {#when-something-goes-wrong}

| 보이는 것 | 뜻 | 할 일 |
|---|---|---|
| `'python' is not recognized` | Python이 PATH에 없습니다 | PATH 체크를 하고 Python을 다시 설치한 뒤 새 터미널을 여세요. |
| `No module named heat3d_capture` | 터미널이 도구의 폴더에 있지 않습니다 | `3DHeat-GameCapture` 폴더로 `cd` 하세요. |
| `No module named numpy` (또는 다른 패키지) | 패키지가 설치되지 않았거나, 다른 Python을 썼습니다 | `.venv\Scripts\python`으로 `pip install -r requirements.txt` 줄을 다시 실행하세요. |
| `'.venv' is not recognized` | cmd에서 `/`를 입력했습니다 | 역슬래시를 쓰세요: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg이 없습니다 | 6단계를 보고, 그다음 새 터미널을 여세요. |

다음: [홈](index.md)에 각 일의 첫 예시가 있습니다.
