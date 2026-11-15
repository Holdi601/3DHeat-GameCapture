---
title: "Forza Horizon og Forza Motorsport"
nav_order: 1
lang: "no"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon og Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # spillet -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # og FH Companion fungerer fortsatt
```

Kode: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(oppsettdeteksjon),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(alle kanaler, rundefiler, videresending).

## Slå det på i spillet {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (eller det du gir som `--port`). Forza Motorsport tilbyr
også et pakkeformat: det må være **Dash**, ikke Sled. Sled inneholder ingen posisjon i det hele tatt, og opptakeren nekter den.

Opptakeren binder seg til `127.0.0.1`, så spillet må kjøre på samme PC.

## Hva spillet sender, og hvordan oppsettet finnes {#what-the-game-sends-and-how-the-layout-is-found}

Data Out er én UDP-pakke per simuleringstikk (omtrent 60 i sekundet), en flat little-endian C-struct i disse størrelsene:

| Lengde | Variant |
|---|---|
| 232 bytes | Motorsport "Sled": ingen posisjon. Avvist med en melding som sier at du må bytte til Dash. |
| 311 bytes | Motorsport "Dash": Sled-blokken pluss 79-byte-dash-blokken |
| 324 bytes | Horizon "Dash": det samme med polstring mellom de to blokkene |
| 331 bytes | Forza Motorsport (2023): Dash pluss 20 bytes dekkslitasje og banens id |

Sled-blokken (forskyvning 0-231) er stabil. Hvor dash-blokken starter i Horizon-varianten, beskrives
ulikt i publiserte kilder, og å gjette feil feiler ikke - den gir plausible flyttall fra de feile feltene. Så starten
**oppdages**:

1. Kandidatstarter prøves i rekkefølge: `lengde - 79` (dash-blokken går til siste byte i hver dokumenterte variant), 232, 244, og 232 til 260 i steg på 4.
2. Hver kandidat poengsettes på pakker fra en bil i bevegelse (en hastighetskomponent over 1 m/s): Sled-blokkens hastighetsvektor og dash-blokkens
   skalare `Speed` er den samme størrelsen på to steder, så `| |hastighet| - Speed |` er nær null bare for riktig start.
3. Kandidaten med minst verstefalls uenighet vinner, hvis den uenigheten er høyst **1 m/s**. Ellers venter detekteringen videre.

Mens bilen står parkert leser hver kandidat null og er enige, noe som beviser ingenting, så **detekteringen venter til bilen beveger seg**: kjør noen meter før du
venter output. Opptil 600 pakker holdes mens den venter (kuttet til de siste 300). Når oppsettet er kjent, dekodes de holdte pakkene også, så starten av første runde
mistes ikke. Pakker med en annen lengde enn det detekterte oppsettet, pakker kortere enn 311 bytes, og pakker med en ikke-endelig posisjon eller fart ignoreres for rundefilene.

Hvilken Forza det er følger av oppsettet: et Horizon-oppsett gir `"game": "forza-horizon"`, et Motorsport- eller 331-byte-oppsett gir
`"forza-motorsport"`, alt annet `"forza"`. Oppsettets navn (`Horizon dash`, `Motorsport dash`, `331-byte dash`) skrives som `layout`.

## Kanaler som tas opp {#channels-recorded}

Hvert felt i pakken dekodes (`decode_full`) og konverteres:

- pedalene `throttle`, `brake`, `clutch`, `handbrake` fra 0..255 til 0..1;
- `steer` fra -127..127 til -1..1; `drivingLine` og `aiBrakeDifference` deles likeså på 127;
- `tireTemp.FL` ... `.RR` fra Fahrenheit til Celsius;
- `latAcc`, `longAcc`, `vertAcc` og `yawRate` er kopier av `accelX`, `accelZ`, `accelY` og `angVelY` under de kanoniske navnene (bilens ramme: x høyre, y opp, z fremover);
- Sled-farten, som er i bilens egen ramme (x høyre, y opp, z fremover - ikke verdens), skrives rett ut under de kanoniske navnene `latVel`, `vertVel` og `longVel`, slik at viewer
  leser driftvinkelen fra den i stedet for å anslå den fra retning og bane.

Rundefilens kanaler er alle disse unntatt de per-runde feltene:

| Gruppe | Kanaler |
|---|---|
| Tid og sted | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Bevegelse | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Fører | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Per hjul (`.FL .FR .RL .RR`) | `suspension` (0 strukket .. 1 sammentrykt), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalisert: over 1 gir dekket slipp), `wheelSpeed` (rad/s), `rumble` (på en rumlestripe), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Bare Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` er spillets nåværende rundetimer minus verdien ved rundens første prøve; `distance` er spillets kjørte distanse minus
dens første verdi. Posisjoner er Forzas verdenskoordinater i meter, uendret (y er opp; verden er venstrehåndet).

Tatt én gang per runde i stedet for per prøve, under `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`.
FM2023s banes id legges også inn én gang, som `lap.trackOrdinal`. Ikke beholdt per prøve: `isRaceOn` (1 i hver ramme av en runde). `timestampMs`,
`raceTime`, `bestLap` og `lastLap` beholdes som kanaler.

Resten av dokumentet fylles slik som for hver annen opptaker:

- `"track": null` - Forza Horizon oppgir ikke banen, og Forza Motorsport bare nummererer den;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - sklikanalene er normalisert slik at over 1 gir dekket slipp;
- `units` lister bare kanalene filen har (per-hjul-kanaler under sitt grunnnavn);
- en verdi som ikke er et endelig tall skrives som `null`, aldri `NaN`.

Se [`heat3d-lap`-filen](lap-format.md).

## Hvordan runder deles {#how-laps-are-split}

`LapSplitter` (se [Hvordan runder og etapper deles](lap-splitting.md)): en runde lukkes når spillets rundeteller går videre, og tiden er da spillets
egen `lastLap` (det spillet viser). Et løp fra A til B eller en økt som slutter midt i en runde lukkes når spillet forlater løpet (`isRaceOn` faller),
når pakkene stopper i 2 sekunder, eller når spillets tidsstempel hopper bakover; den beholdes som en `run` hvis den dekket minst 400 m.

## Videresending til FH Companion {#relaying-to-fh-companion}

Spillet sender Data Out til bare én adresse. Med `--forward host:port` sender opptakeren **hver pakke den mottar videre uendret**, før den dekoder noe
(også mens den fortsatt venter på å oppdage oppsettet), slik at en annen app som leser strømmen fortsetter å fungere: sett spillet til 5300, den andre appen til
5301, og kjør med `--forward 127.0.0.1:5301`.

FH Companion er en egen app, ikke en del av 3DHeat. Den holder et rundebibliotek under `%LOCALAPPDATA%\FHCompanion\laps`: en mappe per bane, én rundefil per runde
prøvet omtrent hver femte meter, og ved siden av hver rundefil `<lap>.json.tele.gz`, hele rundens Data Out i spillets takt. 3DHeat leser begge:

- **Viewer leser `.tele.gz` direkte** når du slipper den (med eller uten rundefilen) på fanen Løpsanalyse. Den kobler Forzas egne feltnavn (`PositionX`, `VelocityX`, `TireSlipRatio`
  + hjul, ...) til de kanoniske kanalene, gjør den bilens lokale `VelocityX/Y/Z` om til `latVel`, `vertVel`, `longVel`, konverterer dekktemperaturer fra Fahrenheit, dropper rader
  som gjentar forrige bortsett fra opptakerens klokke, og markerer sklien som `peak`. Gitt rundefilen også, tar runden bil og rundetid fra den. Denne leseren ligger i viewer
  (`src/race/adapters.ts`, `readForzaTelemetry`), ikke i dette depotet.
- **Kommandoen `laps`** leser rundebiblioteket og skriver en banes rute og en CSV med hver prøve; se [Kommandoreferanse](commands.md#laps).

## Andre bruksområder for samme strøm {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` tar bare opp posisjonene, lagret omtrent hvert andre sekund under kjøring; se [Kommandoreferanse](commands.md#route).
- Skannevinduets alternativ "Racing telemetry (Forza)" bruker strømmen som eksakte kameraposisjoner for rekonstruksjon; se [Kameraposisjon og skala](reconstruction-pose.md#telemetry-poses).

## Merknader og forbehold {#notes-and-caveats}

- Hva Forza normaliserer sklien mot, er ikke dokumentert. `1` leses som grensen for grep, men viewer måler hvor hver bils grep faktisk avtar.
- Sled-farten er i bilens ramme, slik Forzas Data Out-dokumentasjon sier og innspilte runder bekrefter (fremoverkomponenten bærer farten, og sidekomponenten holder seg nær null).
  Oppsettdeteksjonen bruker bare lengden, som er den samme i hvilken som helst ramme.
- Posisjoner er spillets verden, y opp og venstrehåndet. Fortegnene til `yaw`, `pitch` og `roll` ble kontrollert på innspilte runder: yaw er lik kjøreretningen `atan2(dx, dz)`,
  positiv stigning er nesen ned, og positiv rulling senker høyre side.
