---
title: Okno skanowania
nav_order: 1
lang: "pl"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Okno skanowania {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Okno jest cienkim widokiem nad `scan/session.py` i `scan/reconstruct.py`; nie zawiera
żadnej logiki skanowania ani geometrii.

Etykiety, przyciski i pola na poniższych listach są napisane tak, jak widać je w oknie (po angielsku), a objaśnienia są po polsku.

## Uruchamianie {#starting-up}

1. **Sprawdzenie aktualizacji** - zob. [Aktualizacje](updates.md).
2. **Sprawdzenie zależności** - każdy pakiet potrzebny skanerowi jest sprawdzany, zanim cokolwiek zostanie zaimportowane; brakujące są wypisywane wraz z tym, do czego służą, i rozmiarem pobrania, a instalowane dopiero po **Download and install**. Cancel kończy działanie bez zmian. Zob. [Środowisko i zależności](runtime.md#first-run-preflight).
3. **Okno** - „3DHeat — Level scanner”, 1420 x 900, styl Fusion z Qt.
4. **Sprawdzenie sprzętu** - wybierany jest najlepszy silnik wnioskowania, model głębi się ładuje, a jego przepustowość mierzy się na 6 klatkach; pole werdyktu w lewym górnym rogu mówi, jak będzie przebiegać skan (zob. [Środowisko](runtime.md#what-to-expect-from-this-machine)).
5. **Skróty globalne** rejestrują się na końcu.

### Gdy nie ma jeszcze modelu głębi {#when-there-is-no-depth-model-yet}

Jeśli w `models/` nie ma `depth-*.onnx`, werdykt brzmi **„One more thing to set up.”**, przycisk Start jest nieaktywny, a pojawia się przycisk **Set up the depth model**. Ten przycisk:

- sprawdza PyTorch, `transformers` i `onnxscript` (razem około 945 MB) i pyta przed instalacją;
- uruchamia `tools/export_onnx.py --size small` jako osobny proces (dzięki temu PyTorch nigdy nie zostaje w pamięci skanera), z limitem 30 minut. Okno w tym czasie nie reaguje;
- po sukcesie ponownie uruchamia sprawdzenie sprzętu; po niepowodzeniu pokazuje ostatnie 600 znaków wyjścia konwertera.

Gdy obecnych jest kilka modeli, wybór zależy od **licencji, a nie od nazwy pliku**: `depth-small-*` (Apache-2.0, dozwolone użycie komercyjne), gdy jest taki plik; potem Base, a dopiero potem Large (oba niekomercyjne). Pole werdyktu i szara linia pod przyciskami mówią, który plik jest w użyciu, jego licencję i inne obecne, ale nieużywane pliki modeli - na przykład `Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used: depth-base-518.onnx`. Aby skanować z Base, przenieś plik Small poza `models/`.

## Lewa kolumna: ustawienia {#left-column-settings}

| Grupa | Kontrolka | Domyślnie | Zakres / wartości | Co robi |
|---|---|---|---|---|
| (góra) | Pole werdyktu | „Checking your graphics card…” | zielone, bursztynowe lub czerwone według poziomu | Nagłówek, `<device> via <API> — N views per second`, jedna uwaga oraz `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Skąd biorą się klatki |
| | Which | `1` | numer monitora / tytuł okna / ścieżka do wideo | `monitor:<n>`, `window:<title>` albo ścieżka pliku |
| | Choose file… | widoczne dla wideo | `*.mp4 *.mkv *.avi *.mov` | Wstawia ścieżkę |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Rozdzielczość przechwytywania i to, jak selektywnie wybiera się klatki kluczowe (niżej); pod spodem pokazane jest jednozdaniowe podsumowanie |
| | Game field of view | 90° | 30-140° | **Poziome** pole widzenia gry. Zbyt wąskie - poziom rekonstruuje się głębiej, niż jest; zbyt szerokie - spłaszcza się. Gry wyścigowe są bliżej 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, krok 0.05 | Rozmiar woksela powierzchni. Mniejszy to dokładniej i cięższe |
| Stop after | Time | bez limitu | 0-120 min | Kończy skan po tym czasie (0 = bez limitu) |
| | Views kept | 3000 | 0-100,000 | Kończy skan po tylu klatkach kluczowych jako zabezpieczenie pamięci (0 = bez limitu) |
| What to ignore | Ignore HUD and anything on the camera | włączone | | Uczy się i maskuje HUD, celownik, broń, maskę silnika, kabinę ([Przechwytywanie](reconstruction-capture.md#what-is-not-the-world)). Linia pod nią mówi, co detektor w tej chwili decyduje |
| While you play | Show feedback over the game | włączone | | Otwiera nakładkę przepuszczającą kliknięcia podczas skanowania. Podpowiedź pod nią: uruchom grę w **borderless windowed**; pełnego ekranu na wyłączność nic nie może przykryć |
| Racing telemetry (Forza) | Listen for position data | wyłączone | | Bierze ścieżkę kamery z Forza Data Out zamiast ją szacować z obrazu ([Poza](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Port Data Out |
| | (status line) | | | `N packets — poses come from the game, not from the picture` albo `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Uruchamia lub zatrzymuje; pokazuje skrót, gdy został zarejestrowany |
| | **Set up the depth model** | ukryte | | Zob. wyżej |
| | **Save level…** | nieaktywne | | Włącza się po skanie, który dał woksele powierzchni; pyta o nazwę pliku (domyślnie `scan.glb`) |
| | (szara linia) | | | `Model: <file> (<licence>) · Available: <backends>`, plus uwagi o konfiguracji, na przykład o instalacji `onnxruntime-gpu` |

### Presety {#the-presets}

| Preset | Dłuższy bok przechwytywania | Kwantyl zachowania | Początkowy próg | Pokazywane podsumowanie |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Szybko i zgrubnie. Dobre do sprawdzenia trasy przed prawdziwym skanem. |
| Balanced | 960 px | 0.65 | 0.010 | Zwykły wybór. Chodź w normalnym tempie. |
| Detailed | 1280 px | 0.40 | 0.004 | Wolno i dokładnie. Chodź celowo i skręcaj łagodnie. |

Kwantyl zachowania oznacza „zachowaj klatkę, gdy zmieniła się bardziej niż ten kwantyl zmian z ostatnich 240 klatek” - Draft zachowuje mniej więcej najbardziej zajęte 15%, Detailed - najbardziej zajęte 60%. Zob. [Klatki kluczowe](reconstruction-capture.md#keyframes).

### Ustawienia stałe w oknie {#settings-that-are-fixed-in-the-window}

Okno zawsze rekonstruuje podczas skanowania, używa wysokości kamery **1.15 m** dla skali płaszczyzny gruntu (wartość chodzenia 1.70 m nie jest do wyboru) i pozwala drabince silników wybrać GPU. To są pola `ScanSettings` (`camera_height`, `prefer_backend`), które może zmienić tylko skrypt.

## Prawa kolumna: co robi skan {#right-column-what-the-scan-is-doing}

| Element | Pokazuje |
|---|---|
| **What the camera sees** | ostatnią klatkę kluczową |
| **Shape it is reading** | przewidywaną głębię, pokolorowaną mapą Turbo, znormalizowaną między 2. a 98. percentylem tej klatki (żeby jeden piksel nieba nie spłaszczał zakresu) |
| **Coverage — where you have been, and how well** | widok z góry (zob. niżej) |
| **Worth another look** | słabe miejsca, ponumerowane tak jak pierścienie na mapie, każde z instrukcją; od najgorszego (największego), najwyżej 8; potem miejsca, które zaznaczyłeś (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Pasek walk-speed | `walk speed — N% of the way to the next view`: zmiana obrazu ostatniej klatki podzielona przez **używany próg** - początkowa wartość presetu dla pierwszych 30 klatek, potem wartość dopasowana ([Klatki kluczowe](reconstruction-capture.md#keyframes)) |
| Linia zdrowia | zdrowie śledzenia albo ostrzeżenie przechwytywania (niżej) |
| Linia rozmiaru | `Size: ...`, jak ustalono skalę poziomu albo dlaczego się nie udało ([Skala](reconstruction-pose.md#scale)) |
| Linia statystyk | `views  frames  dropped  depth-per-second  seconds`, a podczas rekonstrukcji `placed  cells  % well seen  metres`, plus `recovered` i `loops closed`, gdy któraś jest niezerowa |
| Linia skrótów | zarejestrowane klawisze albo powód, dla którego nie udało się ich zarejestrować |
| Linia podpowiedzi (bursztynowa) | podpowiedzi na żywo (niżej), końcowy komunikat skanu i zaznaczenia |

### Mapa pokrycia {#the-coverage-map}

Rysowana ponownie co 900 ms na wątku w tle (nigdy na wątku interfejsu), w siatce 200 x 200 komórek przeskalowanej do 420 px:

- każda kolumna siatki pokrycia przyjmuje **najlepszą** jakość obserwacji w sobie (więc dobrze widziana podłoga nie jest malowana na bursztynowo przez słabo widziany sufit nad nią);
- skala przechodzi od czerwieni (źle) przez bursztyn (cienko) i żółty (do przyjęcia) do zieleni (dobrze);
- komórki nigdy nie obserwowane są wyraźnie ciemnoszare, żeby niezbadany róg nie wyglądał na źle przeskanowany;
- przebyta droga jest cienką jasną linią, bieżąca pozycja białą kropką;
- słabe miejsca to białe pierścienie z numerem;
- zaznaczone miejsca to bursztynowe kwadraty z etykietami `M1`, `M2`, …

Jak liczy się jakość i słabe miejsca: [Fuzja, pokrycie i kolor](reconstruction-fusion-and-texture.md#coverage).

### Linia zdrowia {#the-health-line}

| Zdrowie śledzenia (klatki umieszczone / klatki) | Tekst | Kolor |
|---|---|---|
| brak klatek jeszcze | Waiting for the first frame. | szary |
| 90% lub więcej | Tracking well — N of M frames placed. | zielony |
| 60% lub więcej | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | bursztynowy |
| poniżej 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | czerwony |

Ostrzeżenie przechwytywania z siatki pokrycia zastępuje tę linię (czerwone, gdy skan uznano za nie do zrekonstruowania, w przeciwnym razie bursztynowe): prawie zerowa paralaksa, wszystko widziane z ponad 25 m albo cienka paralaksa. Zob. [Pokrycie](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Linia podpowiedzi {#the-hint-line}

| Warunek | Podpowiedź |
|---|---|
| więcej niż połowa klatek odrzucona, po 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| mniej niż 0.3 zachowanych widoków na sekundę, po 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| więcej niż 8 zachowanych widoków na sekundę, po 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skan się skończył | komunikat sesji: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes` albo `failed: <error>` |

## Skróty klawiszowe {#hotkeys}

Rejestrowane w Windows (`RegisterHotKey`), więc działają, gdy gra ma fokus. Alt-Tab z gry na pełnym ekranie właśnie psuje przechwytywanie.

| Klawisze | Działanie |
|---|---|
| **Ctrl+Alt+F9** | Rozpocznij / zatrzymaj skanowanie |
| **Ctrl+Alt+F10** | Zaznacz to miejsce do ponownego odwiedzenia (podczas skanowania) |
| **Ctrl+Alt+F11** | Pokaż / ukryj nakładkę (przełącza pole „Show feedback over the game”) |

- Są rejestrowane raz, gdy okno się otwiera, i zwalniane, gdy się zamyka; dopóki są zarejestrowane, te kombinacje klawiszy są odbierane każdemu innemu programowi, w tym grze. Klawisze F z dwoma modyfikatorami wybrano, bo gry rzadko je przypisują.
- Auto-powtarzanie jest wyciszone (`MOD_NOREPEAT`), więc przytrzymanie klawisza nie przełącza skanu kilkadziesiąt razy.
- Klawisz, który już trzyma inny program, jest zgłaszany (`... unavailable: another program already has this key`), a pozostałe nadal działają. Przycisk pokazuje tylko klawisz, który faktycznie się zarejestrował.
- Klawisze są ustalone w kodzie (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); parser przyjmuje F1-F12 z `ctrl`, `alt` i `shift`. Poza Windows nie ma skrótów globalnych i okno to mówi.
- **Mark** zapisuje bieżącą pozycję kamery (ostatniej umieszczonej klatki) i pokazuje „Marked MN. Marked spots are on the map and saved with the level.”. Zanim jakakolwiek klatka zostanie umieszczona, pisze, że nie ma gdzie zaznaczyć. Zaznaczone miejsca są rysowane na mapie okna i w nakładce jako bursztynowe kwadraty z etykietami `M1`, `M2`, …, wypisywane pod słabymi miejscami, liczone w linii statystyk nakładki i zapisywane razem z poziomem (niżej).

## Nakładka {#the-overlay}

Mały panel przypięty nad grą, żeby informacja zwrotna była tam, gdzie już patrzą oczy.

- Bez ramki, zawsze na wierzchu, okno narzędziowe (nie w pasku zadań ani w alt-tab), przezroczyste dla wejścia w Qt i przepuszczające kliknięcia w Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), więc kliknięcie przeznaczone dla gry nigdy nie zostaje pochłonięte. Pokazywane bez zabierania fokusu.
- Prawy górny róg głównego ekranu, 18 px od krawędzi; 214 x 358 px.
- Otwiera się, gdy skan się zaczyna (jeśli „Show feedback over the game” jest włączone), zamyka się, gdy skan się kończy.
- **Wymaga trybu borderless windowed**: nic nie może rysować nad pełnym ekranem na wyłączność - ani to, ani overlay Steama, ani Discorda.

Od góry do dołu pokazuje:

| Element | Zawartość |
|---|---|
| Mapa pokrycia | 190 px, ta sama mapa co w oknie, w grubszej siatce 120 x 120, ze ścieżką, pierścieniami słabych miejsc i zaznaczonymi miejscami |
| Zdrowie | ten sam tekst i kolor co linia zdrowia w oknie |
| Statystyki | `N placed · M to revisit · X m`, z `· K marked`, gdy są jakieś zaznaczone |
| pasek **movement** | taki sam jak pasek walk-speed w oknie: zmiana obrazu ostatniej klatki podzielona przez używany próg, pełny, gdy następna klatka zostanie zachowana |
| pasek **sharpness** | ostrość względem mediany tego przechwytywania: zielony od 0.75, bursztynowy od 0.45, czerwony poniżej |
| Advice | jedna instrukcja, zielona / bursztynowa / czerwona (pogrubiona, gdy nie jest „ok”) - zob. [jakość klatek](reconstruction-capture.md#frame-quality-and-advice) |
| Hotkeys | zarejestrowane klawisze |

Jeśli aktualizacja nakładki kiedykolwiek się wysypie, przechodzi ona w czerwony panel **„Feedback stopped”**, który mówi, że wszystko pokazane wcześniej jest nieaktualne, że skan nadal trwa, a główne okno jest poprawne, wraz z błędem i licznikiem. Panel, który zamarł na zielono, bez tego czytałby się dalej jak potwierdzenie.

## Zapis {#saving}

**Save level…** zapisuje rekonstrukcję jako `.glb` (zob. [Wynik .glb](glb-output.md)). Jeśli wolumen nie daje powierzchni, „Nothing to save” wyjaśnia, że śledzenie prawdopodobnie zostało utracone przez większość skanu. Po sukcesie: „Written to <path> ... Load it in 3DHeat through the Level panel.”, z nazwą pliku znaczników, gdy są zaznaczone miejsca.

Zaznaczone miejsca zapisują się obok poziomu jako **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` jest we współrzędnych własnych poziomu (zastosowana skala GLB, więc znacznik leży na siatce, nad którą został zrobiony), `metres` w metrach; `number` odpowiada `M1`, `M2`, … w oknie. Gdy skalę znaleziono na późniejszej klatce kluczowej ([Skala](reconstruction-pose.md#scale)), oba zawierają ten współczynnik.

Zatrzymanie skanu zachowuje to, co zebrano; nowe **Start** odrzuca poprzedni skan. **Zamknięcie okna nie pyta o zapis**: zatrzymuje skan, zwalnia skróty i zamyka nakładkę.
