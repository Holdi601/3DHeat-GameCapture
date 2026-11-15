---
title: "Rallyspil"
nav_order: 3
lang: "da"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # eller dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kode: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tests: `tests/test_rally.py`, på pakker bygget efter de dokumenterede layouts. **Ikke kørt mod de live spil endnu.**

Alle sender UDP, som spillet slår til fra sine egne indstillingsfiler. Optageren lytter på alle grænseflader (`0.0.0.0`) på spillets standardport, medmindre `--port` giver en anden: **20777** for `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** for `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Slå det til {#switching-it-on}

Spillet læser `Documents\My Games\WRC\telemetry\config.json`. Standardstrukturen `wrc`s pakke `session_update` skal være slået til mod denne maskine:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<sti til config.json>"
```

`--configure` (funktionen `configure_wrc`):

- læser JSON'en, finder `udp.packets` og posten med `"structure": "wrc"` og `"packet": "session_update"`;
- hvis den allerede er slået til `127.0.0.1` eller `localhost` på den port, der bruges, skrives `already on`, og intet ændres;
- ellers sættes `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, og posten `frequencyHz` beholdes (eller `-1`, hvis der ingen er); findes posten ikke, tilføjes en;
- den oprindelige tekst skrives til `config.json.bak` ved siden af, derefter skrives den nye fil (indrykket med 4 mellemrum).

Genstart spillet efter ændring af filen, hvis det ikke opfanger ændringen (ikke kontrolleret).

### Hvad det sender {#what-it-sends}

Standardstrukturen `wrc` er 237 bytes, little-endian, uden header: verdensposition, hastighed og acceleration (X til venstre, Y op, Z fremad), bilens venstre/fremad/op-enhedsvektorer, pr. hjul (bagvenstre, bagerste højre, forvenstre, forreste højre) hjulnavens højde og lodrette hastighed og kontaktfladens hastighed fremad, bremsetemperaturer, pedaler efter hjælpesystemer, styring (-1 venstre, +1 højre), håndbremse, rpm, gear og etapeuret, -distancen og -længden. En pakke kortere end 237 bytes ignoreres og meldes én gang.

| Kanal | Fra |
|---|---|
| `x`, `y`, `z` | verdensposition |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | verdenshastighed projiceret på fremad, på minus venstre (så positiv er højre), på op |
| `longAcc`, `latAcc`, `vertAcc` | verdensacceleration projiceret på samme måde |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | som sendt |
| `gear` | `gear_index`; -1 når den er lig med bakgearets indeks, 0 når den er lig med neutralindekset |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | navens position |
| `wheelSurfaceSpeed.*` | kontaktfladens hastighed fremad |
| `brakeTemp.*` | bremsetemperatur |

Kontrol: er `speed` over 10, og længden af verdenshastighedsvektoren afviger fra den med mere end 20 %, skriver optageren én gang, at layoutet måske ikke er standardstrukturen `wrc`.

En etape er **færdig**, når etapelængden er positiv, og distancen har nået længden minus 0,5 m. Uret, der bruges til opdeling og til `time`, er `stage_time`.

Kilder: EA's UDP Telemetry Guide v1.3; kanallisten spillet skriver til `readme/channels.json`; forskydninger som afkodet af nobonobo/obs-codemasters-telemetry og SpaceMonkey. Standardporten for spillet er ikke dokumenteret; optageren bruger 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Slå det til {#switching-it-on-1}

Redigér `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally og DiRT 4 bruger også en `hardware_settings_config.xml`; deres præcise mappe til dem to er ikke kontrolleret her), så elementet `udp` lyder:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` er det, der lægger positioner, hjul og etapelængden i pakken. Optageren redigerer ikke denne fil.

### Hvad det sender {#what-it-sends-1}

66 little-endian decimaltal (DiRT Rally: 64); pakker kortere end 64 decimaltal ignoreres, og en pakke på 64 decimaltal udfyldes med nuller. De brugte indekser:

| Indeks | Felt | Kanal |
|---|---|---|
| 1 | omgangs- (etape-) tid | opdelingsuret og `time` |
| 2 | omgangsdistance | `stageDistance` |
| 4-6 | verdensposition | `x`, `y`, `z` |
| 7 | hastighed | `speed` |
| 8-10 | verdenshastighed | `longVel` (på fremad), `latVel` (på sidevektoren) |
| 11-13 | sidevektor | |
| 14-16 | fremadvektor | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | fjederposition RL RR FL FR | `suspensionM.*` |
| 25-28 | hjulets kontaktfladehastighed RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gas, styring, bremse, kobling, gear | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 eller mere betyder bak, skrevet som -1) |
| 34, 35 | sidelæns og længdegående g | `latAcc`, `longAcc` (gange 9,80665) |
| 37 | rpm / 10 | `rpm` (gange 10) |
| 51-54 | bremsetemperaturer | `brakeTemp.*` |
| 59, 60, 61, 62 | gennemførte omgange, samlede omgange, banelængde, sidste omgangstid | opdeling |

Der er **ingen håndbremsekanal**. Sidevektorens retning er dokumenteret begge veje, så fortegnet for `latVel` skal ikke stoles på (viewer'en læser driftvinklens størrelse).

En etape er **færdig**, når antallet af gennemførte omgange stiger over sin værdi ved etapens start (en rallycross-omgang hver gang det sker), eller, for en begivenhed med én omgang, når omgangsdistancen når 99,9 % af banens længde. Etapens tid er spillets sidste omgangstid, når den er positiv. Kontrol: hastighed mod fart som for EA WRC, med beskeden "is extradata set to 3?".

Kilder: Codemasters' UDP-dokument for DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Slå det til {#switching-it-on-2}

I `RichardBurnsRally.ini`, sektionen `[NGP]`: `udpTelemetry=1` og endepunktet (127.0.0.1, port 6776, medmindre du giver en anden med `--port`). Optageren redigerer ikke denne fil.

### Hvad det sender {#what-it-sends-2}

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): etapeur og distance til enden, pedaler, styring, gear, verdensposition, attityde, bilens egne hastigheder (fremad, sideværts, op), accelerationer, rpm og fire 128-byte hjulblokke (LF, RF, LB, RB) med fjederudbøjning og fjederkraft. Ingen hjulhastigheder.

| Kanal | Fra |
|---|---|
| `x`, `y`, `z` | position, akser som sendt, derefter omsorteret (se nedenfor) |
| `longVel`, `latVel`, `vertVel` | fremad, sidelæns, op |
| `longAcc`, `latAcc` | acceleration x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | som sendt |
| `gear` | `gear - 1` (0 bak, 1 neutral, 2 første gear) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | fjederudbøjning |
| `wheelLoad.*` | fjederkraft |
| `speed` | **udregnet fra positionerne** over ±2 prøver, ikke taget fra pakken |

RBR's positionsakser, attitudeenheder og hastighedsenhed er ikke dokumenteret, så når en etape skrives: aksen, etapen varierer mindst langs, tages som op og byttes over i `y` (`orient_up`, kræver mindst 10 prøver), og hastigheden udregnes igen ud fra positionerne (`speed_from_positions`). Attitude afkodes, men skrives ikke, så RBR-filer har ingen `yaw`.

En etape er **færdig**, når løbsuret kører, og afstanden til enden er nået nul. Uret er `race_time`.

Kilder: NGP's `rbr.telemetry.data.TelemetryData.h` via mika-n/RBRUDPTelemetryLogger og groybe/rbr-udp-telem.

## Etaper {#stages}

Alle fem bruger `StageSplitter` på spillets etapeur: en etape åbnes, når uret starter, og lukkes afsluttet, når spillet siger, at bilen er færdig; et ur, der går tilbage (en genstart eller den næste etape), opgiver den åbne etape - den gemmes som en `_partial`-fil, hvis den har mere end 10 prøver og mindst 300 m. Afsluttede etaper kortere end 300 m skrives ikke. Detaljer: [Opdeling i omgange og etaper](lap-splitting.md).

## Omgangsfilen {#the-lap-file}

`game` er `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` eller `richard-burns-rally`. `meta` er `{"discipline": "rally", "slip": null}`, plus `"surface": "<værdi>"`, når `--surface` blev givet. `slip` er null, fordi ingen af disse spil sender dæk-slip. Hvert hjuls kontaktfladehastighed (EA WRC, DiRT) ligger i filen i stedet; viewer'en udleder slip og driftvinklen ud fra den og bilens akser; se [Slip, drift og afledte kanaler](slip-and-drift.md). `suspension.*`-kanalerne (0..1 af den brugte vej) tilføjes ud fra `suspensionM.*`.

Når der ikke gives `--surface`, har filen med vilje intet underlag: en standard skrevet her ville overskrive viewer'ens egen udledning. Viewer'en tager så underlaget fra etapens eller begivenhedens navn (asfaltløb, vinterløb, Monte som blandet), ellers ud fra hvordan bilen blev kørt på det (hård kørsel i sving med små driftvinkler er asfalt), og løst, når intet siger det - det er det, en rallyetape oftest er. Giv `--surface`, når du ved bedre.
