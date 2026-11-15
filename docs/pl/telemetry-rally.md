---
title: Gry rajdowe
nav_order: 3
lang: "pl"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # or dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testy: `tests/test_rally.py`, na pakietach zbudowanych z udokumentowanych układów. **Jeszcze nie uruchamiane na działających grach.**

Wszystkie wysyłają UDP, które gra włącza w swoich plikach ustawień. Rejestrator nasłuchuje na wszystkich interfejsach (`0.0.0.0`) na domyślnym porcie gry, chyba że `--port` poda inny: **20777** dla `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** dla `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Włączenie {#switching-it-on}

Gra czyta `Documents\My Games\WRC\telemetry\config.json`. Pakiet `session_update` domyślnej struktury `wrc` musi być włączony w stronę tego komputera:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funkcja `configure_wrc`):

- czyta JSON, znajduje `udp.packets` i wpis z `"structure": "wrc"` i `"packet": "session_update"`;
- jeśli jest już włączony na `127.0.0.1` albo `localhost` na używanym porcie, wypisuje `already on` i nic nie zmienia;
- w przeciwnym razie ustawia `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` i zachowuje `frequencyHz` wpisu (albo `-1`, gdy go nie ma); jeśli takiego wpisu nie ma, dopisuje go;
- zapisuje oryginalny tekst do `config.json.bak` obok niego, a potem zapisuje nowy plik (wcięcia 4 spacje).

Po zmianie pliku uruchom grę ponownie, jeśli nie podejmie zmiany (nie sprawdzono).

### Co wysyła {#what-it-sends}

Domyślna struktura `wrc` ma 237 bajtów, little-endian, bez nagłówka: pozycja świata, prędkość i przyspieszenie (X w lewo, Y w górę, Z do przodu), lewy / przedni / górny wektor jednostkowy samochodu, na koło (tylne lewe, tylne prawe, przednie lewe, przednie prawe) wysokość piasty i jej prędkość pionową oraz prędkość do przodu strefy styku, temperatury hamulców, pedały po asystach, kierowanie (-1 lewo, +1 prawo), hamulec ręczny, obroty, bieg, zegar odcinka, dystans i długość. Pakiet krótszy niż 237 bajtów jest ignorowany i zgłaszany raz.

| Kanał | Z |
|---|---|
| `x`, `y`, `z` | pozycja świata |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | prędkość świata rzutowana na przód, na minus lewo (więc dodatnia to w prawo), na górę |
| `longAcc`, `latAcc`, `vertAcc` | przyspieszenie świata rzutowane tak samo |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | tak, jak wysłane |
| `gear` | `gear_index`; -1, gdy równa się indeksowi wstecznego, 0, gdy równa się indeksowi luzu |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | pozycja piasty |
| `wheelSurfaceSpeed.*` | prędkość do przodu strefy styku |
| `brakeTemp.*` | temperatura hamulca |

Kontrola: jeśli `speed` przekracza 10, a długość wektora prędkości świata różni się od niego o więcej niż 20%, rejestrator raz wypisuje, że układ może nie być domyślną strukturą `wrc`.

Odcinek jest **skończony**, gdy długość odcinka jest dodatnia, a dystans dosięgnął długości minus 0,5 m. Zegar używany do podziału i do `time` to `stage_time`.

Źródła: UDP Telemetry Guide v1.3 od EA; lista kanałów, którą gra zapisuje do `readme/channels.json`; przesunięcia odkodowane przez nobonobo/obs-codemasters-telemetry i SpaceMonkey. Domyślny port w grze nie jest udokumentowany; rejestrator używa 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Włączenie {#switching-it-on-1}

Edytuj `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally i DiRT 4 też mają `hardware_settings_config.xml`; ich dokładny folder dla tych dwóch nie został sprawdzony), tak by element `udp` brzmiał:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` sprawia, że pozycje, koła i długość odcinka trafiają do pakietu. Rejestrator nie edytuje tego pliku.

### Co wysyła {#what-it-sends-1}

66 liczb zmiennoprzecinkowych little-endian (DiRT Rally: 64); pakiety krótsze niż 64 liczby są ignorowane, a 64-liczbowy jest uzupełniany zerami. Używane indeksy:

| Indeks | Pole | Kanał |
|---|---|---|
| 1 | czas odcinka (okrążenia) | zegar podziału i `time` |
| 2 | dystans okrążenia | `stageDistance` |
| 4-6 | pozycja świata | `x`, `y`, `z` |
| 7 | prędkość | `speed` |
| 8-10 | prędkość świata | `longVel` (na przód), `latVel` (na wektor boczny) |
| 11-13 | wektor boczny | |
| 14-16 | wektor do przodu | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | pozycja zawieszenia RL RR FL FR | `suspensionM.*` |
| 25-28 | prędkość strefy styku kół RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gaz, kierowanie, hamulec, sprzęgło, bieg | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 lub więcej oznacza wsteczny, zapisywany jako -1) |
| 34, 35 | przeciążenie boczne, podłużne (g) | `latAcc`, `longAcc` (razy 9,80665) |
| 37 | obroty / 10 | `rpm` (razy 10) |
| 51-54 | temperatury hamulców | `brakeTemp.*` |
| 59, 60, 61, 62 | ukończone okrążenia, łączna liczba okrążeń, długość toru, czas ostatniego okrążenia | podział |

**Brak kanału hamulca ręcznego.** Kierunek wektora bocznego jest udokumentowany w obu kierunkach, więc na znak `latVel` nie należy polegać (przeglądarka czyta wielkość kąta dryfu).

Odcinek jest **skończony**, gdy liczba ukończonych okrążeń wzrośnie powyżej wartości z początku odcinka (rajdcross - za każdym razem, gdy to się dzieje), albo - w zdarzeniu jednookrążeniowym - gdy dystans okrążenia dosięgnie 99,9% długości toru. Czas odcinka to czas ostatniego okrążenia gry, gdy jest dodatni. Kontrola: prędkość względem `speed` jak przy EA WRC, z komunikatem „is extradata set to 3?”.

Źródła: dokument UDP Codemasters dla DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Włączenie {#switching-it-on-2}

W `RichardBurnsRally.ini`, sekcja `[NGP]`: `udpTelemetry=1` oraz punkt końcowy (127.0.0.1, port 6776, chyba że podasz inny w `--port`). Rejestrator nie edytuje tego pliku.

### Co wysyła {#what-it-sends-2}

664 bajty (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): zegar odcinka i dystans do mety, pedały, kierowanie, bieg, pozycja świata, orientacja, własne prędkości samochodu (przód, bok, pion), przyspieszenia, obroty oraz cztery 128-bajtowe bloki kół (LF, RF, LB, RB) z ugięciem i siłą sprężyny. Brak prędkości kół.

| Kanał | Z |
|---|---|
| `x`, `y`, `z` | pozycja, osie tak, jak wysłane, potem przestawione (niżej) |
| `longVel`, `latVel`, `vertVel` | przód, bok, pion |
| `longAcc`, `latAcc` | przyspieszenie x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | tak, jak wysłane |
| `gear` | `gear - 1` (0 wsteczny, 1 luz, 2 pierwszy) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | ugięcie sprężyny |
| `wheelLoad.*` | siła sprężyny |
| `speed` | **wyliczana z pozycji** w oknie ±2 próbek, nie brana z pakietu |

Osie pozycji RBR, jednostki orientacji i jednostka prędkości nie są udokumentowane, więc gdy odcinek jest zapisywany: oś, wzdłuż której odcinek zmienia się najmniej, jest brana za pionową i wstawiana do `y` (`orient_up`, potrzeba co najmniej 10 próbek), a prędkość jest przeliczana z pozycji (`speed_from_positions`). Orientacja jest dekodowana, ale nie zapisywana, więc pliki RBR nie mają `yaw`.

Odcinek jest **skończony**, gdy zegar wyścigu biegnie, a dystans do mety dosięgnął zera. Zegar to `race_time`.

Źródła: `rbr.telemetry.data.TelemetryData.h` od NGP, przez mika-n/RBRUDPTelemetryLogger i groybe/rbr-udp-telem.

## Odcinki {#stages}

Wszystkie pięć używa `StageSplitter` na zegarze odcinka gry: odcinek otwiera się, gdy zegar startuje, zamyka się jako ukończony, gdy gra mówi, że samochód dojechał, a zegar, który się cofa (restart albo kolejny odcinek), porzuca otwarty odcinek - zachowany jako plik `_partial`, jeśli ma ponad 10 próbek i co najmniej 300 m. Ukończone odcinki krótsze niż 300 m nie są zapisywane. Szczegóły: [Podział okrążeń i odcinków](lap-splitting.md).

## Plik okrążenia {#the-lap-file}

`game` to `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` lub `richard-burns-rally`. `meta` to `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"`, gdy podano `--surface`. `slip` jest null, bo żadna z tych gier nie wysyła poślizgu opon. Zamiast tego w pliku jest prędkość strefy styku każdego koła (EA WRC, DiRT), a przeglądarka z niej i z osi samochodu wylicza poślizg i kąt dryfu; zob. [Poślizg, dryf i kanały pochodne](slip-and-drift.md). Kanały `suspension.*` (0..1 użytego skoku) są dodawane z `suspensionM.*`.

Gdy nie podano `--surface`, plik nie zawiera nawierzchni wcale, celowo: domyślna wartość zapisana tutaj nadpisałaby wnioskowanie przeglądarki. Przeglądarka bierze wtedy nawierzchnię z nazwy odcinka lub zdarzenia (rajdy asfaltowe, zimowe, a Monte jako mieszane), a jeśli nie ma wskazówki - z tego, jak prowadzono samochód (ostre zakręty przy małych kątach dryfu to asfalt), i luźną, gdy nic nie wskazuje - co najczęściej jest prawdą dla odcinka rajdowego. Podaj `--surface`, gdy wiesz lepiej.
