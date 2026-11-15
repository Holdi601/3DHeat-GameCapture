---
title: "EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally"
nav_order: 3
lang: "hr"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# EA SPORTS WRC, DiRT Rally 2.0 / DiRT Rally / DiRT 4, Richard Burns Rally {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # ili dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Kod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testovi: `tests/test_rally.py`, na paketima izrađenima prema dokumentiranim rasporedima.
**Još nije pokrenuto uz žive igre.**

Sve šalju UDP koji igra uključuje iz vlastitih postavki. Snimač sluša na svim sučeljima
(`0.0.0.0`) na zadanom portu igre, osim ako `--port` zada drugi: **20777** za `wrc`,
`dirtrally2`, `dirtrally`, `dirt4`; **6776** za `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Uključivanje {#switching-it-on}

Igra čita `Documents\My Games\WRC\telemetry\config.json`. Zadana struktura `wrc`, paket
`session_update`, mora biti uključena prema ovom računalu:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funkcija `configure_wrc`):

- čita JSON, pronalazi `udp.packets` i unos s `"structure": "wrc"` i
  `"packet": "session_update"`;
- ako je već uključen za `127.0.0.1` ili `localhost` na korištenom portu, ispisuje
  `already on` i ništa ne mijenja;
- inače postavlja `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, i zadržava
  `frequencyHz` unosa (ili `-1` ako ga nema); ako takav unos ne postoji, dodaje ga;
- izvorni tekst zapisuje u `config.json.bak` pokraj datoteke, zatim piše novu datoteku
  (uvučenu s 4 razmaka).

Ponovno pokrenite igru nakon promjene datoteke ako je ne prihvati (nije provjereno).

### Što šalje {#what-it-sends}

Zadana struktura `wrc` ima 237 bajtova, little-endian, bez zaglavlja: položaj u svijetu,
brzinu i ubrzanje (X lijevo, Y gore, Z naprijed), lijevi / naprijed / gornji jedinični vektori
automobila, po kotaču (stražnji lijevi, stražnji desni, prednji lijevi, prednji desni) visinu
glavčine i njezinu vertikalnu brzinu te brzinu naprijed dodirne površine, temperature kočnica,
pedale nakon pomoći, upravljanje (-1 lijevo, +1 desno), ručnu kočnicu, rpm, brzinu i sat
etape, udaljenost i duljinu. Paket kraći od 237 bajtova se ignorira i jednom se javi.

| Kanal | Iz |
|---|---|
| `x`, `y`, `z` | položaj u svijetu |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | brzina svijeta projicirana na naprijed, na minus lijevo (tako da je pozitivno desno), na gore |
| `longAcc`, `latAcc`, `vertAcc` | ubrzanje svijeta projicirano na isti način |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | kako su poslani |
| `gear` | `gear_index`; -1 kad je jednak indeksu za vožnju unatrag, 0 kad je jednak indeksu mrtvog hoda |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | položaj glavčine |
| `wheelSurfaceSpeed.*` | brzina naprijed dodirne površine |
| `brakeTemp.*` | temperatura kočnice |

Provjera: ako je `speed` iznad 10 i duljina vektora brzine svijeta odstupa od njega za više od
20 %, snimač jednom ispiše da raspored možda nije zadana struktura `wrc`.

Etapa je **završena** kad je duljina etape pozitivna i udaljenost je dosegla duljinu minus
0,5 m. Sat koji se koristi za dijeljenje i za `time` je `stage_time`.

Izvori: EA-in UDP Telemetry Guide v1.3; popis kanala koji igra zapisuje u
`readme/channels.json`; pomaci kako ih dekodiraju nobonobo/obs-codemasters-telemetry i
SpaceMonkey. Zadani port igre nije dokumentiran; snimač koristi 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Uključivanje {#switching-it-on-1}

Uredite `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml`
(DiRT Rally i DiRT 4 također koriste `hardware_settings_config.xml`; njihova točna mapa za
ta dva nije provjerena ovdje) tako da element `udp` glasi:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` stavlja položaje, kotače i duljinu etape u paket. Snimač ne uređuje ovu
datoteku.

### Što šalje {#what-it-sends-1}

66 little-endian brojeva s pomičnom točkom (DiRT Rally: 64); paketi kraći od 64 broja
ignoriraju se, a paket od 64 broja dopunjava se nulama. Korišteni indeksi:

| Indeks | Polje | Kanal |
|---|---|---|
| 1 | vrijeme etape (kruga) | sat za dijeljenje i `time` |
| 2 | udaljenost po etapi | `stageDistance` |
| 4-6 | položaj u svijetu | `x`, `y`, `z` |
| 7 | brzina | `speed` |
| 8-10 | brzina svijeta | `longVel` (na naprijed), `latVel` (na bočni vektor) |
| 11-13 | bočni vektor | |
| 14-16 | vektor naprijed | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | položaj ovjesa SL SD PL PD | `suspensionM.*` |
| 25-28 | brzina dodira kotača SL SD PL PD | `wheelSurfaceSpeed.*` |
| 29-33 | gas, upravljanje, kočnica, kvačilo, brzina | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ili više znači vožnju unatrag, zapisano kao -1) |
| 34, 35 | bočni, uzdužni g | `latAcc`, `longAcc` (puta 9,80665) |
| 37 | rpm / 10 | `rpm` (puta 10) |
| 51-54 | temperature kočnica | `brakeTemp.*` |
| 59, 60, 61, 62 | završeni krugovi, ukupno krugova, duljina staze, vrijeme zadnjeg kruga | dijeljenje |

**Nema kanala ručne kočnice.** Smjer bočnog vektora dokumentiran je u oba smjera, zato se
predznaku `latVel` ne smije vjerovati (preglednik čita veličinu kuta drifta).

Etapa je **završena** kad broj završenih krugova poraste iznad vrijednosti na početku
etape (svaki put kad se to dogodi, rallycross krug), ili, za događaj s jednim krugom, kad
udaljenost po krugu dosegne 99,9 % duljine staze. Vrijeme etape je vlastito vrijeme zadnjeg
kruga igre kad je pozitivno. Provjera: brzina naprema brzini kao kod EA WRC-a, uz poruku
„is extradata set to 3?”.

Izvori: Codemasters-ov UDP dokument za DiRT 4; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Uključivanje {#switching-it-on-2}

U `RichardBurnsRally.ini`, odjeljak `[NGP]`: `udpTelemetry=1` i krajnja točka (127.0.0.1,
port 6776 osim ako zadate drugi `--port`). Snimač ne uređuje ovu datoteku.

### Što šalje {#what-it-sends-2}

664 bajta (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): sat etape i udaljenost do
kraja, pedale, upravljanje, brzina, položaj u svijetu, stav, vlastite brzine automobila
(uzdužna naprijed, bočna u stranu, vertikalna), ubrzanja, rpm i četiri bloka kotača od 128
bajtova (LF, RF, LB, RB) s progibom opruge i silom opruge. Nema brzina kotača.

| Kanal | Iz |
|---|---|
| `x`, `y`, `z` | položaj, osi kako su poslane, pa preslagane (niže) |
| `longVel`, `latVel`, `vertVel` | uzdužna, bočna, vertikalna brzina |
| `longAcc`, `latAcc` | ubrzanje x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | kako su poslani |
| `gear` | `gear - 1` (0 vožnja unatrag, 1 mrtvi hod, 2 prva) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | progib opruge |
| `wheelLoad.*` | sila opruge |
| `speed` | **izračunata iz položaja** preko ±2 uzorka, ne uzeta iz paketa |

Osi položaja, jedinice stava i jedinica brzine RBR-a nisu dokumentirane, pa se kad se etapa
zapisuje: os po kojoj se etapa najmanje mijenja uzima kao gore i zamjenjuje u `y`
(`orient_up`, treba najmanje 10 uzoraka), a brzina se ponovno računa iz položaja
(`speed_from_positions`). Stav se dekodira, ali se ne zapisuje, pa datoteke RBR-a nemaju `yaw`.

Etapa je **završena** kad sat utrke teče i udaljenost do kraja dosegne nulu. Sat je
`race_time`.

Izvori: `rbr.telemetry.data.TelemetryData.h` od NGP-a preko mika-n/RBRUDPTelemetryLogger i
groybe/rbr-udp-telem.

## Etape {#stages}

Svih pet koristi `StageSplitter` na satu etape igre: etapa se otvara kad sat krene, zatvara
se kao završena kad igra javi da je automobil završio, a sat koji ide unatrag (ponovno
pokretanje ili sljedeća etapa) napušta otvorenu etapu - zadržava se kao datoteka `_partial`
ako ima više od 10 uzoraka i najmanje 300 m. Završene etape kraće od 300 m se ne zapisuju.
Pojedinosti: [Kako se krugovi i etape dijele](lap-splitting.md).

## Datoteka kruga {#the-lap-file}

`game` je `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ili `richard-burns-rally`.
`meta` je `{"discipline": "rally", "slip": null}`, uz `"surface": "<value>"` kad je dan
`--surface`. `slip` je null jer nijedna od ovih igara ne šalje klizanje guma. Brzina
dodirne površine svakog kotača (EA WRC, DiRT) umjesto toga je u datoteci, a preglednik iz
nje i iz osi automobila izvodi klizanje i kut drifta; vidi
[Klizanje, drift i izvedeni kanali](slip-and-drift.md). Kanali `suspension.*` (0..1 puta koji
je korišten) dodaju se iz `suspensionM.*`.

Kad nije dan `--surface`, datoteka namjerno nema podlogu: zadana vrijednost zapisana ovdje
prebrisala bi zaključak preglednika. Preglednik tada podlogu uzima iz naziva etape ili
događaja (asfaltne utrke, zimske, a Monte kao mixed), inače iz načina na koji je automobil
vožen na njoj (oštro zavijanje s malim kutovima drifta znači asfalt), a rastresita kad ništa
ne govori - što je najčešće slučaj za vozačku etapu. Zadajte `--surface` kad znate bolje.
