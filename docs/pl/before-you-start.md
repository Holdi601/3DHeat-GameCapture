---
title: "Zanim zaczniesz"
nav_order: 1.5
lang: pl
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Zanim zaczniesz {#before-you-start}

Nigdy nie używałeś wiersza poleceń? Ta strona przeprowadzi cię od zera do pierwszego działającego polecenia.
Zajmie to około dziesięciu minut, tylko raz.

## 1. Zainstaluj Pythona {#install-python}

GameCapture to program w Pythonie. Potrzebujesz **Pythona 3.10 lub nowszego**.

1. Wejdź na [python.org/downloads](https://www.python.org/downloads/) i pobierz najnowszego
   Pythona dla Windows.
2. Uruchom instalator. Na pierwszym ekranie **zaznacz „Add python.exe to PATH”**. Bez tej opcji
   terminal nie znajdzie Pythona.
3. Kliknij *Install Now*.

Albo w terminalu: `winget install Python.Python.3.12`.

## 2. Zainstaluj Git {#install-git}

Git pobiera narzędzie. Weź go z [git-scm.com](https://git-scm.com/download/win) albo uruchom
`winget install Git.Git`. Jeśli nie chcesz Gita, użyj *Code > Download ZIP* na
[stronie GitHub](https://github.com/Holdi601/3DHeat-GameCapture) i rozpakuj plik.

## 3. Otwórz terminal w folderze {#open-a-terminal-in-a-folder}

Terminal to okno, w którym wpisujesz polecenia. Te strony używają **PowerShell**, który jest na każdym
komputerze z Windows.

- Otwórz folder w Eksploratorze plików, kliknij pasek adresu, wpisz `powershell` i naciśnij Enter.
  PowerShell otworzy się **w tym folderze**.
- Albo otwórz PowerShell z menu Start i przejdź do folderu poleceniem `cd`:

```powershell
cd "C:\Games\Tools"
```

## 4. Jak czytać polecenia na tych stronach {#read-the-commands-on-these-pages}

- Wpisz każdą linię polecenia i naciśnij Enter.
- Tekst w nawiasach ostrokątnych to **symbol zastępczy**: wpisz tam własną wartość, bez nawiasów.
  `<recording>.mp4` oznacza plik o nazwie takiej jak `match1.mp4`.
- Tekst w nawiasach kwadratowych, na przykład `[--fps 5]`, jest **opcjonalny**.
- Ścieżka ze spacjami wymaga cudzysłowów: `"C:\My Videos\match1.mp4"`.
- Linie zaczynające się od `#` to komentarze. Nie wpisuj ich.

## 5. Pobierz narzędzie i jego pakiety {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` tworzy prywatny folder na pakiety narzędzia, żeby nie mieszały się z niczym innym
na twoim komputerze. Każde polecenie zaczyna się potem od `.venv\Scripts\python`.

**Powinieneś zobaczyć**, że ostatnia linia mówi `Successfully installed ...`. Sprawdź, czy narzędzie działa:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Powinieneś zobaczyć** listę poleceń, zaczynającą się od `usage: heat3d_capture`.

![Lista poleceń, którą wypisuje --help](../assets/img/cli-help.svg)

Możesz też raz *aktywować* folder i potem wpisywać samo `python`:

| Terminal | Aktywacja | Potem |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Jeśli PowerShell napisze *running scripts is disabled*, uruchom raz
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` albo pomiń aktywację.

## 6. Dodatkowe programy, których potrzebują niektóre polecenia {#extra-programs-some-commands-need}

| Polecenie | Potrzebuje | Instalacja |
|---|---|---|
| `hud` | **ffmpeg** i **ffprobe** (czytają pliki wideo) | `winget install Gyan.FFmpeg`, potem otwórz nowy terminal. Sprawdź poleceniem `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, zainstalowany przed innymi pakietami | polecenie z [pytorch.org](https://pytorch.org/get-started/locally/) dla twojej karty graficznej |

## Gdy coś pójdzie nie tak {#when-something-goes-wrong}

| Widzisz | Co to znaczy | Co zrobić |
|---|---|---|
| `'python' is not recognized` | Python nie jest w PATH | Zainstaluj Pythona ponownie z zaznaczeniem PATH, potem otwórz nowy terminal. |
| `No module named heat3d_capture` | terminal nie jest w folderze narzędzia | Wejdź poleceniem `cd` do folderu `3DHeat-GameCapture`. |
| `No module named numpy` (albo inny pakiet) | pakiety nie są zainstalowane albo użyto innego Pythona | Uruchom ponownie linię `pip install -r requirements.txt`, z `.venv\Scripts\python`. |
| `'.venv' is not recognized` | w cmd wpisano `/` | Użyj backslashy: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | brakuje ffmpeg | Zobacz krok 6, potem otwórz nowy terminal. |

Dalej: [Start](index.md) ma pierwszy przykład dla każdego zadania.
