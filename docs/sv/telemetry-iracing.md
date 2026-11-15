---
title: iRacing
nav_order: 6
lang: "sv"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing behöver **ingen inspelare**. Simulatorn skriver sina egna telemetrifiler, `.ibt`, när
telemetriloggning är på (Alt+L i bilen): hela sessionen med 60 Hz, varje kanal simulatorn
exponerar, med sessionens YAML-beskrivning bredvid. Släpp `.ibt`-filen på visarens flik Racinganalys.

Läsaren finns i visaren, inte i det här förrådet (`src/race/ibt.ts` i 3DHeat-visaren). Den testas
på en syntetisk fil; den dokumenteras här för att den är iRacing-halvan av samma berättelse om
varvinspelning.

## Vad filen innehåller, och hur den läses {#what-the-file-holds-and-how-it-is-read}

Filen är simulatorns dokumenterade minneslayout skriven till disk:

| Del | Storlek | Innehåll |
|---|---|---|
| Huvud | 112 byte | version, tickfrekvens, var YAML och variabeltabellen finns, längden på en samplingsrad, var raderna börjar |
| Diskunderhuvud | 32 byte | startdatum och -tid, antal varv, antal rader |
| Variabeltabell | 144 byte per kanal | typ, offset i raden, antal, namn, beskrivning, enhet |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rader | en per tick | |

En fil avvisas när den är kortare än 144 byte, när dess huvud inte är rimligt (inga variabler, en
variabeltabell utanför filen, en nollängd rad), när den saknar någon av `SessionTime`, `Lap`, `Lat`,
`Lon`, eller när inget sampel har en positionsfix.

## Position {#position}

iRacing rapporterar latitud, longitud och höjd, inte en position i bankens egen ram. Positionerna läggs
ut i meter på ett plan tangentiellt mot det första samplet med en fix (jordradie 6 371 008,8 m): `x`
österut, `z` söderut, `y` höjden - så att norr är uppåt på skärmen sett uppifrån med visarkamerans
standardriktning.

## Varv {#laps}

Sessionen delas på simulatorns räknare `Lap`. Ett varv behålls bara om det har fler än 60 sampel, börjar
under 5 % av varvsträckan (`LapDistPct`) och slutar över 95 % - alltså varv körda från linje till linje.
Om inget varv kvalificerar avvisas filen med ett meddelande som namnger banlängden från YAML.
`distance` är `LapDist` omräknat från varvets start, eller den körda sträckan från positionerna när
`LapDist` saknas; `time` är `SessionTime` från varvets start.

## Kanaler {#channels}

| iRacing | Kanal | Omvandling |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | ingen |
| `Clutch` | `clutch` | `1 - value` (iRacing räknar kopplingen som ingripen; kanalen är pedalen) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radianer, moturs positivt, till -1..1 höger positivt; pi när maximum saknas) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | ingen |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | ingen |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | hjälpinställningar |
| `dcBrakeBias` | `brakeBias` | delas med 100 när den är över 1,5 (en procentsats på vissa bilar) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | kärntemperatur tvärs över mitten |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa gånger 0,145038, till psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Varje annan kanal med ett värde per sampel (och inte en enda byte) skickas vidare under sitt eget
namn, med ett hjulprefix (`LF`, `RF`, `LR`, `RR`) omvandlat till ett suffix (`.FL`, `.FR`, `.RL`,
`.RR`), så att visarens grafer erbjuder den utan att någon behöver beskriva den.

Bilen kommer från `DriverInfo`: posten vars `CarIdx` matchar `DriverCarIdx` ger `CarScreenName`,
`CarID` och `CarClassShortName`. Banan är `TrackDisplayName` (eller `TrackName`).

## Vad iRacing inte ger {#what-iracing-does-not-give}

Ingen däcksslip loggas, så det finns inga slip-kanaler. Driftvinkeln härleds från girhastigheten mot
vägen (se [Slip, drift och härledda kanaler](slip-and-drift.md)). Banmodeller levereras i ett skyddat
format och är inte ett mål för filextrahering (se [Spel](games.md)).
