---
title: "Assetto Corsa játékok"
nav_order: 2
lang: "hu"
source: telemetry-assetto-corsa.md
source_hash: "b428f07c954c"
nav_exclude: true
search_exclude: true
---
# Assetto Corsa, ACC, AC EVO és AC Rally {#assetto-corsa-acc-ac-evo-and-ac-rally}

```bash
python -m heat3d_capture telemetry --game ac      -o laps   # Assetto Corsa
python -m heat3d_capture telemetry --game acc     -o laps   # Assetto Corsa Competizione
python -m heat3d_capture telemetry --game acevo   -o laps   # Assetto Corsa EVO
python -m heat3d_capture telemetry --game acrally -o laps   # Assetto Corsa Rally
```

Kód: [`telemetry/kunos.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/kunos.py).
Tesztek: `tests/test_kunos.py` (szintetikus oldalak). Még nem futtatták az élő játékokon.

## Honnan jön az adat {#where-the-data-comes-from}

A Kunos játékai telemetriát **névvel ellátott Windows-megosztott memóriaoldalakon** teszik közzé az alkalmazásoknak: a játék írja, és bárki olvashatja. A rögzítő csak olvasásra nyitja meg őket (`mmap` egy címkenévvel), ezért a játékot futtató gépen kell futnia, Windowson; máshol kilép egy üzenettel.

Az oldalak egyszer nyílnak meg, amikor a rögzítő elindul. Biztonságos sorrend: először elindítani a játékot és beülni az autóba; hogy a rögzítő a játék előtt indítva működik-e, azt nem ellenőrizték.

| `--game` | Fizikai oldal | Grafikai oldal (köridő-számláló) | Statikus oldal (nevek) |
|---|---|---|---|
| `ac` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acc` | `Local\acpmf_physics` | `Local\acpmf_graphics` | `Local\acpmf_static` |
| `acrally` | `Local\acpmf_physics` | nincs használva | `Local\acpmf_static` |
| `acevo` | `Local\acevo_pmf_physics` | nincs használva | `Local\acevo_pmf_static` |

A fizikai oldalt másodpercenként 200-szor olvassuk (`hz=200`); új mintát csak akkor veszünk, ha a `packetId` megváltozott és nem nulla. A fizikai oldal első 800 bájtja mind a négy játékban ugyanazt az elrendezést használja; az első játék oldala csak 580 bájtot garantál, ezért ha egy 800 bájtos leképezés nem nyitható meg, a rögzítő 580-ra esik vissza, és az azon túli mezők hiányoznak.

## Pozíció {#position}

Egyik oldal sem hordoz autópozíciót mint olyat, de a fizikai oldal **minden gumi érintkezési pontját világkoordinátában** tartalmazza (420-as eltolás, négy XYZ hármas). Az autó pozíciója ezek átlaga. Egy oldal, amelyen mind a négy érintkezési pont nulla (menü, garázs), nem ad mintát.

## Csatornák {#channels}

| Csatorna | Forrás | Megjegyzés |
|---|---|---|
| `time` | a rögzítő saját órája | másodpercek a felvétel kezdete óta, a kör első mintájára igazítva |
| `x`, `y`, `z` | az érintkezési pontok átlaga | világ-méter |
| `speed` | `speedKmh` / 3,6 | m/s |
| `throttle`, `brake`, `clutch` | `gas`, `brake`, `clutch` | 0..1 |
| `steer` | `steerAngle` | a játék egységei, körönként -1..1-re skálázva a kör által használt legnagyobb abszolút értékkel, **csak ha** ez meghaladja az 1,05-öt (a -1..1 közötti bemenet érintetlen marad) |
| `gear` | `gear - 1` | a játék így számolja: 0 hátramenet, 1 üresjárat, 2 első fokozat; -1, 0, 1 ... formában íródik |
| `rpm` | `rpms` | |
| `latAcc`, `vertAcc`, `longAcc` | `accG` x, y, z, szorozva 9,80665-tel | m/s² |
| `yaw`, `pitch`, `roll` | `heading`, `pitch`, `roll` | rad |
| `yawRate` | `localAngularVel` y | rad/s |
| `latVel`, `vertVel`, `longVel` | helyi sebesség a 568-as eltolásnál | az autó keretében; csak ha nem nulla. Hogy az x melyik oldalra mutat, mindkét irányban dokumentált, ezért a driftszög nagyságát olvasd, ne az előjelét |
| `drs`, `pitLimiter`, `boost` | `drs`, `pitLimiterOn`, `turboBoost` | |
| `brakeBias` | 564-es eltolás | csak 800 bájtos oldalon |
| `tcActive`, `absActive` | ACC, AC EVO, AC Rally: a 204-es és 252-es eltolás, 1-ként íródik, ha nagyobb 0-nál; AC: `tcInAction`/`absInAction` a 800 bájtos oldalról, ha van | segédrendszerek működnek |
| `tireTemp.*` | `tyreCoreTemperature` | °C |
| `tireTempInner/Middle/Outer.*` | `tyreTempI/M/O` | °C |
| `tirePressure.*` | `wheelsPressure` | psi |
| `wheelLoad.*` | `wheelLoad` | N |
| `wheelSpeed.*` | `wheelAngularSpeed` | rad/s |
| `camber.*` | `camberRAD` | rad |
| `suspensionM.*` | `suspensionTravel` | m |
| `suspension.*` | származtatott | 0..1 a körben használt utazásból (a `suspensionM` minimumtól maximumig) |
| `brakeTemp.*` | `brakeTemp` | °C |
| `slipRatio.*`, `slipAngle.*` | 640-es és 656-os eltolás (800 bájtos oldal) | egy tipikus csúcsgal osztva – lásd lent |
| `slipRatioRaw.*`, `slipAngleRaw.*` | ugyanaz | a fizikai értékek, nem skálázva |
| `padLife.*`, `discLife.*` | 740-es és 756-os eltolás | csak 800 bájtos oldal |

Az AC Rally a gumi- és fékhőmérsékleteit kelvinben küldi: a `--game acrally` esetén ezen értékek közül minden 200 fölötti értékből 273,15 kivonódik.

A `wheelSlip` (56-os eltolás) dekódolva van, de nem íródik.

## Csúszásskálázás {#slip-scaling}

A Forza úgy küldi a csúszást, hogy 1 a tapadás határa. A Kunos a fizikai csúszási arányt és csúszási szöget küldi. Ezért a rögzítő ezeket egy tipikus aszfaltcsúccsal osztja – **0,12** a csúszási aránynál és **0,14 rad (körülbelül 8 fok)** a csúszási szögnél –, így a nézegető „1 felett csúszik” olvasata nagyjából érvényes marad; a nyers értékeket a skálázottak mellett megtartja, és `"meta": {"slip": "scaled"}`-et ír. Hogy a tapadás valójában hol ér véget, azt a nézegető autónként méri a körökből. Lásd [Csúszás, driftszög és származtatott csatornák](slip-and-drift.md).

## Körök {#laps}

- Az **AC és ACC** a grafikai oldalon számolja a köröket (`completedLaps` a 132-es eltolásnál, az utolsó kör ideje ezredmásodpercben a 144-esnél). A `CounterSplitter` akkor zár le egy kört, amikor a számláló változik; befejezettként, a játék köridejével jelöli, csak ha a számláló pontosan eggyel nőtt.
- Az **AC EVO és AC Rally** nem olvas köröket (az EVO grafikai oldala más, nagyobb elrendezésű; az AC Rally szakaszokat fut). A `LineSplitter` azt a pontot használja vonalként, ahol a rögzítés elkezdődött: egy kör akkor zárul le, amikor az autó legközelebb ér a vonalhoz ugyanabba az irányba haladva, egy szakasz vagy bármely futam pedig akkor, amikor az autó 8 másodpercig áll.

Részletek és küszöbértékek: [Kör- és szakaszdarabolás](lap-splitting.md).

## Pálya- és autónevek {#track-and-car-names}

Egyszer, az első minta érkezésekor olvassuk a statikus oldalból: az AC-nél, ACC-nél és AC Rallynál az autót (UTF-16, 68-as eltolás) és a pályát (134-es eltolás); az AC EVO-nál a pályát és konfigurációját (egybájtos szöveg a 136-os és 169-es eltolásnál, szóközzel összefűzve), autó nélkül. Ezek a fájlba `track` és `car: {"name": ...}` formában kerülnek.

## A körfájl {#the-lap-file}

A `game` értéke `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo` vagy `assetto-corsa-rally`; a `meta` az AC Rallynál `{"slip": "scaled", "discipline": "rally"}`, a másik háromnál `{"slip": "scaled", "discipline": "circuit"}`. `surface` nem íródik.

## Források {#sources}

Az AC1 megosztott memória SDK; az ACC megosztott memória dokumentáció (v1.8); az AC EVO elrendezése, ahogy a `albertowd/live-telemetry-evo` méri; az AC Rally elrendezése, ahogy a `LuizZak/AssettoCorsaRallyTelemetryReader` olvassa. Lásd [Játékok](games.md).
