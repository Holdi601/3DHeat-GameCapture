---
title: "BeamNG.drive"
nav_order: 4
lang: "ro"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copiază modificarea, apoi înregistrează
python -m heat3d_capture telemetry --game beamng -o laps      # înregistrează
```

Apoi în joc: **Options > Other > Protocols**, porniți **„others”**.

Cod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
și modificarea [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Teste: `tests/test_beamng.py`, pe pachete construite din structura modificării. **Modificarea nu a fost
încă rulată în joc.**

## De ce o modificare {#why-a-mod}

BeamNG trimite telemetrie prin „protocoale”: module Lua din vehicul, pe care protocols.lua propriu al
jocului le împachetează și le trimite prin UDP din mașina pe care o conduce jucătorul. Protocoalele
standard nu duc ce are nevoie o analiză a controlului mașinii - OutGauge nu are poziție, MotionSim nu
are roți, iar OutSim este un stub în versiunile actuale. Așa că proiectul livrează propriul protocol,
`heat3d`. Nu atinge nimic în afara Lua-ului vehiculului.

## Instalarea {#installing}

`--install` copiază `mods/beamng/heat3d` în
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 și versiunile
ulterioare țin acolo modificările utilizatorului), ștergând mai întâi o copie mai veche, și afișează
unde a ajuns. Fără `LOCALAPPDATA`, folosește folderul de acasă. Puteți copia și folderul manual.

`--install` continuă apoi direct cu înregistrarea.

## Modificarea {#the-mod}

| Setare (în `heat3d.lua`) | Valoare |
|---|---|
| Adresă | `127.0.0.1` |
| Port | `4460` - schimbați-l aici și transmiteți același `--port` înregistratorului |
| Rata maximă de actualizare | 100 Hz |
| Pas de fizică | folosit (`isPhysicsStepUsed` returnează adevărat) |

Fiecare pachet este marcajul de 4 octeți `H3D1`, urmat de 39 de numere reale în format little-endian
(160 de octeți în total):

| Câmp | Număr | Sursa în Lua-ul vehiculului |
|---|---|---|
| `time` | 1 | ceasul propriu al modificării: suma pașilor de fizică, resetat când vehiculul se resetează |
| poziție | 3 | `obj:getPositionXYZ()` |
| viteză | 3 | `obj:getVelocityXYZ()` (în lume) |
| înainte | 3 | `obj:getDirectionVector()` |
| sus | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, și 1/0 din `absActive` și `tcsActive` |
| `wheelSpeed` | 4 | viteza de suprafață a fiecărei roți (m/s) |
| `wheelAngular` | 4 | viteza unghiulară înmulțită cu direcția roții (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 când roata nu atinge solul |

Cele patru roți sunt alese după **unde stau pe mașină**, nu după nume (numele diferă între vehicule):
față sau spate după poziția nodului de-a lungul mașinii, stânga sau dreapta pe lățime (cadrul
vehiculului: +X stânga, -Y înainte), luând pentru fiecare colț roata cea mai departe de centru. Un colț
lipsă este trimis ca zerouri, cu materialul -1.

## Ce face înregistratorul cu ea {#what-the-recorder-does-with-it}

Lumea BeamNG are Z în sus; cea a vizualizatorului are Y în sus. Pozițiile și vectorii sunt rotiți în
jurul axei X, `(x, y, z) -> (x, z, -y)`, ceea ce păstrează sistemul de coordonate al lumii. Apoi:

| Canal | Calculat ca |
|---|---|
| `x`, `y`, `z` | poziția rotită |
| `speed` | lungimea vitezei rotite |
| `longVel`, `latVel`, `vertVel` | viteza proiectată pe înainte, pe dreapta = înainte x sus, pe sus |
| `longAcc`, `latAcc`, `vertAcc` | schimbarea vitezei în lume pe ±2 eșantioane, proiectată pe aceleași axe (cadrul senzorilor mașinii nu este documentat, așa că nu se folosesc) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | cum au fost trimise |
| `absActive`, `tcActive` | lămpile ABS și TC, acolo unde mașina le are |
| `wheelSurfaceSpeed.*` | valoarea absolută a vitezei de suprafață a roții |
| `wheelSpeed.*` | rotația |
| `wheelLoad.*` | sarcina |
| `groundContact.*` | 0 când materialul este negativ, altfel 1 |

Pachetele fără marcaj sau mai scurte de 160 de octeți sunt ignorate.

## Ture {#laps}

`LineSplitter`, ca la AC EVO: punctul unde a început înregistrarea este linia; un tur se închide acolo
unde mașina trece din nou cel mai aproape de el, având același sens, cel puțin 300 m mai târziu; o
rulare se închide când mașina stă pe loc 8 secunde. Un tur se consideră complet doar dacă a început cu
peste 5 m/s, astfel încât primul tur dintr-o pornire de pe loc este unul parțial. Când ceasul
modificării dă înapoi cu mai mult de o jumătate de secundă (mașina a fost resetată), rularea deschisă
în acel moment este închisă mai întâi - scrisă ca rulare parțială dacă a acoperit cel puțin 300 m, ca
la sfârșitul unei înregistrări - și apoi despicătorul începe de la capăt. Vezi
[Împărțirea în ture și etape](lap-splitting.md).

## Fișierul turului {#the-lap-file}

`game` este `beamng`, `meta` este `{"discipline": "circuit"}`, fișierele se numesc
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Nu se scrie niciun slip; vizualizatorul îl calculează
din vitezele de suprafață ale roților (vezi [Slip, derapaj și canale derivate](slip-and-drift.md)).
Pozițiile sunt în același cadru în care le scrie exportul de traseu BeamNG din GameFiles, astfel încât
un tur înregistrat stă exact pe un traseu exportat.
