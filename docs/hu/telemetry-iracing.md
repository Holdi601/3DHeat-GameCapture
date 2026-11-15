---
title: iRacing
nav_order: 6
lang: "hu"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

Az iRacinghez **nincs szükség rögzítőre**. A szimulátor saját telemetriafájlokat, `.ibt` fájlokat ír, ha a
telemetria-naplózás be van kapcsolva (az autóban Alt+L): a teljes munkamenet 60 Hz-en, minden csatornával,
amelyet a szimulátor kínál, mellette a munkamenet YAML-leírásával. Ezt a fájlt a megjelenítő
Versenyelemzés fülére húzza.

Az olvasó nem ebben a tárolóban van, hanem a megjelenítőben (a 3DHeat megjelenítő `src/race/ibt.ts` fájljában).
Szintetikus fájlon tesztelt, és azért dokumentáljuk itt, mert ez az iRacing-fele ugyanannak a körrögzítési
történetnek.

## Mit tartalmaz a fájl, és hogyan olvassuk {#what-the-file-holds-and-how-it-is-read}

A fájl a szimulátor dokumentált memóriaelrendezése, lemezre írva:

| Rész | Méret | Tartalom |
|---|---|---|
| Fejléc | 112 bájt | verzió, órajel, hol van a YAML és a változótábla, egy mintasor hossza, hol kezdődnek a sorok |
| Lemez-alfejléc | 32 bájt | kezdő dátum és idő, körszám, sorszám |
| Változótábla | 144 bájt csatornánként | típus, eltolás a sorban, darabszám, név, leírás, mértékegység |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Sorok | tickenként egy | |

A fájl elutasításra kerül, ha 144 bájtnál rövidebb, ha a fejléce nem épkézláb (nincs változó, a változótábla
a fájlon kívül van, vagy a sorhossz nulla), ha hiányzik belőle a `SessionTime`, `Lap`, `Lat` vagy `Lon`, vagy
ha egyetlen mintának sincs pozícióhelymeghatározása.

## Pozíció {#position}

Az iRacing szélességet, hosszúságot és magasságot ad, nem pályasíkbeli pozíciót. A pozíciókat méterben adjuk meg
egy olyan síkon, amely az első helymeghatározással rendelkező mintánál érinti a Földet (Föld-sugár 6 371 008,8 m):
`x` kelet, `z` dél, `y` a magasság - így felülről nézve, a megjelenítő kamerájának alapértelmezett irányával, észak
felfelé mutat a képernyőn.

## Körök {#laps}

A munkamenetet a szimulátor `Lap` számlálója szerint bontjuk. Egy kör csak akkor marad meg, ha több mint 60 mintát
tartalmaz, a `LapDistPct` 5%-a alatt kezdődik, és 95% felett ér véget - azaz vonaltól vonalig megtett körök. Ha
egyik kör sem felel meg, a fájl elutasításra kerül, a YAML-ből vett pályahossz megnevezésével. A `distance` a
`LapDist` a kör kezdetéhez igazítva, vagy a pozíciókból megtett táv, ha a `LapDist` hiányzik; a `time` a kör
kezdetétől vett `SessionTime`.

## Csatornák {#channels}

| iRacing | Csatorna | Átalakítás |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | nincs |
| `Clutch` | `clutch` | `1 - érték` (az iRacing a kuplungot bekapcsoltnak számolja; a csatorna maga a pedál) |
| `SteeringWheelAngle` | `steer` | `-szög / SteeringWheelAngleMax` (radián, az óramutató-járásával ellentétes irány pozitív, -1..1 tartományra, a jobb oldal pozitív; pi, ha a maximum hiányzik) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | nincs |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | nincs |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | segédbeállítások |
| `dcBrakeBias` | `brakeBias` | 100-zal osztva, ha 1,5 felett van (egyes autókon százalékban adják) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | a gumi belső, középső hőmérséklete |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa szorozva 0,145038-cal, psi-re váltva |
| `..wearM` | `tireWear.*` | `1 - érték` |

Minden más, mintánként egy értékű csatornát (és nem egyetlen bájtot), a saját nevén továbbítunk, a kerékprefixet
(`LF`, `RF`, `LR`, `RR`) utótagra cserélve (`.FL`, `.FR`, `.RL`, `.RR`), így a megjelenítő grafikonjai leírás
nélkül is felajánlják.

Az autót a `DriverInfo` adja: az a bejegyzés, amelynek `CarIdx` értéke megegyezik a `DriverCarIdx`-szel, megadja a
`CarScreenName`, `CarID` és `CarClassShortName` értékeit. A pálya a `TrackDisplayName` (vagy a `TrackName`).

## Amit az iRacing nem ad meg {#what-iracing-does-not-give}

Nincs naplózott gumicsúszás, így nincsenek csúszási csatornák. A sodródási szöget a yaw-rátából és az úthoz
viszonyított irányból számoljuk (lásd: [Csúszás, driftelés és származtatott csatornák](slip-and-drift.md)). A
pályamodellek védett formátumban érkeznek, és nem fájlkinyerési célpontok (lásd: [Játékok](games.md)).
