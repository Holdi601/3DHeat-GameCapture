---
title: Poślizg, dryf i kanały pochodne
nav_order: 8
lang: "pl"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Poślizg, dryf i kanały pochodne {#slip-drift-and-derived-channels}

Analiza jazdy samochodem w zakładce Analiza wyścigowa przeglądarki potrzebuje tych samych kilku wielkości z każdej gry: jak bardzo każda opona się ślizga, o ile samochód jest odwrócony od kierunku, w którym jedzie (kąt dryfu), czy jest w powietrzu, czy jedzie po luźnym podłożu. Gry wysyłają je w bardzo różnych formach albo wcale. Rejestratory tutaj zapisują to, co wysyła każda gra, pod kanonicznymi nazwami, plus notatkę `meta.slip` mówiącą, co znaczą liczby poślizgu; przeglądarka wylicza potem to, czego brakuje, raz, przy wczytaniu okrążenia. **Wartość podana przez grę zawsze wygrywa z wyliczoną.**

## Co zapisują rejestratory {#what-the-recorders-write}

| Gra | Kanały poślizgu | `meta.slip` | Wejścia kąta dryfu |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` na koło, tak jak wysłane | `peak` (zapisywane przez rejestrator; czytnik `.tele.gz` w przeglądarce ustawia to samo) | `latVel`, `longVel` z prędkości w układzie samochodu |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` z prędkości w układzie samochodu |
| EA SPORTS WRC, gry DiRT | brak; zamiast tego `wheelSurfaceSpeed` na koło | `null` | `latVel`, `longVel` = prędkość świata rzutowana na osie samochodu |
| Richard Burns Rally | brak; także bez prędkości kół | brak | `latVel`, `longVel` = własne kołysanie i postęp samochodu |
| BeamNG.drive | brak; `wheelSurfaceSpeed` i `wheelSpeed` na koło | brak | `latVel`, `longVel` = prędkość świata rzutowana na osie samochodu |
| Trackmania | `slipIndex` na koło (miara poślizgu 0..1) | `index` | `latVel` (prędkość boczna), `longVel` (prędkość przednia) |
| iRacing | brak (nie jest logowany) | brak | `yaw` i trasa, `yawRate` |

Wartości `meta.slip` są zdefiniowane w [Plik heat3d-lap](lap-format.md): `peak` (znormalizowany, więc powyżej 1 opona traci przyczepność), `scaled` (poślizg fizyczny podzielony przez typowy szczyt dla asfaltu), `physical` (ułamek i radiany), `index` (miara poślizgu 0..1).

### Dlaczego poślizg Kunos jest skalowany {#why-kunos-slip-is-scaled}

Poślizg Forzy jest znormalizowany tak, że 1 to krawędź przyczepności; do czego normalizuje, nie jest udokumentowane. Kunos wysyła fizyczny współczynnik poślizgu podłużnego (ułamek) i kąt poślizgu bocznego (radiany). Dzielenie przez typowy szczyt dla asfaltu - 0,12 dla współczynnika i 0,14 rad (około 8 stopni) dla kąta - sprawia, że „powyżej 1 znaczy ślizganie” jest w przybliżeniu prawdziwe dla obu rodzin, co zachowuje jedną interpretację dla wyświetlaczy przeglądarki. To przybliżenie: prawdziwe szczyty różnią się w zależności od opony i nawierzchni, dlatego surowe wartości są zachowywane obok skalowanych i dlatego przeglądarka mierzy na samych okrążeniach, gdzie przyczepność każdego samochodu faktycznie słabnie.

## Co wylicza przeglądarka (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Działa to w przeglądarce (`src/race/derive.ts` w przeglądarce 3DHeat), a nie w tym repozytorium.

### Kąt dryfu, `bodySlip` {#drift-angle-bodyslip}

- **Z prędkości w układzie samochodu**, gdy są `latVel` i `longVel`: `atan2(latVel, |longVel|)`, a poniżej 3 m/s wynik to 0 (samochód stojący bokiem nie dryfuje). Jego znak wynika z prędkości bocznej gry, której kierunek dla niektórych gier jest udokumentowany w obu kierunkach - czytaj wielkość.
- **Inaczej z kąta między kierunkiem a trasą**: kierunek jazdy jest brany z pozycji około 2 m po obu stronach każdej próbki (`atan2(dx, dz)`); `yaw` gry jest dopasowywany do niego ze znakiem i przesunięciem (każda gra ma własne zero i kierunek obrotu), używając próbek powyżej 10 m/s i ufając mu tylko, jeśli następnie dobrze się zgadza (rozrzut kołowy co najwyżej 0,05, co najmniej 20 próbek). Kąt dryfu to różnica, a poniżej 3 m/s wynosi 0.

### Poślizg z kół {#slip-ratio-from-the-wheels}

Tam, gdzie okrążenie nie ma `slipRatio.*`, ale ma prędkości kół, współczynnik poślizgu podłużnego to `(koło - samochód) / samochód` na koło, z:

- `wheelSurfaceSpeed.*` (prędkość strefy styku, m/s) wprost, gdy jest wysłana (EA WRC, DiRT, BeamNG);
- w przeciwnym razie `wheelSpeed.*` (obrót, rad/s) razy **promień toczenia zmierzony na okrążeniu**: mediana `speed / |omega|` z próbek, gdzie samochód toczy się bez gazu po prostej (powyżej 10 m/s, nie w powietrzu, przepustnica poniżej 0,3, hamulec poniżej 0,05, przyspieszenie podłużne poniżej 3 m/s²); przy mniej niż 20 takich próbkach - każda próbka powyżej 10 m/s. Promień poza zakresem 0,1-1 m jest odrzucany.

Tylko gdy da się wyliczyć wszystkie cztery koła; `meta.slip` okrążenia staje się wtedy `physical`. Poniżej 3 m/s poślizg wynosi 0.

### W powietrzu {#airborne}

`airborne` ma wartość 1 tam, gdzie każde koło jest oderwane od podłoża, oceniane według pierwszego z tych, które okrążenie ma dla wszystkich czterech kół:

1. `groundContact.*` (BeamNG): żadne koło powyżej 0,5;
2. `wheelLoad.*` (gry AC, RBR, BeamNG): żadne koło powyżej 5% własnej mediany obciążenia;
3. `suspension.*` (0..1 skoku): żadne koło powyżej 0,02, czyli wszystkie w pełni wysunięte.

Pojedyncza odosobniona próbka w powietrzu jest kasowana. Trackmania zapisuje `airborne` sama.

### Luźne podłoże {#loose-ground}

Tam, gdzie okrążenie ma `surfaceRumble.*` (Forza), `loose` ma wartość 1, gdy co najmniej dwa koła zgłaszają wibracje przez co najmniej jedną trzecią sekundy, z przerwami krótszymi niż sekunda połączonymi (gładki fragment żwirowej drogi to wciąż żwirowa droga). Trackmania zapisuje `loose` sama, z materiałów podłoża kół.

### Prędkość kątowa (yaw rate) {#yaw-rate}

Tam, gdzie okrążenie ma `yaw`, ale nie ma `yawRate`, jest to zmiana yaw w sąsiednich próbkach.

## Co wyliczają same rejestratory {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): każdy rejestrator poza Forzą (która go wysyła) zapisuje to z `suspensionM.*` jako położenie w zakresie użytym na tym okrążeniu (od minimum do maksimum). Służy do słupków zawieszenia samochodu i do wykrywania koła wiszącego w powietrzu; nie jest bezwzględnym ułamkiem skoku.
- **`steer`** dla gier Kunos, skalowany na okrążenie (zob. [Gry Assetto Corsa](telemetry-assetto-corsa.md)).
- **Przyspieszenia** dla BeamNG, z różnicy prędkości świata ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** i oś pionowa dla Richard Burns Rally, z pozycji ([Gry rajdowe](telemetry-rally.md)).

## Skrętność {#handedness}

Tam, gdzie świat gry jest lewoskrętny - tak jest w Forzie - tor wychodzi odbity lustrzanie w prawoskrętnej przeglądarce; sterowanie i zawieszenie z samych okrążeń to pokazują. Rejestratory nie zmieniają skrętności: świat z Z w górę (BeamNG) jest obracany do Y w górę, co zachowuje skrętność, a wszystko inne jest zapisywane tak, jak wysłane.
