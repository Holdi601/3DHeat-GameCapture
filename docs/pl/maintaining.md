---
title: "Utrzymanie tych dokumentów"
nav_order: 96
lang: "pl"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Utrzymanie tych dokumentów {#maintaining-these-docs}

Lista kontrolna dla każdego wydania, tak by kod, strony po angielsku i ich tłumaczenia zostawały w zgodzie.
Wykonuj kroki po kolei.

1. **Odśwież wygenerowane strony.**
   - `python tools/gen_docs_reference.py` przepisuje [Opis poleceń](../cli-reference.md) na podstawie `--help`
     i list kolumn w kodzie. `--check` kończy się kodem 1, gdy strona jest nieaktualna: uruchamiaj go przed
     każdym wydaniem.
   - `python tools/docs_diagrams.py` ponownie rysuje diagramy w `docs/assets/img/`; `--strings` dodatkowo
     odświeża `docs/assets/i18n/en.json`, czyli etykiety do przetłumaczenia.
   - `python tools/sync_wiki.py` odtwarza kopię wiki GitHub w `docs/wiki/`.
2. **Wypisz, co się zmieniło od ostatniego wydania.** `git log --oneline v$(cat VERSION)..` (ostatni tag to
   `v` + wersja z `VERSION`). Dla każdego nowego lub zmienionego polecenia, opcji, kolumny wyniku albo
   zachowania: zaktualizuj jego stronę i dodaj wiersz do tabeli *Docs* w `CHANGELOG.md`.
3. **Niezależny przegląd.** Ktoś, kto nie pisał zmiany, czyta zmienione strony i diagramy oczami trzech
   czytelników: **początkującego** (nigdy nie używał wiersza poleceń: czy umie zainstalować i uruchomić?),
   **ośmiolatka** (czy strona prostymi słowami mówi, czym to jest i po co?) oraz **profesjonalisty** (czy
   opcje, wartości domyślne i kolumny zgadzają się z kodem?). Sprawdź, czy żadna strona nie wymienia
   prawdziwych poziomów, map, graczy ani nagrań: przykłady są syntetyczne, a twierdzenia o weryfikacji
   podają tylko metodę i tolerancję.
4. **Popraw uwagi z przeglądu.**
5. **Przetłumacz.** Każda przetłumaczona strona zapisuje skrót (hash) angielskiej strony, z której powstała.
   Przetłumacz ponownie strony, których angielski skrót się zmienił, oraz zmienione etykiety diagramów; potem
   sprawdź każdy język: czy jest zrozumiały dla trzech czytelników, czy etykiety diagramów są poprawne, czy
   słowa zgadzają się ze zlokalizowanym interfejsem przeglądarki.
6. **Wysyłaj dopiero po zgodzie właściciela.** Potem oznacz wydanie tagiem `v<VERSION>`.

Nowy w uruchamianiu tych poleceń? [Zanim zaczniesz](before-you-start.md) opisuje Pythona i wiersz poleceń.

## Tłumaczenia: polecenia {#translations-the-commands}

Strony są przetłumaczone na 40 języków przeglądarki 3DHeat: angielski w `docs/`, każdy inny język w
`docs/<lang>/` z tymi samymi nazwami plików. `tools/docs_i18n.py` prowadzi całą ewidencję:

```bash
python tools/docs_i18n.py hashes             # po każdej zmianie w języku angielskim: zapisz skrót każdej strony
python tools/docs_i18n.py svg-strings        # po każdej zmianie obrazka: etykiety do przetłumaczenia
python tools/docs_i18n.py status             # dla każdego języka: aktualne, nieaktualne i brakujące strony
python tools/docs_i18n.py todo --lang de     # niemieckie strony do (ponownego) przetłumaczenia
python tools/docs_i18n.py svg-build --lang de    # niemieckie obrazki z docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # oznacz niemieckie strony skrótem angielskiego źródła
python tools/docs_i18n.py check              # kończy się kodem 1, gdy skróty lub etykiety są nieaktualne
```

Tłumacz tylko to, co wypisuje `todo`: Markdown, linki, kod, nazwy plików i kolumn zostają bez zmian,
tłumacz tytuły i opisy obrazków, a przyciski i panele przeglądarki 3DHeat nazywaj jej własnymi słowami
(z `src/i18n/locales/<lang>/`). Wygenerowane strony opisów i obrazki terminala pozostają po angielsku. Na
stronie nieaktualne tłumaczenie to mówi i linkuje stronę angielską; brakujące przechodzi na angielski. Menu
języków w nagłówku i przekierowanie strony głównej według języka przeglądarki pochodzą z `docs/_includes/`.
