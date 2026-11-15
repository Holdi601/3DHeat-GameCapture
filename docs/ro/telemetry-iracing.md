---
title: "iRacing"
nav_order: 6
lang: "ro"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **nu are nevoie de înregistrator**. Simulatorul își scrie propriile fișiere de telemetrie,
`.ibt`, când înregistrarea telemetriei este pornită (Alt+L în mașină): toată sesiunea la 60 Hz, fiecare
canal pe care îl expune simulatorul, cu descrierea YAML a sesiunii alături. Trageți fișierul `.ibt` pe
fila Analiză de cursă a vizualizatorului.

Cititorul se află în vizualizator, nu în acest depozit (`src/race/ibt.ts` din vizualizatorul 3DHeat).
Este testat pe un fișier sintetic; este documentat aici pentru că este partea iRacing a aceleiași
povești a înregistrării tururilor.

## Ce conține fișierul și cum este citit {#what-the-file-holds-and-how-it-is-read}

Fișierul este aspectul de memorie documentat al simulatorului, scris pe disc:

| Parte | Mărime | Conține |
|---|---|---|
| Antet | 112 octeți | versiunea, rata de tact, unde sunt YAML-ul și tabelul de variabile, lungimea unui rând de eșantion, unde încep rândurile |
| Sub-antet de disc | 32 de octeți | data și ora de început, numărul de ture, numărul de rânduri |
| Tabelul de variabile | 144 de octeți per canal | tipul, decalajul în rând, numărul, numele, descrierea, unitatea |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Rânduri | unul per tact | |

Un fișier este refuzat când are mai puțin de 144 de octeți, când antetul nu este sănătos (fără
variabile, un tabel de variabile în afara fișierului, o lungime de rând zero), când îi lipsește vreunul
dintre `SessionTime`, `Lap`, `Lat`, `Lon`, sau când niciun eșantion nu are o poziție fixată.

## Poziția {#position}

iRacing raportează latitudinea, longitudinea și altitudinea, nu o poziție în propriul cadru al pistei.
Pozițiile sunt așezate în metri pe un plan tangent la primul eșantion cu poziție fixată (raza Pământului
6.371.008,8 m): `x` est, `z` sud, `y` altitudinea - astfel încât, privit de sus, cu cap-ul implicit al
camerei vizualizatorului, nordul este sus pe ecran.

## Ture {#laps}

Sesiunea este împărțită după contorul `Lap` al simulatorului. Un tur se păstrează doar dacă are mai mult
de 60 de eșantioane, începe sub 5% din distanța turului (`LapDistPct`) și se termină peste 95% - adică
ture parcurse de la linie la linie. Dacă niciun tur nu se califică, fișierul este refuzat, cu un mesaj
care numește lungimea pistei din YAML. `distance` este `LapDist` raportat la începutul turului, sau
distanța parcursă din poziții când `LapDist` lipsește; `time` este `SessionTime` de la începutul turului.

## Canale {#channels}

| iRacing | Canal | Conversie |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | niciuna |
| `Clutch` | `clutch` | `1 - value` (iRacing numără ambreiajul ca fiind cuplat; canalul este pedala) |
| `SteeringWheelAngle` | `steer` | `-angle / SteeringWheelAngleMax` (radiani, pozitiv în sens trigonometric, la -1..1 pozitiv spre dreapta; pi când maximul lipsește) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | niciuna |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | niciuna |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | setările de asistență |
| `dcBrakeBias` | `brakeBias` | împărțit la 100 când depășește 1,5 (procent, la unele mașini) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura carcasei, pe mijlocul benzii de rulare |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa înmulțit cu 0,145038, în psi |
| `..wearM` | `tireWear.*` | `1 - value` |

Fiecare alt canal cu o singură valoare pe eșantion (și care nu este un singur octet) trece sub propriul
nume, iar prefixul de roată (`LF`, `RF`, `LR`, `RR`) devine sufix (`.FL`, `.FR`, `.RL`, `.RR`), astfel
încât graficele vizualizatorului îl oferă fără ca cineva să-l fi descris.

Mașina vine din `DriverInfo`: intrarea a cărei `CarIdx` se potrivește cu `DriverCarIdx` dă
`CarScreenName`, `CarID` și `CarClassShortName`. Pista este `TrackDisplayName` (sau `TrackName`).

## Ce nu oferă iRacing {#what-iracing-does-not-give}

Nu se înregistrează alunecarea anvelopelor, deci nu există canale de slip. Unghiul de derapaj este
calculat din viteza de rotație față de traseu (vezi [Slip, derapaj și canale derivate](slip-and-drift.md)).
Modelele de pistă vin într-un format protejat și nu sunt o țintă de extragere a fișierelor (vezi
[Jocurile](games.md)).
