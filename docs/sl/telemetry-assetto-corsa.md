---
title: "Igre Assetto Corsa"
nav_order: 2
lang: "sl"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO in AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Koda: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py). Testi: `tests/test_kunos.py` (sintetične strani). Še ni zagnano proti živim igram.

## Od kod pridejo podatki {#where-the-data-comes-from}

Igre Kunos objavljajo telemetrijo za aplikacije kot **poimenovane strani deljenega pomnilnika v Windows**, ki jih igra piše in jih lahko bere kdorkoli. Snemalnik jih odpre samo za branje (`mmap` z oznako imena), zato mora teči **na računalniku, kjer teče igra**, v Windows; drugje konča z napisom.

Strani se odprejo enkrat, ob zagonu snemalnika. Najbolj varen vrstni red je najprej zagnati igro in sesti v avto; ali deluje zagon snemalnika pred igro, ni preverjeno.

| `--game` | Fizikalna stran | Grafična stran (števec krogov) | Statična stran (imena) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ni v uporabi | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ni v uporabi | `Local\acevo_pmf_static` |

Fizikalna stran se bere 200-krat na sekundo (`hz=200`); nov vzorec se vzame samo, kadar se njen `packetId` spremeni in ni nič. Prvih 800 bajtov fizikalne strani ima isto postavitev v vseh štirih igrah; prva igra ima zajamčenih samo 580 bajtov, zato se snemalnik, če preslikave dolžine 800 bajtov ni mogoče odpreti, vrne na 580, polja za tem pa so odsotna.

## Položaj {#position}

Nobena stran ne nosi položaja avta kot takega, fizikalna stran pa ima **svetovne koordinate točke stika vsake gume** (odmik 420, štiri trojke XYZ). Položaj avta je povprečje teh štirih. Stran, na kateri so vse točke stika ničle (meni, garaža), ne da vzorca.

## Kanali {#channels}

| Kanal | Od kod | Opombe |
|---|---|---|
| `time` | lastna ura snemalnika | sekunde od začetka snemanja, premaknjene na prvi vzorec kroga |
| `x`, `y`, `z` | povprečna točka stika gume | svetovni metri |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | enote igre, na krog preračunane na -1..1 po največji absolutni vrednosti, ki jo je krog uporabil, **samo če ta vrednost presega 1,05** (vnos, ki je že v -1..1, ostane nedotaknjen) |
| `gear` | `gear - 1` | igra šteje 0 vzvratna, 1 prosti tek, 2 prva; zapisano kot -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, pomnoženo z 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokalna hitrost na odmiku 568 | koordinatni sistem avta; samo kadar ni nič. Na katero stran kaže x, je dokumentirano na obe strani, zato berite velikost kota drifta, ne njegovega predznaka |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | odmik 564 | samo stran dolžine 800 bajtov |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: odmiki 204 in 252, zapisano kot 1, kadar je nad 0; AC: `tcInAction`/`absInAction` iz strani dolžine 800 bajtov, kadar je prisotna | pomoči delujejo |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | izpeljano | 0..1 pota, ki ga je krog uporabil (najmanj do največ `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | odmiki 640, 656 (stran dolžine 800 bajtov) | deljeno s tipičnim vrhom – glejte spodaj |
| `slipRatioRaw.*`, `slipAngleRaw.*` | isto | fizikalne vrednosti, neskalirane |
| `padLife.*`, `discLife.*` | odmiki 740, 756 | samo stran dolžine 800 bajtov |

AC Rally pošilja temperature gum in zavor v kelvinih: za `--game acrally` se od vsake take vrednosti nad 200 odšteje 273,15.

`wheelSlip` (odmik 56) se dekodira, vendar se ne zapiše.

## Skaliranje zdrsa {#slip-scaling}

Forza pošilja zdrs normiran tako, da je 1 rob oprijema. Kunos pošilja fizikalni zdrs razmerja in kot zdrsa. Zato snemalnik deli z običajnim vrhom na asfaltu – **0,12** za zdrs razmerja in **0,14 rad (približno 8 stopinj)** za kot zdrsa – tako da bralni pomen pregledovalnika "nad 1 pomeni zdrsavanje" približno drži; surove vrednosti ohrani poleg skaliranih in zapiše `"meta": {"slip": "scaled"}`. Kje se oprijem dejansko konča, pregledovalnik izmeri za vsak avto iz samih krogov. Glejte [Zdrs, drift in izpeljani kanali](slip-and-drift.md).

## Krogi {#laps}

- **AC in ACC** štejeta kroge na grafični strani (`completedLaps` na odmiku 132, čas zadnjega kroga v milisekundah na 144). `CounterSplitter` zaključi krog, ko se števec spremeni; krog je označen kot dokončan, z igrinim časom kroga, samo če se je števec povečal za točno ena.
- **AC EVO in AC Rally** se za kroge ne berejo (grafična stran EVO je drugačne, večje postavitve; AC Rally vozi etape). `LineSplitter` za črto vzame točko, kjer se je snemanje začelo: krog se zapre, ko avto naslednjič prečka najbližje tej točki v isto smer, etapa ali katera koli vožnja pa se zapre, ko avto stoji 8 sekund.

Podrobnosti in pragovi: [Razdeljevanje krogov in etap](lap-splitting.md).

## Imena prog in avtomobilov {#track-and-car-names}

Preberejo se enkrat iz statične strani, ko pride prvi vzorec: za AC, ACC in AC Rally avto (UTF-16, odmik 68) in progo (odmik 134); za AC EVO progo in njeno konfiguracijo (enobajtno besedilo na odmikih 136 in 169, združeno s presledkom) in brez avta. Zapišeta se v datoteko kot `track` in `car: {"name": ...}`.

## Datoteka kroga {#the-lap-file}

`game` je `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ali `assetto-corsa-rally`; `meta` je `{"slip": "scaled", "discipline": "rally"}` za AC Rally in `{"slip": "scaled", "discipline": "circuit"}` za ostale tri. `surface` se ne zapiše.

## Viri {#sources}

Vodnik za deljeni pomnilnik AC1 SDK; dokumentacija deljenega pomnilnika ACC (v1.8); postavitev AC EVO, izmerjena v `albertowd/live-telemetry-evo`; postavitev AC Rally, kot jo bere `LuizZak/AssettoCorsaRallyTelemetryReader`. Glejte [Igre](games.md).
