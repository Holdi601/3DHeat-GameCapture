---
title: Przechwytywanie, maski i jakość klatek
nav_order: 2
lang: "pl"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Przechwytywanie, maski i jakość klatek {#capture-masks-and-frame-quality}

Kod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Skąd biorą się klatki {#where-frames-come-from}

Cel źródła to jeden z poniższych:

| Cel | Źródło | Uwagi |
|---|---|---|
| `monitor:<n>` | cały monitor, na żywo | w oknie „Whole screen”, z numerem w „Which” |
| `window:<title>` | jedno okno, na żywo | w oknie „A window”, z jego tytułem |
| ścieżka pliku | plik wideo | w oknie „A video file”; każdy format, który OpenCV umie czytać |

### Przechwytywanie na żywo: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` używa pakietu `windows-capture`, który opakowuje **Windows Graphics Capture** - publiczne API, którego używają programy do nagrywania ekranu. Nic nie jest wstrzykiwane do gry. Kursor nie jest przechwytywany i nie jest rysowana żółta ramka przechwytywania.

Biblioteka przechwytywania dostarcza klatki do callbacku w wątku kompozytora i oczekuje, że callback zwróci od razu, więc callback tylko kopiuje klatkę (bufor jest wielokrotnie używany), konwertuje BGRA na RGB, zmienia rozmiar, stempluje ją i wkłada do kolejki na **4 klatki**. Gdy kolejka jest pełna, **najstarsza klatka jest odrzucana** i licznik rośnie: nadążanie za grą ma kosztować klatki, a nie pamięć czy poprawność, a podgląd na żywo ma pokazywać, gdzie gracz jest teraz. Odrzucone klatki są widoczne w linii statystyk okna, a gdy odrzucono więcej niż połowę, pojawia się podpowiedź.

Każda klatka niesie `t` (sekundy od startu przechwytywania) i `monotonic` (surowy `time.monotonic()` w chwili przechwycenia) - ten sam zegar, którym są stemplowane pakiety telemetrii. Dzięki temu pozy Forzy można dopasować do klatek.

`windows-capture` jest opcjonalne w sprawdzeniu zależności: bez niego plik wideo nadal można skanować.

### Pliki wideo {#video-files}

`VideoSource` czyta przez OpenCV, konwertuje do RGB i zmienia rozmiar. Kontener bez częstotliwości klatek jest traktowany jako 30 klatek na sekundę. Znaczniki czasu to indeks klatki podzielony przez częstotliwość; plik nie ma czasu rzeczywistego, więc telemetrii nie da się dopasować do wideo.

### Rozdzielczość {#resolution}

Klatki są zmieniane w źródle tak, by najdłuższy bok był rozmiarem przechwytywania z ustawienia (Draft 640, Balanced 960, Detailed 1280 px), z interpolacją obszarową. Klatka 4K ma trzydzieści razy więcej pikseli niż używa model głębokości.

## Klatki kluczowe {#keyframes}

Prawie każda klatka przechwytywania jest zbędna: stanie w miejscu daje setki widoków jednej rzeczy. Rekonstrukcja potrzebuje *paralaksy*. Dlatego klatka jest zachowywana według **tego, jak bardzo obraz zmienił się od ostatniej zachowanej klatki**, a nie według zegara.

`picture_change(a, b)`:

1. obie klatki na szarość i do siatki 16 x 16 średnich bloków (średnie bloków reagują na ruch obrazu, a nie na ziarno, roślinność, migotanie czy HUD);
2. średnia bezwzględna różnica, jako ułamek 255;
3. gdy znana jest maska świata, każdy blok jest ważony udziałem świata (a nie kabiny) w nim, więc blok w połowie zasłonięty deską rozdzielczą liczy się w połowie (używane, gdy maska obejmuje ponad 5% wagi siatki).

Próg **dostosowuje się do przechwytywania**: przez pierwsze 30 klatek jest to wartość startowa ustawienia (0,020 / 0,010 / 0,004), potem kwantyl ustawienia (0,85 / 0,65 / 0,40) z ostatnich 240 zmierzonych zmian, nigdy poniżej 0,0001. Klatka jest zachowywana, gdy jej zmiana sięga progu; pierwsza klatka jest zawsze zachowywana. Stały próg nie działa między scenami - zmiana między klatkami ciemnej kabiny na jadącym okrążeniu to mały ułamek zmiany w jasnym, teksturowanym pomieszczeniu - podczas gdy „zachowaj najbardziej zajęte jedną trzecią” znaczy to samo w obu. Używany próg wychodzi z każdym raportem postępu (`ScanProgress.threshold`), a paski tempa chodzenia w oknie i na nakładce mierzą ostatnią zmianę względem niego (`ScanProgress.toward_next_view`).

Tylko zachowane klatki idą przez model głębokości i rekonstrukcję. Klatki nie są przechowywane, chyba że wywołujący o to poprosi (`keep_frames`); 160 z nich jest zachowywanych do kolorowania siatki (zob. [kolor](reconstruction-fusion-and-texture.md#colour)).

Skan kończy się, gdy zostanie zatrzymany, gdy skończy się wideo, albo przy limicie czasu lub klatek kluczowych.

## Co nie jest światem {#what-is-not-the-world}

Dwie rzeczy w klatce gry nie są geometrią poziomu, a obie psują rekonstrukcję:

- **HUD.** Celownik to najbardziej powtarzalna cecha w każdej klatce. Dopasowywacz cech go kocha: pasuje idealnie między każdą parą klatek, a każde dopasowanie jest dowodem, że kamera się nie ruszyła - co ściska całą rekonstrukcję.
- **Rzeczy przymocowane do kamery.** Broń, maska, rama kabiny, deska rozdzielcza. Prawdziwa geometria w złym układzie współrzędnych: po fuzji rozmazuje się wzdłuż całej przebytej drogi.

Dwa detektory je znajdują. Oba tworzą maskę (255 = świat, 0 = nie świat) albo `None`, gdy dowodów jest za mało; `None` zawsze oznacza „użyj wszystkiego”, nigdy „nie używaj niczego”.

Maska jest stosowana:

- przy **wykrywaniu cech** w wizualnej odometrii (maskowanie celownika na wyjściu, przy jednoczesnym pozwalaniu mu głosować na pozę, naprawiłoby widoczny objaw i zostawiłoby szkodliwy);
- do **zfuzowanych pikseli**, więc żadna geometria kabiny nie jest fuzowana;
- do miary **ostrości i jasności**, bo kabina jest zawsze idealnie ostra;
- do **zmiany obrazu**, która decyduje o klatkach kluczowych.

Nie jest stosowana do klatek podawanych offline'owemu solverowi VGGT (zob. [Rekonstrukcja offline](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: co się nie zmienia {#screenmask-what-does-not-change}

Używana od pierwszej klatki kluczowej, aż FlowMask będzie gotowa.

- Każda klatka jest zamieniana na szarość, zmniejszana o połowę i rozmywana (Gauss 3 x 3), więc przesunięcie o jeden piksel statycznego elementu HUD nie wygląda jak ruch.
- Bezwzględna różnica każdego piksela względem poprzedniej klatki jest składana w wykładniczą średnią (zanik 0,9), więc maska podąża za HUD-em, który pojawia się lub znika w trakcie skanowania.
- Uczy się tylko z klatek, w których wiadomo, że kamera się rusza (w skanie: gdy co najmniej jedna klatka została śledzona) - zaparkowana kamera sprawia, że wszystko jest statyczne.
- Po **12** klatkach uczenia piksel jest statyczny, gdy jego średnia zmiana jest mniejsza niż **0,22** mediany zmiany klatki - względnie, więc próg podąża za tym, jak szybko gracz się porusza.
- Jeśli więcej niż **45%** klatki wygląda na statyczne, założenie zawiodło (menu, przerywnik filmowy) i nic nie jest maskowane.
- Maska jest erodowana o jeden piksel (krawędzie HUD z antyaliasingiem nie należą do żadnej strony) i skalowana z powrotem do pełnego rozmiaru.

Jej uwagi w oknie: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` albo `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: co nigdy się nie przesuwa {#flowmask-what-never-travels}

Kokpit nie jest statyczny: wskazówki się przesuwają, obrotomierz drga, mapa się obraca, więc detektor zmian uznaje te piksele za świat - a są to najgorsze cechy do podania solverowi pozy. FlowMask zadaje lepsze pytanie: **które cechy utrzymują się, nie przemieszczając się?**

- W skanie na żywo uczy się raz, z pierwszych **40 klatek kluczowych** (w skali szarości); potem zastępuje ScreenMask na resztę skanu.
- Klatki są cięte na okna po **30** klatek, nachodzące na siebie w połowie. W każdym oknie zasiewa się do 800 narożników (`goodFeaturesToTrack`, jakość 0,01, co 8 px) i śledzi je piramidalny Lucas-Kanade (21 x 21, 4 poziomy) z **kontrolą w przód i w tył**: ślad, którego przepływ wsteczny nie ląduje w promieniu 1 px od punktu startu, jest odrzucany, bo tracker dryfujący na sąsiedni wzorzec wyprodukowałby dokładnie sygnaturę „utrzymuje się, ale stoi”, której się szuka. Okna krótsze niż 20 klatek są pomijane. Krótkie okna mają znaczenie: w długim przejeździe prawie każda cecha świata opuszcza kadr i dowody się rozrzedzają do zera.
- Netto przemieszczenie każdej przetrwałej cechy jest porównywane z **2% szerokości klatki**: poniżej jest „stuck” (zablokowana), powyżej „moving” (poruszająca się). Liczniki są sumowane na siatce **24 x 24** komórek ekranu według miejsca startu cechy.
- Komórka jest zablokowana, gdy ma co najmniej 2 zablokowane cechy i więcej zablokowanych niż poruszających się, **oraz** co najmniej 3 z jej 8 sąsiadów są też zablokowane (pojedyncza komórka to szum; ciemne ujęcia dają ich mnóstwo).
- Zachowywane są tylko zablokowane obszary **połączone z krawędzią klatki**. Wszystko przymocowane do kamery sięga krawędzi ekranu; to, co leży w środku i się nie przesuwa, to punkt zbiegu - jadąc do przodu, droga przed tobą nie ma przepływu i jest najbardziej pożądaną geometrią.
- Pozostały obszar jest powiększany o jedną komórkę (krawędź panelu przyrządów to gradient).
- Jeśli ponad **60%** klatki byłoby zamaskowane, nie maskuje się niczego: w nocnym materiale większość komórek nie ma śledzalnej cechy, co wygląda tak samo jak tarcza zegara.

Jej uwagi: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, a powyżej 60% komunikat wyjaśniający, że nic nie jest maskowane.

Ścieżka offline uczy tego samego FlowMask z 4 serii po 90 kolejnych klatek rozłożonych na całe wideo, przy 960 x 540 ([Offline](reconstruction-offline.md)).

## Jakość klatek i porady {#frame-quality-and-advice}

`QualityWatcher` ocenia każdą klatkę kluczową i wybiera **jedną** instrukcję, by nakładka mogła powiedzieć „zwolnij”, dopóki jest jeszcze czas.

Dla każdej klatki mierzy na samych pikselach świata (wszystkie piksele, jeśli maska zostawia mniej niż 5%):

- **ostrość**: wariancja Laplace'a - standardowa miara jednoprzebiegowa, reaguje dokładnie na to, co niszczy rozmycie ruchu;
- **jasność**: średni poziom szarości, 0-255.

Ostrość nie ma bezwzględnej skali (scena nocna i jasna ulica różnią się o rząd wielkości, a obie są ostre), więc ocenia się ją względem **bieżącej mediany tego przechwytywania**: ostatnie 90 klatek, przy czym potrzeba 20, zanim wyda się jakikolwiek osąd. Każda klatka jest porównywana z historią *sprzed* siebie, więc długi rozmyty odcinek nie może obniżyć mediany do własnego poziomu.

| Warunek | Test |
|---|---|
| płaski | ostrość co najwyżej 1,0 (ekran ładowania, ściana, niebo) |
| ciemny | jasność poniżej 26 |
| rozmyty | ostrość poniżej 0,55 mediany i nie płaski |

Porada, pierwsze dopasowanie wygrywa (uporządkowane według tego, co najmocniej blokuje skan):

| Sytuacja | Porada | Poziom |
|---|---|---|
| mniej niż 20 klatek | Wyczuwam obraz… | ok |
| płaski | Nie ma czego mierzyć - skieruj kamerę na poziom, nie na niebo. | stop |
| ciemny | Za ciemno, by rekonstruować. Włącz światła albo przejedź ten odcinek w dzień. | stop |
| rozmyty | Rozmycie - zwolnij. | ostrzeżenie |
| mniej niż połowa klatek śledzona | Tracę trop - zwolnij i zostaw w kadrze więcej poziomu. | ostrzeżenie |
| mniej niż 40% śledzonych klatek zfuzowanych | Pozycje są dobre, ale głębia się nie trzyma. Jedź bliżej scenerii. | ostrzeżenie |
| są słabe miejsca | N słabych miejsc - mapa je oznacza. | ok |
| inaczej | Dobrze - jedź dalej. | ok |

Poziom koloruje poradę na nakładce (zielony / bursztynowy / czerwony). Pasek **ostrości** na nakładce to ostrość klatki względem mediany.

(Kod ma też komunikat „Blurred, and the camera is not moving. Check the capture.” dla nieruchomej kamery; skan zawsze zgłasza, że kamera się porusza, więc nie jest on pokazywany.)
