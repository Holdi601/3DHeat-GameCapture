---
title: "Ralijátékok"
nav_order: 3
lang: "hu"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # or dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kód: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Tesztek: `tests/test_rally.py`, a dokumentált elrendezésekből épített csomagokon. **Még nem futtatták az élő játékokon.**

Mindegyik UDP-t küld, amelyet a játék a saját beállítási fájljaiból kapcsol be. A rögzítő minden interfészen hallgat (`0.0.0.0`) a játék alapértelmezett portján, hacsak a `--port` másikat nem ad meg: **20777** a `wrc`, `dirtrally2`, `dirtrally`, `dirt4` esetén; **6776** az `rbr` esetén.

## EA SPORTS WRC {#ea-sports-wrc}

### Bekapcsolás {#switching-it-on}

A játék a `Documents\My Games\WRC\telemetry\config.json` fájlt olvassa. Az alapértelmezett `wrc` struktúra `session_update` csomagját erre a gépre kell engedélyezni:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

A `--configure` (a `configure_wrc` függvény):

- beolvassa a JSON-t, megkeresi a `udp.packets`-et és a `"structure": "wrc"` és `"packet": "session_update"` bejegyzést;
- ha már engedélyezve van a `127.0.0.1` vagy `localhost` címre a használt porton, kiírja: `already on`, és nem változtat semmit;
- különben beállítja a `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` értékeket, és megtartja a bejegyzés `frequencyHz` értékét (vagy `-1`-et, ha nincs); ha nincs ilyen bejegyzés, hozzáfűz egyet;
- az eredeti szöveget `config.json.bak` néven elmenti mellé, majd a új fájlt írja (4 szóközös behúzással).

Indítsd újra a játékot a fájl módosítása után, ha nem veszi észre a változtatást (nem ellenőrizték).

### Mit küld {#what-it-sends}

Az alapértelmezett `wrc` struktúra 237 bájt, little-endian, fejléc nélkül: világpozíció, sebesség és gyorsulás (X balra, Y felfelé, Z előre), az autó bal / előre / felfelé egységvektorai, kerekenként (hátsó bal, hátsó jobb, első bal, első jobb) a kerék magassága és függőleges sebessége és az érintkezési folt előre irányuló sebessége, fékhőmérsékletek, a segédrendszerek utáni pedálok, kormányzás (-1 balra, +1 jobbra), kézifék, fordulatszám, fokozat, valamint a szakaszóra, a megtett távolság és a szakasz hossza. A 237 bájtnál rövidebb csomagot figyelmen kívül hagyja, és egyszer jelzi.

| Csatorna | Forrás |
|---|---|
| `x`, `y`, `z` | világpozíció |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | a világsebesség vetítve az előrére, a mínusz baloldalra (így a pozitív a jobb), és a felfelére |
| `longAcc`, `latAcc`, `vertAcc` | a világgyorsulás ugyanúgy vetítve |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | ahogy küldik |
| `gear` | `gear_index`; -1, ha a hátramenet indexével egyezik, 0, ha az üresjáratéval |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | a kerék tengelyének pozíciója |
| `wheelSurfaceSpeed.*` | az érintkezési folt előre irányuló sebessége |
| `brakeTemp.*` | fékhőmérséklet |

Ellenőrzés: ha a `speed` 10 felett van, és a világsebesség vektorának hossza több mint 20%-kal eltér tőle, a rögzítő egyszer kiírja, hogy az elrendezés lehet, hogy nem az alapértelmezett `wrc` struktúra.

Egy szakasz **befejezettnek** számít, ha a szakaszhossz pozitív, és a távolság elérte a hossz mínusz 0,5 m-t. A darabolásra és a `time`-ra használt óra a `stage_time`.

Források: az EA UDP Telemetry Guide v1.3; a csatornalista, amelyet a játék a `readme/channels.json` fájlba ír; az eltolások, ahogy a nobonobo/obs-codemasters-telemetry és a SpaceMonkey dekódolja. Az alapértelmezett port nincs dokumentálva; a rögzítő a 20777-et használja.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Bekapcsolás {#switching-it-on-1}

Szerkeszd a `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` fájlt (a DiRT Rally és a DiRT 4 szintén használ `hardware_settings_config.xml` fájlt; pontos mappájuk ezeknél nincs itt ellenőrizve), hogy az `udp` elem így szóljon:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

Az `extradata="3"` teszi, hogy a pozíciók, a kerekek és a szakasz hossza bekerüljenek a csomagba. A rögzítő nem szerkeszti ezt a fájlt.

### Mit küld {#what-it-sends-1}

66 little-endian lebegőpontos szám (DiRT Rally: 64); a 64-nél kevesebb számot tartalmazó csomagot figyelmen kívül hagyja, a 64 számosat nullákkal egészíti ki. A használt indexek:

| Index | Mező | Csatorna |
|---|---|---|
| 1 | kör (szakasz) ideje | a darabolóóra és a `time` |
| 2 | körtávolság | `stageDistance` |
| 4-6 | világpozíció | `x`, `y`, `z` |
| 7 | sebesség | `speed` |
| 8-10 | világsebesség | `longVel` (az előrére), `latVel` (az oldalvektoron) |
| 11-13 | oldalvektor | |
| 14-16 | előre vektor | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | felfüggesztési pozíció HÁ, HJ, ELs, EJ | `suspensionM.*` |
| 25-28 | kerék-folt sebesség HÁ, HJ, ELs, EJ | `wheelSurfaceSpeed.*` |
| 29-33 | gáz, kormány, fék, kuplung, fokozat | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 vagy több hátramenetet jelent, -1-ként íródik) |
| 34, 35 | oldalirányú, hosszirányú g | `latAcc`, `longAcc` (szorozva 9,80665-tel) |
| 37 | fordulatszám / 10 | `rpm` (szorozva 10-zel) |
| 51-54 | fékhőmérsékletek | `brakeTemp.*` |
| 59, 60, 61, 62 | teljesített körök, összes kör, pályahossz, utolsó köridő | darabolás |

**Nincs kézifék-csatorna.** Az oldalvektor iránya mindkét irányban dokumentált, ezért a `latVel` előjelére nem szabad támaszkodni (a nézegető a driftszög nagyságát olvassa).

Egy szakasz **befejezettnek** számít, ha a teljesített körök száma a szakasz kezdetén mért értéke fölé emelkedik (egy rallycross-kör minden alkalommal), vagy egykörös eseménynél, ha a körtávolság eléri a pálya hosszának 99,9%-át. A szakasz ideje a játék utolsó köridője, ha az pozitív. Ellenőrzés: a sebesség és a sebességvektor összevetése, mint az EA WRC-nél, az üzenettel: „is extradata set to 3?” (be van állítva az extradata 3-ra?).

Források: a Codemasters DiRT 4 UDP-dokumentuma; az ErlerPhilipp/dr2_logger; a soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Bekapcsolás {#switching-it-on-2}

A `RichardBurnsRally.ini` fájlban, a `[NGP]` szakaszban: `udpTelemetry=1`, és a végpont (127.0.0.1, 6776-os port, hacsak nem adsz meg másikat a `--port`-tal). A rögzítő nem szerkeszti ezt a fájlt.

### Mit küld {#what-it-sends-2}

664 bájt (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): szakaszóra és a végig hátralévő távolság, pedálok, kormány, fokozat, világpozíció, hozzáállás, az autó saját sebességei (előre irányuló lökés, oldalirányú siklás, függőleges emelkedés), gyorsulások, fordulatszám, és négy 128 bájtos kerékblokk (LF, RF, LB, RB) rugóbehajlással és rugóerővel. Nincs kerékfordulatszám.

| Csatorna | Forrás |
|---|---|
| `x`, `y`, `z` | pozíció, a tengelyek úgy, ahogy érkeznek, majd átrendezve (lent) |
| `longVel`, `latVel`, `vertVel` | lökés, siklás, emelkedés |
| `longAcc`, `latAcc` | gyorsulás x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | ahogy küldik |
| `gear` | `gear - 1` (0 hátramenet, 1 üresjárat, 2 első fokozat) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | rugóbehajlás |
| `wheelLoad.*` | rugóerő |
| `speed` | **a pozíciókból számolva** ±2 mintán, nem a csomagból véve |

Az RBR pozíciótengelyei, hozzáállás-egységei és a sebességegysége nincs dokumentálva, ezért egy szakasz kiírásakor: az a tengely, amely mentén a szakasz a legkevésbé változik, a függőleges, és `y`-ba cserélődik (`orient_up`, legalább 10 minta kell); a sebesség újra kiszámolódik a pozíciókból (`speed_from_positions`). A hozzáállást dekódolja, de nem írja, így az RBR-fájlokban nincs `yaw`.

Egy szakasz **befejezettnek** számít, ha a versenyóra fut, és a végig hátralévő távolság elérte a nullát. Az óra a `race_time`.

Források: az NGP `rbr.telemetry.data.TelemetryData.h` fájlja a mika-n/RBRUDPTelemetryLogger és a groybe/rbr-udp-telem közvetítésével.

## Szakaszok {#stages}

Mind az öt a `StageSplitter`-t használja a játék szakaszórájára: egy szakasz akkor nyílik, amikor az óra elindul, és befejezettként zárul, amikor a játék azt mondja, hogy az autó befutott; egy óra, amely visszamegy (újraindítás vagy a következő szakasz), a nyitott szakaszt elveti – `_partial` fájlként marad meg, ha több mint 10 mintája van és legalább 300 m. A 300 m-nél rövidebb befejezett szakaszok nem íródnak. Részletek: [Kör- és szakaszdarabolás](lap-splitting.md).

## A körfájl {#the-lap-file}

A `game` értéke `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` vagy `richard-burns-rally`. A `meta` `{"discipline": "rally", "slip": null}`, plusz `"surface": "<érték>"`, ha a `--surface` meg volt adva. A `slip` null, mert egyik játék sem küld gumicsúszást. Helyette minden kerék érintkezési folt-sebessége (EA WRC, DiRT) bekerül a fájlba; a csúszást és a driftszöget ebből és az autó tengelyeiből a nézegető számolja; lásd [Csúszás, driftszög és származtatott csatornák](slip-and-drift.md). A `suspension.*` csatornák (a használt utazás 0..1-e) a `suspensionM.*`-ből kerülnek hozzá.

Ha nincs `--surface`, a fájlban egyáltalán nincs felület, szándékosan: egy itt írt alapérték felülírná a nézegető saját következtetését. A nézegető ekkor a felületet a szakasz vagy az esemény nevéből veszi (aszfaltos ralik, téli ralik, a Monte vegyes), különben abból, hogyan vezették az autót rajta (erős kanyarvétel kis driftszögekkel aszfalt), és lazának tekinti, ha semmi nem árul el többet – ami egy ralis szakasz leggyakrabban. Add meg a `--surface`-t, ha jobban tudod.
