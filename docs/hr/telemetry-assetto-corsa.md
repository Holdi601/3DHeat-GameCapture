---
title: "Assetto Corsa, ACC, AC EVO i AC Rally"
nav_order: 2
lang: "hr"
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
Testovi: `tests/test_kunos.py` (sintetičke stranice). Još nije pokrenuto uz žive igre.

## Odakle dolaze podaci {#where-the-data-comes-from}

Kunosove igre objavljuju telemetriju za aplikacije kao **imenovane stranice dijeljene
memorije u Windowsu** koje igra piše i koje svatko smije čitati. Snimač ih otvara samo za
čitanje (`mmap` s oznakom imena), pa mora raditi **na računalu na kojem igra radi**, na
Windowsu; drugdje izlazi uz poruku.

Stranice se otvaraju jednom, kad snimač počne. Siguran redoslijed je prvo pokrenuti igru i
ući u automobil; nije provjereno radi li pokretanje snimača prije igre.

| `--game` | Stranica fizike | Stranica grafike (brojač krugova) | Statička stranica (imena) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nije korištena | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nije korištena | `Local\acevo_pmf_static` |

Stranica fizike čita se 200 puta u sekundi (`hz=200`); novi uzorak se uzima samo kad se
njezin `packetId` promijeni i nije nula. Prvih 800 bajtova stranice fizike ima isti raspored
u sve četiri igre; stranica prve igre sigurno ima samo 580 bajtova, pa ako se 800-bajtno
preslikavanje ne može otvoriti, snimač prelazi na 580, a polja iza toga nisu prisutna.

## Položaj {#position}

Nijedna stranica ne nosi položaj automobila kao takav, ali stranica fizike sadrži **točku
dodira svake gume sa svijetom** u svjetskim koordinatama (pomak 420, četiri trojke XYZ).
Položaj automobila je srednja vrijednost četiriju. Stranica čije su sve točke dodira nule
(izbornik, garaža) ne daje uzorak.

## Kanali {#channels}

| Kanal | Iz | Napomene |
|---|---|---|
| `time` | vlastiti sat snimača | sekunde od početka snimanja, preračunate na prvi uzorak kruga |
| `x`, `y`, `z` | srednja točka dodira guma | metri u svijetu |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | jedinice igre, skalirane po krugu na -1..1 prema najvećoj apsolutnoj vrijednosti koju je krug koristio, **samo ako** ta vrijednost premašuje 1,05 (ulaz već u -1..1 ostaje netaknut) |
| `gear` | `gear - 1` | igra broji 0 za vožnju unatrag, 1 za mrtvi hod, 2 za prvu; zapisuje se kao -1, 0, 1 ... |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, puta 9,80665 | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | lokalna brzina na pomaku 568 | okvir automobila; samo kad nije nula. Na koju stranu pokazuje x dokumentirano je u oba smjera, zato čitajte veličinu kuta drifta, a ne predznak |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | pomak 564 | samo stranica od 800 bajtova |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: pomaci 204 i 252, zapisani kao 1 kad je iznad 0; AC: `tcInAction`/`absInAction` sa stranice od 800 bajtova kad je prisutna | pomoći u radu |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | izvedeno | 0..1 puta koji je ovaj krug koristio (najmanji do najveći `suspensionM`) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | pomaci 640, 656 (stranica od 800 bajtova) | podijeljeno s tipičnim vrhom - vidi niže |
| `slipRatioRaw.*`, `slipAngleRaw.*` | isto | fizičke vrijednosti, neskalirane |
| `padLife.*`, `discLife.*` | pomaci 740, 756 | samo stranica od 800 bajtova |

AC Rally šalje temperature guma i kočnica u kelvinima: za `--game acrally` svaka od tih
vrijednosti iznad 200 umanjuje se za 273,15.

`wheelSlip` (pomak 56) se dekodira, ali se ne zapisuje.

## Skaliranje klizanja {#slip-scaling}

Forza šalje klizanje normalizirano tako da je 1 rub prianjanja. Kunos šalje fizički omjer
klizanja i kut klizanja. Zato ih snimač dijeli s tipičnim vrhom na asfaltu - **0,12** za
omjer klizanja i **0,14 rad (oko 8 stupnjeva)** za kut klizanja - pa čitanje preglednika
„iznad 1 znači klizanje” približno vrijedi, sirove vrijednosti čuvaju se uz njih, a zapisuje
se `"meta": {"slip": "scaled"}`. Gdje prianjanje stvarno prestaje, preglednik mjeri po
automobilu iz krugova. Vidi [Klizanje, drift i izvedeni kanali](slip-and-drift.md).

## Krugovi {#laps}

- **AC i ACC** broje krugove na stranici grafike (`completedLaps` na pomaku 132, vrijeme
  zadnjeg kruga u milisekundama na 144). `CounterSplitter` zatvara krug kad se brojač
  promijeni; krug se označava završenim, s vremenom igre, samo ako je brojač porastao točno
  za jedan.
- **AC EVO i AC Rally** se ne čitaju za krugove (stranica grafike EVO-a je drukčiji, veći
  raspored; AC Rally vozi etape). `LineSplitter` koristi mjesto na kojem je snimanje počelo
  kao liniju: krug se zatvara kad automobil ponovno prođe najbliže toj liniji u istom smjeru,
  a etapa ili svaka vožnja se zatvara kad automobil stoji 8 sekundi.

Pojedinosti i pragovi: [Kako se krugovi i etape dijele](lap-splitting.md).

## Nazivi staze i vozila {#track-and-car-names}

Čitaju se jednom, sa statičke stranice, kad stigne prvi uzorak: za AC, ACC i AC Rally
vozilo (UTF-16, pomak 68) i staza (pomak 134); za AC EVO staza i njezina konfiguracija
(jednobajtni tekst na pomacima 136 i 169, spojeni razmakom) i bez vozila. Zapisuju se u
datoteku kao `track` i `car: {"name": ...}`.

## Datoteka kruga {#the-lap-file}

`game` je `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` ili
`assetto-corsa-rally`; `meta` je `{"slip": "scaled", "discipline": "rally"}` za AC Rally, a
`{"slip": "scaled", "discipline": "circuit"}` za ostale tri. `surface` se ne zapisuje.

## Izvori {#sources}

SDK za dijeljenu memoriju AC1; dokumentacija dijeljene memorije ACC-a (v1.8); raspored AC
EVO-a kako je izmjeren u `albertowd/live-telemetry-evo`; raspored AC Rally-ja kako ga čita
`LuizZak/AssettoCorsaRallyTelemetryReader`. Vidi [Igre](games.md).
