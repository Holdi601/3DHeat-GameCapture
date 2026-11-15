---
title: iRacing
nav_order: 6
lang: "sl"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **ne potrebuje snemalnika**. Simulator sam zapisuje svoje telemetrijske datoteke `.ibt`,
kadar je beleženje telemetrije vklopljeno (v avtu Alt+L): celotna seja pri 60 Hz, vsak kanal, ki ga
simulator izpostavi, z opisom seje v YAML ob njej. Datoteko `.ibt` povlecite na zavihek
„Analiza dirke“ v pregledovalniku.

Bralnik je v pregledovalniku, ne v tem repozitoriju (`src/race/ibt.ts` v pregledovalniku 3DHeat). Preizkušen je na
sintetični datoteki; tu je opisan, ker je iRacing polovica iste zgodbe o snemanju krogov.

## Kaj datoteka vsebuje in kako se bere {#what-the-file-holds-and-how-it-is-read}

Datoteka je dokumentirana postavitev pomnilnika simulatorja, zapisana na disk:

| Del | Velikost | Vsebuje |
|---|---|---|
| Glava | 112 bajtov | različica, hitrost ticev, kje sta YAML in tabela spremenljivk, dolžina ene vrstice vzorcev, kje se začnejo vrstice |
| Podglava za disk | 32 bajtov | datum in ura začetka, število krogov, število vrstic |
| Tabela spremenljivk | 144 bajtov na kanal | tip, odmik v vrstici, število, ime, opis, enota |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Vrstice | ena na tick | |

Datoteka se zavrne, če je krajša od 144 bajtov, če glava ni smiselna (ni spremenljivk, tabela
spremenljivk je zunaj datoteke, dolžina vrstice je nič), če manjka kateri od `SessionTime`, `Lap`,
`Lat`, `Lon`, ali če nobeden vzorec nima določenega položaja.

## Položaj {#position}

iRacing poroča zemljepisno širino, dolžino in višino, ne položaja v lastnem okviru proge. Položaji so
razporejeni v metrih na ravnino, tangentno na prvi vzorec z določenim položajem (polmer Zemlje
6.371.008,8 m): `x` vzhod, `z` jug, `y` nadmorska višina – tako da je od zgoraj, s privzeto smerjo
kamere pogleda, sever na vrhu zaslona.

## Krogi {#laps}

Seja se razdeli po števcu `Lap` simulatorja. Krog se ohrani samo, če ima več kot 60 vzorcev, se
začne pod 5 % razdalje kroga (`LapDistPct`) in konča nad 95 % – to pomeni krogi, vožnji od črte do
črte. Če se noben krog ne kvalificira, se datoteka zavrne s sporočilom, ki navede dolžino proge iz
YAML. `distance` je `LapDist`, preračunan na začetek kroga, ali prevožena razdalja iz položajev,
kadar `LapDist` manjka; `time` je `SessionTime` od začetka kroga.

## Kanali {#channels}

| iRacing | Kanal | Pretvorba |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | brez |
| `Clutch` | `clutch` | `1 - vrednost` (iRacing šteje sklopko kot vključeno; kanal je pedal) |
| `SteeringWheelAngle` | `steer` | `-kot / SteeringWheelAngleMax` (radiani, v nasprotni smeri urnega kazalca pozitivno, na -1..1 desno pozitivno; pi, kadar maksimum manjka) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | brez |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | brez |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | nastavitve pomoči |
| `dcBrakeBias` | `brakeBias` | deljeno s 100, kadar je nad 1,5 (pri nekaterih vozilih odstotek) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura karkase čez sredino |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa, pomnoženo z 0,145038, v psi |
| `..wearM` | `tireWear.*` | `1 - vrednost` |

Vsak drug kanal z eno vrednostjo na vzorec (in ne samo en bajt) se prenese pod svojim imenom;
predpona kolesa (`LF`, `RF`, `LR`, `RR`) se spremeni v pripono (`.FL`, `.FR`, `.RL`, `.RR`), tako da
ga pregledovalnik ponudi, ne da bi ga kdo opisal.

Vozilo pride iz `DriverInfo`: vnos, katerega `CarIdx` se ujema z `DriverCarIdx`, da `CarScreenName`,
`CarID` in `CarClassShortName`. Proga je `TrackDisplayName` (ali `TrackName`).

## Česa iRacing ne da {#what-iracing-does-not-give}

Zdrs pnevmatik se ne beleži, zato ni kanalov zdrsa. Kot drifta se izpelje iz hitrosti zasuka glede
na pot (glejte [Zdrs, drift in izpeljani kanali](slip-and-drift.md)). Modeli prog so v zaščitenem
formatu in niso cilj izvlečenja datotek (glejte [Igre](games.md)).
