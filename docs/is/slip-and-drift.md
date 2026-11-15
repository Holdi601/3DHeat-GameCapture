---
title: "Skrið, rek og afleiddar rásir"
nav_order: 8
lang: "is"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Skrið, rek og afleiddar rásir {#slip-drift-and-derived-channels}

Aksturgreiningin í flipa áhorfandans Kappakstursgreining vill sömu fáu stærðirnar úr hverjum
leik: hversu mikið hvert dekk skríður, hversu mikið bíllinn vísar frá þeirri átt sem hann stefnir (rekhornið),
hvort hann er í lofti, hvort hann er á lausu undirlagi. Leikir senda þetta á mjög
ólíkan hátt, eða alls ekki. Upptökutækin hér skrifa það sem hver leikur sendir, undir
föstum heitum, ásamt `meta.slip` athugasemd sem segir hvað skriðtölurnar þýða; áhorfandinn
leiðir síðan út það sem vantar, einu sinni, þegar hann hleður hring. **Eigið gildi leiks vinnur alltaf
afleitt gildi.**

## Hvað upptökutækin skrifa {#what-the-recorders-write}

| Leikur | Skriðrásir | `meta.slip` | Inntak rekhorns |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` á hvert hjól, eins og sent | `peak` (skrifað af upptökutækinu; `.tele.gz` lesari áhorfandans setur það sama) | `latVel`, `longVel` úr hraða í ramma bílsins |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0.12, `slipAngle` / 0.14 rad, auk `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` úr hraða í ramma bílsins |
| EA SPORTS WRC, DiRT leikir | engar; `wheelSurfaceSpeed` á hvert hjól í staðinn | `null` | `latVel`, `longVel` = heimshraði varpað á ása bílsins |
| Richard Burns Rally | engar; engir hjólahraðar heldur | engin | `latVel`, `longVel` = eigin hliðarhreyfing og framhreyfing bílsins |
| BeamNG.drive | engar; `wheelSurfaceSpeed` og `wheelSpeed` á hvert hjól | engin | `latVel`, `longVel` = heimshraði varpað á ása bílsins |
| Trackmania | `slipIndex` á hvert hjól (0..1 mælikvarði á rennsli) | `index` | `latVel` (hliðarhraði), `longVel` (framhraði) |
| iRacing | engar (ekki skráð) | engin | `yaw` og ferillinn, `yawRate` |

`meta.slip` gildin eru skilgreind í [heat3d-lap skránni](lap-format.md): `peak`
(stöðlað svo yfir 1 sleppir dekkið gripinu), `scaled` (eðlisfræðilegt skrið deilt með dæmigerðu hámarki á
malbiki), `physical` (brot og radíanar), `index` (0..1 mælikvarði á rennsli).

### Hvers vegna Kunos skrið er skalað {#why-kunos-slip-is-scaled}

Skrið Forza er stöðlað þannig að 1 er jaðar grips; við hvað það er stillt er ekki
skjalfest. Kunos sendir eðlisfræðilegt skriðhlutfall (brot) og skriðhorn (radíanar). Að deila
með dæmigerðu hámarki á malbiki - 0,12 fyrir hlutfallið, 0,14 rad (um 8 gráður) fyrir hornið -
gerir „yfir 1 þýðir rennsli“ nokkurn veginn satt fyrir báðar fjölskyldur, sem heldur einni lestraraðferð
fyrir birtingar áhorfandans. Þetta er nálgun: raunveruleg hámörk eru breytileg eftir dekki og undirlagi, sem
er ástæðan fyrir því að hrágildin eru geymd við hlið skölduðu gildanna og hvers vegna áhorfandinn mælir hvar grip hvers
bíls fer í raun að minnka út frá hringjunum sjálfum.

## Hvað áhorfandinn leiðir út (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Þetta keyrir í áhorfandanum (`src/race/derive.ts` í 3DHeat áhorfandanum), ekki í þessari geymslu.

### Rekhorn, `bodySlip` {#drift-angle-bodyslip}

- **Úr hraða í ramma bílsins** þegar `latVel` og `longVel` eru til staðar:
  `atan2(latVel, |longVel|)`, og 0 undir 3 m/s (bíll sem stendur þversum er ekki að reka).
  Formerki þess fylgir hliðarhraða leiksins, sem er skjalfestur á báða vegu í sumum
  leikjum - lestu stærðina.
- **Annars úr stefnunni miðað við ferilinn**: ferðastefnan er tekin úr
  staðsetningum um 2 m sitt hvorum megin við hvert sýni (`atan2(dx, dz)`); `yaw` leiksins er aðlagað
  henni með formerki og hliðrun (hver leikur hefur sitt núll og snúningsátt) með
  sýnum yfir 10 m/s, og aðeins treyst ef það passar þá náið (hringdreifing í mesta lagi
  0,05, að minnsta kosti 20 sýni). Rekhornið er mismunurinn, 0 undir 3 m/s.

### Skriðhlutfall úr hjólunum {#slip-ratio-from-the-wheels}

Þar sem hringur hefur ekkert `slipRatio.*` en hefur hjólahraða er skriðhlutfallið
`(wheel - car) / car` á hvert hjól, úr:

- `wheelSurfaceSpeed.*` (hraði snertiflatar, m/s) beint, þegar sent (EA WRC, DiRT,
  BeamNG);
- annars `wheelSpeed.*` (snúningur, rad/s) sinnum **veltiradíus mældur á hringnum**:
  miðgildi `speed / |omega|` yfir sýni þar sem bíllinn rennur beint áfram (yfir
  10 m/s, ekki í lofti, inngjöf undir 0,3, bremsa undir 0,05, langhröðun undir
  3 m/s²); með færri en 20 slík sýni, öll sýni yfir 10 m/s. Radíus utan
  0,1-1 m er hafnað.

Aðeins þegar hægt er að leiða út öll fjögur hjólin; `meta.slip` hringsins verður þá `physical`. Undir
3 m/s er skriðið 0.

### Í lofti {#airborne}

`airborne` er 1 þar sem hvert hjól er frá jörðu, metið eftir því fyrsta af þessu sem hringurinn hefur
fyrir öll fjögur hjólin:

1. `groundContact.*` (BeamNG): ekkert hjól yfir 0,5;
2. `wheelLoad.*` (AC leikir, RBR, BeamNG): ekkert hjól yfir 5% af eigin miðgildisálagi;
3. `suspension.*` (0..1 af slagi): ekkert hjól yfir 0,02, þ.e. öll fullútdregin.

Stakt einangrað sýni í lofti er hreinsað burt. Trackmania skrifar `airborne` sjálft.

### Laust undirlag {#loose-ground}

Þar sem hringur hefur `surfaceRumble.*` (Forza) er `loose` 1 þar sem að minnsta kosti tvö hjól tilkynna
skrölt í að minnsta kosti þriðjung úr sekúndu, með eyðum styttri en ein sekúnda brúaðar (slétt
blettur á malarvegi er samt malarvegur). Trackmania skrifar `loose` sjálft úr
undirlagsefni hjólanna.

### Snúningshraði um lóðás {#yaw-rate}

Þar sem hringur hefur `yaw` en ekki `yawRate` er það breyting `yaw` yfir nálæg sýni.

## Hvað upptökutækin leiða sjálf út {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): öll upptökutæki nema Forza (sem sendir það) skrifa það úr
  `suspensionM.*` sem stöðuna innan þess bils sem hringurinn notaði (lágmark til hámarks). Það er
  fyrir fjöðrunarstikur bílsins og til að koma auga á hjól sem hangir í lofti; það er ekki
  algilt hlutfall slags.
- **`steer`** fyrir Kunos leikina, skalað á hring (sjá
  [Assetto Corsa leiki](telemetry-assetto-corsa.md)).
- **Hröðun** fyrir BeamNG, úr breytingu heimshraða
  ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** og upp-ásinn fyrir Richard Burns Rally, úr staðsetningunum
  ([Ralllíleikir](telemetry-rally.md)).

## Handstefna {#handedness}

Þar sem heimur leiks er örvhentur - heimur Forza er það - kemur braut út spegluð í
rétthentum áhorfanda; stýring og fjöðrun hringjanna sjálfra koma upp um það. Upptökutækin breyta ekki
handstefnu: Z-upp heimur (BeamNG) er snúinn í Y-upp með snúningi, sem heldur henni, og
allt annað er skrifað eins og það var sent.
