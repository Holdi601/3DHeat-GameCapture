---
title: "Forza"
nav_order: 1
lang: "bs"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon i Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # game -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # and FH Companion keeps working
```

Kod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(otkrivanje rasporeda),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(svi kanali, datoteke krugova, prosljeđivanje).

## Uključivanje u igri {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (ili šta god
date kao `--port`). Forza Motorsport nudi i format paketa: mora biti **Dash**, ne
Sled. Sled uopće ne nosi poziciju, i snimač ga odbija.

Snimač se veže na `127.0.0.1`, pa igra mora raditi na istom računaru.

## Šta igra šalje i kako se pronalazi raspored {#what-the-game-sends-and-how-the-layout-is-found}

Data Out je jedan UDP paket po koraku simulacije (oko 60 u sekundi), ravna little-endian C
struktura ovih veličina:

| Dužina | Varijanta |
|---|---|
| 232 bajta | Motorsport "Sled": nema pozicije. Odbija se porukom koja kaže da pređete na Dash. |
| 311 bajta | Motorsport "Dash": Sled blok plus dash blok od 79 bajta |
| 324 bajta | Horizon "Dash": isto s ispunom između dva bloka |
| 331 bajt | Forza Motorsport (2023): Dash plus 20 bajta istrošenosti guma i id staze |

Sled blok (pomaci 0-231) je stabilan. Gdje dash blok počinje u Horizon varijanti
objavljeni izvori opisuju nedosljedno, a pogrešno pogađanje ne zakazuje - daje
uvjerljive float vrijednosti iz pogrešnih polja. Zato se početak **otkriva**:

1. Kandidati za početak isprobavaju se redom: `length - 79` (dash blok ide do posljednjeg
   bajta u svakoj dokumentiranoj varijanti), 232, 244, te 232 do 260 u koracima od 4.
2. Svaki kandidat se ocjenjuje na paketima automobila u pokretu (komponenta brzine iznad
   1 m/s): vektor brzine Sled bloka i skalarni `Speed` dash bloka su ista
   veličina na dva mjesta, pa je `| |velocity| - Speed |` blizu nule samo za pravi početak.
3. Pobjeđuje kandidat s najmanjim najgorim neslaganjem, ako je to neslaganje najviše
   **1 m/s**. Inače otkrivanje nastavlja čekati.

Dok je automobil parkiran, svaki kandidat čita nulu i slažu se, što ništa ne dokazuje, pa
**otkrivanje čeka dok se automobil ne pokrene**: vozite nekoliko metara prije nego što očekujete izlaz. Do
600 paketa se drži dok se čeka (skraćeno na posljednjih 300). Kad se raspored sazna,
zadržani paketi se također dekodiraju, pa se početak prvog kruga ne gubi. Paketi
drugačije dužine od otkrivenog rasporeda, paketi kraći od 311 bajta i paketi
s nekonačnom pozicijom ili brzinom ignorišu se za datoteke krugova.

Koja je to Forza proizlazi iz rasporeda: Horizon raspored daje `"game": "forza-horizon"`,
Motorsport ili raspored od 331 bajta daje `"forza-motorsport"`, sve ostalo `"forza"`. Ime
otkrivenog rasporeda (`Horizon dash`, `Motorsport dash`, `331-byte dash`) zapisuje se kao
`layout`.

## Snimljeni kanali {#channels-recorded}

Svako polje paketa se dekodira (`decode_full`) i pretvara:

- pedale `throttle`, `brake`, `clutch`, `handbrake` iz 0..255 u 0..1;
- `steer` iz -127..127 u -1..1; `drivingLine` i `aiBrakeDifference` također podijeljeni sa 127;
- `tireTemp.FL` ... `.RR` iz Fahrenheita u Celzijus;
- `latAcc`, `longAcc`, `vertAcc` i `yawRate` su kopije `accelX`, `accelZ`, `accelY` i
  `angVelY` pod kanonskim imenima (okvir automobila: x desno, y gore, z naprijed);
- Sled brzina, koja je u vlastitom okviru automobila (x desno, y gore, z naprijed - ne
  svjetskom), zapisuje se direktno pod kanonskim imenima `latVel`, `vertVel` i `longVel`, tako da
  preglednik ugao zanošenja čita iz nje, a ne procjenjuje iz smjera i putanje.

Kanali datoteke kruga su svi ovi osim polja po krugu:

| Grupa | Kanali |
|---|---|
| Vrijeme i mjesto | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Kretanje | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Vozač | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Po točku (`.FL .FR .RL .RR`) | `suspension` (0 rastegnut .. 1 stisnut), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizirano: preko 1 guma popušta), `wheelSpeed` (rad/s), `rumble` (na rumble traci), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Samo Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` je igrin mjerač trenutnog kruga minus njegova vrijednost u prvom uzorku kruga; `distance`
je igrina prevaljena udaljenost minus njena prva vrijednost. Pozicije su Forzine svjetske
koordinate u metrima, nepromijenjene (y je gore; svijet je lijevoruk).

Uzimaju se jednom po krugu, a ne po uzorku, pod `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. ID staze FM2023 također ide jednom, kao
`lap.trackOrdinal`. Ne čuva se po uzorku: `isRaceOn` (1 u svakom kadru kruga). `timestampMs`,
`raceTime`, `bestLap` i `lastLap` čuvaju se kao kanali.

Ostatak dokumenta popunjava se kao kod svakog drugog snimača:

- `"track": null` - Forza Horizon ne imenuje stazu, a Forza Motorsport je samo numeriše;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kanali klizanja su normalizirani tako da
  preko 1 guma popušta;
- `units` navodi samo kanale koje datoteka ima (one po točku po osnovnom imenu);
- vrijednost koja nije konačan broj zapisuje se kao `null`, nikad `NaN`.

Pogledajte [Datoteka heat3d-lap](lap-format.md).

## Kako se dijele krugovi {#how-laps-are-split}

`LapSplitter` (pogledajte [Dijeljenje na krugove i dionice](lap-splitting.md)): krug se zatvara kada
igrin brojač krugova krene dalje, a njegovo vrijeme je tada igrin vlastiti `lastLap` (ono što igra
prikazuje). Trka od tačke do tačke ili sesija koja završi usred kruga zatvara se kada igra napusti
trku (`isRaceOn` padne), kada paketi prestanu 2 sekunde ili kada se igrina vremenska oznaka
vrati unazad; zadržava se kao `run` ako je prešla najmanje 400 m.

## Prosljeđivanje do FH Companion {#relaying-to-fh-companion}

Igra šalje Data Out samo na jednu adresu. S `--forward host:port` snimač prosljeđuje
**svaki primljeni paket dalje nepromijenjen**, prije nego išta dekodira (i dok još
čeka da otkrije raspored), pa druga aplikacija koja čita feed nastavlja raditi: postavite igru
na 5300, drugu aplikaciju na 5301, i pokrenite s `--forward 127.0.0.1:5301`.

FH Companion je zasebna aplikacija, nije dio 3DHeat. Čuva biblioteku krugova pod
`%LOCALAPPDATA%\FHCompanion\laps`: folder po stazi, jedna datoteka kruga po krugu uzorkovana otprilike
svakih pet metara, a pored svake datoteke kruga `<lap>.json.tele.gz`, cijeli Data Out kruga u
brzini igre. 3DHeat čita oboje:

- **Preglednik čita `.tele.gz` direktno** kada ga ispustite (sa ili bez njegove datoteke kruga) na
  karticu Analiza utrke. Preslikava Forzina vlastita imena polja (`PositionX`, `VelocityX`, `TireSlipRatio`
  + točak, ...) u kanonske kanale, pretvara lokalne `VelocityX/Y/Z` automobila u `latVel`,
  `vertVel`, `longVel`, pretvara temperature guma iz Fahrenheita, odbacuje redove koji ponavljaju
  prethodni osim po satu snimača, i klizanje označava kao `peak`. Ako je data i datoteka kruga,
  krug odatle uzima automobil i vrijeme kruga. Ovaj čitač je u pregledniku
  (`src/race/adapters.ts`, `readForzaTelemetry`), a ne u ovom repozitoriju.
- **Komanda `laps`** čita biblioteku krugova i zapisuje rutu staze i CSV svakog
  uzorka; pogledajte [Pregled komandi](commands.md#laps).

## Druge upotrebe istog feeda {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` snima samo pozicije, spremljene svakih nekoliko sekundi
  tokom vožnje; pogledajte [Pregled komandi](commands.md#route).
- Opcija "Racing telemetry (Forza)" u prozoru za skeniranje koristi feed kao tačne poze kamere
  za rekonstrukciju; pogledajte [Poza kamere i skala](reconstruction-pose.md#telemetry-poses).

## Napomene i upozorenja {#notes-and-caveats}

- Prema čemu Forza normalizira klizanje nije dokumentirano. `1` se čita kao rub prianjanja,
  ali preglednik mjeri gdje prianjanje svakog automobila zaista popušta.
- Sled brzina je lokalna za automobil, kako kaže Forzina Data Out dokumentacija i potvrđuju snimljeni
  krugovi (njena prednja komponenta nosi brzinu, bočna ostaje blizu nule). Otkrivanje
  rasporeda koristi samo njenu dužinu, koja je ista u bilo kojem okviru.
- Pozicije su svijet igre, Y gore i lijevoruk. Smislovi `yaw`, `pitch` i `roll`
  provjereni su na snimljenim krugovima: yaw jednak smjeru kretanja `atan2(dx, dz)`, pozitivan
  pitch je nos dolje, a pozitivan roll spušta desnu stranu.
