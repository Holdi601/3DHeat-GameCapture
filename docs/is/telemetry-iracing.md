---
title: "iRacing"
nav_order: 6
lang: "is"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing þarf **engan skráningarhugbúnað**. Hermirinn skrifar sínar eigin mælingaskrár, `.ibt`, þegar
mælingaskráning er á (Alt+L í bílnum): alla lotuna á 60 Hz, hverja rás sem hermirinn birtir,
ásamt YAML lýsingu lotunnar. Slepptu `.ibt` skránni á flipann Kappakstursgreining í skoðaranum.

Lesarinn er í skoðaranum, ekki í þessari geymslu (`src/race/ibt.ts` í 3DHeat
skoðaranum). Hann er prófaður á tilbúinni skrá; hann er skjalfestur hér af því að hann er iRacing-
helmingur sömu hringskráningarsögu.

## Hvað skráin geymir og hvernig hún er lesin {#what-the-file-holds-and-how-it-is-read}

Skráin er skjalfest minnisskipulag hermisins skrifað á disk:

| Hluti | Stærð | Geymir |
|---|---|---|
| Haus | 112 bæti | útgáfu, tíðni, hvar YAML og breytutaflan eru, lengd einnar sýnaraðar, hvar raðirnar byrja |
| Undirhaus disks | 32 bæti | upphafsdagsetningu og -tíma, fjölda hringja, fjölda raða |
| Breytutafla | 144 bæti á rás | tegund, hliðrun í röðinni, fjölda, heiti, lýsingu, einingu |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Raðir | ein á hvert tikk | |

Skrá er hafnað þegar hún er styttri en 144 bæti, þegar haus hennar er ekki heilbrigður (engar
breytur, breytutafla utan skrárinnar, röðin núll á lengd), þegar hana vantar eitthvað af
`SessionTime`, `Lap`, `Lat`, `Lon`, eða þegar ekkert sýni hefur staðsetningarfestu.

## Staða {#position}

iRacing gefur upp breiddargráðu, lengdargráðu og hæð, ekki stöðu í eigin ramma brautarinnar.
Stöður eru lagðar út í metrum á sléttu sem snertir jörðina í fyrsta sýni með festu (radíus jarðar
6.371.008,8 m): `x` austur, `z` suður, `y` hæðin - svo að séð að ofan, með sjálfgefinni stefnu
myndavélar skoðarans, er norður upp á skjánum.

## Hringir {#laps}

Lotan er skipt eftir `Lap` teljara hermisins. Hringur er aðeins geymdur ef hann hefur fleiri en 60
sýni, byrjar undir 5% af hringlengd (`LapDistPct`) og endar yfir 95% - það er, hringir
eknir frá línu til línu. Ef enginn hringur uppfyllir skilyrðin er skránni hafnað með skilaboðum sem nefna
lengd brautarinnar úr YAML. `distance` er `LapDist` miðað við upphaf hringsins, eða
ekna vegalengdin úr stöðunum þegar `LapDist` vantar; `time` er `SessionTime` frá
upphafi hringsins.

## Rásir {#channels}

| iRacing | Rás | Umbreyting |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | engin |
| `Clutch` | `clutch` | `1 - value` (iRacing telur kúplinguna tengda; rásin er pedallinn) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radíanar, rangsælis jákvætt, í -1..1 hægri jákvætt; pi þegar hámarkið vantar) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | engin |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | engin |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | stillingar hjálpartækja |
| `dcBrakeBias` | `brakeBias` | deilt með 100 þegar yfir 1,5 (prósenta í sumum bílum) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | hiti hjólbarðabols í miðjunni |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa sinnum 0,145038, í psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Sérhver önnur rás með eitt gildi fyrir hvert sýni (og ekki stakt bæti) er send áfram undir
eigin heiti, með hjólaforskeyti (`LF`, `RF`, `LR`, `RR`) breytt í viðskeyti
(`.FL`, `.FR`, `.RL`, `.RR`), svo að línurit skoðarans bjóði hana án þess að nokkur lýsi henni.

Bíllinn kemur úr `DriverInfo`: færslan þar sem `CarIdx` passar við `DriverCarIdx` gefur
`CarScreenName`, `CarID` og `CarClassShortName`. Brautin er `TrackDisplayName` (eða
`TrackName`).

## Það sem iRacing gefur ekki {#what-iracing-does-not-give}

Ekkert hjólbarðaslip er skráð, svo engar slip-rásir eru til. Skriðhornið er leitt af
yaw-hraðanum gagnvart ferlinum (sjá [Slip, skrið og afleiddar rásir](slip-and-drift.md)). Brautarlíkön
fylgja í vernduðu sniði og er ekki hægt að draga út úr skrám (sjá [Leikir](games.md)).
