---
title: "Forza Horizon och Forza Motorsport"
nav_order: 1
lang: "sv"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon och Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(layoutdetektering),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(alla kanaler, varvfiler, vidarebefordran).

## Slå på det i spelet {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (eller vad du än anger med `--port`). Forza Motorsport erbjuder också ett paketformat: det måste vara **Dash**, inte Sled. Sled bär ingen position alls, och inspelaren vägrar den.

Inspelaren binder till `127.0.0.1`, så spelet måste köras på samma dator.

## Vad spelet skickar, och hur layouten hittas {#what-the-game-sends-and-how-the-layout-is-found}

Data Out är ett UDP-paket per simuleringstick (ungefär 60 per sekund), en platt little-endian C-struct i dessa storlekar:

| Längd | Variant |
|---|---|
| 232 byte | Motorsport "Sled": ingen position. Avvisas med ett meddelande som säger att du ska byta till Dash. |
| 311 byte | Motorsport "Dash": Sled-blocket plus dash-blocket på 79 byte |
| 324 byte | Horizon "Dash": samma, med utfyllnad mellan de två blocken |
| 331 byte | Forza Motorsport (2023): Dash plus 20 byte däckslitage och banans id |

Sled-blocket (offset 0-231) är stabilt. Var dash-blocket börjar i Horizon-varianten beskrivs på olika sätt i publicerade källor, och att gissa fel ger inget felmeddelande. Det ger rimliga flyttal från fel fält. Därför **upptäcks** starten:

1. Kandidatstarter prövas i ordning: `length - 79` (dash-blocket går till sista byten i varje dokumenterad variant), 232, 244, och 232 till 260 i steg om 4.
2. Varje kandidat poängsätts på paket från en rörlig bil (en hastighetskomponent över 1 m/s). Sled-blockets hastighetsvektor och dash-blockets skalära `Speed` är samma storhet på två ställen, så `| |velocity| - Speed |` är nära noll bara för rätt start.
3. Kandidaten med minsta värsta oenighet vinner, om den oenigheten är högst **1 m/s**. Annars väntar upptäckten vidare.

Medan bilen står parkerad läser varje kandidat noll och alla stämmer, vilket inte bevisar något. Därför **väntar upptäckten tills bilen rör sig**: kör några meter innan du väntar dig utdata. Upp till 600 paket hålls medan den väntar (trimmade till de senaste 300). När layouten är känd avkodas även de hållna paketen, så starten av första varvet förloras inte. Paket med en annan längd än den upptäckta layouten, paket kortare än 311 byte och paket med en ändlig position eller hastighet ignoreras för varvfilerna.

Vilken Forza det är följer av layouten. En Horizon-layout ger `"game": "forza-horizon"`, en Motorsport- eller 331-byte-layout ger `"forza-motorsport"`, och allt annat ger `"forza"`. Den upptäckta layoutens namn (`Horizon dash`, `Motorsport dash`, `331-byte dash`) skrivs som `layout`.

## Kanaler som spelas in {#channels-recorded}

Varje fält i paketet avkodas (`decode_full`) och konverteras:

- pedaler `throttle`, `brake`, `clutch`, `handbrake` från 0..255 till 0..1;
- `steer` från -127..127 till -1..1; `drivingLine` och `aiBrakeDifference` likaså, delade med 127;
- `tireTemp.FL` ... `.RR` från Fahrenheit till Celsius;
- `latAcc`, `longAcc`, `vertAcc` och `yawRate` är kopior av `accelX`, `accelZ`, `accelY` och `angVelY` under de kanoniska namnen (bilens ram: x höger, y upp, z framåt);
- Sled-hastigheten, som är i bilens egen ram (x höger, y upp, z framåt, inte världens), skrivs rakt under de kanoniska namnen `latVel`, `vertVel` och `longVel`. Visaren läser då driftvinkeln direkt i stället för att skatta den från riktning och bana.

Varvfilens kanaler är alla dessa, utom de per-varv-fälten:

| Grupp | Kanaler |
|---|---|
| Tid och plats | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Rörelse | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Förare | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Per hjul (`.FL .FR .RL .RR`) | `suspension` (0 utsträckt .. 1 ihopträngd), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normaliserad: över 1 släpper däcket taget), `wheelSpeed` (rad/s), `rumble` (på en vibrationsremsa), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Forza Motorsport 2023 endast | `tireWear.FL` ... `.RR` |

`time` är spelets timer för aktuellt varv minus dess värde vid varvets första sampel. `distance` är spelets körda distans minus dess första värde. Positionerna är Forzas världskoordinater i meter, oförändrade (y är upp; världen är vänsterhänt).

En gång per varv i stället för per sampel, under `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. FM2023:s banid läggs också in en gång, som `lap.trackOrdinal`. `isRaceOn` behålls inte per sampel (den är 1 i varje bildruta på ett varv). `timestampMs`, `raceTime`, `bestLap` och `lastLap` behålls som kanaler.

Resten av dokumentet fylls som för alla andra inspelare:

- `"track": null`: Forza Horizon namnger inte banan, och Forza Motorsport bara numrerar den;
- `"meta": {"slip": "peak", "discipline": "circuit"}`: slip-kanalerna är normaliserade så att över 1 släpper däcket taget;
- `units` listar bara de kanaler filen har (per-hjul-kanaler under sitt basnamn);
- ett värde som inte är ett ändligt tal skrivs som `null`, aldrig `NaN`.

Se [heat3d-lap-filen](lap-format.md).

## Hur varv delas {#how-laps-are-split}

`LapSplitter` (se [Hur varv och etapper delas](lap-splitting.md)): ett varv stängs när spelets varvräknare går vidare, och dess tid är då spelets egen `lastLap` (det spelet visar). Ett punkt-till-punkt-lopp, eller en session som slutar mitt i ett varv, stängs när spelet lämnar loppet (`isRaceOn` faller), när paketen slutar komma i 2 sekunder, eller när spelets tidsstämpel hoppar bakåt. Det behålls som en `run` om det täckte minst 400 m.

## Vidarebefordran till FH Companion {#relaying-to-fh-companion}

Spelet skickar Data Out till bara en adress. Med `--forward host:port` skickar inspelaren **varje paket den tar emot oförändrat**, innan den avkodar något (även medan den väntar på att upptäcka layouten). Då fortsätter en annan app som läser flödet att fungera. Ställ spelet på 5300, den andra appen på 5301, och kör med `--forward 127.0.0.1:5301`.

FH Companion är en separat app, inte en del av 3DHeat. Den håller ett varvbibliotek under `%LOCALAPPDATA%\FHCompanion\laps`: en mapp per bana, en varvfil per varv samplad ungefär var femte meter, och bredvid varje varvfil `<lap>.json.tele.gz`, hela varvets Data Out i spelets takt. 3DHeat läser båda:

- **Visaren läser `.tele.gz` direkt** när du släpper den (med eller utan dess varvfil) på fliken Racinganalys. Den mappar Forzas egna fältnamn (`PositionX`, `VelocityX`, `TireSlipRatio` + hjul, ...) till de kanoniska kanalerna. Den gör den bilslokala `VelocityX/Y/Z` till `latVel`, `vertVel`, `longVel`, omvandlar däcktemperaturer från Fahrenheit, tar bort rader som upprepar föregående bortsett från inspelarens klocka, och markerar slip som `peak`. Med varvfilen också tas bil och varvtid därifrån. Den läsaren finns i visaren (`src/race/adapters.ts`, `readForzaTelemetry`), inte i det här repot.
- **Kommandot `laps`** läser varvbiblioteket och skriver en bans rutt och en CSV med varje sampel; se [Kommandon](commands.md#laps).

## Andra användningar av samma flöde {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` spelar bara in positionerna, sparade med ett par sekunders mellanrum medan du kör; se [Kommandon](commands.md#route).
- Skanningsfönstrets alternativ "Racing telemetry (Forza)" använder flödet som exakta kameraposer för rekonstruktion; se [Kamerapose och skala](reconstruction-pose.md#telemetry-poses).

## Noteringar och förbehåll {#notes-and-caveats}

- Vad Forza normaliserar slip mot är inte dokumenterat. `1` läses som gränsen för grepp, men visaren mäter var varje bils grepp faktiskt upphör.
- Sled-hastigheten är bilslokal, som Forzas Data Out-dokumentation säger och inspelade varv bekräftar: dess framåtkomponent bär farten, dess sidokomponent ligger nära noll. Layoutdetekteringen använder bara dess längd, som är densamma i varje bildruta.
- Positionerna är spelets värld, Y upp och vänsterhänt. Riktningarna för `yaw`, `pitch` och `roll` kontrollerades på inspelade varv: yaw är lika med färdriktningen `atan2(dx, dz)`, en positiv stigning är nos ner, och en positiv rulle sänker högra sidan.
