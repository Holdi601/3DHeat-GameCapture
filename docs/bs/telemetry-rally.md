---
title: "Reli igre"
nav_order: 3
lang: "bs"
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

Kod: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testovi: `tests/test_rally.py`, na paketima izgrađenim iz dokumentiranih rasporeda. **Još nije
pokrenuto protiv živih igara.**

Sve šalju UDP koji igra uključuje iz vlastitih datoteka postavki. Snimač
sluša na svim sučeljima (`0.0.0.0`) na zadanom portu igre osim ako `--port` ne daje
drugi: **20777** za `wrc`, `dirtrally2`, `dirtrally`, `dirt4`; **6776** za `rbr`.

## EA SPORTS WRC {#ea-sports-wrc}

### Uključivanje {#switching-it-on}

Igra čita `Documents\My Games\WRC\telemetry\config.json`. Paket `session_update` zadane `wrc`
strukture mora biti uključen prema ovom računaru:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funkcija `configure_wrc`):

- čita JSON, pronalazi `udp.packets` i unos s `"structure": "wrc"` i
  `"packet": "session_update"`;
- ako je već uključen prema `127.0.0.1` ili `localhost` na portu koji se koristi, ispisuje
  `already on` i ništa ne mijenja;
- inače postavlja `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true`, i zadržava
  `frequencyHz` unosa (ili `-1` ako ga nema); ako takvog unosa nema, dodaje ga;
- zapisuje originalni tekst u `config.json.bak` pored, zatim zapisuje novu datoteku
  (uvučenu 4 razmaka).

Ponovo pokrenite igru nakon promjene datoteke ako ne preuzme promjenu (nije provjereno).

### Šta šalje {#what-it-sends}

Zadana `wrc` struktura je 237 bajta, little-endian, bez zaglavlja: svjetska pozicija,
brzina i ubrzanje (X lijevo, Y gore, Z naprijed), jedinični vektori automobila lijevo / naprijed / gore, po točku (zadnji lijevi, zadnji desni, prednji lijevi, prednji desni) visina glavčine
i vertikalna brzina te prednja brzina kontaktne površine, temperature kočnica, pedale nakon
pomoćnih sistema, upravljanje (-1 lijevo, +1 desno), ručna kočnica, rpm, stepen prijenosa, te sat dionice, udaljenost i
dužina. Paket kraći od 237 bajta se ignoriše i prijavljuje jednom.

| Kanal | Iz |
|---|---|
| `x`, `y`, `z` | svjetska pozicija |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | svjetska brzina projicirana na naprijed, na minus lijevo (pa je pozitivno desno), na gore |
| `longAcc`, `latAcc`, `vertAcc` | svjetsko ubrzanje projicirano na isti način |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | kako su poslani |
| `gear` | `gear_index`; -1 kada je jednak indeksu za nazad, 0 kada je jednak indeksu za neutralno |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | pozicija glavčine |
| `wheelSurfaceSpeed.*` | prednja brzina kontaktne površine |
| `brakeTemp.*` | temperatura kočnice |

Provjera: ako je `speed` iznad 10, a dužina svjetske brzine se razlikuje od nje za više od
20%, snimač jednom ispisuje da raspored možda nije zadana `wrc` struktura.

Dionica je **završena** kada je dužina dionice pozitivna, a udaljenost je dostigla
dužinu minus 0,5 m. Sat koji se koristi za dijeljenje i za `time` je `stage_time`.

Izvori: EA-ov UDP Telemetry Guide v1.3; spisak kanala koji igra upisuje u
`readme/channels.json`; pomaci kako su dekodirani u nobonobo/obs-codemasters-telemetry i
SpaceMonkey. Zadani port nije dokumentiran; snimač koristi 20777.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Uključivanje {#switching-it-on-1}

Uredite `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT
Rally i DiRT 4 također koriste `hardware_settings_config.xml`; njegov tačan folder za ta dva
ovdje nije provjeren) tako da element `udp` glasi:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` je ono što u paket stavlja pozicije, točkove i dužinu dionice. Snimač
ne uređuje ovu datoteku.

### Šta šalje {#what-it-sends-1}

66 little-endian float vrijednosti (DiRT Rally: 64); paketi kraći od 64 floata se ignorišu, a
paket od 64 floata dopunjava se nulama. Korišteni indeksi:

| Indeks | Polje | Kanal |
|---|---|---|
| 1 | vrijeme kruga (dionice) | sat dijeljenja i `time` |
| 2 | udaljenost kruga | `stageDistance` |
| 4-6 | svjetska pozicija | `x`, `y`, `z` |
| 7 | brzina | `speed` |
| 8-10 | svjetska brzina | `longVel` (na naprijed), `latVel` (na bočni vektor) |
| 11-13 | bočni vektor | |
| 14-16 | vektor naprijed | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | pozicija ovjesa RL RR FL FR | `suspensionM.*` |
| 25-28 | brzina površine točka RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | gas, upravljanje, kočnica, kvačilo, stepen prijenosa | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 ili više znači nazad, zapisuje se kao -1) |
| 34, 35 | bočni, uzdužni g | `latAcc`, `longAcc` (puta 9,80665) |
| 37 | rpm / 10 | `rpm` (puta 10) |
| 51-54 | temperature kočnica | `brakeTemp.*` |
| 59, 60, 61, 62 | završeni krugovi, ukupno krugova, dužina staze, vrijeme posljednjeg kruga | dijeljenje |

**Nema kanala ručne kočnice.** Smisao bočnog vektora dokumentiran je na oba načina, pa se
predznak `latVel` ne smije oslanjati (preglednik čita veličinu ugla zanošenja).

Dionica je **završena** kada broj završenih krugova poraste iznad svoje vrijednosti na početku dionice
(jedan rallycross krug svaki put kad se to desi), ili, za događaj od jednog kruga, kada udaljenost kruga
dostigne 99,9% dužine staze. Vrijeme dionice je igrino vrijeme posljednjeg kruga kada je
pozitivno. Provjera: brzina naspram iznosa kao za EA WRC, s porukom "is extradata set
to 3?".

Izvori: Codemastersov UDP dokument za DiRT 4; ErlerPhilipp/dr2_logger;
soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Uključivanje {#switching-it-on-2}

U `RichardBurnsRally.ini`, odjeljak `[NGP]`: `udpTelemetry=1` i krajnja tačka (127.0.0.1,
port 6776 osim ako ne date drugi `--port`). Snimač ne uređuje ovu datoteku.

### Šta šalje {#what-it-sends-2}

664 bajta (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): sat dionice i udaljenost
do kraja, pedale, upravljanje, stepen prijenosa, svjetska pozicija, stav, vlastite brzine automobila
(surge naprijed, sway bočno, heave), ubrzanja, rpm, i četiri bloka točkova od 128 bajta
(LF, RF, LB, RB) s ugibom opruge i silom opruge. Nema brzina točkova.

| Kanal | Iz |
|---|---|
| `x`, `y`, `z` | pozicija, ose kako su poslane, zatim preuređene (ispod) |
| `longVel`, `latVel`, `vertVel` | surge, sway, heave |
| `longAcc`, `latAcc` | ubrzanje x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | kako su poslani |
| `gear` | `gear - 1` (0 nazad, 1 neutralno, 2 prva) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | ugib opruge |
| `wheelLoad.*` | sila opruge |
| `speed` | **izračunato iz pozicija** preko +-2 uzorka, ne uzeto iz paketa |

RBR-ove ose pozicije, jedinice stava i jedinica brzine nisu dokumentirane, pa kad se dionica
zapisuje: osa duž koje dionica najmanje varira uzima se kao gore i zamjenjuje u `y`
(`orient_up`, treba najmanje 10 uzoraka), a brzina se ponovo računa iz pozicija
(`speed_from_positions`). Stav se dekodira, ali ne zapisuje, pa RBR datoteke nemaju `yaw`.

Dionica je **završena** kada sat trke radi, a udaljenost do kraja
je dostigla nulu. Sat je `race_time`.

Izvori: NGP-ov `rbr.telemetry.data.TelemetryData.h` preko mika-n/RBRUDPTelemetryLogger i
groybe/rbr-udp-telem.

## Dionice {#stages}

Svih pet koristi `StageSplitter` na satu dionice igre: dionica se otvara kada sat krene,
zatvara završena kada igra kaže da je automobil stigao do cilja, a sat koji ide unazad (ponovno pokretanje,
ili sljedeća dionica) napušta otvorenu dionicu - zadržava se kao `_partial` datoteka ako ima više od 10
uzoraka i najmanje 300 m. Završene dionice kraće od 300 m se ne zapisuju. Detalji:
[Dijeljenje na krugove i dionice](lap-splitting.md).

## Datoteka kruga {#the-lap-file}

`game` je `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` ili `richard-burns-rally`.
`meta` je `{"discipline": "rally", "slip": null}`, plus `"surface": "<value>"` kada je dat
`--surface`. `slip` je null jer nijedna od ovih igara ne šalje klizanje guma. Umjesto toga je u datoteci
brzina kontaktne površine svakog točka (EA WRC, DiRT), a preglednik iz nje i osa automobila izvodi klizanje i
ugao zanošenja; pogledajte [Klizanje, zanošenje i izvedeni kanali](slip-and-drift.md). Kanali
`suspension.*` (0..1 korištenog hoda) dodaju se iz `suspensionM.*`.

Kada `--surface` nije dat, datoteka namjerno ne nosi nikakvu površinu: zadana vrijednost zapisana
ovdje bi nadjačala vlastito zaključivanje preglednika. Preglednik tada uzima površinu iz
imena dionice ili događaja (asfaltni relii, zimski, Monte kao mješovita), inače iz načina
na koji je automobil na njoj vožen (jako skretanje pri malim uglovima zanošenja je asfalt), a rastresitu kada ništa ne
govori drugačije - što dionica reli-a najčešće jeste. Dajte `--surface` kada znate bolje.
