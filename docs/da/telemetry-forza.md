---
title: "Forza Horizon og Forza Motorsport"
nav_order: 1
lang: "da"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon og Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # spil -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # og FH Companion virker stadig
```

Kode: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(layoutgenkendelse),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(alle kanaler, omgangsfiler, videresendelse).

## Slå det til i spillet {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (eller det, du giver som `--port`). Forza Motorsport tilbyder også et pakkeformat: det skal være **Dash**, ikke Sled. Sled indeholder slet ingen position, og optageren afviser den.

Optageren binder til `127.0.0.1`, så spillet skal køre på samme pc.

## Hvad spillet sender, og hvordan layoutet findes {#what-the-game-sends-and-how-the-layout-is-found}

Data Out er én UDP-pakke pr. simuleringstik (omkring 60 i sekundet), en flad little-endian C-struct i disse størrelser:

| Længde | Variant |
|---|---|
| 232 bytes | Motorsport "Sled": ingen position. Afvist med en besked om at skifte til Dash. |
| 311 bytes | Motorsport "Dash": Sled-blokken plus dash-blokken på 79 bytes |
| 324 bytes | Horizon "Dash": det samme med udfyldning mellem de to blokke |
| 331 bytes | Forza Motorsport (2023): Dash plus 20 bytes dæksslid og banens id |

Sled-blokken (forskydninger 0-231) er stabil. Hvor dash-blokken begynder i Horizon-varianten, beskrives forskelligt i offentliggjorte kilder, og et forkert gæt fejler ikke - det giver plausible decimaltal fra de forkerte felter. Derfor **findes** starten:

1. Kandidatstarter prøves i rækkefølge: `længde - 79` (dash-blokken løber til den sidste byte i hver dokumenteret variant), 232, 244 og 232 til 260 i trin på 4.
2. Hver kandidat scores på pakker fra en bil i bevægelse (en hastighedskomponent over 1 m/s): Sled-blokkens hastighedsvektor og dash-blokkens skalare `Speed` er den samme størrelse på to steder, så `| |hastighed| - Speed |` er tæt på nul kun for den rigtige start.
3. Kandidaten med den mindste værste uoverensstemmelse vinder, hvis uoverensstemmelsen højst er **1 m/s**. Ellers venter registreringen videre.

Mens bilen står stille, læser alle kandidater nul og er enige, hvilket intet beviser, så **registreringen venter, til bilen kører**: kør nogle meter, før du venter output. Op til 600 pakker holdes, mens der ventes (beskåret til de seneste 300). Når layoutet er kendt, afkodes de holdte pakker også, så starten af den første omgang ikke går tabt. Pakker med en anden længde end det fundne layout, pakker kortere end 311 bytes og pakker med en position eller hastighed, der ikke er et endeligt tal, ignoreres for omgangsfilerne.

Hvilken Forza det er, følger af layoutet: et Horizon-layout giver `"game": "forza-horizon"`, et Motorsport- eller 331-bytes-layout giver `"forza-motorsport"`, og alt andet `"forza"`. Det fundne layouts navn (`Horizon dash`, `Motorsport dash`, `331-byte dash`) skrives som `layout`.

## Kanaler der optages {#channels-recorded}

Hvert felt i pakken afkodes (`decode_full`) og omregnes:

- pedalerne `throttle`, `brake`, `clutch`, `handbrake` fra 0..255 til 0..1;
- `steer` fra -127..127 til -1..1; `drivingLine` og `aiBrakeDifference` deles ligeså med 127;
- `tireTemp.FL` ... `.RR` fra Fahrenheit til Celsius;
- `latAcc`, `longAcc`, `vertAcc` og `yawRate` er kopier af `accelX`, `accelZ`, `accelY` og `angVelY` under de kanoniske navne (bilens ramme: x til højre, y op, z fremad);
- Sled-hastigheden, som er i bilens egen ramme (x til højre, y op, z fremad - ikke verdenens), skrives direkte under de kanoniske navne `latVel`, `vertVel` og `longVel`, så viewer'en læser driftvinklen af den i stedet for at estimere den ud fra retning og sti.

Omgangsfilens kanaler er alle disse undtagen de felter, der hører til hele omgangen:

| Gruppe | Kanaler |
|---|---|
| Tid og sted | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Bevægelse | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Fører | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Pr. hjul (`.FL .FR .RL .RR`) | `suspension` (0 strakt .. 1 sammentrykt), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normaliseret: over 1 slipper dækket), `wheelSpeed` (rad/s), `rumble` (på en rumlestrimmel), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Kun Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` er spillets timer for den aktuelle omgang minus dens værdi ved omgangens første prøve; `distance` er spillets kørte afstand minus dens første værdi. Positioner er Forzas verdenskoordinater i meter, uændrede (y er op; verden er venstrehåndet).

Hentet én gang pr. omgang i stedet for pr. prøve, under `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. FM2023's bane-id gemmes også én gang, som `lap.trackOrdinal`. Gemmes ikke pr. prøve: `isRaceOn` (1 i hvert billede af en omgang). `timestampMs`, `raceTime`, `bestLap` og `lastLap` gemmes som kanaler.

Resten af dokumentet udfyldes ligesom for alle andre optageres:

- `"track": null` - Forza Horizon nævner ikke banen, og Forza Motorsport nummererer den kun;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - slip-kanalerne er normaliseret, så over 1 slipper dækket;
- `units` lister kun de kanaler, filen har (kanaler pr. hjul under deres grundnavn);
- en værdi, der ikke er et endeligt tal, skrives som `null`, aldrig som `NaN`.

Se [Filen `heat3d-lap`](lap-format.md).

## Sådan opdeles omgangene {#how-laps-are-split}

`LapSplitter` (se [Opdeling i omgange og etaper](lap-splitting.md)): en omgang lukkes, når spillets omgangstæller går videre, og dens tid er da spillets egen `lastLap` (det, spillet viser). Et point-to-point-løb eller en session, der slutter midt i en omgang, lukkes, når spillet forlader løbet (`isRaceOn` falder), når pakkerne holder op i 2 sekunder, eller når spillets tidsstempel springer tilbage; den gemmes som en `run`, hvis den dækkede mindst 400 m.

## Videresendelse til FH Companion {#relaying-to-fh-companion}

Spillet sender Data Out til kun én adresse. Med `--forward host:port` sender optageren **hver pakke, den modtager, uændret videre**, før den afkoder noget - også mens den stadig venter på at finde layoutet - så et andet program, der læser feedet, fortsat virker: sæt spillet til 5300, det andet program til 5301, og kør med `--forward 127.0.0.1:5301`.

FH Companion er et særskilt program, ikke en del af 3DHeat. Det gemmer et banebibliotek under `%LOCALAPPDATA%\FHCompanion\laps`: en mappe pr. bane, én omgangsfil pr. omgang samplet cirka hver femte meter, og ved siden af hver omgangsfil `<lap>.json.tele.gz`, hele omgangens Data Out i spillets takt. 3DHeat læser begge:

- **Viewer'en læser `.tele.gz` direkte**, når du slipper den (med eller uden dens omgangsfil) på fanen Løbsanalyse. Den oversætter Forzas egne feltnavne (`PositionX`, `VelocityX`, `TireSlipRatio` + hjul, ...) til de kanoniske kanaler, omregner de bilbårne `VelocityX/Y/Z` til `latVel`, `vertVel`, `longVel`, omregner dæktemperaturer fra Fahrenheit, dropper rækker, der gentager den forrige bortset fra optagerens ur, og markerer slippet som `peak`. Får den også omgangsfilen, tager omgangen sin bil og omgangstid derfra. Denne læser ligger i viewer'en (`src/race/adapters.ts`, `readForzaTelemetry`), ikke i dette repository.
- **Kommandoen `laps`** læser banebiblioteket og skriver en banes rute og en CSV med hver prøve; se [Kommandoreference](commands.md#laps).

## Andre anvendelser af det samme feed {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` optager kun positionerne, gemt hvert par sekunder under kørslen; se [Kommandoreference](commands.md#route).
- Valgmuligheden "Racing telemetry (Forza)" i scanvinduet bruger feedet som præcise kameraposer til rekonstruktion; se [Kameraposition og skala](reconstruction-pose.md#telemetry-poses).

## Noter og forbehold {#notes-and-caveats}

- Hvad Forza normaliserer sit slip med, er ikke dokumenteret. `1` læses som grænsen for greb, men viewer'en måler, hvor hver bils greb reelt bliver mindre.
- Sled-hastigheden er bilbåren, som Forzas Data Out-dokumentation siger, og optagede omgange bekræfter det (dens fremadrettede komponent bærer farten, dens sidelæns komponent bliver nær nul). Layoutgenkendelsen bruger kun dens længde, som er den samme i alle rammer.
- Positionerne er spillets verden, y op og venstrehåndet. Fortegnene for `yaw`, `pitch` og `roll` er kontrolleret på optagne omgange: yaw er lig med kørselsretningen `atan2(dx, dz)`, en positiv pitch er snuden nedad, og en positiv roll sænker højre side.
