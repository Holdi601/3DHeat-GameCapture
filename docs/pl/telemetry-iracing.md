---
title: "iRacing"
nav_order: 6
lang: "pl"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **nie potrzebuje rejestratora**. Symulator sam zapisuje pliki telemetrii `.ibt`, gdy włączone jest
zapisywanie telemetrii (Alt+L w samochodzie): całą sesję z częstotliwością 60 Hz, każdy kanał, który symulator
udostępnia, z opisem sesji w YAML obok. Przeciągnij plik `.ibt` na zakładkę Analiza wyścigowa w przeglądarce.

Czytnik żyje w przeglądarce, a nie w tym repozytorium (`src/race/ibt.ts` w przeglądarce 3DHeat). Jest
testowany na syntetycznym pliku; opisano go tutaj, bo to część iRacing tej samej historii nagrywania okrążeń.

## Co zawiera plik i jak się go czyta {#what-the-file-holds-and-how-it-is-read}

Plik to udokumentowany układ pamięci symulatora zapisany na dysk:

| Część | Rozmiar | Zawiera |
|---|---|---|
| Nagłówek | 112 bajtów | wersja, częstotliwość taktowania, gdzie są YAML i tabela zmiennych, długość jednego wiersza próbki, gdzie zaczynają się wiersze |
| Podnagłówek dysku | 32 bajty | data i godzina startu, liczba okrążeń, liczba wierszy |
| Tabela zmiennych | 144 bajty na kanał | typ, przesunięcie w wierszu, liczba, nazwa, opis, jednostka |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Wiersze | jeden na takt | |

Plik jest odrzucany, gdy jest krótszy niż 144 bajty, gdy jego nagłówek nie ma sensu (brak zmiennych, tabela
zmiennych poza plikiem, zerowa długość wiersza), albo gdy brakuje któregoś z `SessionTime`, `Lap`, `Lat`,
`Lon`, albo gdy nie ma żadnej próbki z ustaloną pozycją.

## Pozycja {#position}

iRacing podaje szerokość, długość geograficzną i wysokość, a nie pozycję w układzie samego toru. Pozycje
wyznacza się w metrach na płaszczyźnie stycznej w pierwszej próbce z ustaloną pozycją (promień Ziemi
6 371 008,8 m): `x` na wschód, `z` na południe, `y` to wysokość - tak że patrząc z góry, przy domyślnym kierunku
kamery przeglądarki, północ jest u góry ekranu.

## Okrążenia {#laps}

Sesja dzielona jest według licznika `Lap` symulatora. Okrążenie zostaje tylko wtedy, gdy ma ponad 60 próbek,
zaczyna się poniżej 5% długości okrążenia (`LapDistPct`) i kończy powyżej 95% - czyli gdy przejechano je od
linii do linii. Jeśli żadne okrążenie nie spełnia warunków, plik jest odrzucany, a komunikat podaje długość
toru z YAML. `distance` to `LapDist` przeliczone od startu okrążenia albo przejechany dystans z pozycji, gdy
brakuje `LapDist`; `time` to `SessionTime` od startu okrążenia.

## Kanały {#channels}

| iRacing | Kanał | Przeliczenie |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | brak |
| `Clutch` | `clutch` | `1 - value` (iRacing liczy sprzęgło jako załączone; kanał to pedał) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radiany, dodatnie przeciwnie do wskazówek zegara, do -1..1, w prawo dodatnie; pi, gdy brakuje maksimum) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | brak |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | brak |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | ustawienia wspomagania |
| `dcBrakeBias` | `brakeBias` | dzielone przez 100, gdy powyżej 1,5 (w niektórych autach procent) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura karkasu w środku opony |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa razy 0,145038, na psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Każdy inny kanał z jedną wartością na próbkę (i nie pojedynczym bajtem) przechodzi pod własną nazwą, a
prefiks koła (`LF`, `RF`, `LR`, `RR`) zamienia się w sufiks (`.FL`, `.FR`, `.RL`, `.RR`), więc wykresy
przeglądarki oferują go bez niczyjego opisu.

Samochód pochodzi z `DriverInfo`: wpis, którego `CarIdx` zgadza się z `DriverCarIdx`, daje `CarScreenName`,
`CarID` i `CarClassShortName`. Tor to `TrackDisplayName` (albo `TrackName`).

## Czego iRacing nie daje {#what-iracing-does-not-give}

Poślizg opon nie jest zapisywany, więc nie ma kanałów poślizgu. Kąt dryfu wylicza się z prędkości obrotu
względem toru (zobacz [Poślizg, dryf i kanały pochodne](slip-and-drift.md)). Modele torów są dostarczane w
chronionym formacie i nie są celem wyciągania plików (zobacz [Gry](games.md)).
