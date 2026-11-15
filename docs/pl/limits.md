---
title: Ograniczenia i sprawdzenie
nav_order: 9
lang: "pl"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Ograniczenia i to, co zostało sprawdzone {#limits-and-what-is-verified}

Szczera lista: czego narzędzia nie robią i czego nie sprawdzono na działającej grze.

## Telemetria {#telemetry}

| Rejestrator | Stan |
|---|---|
| Forza | Oparty na oficjalnej dokumentacji Data Out; układ jest wykrywany z samych pakietów. Czytnik `.tele.gz` z FH Companion w przeglądarce sprawdzono na prawdziwych okrążeniach. |
| AC, ACC, AC EVO, AC Rally | Przetestowane na syntetycznych stronach zbudowanych z opublikowanych układów. **Nie uruchamiano jeszcze na działających grach.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Przetestowane na pakietach zbudowanych z udokumentowanych układów. **Nie uruchamiano jeszcze na działających grach.** Osie, postawa i jednostki prędkości RBR nie są udokumentowane i są obsługiwane na podstawie danych. |
| BeamNG.drive | Rejestrator przetestowany na pakietach zbudowanych ze struktury moda. **Mod nie był uruchamiany w grze.** |
| Trackmania | Czytnik CSV w przeglądarce przetestowany. **Wtyczka nie była uruchamiana w grze.** Ładuje się tylko w trybie dewelopera Openplanet. |
| iRacing | Czytnik `.ibt` w przeglądarce przetestowany na syntetycznym pliku. |

Inne ograniczenia telemetrii:

- Normalizacja poślizgu w Forzy nie jest udokumentowana; poślizg Kunosa jest skalowany typowym szczytem dla asfaltu, co jest przybliżeniem.
- Zwrot niektórych bocznych osi w układzie samochodu (Kunos, DiRT) jest udokumentowany w obu kierunkach; wielkość kąta dryfu jest wiarygodna, jego znak - nie.
- Żadna z gier rajdowych nie wysyła poślizgu kół; jest wyliczany w przeglądarce. RBR nie wysyła prędkości kół.
- Nawierzchnia odcinka rajdowego jest zapisywana tylko wtedy, gdy podano `--surface`; w przeciwnym razie plik jej nie wymienia, a przeglądarka ją wnioskuje (nazwa odcinka lub wydarzenia, potem styl jazdy, domyślnie luźno).
- Wykrywanie okrążeń bez licznika okrążeń (AC EVO, AC Rally, BeamNG) używa punktu, w którym zaczęto nagrywanie, jako linii; zacznij więc nagrywanie na linii startu.
- Reset pojazdu w BeamNG zamyka okrążenie otwarte w tym momencie: jest zapisywane jako częściowy przejazd, gdy pokryło minimalny dystans (300 m), a w przeciwnym razie jest odrzucane.
- `route` zapisuje co 2 sekundy lub mniej podczas jazdy; awaria lub zabicie procesu traci co najwyżej pozycje od ostatniego zapisu.
- Forza Horizon nie wysyła nazwy toru, więc pliki okrążeń Forzy mają `"track": null`; Forza Motorsport (2023) wysyła tylko numer, zachowywany jako `lap.trackOrdinal`.

## Rekonstrukcja {#reconstruction}

- **Głębia jest szacowana, a nie odczytywana.** To sufit całego podejścia i cena za to, że proces gry nigdy nie jest dotykany.
- **Pole widzenia jest zakładane, a nie mierzone.** Zbyt wąskie i poziom rekonstruuje się głębiej, niż jest.
- **Skala globalna** pochodzi z zakładanej wysokości kamery (1,15 m w oknie) albo z telemetrii. Jest mierzona na pierwszej klatce kluczowej; gdy nie ma na niej użytecznego gruntu, sprawdza się kolejne klatki kluczowe (do 30), a skala znaleziona później jest stosowana do całego poziomu przy zapisie. Linia `Size:` w oknie mówi, co się stało; gdy nie znaleziono żadnego gruntu, skan pozostaje bez jednostek. Rozmiar woksela jest wtedy w jednostkach pierwszej klatki, więc jego rozmiar w metrach różni się od ustawienia. Rekonstrukcje offline są w jednostkach samego rozwiązania.
- **Domknięcie pętli jest wyłączone** i po włączeniu w kodzie nie jest grafem pozycji; dryf ogranicza tylko jakość śledzenia klatka po klatce.
- **Korekcja wiązki w oknie istnieje, ale nie jest podłączona**; na prawdziwych nagraniach się załamała.
- **Powierzchnia jest ważoną zajętością, a nie TSDF**: cienkie struktury i wolna przestrzeń wychodzą gorzej niż przy TSDF.
- **Brak atlasu tekstur.** Kolor jest na wierzchołkach (`COLOR_0`), mieszany z 4 najlepszych widoków spośród 160 zachowanych klatek. Test zasłonięcia jest zgrubny: sprawdza się go względem wierzchołków własnej siatki w buforze głębi o rozdzielczości 2 pikseli, więc zasłaniacza, którego siatka nie zawiera (przejeżdżający samochód), nie wykrywa się.
- **Woda nigdy nie jest oznaczana**; wszystko jest gruntem albo strukturą.
- **Rozwiązanie feed-forward nie działa na żywo**: wymaga najpierw nagrania. Adaptacyjne ponowne rozwiązywanie trudnych fragmentów nie jest zbudowane.
- **Pozy z telemetrii** umieszczają kamerę przy samochodzie (przesunięcie kamery trzeciej osoby jest nieznane). Pozycje są przyjmowane tak, jak wysyła je Forza (Y w górę, jak w plikach okrążeń); kierunki yaw, pitch i roll odczytano z zapisanych okrążeń (kierunek jazdy, nachylenie, która strona zawieszenia się ściska), a nie z kamery działającej gry.
- Nakładka nie może rysować nad **pełnym ekranem na wyłączność**; użyj trybu bezramkowego okna.
- Skróty globalne, nakładka przepuszczająca kliknięcia i przechwytywanie na żywo działają **tylko w Windows**.
- Zamknięcie okna nie pyta o zapis.

## Co jest mierzone {#what-is-measured}

- `tests/test_accuracy.py`: syntetyczny pokój ze znaną ścieżką i analityczną głębią - umieszczone klatki, błąd ścieżki, przejechany dystans, rozmiar pokoju, powierzchnia na ścianach ([Rekonstrukcja poziomu](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: droga o znanej szerokości, przejechana poza środkiem, odtwarza swoją szerokość.
- `tests/test_track_scale.py`: wyodrębnianie powierzchni w skali toru wyścigowego, pamięć proporcjonalna do przeskanowanego obszaru, bloki łączące się w jedną powierzchnię.
- `tests/test_glb.py` oraz własne testy przeglądarki: kontrakt `.glb` z obu stron.
- Jak sieć głębi radzi sobie z prawdziwą rozgrywką, nie może rozstrzygnąć syntetyczna scena i nie jest to mierzone przez zestaw testów.
