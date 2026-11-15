---
title: "Forza"
nav_order: 1
lang: "sl"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon in Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # igra -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # in FH Companion še vedno deluje
```

Koda: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py) (zaznavanje postavitve), [`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py) (vsi kanali, datoteke krogov, posredovanje).

## Vklop v igri {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, vrata `5300` (ali karkoli vnesete v `--port`). Forza Motorsport ponuja tudi obliko paketa: mora biti **Dash**, ne Sled. Sled ne nosi nobenega položaja, snemalnik ga zavrne.

Snemalnik se veže na `127.0.0.1`, zato mora igra teči na istem računalniku.

## Kaj igra pošilja in kako se najde postavitev {#what-the-game-sends-and-how-the-layout-is-found}

Data Out je en UDP paket na vsak tick simulacije (okoli 60 na sekundo), ravna C struktura v little-endian obliki, v teh velikostih:

| Dolžina | Varianta |
|---|---|
| 232 bajtov | Motorsport "Sled": brez položaja. Zavrnjen s sporočilom, naj preklopite na Dash. |
| 311 bajtov | Motorsport "Dash": blok Sled plus 79-bajtni dash blok |
| 324 bajtov | Horizon "Dash": isto z zamikom med obema blokoma |
| 331 bajtov | Forza Motorsport (2023): Dash plus 20 bajtov obrabe gum in id proge |

Blok Sled (odmiki 0–231) je stabilen. Kje se začne dash blok v varianti Horizon, objavljeni viri opisujejo nedosledno, napačno ugibanje pa ne javi napake, ampak da plavajoča števila iz napačnih polj. Zato se začetek **odkrije**:

1. Preizkusijo se kandidatni začetki v tem vrstnem redu: `length - 79` (dash blok sega do zadnjega bajta v vsaki dokumentirani varianti), 232, 244 in 232 do 260 v korakih po 4.
2. Vsak kandidat se oceni na paketih premikajočega se avta (komponenta hitrosti nad 1 m/s): vektor hitrosti v bloku Sled in skalarni `Speed` v dash bloku sta ista količina na dveh mestih, zato je `| |velocity| - Speed |` blizu nič samo za pravi začetek.
3. Zmaga kandidat z najmanjšim najslabšim odstopanjem, če je to odstopanje največ **1 m/s**. Sicer zaznavanje še čaka.

Medtem ko avto stoji, vsi kandidati berejo nič in se ujemajo, kar nič ne dokazuje, zato **zaznavanje čaka, da se avto premakne**: prevozite nekaj metrov, preden pričakujete izpis. Med čakanjem se zadrži do 600 paketov (obreže se na zadnjih 300). Ko je postavitev znana, se zadržani paketi tudi dekodirajo, da se začetek prvega kroga ne izgubi. Paketi druge dolžine od zaznane postavitve, paketi krajši od 311 bajtov in paketi z nekončnim položajem ali hitrostjo se za datoteke krogov prezrejo.

Katera Forza je, sledi iz postavitve: postavitev Horizon da `"game": "forza-horizon"`, postavitev Motorsport ali 331-bajtna pa `"forza-motorsport"`, vse drugo `"forza"`. Ime zaznane postavitve (`Horizon dash`, `Motorsport dash`, `331-byte dash`) se zapiše kot `layout`.

## Kanali, ki se snemajo {#channels-recorded}

Dekodira se vsako polje paketa (`decode_full`) in pretvori:

- pedala `throttle`, `brake`, `clutch`, `handbrake` iz 0..255 v 0..1;
- `steer` iz -127..127 v -1..1; `drivingLine` in `aiBrakeDifference` prav tako delita z 127;
- `tireTemp.FL` ... `.RR` iz Fahrenheita v Celzija;
- `latAcc`, `longAcc`, `vertAcc` in `yawRate` sta kopiji `accelX`, `accelZ`, `accelY` in `angVelY` pod kanoničnimi imeni (koordinatni sistem avta: x desno, y navzgor, z naprej);
- hitrost iz bloka Sled, ki je v lastnem koordinatnem sistemu avta (x desno, y navzgor, z naprej – ne sveta), se zapiše naravnost pod kanoničnima imenoma `latVel`, `vertVel` in `longVel`, da pregledovalnik kot drifta prebere neposredno, namesto da ga oceni iz smeri in poti.

Kanali datoteke kroga so vsi našteti, razen polj na krog:

| Skupina | Kanali |
|---|---|
| Čas in mesto | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Gibanje | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Motor | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Voznik | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Po kolesu (`.FL .FR .RL .RR`) | `suspension` (0 raztegnjeno .. 1 stisnjeno), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normirano: nad 1 guma popusti), `wheelSpeed` (rad/s), `rumble` (na robnem pasu), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Samo Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` je igrin časovnik trenutnega kroga minus njegova vrednost ob prvem vzorcu kroga; `distance` je prevožena razdalja, ki jo šteje igra, minus njena prva vrednost. Položaji so svetovne koordinate Forze v metrih, nespremenjeni (y je navzgor; svet je levosučen).

Enkrat na krog, ne na vzorec, se zapišejo pod `car`: `carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`, `rpmMax`, `rpmIdle`. Id proge Forze Motorsport 2023 gre prav tako enkrat, kot `lap.trackOrdinal`. Na vzorec se ne shrani `isRaceOn` (1 v vsakem okvirju kroga). `timestampMs`, `raceTime`, `bestLap` in `lastLap` se ohranijo kot kanali.

Preostanek dokumenta se napolni kot pri vseh drugih snemalnikih:

- `"track": null` – Forza Horizon ne pove imena proge, Forza Motorsport pa jo samo oštevilči;
- `"meta": {"slip": "peak", "discipline": "circuit"}` – kanali zdrsa so normirani tako, da nad 1 guma popusti;
- `units` našteva samo kanale, ki jih datoteka ima (kanali na kolo po osnovnem imenu);
- vrednost, ki ni končno število, se zapiše kot `null`, nikoli kot `NaN`.

Glejte [Datoteka `heat3d-lap`](lap-format.md).

## Kako se krogi razdelijo {#how-laps-are-split}

`LapSplitter` (glejte [Razdeljevanje krogov in etap](lap-splitting.md)): krog se zaključi, ko se igrin števec krogov premakne naprej, njegov čas pa je takrat igrin lastni `lastLap` (to, kar kaže igra). Točka-do-točke dirka ali seja, ki se konča sredi kroga, se zaključi, ko igra zapusti dirko (`isRaceOn` pade), ko paketi ostanejo brez 2 sekund, ali ko igrin časovni žig skoči nazaj; ohrani se kot `run`, če je pokril vsaj 400 m.

## Posredovanje FH Companionu {#relaying-to-fh-companion}

Igra pošilja Data Out samo enemu naslovu. Z `--forward host:port` snemalnik posreduje **vsak prejeti paket nespremenjen**, še preden karkoli dekodira (tudi med čakanjem na zaznavanje postavitve), da druga aplikacija, ki bere tok, še naprej deluje: nastavite igro na 5300, drugo aplikacijo na 5301 in zaženite z `--forward 127.0.0.1:5301`.

FH Companion je ločena aplikacija, ne del 3DHeat. Hrani knjižnico krogov v `%LOCALAPPDATA%\FHCompanion\laps`: mapo na progo, eno datoteko kroga na krog, vzorčeno približno na vsakih pet metrov, in ob vsaki datoteki kroga `<lap>.json.tele.gz`, celoten Data Out kroga pri igrini hitrosti. 3DHeat obe bere:

- **Pregledovalnik bere `.tele.gz` neposredno**, ko jo spustite (z ali brez njene datoteke kroga) na zavihek Analiza dirke. Igrina lastna imena polj (`PositionX`, `VelocityX`, `TireSlipRatio` + kolo, ...) preslika v kanonične kanale, lokalne `VelocityX/Y/Z` avta pretvori v `latVel`, `vertVel`, `longVel`, temperature gum pretvori iz Fahrenheita, izpusti vrstice, ki ponavljajo prejšnjo razen snemalnikove ure, in označi zdrs kot `peak`. Če je dana tudi datoteka kroga, krog od tam vzame avto in čas kroga. Ta bralnik je v pregledovalniku (`src/race/adapters.ts`, `readForzaTelemetry`), ne v tem repozitoriju.
- **Ukaz `laps`** bere knjižnico krogov in zapiše potek proge ter CSV vseh vzorcev; glejte [Pregled ukazov](commands.md#laps).

## Druga uporaba istega toka {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` snema samo položaje, shranjene na vsaki nekaj sekund med vožnjo; glejte [Pregled ukazov](commands.md#route).
- Možnost okna za pregled "Racing telemetry (Forza)" uporabi tok kot natančne poze kamere za rekonstrukcijo; glejte [Položaj kamere in merilo](reconstruction-pose.md#telemetry-poses).

## Opombe in opozorila {#notes-and-caveats}

- Proti čemu Forza normira svoj zdrs, ni dokumentirano. `1` beremo kot mejo oprijema, vendar pregledovalnik izmeri, kje se oprijem pri vsakem avtu res izgublja.
- Hitrost iz bloka Sled je lokalna za avto, kot pravi Forzina dokumentacija Data Out in potrjujejo posneti krogi (njena komponenta naprej nosi hitrost, stranska pa ostane blizu nič). Zaznavanje postavitve uporablja samo njeno dolžino, ki je v vsakem okvirju enaka.
- Položaji so svet igre, y navzgor in levosučen. Smisel `yaw`, `pitch` in `roll` je bil preverjen na posnetih krogih: yaw je enak smeri vožnje `atan2(dx, dz)`, pozitiven pitch je nos navzdol, pozitiven roll pa spusti desno stran.
