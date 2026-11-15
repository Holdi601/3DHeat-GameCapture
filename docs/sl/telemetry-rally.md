---
title: "Relijske igre"
nav_order: 3
lang: "sl"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # ali dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Koda: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py), [`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py). Testi: `tests/test_rally.py`, na paketih, sestavljenih iz dokumentiranih postavitev. **Še ni zagnano proti živim igram.**

Vse te igre pošiljajo UDP, ki ga igra vklopi iz svojih lastnih nastavitvenih datotek. Snemalnik posluša na vseh vmesnikih (`0.0.0.0`) na privzetih vratih igre, razen če z `--port` ne nastavite drugih: **20777** za `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** za `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Vklop {#switching-it-on}

Igra bere `Documents\My Games\WRC\telemetry\config.json`. Paket `session_update` privzete strukture `wrc` mora biti vklopljen proti temu računalniku:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funkcija `configure_wrc`):

- prebere JSON, poišče `udp.packets` in vnos z `"structure": "wrc"` ter `"packet": "session_update"`;
- če je že vklopljen na `127.0.0.1` ali `localhost` na uporabljenih vratih, izpiše `already on` in ničesar ne spremeni;
- sicer nastavi `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` in ohrani vnosov `frequencyHz` (ali `-1`, če ga ni); če takega vnosa ni, ga doda;
- izvirno besedilo zapiše v `config.json.bak` poleg datoteke, nato zapiše novo datoteko (zamik 4 presledki).

Če igra spremembe datoteke ne prevzame, jo po spremembi ponovno zaženite (ni preverjeno).

### Kaj pošilja {#what-it-sends}

Privzeta struktura `wrc` je 237 bajtov, little-endian, brez glave: svetovni položaj, hitrost in pospešek (X levo, Y navzgor, Z naprej), enotski vektorji avta levo / naprej / navzgor, po kolesu (zadaj-levo, zadaj-desno, spredaj-levo, spredaj-desno) višina središča in navpična hitrost ter hitrost naprej točke stika, temperature zavor, pedala po pomočeh, krmiljenje (-1 levo, +1 desno), ročna zavora, rpm, prestava in ura etape, razdalja in dolžina. Paket, krajši od 237 bajtov, se zavrže in enkrat javi.

| Kanal | Od kod |
|---|---|
| `x`, `y`, `z` | svetovni položaj |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | svetovna hitrost, projicirana na naprej, na minus levo (tako je pozitivno desno), na gor |
| `longAcc`, `latAcc`, `vertAcc` | svetovni pospešek, projiciran na enak način |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | kot poslano |
| `gear` | `gear_index`; -1, kadar je enak indeksu vzvratne, 0, kadar je enak indeksu prostega teka |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | položaj središča kolesa |
| `wheelSurfaceSpeed.*` | hitrost točke stika naprej |
| `brakeTemp.*` | temperatura zavore |

Preverjanje: če je `speed` nad 10 in se dolžina svetovne hitrosti od nje razlikuje za več kot 20 %, snemalnik enkrat izpiše, da postavitev morda ni privzeta struktura `wrc`.

Etapa je **končana**, ko je dolžina etape pozitivna in razdalja doseže dolžino minus 0,5 m. Ura, uporabljena za razdeljevanje in za `time`, je `stage_time`.

Viri: UDP Telemetry Guide v1.3 podjetja EA; seznam kanalov, ki ga igra zapiše v `readme/channels.json`; odmiki, kot jih dekodirata nobonobo/obs-codemasters-telemetry in SpaceMonkey. Privzetih vrat igre ni v dokumentaciji; snemalnik uporablja 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Vklop {#switching-it-on-1}

Uredite `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (tudi DiRT Rally in DiRT 4 uporabljata `hardware_settings_config.xml`; njuna točna mapa ni preverjena), tako da se element `udp` glasi:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` poskrbi, da so položaji, kolesa in dolžina etape v paketu. Snemalnik te datoteke ne ureja.

### Kaj pošilja {#what-it-sends-1}

66 little-endian števil s plavajočo vejico (DiRT Rally: 64); paketi, krajši od 64 števil, se zavržejo, paket s 64 števili pa se dopolni z ničlami. Uporabljeni indeksi:

| Indeks | Polje | Kanal |
|---|---|---|
| 1 | čas kroga (etape) | ura za razdeljevanje in `time` |
| 2 | razdalja kroga | `stageDistance` |
| 4–6 | svetovni položaj | `x`, `y`, `z` |
| 7 | hitrost | `speed` |
| 8–10 | svetovna hitrost | `longVel` (na naprej), `latVel` (na stranski vektor) |
| 11–13 | stranski vektor | |
| 14–16 | vektor naprej | `yaw = atan2(forward.x, forward.z)` |
| 17–20 | položaj vzmeti ZL ZD SL SD | `suspensionM.*` |
| 25–28 | hitrost točke stika koles ZL ZD SL SD | `wheelSurfaceSpeed.*` |
| 29–33 | plin, krmiljenje, zavora, sklopka, prestava | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ali več pomeni vzvratno, zapisano kot -1) |
| 34, 35 | bočni, vzdolžni g | `latAcc`, `longAcc` (pomnoženo z 9,80665) |
| 37 | rpm / 10 | `rpm` (pomnoženo z 10) |
| 51–54 | temperature zavor | `brakeTemp.*` |
| 59, 60, 61, 62 | odvoženi krogi, skupaj krogov, dolžina proge, čas zadnjega kroga | razdeljevanje |

**Ni kanala za ročno zavoro.** Smer stranskega vektorja je dokumentirana na obe strani, zato predznaku `latVel` ni treba zaupati (pregledovalnik bere velikost kota drifta).

Etapa je **končana**, ko število odvoženih krogov naraste nad vrednost ob začetku etape (rallycross krog vsakič, ko naraste), ali pri dogodku z enim krogom, ko razdalja kroga doseže 99,9 % dolžine proge. Čas etape je igrin čas zadnjega kroga, kadar je pozitiven. Preverjanje: hitrost glede na hitrost kot pri EA WRC, s sporočilom "is extradata set to 3?".

Viri: Codemastersov UDP dokument za DiRT 4; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Vklop {#switching-it-on-2}

V `RichardBurnsRally.ini`, razdelek `[NGP]`: `udpTelemetry=1` in končna točka (127.0.0.1, vrata 6776, razen če daš drugo z `--port`). Snemalnik te datoteke ne ureja.

### Kaj pošilja {#what-it-sends-2}

664 bajtov (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): ura etape in razdalja do cilja, pedala, krmiljenje, prestava, svetovni položaj, drža, lastne hitrosti avta (naprej, vstran, navpično), pospeški, rpm in štirje 128-bajtni bloki koles (LF, RF, LB, RB) z odklonom in silo vzmeti. Hitrosti koles ni.

| Kanal | Od kod |
|---|---|
| `x`, `y`, `z` | položaj, osi kot poslane, nato preurejene (spodaj) |
| `longVel`, `latVel`, `vertVel` | naprej, vstran, navpično |
| `longAcc`, `latAcc` | pospešek x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | kot poslano |
| `gear` | `gear - 1` (0 vzvratna, 1 prosti tek, 2 prva) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | odklon vzmeti |
| `wheelLoad.*` | sila vzmeti |
| `speed` | **izračunano iz položajev** čez ±2 vzorca, ne vzeto iz paketa |

Osi položaja RBR, enote drže in enota hitrosti niso dokumentirane, zato se ob zapisu etape os, v kateri etapa najmanj niha, vzame kot navzgor in zamenja z `y` (`orient_up`, potrebuje vsaj 10 vzorcev), hitrost pa se ponovno izračuna iz položajev (`speed_from_positions`). Drža se dekodira, vendar se ne zapiše, zato datoteke RBR nimajo `yaw`.

Etapa je **končana**, ko teče ura dirke in razdalja do cilja doseže nič. Ura je `race_time`.

Viri: NGP-jeva datoteka `rbr.telemetry.data.TelemetryData.h` prek mika-n/RBRUDPTelemetryLogger in groybe/rbr-udp-telem.

## Etape {#stages}

Vseh pet uporablja `StageSplitter` na igrini uri etape: etapa se odpre, ko se ura zažene, in se zapre kot dokončana, ko igra pove, da je avto končal; ura, ki gre nazaj (ponovni zagon ali naslednja etapa), odprto etapo opusti – ohrani se kot datoteka `_partial`, če ima več kot 10 vzorcev in vsaj 300 m. Končane etape, krajše od 300 m, se ne zapišejo. Podrobnosti: [Razdeljevanje krogov in etap](lap-splitting.md).

## Datoteka kroga {#the-lap-file}

`game` je `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ali `richard-burns-rally`. `meta` je `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"`, kadar je bil dan `--surface`. `slip` je null, ker nobena od teh iger ne pošilja zdrsa gume. Namesto tega je v datoteki hitrost točke stika vsakega kolesa (EA WRC, DiRT), iz nje in iz osi avta pa pregledovalnik izpelje zdrs in kot drifta; glejte [Zdrs, drift in izpeljani kanali](slip-and-drift.md). Kanali `suspension.*` (0..1 uporabljene poti) se dodajo iz `suspensionM.*`.

Kadar ni dan `--surface`, datoteka namenoma nima nobene podlage: privzeta vrednost, zapisana tukaj, bi prepisala pregledovalnikovo lastno sklepanje. Pregledovalnik podlago vzame iz imena etape ali dogodka (asfaltni reliji, zimski, Monte kot mešano), sicer iz tega, kako je bil avto voden na njej (močno zavijanje pri majhnih kotih drifta je asfalt), in ohlapno, kadar nič ne pove – kar je najpogosteje tisto, kar je relijska etapa. Dajte `--surface`, kadar veste bolje.
