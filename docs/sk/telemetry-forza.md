---
title: "Forza Horizon a Forza Motorsport"
nav_order: 1
lang: "sk"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon a Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # hra -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # a FH Companion ďalej funguje
```

Kód: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(zisťovanie rozloženia),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(každý kanál, súbory kôl, preposielanie).

## Zapnutie v hre {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300`
(alebo čokoľvek, čo zadáte ako `--port`). Forza Motorsport tiež ponúka formát
paketu: musí byť **Dash**, nie Sled. Sled neobsahuje žiadnu polohu a nahrávač ho
odmietne.

Nahrávač sa viaže na `127.0.0.1`, takže hra musí bežať na tom istom PC.

## Čo hra posiela a ako sa zisťuje rozloženie {#what-the-game-sends-and-how-the-layout-is-found}

Data Out je jeden UDP paket na každý krok simulácie (asi 60 za sekundu), plochá
štruktúra C little-endian v týchto veľkostiach:

| Dĺžka | Variant |
|---|---|
| 232 bajtov | Motorsport „Sled“: bez polohy. Odmietnutý správou, ktorá hovorí prepnúť na Dash. |
| 311 bajtov | Motorsport „Dash“: blok Sled plus 79-bajtový blok dash |
| 324 bajtov | Horizon „Dash“: to isté s výplňou medzi oboma blokmi |
| 331 bajtov | Forza Motorsport (2023): Dash plus 20 bajtov opotrebenia pneumatík a id trate |

Blok Sled (offsety 0-231) je stabilný. Kde sa v Horizon variante začína blok
dash, je v publikovaných zdrojoch opísané nekonzistentne, a zlý odhad nezlyhá –
dá vierohodné čísla z nesprávnych polí. Preto sa začiatok **zisťuje**:

1. Kandidátske začiatky sa skúšajú v tomto poradí: `length - 79` (blok dash
   beží do poslednému bajtu v každom zdokumentovanom variante), 232, 244 a
   232 až 260 po krokoch 4.
2. Každý kandidát sa ohodnotí na paketoch od jazdiaceho auta (zložka rýchlosti
   väčšia ako 1 m/s): vektor rýchlosti bloku Sled a skalárna `Speed` bloku dash
   sú tá istá veličina na dvoch miestach, takže `| |velocity| - Speed |` je
   blízko nuly len pri správnom začiatku.
3. Vyhráva kandidát s najmenšou najhoršou nezhodou, ak je táto nezhoda
   najviac **1 m/s**. Inak zisťovanie ďalej čaká.

Kým auto stojí, každý kandidát číta nuly a všetci sa zhodujú, čo nič nedokazuje,
preto **zisťovanie čaká, kým sa auto pohne**: pred očakávaním výstupu prejdite
niekoľko metrov. Počas čakania sa drží až 600 paketov (orezaných na posledných
300). Keď je rozloženie známe, dekódujú sa aj držané pakety, takže sa nestratí
začiatok prvého kola. Pakety inej dĺžky ako zistené rozloženie, pakety kratšie
ako 311 bajtov a pakety s nekonečnou polohou alebo rýchlosťou sa pre súbory kôl
ignorujú.

Ktorá Forza to je, vyplýva z rozloženia: rozloženie Horizon dáva
`"game": "forza-horizon"`, rozloženie Motorsport alebo 331-bajtové dáva
`"forza-motorsport"`, ostatné `"forza"`. Názov zisteného rozloženia (`Horizon dash`,
`Motorsport dash`, `331-byte dash`) sa zapisuje ako `layout`.

## Nahrávané kanály {#channels-recorded}

Každé pole paketu sa dekóduje (`decode_full`) a prevedie:

- pedále `throttle`, `brake`, `clutch`, `handbrake` z 0..255 na 0..1;
- `steer` z -127..127 na -1..1; `drivingLine` a `aiBrakeDifference` podobne delené 127;
- `tireTemp.FL` ... `.RR` z Fahrenheita na Celzia;
- `latAcc`, `longAcc`, `vertAcc` a `yawRate` sú kópie `accelX`, `accelZ`, `accelY`
  a `angVelY` pod kanonickými menami (vnútorný systém auta: x doprava, y hore, z dopredu);
- rýchlosť bloku Sled je vo vnútornom systéme auta (x doprava, y hore, z dopredu –
  nie sveta) a zapisuje sa priamo pod kanonickými menami `latVel`, `vertVel` a
  `longVel`, takže prehliadač číta driftový uhol priamo, namiesto aby ho odhadoval
  zo smeru a dráhy.

Kanály súboru kola sú všetky tieto okrem polí na kolo:

| Skupina | Kanály |
|---|---|
| Čas a miesto | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Pohyb | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Vodič | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Pre každé koleso (`.FL .FR .RL .RR`) | `suspension` (0 natiahnuté .. 1 stlačené), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizované: nad 1 pneumatika stráca prilipnutie), `wheelSpeed` (rad/s), `rumble` (na vibračnom páse), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Len Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` je časovač aktuálneho kola hry mínus jeho hodnota v prvej vzorke kola;
`distance` je prejdená vzdialenosť hry mínus jej prvá hodnota. Polohy sú
súradnice sveta Forzy v metroch, nezmenené (y je hore; svet je ľavoruký).

Raz na kolo, nie pre každú vzorku, pod `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Id trate FM2023 sa zapíše tiež
raz, ako `lap.trackOrdinal`. Neuchováva sa pre každú vzorku: `isRaceOn` (1 v každom
snímku kola). `timestampMs`, `raceTime`, `bestLap` a `lastLap` sa uchovávajú ako kanály.

Zvyšok dokumentu sa vypĺňa ako u každého iného nahrávača:

- `"track": null` – Forza Horizon nepomenúva trať a Forza Motorsport ju len čísluje;
- `"meta": {"slip": "peak", "discipline": "circuit"}` – kanály prešmyku sú
  normalizované tak, že nad 1 pneumatika stráca prilipnutie;
- `units` uvádza len kanály, ktoré súbor má (kanály pre jednotlivé kolesá podľa ich základného názvu);
- hodnota, ktorá nie je konečné číslo, sa zapíše ako `null`, nikdy ako `NaN`.

Pozrite [Súbor heat3d-lap](lap-format.md).

## Ako sa delia kolá {#how-laps-are-split}

`LapSplitter` (pozrite [Delenie kôl a etáp](lap-splitting.md)): kolo sa uzavrie, keď
sa počítadlo kôl hry posunie, a jeho čas je vtedy vlastný `lastLap` hry (to, čo
hra zobrazuje). Jazda z bodu A do bodu B alebo relácia, ktorá skončí uprostred
kola, sa uzavrie, keď hra opustí pretek (klesne `isRaceOn`), keď pakety
prestanú na 2 sekundy, alebo keď časová pečiatka hry skočí späť; ponechá sa ako
`run`, ak pokryla aspoň 400 m.

## Preposielanie do FH Companion {#relaying-to-fh-companion}

Hra posiela Data Out len na jednu adresu. S `--forward host:port` nahrávač
prepošle **každý prijatý paket nezmenený**, ešte pred dekódovaním čohokoľvek
(aj kým ešte čaká na zistenie rozloženia), takže iná aplikácia čítajúca prúd
funguje ďalej: nastavte hru na 5300, druhú aplikáciu na 5301 a spustite s
`--forward 127.0.0.1:5301`.

FH Companion je samostatná aplikácia, nie súčasť 3DHeat. Drží knižnicu kôl v
`%LOCALAPPDATA%\FHCompanion\laps`: priečinok na každú trať, jeden súbor kola na
kolo vzorkovaný približne každých päť metrov, a vedľa každého súboru kola
`<lap>.json.tele.gz`, celé Data Out kola v rýchlosti hry. 3DHeat číta obe:

- **Prehliadač číta `.tele.gz` priamo**, keď ho pretiahnete (so súborom kola
  alebo bez neho) na kartu Analýza pretekov. Mapuje vlastné názvy polí Forzy
  (`PositionX`, `VelocityX`, `TireSlipRatio` + koleso, ...) na kanonické kanály,
  mení vnútorné `VelocityX/Y/Z` auta na `latVel`, `vertVel`, `longVel`, prevádza
  teploty pneumatík z Fahrenheita, zahodí riadky, ktoré opakujú predchádzajúci
  okrem hodinovej pečiatky nahrávača, a označí prešmyk ako `peak`. Ak je
  pridaný aj súbor kola, kolo z neho prevezme auto a čas kola. Tento čítač je v
  prehliadači (`src/race/adapters.ts`, `readForzaTelemetry`), nie v tomto repozitári.
- **Príkaz `laps`** číta knižnicu kôl a zapíše trasu trate a CSV každej vzorky;
  pozrite [Prehľad príkazov](commands.md#laps).

## Ďalšie použitia rovnakého prúdu {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` zaznamenáva len polohy, ukladané každých pár
  sekúnd pri jazde; pozrite [Prehľad príkazov](commands.md#route).
- Voľba skenovania „Racing telemetry (Forza)“ používa prúd ako presné polohy
  kamery pre rekonštrukciu; pozrite [Poloha kamery a mierka](reconstruction-pose.md#telemetry-poses).

## Poznámky a upozornenia {#notes-and-caveats}

- Voči čomu Forza normalizuje svoj prešmyk, nie je zdokumentované. `1` sa číta
  ako hranica prilipnutia, ale prehliadač meria, kde sa prilipnutie každého auta
  skutočne stráca.
- Rýchlosť bloku Sled je vo vnútornom systéme auta, ako to hovorí dokumentácia Data
  Out od Forzy a potvrdzujú nahraté kolá (jej zložka dopredu nesie rýchlosť, bočná
  zostáva blízko nuly). Zisťovanie rozloženia používa len jeho dĺžku, ktorá je v
  každom rámci rovnaká.
- Polohy sú svet hry, Y hore a ľavoruký. Smery `yaw`, `pitch` a `roll` boli
  overené na nahratých kolách: yaw sa rovná smeru jazdy `atan2(dx, dz)`, kladný
  pitch znamená nos dole a kladný roll znamená pravú stranu dole.
