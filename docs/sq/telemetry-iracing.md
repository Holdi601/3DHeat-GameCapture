---
title: "iRacing"
nav_order: 6
lang: "sq"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **nuk ka nevojë për regjistrues**. Simulatori shkruan vetë skedarët e tij të telemetrisë, `.ibt`, kur regjistrimi i telemetrisë
është ndezur (Alt+L në makinë): gjithë seancën me 60 Hz, çdo kanal që ekspozon simulatori,
me përshkrimin YAML të seancës pranë. Hidhe skedarin `.ibt` te skeda Analiza e garës e shikuesit.

Lexuesi ndodhet në shikues, jo në këtë repozitor (`src/race/ibt.ts` në shikuesin
3DHeat). Testohet mbi një skedar sintetik; dokumentohet këtu sepse është gjysma iRacing e
së njëjtës histori të regjistrimit të xhirave.

## Çfarë mban skedari, dhe si lexohet {#what-the-file-holds-and-how-it-is-read}

Skedari është struktura e dokumentuar e memories së simulatorit e shkruar në disk:

| Pjesa | Madhësia | Mban |
|---|---|---|
| Header | 112 bajt | versionin, shpejtësinë e tik-ut, ku janë YAML dhe tabela e ndryshoreve, gjatësinë e një rreshti mostre, ku fillojnë rreshtat |
| Nënheader i diskut | 32 bajt | datën dhe orën e fillimit, numrin e xhirave, numrin e rreshtave |
| Tabela e ndryshoreve | 144 bajt për kanal | llojin, zhvendosjen në rresht, numrin, emrin, përshkrimin, njësinë |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rreshtat | një për tik | |

Një skedar refuzohet kur është më i shkurtër se 144 bajt, kur header-i i tij nuk është i arsyeshëm (pa
ndryshore, tabelë ndryshoresh jashtë skedarit, gjatësi rreshti zero), kur i mungon ndonjë nga
`SessionTime`, `Lap`, `Lat`, `Lon`, ose kur asnjë mostër nuk ka pozicion të fiksuar.

## Pozicioni {#position}

iRacing raporton gjerësi, gjatësi dhe lartësi mbi nivelin e detit, jo një pozicion në kornizën e vetë pistës.
Pozicionet vendosen në metra mbi një plan tangent në mostrën e parë me fiksim (rrezja e Tokës
6,371,008.8 m): `x` lindje, `z` jug, `y` lartësia - kështu që nga lart, me drejtimin e paracaktuar të
kamerës së shikuesit, veriu është lart në ekran.

## Xhirat {#laps}

Seanca ndahet sipas numëruesit `Lap` të simulatorit. Një xhiro mbahet vetëm nëse ka më shumë se 60
mostra, fillon nën 5% të distancës së xhirasë (`LapDistPct`) dhe mbaron mbi 95% - pra xhirat
e vozitura nga vija në vijë. Nëse asnjë xhiro nuk kualifikohet, skedari refuzohet me një mesazh që emërton
gjatësinë e pistës nga YAML. `distance` është `LapDist` e rivendosur në fillimin e xhirasë, ose
distanca e vozitur nga pozicionet kur mungon `LapDist`; `time` është `SessionTime` nga
fillimi i xhirasë.

## Kanalet {#channels}

| iRacing | Kanali | Konvertimi |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | asnjë |
| `Clutch` | `clutch` | `1 - value` (iRacing e numëron friksionin si të lidhur; kanali është pedali) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radianë, e kundërt me akrepat pozitive, në -1..1 djathtas pozitive; pi kur mungon maksimumi) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | asnjë |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | asnjë |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | cilësime ndihmësish |
| `dcBrakeBias` | `brakeBias` | pjesëtohet me 100 kur është mbi 1.5 (përqindje në disa makina) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura e karkasës në mes |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa herë 0.145038, në psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Çdo kanal tjetër me një vlerë për mostër (dhe jo një bajt i vetëm) kalon nën emrin e vet,
me parashtesën e rrotës (`LF`, `RF`, `LR`, `RR`) të kthyer në prapashtesë
(`.FL`, `.FR`, `.RL`, `.RR`), që grafikët e shikuesit ta ofrojnë pa e përshkruar askush.

Makina vjen nga `DriverInfo`: hyrja ku `CarIdx` përputhet me `DriverCarIdx` jep
`CarScreenName`, `CarID` dhe `CarClassShortName`. Pista është `TrackDisplayName` (ose
`TrackName`).

## Çfarë nuk jep iRacing {#what-iracing-does-not-give}

Nuk regjistrohet slip i gomave, ndaj nuk ka kanale slip. Këndi i drift-it nxirret nga shpejtësia e yaw
kundrejt shtegut (shih [Slip, drift dhe kanalet e nxjerra](slip-and-drift.md)). Modelet e pistave
vijnë në një format të mbrojtur dhe nuk janë objektiv për nxjerrje skedarësh (shih [Lojërat](games.md)).
