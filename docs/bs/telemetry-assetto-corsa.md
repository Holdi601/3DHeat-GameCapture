---
title: "Assetto Corsa igre"
nav_order: 2
lang: "bs"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO i AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kod: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Testovi: `tests/test_kunos.py` (sintetičke stranice). Još nije pokrenuto protiv živih igara.

## Odakle dolaze podaci {#where-the-data-comes-from}

Kunosove igre objavljuju telemetriju za aplikacije kao **imenovane Windows stranice dijeljene memorije** koje
igra upisuje, a čitati ih može bilo ko. Snimač ih otvara samo za čitanje (`mmap` s imenom oznake),
pa mora raditi **na računaru na kojem radi igra**, na Windowsu; drugdje izlazi s porukom.
Stranice se otvaraju jednom, kad se snimač pokrene. Sigurniji redoslijed je prvo pokrenuti igru i ući u
automobil; da li radi pokretanje snimača prije igre nije
provjereno.

| `--game` | Stranica fizike | Stranica grafike (brojač krugova) | Statična stranica (imena) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | ne koristi se | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | ne koristi se | `Local\acevo_pmf_static` |

Stranica fizike čita se 200 puta u sekundi (`hz=200`); novi uzorak se uzima samo kada se njen
`packetId` promijenio i nije nula. Prvih 800 bajta stranice fizike dijele jedan
raspored u sve četiri igre; stranica prve igre ima zajamčenih samo 580 bajta, pa ako se
mapiranje od 800 bajta ne može otvoriti, snimač se vraća na 580 i polja iza toga
su odsutna.

## Pozicija {#position}

Nijedna stranica ne nosi poziciju automobila kao takvu, ali stranica fizike drži **kontaktnu tačku svake
gume u svjetskim koordinatama** (pomak 420, četiri XYZ trojke). Pozicija automobila je
srednja vrijednost ta četiri. Stranica čije su sve kontaktne tačke nula (meni, garaža) ne daje
uzorak.

## Kanali {#channels}

| Kanal | Iz | Napomene |
|---|---|---|
| `time` | vlastiti sat snimača | sekunde od početka snimanja, pomaknute na prvi uzorak kruga |
| `x`, `y`, `z` | srednja kontaktna tačka guma | svjetski metri |
| `speed` | `speedKmh` / 3.6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | igrine jedinice, skalirane po krugu na -1..1 najvećom apsolutnom vrijednošću koju je krug koristio, **samo ako** ta vrijednost prelazi 1,05 (ulaz koji je već u -1..1 ostaje netaknut) |
| `gear` | `gear - 1` | igra broji 0 nazad, 1 neutralno, 2 prva; zapisuje se kao -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, puta 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokalna brzina na pomaku 568 | okvir automobila; samo kada nije nula. Na koju stranu pokazuje x dokumentirano je na oba načina, pa čitajte veličinu ugla zanošenja, a ne njegov predznak |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | pomak 564 | samo stranica od 800 bajta |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: pomaci 204 i 252, zapisano kao 1 kada je iznad 0; AC: `tcInAction`/`absInAction` sa stranice od 800 bajta kada postoji | pomoćni sistemi u radu |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | izvedeno | 0..1 hoda korištenog u ovom krugu (od minimuma do maksimuma `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | pomaci 640, 656 (stranica od 800 bajta) | podijeljeno tipičnim vrhom - pogledajte ispod |
| `slipRatioRaw.*`, `slipAngleRaw.*` | isto | fizičke vrijednosti, neskalirane |
| `padLife.*`, `discLife.*` | pomaci 740, 756 | samo stranica od 800 bajta |

AC Rally šalje temperature guma i kočnica u kelvinima: za `--game acrally`, od svake takve
vrijednosti iznad 200 oduzima se 273,15.

`wheelSlip` (pomak 56) se dekodira, ali ne zapisuje.

## Skaliranje klizanja {#slip-scaling}

Forza šalje klizanje normalizirano tako da je 1 rub prianjanja. Kunos šalje fizički omjer klizanja
i ugao klizanja. Zato ih snimač dijeli tipičnim asfaltnim vrhom - **0,12** za
omjer klizanja i **0,14 rad (oko 8 stepeni)** za ugao klizanja - tako da čitanje preglednika "preko 1
znači klizanje" približno vrijedi, zadržava sirove vrijednosti pored njih i zapisuje
`"meta": {"slip": "scaled"}`. Gdje prianjanje zaista završava, preglednik mjeri po automobilu iz
krugova. Pogledajte [Klizanje, zanošenje i izvedeni kanali](slip-and-drift.md).

## Krugovi {#laps}

- **AC i ACC** broje krugove na stranici grafike (`completedLaps` na pomaku 132, vrijeme
  posljednjeg kruga u milisekundama na 144). `CounterSplitter` zatvara krug kada se brojač
  promijeni; označava se završenim, s igrinim vremenom kruga, samo ako je brojač porastao za
  tačno jedan.
- **AC EVO i AC Rally** se ne čitaju za krugove (grafička stranica EVO-a je drugačiji, veći
  raspored; AC Rally vozi dionice). `LineSplitter` koristi tačku gdje je snimanje počelo kao
  liniju: krug se zatvara kada automobil sljedeći put prođe najbliže njoj krećući se istim smjerom, a
  dionica ili bilo koja vožnja zatvara se kada automobil stoji 8 sekundi.

Detalji i pragovi: [Dijeljenje na krugove i dionice](lap-splitting.md).

## Imena staze i automobila {#track-and-car-names}

Čitaju se jednom, sa statične stranice, kad stigne prvi uzorak: za AC, ACC i AC Rally
automobil (UTF-16, pomak 68) i staza (pomak 134); za AC EVO staza i njena konfiguracija
(jednobajtni tekst na pomacima 136 i 169, spojeni razmakom) i nema automobila. Idu u
datoteku kao `track` i `car: {"name": ...}`.

## Datoteka kruga {#the-lap-file}

`game` je `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ili
`assetto-corsa-rally`; `meta` je `{"slip": "scaled", "discipline": "rally"}` za AC Rally i
`{"slip": "scaled", "discipline": "circuit"}` za ostale tri. `surface` se ne zapisuje.

## Izvori {#sources}

AC1 SDK za dijeljenu memoriju; dokumentacija dijeljene memorije za ACC (v1.8); raspored AC EVO-a
kako je izmjeren u `albertowd/live-telemetry-evo`; AC Rally-jev kako ga čita
`LuizZak/AssettoCorsaRallyTelemetryReader`. Pogledajte [Igre](games.md).
