---
title: "Rallyspill"
nav_order: 3
lang: "no"
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
Tester: `tests/test_rally.py`, på pakker bygget etter de dokumenterte oppsettene. **Ikke kjørt mot de levende spillene ennå.**

Alle sender UDP som spillet slår på fra sine egne innstillingsfiler. Opptakeren lytter på alle grensesnitt (`0.0.0.0`) på spillets standardport
med mindre `--port` gir en annen: **20777** for `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** for `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Slå det på {#switching-it-on}

Spillet leser `Documents\My Games\WRC\telemetry\config.json`. Standardstrukturen `wrc` sin `session_update`-pakke må
være slått på mot denne maskinen:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funksjonen `configure_wrc`):

- leser JSON-en, finner `udp.packets` og oppføringen med `"structure": "wrc"` og `"packet": "session_update"`;
- hvis den allerede er slått på mot `127.0.0.1` eller `localhost` på den porten som brukes, skriver den `already on` og endrer ingenting;
- ellers setter den `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, og beholder oppføringens `frequencyHz` (eller `-1` hvis det ikke finnes noen); finnes ingen slik oppføring, legger den til en;
- skriver den opprinnelige teksten til `config.json.bak` ved siden av, og skriver deretter den nye filen (innrykk på 4 mellomrom).

Start spillet på nytt etter å ha endret filen hvis det ikke tar imot endringen (ikke kontrollert).

### Hva det sender {#what-it-sends}

Standardstrukturen `wrc` er 237 bytes, little-endian, uten topptekst: verdensposisjon, fart og akselerasjon (X venstre, Y opp, Z fremover), bilens
venstre / fremover / opp-enhetsvektorer, per hjul (bak venstre, bak høyre, foran venstre, foran høyre) hjulets høyde og vertikale fart og kontaktflatens
fremoverfart, bremsetemperaturer, pedaler etter hjelpesystemer, styring (-1 venstre, +1 høyre), håndbrems, rpm, gir, og etappeklokken, distansen og lengden.
En pakke kortere enn 237 bytes ignoreres og rapporteres én gang.

| Kanal | Fra |
|---|---|
| `x`, `y`, `z` | verdensposisjon |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | verdenshastighet projisert på fremover, på minus venstre (så positiv er høyre), på opp |
| `longAcc`, `latAcc`, `vertAcc` | verdensakselerasjon projisert på samme måte |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | slik sendt |
| `gear` | `gear_index`; -1 når den er lik revers-indeksen, 0 når den er lik nøytral-indeksen |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | hubposisjon |
| `wheelSurfaceSpeed.*` | kontaktflatens fremoverfart |
| `brakeTemp.*` | bremsetemperatur |

Kontroll: hvis `speed` er over 10 og lengden av verdenshastighetsvektoren avviker fra den med mer enn 20 %, skriver opptakeren én gang at oppsettet kanskje ikke er standardstrukturen `wrc`.

En etappe er **ferdig** når etappelengden er positiv og distansen har nådd lengden minus 0,5 m. Klokken som brukes til deling og til `time` er `stage_time`.

Kilder: EAs UDP Telemetry Guide v1.3; kanallisten spillet skriver til `readme/channels.json`; forskyvninger slik nobonobo/obs-codemasters-telemetry
og SpaceMonkey har tolket dem. Standardporten i spillet er ikke dokumentert; opptakeren bruker 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Slå det på {#switching-it-on-1}

Rediger `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally og DiRT 4 bruker også en `hardware_settings_config.xml`; deres
nøyaktige mappe for de to er ikke kontrollert her) slik at `udp`-elementet lyder:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` er det som gjør at posisjoner, hjul og etappelengden kommer med i pakken. Opptakeren redigerer ikke denne filen.

### Hva det sender {#what-it-sends-1}

66 little-endian flyttall (DiRT Rally: 64); pakker kortere enn 64 flyttall ignoreres, og en 64-flyttall-pakke fylles med nuller. Indeksene som brukes:

| Indeks | Felt | Kanal |
|---|---|---|
| 1 | etappetid (runde) | delingsklokken og `time` |
| 2 | rundedistanse | `stageDistance` |
| 4-6 | verdensposisjon | `x`, `y`, `z` |
| 7 | fart | `speed` |
| 8-10 | verdenshastighet | `longVel` (på fremover), `latVel` (på sidevektoren) |
| 11-13 | sidevektor | |
| 14-16 | fremovervektor | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | fjæringsposisjon BV BH FV FH | `suspensionM.*` |
| 25-28 | hjulkontaktfart BV BH FV FH | `wheelSurfaceSpeed.*` |
| 29-33 | gass, styring, brems, kopling, gir | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 eller mer betyr revers, skrevet som -1) |
| 34, 35 | side-g, lengde-g | `latAcc`, `longAcc` (ganget med 9,80665) |
| 37 | rpm / 10 | `rpm` (ganget med 10) |
| 51-54 | bremsetemperaturer | `brakeTemp.*` |
| 59, 60, 61, 62 | fullførte runder, totale runder, banelengde, siste rundetid | deling |

Det er **ingen kanal for håndbrems**. Retningen på sidevektoren er dokumentert begge veier, så fortegnet på `latVel` skal ikke stoles på (viewer leser driftvinkelens størrelse).

En etappe er **ferdig** når antallet fullførte runder stiger over verdien ved etappens start (en rallycross-runde hver gang det skjer), eller, for et enkeltrunde-arrangement,
når rundedistansen når 99,9 % av banelengden. Etappens tid er spillets siste rundetid når den er positiv. Kontroll: fart mot hastighet som for EA WRC, med meldingen "is extradata set to 3?".

Kilder: Codemasters' DiRT 4 UDP-dokument; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Slå det på {#switching-it-on-2}

I `RichardBurnsRally.ini`, seksjon `[NGP]`: `udpTelemetry=1` og endepunktet (127.0.0.1, port 6776 med mindre du gir en annen `--port`). Opptakeren redigerer ikke denne filen.

### Hva det sender {#what-it-sends-2}

664 bytes (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): etappeklokke og distanse til mål, pedaler, styring, gir, verdensposisjon, holdning, bilens egne
hastigheter (surge fremover, sway sidelengs, heave), akselerasjoner, rpm, og fire 128-byte hjulblokker (LF, RF, LB, RB) med fjærutslag og fjærkraft. Ingen hjulfart.

| Kanal | Fra |
|---|---|
| `x`, `y`, `z` | posisjon, akser slik sendt, deretter omordnet (under) |
| `longVel`, `latVel`, `vertVel` | surge, sway, heave |
| `longAcc`, `latAcc` | akselerasjon x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | slik sendt |
| `gear` | `gear - 1` (0 revers, 1 nøytral, 2 første) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | fjærutslag |
| `wheelLoad.*` | fjærkraft |
| `speed` | **regnet ut fra posisjonene** over +-2 prøver, ikke hentet fra pakken |

RBRs posisjonsakser, holdningsenheter og fartsenhet er ikke dokumentert, så når en etappe skrives: aksen etappen varierer minst langs tas som opp og byttes inn i `y`
(`orient_up`, trenger minst 10 prøver), og farten regnes ut på nytt fra posisjonene (`speed_from_positions`). Holdningen dekodes, men skrives ikke, så RBR-filer har ingen `yaw`.

En etappe er **ferdig** når løpsklokken går og avstanden til mål har nådd null. Klokken er `race_time`.

Kilder: NGPs `rbr.telemetry.data.TelemetryData.h` via mika-n/RBRUDPTelemetryLogger og groybe/rbr-udp-telem.

## Etapper {#stages}

Alle fem bruker `StageSplitter` på spillets etappeklokke: en etappe åpnes når klokken starter, lukkes fullført når spillet sier at bilen er ferdig, og en klokke som går tilbake
(en omstart, eller neste etappe) forlater den åpne etappen - beholdt som en `_partial`-fil hvis den har mer enn 10 prøver og minst 300 m. Ferdige etapper kortere enn 300 m skrives ikke.
Detaljer: [Hvordan runder og etapper deles](lap-splitting.md).

## Rundefilen {#the-lap-file}

`game` er `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` eller `richard-burns-rally`. `meta` er `{"discipline": "rally", "slip": null}`, pluss `"surface": "<verdi>"` når `--surface` ble gitt.
`slip` er null fordi ingen av disse spillene sender dekksli. Hvert hjuls kontaktflatefart (EA WRC, DiRT) ligger i filen i stedet, og viewer utleder sklí og driftvinkel fra den og bilens akser;
se [Skli, drift og avledede kanaler](slip-and-drift.md). `suspension.*`-kanalene (0..1 av utslaget brukt) legges til fra `suspensionM.*`.

Når ingen `--surface` gis, har filen ingen underlag i det hele tatt, med vilje: en standard skrevet her ville overstyrt viewers egen utledning. Viewer tar da underlaget fra etappens eller
arrangementets navn (asfaltrallier, vinterrallier, Monte som blandet), ellers fra hvordan bilen ble kjørt på det (hard svingkjøring med små driftvinkler er asfalt), og løst når ingenting forteller det -
det en rallyetappe oftest er. Gi `--surface` når du vet bedre.
