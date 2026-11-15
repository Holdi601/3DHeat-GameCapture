---
title: iRacing
nav_order: 6
lang: "no"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing trenger **ingen opptaker**. Simulatoren skriver sine egne telemetrifiler, `.ibt`, når
telemetriloggingen er på (Alt+L i bilen). Den tar hele økten med 60 Hz, alle kanaler simulatoren
viser, med øktens YAML-beskrivelse ved siden av. Dra `.ibt`-filen over visningsprogrammets
Løpsanalyse-fane.

Leseren ligger i visningsprogrammet, ikke i dette repositoriet (`src/race/ibt.ts` i 3DHeat-
visningsprogrammet). Den er testet på en syntetisk fil. Den er dokumentert her fordi den er iRacing-
halvdelen av den samme historien om rundeopptak.

## Hva filen inneholder, og hvordan den leses {#what-the-file-holds-and-how-it-is-read}

Filen er simulatorens dokumenterte minneoppsett skrevet til disk:

| Del | Størrelse | Inneholder |
|---|---|---|
| Hode | 112 byte | versjon, tikkfrekvens, hvor YAML-en og variabeltabellen ligger, lengden på en prøverad, og hvor radene begynner |
| Disk-underhode | 32 byte | startdato og -klokkeslett, antall runder, antall rader |
| Variabeltabell | 144 byte per kanal | type, forskyvning i raden, antall, navn, beskrivelse, enhet |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rader | én per tikk | |

En fil avvises når den er kortere enn 144 byte, når hodet ikke er fornuftig (ingen variabler, en
variabeltabell utenfor filen, en radlengde på null), når den mangler noen av `SessionTime`, `Lap`,
`Lat` eller `Lon`, eller når ingen prøve har en posisjon.

## Posisjon {#position}

iRacing oppgir breddegrad, lengdegrad og høyde, ikke en posisjon i banens egen ramme. Posisjonene legges
ut i meter på et plan som tangerer jorden ved den første prøven med posisjon (jordradius 6 371 008,8 m):
`x` øst, `z` sør, `y` høyden. Dermed er nord opp på skjermen sett ovenfra, med visningskameraets
standardretning.

## Runder {#laps}

Økten deles på simulatorens `Lap`-teller. En runde beholdes bare hvis den har mer enn 60 prøver, starter
under 5 % av rundelengden (`LapDistPct`) og slutter over 95 %. Det vil si runder kjørt fra linje til linje.
Hvis ingen runde kvalifiserer, avvises filen med en melding som nevner banelengden fra YAML-en. `distance`
er `LapDist` regnet fra rundens start, eller den kjørte distansen fra posisjonene når `LapDist` mangler.
`time` er `SessionTime` fra rundens start.

## Kanaler {#channels}

| iRacing | Kanal | Omregning |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | ingen |
| `Clutch` | `clutch` | `1 - verdi` (iRacing regner clutchen som inne; kanalen er pedalen) |
| `SteeringWheelAngle` | `steer` | `-vinkel / SteeringWheelAngleMax` (radianer, mot klokken positivt, til -1..1 med høyre positivt; pi når maksimum mangler) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | ingen |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | ingen |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | hjelpeinnstillinger |
| `dcBrakeBias` | `brakeBias` | delt på 100 når den er over 1,5 (en prosent på noen biler) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatur i midten av karkassen |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa ganget med 0,145038, til psi |
| `..wearM` | `tireWear.*` | `1 - verdi` |

Alle andre kanaler med én verdi per prøve (og ikke bare én byte) sendes videre under sitt eget navn. Et
hjulprefiks (`LF`, `RF`, `LR`, `RR`) gjøres om til et suffiks (`.FL`, `.FR`, `.RL`, `.RR`). Da tilbyr
visningsprogrammets grafer dem uten at noen må beskrive dem.

Bilen hentes fra `DriverInfo`: oppføringen der `CarIdx` stemmer med `DriverCarIdx` gir `CarScreenName`,
`CarID` og `CarClassShortName`. Banen er `TrackDisplayName` (eller `TrackName`).

## Hva iRacing ikke gir {#what-iracing-does-not-give}

Det logges ingen dekkslirung, så det finnes ingen slirkanaler. Driftvinkelen utledes fra
giringshastigheten mot banen (se [Skli, drift og avledede kanaler](slip-and-drift.md)). Banemodeller leveres i
et beskyttet format og er ikke et mål for filuttrekk (se [Spill](games.md)).
