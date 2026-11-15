---
title: "Assetto Corsa, ACC, AC EVO og AC Rally"
nav_order: 2
lang: "da"
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
Tests: `tests/test_kunos.py` (syntetiske sider). Ikke kørt mod de live spil endnu.

## Hvor dataene kommer fra {#where-the-data-comes-from}

Kunos' spil udgiver telemetri til apps som **navngivne Windows-sider i delt hukommelse**, som spillet skriver, og som alle må læse. Optageren åbner dem skrivebeskyttet (`mmap` med et mærkenavn), så den skal køre **på den pc, spillet kører på**, på Windows; ellers stopper den med en besked. Siderne åbnes én gang, når optageren starter. Den sikre rækkefølge er at starte spillet og komme ind i bilen først; om det virker at starte optageren før spillet, er ikke kontrolleret.

| `--game` | Fysiksiden | Grafiksiden (omgangstæller) | Statisk side (navne) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ikke brugt | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ikke brugt | `Local\acevo_pmf_static` |

Fysiksiden læses 200 gange i sekundet (`hz=200`); en ny prøve tages kun, når dens `packetId` har ændret sig og ikke er nul. De første 800 bytes af fysiksiden har ét layout i alle fire spil; det første spils side er kun garanteret 580 bytes, så hvis en 800-byte-mapning ikke kan åbnes, falder optageren tilbage til 580, og felterne ud over dem mangler.

## Position {#position}

Ingen af siderne bærer en bilposition som sådan, men fysiksiden har **hvert dæks kontaktpunkt i verdenskoordinater** (forskydning 420, fire XYZ-tripler). Bilens position er gennemsnittet af de fire. En side, hvor alle kontaktpunkter er nul (menu, garage), giver ingen prøve.

## Kanaler {#channels}

| Kanal | Fra | Noter |
|---|---|---|
| `time` | optagerens eget ur | sekunder siden optagelsen begyndte, omregnet til omgangens første prøve |
| `x`, `y`, `z` | gennemsnit af dækkenes kontaktpunkt | verdenens meter |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | spillets enheder, skaleret pr. omgang til -1..1 efter den største absolutte værdi, omgangen brugte, **kun hvis** den værdi er over 1,05 (et input, der allerede er i -1..1, lades være) |
| `gear` | `gear - 1` | spillet tæller 0 bak, 1 neutral, 2 første gear; skrevet som -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, gange 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokal hastighed ved forskydning 568 | bilens ramme; kun når den ikke er nul. Hvilken side x peger mod, er dokumenteret begge veje, så læs driftvinklens størrelse, ikke dens fortegn |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | forskydning 564 | kun 800-byte-siden |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: forskydningerne 204 og 252, skrevet som 1 når over 0; AC: `tcInAction`/`absInAction` fra 800-byte-siden, når den findes | hjælpesystemer i brug |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | udledt | 0..1 af det vej, omgangen brugte (min til maks af `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | forskydninger 640, 656 (800-byte-siden) | divideret med en typisk top - se nedenfor |
| `slipRatioRaw.*`, `slipAngleRaw.*` | det samme | de fysiske værdier, uskalerede |
| `padLife.*`, `discLife.*` | forskydninger 740, 756 | kun 800-byte-siden |

AC Rally sender sine dæk- og bremsetemperaturer i kelvin: for `--game acrally` trækkes 273,15 fra alle disse værdier, der er over 200.

`wheelSlip` (forskydning 56) afkodes, men skrives ikke.

## Skalering af slip {#slip-scaling}

Forza sender slip normaliseret, så 1 er grænsen for greb. Kunos sender det fysiske slip-forhold og slip-vinklen. Derfor divideres de af optageren med en typisk asfalttop - **0,12** for slip-forholdet og **0,14 rad (cirka 8 grader)** for slip-vinklen - så viewer'ens læsning "over 1 betyder glidning" holder cirka, de rå værdier gemmes ved siden af dem, og filen skriver `"meta": {"slip": "scaled"}`. Hvor greb reelt slutter, måler viewer'en pr. bil ud fra omgangene. Se [Slip, drift og afledte kanaler](slip-and-drift.md).

## Omgange {#laps}

- **AC og ACC** tæller omgange på grafiksiden (`completedLaps` ved forskydning 132, den sidste omgangs tid i millisekunder ved 144). `CounterSplitter` lukker en omgang, når tælleren ændrer sig; den markeres som afsluttet, med spillets omgangstid, kun hvis tælleren steg med præcis én.
- **AC EVO og AC Rally** læses ikke for omgange (EVO's grafikside har et andet, større layout; AC Rally kører etaper). `LineSplitter` bruger det sted, hvor optagelsen begyndte, som linje: en omgang lukkes, når bilen næste gang passerer tættest på den og kører samme vej, og en etape eller en vilkårlig kørsel lukkes, når bilen står stille i 8 sekunder.

Detaljer og grænseværdier: [Opdeling i omgange og etaper](lap-splitting.md).

## Navne på bil og bane {#track-and-car-names}

Læses én gang fra den statiske side, når den første prøve kommer: for AC, ACC og AC Rally bilen (UTF-16, forskydning 68) og banen (forskydning 134); for AC EVO banen og dens konfiguration (enkeltbyte-tekst ved forskydningerne 136 og 169, sammenføjet med et mellemrum) og ingen bil. De skrives til filen som `track` og `car: {"name": ...}`.

## Omgangsfilen {#the-lap-file}

`game` er `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` eller `assetto-corsa-rally`; `meta` er `{"slip": "scaled", "discipline": "rally"}` for AC Rally og `{"slip": "scaled", "discipline": "circuit"}` for de tre andre. Der skrives ingen `surface`.

## Kilder {#sources}

AC1's SDK for delt hukommelse; ACC's dokumentation for delt hukommelse (v1.8); AC EVO's layout, målt i `albertowd/live-telemetry-evo`; AC Rallys layout, som læst af `LuizZak/AssettoCorsaRallyTelemetryReader`. Se [Spil](games.md).
