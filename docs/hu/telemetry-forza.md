---
title: "Forza"
nav_order: 1
lang: "hu"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon és Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kód: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(elrendezés-felismerés),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(minden csatorna, körfájlok, továbbítás).

## Bekapcsolás a játékban {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out** (Beállítások -> HUD és játékmenet -> Data Out): `ON`, IP `127.0.0.1`, port `5300` (vagy amit a `--port`-tal adsz meg). A Forza Motorsport csomagformátumot is kínál: **Dash** legyen, ne Sled. A Sled egyáltalán nem hordoz pozíciót, a rögzítő visszautasítja.

A rögzítő a `127.0.0.1`-re köt, ezért a játéknak ugyanazon a gépen kell futnia.

## Mit küld a játék, és hogyan találjuk meg az elrendezést {#what-the-game-sends-and-how-the-layout-is-found}

A Data Out egy UDP-csomag szimulációs lépésenként (másodpercenként körülbelül 60), egy lapos, little-endian C-struktúra, ezekben a méretekben:

| Hossz | Változat |
|---|---|
| 232 bájt | Motorsport „Sled”: nincs pozíció. Visszautasítva egy üzenettel, amely a Dashre váltásra kér. |
| 311 bájt | Motorsport „Dash”: a Sled blokk plusz a 79 bájtos dash blokk |
| 324 bájt | Horizon „Dash”: ugyanaz, a két blokk között kitöltéssel |
| 331 bájt | Forza Motorsport (2023): Dash plusz 20 bájt gumikopás és a pályaazonosító |

A Sled blokk (0–231 eltolások) stabil. Hogy a dash blokk hol kezdődik a Horizon-változatban, azt a közzétett forrásokban ellentmondásosan írják le, és a tévesztés nem hibázik – hihető lebegőpontos számokat ad a rossz mezőkből. Ezért a kezdetet **felfedezzük**:

1. A jelölt kezdeteket ebben a sorrendben próbáljuk: `hossz - 79` (a dash blokk minden dokumentált változatban az utolsó bájtig tart), 232, 244, és 232-től 260-ig 4-es lépésekkel.
2. Minden jelöltet mozgó autóról érkező csomagokon pontozunk (egy sebességkomponens 1 m/s felett): a Sled blokk sebességvektora és a dash blokk skalár `Speed` értéke ugyanaz a mennyiség két helyen, így a `| |sebesség| - Speed |` csak a helyes kezdetnél közel nulla.
3. A jelölt, amelynek a legkisebb a legrosszabb esetbeli eltérése, nyer, ha az eltérés legfeljebb **1 m/s**. Különben a felismerés tovább vár.

Amíg az autó áll, minden jelölt nullát olvas és egyezik, ami semmit nem bizonyít, ezért **a felismerés addig vár, amíg az autó nem mozog**: tegyél meg néhány métert, mielőtt kimenetet várnál. Várakozás közben legfeljebb 600 csomag tartható (a legutolsó 300-ra vágva). Miután az elrendezés ismert, a visszatartott csomagok is dekódolódnak, így az első kör eleje nem vész el. Az elrendezéstől eltérő hosszúságú csomagok, a 311 bájtnál rövidebb csomagok és a nem véges pozíciójú vagy sebességű csomagok figyelmen kívül maradnak a körfájloknál.

Hogy melyik Forza ez, az elrendezésből következik: egy Horizon-elrendezés `"game": "forza-horizon"`-t ad, egy Motorsport- vagy 331 bájtos elrendezés `"forza-motorsport"`-ot, minden más `"forza"`-t. A felismert elrendezés neve (`Horizon dash`, `Motorsport dash`, `331-byte dash`) `layout`-ként íródik.

## Rögzített csatornák {#channels-recorded}

Minden mező dekódolva van (`decode_full`) és átalakítva:

- a pedálok `throttle`, `brake`, `clutch`, `handbrake` 0..255-ről 0..1-re;
- `steer` -127..127-ről -1..1-re; a `drivingLine` és az `aiBrakeDifference` szintén 127-tel osztva;
- `tireTemp.FL` ... `.RR` Fahrenheitből Celsiusba;
- a `latAcc`, `longAcc`, `vertAcc` és `yawRate` az `accelX`, `accelZ`, `accelY` és `angVelY` másolatai a kanonikus neveken (autó-keret: x jobbra, y felfelé, z előre);
- a Sled sebesség, amely az autó saját keretében van (x jobbra, y felfelé, z előre – nem a világé), egyenesen a `latVel`, `vertVel` és `longVel` kanonikus neveken íródik, így a nézegető a driftszöget ebből olvassa, nem számolja a iránybólés az útvonalból.

A körfájl csatornái ezek mind, az egy körre jutó mezők kivételével:

| Csoport | Csatornák |
|---|---|
| Idő és hely | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Mozgás | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Vezető | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Kerekenként (`.FL .FR .RL .RR`) | `suspension` (0 kinyújtva .. 1 összenyomva), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizált: 1 felett a gumi elengedi az utat), `wheelSpeed` (rad/s), `rumble` (rezgősávon van), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Csak a Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

A `time` a játék aktuális körórája mínusz az értéke a kör első mintájánál; a `distance` a játék megtett távolsága mínusz az első értéke. A pozíciók a Forza világkoordinátái méterben, változatlanul (y felfelé; a világ balkezes).

Körönként egyszer, mintánként helyett, a `car` alatt: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Az FM2023 pályaazonosítója szintén egyszer kerül be, mint `lap.trackOrdinal`. Nem tárolódik mintánként: `isRaceOn` (1 minden kör minden képkockáján). A `timestampMs`, `raceTime`, `bestLap` és `lastLap` csatornaként megmarad.

A dokumentum többi része ugyanúgy töltődik ki, mint minden más rögzítőnél:

- `"track": null` – a Forza Horizon nem nevezi meg a pályát, a Forza Motorsport csak megszámozza;
- `"meta": {"slip": "peak", "discipline": "circuit"}` – a csúszási csatornák úgy normalizáltak, hogy 1 felett a gumi elengedi az utat;
- a `units` csak azokat a csatornákat sorolja fel, amelyek a fájlban megvannak (a kerekenkénti csatornákat az alapnevükön);
- az, ami nem véges szám, `null`-ként íródik, sosem `NaN`-ként.

Lásd [A heat3d-lap fájl](lap-format.md).

## Hogyan darabolódnak a körök {#how-laps-are-split}

`LapSplitter` (lásd [Kör- és szakaszdarabolás](lap-splitting.md)): egy kör akkor zárul, amikor a játék köridő-számlálója továbblép, és ideje ekkor a játék saját `lastLap` értéke (amit a játék mutat). Egy pont-pont verseny vagy egy körön belül véget érő munkamenet akkor zárul, amikor a játék kilép a versenyből (`isRaceOn` leesik), amikor a csomagok 2 másodpercig elmaradnak, vagy amikor a játék időbélyege visszaugrik; `run`-ként marad meg, ha legalább 400 m-t fedett le.

## Továbbítás az FH Companionnak {#relaying-to-fh-companion}

A játék a Data Outot csak egy címre küldi. A `--forward host:port` kapcsolóval a rögzítő **minden fogadott csomagot változatlanul továbbít**, mielőtt bármit dekódolna (akkor is, amikor még az elrendezés felismerésére vár), így a feedet olvasó másik alkalmazás tovább működik: állítsd a játékot 5300-ra, a másik alkalmazást 5301-re, és futtasd a `--forward 127.0.0.1:5301` kapcsolóval.

Az FH Companion külön alkalmazás, nem része a 3DHeatnek. Egy körkönyvtárat tart a `%LOCALAPPDATA%\FHCompanion\laps` alatt: egy mappát pályánként, egy körfájlt körönként, körülbelül ötméterenként mintavételezve, és minden körfájl mellett egy `<lap>.json.tele.gz` fájlt, amely a kör teljes Data Outját tartalmazza a játék sebességén. A 3DHeat mindkettőt olvassa:

- **A nézegető közvetlenül olvassa a `.tele.gz` fájlt**, ha a Versenyelemzés fülre ejted (a körfájl nélkül is, azzal együtt is). Leképezi a Forza saját mezőneveit (`PositionX`, `VelocityX`, `TireSlipRatio` + kerék, ...) a kanonikus csatornákra, az autó-helyi `VelocityX/Y/Z`-t `latVel`, `vertVel`, `longVel`-lé alakítja, a gumihőmérsékleteket Fahrenheitből átváltja, eldobja azokat a sorokat, amelyek az előzőt ismétlik a rögzítő órájának kivételével, és a csúszást `peak`-nek jelöli. Ha a körfájl is megvan, a kör autóját és köridejét onnan veszi. Ez az olvasó a nézegetőben van (`src/race/adapters.ts`, `readForzaTelemetry`), nem ebben a tárolóban.
- **A `laps` parancs** olvassa a körkönyvtárat, és egy pálya útvonalát és minden mintájának CSV-jét írja; lásd [Parancsreferencia](commands.md#laps).

## A ugyanezen feed más felhasználásai {#other-uses-of-the-same-feed}

- A `python -m heat3d_capture route` csak a pozíciókat rögzíti, néhány másodpercenként mentve vezetés közben; lásd [Parancsreferencia](commands.md#route).
- A szkennelő ablak „Racing telemetry (Forza)” (Versenytelemetria (Forza)) beállítása a feedet pontos kamerapózként használja a rekonstrukcióhoz; lásd [Kamera pózai és mérete](reconstruction-pose.md#telemetry-poses).

## Megjegyzések és korlátok {#notes-and-caveats}

- Hogy a Forza mihez normalizálja a csúszását, nincs dokumentálva. Az `1`-et a tapadás határának olvassuk, de a nézegető méri, hol kezd elfogyni az egyes autók tapadása.
- A Sled sebesség autó-helyi, ahogy a Forza Data Out dokumentációja mondja, és a rögzített körök igazolják (előre mutató összetevője hordozza a sebességet, oldalirányú összetevője közel nulla marad). Az elrendezés-felismerés csak a hosszát használja, ami bármely keretben ugyanaz.
- A pozíciók a játék világa: y felfelé, és balkezes. A `yaw`, `pitch` és `roll` irányait rögzített köröken ellenőrizték: a yaw egyenlő a haladási iránnyal, `atan2(dx, dz)`, a pozitív pitch az orr lefelé, és a pozitív roll leejti a jobb oldalt.
