---
title: "Forza Horizon i Forza Motorsport"
nav_order: 1
lang: "hr"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon i Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # igra -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # i FH Companion radi dalje
```

Kod: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(otkrivanje rasporeda),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(svi kanali, datoteke krugova, prosljeđivanje).

## Uključivanje u igri {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, port `5300` (ili što god
zadate kao `--port`). Forza Motorsport također nudi format paketa: mora biti **Dash**, ne
Sled. Sled uopće ne nosi položaj, a snimač ga odbija.

Snimač se veže na `127.0.0.1`, pa igra mora raditi na istom računalu.

## Što igra šalje i kako se pronalazi raspored {#what-the-game-sends-and-how-the-layout-is-found}

Data Out je jedan UDP paket po koraku simulacije (oko 60 u sekundi), ravna C struktura s
little-endian poretkom bajtova u ovim veličinama:

| Duljina | Varijanta |
|---|---|
| 232 bajta | Motorsport „Sled”: nema položaja. Odbija se uz poruku da se prebaci na Dash. |
| 311 bajtova | Motorsport „Dash”: blok Sled plus blok dash od 79 bajtova |
| 324 bajta | Horizon „Dash”: isto, s ispunom između dvaju blokova |
| 331 bajt | Forza Motorsport (2023.): Dash plus 20 bajtova trošenja guma i id staze |

Blok Sled (pomaci 0-231) je stabilan. Gdje u varijanti Horizon počinje blok dash opisano je
nedosljedno u objavljenim izvorima, a pogrešno pogađanje ne javlja grešku - daje uvjerljive
decimalne brojeve iz pogrešnih polja. Zato se početak **otkriva**:

1. Kandidatski početci isprobavaju se redom: `length - 79` (blok dash ide do zadnjeg bajta u
   svakoj dokumentiranoj varijanti), 232, 244, i 232 do 260 korakom 4.
2. Svaki kandidat ocjenjuje se na paketima pokretnog automobila (komponenta brzine iznad 1
   m/s): vektor brzine bloka Sled i skalarni `Speed` bloka dash su ista veličina na dva mjesta,
   pa je `| |velocity| - Speed |` blizu nule samo za pravi početak.
3. Kandidat s najmanjim najgorim odstupanjem pobjeđuje, ako je to odstupanje najviše **1
   m/s**. Inače otkrivanje nastavlja čekati.

Dok automobil stoji, svi kandidati čitaju nule i slažu se, što ništa ne dokazuje, pa
**otkrivanje čeka dok se automobil ne pokrene**: provozajte nekoliko metara prije nego što
očekujete izlaz. Dok čeka, zadržava se do 600 paketa (svodi se na zadnjih 300). Kad je
raspored poznat, zadržani paketi se također dekodiraju, pa se ne izgubi početak prvog kruga.
Paketi drukčije duljine od otkrivenog rasporeda, paketi kraći od 311 bajtova i paketi s
položajem ili brzinom koja nije konačan broj ignoriraju se za datoteke krugova.

Koja je Forza u pitanju slijedi iz rasporeda: raspored Horizona daje `"game": "forza-horizon"`,
raspored Motorsporta ili 331-bajtni raspored `"forza-motorsport"`, a bilo koji drugi
`"forza"`. Naziv otkrivenog rasporeda (`Horizon dash`, `Motorsport dash`, `331-byte dash`)
zapisuje se kao `layout`.

## Kanali koji se snimaju {#channels-recorded}

Svako polje paketa dekodira se (`decode_full`) i pretvara:

- pedale `throttle`, `brake`, `clutch`, `handbrake` iz 0..255 u 0..1;
- `steer` iz -127..127 u -1..1; `drivingLine` i `aiBrakeDifference` također se dijele s 127;
- `tireTemp.FL` ... `.RR` iz Fahrenheita u Celzija;
- `latAcc`, `longAcc`, `vertAcc` i `yawRate` su kopije `accelX`, `accelZ`, `accelY` i
  `angVelY` pod kanonskim nazivima (okvir automobila: x desno, y gore, z naprijed);
- brzina Sleda, koja je u vlastitom okviru automobila (x desno, y gore, z naprijed - ne
  svijeta), zapisuje se izravno pod kanonskim nazivima `latVel`, `vertVel` i `longVel`, pa
  preglednik kut drifta čita odatle umjesto da ga procjenjuje iz smjera i putanje.

Datoteka kruga ima sve ove kanale osim polja po krugu:

| Skupina | Kanali |
|---|---|
| Vrijeme i mjesto | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Kretanje | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Vozač | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Po kotaču (`.FL .FR .RL .RR`) | `suspension` (0 ispružen .. 1 sabijen), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalizirano: iznad 1 guma popušta), `wheelSpeed` (rad/s), `rumble` (na rubnim trakama za vibriranje), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Samo Forza Motorsport 2023. | `tireWear.FL` ... `.RR` |

`time` je tekući sat kruga igre umanjen za njegovu vrijednost na prvom uzorku kruga;
`distance` je prijeđeni put igre umanjen za njegovu prvu vrijednost. Položaji su svjetske
koordinate Forze u metrima, nepromijenjene (y je gore; svijet je lijevo orijentiran).

Jednom po krugu, a ne po uzorku, u bloku `car`: `carOrdinal`, `carClass`, `carPI`,
`drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Id staze FM2023 također se zapisuje jednom,
kao `lap.trackOrdinal`. Ne čuva se po uzorku: `isRaceOn` (1 u svakom okviru kruga).
`timestampMs`, `raceTime`, `bestLap` i `lastLap` čuvaju se kao kanali.

Ostatak dokumenta popunjava se kao i kod svakog drugog snimača:

- `"track": null` - Forza Horizon ne imenuje stazu, a Forza Motorsport je samo broji;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - kanali klizanja normalizirani su tako
  da iznad 1 guma popušta;
- `units` navodi samo kanale koje datoteka ima (po kotaču, prema osnovnom nazivu);
- vrijednost koja nije konačan broj zapisuje se kao `null`, nikad kao `NaN`.

Vidi [Datoteka `heat3d-lap`](lap-format.md).

## Kako se krugovi dijele {#how-laps-are-split}

`LapSplitter` (vidi [Kako se krugovi i etape dijele](lap-splitting.md)): krug se zatvara kad
brojač krugova igre pređe dalje, a njegovo vrijeme je tada vlastiti `lastLap` igre (ono što
igra prikazuje). Utrka od točke do točke ili sesija koja završi usred kruga zatvara se kad
igra napusti utrku (`isRaceOn` pada), kad paketi stanu na 2 sekunde ili kad vremenska oznaka
igre skoči unatrag; zadržava se kao `run` ako je pokrio najmanje 400 m.

## Prosljeđivanje FH Companion-u {#relaying-to-fh-companion}

Igra šalje Data Out samo na jednu adresu. S `--forward host:port` snimač prosljeđuje
**svaki primljeni paket nepromijenjen**, prije nego što išta dekodira (također dok još čeka
otkrivanje rasporeda), pa druga aplikacija koja čita tok nastavlja raditi: postavite igru na
5300, drugu aplikaciju na 5301, i pokrenite s `--forward 127.0.0.1:5301`.

FH Companion je zasebna aplikacija, a ne dio 3DHeata. Vodi biblioteku krugova u
`%LOCALAPPDATA%\FHCompanion\laps`: mapu po stazi, jednu datoteku kruga po krugu uzorkovanu
otprilike svakih pet metara, i uz svaku datoteku kruga `<lap>.json.tele.gz`, cijeli Data Out
vožnje pri brzini igre. 3DHeat čita obje:

- **Preglednik čita `.tele.gz` izravno** kad ga ispustite (sa ili bez njegove datoteke kruga)
  na kartici Analiza utrke. Preslikava Forzina vlastita imena polja (`PositionX`, `VelocityX`,
  `TireSlipRatio` + kotač, ...) u kanonske kanale, pretvara `VelocityX/Y/Z` iz okvira
  automobila u `latVel`, `vertVel`, `longVel`, pretvara temperature guma iz Fahrenheita,
  odbacuje retke koji ponavljaju prethodni osim po satu snimača i označava klizanje kao
  `peak`. Ako se dade i datoteka kruga, krug uzima automobil i vrijeme kruga iz nje. Ovaj
  čitač je u pregledniku (`src/race/adapters.ts`, `readForzaTelemetry`), ne u ovom repozitoriju.
- **Naredba `laps`** čita biblioteku krugova i piše rutu staze i CSV svakog uzorka; vidi
  [Pregled naredbi](commands.md#laps).

## Ostale upotrebe istog toka {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` snima samo položaje, spremljene svakih nekoliko sekundi
  tijekom vožnje; vidi [Pregled naredbi](commands.md#route).
- Opcija „Racing telemetry (Forza)” u prozoru skeniranja koristi tok kao točne položaje
  kamere za rekonstrukciju; vidi [Položaj kamere i mjerilo](reconstruction-pose.md#telemetry-poses).

## Napomene i upozorenja {#notes-and-caveats}

- Nije dokumentirano prema čemu Forza normalizira klizanje. `1` se čita kao rub prianjanja,
  ali preglednik mjeri gdje se prianjanje svakog automobila stvarno gubi.
- Brzina Sleda je u okviru automobila, kao što kaže Forzina dokumentacija Data Out i
  potvrđuju snimljeni krugovi (njezina komponenta naprijed nosi brzinu, a bočna ostaje blizu
  nule). Otkrivanje rasporeda koristi samo njezinu duljinu, koja je ista u bilo kojem okviru.
- Položaji su svijet igre, y gore i lijevo orijentiran. Smjerovi `yaw`, `pitch` i `roll`
  provjereni su na snimljenim krugovima: yaw je jednak smjeru vožnje `atan2(dx, dz)`,
  pozitivan pitch znači nos prema dolje, a pozitivan roll spušta desnu stranu.
