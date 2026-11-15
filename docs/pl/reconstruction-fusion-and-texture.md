---
title: Fuzja, pokrycie i kolor
nav_order: 5
lang: "pl"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fuzja, pokrycie i kolor

Kod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Każda umieszczona klatka kluczowa aktualizuje jednocześnie dwie rzadkie siatki: **objętość powierzchni**, z której powstaje siatka, oraz **siatkę pokrycia**, która mówi, na ile jej wierzyć i dokąd wrócić. Obie są aktualizowane na każdą klatkę kluczową, a nie na końcu, bo to według mapy pokrycia gracz się kieruje.

## Od głębokości do punktów

Dla każdej klatki kluczowej, której poza jest znana **i** której głębokość ma skalę:

1. Używany jest co drugi piksel w każdym kierunku (`PIXEL_STRIDE = 2`; sąsiednie piksele jednej powierzchni nie są niezależnymi pomiarami).
2. Głębokość jest zamieniana na metry przez afiniczne dopasowanie klatki.
3. Zachowywane są tylko głębokości między **0,35 m** (bliżej to broń, HUD, maska pojazdu) a **60 m** (błąd monokularny rośnie mniej więcej z kwadratem odległości, więc odległe punkty to szum o kształcie geometrii) i tylko na pikselach świata z maski.
4. Punkt jest podniesiony przez model kamery i przeniesiony do świata przez pozę.
5. Każdy punkt niesie kolor piksela.

Klatka, która jest umieszczona, ale nie ma skali głębokości, jest liczona jako *umieszczona*, ale nie *zfuzowana*.

## Objętość powierzchni

`SurfaceVolume(voxel=0.25)` - woksel to „Surface detail” w oknie.

### Ważona zajętość, nie TSDF

Obcięte pole odległości ze znakiem (TSDF) rzeźbi wzdłuż promienia każdego piksela i dobrze oddaje cienkie struktury oraz czystą wolną przestrzeń, bo wie, że promień *przeszedł przez* pustą przestrzeń. To oznacza przechodzenie promienia dla setek milionów pikseli. Ta objętość zamiast tego zlicza **ważoną zajętość** na woksel i uruchamia marching cubes na wygładzonym wyniku: wystarczająco szybko, by działać podczas skanowania na maszynie bez użytecznego GPU, a wynik jest zamkniętą powierzchnią, a nie chmurą punktów. Koszt: cienkie struktury i wolna przestrzeń są gorsze niż dałby TSDF.

### Integrowanie klatki

- Punkty są wrzucane do wokseli (`floor(point / voxel)`).
- Każdy dotknięty woksel dostaje `weight x sqrt(count / max_count)`, gdzie `count` to ile punktów klatki wpadło do niego, a `weight = max(0.1, pewność pozy)`. Pierwiastek kwadratowy: po pewnym punkcie więcej pikseli tej samej powierzchni z tego samego miejsca przestaje być dowodem; ważenie pewnością pozy nie pozwala wątpliwej pozie przesuwać powierzchni.
- Kolor to bieżąca ważona średnia na woksel.

Siatka jest **rzadka**: przejechana trasa dotyka małego ułamka swojej obwiedni. Współrzędne wokseli są upakowane w jeden 64-bitowy klucz (21 bitów na oś, do +-1 048 575 wokseli - przy 0,25 m około +-262 km) i wyszukiwane przez posortowaną tablicę i wyszukiwanie binarne, w pełni wektoryzowane.

### Wyciąganie siatki

1. Woksele o wadze poniżej **0,35** są odrzucane (pojedyncze punkty na krawędziach sylwetki stałyby się kolcami).
2. Wagi są skalowane przez **75. percentyl** całego skanu i obcinane do 1.
3. Zajęta przestrzeń jest cięta na **bloki po 64 woksele** na bok, każdy realizowany z **otoczką 3 wokseli** danych sąsiadów (bez niej każda granica bloku zamykałaby się w ścianę, a droga wychodziłaby jako rząd pudełek).
4. Pole każdego bloku jest wygładzane Gaussem (sigma 0,8 woksela), by usunąć zmarszczkę, jaką zostawia szum głębokości.
5. **Przebieg pierwszy**: 99. percentyl wygładzonego pola, próbkowany po wszystkich blokach (co najwyżej 2 miliony wartości), ustala jedną globalną skalę poziomu. Normalizowanie per blok awansowałoby pojedynczy odstający element do pełnej powierzchni we własnym pustym bloku.
6. **Przebieg drugi**: pole każdego bloku podzielone przez tę skalę, marching cubes przy **0,5**. Trójkąt należy do bloku, w którym leży jego **środek ciężkości**, więc trójkąty przecinające szew są emitowane dokładnie raz.
7. Wierzchołki przechodzą do jednostek świata w środkach wokseli; każdy wierzchołek bierze kolor swojego wokseli (szary średni tam, gdzie wypada poza zajętym wokselem).

Ekstrakcja blokowa umożliwia skan wielkości toru: jedna gęsta tablica nad kilometrowym kwadratem przy 0,25 m to miliardy komórek. `tests/test_track_scale.py` pilnuje, że działa to w tej skali, z pamięcią proporcjonalną do tego, co zeskanowano.

### Podłoże i struktura

`classify` oznacza każdy trójkąt według jego normalnej (zorientowanej według normalnych wierzchołków): w granicy **35 stopni od pionu w górę** to `ground` (podłoże), wszystko inne to `structure` (struktura). Przeglądarka rysuje podłoże pełne, a struktury prawie przezroczyste. **Woda nigdy nie jest oznaczana** - nie da się jej odróżnić od płaskiego podłoża po kształcie, a błędna etykieta renderowałaby dziedziniec jako jezioro. Każda etykieta staje się jedną częścią `.glb` ([Wyjście .glb](glb-output.md)).

## Pokrycie

`CoverageGrid(voxel=0.5)` zapisuje dla każdej komórki o boku pół metra cztery rzeczy, które nie są tym samym:

| Składnik | Zapisane | Wynik (każdy przycięty do 0..1) | Dlaczego liczy się osobno |
|---|---|---|---|
| Ile razy widziano | liczba klatek kluczowych, które widziały komórkę | `count / 3` | raz to zgadywanie, bez czego uśrednić |
| Z ilu kierunków | suma jednostkowych wektorów widoku | `(1 - spread) / (1 - 0,93)`, gdzie spread = długość sumy / liczba | dwadzieścia klatek idących prosto na ścianę nie ma między sobą paralaksy; dwa widoki pod trzydziestoma stopniami są warte więcej |
| Z jak daleka | najbliższa odległość widzenia | `1 - nearest / 40 m` | błąd głębokości rośnie mniej więcej z kwadratem odległości |
| Jak dobrze kamera była ustawiona | najlepsza pewność pozy | sama pewność | geometria zfuzowana z wątpliwą pozą ląduje w złym miejscu |

Punkty klatki są najpierw grupowane według komórki, więc dziesięć tysięcy pikseli jednej ściany liczy się jako jedna obserwacja z jednego kierunku.

**Jakość = iloczyn czterech składników**, a nie średnia: to warunki, z których każdy musi być spełniony. Miejsce widziane dwieście razy z jednego kierunku z odległości sześćdziesięciu metrów jest słabo obserwowane, a średnia schowałaby to za jednym doskonałym składnikiem.

Główne liczby (`summary`): zajęte komórki, udział z jakością co najmniej 0,5 („% well seen” w oknie), średnia jakość i objętość.

### Słabe miejsca

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. komórki o jakości poniżej 0,35 są słabe;
2. słabe komórki są grupowane według **połączenia** (sąsiedztwo 26, union-find tylko po zajętych komórkach - nie raster po obwiedni, która na długim przejeździe to miliony pustych komórek);
3. grupy mniejsze niż 8 komórek są ignorowane;
4. powód grupy to najczęstszy *najsłabszy składnik* jej komórek, a jej położenie to średnia ich komórek;
5. sortowane od największej (potem od najgorszej jakości), co najwyżej 8.

| Powód | Pokazywana porada |
|---|---|
| few views | Widziano tylko raz lub dwa razy - przejdź obok jeszcze raz. |
| one direction | Widziano tylko z jednego kąta. Zrób krok w bok i spójrz jeszcze raz. |
| distant | Widziano tylko z daleka. Podejdź bliżej. |
| poor tracking | Kamera nie była tu dobrze umiejscowiona. Podchodź wolniej. |

Połączenie ma znaczenie: grupowanie według stałej siatki bloków pokazuje jeden zaniedbany pokój boczny jako wiele oddzielnych pierścieni, a nikt nie odróżni ośmiu miejsc od jednego miejsca policzonego osiem razy.

## Plan widokowy

`top_down(resolution)` rzutuje komórki na x/z i zachowuje **najlepszą** jakość na kolumnę (ktoś stojący w pokoju ma słabe pokrycie sufitu i doskonałe pokrycie podłogi; uśrednianie pomalowałoby pokój na bursztynowo). Kolumny nigdy nieobserwowane są zaznaczane osobno. Okno rysuje to w 200 x 200, nakładka w 120 x 120 ([Mapa pokrycia](reconstruction-scan-ui.md#the-coverage-map)).

## Czy to da się zrekonstruować?

Co 25 zfuzowanych klatek, gdy jest co najmniej 500 komórek:

| Wynik | Werdykt | Komunikat (skrócony) |
|---|---|---|
| mniej niż 2% komórek ma rozrzut widoku poniżej 0,93 | nie do zrekonstruowania | Prawie brak paralaksy. Albo kamera nigdy nie patrzy w bok, albo śledzenie dryfuje, więc ta sama powierzchnia nigdy nie ląduje dwa razy w tym samym miejscu. Sprawdź liczbę umieszczonych klatek: jeśli jest wysoka, to dryf. |
| mediana najbliższej odległości powyżej 25 m | nie do zrekonstruowania | Wszystko widziano z N m lub dalej ... Podejdź bliżej tego, czego chcesz. |
| mniej niż 6% z dobrym rozrzutem | do zrekonstruowania, z ostrzeżeniem | Cienka paralaksa - geometria będzie szorstka. Najbardziej pomaga ruch na bok względem tego, na co patrzysz. |

Mała paralaksa ma dwie przyczyny, których to narzędzie nie potrafi rozróżnić, dlatego komunikat wymienia obie.

## Kolor

Kolor zfuzowany na woksel jest tani i na żywo, i rozmyty: każdy piksel komórki o boku ćwierć metra jest uśredniany, także te widziane krawędziowo z trzydziestu metrów. Dlatego przy eksporcie siatka jest kolorowana ponownie, raz, z samych klatek:

- **Zachowane klatki**: do **160** klatek kluczowych (obraz i poza), wybranych losowaniem ze zbiornikiem, by rozłożyły się na cały skan, a nie na jego ogon.
- **Na wierzchołek** (`project_colours`): każda zachowana klatka wnosi wkład, jeśli wierzchołek jest przed kamerą i w obrazie, powierzchnia jest odwrócona co najwyżej około 70 stopni od bezpośredniego patrzenia na kamerę (`|normal . view| > 0.34`), jest bliżej niż **35 m** i nic bliżej nie stało przed nim (poniżej).
- Każdy taki widok jest oceniany jako `facing x (1 - distance / 35)`, więc bliski widok prostopadły bije daleki ślizgowy. **4 najwyżej punktowane** widoki każdego wierzchołka są zachowywane - w jakiejkolwiek kolejności są klatki, lepszy widok zastępuje najsłabszy z czterech - i mieszane, ważone tym samym wynikiem.
- **Zasłanianie**: w każdej klatce wierzchołki własnej siatki w widoku są rysowane do bufora głębokości z komórkami po 2 piksele, zachowując najbliższy na komórkę. Wierzchołek, który leży za najbliższym w swojej komórce o więcej niż `0,3 m + 5%` swojej odległości, był w tej klatce ukryty - ściana między kamerą a drogą za nią - i ten widok nie liczy się wcale. Test zna tylko siatkę: zasłaniacz, który nigdy nie został zfuzowany (przejeżdżający samochód, słupek kabiny poza maską HUD), nie zostanie wychwycony.
- Wierzchołek, którego żadna klatka nie widziała, zachowuje kolor wokselowy; wierzchołek bez obu jest szary średni (czarny czytałby się jak dziura).

Kolor jest zapisywany jako `COLOR_0` na wierzchołek, a nie jako atlas tekstur. Domyślny wygląd przeglądarki to szara mapa pod nasyconym cieplnym nakładaniem; kolor służy do znalezienia drogi na skanowanym torze, gdzie sama geometria nie oddziela jej od pobocza, i jest pokazywany za przełącznikiem przeglądarki *Zarejestrowany kolor* w jej panelu Tło / poziom. Atlas podwoiłby rozmiar pliku i wymagał rozwijania UV, dla widoku, który celowo nie jest domyślny. Blender i inne narzędzia glTF czytają `COLOR_0`.
