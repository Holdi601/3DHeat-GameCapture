---
title: Poza kamery i skala
nav_order: 4
lang: "pl"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poza kamery i skala {#camera-pose-and-scale}

Mapa głębokości mówi, jak daleko są rzeczy od *jednego* punktu widzenia. Zamiana wielu takich map w jeden poziom wymaga wiedzy, gdzie był każdy punkt widzenia i w jakich jednostkach. Ta strona opisuje ścieżki na żywo; rozwiązanie feed-forward offline jest na [Rekonstrukcja offline](reconstruction-offline.md).

Kod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamery {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` buduje kamerę pinhole z **poziomego pola widzenia** ustawionego w oknie: `fx = (width / 2) / tan(fov / 2)`, piksele kwadratowe (`fy = fx`), punkt główny w środku klatki. Gra nie publikuje swojej projekcji, więc to jedyna zakładana liczba: za wąskie pole sprawia, że scena wygląda na głębszą, niż jest. Ścieżka offline używa 65 stopni.

`Pose` jest zapisywana jako **świat-od-kamery**: `rotation` (3 x 3) i `translation` = środek kamery w świecie, czyli to, czego chcą trajektoria, mapa pokrycia i nakładka.

## Wizualna odometria (domyślna) {#visual-odometry-the-default}

`VisualOdometry` śledzi każdą klatkę kluczową względem poprzedniej:

1. **Cechy**: ORB, do 1500 na klatkę, wykrywane tylko na masce świata (zob. [Przechwytywanie](reconstruction-capture.md#what-is-not-the-world)).
2. **Dopasowania** do poprzedniej klatki kluczowej: siłowo, odległość Hamminga, sprawdzane krzyżowo (tylko wzajemnie najlepsze pary).
3. **Podniesienie do 3D**: głębokość poprzedniej klatki jest już w jednostkach świata, więc dopasowane piksele stają się punktami świata.
4. **Umieszczenie kamery**: `solvePnPRansac` na tych punktach (błąd reprojekcji 3 px, pewność 0,999, 200 iteracji). Translacja wychodzi w tych samych jednostkach, więc **skala przechodzi przez lukę między klatkami**.
5. **Zakotwiczenie głębokości tej klatki**: jej własna przewidywana odwrotna głębokość jest dopasowywana (`fit_scale`) do głębokości punktów zgodnych z PnP, i cykl się powtarza.

**Pierwsza klatka** to początek układu: pozycja jednostkowa, a jej afiniczne dopasowanie głębokości to albo kalibracja podłoża poniżej, albo - bez niej - tożsamość (rekonstrukcja jest wtedy spójna wewnętrznie, ale bez jednostek).

Poza potrzebuje co najmniej **18 inlierów RANSAC** - wyraźnie więcej niż minimum PnP wynoszące sześć, bo rozwiązanie z ledwo wystarczającej liczby punktów to dokładnie to, które jest pewnie błędne.

### Pewność {#confidence}

Każda umieszczona klatka dostaje pewność z zakresu 0..1, która waży jej fuzję i pokrycie:

| Poza pochodzi z | Pewność |
|---|---|
| telemetrii | 1.0 |
| rozwiązania feed-forward | 0.85 |
| śledzenia wizualnego | `inliers / matches x min(1, inliers / 60)` |

### Gdy śledzenie się załamie {#when-tracking-breaks}

Klatka, której nie da się umieścić, jest zgłaszana, nigdy nie zgadywana: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Nie zapisuje się żadnej pozy i nic nie jest zfuzowane. Kontynuowanie od ostatniej pozy albo start od nowa postawiłyby następny odcinek poziomu w dowolnym przesunięciu - szew, który wygląda jak prawdziwa geometria.

Po załamaniu każda nowa klatka jest **relokalizowana** względem bazy danych minionych klatek kluczowych (co 4. śledzona klatka jest dodawana, do 120, najstarsze odrzucane), zaczynając od najnowszych, tym samym krokiem dopasowania i PnP. Dopóki żadne się nie uda, klatki są odrzucane. Odzyskana klatka kontynuuje we tym samym układzie współrzędnych. Odzyskania są liczone i pokazywane w oknie (`N recovered`).

### Zamykanie pętli: wyłączone {#loop-closure-off}

Ta sama baza danych obsługuje zamykanie pętli: dopasowywanie do klatek kluczowych z dużo wcześniej, by wykryć powrót w to samo miejsce i przyciągnąć trasę z powrotem. **Jest wyłączone domyślnie, a skaner nigdy go nie włącza** (`Reconstructor(loop_closure=False)`). Na powtarzalnych scenach - odcinek rajdowy, korytarz, rząd drzew - każdy fragment wygląda jak każdy inny, a dopasowywanie cech potwierdza fałszywe powroty, co przypina kamerę blisko miejsca startu, podczas gdy ona jedzie dalej. Zrobienie tego porządnie wymaga rozpoznawania miejsc (słownika bag-of-words albo nauczonego deskryptora) i geometrycznej weryfikacji względem mapy, czego nie ma.

Gdy włączone z kodu, zamknięcie wymaga: klatki kluczowej co najmniej 60 klatek starszej, w odległości 6 m od bieżącej pozy, dopasowanej przynajmniej 90 inlierami, przesuwającej pozę o więcej niż 0,02 m i mniej niż 6 m. Nawet wtedy tylko zastępuje bieżącą pozę; to nie jest graf pozy i nie przesuwa wcześniejszych klatek ani zfuzowanej geometrii.

## Pozy z telemetrii {#telemetry-poses}

Przy włączonym **Racing telemetry (Forza) -> Listen for position data** ścieżka kamery pochodzi z Data Out Forzy, a nie z obrazów (`ForzaPoseSource`):

- Wątek nasłuchuje na `127.0.0.1:<port>` (domyślnie 5300), z tym samym wykrywaniem układu co rejestratory ([Forza](telemetry-forza.md)); pakiety są używane, gdy ustawiona jest flaga `isRaceOn`. Zajęty port jest zgłaszany, a nie rzucany jako wyjątek: telemetria to ulepszenie, a skan jedzie dalej wizualnie.
- Każdy pakiet jest stemplowany **monotonicznym czasem przybycia** - tym samym zegarem, którym kamera stempluje klatki. Własny znacznik czasu gry liczy od czegoś niezwiązanego, więc nie jest używany do dopasowania. Jitter pętli zwrotnej o milisekundę lub dwie to około 6 cm przy 200 km/h.
- Trzymany jest kroczący bufor 30 sekund. Poza klatki jest **interpolowana** z próbek po obu stronach czasu przechwycenia: pozycja liniowo, obrót przez interpolację sferyczną (zmieszana macierz nie jest obrotem i wykrzywiłaby każdy punkt). Przez lukę dłuższą niż **0,35 s** albo poza buforem nie ma pozy.
- `pose_from_forza`: kamera jest umieszczona przy samochodzie (przesunięcie kamery pościgowej nie jest publikowane). **Pozycje są zachowywane dokładnie tak, jak gra je wysyła**: świat Forzy jest już w osi Y w górę (x i z po mapie, y to wysokość), co jest tym, jak pliki okrążeń i tras go zapisują, więc powierzchnia ląduje na tych samych współrzędnych co okrążenia nagrane na niej. (Wcześniejsza wersja zamieniała y i z dla świata „Z w górę” i kładła tor na boku.)
- Obrót to kolejno yaw, pitch, roll, z kierunkami odczytanymi z nagranych okrążeń: kierunek jazdy `atan2(dx, dz)` równa się yaw, nachylenie pod górę równa się minus pitch (dodatni to nos w dół), a roll jest dodatni, gdy prawe zawieszenie jest ściśnięte (dodatni opuszcza prawą stronę). Osie samochodu (x w prawo, y w górę, z do przodu) są następnie przekształcane w osie kamery (x w prawo, y w dół, z do przodu) przez odwrócenie y.
- Świat Forzy jest **lewoskrętny**, a ramka kamery nie, więc wynikowa macierz świat-od-kamery jest odbiciem (wyznacznik -1), i skan wychodzi lewoskrętny, jak pliki okrążeń. Interpolacja nie jest tym naruszona (obrót między dwiema takimi pozami jest prawdziwym obrotem).
- Gdy klatka nie ma pozy z telemetrii (luka), rekonstruktor wraca do **wizualnego śledzenia** dla tej klatki, startując od ostatniej pozy z telemetrii, i wraca do póz z kanału, gdy tylko ten odpowie. PnP zwraca tylko obroty, więc w lustrzanym świecie jest rozwiązywany z lustrzanym światem odbitym przez z, a odbicie jest składane z powrotem; klatka ląduje we współrzędnych gry. Dopiero gdy śledzenie wizualne też zawiedzie, klatka jest nieśledzona.

### Skala głębokości z telemetrii {#depth-scale-from-telemetry}

Gra mówi, gdzie jest kamera, a nie jak daleko są rzeczy, więc głębokość każdej klatki wciąż wymaga zakotwiczenia - ale nie przez łańcuch od klatki zero, której jednostka jest dowolna, podczas gdy pozy są w metrach. Zamiast tego cechy dopasowane między poprzednią a bieżącą klatką (co najmniej 8) są **triangulowane bezpośrednio z dwóch znanych póz**, w metrach, a mapa głębokości jest dopasowywana do punktów przed kamerą. Każda klatka jest zakotwiczana względem telemetrii, więc nie ma łańcucha, który mógłby dryfować.

Jeśli dwie pozy są bliżej niż **0,05 m**, promienie są prawie równoległe i triangulacja to szum, więc klatka zostaje niezakotwiczona: umieszczona dokładnie, ale nie zfuzowana („positioned, but its depth has no scale yet”). Dlatego okno liczy osobno klatki *umieszczone* i *zfuzowane*.

## Skala {#scale}

Wizualna odometria poprawnie łączy względną skalę kolejnych klatek, ale cały poziom wciąż „pływa” o jeden nieznany czynnik. Względne wyjście Depth Anything jest w dowolnych jednostkach, więc pozostawienie pierwszej klatki jako tożsamości stawia świat w odległości metrów od kamery w dowolnym rozmiarze.

`GroundCalibrator` przypina ten czynnik do **wysokości kamery nad podłożem**, mierzonej na **pierwszej klatce kluczowej** i, gdy tam nie ma użytecznego podłoża, na kolejnych:

- Wysokość kamery: **1,15 m** (linia oczu kierowcy) - okno zawsze tego używa; skrypty mogą podać 1,70 m (`WALKING_HEIGHT`, stojący gracz) albo `None` (bez kalibracji).
- Próbka podłoża: wiersze 62-92% w dół klatki (poniżej horyzontu, powyżej maski albo broni) i kolumny 30-70% w poprzek (z dala od pobocza).
- Każdy piksel tam, z użyteczną predykcją, jest podniesiony z głębokością `1 / predicted` w jednostkach sieci; punkty poniżej optycznej osi dają wysokość poniżej kamery. Ich mediana to wysokość kamery w jednostkach sieci, więc `metres per unit = 1.15 / median`, a afiniczne dopasowanie klatki to `scale = 1 / metres_per_unit`, przesunięcie 0.
- Ufa się jej tylko przy co najmniej 200 próbkach podłoża i **rozrzucie** (mediana bezwzględnego odchylenia podzielona przez medianę) poniżej **0,60**.
- Na pierwszej klatce kluczowej dopasowanie staje się jednostką początku, więc skan jest w metrach od początku. Gdy pierwsza klatka kluczowa nie ma użytecznego podłoża, skan startuje bez jednostek i każda późniejsza śledzona klatka kluczowa jest sprawdzana, do **30 klatek** łącznie. Pierwsza, która się skalibruje, daje *metry na jednostkę*: medianę, po paśmie podłoża, głębokości, jaką podłoże implikuje, podzielonej przez głębokość, jaką dał łańcuch dla tej klatki. Wszystko, co już zfuzowane, jest w jednostce pierwszej klatki, więc czynnik nie jest zwracany do łańcucha; jest stosowany do całego poziomu (i zaznaczonych miejsc) przy zapisie oraz do wyświetlanej odległości w międzyczasie. Rozmiar woksela jest wtedy w jednostkach pierwszej klatki, więc jego rozmiar w metrach różni się od ustawienia o ten czynnik.
- Po 30 klatkach bez podłoża skan pozostaje bez jednostek i mówi o tym.
- Z telemetrią późniejsze klatki kluczowe nie są sprawdzane: głębokość jest zakotwiczona w metrach telemetrii.

Być w granicy dziesięciu procent prawdziwego rozmiaru jest lepsze niż być w błędzie o czynnik tysiąc; telemetria, gdzie jest dostępna, sprawia, że nie jest to potrzebne. Uwaga jest pokazywana w oknie pod linią śledzenia jako `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (z `found on frame N, so the level is scaled by F when it is written`, gdy przyszło później), `no usable ground in the first N frames - sizes are relative, not metres` albo `in metres, from the telemetry's positions`.

## Dopasowanie wiązek i długie ślady (niepodłączone) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dwie części istnieją dla przyszłego okiennego solvera i **nie są używane przez skaner**:

- **`FeatureTracks`** utrzymuje tożsamość cech przez setki klatek śledzeniem Lucas-Kanade (600 cech, ponowne zasiewanie poniżej 60%, tolerancja w przód i w tył 1 px, nowe cechy co najmniej 10 px od istniejących), czego potrzebuje dopasowanie wiązek - samo dopasowywanie deskryptorów między kolejnymi klatkami daje tylko pary.
- **`bundle_adjust`** poprawia okno póz i punktów razem przez `scipy.optimize.least_squares` (region zaufania, strata soft-L1 ze skalą 2 px, jawny wzorzec rzadkości Jacobianu, stałe kamery przywracane dokładnie). Testowane względem znanej prawdy w `tests/test_bundle.py`.

`WindowedOdometry` łączy je (okna po 12 klatek kluczowych, rozwiązanie co 3 klatki kluczowe, pierwsze dwie kamery stałe, punkty z błędem powyżej 6 px odrzucane, skoki powyżej 6-krotności ostatniego kroku odrzucane). Jego docstring odnotowuje, że na prawdziwym materiale **zwinął trasę i był znacznie wolniejszy** niż śledzenie klatka po klatce, z niejednoznacznością miary (skali) i bootstrapem opartym na głębokości jako znanymi przyczynami i trzecią, niezidentyfikowaną. Więc odometria klatka po klatce pozostaje domyślna; prawdopodobna poprawka, odnotowana w kodzie, to bootstrap dwuwidokowy z macierzą istotną (essential matrix), z bazą ustaloną z kalibracji płaszczyzny podłoża.
