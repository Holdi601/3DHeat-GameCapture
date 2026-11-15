---
title: "iRacing"
nav_order: 6
lang: "sk"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **nepotrebuje žiadny nahrávač**. Simulátor zapíše vlastné telemetrické súbory `.ibt`, keď je
zapnuté nahrávanie telemetrie (Alt+L v aute): celú reláciu s frekvenciou 60 Hz, každý kanál, ktorý
simulátor sprístupní, a popis relácie v YAML vedľa. Súbor `.ibt` pretiahnite na kartu Analýza
pretekov v prehliadači.

Čítačka je v prehliadači, nie v tomto repozitári (`src/race/ibt.ts` v prehliadači 3DHeat). Je
testovaná na syntetickom súbore; je tu zdokumentovaná, lebo je iracingovou polovicou toho istého
príbehu nahrávania kôl.

## Čo súbor obsahuje a ako sa číta {#what-the-file-holds-and-how-it-is-read}

Súbor je zdokumentované rozloženie pamäte simulátora zapísané na disk:

| Časť | Veľkosť | Obsah |
|---|---|---|
| Hlavička | 112 bajtov | verzia, frekvencia taktu, kde sú YAML a tabuľka premenných, dĺžka jedného riadku vzoriek, kde začínajú riadky |
| Podhlavička disku | 32 bajtov | dátum a čas začiatku, počet kôl, počet riadkov |
| Tabuľka premenných | 144 bajtov na kanál | typ, posun v riadku, počet, názov, popis, jednotka |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Riadky | jeden na takt | |

Súbor sa zamietne, keď je kratší ako 144 bajtov, keď jeho hlavička nie je v poriadku (žiadne
premenné, tabuľka premenných mimo súboru, nulová dĺžka riadku), keď chýba niektorý z
`SessionTime`, `Lap`, `Lat`, `Lon`, alebo keď žiadna vzorka nemá určenie pozície.

## Pozícia {#position}

iRacing udáva zemepisnú šírku, dĺžku a výšku, nie pozíciu v rámci trate. Pozície sa rozložia v
metroch na rovine dotyčnicovej k prvej vzorke s určením (polomer Zeme 6 371 008,8 m): `x` na východ,
`z` na juh, `y` výška - takže pri pohľade zhora, s predvoleným smerom kamery prehliadača, je sever
hore na obrazovke.

## Kolá {#laps}

Relácia sa rozdelí podľa počítadla `Lap` simulátora. Kolo sa ponechá, len ak má viac ako 60 vzoriek,
začína pod 5 % dĺžky kola (`LapDistPct`) a končí nad 95 % - teda kolá jazdené od čiary k čiare. Ak
žiadne kolo nevyhovie, súbor sa zamietne so správou, ktorá uvedie dĺžku trate z YAML. `distance` je
`LapDist` prepočítaný na začiatok kola, alebo prejdená vzdialenosť z pozícií, keď `LapDist`
chýba; `time` je `SessionTime` od začiatku kola.

## Kanály {#channels}

| iRacing | Kanál | Prepočet |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | žiadny |
| `Clutch` | `clutch` | `1 - hodnota` (iRacing počíta spojku ako zapojenú; kanál je pedál) |
| `SteeringWheelAngle` | `steer` | `-uhol / SteeringWheelAngleMax` (radiány, proti smeru hodinových ručičiek kladné, na -1..1 kladné doprava; pi, keď chýba maximum) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | žiadny |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | žiadny |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | nastavenia pomôcok |
| `dcBrakeBias` | `brakeBias` | delené 100, keď je nad 1,5 (na niektorých autách percento) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | teplota kostry v strede |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa krát 0,145038, na psi |
| `..wearM` | `tireWear.*` | `1 - hodnota` |

Každý ďalší kanál s jednou hodnotou na vzorku (a nie jediným bajtom) sa prenesie pod svojím názvom,
s predponou kolesa (`LF`, `RF`, `LR`, `RR`) premenenou na príponu (`.FL`, `.FR`, `.RL`, `.RR`), takže
grafy prehliadača ho ponúknu bez toho, aby ho niekto musel opísať.

Auto sa berie z `DriverInfo`: záznam, ktorého `CarIdx` sa zhoduje s `DriverCarIdx`, dá
`CarScreenName`, `CarID` a `CarClassShortName`. Trať je `TrackDisplayName` (alebo `TrackName`).

## Čo iRacing nedáva {#what-iracing-does-not-give}

Žiadny šmyk pneumatík sa nezaznamenáva, takže nie sú kanály šmyku. Uhol driftu sa odvodí z
rýchlosti otáčania voči dráhe (pozrite [Prešmyk, driftový uhol a odvodené kanály](slip-and-drift.md)).
Modely tratí sú v chránenom formáte a nie sú cieľom extrakcie zo súborov (pozrite [Hry](games.md)).
