---
title: iRacing
nav_order: 6
lang: "cs"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **nepotřebuje žádný záznamník**. Simulátor sám zapisuje soubory telemetrie `.ibt`, když je zapnuté logování telemetrie (Alt+L v autě): celou jízdu při 60 Hz, každý kanál, který simulátor vystavuje, a k tomu popis relace v YAML. Soubor `.ibt` přetáhněte na záložku prohlížeče **Analýza závodu**.

Čtečka je v prohlížeči, ne v tomto repozitáři (`src/race/ibt.ts` v prohlížeči 3DHeat). Je testovaná na syntetickém souboru. Je tu popsaná, protože je iRacingovou polovinou stejného příběhu nahrávání kol.

## Co soubor obsahuje a jak se čte {#what-the-file-holds-and-how-it-is-read}

Soubor je zdokumentované paměťové rozložení simulátoru zapsané na disk:

| Část | Velikost | Obsahuje |
|---|---|---|
| Hlavička | 112 bajtů | verzi, frekvenci ticků, kde jsou YAML a tabulka proměnných, délku jednoho řádku vzorku, kde řádky začínají |
| Podhlavička disku | 32 bajtů | datum a čas začátku, počet kol, počet řádků |
| Tabulka proměnných | 144 bajtů na kanál | typ, posun v řádku, počet, název, popis, jednotku |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Řádky | jeden na tick | |

Soubor se odmítne, když je kratší než 144 bajtů, když jeho hlavička není v pořádku (žádné proměnné, tabulka proměnných mimo soubor, nulová délka řádku), když chybí některé z `SessionTime`, `Lap`, `Lat`, `Lon`, nebo když žádný vzorek nemá zaměření polohy.

## Pozice {#position}

iRacing hlásí zeměpisnou šířku, délku a nadmořskou výšku, ne pozici v rámci trati. Pozice se kladou v metrech na rovinu tečnou k prvnímu vzorku se zaměřením (poloměr Země 6 371 008,8 m): `x` na východ, `z` na jih, `y` je nadmořská výška. Takže při pohledu shora s výchozím směrem kamery prohlížeče je sever nahoře na obrazovce.

## Kola {#laps}

Relace se rozdělí podle počítadla `Lap` simulátoru. Kolo se ponechá jen tehdy, když má více než 60 vzorků, začíná pod 5 % délky kola (`LapDistPct`) a končí nad 95 %. Jsou to tedy kola jeté čára na čáru. Když žádné neprojde, soubor se odmítne se zprávou, která pojmenuje délku trati z YAML. `distance` je `LapDist` přepočtené na začátek kola, nebo ujetá vzdálenost z pozic, když `LapDist` chybí. `time` je `SessionTime` od začátku kola.

## Kanály {#channels}

| iRacing | Kanál | Převod |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | žádný |
| `Clutch` | `clutch` | `1 - value` (iRacing počítá spojku jako zapojenou, kanál je pedál) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radiány, proti směru hodinových ručiček kladné, na −1..1 vpravo kladné; pi, když maximum chybí) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | žádný |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | žádný |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | nastavení asistencí |
| `dcBrakeBias` | `brakeBias` | děleno 100, když je nad 1,5 (u některých aut procenta) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | teplota pláště uprostřed |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa × 0,145038, na psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Každý další kanál s jednou hodnotou na vzorek (a ne jen jeden bajt) se propustí pod svým jménem. Předpona kola (`LF`, `RF`, `LR`, `RR`) se přepíše na příponu (`.FL`, `.FR`, `.RL`, `.RR`), takže grafy prohlížeče ho nabídnou, aniž by ho kdo musel popisovat.

Auto je z `DriverInfo`: položka, jejíž `CarIdx` se shoduje s `DriverCarIdx`, dává `CarScreenName`, `CarID` a `CarClassShortName`. Trať je `TrackDisplayName` (nebo `TrackName`).

## Co iRacing nedává {#what-iracing-does-not-give}

Žádný skluz pneumatik se nezapisuje, takže nejsou skluzové kanály. Úhel driftu se odvozuje z rychlosti zatáčení proti dráze (viz [Skluz, drift a odvozené kanály](slip-and-drift.md)). Modely tratí se dodávají v chráněném formátu a nejsou cílem extrakce souborů (viz [Hry](games.md)).
