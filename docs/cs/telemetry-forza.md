---
title: "Forza Horizon a Forza Motorsport"
nav_order: 1
lang: "cs"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon a Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # hra -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # a FH Companion dál funguje
```

Kód: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(zjišťování rozložení),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(každý kanál, soubory kol, přeposílání).

## Zapnutí ve hře {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (nebo cokoli
předáte jako `--port`). Forza Motorsport také nabízí formát paketu: musí být **Dash**, ne
Sled. Sled nenese vůbec žádnou polohu a nahrávač ho odmítne.

Nahrávač se váže na `127.0.0.1`, takže hra musí běžet na stejném počítači.

## Co hra posílá a jak se najde rozložení {#what-the-game-sends-and-how-the-layout-is-found}

Data Out je jeden paket UDP na každý tik simulace (asi 60 za sekundu), plochá C struktura
little-endian v těchto velikostech:

| Délka | Varianta |
|---|---|
| 232 bajtů | Motorsport „Sled“: bez polohy. Odmítnuto se zprávou, ať přepnete na Dash. |
| 311 bajtů | Motorsport „Dash“: blok Sled plus 79bajtový blok dash |
| 324 bajtů | Horizon „Dash“: totéž s výplní mezi oběma bloky |
| 331 bajtů | Forza Motorsport (2023): Dash plus 20 bajtů opotřebení pneumatik a id trati |

Blok Sled (offsety 0-231) je stabilní. Kde blok dash ve variantě Horizon začíná, je v
publikovaných zdrojích popsáno nejednoznačně, a špatný odhad neselže - jen dá věrohodné
hodnoty z špatných polí. Začátek se proto **zjistí**:

1. Kandidátské začátky se zkoušejí v pořadí: `délka - 79` (blok dash končí na posledním
   bajtu v každé dokumentované variantě), 232, 244 a 232 až 260 po čtyřech.
2. Každý kandidát se ohodnotí podle paketů z jedoucího auta (složka rychlosti větší než
   1 m/s): vektor rychlosti bloku Sled a skalár `Speed` bloku dash jsou tatáž veličina na
   dvou místech, takže `| |rychlost| - Speed |` je blízko nule jen pro správný začátek.
3. Vyhrává kandidát s nejmenším nejhorším nesouhlasem, pokud je ten nesouhlas nejvýš
   **1 m/s**. Jinak zjišťování dál čeká.

Zatímco auto stojí, každý kandidát čte nuly a všichni souhlasí, což nic nedokazuje, takže
**zjišťování čeká, dokud se auto nehne**: před očekáváním výstupu ujeďte pár metrů. Během
čekání se drží až 600 paketů (oříznuto na posledních 300). Jakmile je rozložení známé,
podrží se pakety také dekódují, takže se neztratí začátek prvního kola. Pakety jiné délky
než zjištěné rozložení, pakety kratší než 311 bajtů a pakety s nekonečnou nebo nečíselnou
polohou nebo rychlostí se pro soubory kol ignorují.

Která Forza to je, plyne z rozložení: rozložení Horizon dává `"game": "forza-horizon"`,
rozložení Motorsport nebo 331bajtové dává `"forza-motorsport"`, cokoli jiného `"forza"`.
Zjištěný název rozložení (`Horizon dash`, `Motorsport dash`, `331-byte dash`) se zapíše jako
`layout`.

## Zaznamenané kanály {#channels-recorded}

Každé pole paketu se dekóduje (`decode_full`) a převede:

- pedály `throttle`, `brake`, `clutch`, `handbrake` z 0..255 na 0..1;
- `steer` z -127..127 na -1..1; `drivingLine` a `aiBrakeDifference` také děleno 127;
- `tireTemp.FL` ... `.RR` z Fahrenheitů na Celsia;
- `latAcc`, `longAcc`, `vertAcc` a `yawRate` jsou kopie `accelX`, `accelZ`, `accelY` a `angVelY`
  pod kanonickými názvy (rám auta: x vpravo, y nahoru, z dopředu);
- rychlost ze Sled, která je v rámu auta (x vpravo, y nahoru, z dopředu - ne světový), se
  zapisuje přímo pod kanonickými názvy `latVel`, `vertVel` a `longVel`, takže ji prohlížeč
  čte pro driftový úhel místo odhadu ze směru a dráhy.

Kanály souboru kola jsou všechny tyto kromě polí na kolo:

| Skupina | Kanály |
|---|---|
| Čas a místo | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Pohyb | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Řidič | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Na kolo (`.FL .FR .RL .RR`) | `suspension` (0 natažené .. 1 stlačené), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizované: nad 1 pneumatika ztrácí přilnavost), `wheelSpeed` (rad/s), `rumble` (na vibračním pásu), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Jen Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` je časomíra aktuálního kola hry minus její hodnota v prvním vzorku kola; `distance` je
ujetá vzdálenost hry minus její první hodnota. Polohy jsou světové souřadnice Forzy v metrech,
beze změny (y je nahoru; svět je levotočivý).

Jednou na kolo, nikoli na vzorek, v bloku `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Id trati FM2023 se zapíše také jednou, jako
`lap.trackOrdinal`. Neuchovává se na vzorek `isRaceOn` (je 1 v každém snímku kola). `timestampMs`,
`raceTime`, `bestLap` a `lastLap` se uchovávají jako kanály.

Zbytek dokumentu se vyplní jako u ostatních nahrávačů:

- `"track": null` - Forza Horizon netrať nepojmenovává a Forza Motorsport ji jen očísluje;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kanály skluzu jsou normalizované tak,
  že nad 1 pneumatika ztrácí přilnavost;
- `units` vypisuje jen kanály, které soubor má (kanály na kolo podle základního názvu);
- hodnota, která není konečné číslo, se zapíše jako `null`, nikdy jako `NaN`.

Viz [Soubor heat3d-lap](lap-format.md).

## Jak se kola dělí {#how-laps-are-split}

`LapSplitter` (viz [Jak se rozdělují kola a etapy](lap-splitting.md)): kolo se uzavře, když se
posune počítadlo kol hry, a jeho čas je pak vlastní `lastLap` hry (to, co hra ukazuje).
Závod z bodu A do bodu B nebo relace, která skončí uprostřed kola, se uzavře, když hra opustí
závod (`isRaceOn` klesne), když pakety přestanou na 2 sekundy, nebo když časové razítko hry
skočí zpět; zachová se jako `run`, pokud pokryl alespoň 400 m.

## Přeposílání do FH Companion {#relaying-to-fh-companion}

Hra posílá Data Out jen na jednu adresu. S `--forward host:port` nahrávač předá **každý přijatý
paket nezměněný**, ještě před dekódováním čehokoli (i zatímco čeká na zjištění rozložení),
takže jiná aplikace čtoucí feed dál funguje: nastavte hru na 5300, druhou aplikaci na 5301 a
spusťte s `--forward 127.0.0.1:5301`.

FH Companion je samostatná aplikace, ne část 3DHeat. Drží knihovnu kol v
`%LOCALAPPDATA%\FHCompanion\laps`: složku pro každou trať, jeden soubor kola na kolo vzorkovaný
zhruba každých pět metrů, a vedle každého souboru kola `<kolo>.json.tele.gz`, celý Data Out
kola v rychlosti hry. 3DHeat čte obojí:

- **Prohlížeč čte `.tele.gz` přímo**, když ho pustíte (se souborem kola, nebo bez něj) na kartu
  Analýza závodu. Mapuje názvy polí Forzy (`PositionX`, `VelocityX`, `TireSlipRatio` + kolo, ...)
  na kanonické kanály, otáčí lokální `VelocityX/Y/Z` na `latVel`, `vertVel`, `longVel`, převádí
  teploty pneumatik z Fahrenheitů, zahazuje řádky, které opakují předchozí až na hodiny
  nahrávače, a označuje skluz jako `peak`. Když je k dispozici i soubor kola, kolo si vezme auto
  a čas kola odtud. Tato čtečka je v prohlížeči (`src/race/adapters.ts`, `readForzaTelemetry`),
  ne v tomto repozitáři.
- **Příkaz `laps`** čte knihovnu kol a zapíše trasu tratě a CSV každého vzorku; viz
  [Přehled příkazů](commands.md#laps).

## Jiná použití stejného feedu {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` zaznamená jen polohy, ukládané každé dvě sekundy během jízdy;
  viz [Přehled příkazů](commands.md#route).
- Volba okna skenování „Racing telemetry (Forza)“ používá feed jako přesné pózy kamery pro
  rekonstrukci; viz [Poloha kamery a měřítko](reconstruction-pose.md#telemetry-poses).

## Poznámky a upozornění {#notes-and-caveats}

- Vůči čemu Forza normalizuje skluz, není zdokumentováno. `1` se čte jako hrana přilnavosti,
  ale prohlížeč měří, kde přilnavost každého auta skutečně mizí.
- Rychlost ze Sled je lokální vůči autu, jak říká dokumentace Data Out od Forzy a potvrzují
  nahraná kola (její podélná složka nese rychlost, boční zůstává blízko nule). Zjišťování
  rozložení používá jen její délku, která je v každém rámci stejná.
- Polohy jsou světové souřadnice hry, y nahoru a levotočivé. Smysly `yaw`, `pitch` a `roll` byly
  ověřeny na nahraných kolech: yaw se rovná směru jízdy `atan2(dx, dz)`, kladný pitch je nos
  dolů a kladný roll shodí pravou stranu.
