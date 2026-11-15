---
title: iRacing
nav_order: 6
lang: "da"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing har **ingen optager brug for**. Simulatoren skriver selv sine telemetrifiler, `.ibt`, når
telemetriloggning er slået til (Alt+L i bilen): hele sessionen med 60 Hz, hver kanal simulatoren
eksponerer, med sessionens YAML-beskrivelse ved siden af. Læg `.ibt`-filen på viewerens fane Løbsanalyse.

Læseren ligger i viewer'en, ikke i dette repository (`src/race/ibt.ts` i 3DHeat-vieweren). Den er testet
på en syntetisk fil; den er dokumenteret her, fordi den er iRacing-halvdelen af samme lap-optagelseshistorie.

## Hvad filen indeholder, og hvordan den læses {#what-the-file-holds-and-how-it-is-read}

Filen er simulatorens dokumenterede hukommelseslayout skrevet til disk:

| Del | Størrelse | Indeholder |
|---|---|---|
| Header | 112 byte | version, tickrate, hvor YAML'en og variabeltabellen ligger, længden af én prøverække, hvor rækkerne begynder |
| Disk-underheader | 32 byte | startdato og -tid, antal lap, antal rækker |
| Variabeltabel | 144 byte pr. kanal | type, offset i rækken, antal, navn, beskrivelse, enhed |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rækker | én pr. tick | |

En fil afvises, når den er kortere end 144 byte, når dens header ikke er fornuftig (ingen variabler, en
variabeltabel uden for filen, en rækkelængde på nul), når den mangler nogen af `SessionTime`, `Lap`, `Lat`,
`Lon`, eller når ingen prøve har en positionsfiks.

## Position {#position}

iRacing rapporterer breddegrad, længdegrad og højde, ikke en position i banens egen ramme. Positioner
lægges ud i meter på et plan, der tangerer ved den første prøve med en fiks (jordradius 6.371.008,8 m):
`x` øst, `z` syd, `y` højden - så det set fra oven, med viewerkameraets standardretning, er nord op
ad skærmen.

## Lap {#laps}

Sessionen deles op efter simulatorens tæller `Lap`. Et lap beholdes kun, hvis det har mere end 60
prøver, begynder under 5 % af lapafstanden (`LapDistPct`) og slutter over 95 % - altså lap kørt fra linje
til linje. Hvis intet lap kvalificerer sig, afvises filen med en besked, der navner banens længde fra YAML'en.
`distance` er `LapDist` omregnet til lappets start, eller den kørte afstand fra positionerne, når `LapDist`
mangler; `time` er `SessionTime` fra lappets start.

## Kanaler {#channels}

| iRacing | Kanal | Omregning |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | ingen |
| `Clutch` | `clutch` | `1 - værdi` (iRacing regner koblingen som indkoblet; kanalen er pedalen) |
| `SteeringWheelAngle` | `steer` | `-vinkel / SteeringWheelAngleMax` (radianer, mod uret positiv, til -1..1 højre positiv; pi når maksimum mangler) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | ingen |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | ingen |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | hjælpeindstillinger |
| `dcBrakeBias` | `brakeBias` | divideret med 100 når over 1,5 (en procentsats på nogle biler) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | karkassens temperatur midt på dækket |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa gange 0,145038, til psi |
| `..wearM` | `tireWear.*` | `1 - værdi` |

Enhver anden kanal med én værdi pr. prøve (og ikke bare en enkelt byte) sendes igennem under sit eget navn,
med et hjulpræfiks (`LF`, `RF`, `LR`, `RR`) omdannet til et suffiks (`.FL`, `.FR`, `.RL`, `.RR`), så
viewerens grafer tilbyder den, uden at nogen skal beskrive den.

Bilen kommer fra `DriverInfo`: posten hvis `CarIdx` matcher `DriverCarIdx` giver `CarScreenName`, `CarID` og
`CarClassShortName`. Banen er `TrackDisplayName` (eller `TrackName`).

## Hvad iRacing ikke giver {#what-iracing-does-not-give}

Der logges intet dækslip, så der er ingen sliping-kanaler. Driftvinklen udledes af gir-hastigheden mod stien
(se [Slip, drift og afledte kanaler](slip-and-drift.md)). Banemodeller leveres i et beskyttet format og er ikke
et mål for filudtræk (se [Spil](games.md)).
