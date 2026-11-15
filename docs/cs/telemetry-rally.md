---
title: "Rallye hry"
nav_order: 3
lang: "cs"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # nebo dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kód: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testy: `tests/test_rally.py`, na paketech sestavených z dokumentovaných rozložení. **Zatím
nespuštěno proti živým hrám.**

Všechny posílají UDP, které hra zapíná ze svých vlastních nastavovacích souborů. Nahrávač
poslouchá na všech rozhraních (`0.0.0.0`) na výchozím portu hry, pokud `--port` nedá jiný:
**20777** pro `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** pro `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Zapnutí {#switching-it-on}

Hra čte `Documents\My Games\WRC\telemetry\config.json`. Výchozí struktura `wrc`, paket
`session_update`, musí být zapnutá směrem k tomuto počítači:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<cesta ke config.json>"
```

`--configure` (funkce `configure_wrc`):

- přečte JSON, najde `udp.packets` a položku s `"structure": "wrc"` a `"packet": "session_update"`;
- pokud už je zapnutá na `127.0.0.1` nebo `localhost` na použitém portu, vypíše `already on`
  a nic nemění;
- jinak nastaví `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, a ponechá
  `frequencyHz` položky (nebo `-1`, pokud žádná není); když položka neexistuje, připojí se;
- zapíše původní text do `config.json.bak` vedle něj, pak zapíše nový soubor (odsazení 4 mezery).

Po změně souboru hru restartujte, pokud ji změna nepřevezme (neověřeno).

### Co posílá {#what-it-sends}

Výchozí struktura `wrc` má 237 bajtů, little-endian, bez záhlaví: světová poloha, rychlost
a zrychlení (X doleva, Y nahoru, Z dopředu), jednotkové vektory auta doleva / dopředu / nahoru,
pro každé kolo (zadní levé, zadní pravé, přední levé, přední pravé) výšku náboje a jeho
vertikální rychlost a dopřednou rychlost styku pneumatiky, teploty brzd, pedály po asistencích,
řízení (-1 doleva, +1 doprava), ruční brzdu, otáčky, rychlostní stupeň a hodiny etapy, vzdálenost
a délku. Paket kratší než 237 bajtů se ignoruje a jednou nahlásí.

| Kanál | Z čeho |
|---|---|
| `x`, `y`, `z` | světová poloha |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | světová rychlost promítnutá na dopředu, na minus doleva (takže kladné je vpravo), na nahoru |
| `longAcc`, `latAcc`, `vertAcc` | světové zrychlení promítnuté stejně |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | jak poslány |
| `gear` | `gear_index`; -1, když se rovná indexu zpátečky, 0, když se rovná indexu neutrálu |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | poloha náboje |
| `wheelSurfaceSpeed.*` | dopředná rychlost styku pneumatiky |
| `brakeTemp.*` | teplota brzdy |

Kontrola: je-li `speed` nad 10 a délka světové rychlosti se od ní liší o více než 20 %, nahrávač
jednou vypíše, že rozložení možná není výchozí struktura `wrc`.

Etapa je **dokončená**, když je délka etapy kladná a vzdálenost dosáhla délky minus 0,5 m. Hodiny
použité pro dělení a pro `time` jsou `stage_time`.

Zdroje: UDP Telemetry Guide v1.3 od EA; seznam kanálů, který hra zapisuje do
`readme/channels.json`; offsety, jak je dekódovali nobonobo/obs-codemasters-telemetry a
SpaceMonkey. Výchozí port hry není zdokumentován; nahrávač používá 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Zapnutí {#switching-it-on-1}

Upravte `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally a DiRT 4 také používají `hardware_settings_config.xml`; jejich přesná složka pro tyto dvě
nebyla zde ověřena) tak, aby element `udp` zněl:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` je to, co dá do paketu polohy, kola a délku etapy. Nahrávač tento soubor
neupravuje.

### Co posílá {#what-it-sends-1}

66 little-endian floatů (DiRT Rally: 64); pakety kratší než 64 floatů se ignorují a 64floatový
paket se doplní nulami. Používané indexy:

| Index | Pole | Kanál |
|---|---|---|
| 1 | čas kola (etapy) | dělicí hodiny a `time` |
| 2 | vzdálenost na kole | `stageDistance` |
| 4-6 | světová poloha | `x`, `y`, `z` |
| 7 | rychlost | `speed` |
| 8-10 | světová rychlost | `longVel` (na dopředu), `latVel` (na boční vektor) |
| 11-13 | boční vektor | |
| 14-16 | vektor dopředu | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | poloha odpružení ZL ZP PL PP | `suspensionM.*` |
| 25-28 | rychlost styku kol ZL ZP PL PP | `wheelSurfaceSpeed.*` |
| 29-33 | plyn, řízení, brzda, spojka, rychlostní stupeň | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 a více znamená zpátečku, zapíše se jako -1) |
| 34, 35 | boční, podélné g | `latAcc`, `longAcc` (krát 9,80665) |
| 37 | otáčky / 10 | `rpm` (krát 10) |
| 51-54 | teploty brzd | `brakeTemp.*` |
| 59, 60, 61, 62 | dokončená kola, celkem kol, délka trati, čas posledního kola | dělení |

Kanál **ruční brzdy neexistuje**. Smysl bočního vektoru je dokumentován oběma směry, takže na
znaménko `latVel` se nelze spolehnout (prohlížeč čte velikost driftového úhlu).

Etapa je **dokončená**, když počet dokončených kol vzroste nad jeho hodnotu na začátku etapy
(každé kolo rallycrossu), nebo, u jednokolové akce, když vzdálenost na kole dosáhne 99,9 %
délky trati. Čas etapy je čas posledního kola hry, je-li kladný. Kontrola: rychlost proti
rychlosti jako u EA WRC, se zprávou „is extradata set to 3?“.

Zdroje: dokument Codemasters k UDP pro DiRT 4; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Zapnutí {#switching-it-on-2}

V `RichardBurnsRally.ini`, sekce `[NGP]`: `udpTelemetry=1` a koncový bod (127.0.0.1, port 6776,
pokud nepředáte jiný přes `--port`). Nahrávač tento soubor neupravuje.

### Co posílá {#what-it-sends-2}

664 bajtů (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): hodiny etapy a vzdálenost do
cíle, pedály, řízení, rychlostní stupeň, světová poloha, postoj, vlastní rychlosti auta (podélná
dopředu, boční, svislá), zrychlení, otáčky, a čtyři 128bajtové bloky kol (LF, RF, LB, RB) s
průhybem pružiny a silou pružiny. Žádné rychlosti kol.

| Kanál | Z čeho |
|---|---|
| `x`, `y`, `z` | poloha, osy jak poslány, pak přeuspořádány (níže) |
| `longVel`, `latVel`, `vertVel` | podélná, boční, svislá |
| `longAcc`, `latAcc` | zrychlení x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | jak poslány |
| `gear` | `gear - 1` (0 zpátečka, 1 neutrál, 2 první) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | průhyb pružiny |
| `wheelLoad.*` | síla pružiny |
| `speed` | **počítá se z poloh** přes ±2 vzorky, ne z paketu |

Osy polohy RBR, jednotky postojů a jednotka rychlosti nejsou zdokumentovány, takže při zápisu
etapy: osa, podél které etapa nejméně mění, se vezme jako nahoru a prohodí se do `y`
(`orient_up`, potřebuje alespoň 10 vzorků), a rychlost se přepočítá z poloh
(`speed_from_positions`). Postoj se dekóduje, ale nezapisuje, takže soubory RBR nemají `yaw`.

Etapa je **dokončená**, když běží závodní hodiny a vzdálenost do cíle dosáhla nuly. Hodiny jsou
`race_time`.

Zdroje: `rbr.telemetry.data.TelemetryData.h` od NGP, přes mika-n/RBRUDPTelemetryLogger a
groybe/rbr-udp-telem.

## Etapy {#stages}

Všech pět používá `StageSplitter` na etapových hodinách hry: etapa se otevře, když hodiny
začnou, uzavře se jako dokončená, když hra řekne, že auto dojelo, a hodiny, které jdou zpět
(restart, nebo další etapa), otevřenou etapu opustí - zachová se jako soubor `_partial`, pokud
má více než 10 vzorků a alespoň 300 m. Dokončené etapy kratší než 300 m se nezapisují. Podrobnosti:
[Jak se rozdělují kola a etapy](lap-splitting.md).

## Soubor kola {#the-lap-file}

`game` je `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` nebo `richard-burns-rally`.
`meta` je `{"discipline": "rally", "slip": null}`, plus `"surface": "<hodnota>"`, když byl zadán
`--surface`. `slip` je null, protože žádná z těchto her neposílá skluz pneumatik. Příspěvek
styku každého kola (EA WRC, DiRT) je místo něj v souboru; prohlížeč z něj a z os auta odvodí
skluz a driftový úhel; viz [Skluz, driftový úhel a odvozené kanály](slip-and-drift.md). Kanály
`suspension.*` (0..1 použitého zdvihu) se přidají z `suspensionM.*`.

Když není zadán `--surface`, soubor nenese žádný povrch, a to záměrně: výchozí hodnota zapsaná
zde by přepsala odvození prohlížeče. Prohlížeč pak vezme povrch z názvu etapy nebo rallye
(asfaltové rallye, zimní, a Monte jako smíšené), jinak z toho, jak se na něm jezdilo (tvrdé
zatáčení při malých driftových úhlech je asfalt), a volný, když nic neříká - což je to, čím
rallye etapa nejčastěji je. Dejte `--surface`, když to víte lépe.
