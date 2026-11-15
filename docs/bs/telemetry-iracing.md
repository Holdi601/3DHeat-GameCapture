---
title: "iRacing"
nav_order: 6
lang: "bs"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **ne treba snimač**. Sim sam piše svoje telemetrijske datoteke, `.ibt`, kad je telemetrijsko
bilježenje uključeno (Alt+L u autu): cijela sesija na 60 Hz, svaki kanal koji sim izlaže,
uz YAML opis sesije. Prevucite `.ibt` datoteku na karticu Analiza utrke preglednika.

Čitač živi u pregledniku, a ne u ovom repozitoriju (`src/race/ibt.ts` u pregledniku
3DHeat). Testiran je na sintetičkoj datoteci; dokumentiran je ovdje jer je iRacing
polovina iste priče o snimanju krugova.

## Šta datoteka sadrži i kako se čita {#what-the-file-holds-and-how-it-is-read}

Datoteka je dokumentirani raspored memorije sima zapisan na disk:

| Dio | Veličina | Sadrži |
|---|---|---|
| Zaglavlje | 112 bajta | verziju, brzinu otkucaja, gdje su YAML i tabela varijabli, dužinu jednog reda uzorka, gdje redovi počinju |
| Podzaglavlje diska | 32 bajta | datum i vrijeme početka, broj krugova, broj redova |
| Tabela varijabli | 144 bajta po kanalu | tip, pomak u redu, broj, ime, opis, jedinicu |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Redovi | jedan po otkucaju | |

Datoteka se odbija kad je kraća od 144 bajta, kad zaglavlje nije ispravno (nema
varijabli, tabela varijabli je izvan datoteke, dužina reda je nula), kad joj nedostaje bilo koji od
`SessionTime`, `Lap`, `Lat`, `Lon`, ili kad nijedan uzorak nema fiksiranu poziciju.

## Pozicija {#position}

iRacing javlja geografsku širinu, dužinu i visinu, a ne poziciju u vlastitom okviru staze.
Pozicije se postavljaju u metrima na ravan tangentnu u prvom uzorku s fiksom (poluprečnik Zemlje
6.371.008,8 m): `x` istok, `z` jug, `y` visina - tako da je odozgo, sa zadanim smjerom
kamere preglednika, sjever prema vrhu ekrana.

## Krugovi {#laps}

Sesija se dijeli po simovom brojaču `Lap`. Krug se zadržava samo ako ima više od 60
uzoraka, počinje ispod 5% dužine kruga (`LapDistPct`) i završava iznad 95% - to jest, krugovi
vozeni od linije do linije. Ako nijedan krug ne zadovoljava, datoteka se odbija porukom koja navodi
dužinu staze iz YAML-a. `distance` je `LapDist` pomaknut na početak kruga, ili
pređena udaljenost iz pozicija kad `LapDist` nedostaje; `time` je `SessionTime` od
početka kruga.

## Kanali {#channels}

| iRacing | Kanal | Pretvaranje |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | nikakvo |
| `Clutch` | `clutch` | `1 - value` (iRacing računa kvačilo kao uključeno; kanal je pedala) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radijani, suprotno od kazaljke na satu pozitivno, u -1..1 desno pozitivno; pi kad maksimum nedostaje) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | nikakvo |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | nikakvo |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | postavke pomoćnih sistema |
| `dcBrakeBias` | `brakeBias` | podijeljeno sa 100 kad je iznad 1,5 (postotak kod nekih auta) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura karkase preko sredine |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa puta 0,145038, u psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Svaki drugi kanal s jednom vrijednošću po uzorku (i ne jednim bajtom) prosljeđuje se pod
vlastitim imenom, s prefiksom točka (`LF`, `RF`, `LR`, `RR`) pretvorenim u sufiks
(`.FL`, `.FR`, `.RL`, `.RR`), pa ga grafikoni preglednika nude a da ga niko ne mora opisivati.

Auto dolazi iz `DriverInfo`: stavka čiji `CarIdx` odgovara `DriverCarIdx` daje
`CarScreenName`, `CarID` i `CarClassShortName`. Staza je `TrackDisplayName` (ili
`TrackName`).

## Šta iRacing ne daje {#what-iracing-does-not-give}

Klizanje guma se ne bilježi, pa nema slip kanala. Ugao drifta se izvodi iz brzine
skretanja (yaw) prema putanji (pogledajte [Slip, drift i izvedeni kanali](slip-and-drift.md)). Modeli staza
dolaze u zaštićenom formatu i nisu cilj izvlačenja datoteka (pogledajte [Igre](games.md)).
