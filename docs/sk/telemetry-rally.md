---
title: "Rallye hry"
nav_order: 3
lang: "sk"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # alebo dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kód: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testy: `tests/test_rally.py`, na paketoch zostavených podľa zdokumentovaných rozložení. **Zatiaľ
nespustené proti živým hrám.**

Všetky posielajú UDP, ktoré hra zapína zo svojich vlastných nastavení. Nahrávač počúva na všetkých
rozhraniach (`0.0.0.0`) na predvolenom porte hry, pokiaľ `--port` nedá iný: **20777** pre `wrc`,
`dirtrally2`, `dirtrally`, `dirt4`; **6776** pre `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Zapnutie {#switching-it-on}

Hra číta `Documents\My Games\WRC\telemetry\config.json`. Správa `session_update` predvolenej
štruktúry `wrc` musí byť zapnutá smerom k tomuto počítaču:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funkcia `configure_wrc`):

- prečíta JSON, nájde `udp.packets` a položku s `"structure": "wrc"` a `"packet": "session_update"`;
- ak je už zapnutá na `127.0.0.1` alebo `localhost` na používanom porte, vypíše `already on` a nič nemení;
- inak nastaví `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` a ponechá `frequencyHz`
  položky (alebo `-1`, ak žiadna nie je); ak takáto položka neexistuje, pridá ju;
- pôvodný text zapíše do `config.json.bak` vedľa neho, potom zapíše nový súbor (odsadenie 4 medzery).

Ak hra zmenu súboru nepreberie, reštartujte ju (neoverené).

### Čo posiela {#what-it-sends}

Predvolená štruktúra `wrc` má 237 bajtov, little-endian, bez hlavičky: svetová poloha,
rýchlosť a zrýchlenie (X doľava, Y hore, Z dopredu), jednotkové vektory auta doľava / dopredu /
hore, pre každé koleso (zadné ľavé, zadné pravé, predné ľavé, predné pravé) výška náboja a
jeho vertikálna rýchlosť a dopredná rýchlosť kontaktnej plochy, teploty bŕzd, pedále po
asistenciách, riadenie (-1 vľavo, +1 vpravo), ručná brzda, rpm, rýchlostný stupeň a hodiny
etapy, vzdialenosť a dĺžka. Paket kratší ako 237 bajtov sa ignoruje a raz sa nahlási.

| Kanál | Z čoho |
|---|---|
| `x`, `y`, `z` | svetová poloha |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | svetová rýchlosť premietnutá na dopredu, na mínus doľava (takže kladné je doprava), na hore |
| `longAcc`, `latAcc`, `vertAcc` | svetové zrýchlenie premietnuté rovnako |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | tak, ako sa posielajú |
| `gear` | `gear_index`; -1, keď sa rovná indexu spiatočky, 0, keď sa rovná indexu neutrálu |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | poloha náboja |
| `wheelSurfaceSpeed.*` | dopredná rýchlosť kontaktnej plochy |
| `brakeTemp.*` | teplota brzdy |

Kontrola: ak je `speed` väčšie ako 10 a dĺžka svetového rýchlostného vektora sa od nej líši o viac
ako 20 %, nahrávač raz vypíše, že rozloženie možno nie je predvolená štruktúra `wrc`.

Etapa je **dokončená**, keď je dĺžka etapy kladná a vzdialenosť dosiahla dĺžku mínus 0,5 m.
Hodiny na delenie a na `time` sú `stage_time`.

Zdroje: UDP Telemetry Guide v1.3 od EA; zoznam kanálov, ktorý hra zapisuje do
`readme/channels.json`; posuny ako ich dekódovali nobonobo/obs-codemasters-telemetry a
SpaceMonkey. Predvolený port hry nie je zdokumentovaný; nahrávač používa 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Zapnutie {#switching-it-on-1}

Upravte `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally a DiRT 4 tiež používajú `hardware_settings_config.xml`; ich presný priečinok pre tieto dve
nebol overený), tak aby prvok `udp` znel:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` zaručí, že paket obsahuje polohy, kolesá a dĺžku etapy. Nahrávač tento súbor
neupravuje.

### Čo posiela {#what-it-sends-1}

66 little-endian desatinných čísel (DiRT Rally: 64); pakety kratšie ako 64 čísel sa ignorujú
a 64-číselný paket sa doplní nulami. Používané indexy:

| Index | Pole | Kanál |
|---|---|---|
| 1 | čas kola (etapy) | deliace hodiny a `time` |
| 2 | vzdialenosť po kole | `stageDistance` |
| 4-6 | svetová poloha | `x`, `y`, `z` |
| 7 | rýchlosť | `speed` |
| 8-10 | svetová rýchlosť | `longVel` (na dopredu), `latVel` (na vektor strany) |
| 11-13 | vektor strany | |
| 14-16 | vektor dopredu | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | poloha zavesenia RL RR FL FR | `suspensionM.*` |
| 25-28 | rýchlosť kontaktnej plochy kolies RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | plyn, riadenie, brzda, spojka, rýchlostný stupeň | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 alebo viac znamená spiatočku, zapísané ako -1) |
| 34, 35 | bočné, pozdĺžne g | `latAcc`, `longAcc` (krát 9,80665) |
| 37 | rpm / 10 | `rpm` (krát 10) |
| 51-54 | teploty bŕzd | `brakeTemp.*` |
| 59, 60, 61, 62 | dokončené kolá, celkový počet kôl, dĺžka trate, čas posledného kola | delenie |

Nie je tu **žiadny kanál ručnej brzdy**. Zmysel vektora strany je zdokumentovaný v oboch smeroch,
takže sa na znamienko `latVel` nedá spoliehať (prehliadač číta veľkosť driftového uhla).

Etapa je **dokončená**, keď počet dokončených kôl vzrastie nad hodnotu na začiatku etapy (pri
rallycrosse každé takéto kolo), alebo pri jednokolovej udalosti, keď vzdialenosť po kole dosiahne
99,9 % dĺžky trate. Čas etapy je čas posledného kola hry, ak je kladný. Kontrola: rýchlosť voči
rýchlosti ako pri EA WRC, so správou „is extradata set to 3?“.

Zdroje: dokument Codemasters UDP k DiRT 4; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Zapnutie {#switching-it-on-2}

V `RichardBurnsRally.ini`, sekcia `[NGP]`: `udpTelemetry=1` a koncový bod (127.0.0.1, port
6776, pokiaľ nezadáte iný `--port`). Nahrávač tento súbor neupravuje.

### Čo posiela {#what-it-sends-2}

664 bajtov (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): hodiny etapy a vzdialenosť
do cieľa, pedále, riadenie, rýchlostný stupeň, svetová poloha, postoj, vlastné rýchlosti auta
(zadok dopredu, bok do strán, zdvih), zrýchlenia, rpm a štyri 128-bajtové bloky kolies (LF, RF,
LB, RB) s vychýlením pružiny a silou pružiny. Žiadne rýchlosti kolies.

| Kanál | Z čoho |
|---|---|
| `x`, `y`, `z` | poloha, osi tak, ako sa posielajú, potom preusporiadané (nižšie) |
| `longVel`, `latVel`, `vertVel` | zadok, bok, zdvih |
| `longAcc`, `latAcc` | zrýchlenie x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | tak, ako sa posielajú |
| `gear` | `gear - 1` (0 spiatočka, 1 neutrál, 2 prvý stupeň) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | vychýlenie pružiny |
| `wheelLoad.*` | sila pružiny |
| `speed` | **vypočítaná z polôh** cez ±2 vzorky, nie zo série paketu |

Osi polohy RBR, jednotky uhlov a jednotka rýchlosti nie sú zdokumentované, takže pri zápise etapy
sa os, v ktorej sa etapa najmenej mení, považuje za os hore a vymení sa do `y` (`orient_up`,
potrebuje aspoň 10 vzoriek) a rýchlosť sa znovu vypočíta z polôh (`speed_from_positions`).
Postoj sa dekóduje, ale nezapisuje, takže súbory RBR nemajú `yaw`.

Etapa je **dokončená**, keď beží čas pretekov a vzdialenosť do cieľa dosiahla nulu. Hodiny sú
`race_time`.

Zdroje: `rbr.telemetry.data.TelemetryData.h` od NGP cez mika-n/RBRUDPTelemetryLogger a
groybe/rbr-udp-telem.

## Etapy {#stages}

Všetkých päť používa `StageSplitter` na hodinách etapy hry: etapa sa otvorí, keď hodiny začnú,
dokončená sa uzavrie, keď hra hovorí, že auto dorazilo, a hodiny, ktoré sa vrátia späť (reštart
alebo ďalšia etapa), otvorenú etapu opustia – zachová sa ako súbor `_partial`, ak má viac ako 10
vzoriek a aspoň 300 m. Dokončené etapy kratšie ako 300 m sa nezapíšu. Podrobnosti:
[Delenie kôl a etáp](lap-splitting.md).

## Súbor kola {#the-lap-file}

`game` je `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` alebo `richard-burns-rally`.
`meta` je `{"discipline": "rally", "slip": null}`, plus `"surface": "<hodnota>"`, keď bol zadaný
`--surface`. `slip` je null, lebo žiadna z týchto hier neposiela prešmyk pneumatík. Namiesto neho
je v súbore rýchlosť kontaktnej plochy každého kolesa (EA WRC, DiRT); prehliadač z nej a z osí
auta odvodzuje prešmyk a driftový uhol; pozrite [Prešmyk, drift a odvodené kanály](slip-and-drift.md).
Kanály `suspension.*` (0..1 použitého zdvihu) sa pridávajú z `suspensionM.*`.

Keď sa nezadá `--surface`, súbor nenesie žiadny povrch, zámerne: predvolená hodnota zapísaná tu
by prepísala odvodenie prehliadača. Prehliadač potom berie povrch z názvu etapy alebo udalosti
(asfaltové rally, zimné, Monte ako zmiešané), inak z toho, ako sa na ňom jazdilo (tvrdé zatáčanie
pri malých driftových uhloch je asfalt), a keď nič nerozhoduje, sypký – čo je najčastejší prípad
rally etapy. Zadajte `--surface`, keď viete lepšie.
