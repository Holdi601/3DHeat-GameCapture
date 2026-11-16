---
title: "Obowiązujące zasady"
nav_order: 2
lang: "pl"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# Zasady, na których to zbudowano {#the-rules-this-is-built-under}

Każda część 3DHeat GameCapture przestrzega tych samych ograniczeń. To decyzje projektowe, a nie zastrzeżenia,
i kilka z nich celowo kosztuje dokładność.

## Nic nie jest wstrzykiwane, nic nie jest podpinane {#nothing-is-injected-nothing-is-hooked}

Żadna część tego nie łączy się z procesem gry, nie czyta jej pamięci i nie dotyka jej interfejsu graficznego.

- **Klatki** pochodzą z Windows Graphics Capture, publicznego API, z którego korzystają rejestratory ekranu
  (przez pakiet `windows-capture`), albo z pliku wideo. Zobacz
  [Przechwytywanie, maski i jakość klatek](reconstruction-capture.md).
- **Telemetria** pochodzi tylko z interfejsów, które gry publikują w tym celu:
  - strumień UDP Data Out Forzy, włączany w ustawieniach gry;
  - nazwane strony pamięci dzielonej, które gry Kunos publikują dla aplikacji (`Local\acpmf_physics` i
    pokrewne). Są otwierane tylko do odczytu przez `mmap`; to udokumentowany sposób, w jaki aplikacje je
    czytają, a nie odczyt pamięci procesu gry;
  - telemetria UDP, którą wysyłają EA SPORTS WRC, gry DiRT i Richard Burns Rally (przez wtyczkę RSF/NGP),
    gdy włączy się ją w ich własnych plikach ustawień;
  - interfejs protokołów BeamNG, przez mały mod Lua „protocol”, który wczytuje i wysyła własny plik gry
    `lua/vehicle/protocols.lua`;
  - interfejs wtyczki Openplanet dla Trackmanii, przez wtyczkę, która tylko czyta to, co udostępnia
    Openplanet, i zapisuje pliki;
  - własne pliki telemetrii `.ibt` iRacing.

## Dlaczego to ważne {#why-it-matters}

Gra zna głębię każdego piksela dokładnie, a podpięty bufor głębi uczyniłby rekonstrukcję poziomu niemal
idealną i trywialną. Oznaczałoby to też wstrzykiwanie się w procesy, które mogą być chronione przez
anti-cheat, co naraża konto każdego, kto to uruchomi. Dlatego głębia jest zamiast tego *szacowana* z obrazu
([Głębia](reconstruction-depth.md)), a duża część potoku rekonstrukcji istnieje po to, by odzyskać jak najwięcej
z tej utraconej dokładności ze źródeł wolnych do użycia: poz z telemetrii tam, gdzie gra je publikuje, skali
płaszczyzny podłoża tam, gdzie tego nie robi, i masek, które trzymają HUD i kabinę poza rozwiązaniem.

Rozważono bufor głębi ReShade i go nie użyto. ReShade z założenia wyłącza dostęp do głębi w sesjach
wieloosobowych, więc pomógłby tylko tytułom dla jednego gracza (zobacz
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Rzeczy, które narzędzie zmienia na komputerze, i tylko na żądanie {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Działanie | Kiedy | Co dokładnie |
|---|---|---|
| Instaluje pakiety Pythona | pierwsze uruchomienie okna skanu, po oknie dialogowym i potwierdzeniu | `pip install` do interpretera uruchamiającego narzędzie - przy `scan.bat` do prywatnego `.venv` obok niego. Nigdy samoistnie w całym systemie. |
| Konwertuje model głębi | przycisk „Set up the depth model”, po drugim oknie dialogowym dla PyTorch i pokrewnych | zapisuje `models/depth-small-518.onnx` |
| Edytuje `config.json` EA SPORTS WRC | `telemetry --game wrc --configure <file>` | włącza pakiet `wrc` / `session_update` na 127.0.0.1; stary plik zostaje jako `config.json.bak` |
| Kopiuje mod BeamNG | `telemetry --game beamng --install` | `mods/beamng/heat3d` do `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (zastępując starszą kopię) |
| Kopiuje wtyczkę Trackmanii | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` do `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (zastępując starszą kopię) |
| Rejestruje globalne skróty klawiszowe | gdy okno skanu jest otwarte (Windows) | Ctrl+Alt+F9 / F10 / F11, zwalniane po zamknięciu okna |
| Aktualizuje narzędzie | po odpowiedzi „tak” na pytanie o aktualizację albo po uruchomieniu `python -m heat3d_update` | zobacz [Aktualizacje](updates.md) |

Pliku `hardware_settings_config.xml` gier DiRT i pliku `RichardBurnsRally.ini` Richard Burns Rally narzędzie
**nie** zmienia; wyjście UDP włączasz samodzielnie (zobacz [Gry rajdowe](telemetry-rally.md)).

## Co jest odczytywane i co zostaje na komputerze {#what-is-read-and-what-stays-on-your-machine}

Narzędzia odczytują to, co gra pokazuje na ekranie, oraz telemetrię i pliki, które gra w tym celu udostępnia, na własnym komputerze użytkownika. Nic z gry nie jest dostarczane ani rozpowszechniane dalej: żadne zasoby gry, żaden kod gry, żadne biblioteki DLL. Pliki okrążeń, nagrania, rekonstrukcje i wyeksportowane trasy zostają na komputerze; `.gitignore` repozytorium trzyma nagrania, pliki okrążeń, siatki, wagi modeli i wideo poza kontrolą wersji według folderu i typu pliku.

3DHeat GameCapture nie jest powiązany z żadnym wydawcą gier ani przez żadnego zatwierdzony. Nazwy gier i powiązane znaki towarowe należą do ich właścicieli. Posiadacze praw: prosimy o zgłoszenie (issue) na [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - odpowiadamy szybko i na żądanie usuwamy wszystko.
