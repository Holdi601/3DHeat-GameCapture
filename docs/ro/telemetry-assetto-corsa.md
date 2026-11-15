---
title: "Jocurile Assetto Corsa"
nav_order: 2
lang: "ro"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO și AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Cod: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Teste: `tests/test_kunos.py` (pagini sintetice). Nerulate încă pe jocurile live.

## De unde vin datele {#where-the-data-comes-from}

Jocurile Kunos publică telemetrie pentru aplicații ca **pagini de memorie partajată Windows cu nume**, pe care jocul le scrie și pe care oricine le poate citi. Înregistratorul le deschide doar pentru citire (`mmap` cu un nume de etichetă), deci trebuie să ruleze **pe PC-ul pe care rulează jocul**, pe Windows; în altă parte iese cu un mesaj.
Paginile se deschid o singură dată, când pornește înregistratorul. Ordinea sigură este pornirea jocului și urcatul în mașină întâi; dacă pornirea înregistratorului înaintea jocului funcționează nu a fost verificat.

| `--game` | Pagina fizicii | Pagina graficii (contorul de ture) | Pagina statică (nume) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nefolosită | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nefolosită | `Local\acevo_pmf_static` |

Pagina fizicii este citită de 200 de ori pe secundă (`hz=200`); un eșantion nou este luat doar când `packetId` s-a schimbat și nu este zero. Primii 800 de octeți ai paginii fizicii au aceeași structură în toate cele patru jocuri; pagina primului joc este garantată doar pe 580 de octeți, deci dacă o mapare de 800 de octeți nu poate fi deschisă, înregistratorul revine la 580, iar câmpurile de după sunt absente.

## Poziția {#position}

Nicio pagină nu conține poziția mașinii ca atare, dar pagina fizicii conține **punctul de contact cu solul al fiecărei anvelope în coordonate ale lumii** (decalaj 420, patru triplete XYZ). Poziția mașinii este media celor patru. O pagină pe care toate punctele de contact sunt zero (meniu, garaj) nu produce niciun eșantion.

## Canale {#channels}

| Canal | Din | Observații |
|---|---|---|
| `time` | ceasul propriu al înregistratorului | secunde de la începutul înregistrării, reașezate la primul eșantion al turei |
| `x`, `y`, `z` | media punctelor de contact ale anvelopelor | metri în lume |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | unitățile jocului, scalate pe tură la -1..1 după cea mai mare valoare absolută folosită de tură, **doar dacă** această valoare depășește 1,05 (o intrare deja în -1..1 rămâne neschimbată) |
| `gear` | `gear - 1` | jocul numără 0 mers înapoi, 1 neutru, 2 întâi; scrise ca -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, înmulțit cu 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | viteza locală la decalajul 568 | cadrul mașinii; doar când nu este zero. Sensul în care indică x este documentat în ambele sensuri, deci citiți mărimea unghiului de derapaj, nu semnul |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | decalajul 564 | doar pagina de 800 de octeți |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: decalajele 204 și 252, scrise ca 1 când sunt peste 0; AC: `tcInAction`/`absInAction` din pagina de 800 de octeți, când există | asistențele active |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | derivat | 0..1 din cursa folosită de tura aceasta (minim până la maxim din `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | decalajele 640, 656 (pagina de 800 de octeți) | împărțite la un vârf tipic - vezi mai jos |
| `slipRatioRaw.*`, `slipAngleRaw.*` | la fel | valorile fizice, nescalate |
| `padLife.*`, `discLife.*` | decalajele 740, 756 | doar pagina de 800 de octeți |

AC Rally trimite temperaturile anvelopelor și ale frânelor în kelvin: pentru `--game acrally`, orice valoare a acestora peste 200 are scăzut 273,15.

`wheelSlip` (decalajul 56) este decodat, dar nu este scris.

## Scalarea alunecării {#slip-scaling}

Forza trimite alunecarea normalizată astfel încât 1 este marginea aderenței. Kunos trimite raportul fizic de alunecare și unghiul de alunecare. Deci înregistratorul le împarte la un vârf tipic de asfalt - **0,12** pentru raportul de alunecare și **0,14 rad (aproximativ 8 grade)** pentru unghiul de alunecare - astfel încât citirea vizualizatorului „peste 1 înseamnă alunecare" să se țină aproximativ, păstrează valorile brute lângă ele și scrie `"meta": {"slip": "scaled"}`. Unde se termină de fapt aderența, vizualizatorul măsoară pe mașină din ture. Vezi [Alunecare, derapaj și canale derivate](slip-and-drift.md).

## Ture {#laps}

- **AC și ACC** numără turele pe pagina graficii (`completedLaps` la decalajul 132, timpul ultimei ture în milisecunde la 144). `CounterSplitter` închide o tură când contorul se schimbă; este marcată completă, cu timpul jocului, doar dacă contorul a crescut exact cu unu.
- **AC EVO și AC Rally** nu sunt citite pentru ture (pagina graficii a EVO este o structură diferită, mai mare; AC Rally conduce etape). `LineSplitter` folosește punctul unde a început înregistrarea drept linie: o tură se închide când mașina trece următoarea dată cel mai aproape de ea, mergând în același sens, iar o etapă sau orice rulare se închide când mașina stă pe loc timp de 8 secunde.

Detalii și praguri: [Cum se împart turele și etapele](lap-splitting.md).

## Numele traseului și al mașinii {#track-and-car-names}

Citite o singură dată, din pagina statică, când sosește primul eșantion: pentru AC, ACC și AC Rally mașina (UTF-16, decalajul 68) și traseul (decalajul 134); pentru AC EVO traseul și configurația lui (text de un octet la decalajele 136 și 169, unite printr-un spațiu) și fără mașină. Ele intră în fișier ca `track` și `car: {"name": ...}`.

## Fișierul de tură {#the-lap-file}

`game` este `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` sau `assetto-corsa-rally`; `meta` este `{"slip": "scaled", "discipline": "rally"}` pentru AC Rally și `{"slip": "scaled", "discipline": "circuit"}` pentru celelalte trei. Nu se scrie niciun `surface`.

## Surse {#sources}

SDK-ul AC1 de memorie partajată; documentația memoriei partajate ACC (v1.8); layout-ul AC EVO așa cum a fost măsurat în `albertowd/live-telemetry-evo`; cel al AC Rally așa cum este citit de `LuizZak/AssettoCorsaRallyTelemetryReader`. Vezi [Jocuri](games.md).
