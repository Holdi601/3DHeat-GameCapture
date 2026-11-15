---
title: "Forza Horizon și Forza Motorsport"
nav_order: 1
lang: "ro"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon și Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Cod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(detectarea structurii),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(fiecare canal, fișierele de ture, retransmiterea).

## Pornirea în joc {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, portul `5300` (sau ce dați ca `--port`). Forza Motorsport oferă și un format de pachet: trebuie să fie **Dash**, nu Sled. Sled nu are deloc poziție, iar înregistratorul îl refuză.

Înregistratorul se leagă de `127.0.0.1`, deci jocul trebuie să ruleze pe același PC.

## Ce trimite jocul și cum se află structura {#what-the-game-sends-and-how-the-layout-is-found}

Data Out este un pachet UDP pe fiecare tic de simulare (aproximativ 60 pe secundă), o structură C plată, little-endian, în aceste dimensiuni:

| Lungime | Variantă |
|---|---|
| 232 de octeți | Motorsport „Sled": fără poziție. Respins, cu un mesaj care spune să treceți pe Dash. |
| 311 de octeți | Motorsport „Dash": blocul Sled plus blocul dash de 79 de octeți |
| 324 de octeți | Horizon „Dash": la fel, cu umplutură între cele două blocuri |
| 331 de octeți | Forza Motorsport (2023): Dash plus 20 de octeți de uzură a anvelopelor și id-ul traseului |

Blocul Sled (decalajele 0-231) este stabil. Unde începe blocul dash în varianta Horizon este descris inconsecvent în sursele publicate, iar a ghici greșit nu eșuează - produce numere în virgulă mobilă plauzibile din câmpurile greșite. Deci începutul este **descoperit**:

1. Începuturile candidate sunt încercate în ordine: `length - 79` (blocul dash ajunge până la ultimul octet în fiecare variantă documentată), 232, 244, și 232 până la 260 din 4 în 4.
2. Fiecare candidat este notat pe pachete de la o mașină în mișcare (o componentă a vitezei peste 1 m/s): vectorul vitezei din blocul Sled și scalarul `Speed` din blocul dash sunt aceeași mărime în două locuri, deci `| |velocity| - Speed |` este aproape zero doar pentru începutul corect.
3. Candidatul cu cea mai mică cea mai proastă dezacord câștigă, dacă dezacordul acela este cel mult **1 m/s**. În caz contrar, detectarea continuă să aștepte.

Cât timp mașina este parcată, fiecare candidat citește zero și toți se înțeleg, ceea ce nu dovedește nimic, deci **detectarea așteaptă până când mașina se mișcă**: conduceți câțiva metri înainte de a aștepta un rezultat. Până la 600 de pachete sunt ținute în așteptare (reduse la ultimele 300). Odată ce structura este cunoscută, pachetele ținute sunt și ele decodate, astfel încât începutul primei ture să nu se piardă. Pachetele de altă lungime decât structura detectată, pachetele mai scurte de 311 octeți și pachetele cu o poziție sau o viteză care nu este finită sunt ignorate pentru fișierele de ture.

Ce Forza este se deduce din structură: o structură Horizon dă `"game": "forza-horizon"`, o structură Motorsport sau de 331 de octeți dă `"forza-motorsport"`, orice altceva `"forza"`. Numele structurii detectate (`Horizon dash`, `Motorsport dash`, `331-byte dash`) este scris ca `layout`.

## Canale înregistrate {#channels-recorded}

Fiecare câmp al pachetului este decodat (`decode_full`) și convertit:

- pedalele `throttle`, `brake`, `clutch`, `handbrake` de la 0..255 la 0..1;
- `steer` de la -127..127 la -1..1; `drivingLine` și `aiBrakeDifference` la fel, împărțite la 127;
- `tireTemp.FL` ... `.RR` din Fahrenheit în Celsius;
- `latAcc`, `longAcc`, `vertAcc` și `yawRate` sunt copii ale `accelX`, `accelZ`, `accelY` și `angVelY` sub nume canonice (cadrul mașinii: x dreapta, y sus, z înainte);
- viteza din Sled, care este în cadrul propriu al mașinii (x dreapta, y sus, z înainte - nu al lumii), este scrisă direct sub numele canonice `latVel`, `vertVel` și `longVel`, astfel încât vizualizatorul citește unghiul de derapaj de acolo în loc să-l estimeze din orientare și traseu.

Fișierul de tură are toate acestea în afară de câmpurile pe tură:

| Grup | Canale |
|---|---|
| Timp și loc | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Mișcare | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Pilot | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Pe fiecare roată (`.FL .FR .RL .RR`) | `suspension` (0 întinsă .. 1 comprimată), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizate: peste 1 anvelopa își pierde aderența), `wheelSpeed` (rad/s), `rumble` (pe o bandă de zgomot), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Doar Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` este cronometrul turei curente al jocului minus valoarea sa la primul eșantion al turei; `distance` este distanța parcursă a jocului minus prima sa valoare. Pozițiile sunt coordonatele lumii Forza în metri, nemodificate (y este sus; lumea este levogiră).

Luate o dată pe tură, nu pe eșantion, sub `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Id-ul traseului FM2023 intră și el o singură dată, ca `lap.trackOrdinal`. Nu sunt păstrate pe eșantion: `isRaceOn` (1 în fiecare cadru al unei ture). `timestampMs`, `raceTime`, `bestLap` și `lastLap` sunt păstrate ca canale.

Restul documentului este completat ca la fiecare alt înregistrator:

- `"track": null` - Forza Horizon nu numește traseul, iar Forza Motorsport doar îl numerotează;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - canalele de alunecare sunt normalizate astfel încât peste 1 anvelopa își pierde aderența;
- `units` listează doar canalele pe care le are fișierul (cele pe fiecare roată după numele lor de bază);
- o valoare care nu este un număr finit este scrisă ca `null`, niciodată ca `NaN`.

Vezi [Fișierul heat3d-lap](lap-format.md).

## Cum se împart turele {#how-laps-are-split}

`LapSplitter` (vezi [Cum se împart turele și etapele](lap-splitting.md)): o tură se închide când contorul de ture al jocului trece mai departe, iar timpul ei este atunci `lastLap` propriu al jocului (ceea ce arată jocul). O cursă punct-la-punct sau o sesiune care se termină în mijlocul unei ture se închide când jocul iese din cursă (`isRaceOn` scade), când pachetele se opresc 2 secunde sau când timestamp-ul jocului sare înapoi; este păstrată ca `run` dacă a acoperit cel puțin 400 m.

## Retransmiterea către FH Companion {#relaying-to-fh-companion}

Jocul trimite Data Out către o singură adresă. Cu `--forward host:port`, înregistratorul trece **fiecare pachet primit neschimbat**, înainte să decodeze ceva (și cât timp așteaptă detectarea structurii), astfel încât o altă aplicație care citește fluxul să funcționeze în continuare: setați jocul pe 5300, cealaltă aplicație pe 5301, și rulați cu `--forward 127.0.0.1:5301`.

FH Companion este o aplicație separată, nu parte din 3DHeat. Ține o bibliotecă de ture în `%LOCALAPPDATA%\FHCompanion\laps`: un dosar pentru fiecare traseu, un fișier de tură pentru fiecare tură, eșantionat aproximativ la fiecare cinci metri, și lângă fiecare fișier de tură `<lap>.json.tele.gz`, întregul Data Out al turei la rata jocului. 3DHeat citește ambele:

- **Vizualizatorul citește direct `.tele.gz`** când îl trageți (cu sau fără fișierul său de tură) în fila Race analysis. Mapează numele de câmpuri ale lui Forza (`PositionX`, `VelocityX`, `TireSlipRatio` + roată, ...) la canalele canonice, transformă `VelocityX/Y/Z` din cadrul mașinii în `latVel`, `vertVel`, `longVel`, convertește temperaturile anvelopelor din Fahrenheit, elimină rândurile care repetă rândul anterior în afară de ceasul înregistratorului și marchează alunecarea ca `peak`. Dacă i se dă și fișierul de tură, tura își ia mașina și timpul din el. Acest cititor se află în vizualizator (`src/race/adapters.ts`, `readForzaTelemetry`), nu în acest depozit.
- **Comanda `laps`** citește biblioteca de ture și scrie traseul unui traseu și un CSV cu fiecare eșantion; vezi [Referința comenzilor](commands.md#laps).

## Alte utilizări ale aceluiași flux {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` înregistrează doar pozițiile, salvate la fiecare câteva secunde în timp ce conduceți; vezi [Referința comenzilor](commands.md#route).
- Opțiunea „Racing telemetry (Forza)" a ferestrei de scanare folosește fluxul ca poziții exacte ale camerei pentru reconstrucție; vezi [Poziția camerei și scara](reconstruction-pose.md#telemetry-poses).

## Note și atenționări {#notes-and-caveats}

- Nu este documentat cu ce normalizează Forza alunecarea. `1` este citit ca marginea aderenței, dar vizualizatorul măsoară unde începe să scape aderența fiecărei mașini.
- Viteza din Sled este locală mașinii, cum spune documentația Data Out a Forza și cum confirmă turele înregistrate (componenta sa înainte poartă viteza, cea laterală rămâne aproape de zero). Detectarea structurii folosește doar lungimea sa, care este aceeași în orice cadru.
- Pozițiile sunt lumea jocului, cu Y sus și levogiră. Sensurile lui `yaw`, `pitch` și `roll` au fost verificate pe ture înregistrate: yaw-ul este egal cu direcția de mers `atan2(dx, dz)`, un pitch pozitiv înseamnă nasul în jos, iar un roll pozitiv coboară partea dreaptă.
