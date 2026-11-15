---
title: Gry
nav_order: 4
lang: "pl"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Gry: nagrywanie i tory {#games-recording-and-courses}

Jak nagrywana jest każda obsługiwana gra, co wysyła i które jej tory można wyeksportować z jej własnych plików.

Zasady są takie same dla każdej gry: tor pochodzi z plików, które użytkownik posiada, albo jest rekonstruowana z jego własnej jazdy. Zaszyfrowane archiwa otwierają się tylko kluczem, który użytkownik już ma - nic tutaj nie dostarcza kluczy ani ich nie odzyskuje i nic nie wstrzykuje się w proces gry. Telemetria pochodzi wyłącznie z interfejsów, które gry udostępniają w tym celu (wyjścia UDP, pamięć współdzielona, ich własne interfejsy modów i wtyczek). To, do czego użytkownik kieruje narzędzia, nadal podlega licencji tej gry.

## Telemetria {#telemetry}

Każda gra zapisuje się jako pliki `heat3d-lap` ([`lap-format.md`](lap-format.md)), z kanałami o kanonicznych nazwach i blokiem `meta` opisującym, co oznaczają ich liczby - jak skalowany jest poślizg, czy to tor, rajd czy arcade, nawierzchnia, jeśli jest znana - więc czytnik traktuje je wszystkie tak samo. Wszystkie polecenia to `python -m heat3d_capture ...` w tym repozytorium.

| Gra | Jak nagrać | Pozycja | Opony i poślizg | Kąt dryfu | Stan |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out przez UDP: `heat3d_capture telemetry` (przekazuje do FH Companion) - albo własny plik `.tele.gz` FH Companion obok każdego okrążenia, wczytywany razem z plikiem okrążenia | współrzędne świata XYZ | współczynnik poślizgu podłużnego, kąt poślizgu bocznego, łączny poślizg na koło, znormalizowane; rumble nawierzchni | prędkość w układzie samochodu | rejestrator przetestowany; czytnik `.tele.gz` sprawdzony na prawdziwych okrążeniach |
| Forza Motorsport (w tym 2023) | to samo; rozróżniane po długości pakietu | współrzędne świata XYZ | to samo | to samo | rejestrator przetestowany |
| Assetto Corsa, ACC, AC EVO | pamięć współdzielona: `telemetry --game ac / acc / acevo` | średnia z punktów styku opon | współczynnik poślizgu podłużnego i kąt poślizgu bocznego (fizyczne, skalowane przez typowy szczyt dla asfaltu); ABS i TC w działaniu (ACC, EVO) | prędkość w układzie samochodu | rejestrator przetestowany na syntetycznych stronach |
| Assetto Corsa Rally | `telemetry --game acrally` | to samo | to samo; obciążenia kół; temperatury przeliczone z kelwinów | prędkość w układzie samochodu | rejestrator przetestowany na syntetycznych stronach |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` włącza domyślny pakiet `wrc` (najpierw plik jest zapisywany jako kopia zapasowa) | współrzędne świata XYZ | prędkość strefy styku na koło; poślizg wyliczony | z osi samochodu i jego prędkości | rejestrator przetestowany na pakietach zbudowanych według udokumentowanego układu |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: ustaw `<udp enabled="true" extradata="3" port="20777" delay="1" />` w `hardware_settings_config.xml`, potem `telemetry --game dirtrally2` (lub `dirtrally`, `dirt4`) | współrzędne świata XYZ | prędkość strefy styku na koło; poślizg wyliczony. Brak kanału hamulca ręcznego | z osi samochodu i jego prędkości | to samo |
| Richard Burns Rally (RSF/NGP) | UDP telemetrii NGP (`udpTelemetry=1`): `telemetry --game rbr` | świat, oś pionowa znaleziona z odcinka | ugięcie i siła sprężyny na koło; brak prędkości kół | własne prędkości samochodu | to samo; osie i jednostki prędkości nie są udokumentowane, obsługiwane na podstawie danych |
| BeamNG.drive | mod protokołu `heat3d`: `telemetry --game beamng --install`, potem Options > Other > Protocols > „others” | świat, obrócony do osi Y w górę | prędkość powierzchni koła, obrót, obciążenie, kontakt z podłożem; poślizg wyliczony | z osi samochodu i jego prędkości | rejestrator przetestowany na pakietach zbudowanych według struktury modu; mod nieprzetestowany w grze |
| Trackmania (2020) | wtyczka Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, ładowana w trybie dewelopera Openplanet; jeden plik CSV na przejazd w jego folderze | współrzędne świata XYZ | współczynnik poślizgu Trackmanii na koło; luźne podłoże z materiałów kół; w powietrzu | prędkość przednia i boczna | czytnik przetestowany; wtyczka nieprzetestowana w grze |
| iRacing | jego własne pliki `.ibt`; nagrywarka niepotrzebna | szerokość i długość geograficzna oraz wysokość, rzutowane na płaszczyznę styczną | brak poślizgu (nie jest zapisywany); prędkość obrotu i przyspieszenie boczne | z prędkości obrotu względem toru | czytnik przetestowany na syntetycznym pliku |

Czego żadna gra rajdowa nie wysyła - poślizgu opon - czytnik wylicza: z prędkości strefy styku każdego koła względem prędkości samochodu tam, gdzie gra jedną wysyła (`(koło - samochód) / samochód`), a z obrotu koła i promienia toczenia zmierzonego na samym okrążeniu tam, gdzie gra wysyła tylko obrót. Kąt dryfu pochodzi z prędkości własnej samochodu (Forza, gry AC, Trackmania, RBR), z prędkości świata rzutowanej na osie samochodu (EA WRC, DiRT, BeamNG) albo z kierunku jazdy względem trasy. To, czy samochód jest w powietrzu, wynika z kontaktu kół, obciążeń lub zawieszenia.

Tam, gdzie świat gry jest lewoskrętny - tak jest w Forzie - tor wychodzi odbity lustrzanie w prawoskrętnym widoku; sterowanie i zawieszenie z samych okrążeń to pokazują. Gry, których skrętność nie jest udokumentowana (RBR, BeamNG, Trackmania), obsługiwane są tak samo: mierzone, nie zakładane.

Poza kanałami jazdy rejestratory zachowują to, co dodaje każda gra: działanie ABS i kontroli trakcji w grach AC, rozkład hamowania, DRS, ogranicznik prędkości w alei serwisowej, doładowanie oraz żywotność klocków i tarcz hamulcowych; ustawienia wspomagania, rozkład hamowania, paliwo, temperatury oleju i wody z iRacing oraz każdy inny kanał, który loguje pod własną nazwą.

### Źródła i to, czego jeszcze nie potwierdzono {#sources-and-what-is-not-yet-confirmed}

- **Forza:** oficjalna dokumentacja Data Out (Forza Motorsport; Forza Horizon 6) dla pól, ich jednostek i układu samochodu (x w prawo, y w górę, z do przodu - lewoskrętny). Do czego Forza normalizuje poślizg, nie jest udokumentowane: zmierz, gdzie przyczepność każdego samochodu faktycznie słabnie, zamiast zakładać, że 1 to granica.
- **Kunos:** SDK AC1, dokumentacja pamięci współdzielonej ACC v1.8.12, `albertowd/live-telemetry-evo` (EVO, zmierzone; AC Rally używa układu ACC, „potwierdzone sondą bajt po bajcie”), `LuizZak/AssettoCorsaRallyTelemetryReader`. Strona, w którą wskazuje oś x samochodu, jest udokumentowana w obu kierunkach: używaj wielkości kąta dryfu, nie jego znaku.
- **EA SPORTS WRC:** UDP Telemetry Guide v1.3 od EA oraz lista kanałów, którą gra zapisuje do `readme/channels.json`; przesunięcia domyślnego pakietu `wrc` odkodowane przez nobonobo/obs-codemasters-telemetry. Domyślny port w grze nie jest udokumentowany; rejestrator włącza pakiet na porcie 20777.
- **DiRT:** dokument UDP Codemasters dla DiRT 4, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Kierunek wektora bocznego i jednostka położenia zawieszenia są udokumentowane w obu kierunkach; żadne z nich nie rozstrzyga wyniku.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` od NGP (przez mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Osie położenia, jednostki orientacji i jednostka prędkości nie są udokumentowane: rejestrator bierze górę z odcinka, a prędkość z pozycji.
- **BeamNG:** documentation.beamng.com (protocols; refNodes: pojazd +X w lewo, -Y do przodu, Z w górę) oraz pliki gry `lua/vehicle/protocols.lua` i `wheels.lua`. OutSim jest atrapą w aktualnych wersjach; OutGauge nie ma pozycji, a MotionSim nie ma kół - stąd mod.
- **Trackmania:** `CSceneVehicleVisState` Openplanet i wtyczka VehicleState, czas wyścigu `CSmScriptPlayer`. Wtyczki Openplanet nie mogą wysyłać UDP, więc wtyczka zapisuje pliki. Niepodpisane wtyczki ładują się tylko w trybie dewelopera, co ogranicza grę online; wtyczkę można podpisać na openplanet.dev.

Żaden z rejestratorów nie był jeszcze uruchamiany na działających tu grach; pierwsza prawdziwa sesja każdego z nich jest decydującym testem, a `tests/test_kunos.py`, `test_rally.py` i `test_beamng.py` utrwalają układy, według których zostały zbudowane. Każdy rejestrator sprawdza swoje pakiety w miarę ich nadejścia - prędkość z pakietu względem prędkości samochodu, rozmiar struktury - i mówi, gdy układ się nie zgadza.

## Tory: co jest eksportowane, dla każdej gry {#courses-what-is-exported-per-game}

Tor dodaje krawężniki, ściany i pobocza, które wyjaśniają linię jazdy. Tory eksportuje [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`) z plików samej gry, tam gdzie zostało to zbudowane i sprawdzone na zainstalowanej kopii. Szczegóły są w [dokumentacji GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Gra | Tor z okrążenia |
|---|---|
| Forza Horizon | tak |
| BeamNG.drive | tak |
| Assetto Corsa Rally | tak |
| Assetto Corsa EVO | nie: jej zawartość nie jest czytelna jako pliki |
| iRacing | nie: modele torów są w chronionym formacie |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | jeszcze nie: każda wymaga zainstalowanej kopii, by zbudować i sprawdzić |

Ścieżka z nagrania rozgrywki, opisana niżej, działa na razie dla wszystkich z nich.

## Ścieżka, która działa dla każdej gry {#the-route-that-works-for-every-game}

GameCapture rekonstruuje poziom z nagrania rozgrywki. Jego trudną częścią jest ścieżka kamery; dla Forzy jest ona dokładna, bo telemetria podaje pozę samochodu w każdej klatce. Każda wymieniona gra ma teraz to samo: pozycję i orientację na żywo, z udokumentowanego interfejsu. Podanie ich do `pose/telemetry_pose.py` zamiast danych Forzy to jedyna rzecz, która sprawia, że ścieżka z rozgrywki jest dokładna dla wszystkich - reszta potoku (głębokość, fuzja, teksturowanie) nie zależy od tego, która gra narysowała klatki.
