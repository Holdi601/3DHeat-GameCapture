---
title: "Assetto Corsa-spill"
nav_order: 2
lang: "no"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO og AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kode: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tester: `tests/test_kunos.py` (syntetiske sider). Ikke kjørt mot de levende spillene ennå.

## Hvor dataene kommer fra {#where-the-data-comes-from}

Kunos' spill publiserer telemetri for apper som **navngitte sider i Windows delt minne**, som spillet skriver og
alle kan lese. Opptakeren åpner dem skrivebeskyttet (`mmap` med et merkenavn), så den må kjøre **på PC-en spillet
kjører på**, i Windows; ellers avslutter den med en melding. Sidene åpnes én gang, når opptakeren starter. Å starte
spillet og komme inn i bilen først er den trygge rekkefølgen; om det fungerer å starte opptakeren før spillet, er ikke kontrollert.

| `--game` | Fysikkside | Grafikkside (rundeteller) | Statisk side (navn) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ikke brukt | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ikke brukt | `Local\acevo_pmf_static` |

Fysikksiden leses 200 ganger i sekundet (`hz=200`); en ny prøve tas bare når dens `packetId` har endret seg og er
ikke-null. De første 800 bytene på fysikksiden har ett oppsett i alle fire spillene; den første spillets side er bare
garantert 580 bytes, så hvis en 800-byte-avbildning ikke kan åpnes, faller opptakeren tilbake til 580, og feltene
utover dem mangler.

## Posisjon {#position}

Ingen av sidene bærer en bilposisjon som sådan, men fysikksiden har **hvert dekks kontaktpunkt i verdenskoordinater**
(forskyvning 420, fire XYZ-trillinger). Bilens posisjon er gjennomsnittet av de fire. En side der alle kontaktpunktene er null
(meny, garasje) gir ingen prøve.

## Kanaler {#channels}

| Kanal | Fra | Merknad |
|---|---|---|
| `time` | opptakerens egen klokke | sekunder siden opptaket startet, omregnet til rundens første prøve |
| `x`, `y`, `z` | gjennomsnittlig dekkkontaktpunkt | verdensmeter |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | spillets enheter, skalert per runde til -1..1 etter den største absoluttverdien runden brukte, **bare hvis** den verdien er over 1,05 (en inndata som allerede er i -1..1 røres ikke) |
| `gear` | `gear - 1` | spillet teller 0 revers, 1 nøytral, 2 første; skrives som -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, ganget med 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokal fart ved forskyvning 568 | bilens ramme; bare når ikke-null. Hvilken side x peker mot er dokumentert begge veier, så les driftvinkelens størrelse, ikke fortegnet |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | forskyvning 564 | bare 800-byte-siden |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: forskyvning 204 og 252, skrevet som 1 når over 0; AC: `tcInAction`/`absInAction` fra 800-byte-siden når den finnes | hjelpesystemer i bruk |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | utledet | 0..1 av utslaget denne runden brukte (minimum til maksimum av `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | forskyvninger 640, 656 (800-byte-siden) | delt på en typisk topp - se under |
| `slipRatioRaw.*`, `slipAngleRaw.*` | det samme | de fysiske verdiene, uskalert |
| `padLife.*`, `discLife.*` | forskyvninger 740, 756 | bare 800-byte-siden |

AC Rally sender sine dekk- og bremsetemperaturer i kelvin: for `--game acrally` trekkes 273,15 fra alle disse verdiene
som er over 200.

`wheelSlip` (forskyvning 56) dekodes, men skrives ikke.

## Sklískalering {#slip-scaling}

Forza sender sklí normalisert slik at 1 er grensen for grep. Kunos sender den fysiske sklíforholdet og sklívinkelen. Så
opptakeren deler dem på en typisk asfalttopp - **0,12** for sklíforholdet og **0,14 rad (omtrent 8 grader)** for
sklívinkelen - slik at viewers "over 1 betyr at den sliper" holder omtrent, beholder de rå verdiene ved siden av, og skriver
`"meta": {"slip": "scaled"}`. Der grepet faktisk tar slutt, måler viewer per bil fra rundene. Se [Skli, drift og avledede kanaler](slip-and-drift.md).

## Runder {#laps}

- **AC og ACC** teller runder på grafikksiden (`completedLaps` ved forskyvning 132, siste runde i millisekunder ved 144).
  `CounterSplitter` lukker en runde når telleren endrer seg; den merkes fullført, med spillets rundetid, bare hvis telleren gikk opp med nøyaktig én.
- **AC EVO og AC Rally** leses ikke for runder (EVOs grafikkside er et annet, større oppsett; AC Rally kjører etapper). `LineSplitter` bruker
  punktet der opptaket startet som linje: en runde lukkes når bilen neste gang passerer nærmest den i samme retning, og en etappe eller en hvilken
  som helst kjøring lukkes når bilen står stille i 8 sekunder.

Detaljer og terskler: [Hvordan runder og etapper deles](lap-splitting.md).

## Bane- og bilnavn {#track-and-car-names}

Leses én gang, fra den statiske siden, når første prøve kommer: for AC, ACC og AC Rally bilen (UTF-16, forskyvning 68) og banen
(forskyvning 134); for AC EVO banen og dens konfigurasjon (enkelt-byte-tekst ved forskyvningene 136 og 169, satt sammen med et mellomrom)
og ingen bil. De havner i filen som `track` og `car: {"name": ...}`.

## Rundefilen {#the-lap-file}

`game` er `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` eller `assetto-corsa-rally`; `meta` er
`{"slip": "scaled", "discipline": "rally"}` for AC Rally og `{"slip": "scaled", "discipline": "circuit"}` for de tre andre.
Ingen `surface` skrives.

## Kilder {#sources}

AC1-SDK-en for delt minne; dokumentasjonen for ACCs delte minne (v1.8); AC EVOs oppsett slik det er målt i
`albertowd/live-telemetry-evo`; AC Rallys slik det leses av `LuizZak/AssettoCorsaRallyTelemetryReader`. Se [Spill](games.md).
