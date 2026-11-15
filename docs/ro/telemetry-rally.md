---
title: "Jocuri de raliu"
nav_order: 3
lang: "ro"
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

Cod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Teste: `tests/test_rally.py`, pe pachete construite din structurile documentate. **Nerulat încă pe jocurile live.**

Toate trimit UDP pe care jocul îl activează din propriile fișiere de setări. Înregistratorul ascultă pe toate interfețele (`0.0.0.0`) pe portul implicit al jocului, dacă `--port` nu dă altul: **20777** pentru `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** pentru `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Activarea {#switching-it-on}

Jocul citește `Documents\My Games\WRC\telemetry\config.json`. Pachetul `session_update` al structurii implicite `wrc` trebuie activat spre acest calculator:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funcția `configure_wrc`):

- citește JSON-ul, găsește `udp.packets` și intrarea cu `"structure": "wrc"` și `"packet": "session_update"`;
- dacă este deja activată spre `127.0.0.1` sau `localhost` pe portul folosit, afișează `already on` și nu schimbă nimic;
- altfel setează `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, și păstrează `frequencyHz` al intrării (sau `-1` dacă nu există); dacă nu există o asemenea intrare, adaugă una;
- scrie textul original în `config.json.bak` alături, apoi scrie fișierul nou (indentat cu 4 spații).

Reporniți jocul după ce schimbați fișierul dacă nu preia schimbarea (nu a fost verificat).

### Ce trimite {#what-it-sends}

Structura implicită `wrc` are 237 de octeți, little-endian, fără antet: poziția lumii, viteza și accelerația (X stânga, Y sus, Z înainte), vectorii unitari stânga / înainte / sus ai mașinii, pe fiecare roată (spate-stânga, spate-dreapta, față-stânga, față-dreapta) înălțimea butucului și viteza sa verticală și viteza înainte a punctului de contact, temperaturile frânelor, pedalele după asistențe, direcția (-1 stânga, +1 dreapta), frâna de mână, rpm, treapta și ceasul etapei, distanța și lungimea. Un pachet mai scurt de 237 de octeți este ignorat și raportat o dată.

| Canal | Din |
|---|---|
| `x`, `y`, `z` | poziția lumii |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | viteza lumii proiectată pe înainte, pe minus stânga (deci pozitiv înseamnă dreapta), pe sus |
| `longAcc`, `latAcc`, `vertAcc` | accelerația lumii proiectată la fel |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | cum sunt trimise |
| `gear` | `gear_index`; -1 când este egal cu indexul de mers înapoi, 0 când este egal cu indexul de neutru |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | poziția butucului |
| `wheelSurfaceSpeed.*` | viteza înainte a punctului de contact |
| `brakeTemp.*` | temperatura frânei |

Verificare: dacă `speed` este peste 10 și lungimea vitezei lumii diferă de el cu mai mult de 20%, înregistratorul afișează o dată că structura poate să nu fie cea implicită `wrc`.

O etapă este **terminată** când lungimea etapei este pozitivă și distanța a ajuns la lungime minus 0,5 m. Ceasul folosit pentru împărțire și pentru `time` este `stage_time`.

Surse: Ghidul UDP Telemetry v1.3 al EA; lista de canale pe care jocul o scrie în `readme/channels.json`; decalajele așa cum le decodează nobonobo/obs-codemasters-telemetry și SpaceMonkey. Portul implicit din fabrică nu este documentat; înregistratorul folosește 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Activarea {#switching-it-on-1}

Editați `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally și DiRT 4 folosesc și ele un `hardware_settings_config.xml`; dosarul lor exact pentru acestea două nu este verificat aici) astfel încât elementul `udp` să fie:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` este ce pune pozițiile, roțile și lungimea etapei în pachet. Înregistratorul nu editează acest fișier.

### Ce trimite {#what-it-sends-1}

66 de numere în virgulă mobilă little-endian (DiRT Rally: 64); pachetele mai scurte de 64 de numere sunt ignorate, iar unul de 64 este completat cu zerouri. Indicii folosiți:

| Index | Câmp | Canal |
|---|---|---|
| 1 | timpul turei (etapei) | ceasul de împărțire și `time` |
| 2 | distanța de tur | `stageDistance` |
| 4-6 | poziția lumii | `x`, `y`, `z` |
| 7 | viteza | `speed` |
| 8-10 | viteza lumii | `longVel` (pe înainte), `latVel` (pe vectorul lateral) |
| 11-13 | vectorul lateral | |
| 14-16 | vectorul înainte | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | poziția suspensiei SS SD SF FD (spate-stânga, spate-dreapta, față-stânga, față-dreapta) | `suspensionM.*` |
| 25-28 | viteza petecului roților SS SD SF FD | `wheelSurfaceSpeed.*` |
| 29-33 | accelerație, direcție, frână, ambreiaj, treaptă | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 sau mai mult înseamnă mers înapoi, scris ca -1) |
| 34, 35 | forța g laterală, longitudinală | `latAcc`, `longAcc` (înmulțit cu 9,80665) |
| 37 | rpm / 10 | `rpm` (înmulțit cu 10) |
| 51-54 | temperaturile frânelor | `brakeTemp.*` |
| 59, 60, 61, 62 | ture terminate, ture totale, lungimea traseului, timpul ultimei ture | împărțire |

**Nu există canal pentru frâna de mână.** Sensul vectorului lateral este documentat în ambele sensuri, deci semnul lui `latVel` nu trebuie crezut (vizualizatorul citește mărimea unghiului de derapaj).

O etapă este **terminată** când numărul de ture terminate crește peste valoarea sa de la începutul etapei (o tură de rallycross de fiecare dată când crește), sau, pentru un eveniment cu o singură tură, când distanța de tur ajunge la 99,9% din lungimea traseului. Timpul etapei este timpul ultimei ture al jocului când este pozitiv. Verificare: viteza lumii față de viteza indicată, ca la EA WRC, cu mesajul „is extradata set to 3?".

Surse: documentul UDP al Codemasters pentru DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Activarea {#switching-it-on-2}

În `RichardBurnsRally.ini`, secțiunea `[NGP]`: `udpTelemetry=1` și punctul final (127.0.0.1, portul 6776 dacă nu dați alt `--port`). Înregistratorul nu editează acest fișier.

### Ce trimite {#what-it-sends-2}

664 de octeți (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): ceasul etapei și distanța până la capăt, pedalele, direcția, treapta, poziția lumii, atitudinea, vitezele proprii ale mașinii (înainte, lateral, pe verticală), accelerațiile, rpm, și patru blocuri de roată de 128 de octeți (ST, DT, SS, DS) cu deformarea arcului și forța arcului. Fără viteze ale roților.

| Canal | Din |
|---|---|
| `x`, `y`, `z` | poziția, axele cum sunt trimise, apoi reordonate (mai jos) |
| `longVel`, `latVel`, `vertVel` | înainte, lateral, vertical |
| `longAcc`, `latAcc` | accelerația x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | cum sunt trimise |
| `gear` | `gear - 1` (0 mers înapoi, 1 neutru, 2 întâi) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | deformarea arcului |
| `wheelLoad.*` | forța arcului |
| `speed` | **calculată din poziții** pe ±2 eșantioane, nu luată din pachet |

Axele poziției RBR, unitățile atitudinii și unitatea de viteză nu sunt documentate, deci când se scrie o etapă: axa pe care etapa variază cel mai puțin este luată drept „sus" și mutată în `y` (`orient_up`, are nevoie de cel puțin 10 eșantioane), iar viteza este recalculată din poziții (`speed_from_positions`). Atitudinea este decodată, dar nu este scrisă, deci fișierele RBR nu au `yaw`.

O etapă este **terminată** când ceasul de cursă rulează și distanța până la capăt a ajuns la zero. Ceasul este `race_time`.

Surse: `rbr.telemetry.data.TelemetryData.h` al NGP, prin mika-n/RBRUDPTelemetryLogger și groybe/rbr-udp-telem.

## Etape {#stages}

Toate cinci folosesc `StageSplitter` pe ceasul de etapă al jocului: o etapă se deschide când pornește ceasul, se închide completă când jocul spune că mașina a terminat, iar un ceas care merge înapoi (o repornire, sau următoarea etapă) abandonează etapa deschisă - păstrată ca fișier `_partial` dacă are peste 10 eșantioane și cel puțin 300 m. Etapele terminate mai scurte de 300 m nu sunt scrise. Detalii: [Cum se împart turele și etapele](lap-splitting.md).

## Fișierul de tură {#the-lap-file}

`game` este `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` sau `richard-burns-rally`. `meta` este `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"` când s-a dat `--surface`. `slip` este null pentru că niciunul dintre aceste jocuri nu trimite alunecarea anvelopei. Viteza punctului de contact al fiecărei roți (EA WRC, DiRT) este în fișier în schimb, iar vizualizatorul derivează din ea alunecarea și unghiul de derapaj, împreună cu axele mașinii; vezi [Alunecare, derapaj și canale derivate](slip-and-drift.md). Canalele `suspension.*` (0..1 din cursa folosită) sunt adăugate din `suspensionM.*`.

Când nu se dă `--surface`, fișierul nu are deloc suprafață, intenționat: o valoare implicită scrisă aici ar suprascrie deducția proprie a vizualizatorului. Vizualizatorul ia atunci suprafața din numele etapei sau al evenimentului (raliuri pe asfalt, de iarnă, Monte ca amestec), altfel din felul în care a fost condusă mașina pe ea (virajele strânse la unghiuri mici de derapaj înseamnă asfalt), iar dacă nimic nu spune, sol afânat - ceea ce este cel mai adesea o etapă de raliu. Dați `--surface` când știți mai bine.
