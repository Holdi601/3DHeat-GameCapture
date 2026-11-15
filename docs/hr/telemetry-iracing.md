---
title: iRacing
nav_order: 6
lang: "hr"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **ne treba snimač**. Simulator sam zapisuje telemetrijske datoteke, `.ibt`, kad je
zapisivanje telemetrije uključeno (Alt+L u automobilu): cijelu sesiju na 60 Hz, svaki kanal koji
simulator izlaže, uz YAML opis sesije pored. Datoteku `.ibt` ispustite na karticu Analiza utrke
preglednika.

Čitač je u pregledniku, a ne u ovom repozitoriju (`src/race/ibt.ts` u pregledniku 3DHeat). Testiran je
na sintetičkoj datoteci; ovdje je dokumentiran jer je to iRacing dio iste priče o snimanju krugova.

## Što datoteka sadrži i kako se čita {#what-the-file-holds-and-how-it-is-read}

Datoteka je dokumentirani raspored memorije simulatora zapisan na disk:

| Dio | Veličina | Sadržaj |
|---|---|---|
| Zaglavlje | 112 bajta | verzija, brzina takta, gdje su YAML i tablica varijabli, duljina jednog retka uzoraka, gdje počinju retci |
| Podzaglavlje diska | 32 bajta | datum i vrijeme početka, broj krugova, broj redaka |
| Tablica varijabli | 144 bajta po kanalu | vrsta, pomak u retku, broj, naziv, opis, jedinica |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Retci | jedan po taktu | |

Datoteka se odbija ako je kraća od 144 bajta, ako zaglavlje nije valjano (nema varijabli, tablica
varijabli je izvan datoteke, ili je duljina retka nula), ako nedostaje bilo koji od
`SessionTime`, `Lap`, `Lat`, `Lon`, ili ako nijedan uzorak nema položajnu točku.

## Položaj {#position}

iRacing izvještava širinu, dužinu i nadmorsku visinu, a ne položaj u vlastitom okviru staze. Položaji
se daju u metrima na ravnini tangentnoj u prvom uzorku s točkom položaja (polumjer Zemlje 6,371,008.8
m): `x` istok, `z` jug, `y` nadmorska visina - tako da gledano odozgo, uz zadani smjer kamere
preglednika, sjever je prema gore na ekranu.

## Krugovi {#laps}

Sesija se dijeli prema brojaču simulatora `Lap`. Krug se zadržava samo ako ima više od 60 uzoraka,
počinje ispod 5% udaljenosti kruga (`LapDistPct`) i završava iznad 95% - to jest, vožnje od linije do
linije. Ako nijedan krug ne prođe, datoteka se odbija s porukom koja navodi duljinu staze iz YAML-a.
`distance` je `LapDist` pomaknut na početak kruga, ili prijeđena udaljenost iz položaja kad `LapDist`
nedostaje; `time` je `SessionTime` od početka kruga.

## Kanali {#channels}

| iRacing | Kanal | Pretvorba |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | nema |
| `Clutch` | `clutch` | `1 - value` (iRacing kvačilo broji kao uključeno; kanal je pedala) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radijani, suprotno kazaljci na satu pozitivno, na -1..1 desno pozitivno; pi kad najveći kut nedostaje) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | nema |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | nema |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | postavke pomoći |
| `dcBrakeBias` | `brakeBias` | podijeljeno sa 100 kad je iznad 1,5 (postotak na nekim automobilima) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura karkase preko sredine |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa puta 0,145038, u psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Svaki drugi kanal s jednom vrijednosti po uzorku (i koji nije jedan bajt) prolazi pod svojim imenom, a
prefiks kotača (`LF`, `RF`, `LR`, `RR`) pretvara se u sufiks (`.FL`, `.FR`, `.RL`, `.RR`), pa grafovi
preglednika nude taj kanal bez da ga itko opisuje.

Automobil dolazi iz `DriverInfo`: unos čiji se `CarIdx` podudara s `DriverCarIdx` daje
`CarScreenName`, `CarID` i `CarClassShortName`. Staza je `TrackDisplayName` (ili `TrackName`).

## Što iRacing ne daje {#what-iracing-does-not-give}

Nema zapisanog proklizavanja guma, pa nema kanala proklizaja. Kut drifta izvodi se iz brzine skretanja
u odnosu na put (vidi [Klizanje, drift i izvedeni kanali](slip-and-drift.md)). Modeli staza isporučuju
se u zaštićenom formatu i nisu cilj izdvajanja datoteka (vidi [Igre](games.md)).
