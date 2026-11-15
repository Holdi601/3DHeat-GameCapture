---
title: "Aktualizacje"
nav_order: 10
lang: "pl"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Aktualizacje {#updates}

3DHeat GameCapture sprawdza wydania GitHub tego repozytorium przy starcie, mówi, kiedy wyszła nowsza wersja,
i proponuje aktualizację. Kod: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Kiedy działa sprawdzanie {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - przed uruchomieniem polecenia.
- `python -m heat3d_capture.ui` (i `scan.bat`) - przed otwarciem okna.
- `python -m heat3d_update` - na żądanie, zawsze pytając GitHub od nowa.

## Jak działa sprawdzanie {#how-the-check-works}

- Zainstalowana wersja to plik `VERSION` w katalogu głównym repozytorium (na przykład `1.0.1`).
- Najnowsze wydanie pytane jest pod adresem
  `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest`, z limitem **5 sekund**. Wolna
  sieć nigdy nie zatrzyma narzędzia dłużej.
- Odpowiedź jest przechowywana w pamięci podręcznej przez **6 godzin** w
  `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` (`~/.cache/3DHeat/...` bez `LOCALAPPDATA`).
  Każde narzędzie 3DHeat ma własny plik pamięci podręcznej. „Brak wydania jeszcze” (HTTP 404) zapisuje się jak
  każda odpowiedź; inne błędy nie są zapisywane i po prostu oznaczają brak powiadomienia.
- Wersje porównuje się liczbowo (`v1.2.3` albo `1.2.3`; wszystko po `-` lub `+` jest ignorowane).
- Bez sieci, z limitem zapytań albo za proxy narzędzie działa dalej z wersją, którą ma.

## Co się dzieje, gdy wyszło nowsze wydanie {#what-happens-when-a-newer-release-is-out}

Przy starcie wypisuje na strumień błędów:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Gdy jest terminal, na którym można odpowiedzieć, pyta `Update now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja`
  znaczą tak). Po udanej aktualizacji **to samo polecenie uruchamia się ponownie**, już na nowym kodzie.
- Bez terminala (potok, uruchomienie zaplanowane) wypisuje `Run python -m heat3d_update in <folder> to update.`
  i działa dalej bez zmian.

## Jak stosuje się aktualizację {#how-an-update-is-applied}

Zależy od tego, jak zainstalowano narzędzia:

- **Klon git** (folder `.git` i `git` w PATH): `git pull --ff-only`. Odmawia, dopóki w kopii są lokalne zmiany
  w śledzonych plikach - to czyjaś praca; najpierw zatwierdź je albo odłóż (stash).
- **Pobrana kopia**: archiwum źródeł wydania zostaje pobrane, rozpakowane do folderu tymczasowego (wpisy spoza
  folderu archiwum są pomijane) i **sprawdzane, czy jest wersją, za którą się podaje** według pliku `VERSION`.
  Potem jego pliki kopiuje się na ten folder. W pakietach Pythona samego wydania (foldery `heat3d_*` na górze
  repozytorium, a jeden poziom niżej dla starego układu monorepo) usuwa się moduły `.py`, których wydanie już nie
  ma, tak by przestarzały moduł nie przesłaniał swojego następcy.

Twoje pliki - nagrania, pliki okrążeń, ustawienia, eksporty, `.venv` - nigdy nie są ruszane: zapisuje się tylko
pliki, które są częścią wydania.

## Ręcznie {#by-hand}

```bash
python -m heat3d_update            # check and update
python -m heat3d_update --check    # only say whether a newer release is out
```

Wypisuje `Up to date: <version>.`, `No release found ... offline, or nothing published yet.` albo nową wersję i
to, co zrobiło. Kod wyjścia 1, gdy nie udało się zastosować aktualizacji.

## Wyłączanie {#switching-it-off}

Ustaw **`HEAT3D_NO_UPDATE=1`** (dowolna wartość poza pustą, `0`, `false`, `no`). To wyłącza sprawdzanie i
powiadomienie przy starcie. `python -m heat3d_update` uruchomiony ręcznie nadal sprawdza.
