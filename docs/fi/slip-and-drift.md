---
title: "Luisto, sivuliuku ja johdetut kanavat"
nav_order: 8
lang: "fi"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Luisto, sivuliuku ja johdetut kanavat {#slip-drift-and-derived-channels}

Katselimen Kisa-analyysi-välilehden autonhallinta-analyysi tarvitsee samat muutamat suureet jokaisesta pelistä:
kuinka paljon kukin rengas luistaa, kuinka paljon auto osoittaa pois suunnasta, johon se menee (sivuliukukulma),
onko se ilmassa ja onko se löysällä alustalla. Pelit lähettävät näitä hyvin eri muodoissa, tai eivät lainkaan.
Tallentimet kirjoittavat, mitä kukin peli lähettää, yhtenäisillä nimillä, ja `meta.slip`-merkinnän, joka kertoo, mitä
luistoluvut tarkoittavat; katselin johtaa sitten puuttuvan, kerran, kun se lataa kierroksen. **Pelin oma arvo voittaa
aina johdetun.**

## Mitä tallentimet kirjoittavat {#what-the-recorders-write}

| Peli | Luistokanavat | `meta.slip` | Sivuliukukulman lähtötiedot |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` renkaittain, lähetettynä | `peak` (tallentimen kirjoittama; katselimen `.tele.gz`-lukija asettaa saman) | `latVel`, `longVel` auton paikallisesta nopeudesta |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, sekä `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` auton kehyksen nopeudesta |
| EA SPORTS WRC, DiRT-pelit | ei mitään; sen sijaan `wheelSurfaceSpeed` renkaittain | `null` | `latVel`, `longVel` = maailman nopeus projisoituna auton akseleille |
| Richard Burns Rally | ei mitään; ei myöskään pyörien nopeuksia | ei mitään | `latVel`, `longVel` = auton oma heilunta ja etenemä |
| BeamNG.drive | ei mitään; `wheelSurfaceSpeed` ja `wheelSpeed` renkaittain | ei mitään | `latVel`, `longVel` = maailman nopeus projisoituna auton akseleille |
| Trackmania | `slipIndex` renkaittain (0..1 liukumismitta) | `index` | `latVel` (sivunopeus), `longVel` (etunopeus) |
| iRacing | ei mitään (ei kirjata) | ei mitään | `yaw` ja polku, `yawRate` |

`meta.slip`-arvot on määritelty kohdassa [heat3d-lap-tiedosto](lap-format.md): `peak` (normalisoitu, joten
yli 1 tarkoittaa, että rengas päästää irti), `scaled` (fyysinen luisto jaettuna tyypillisellä asfaltin huipulla),
`physical` (murto-osa ja radiaaneja), `index` (0..1 liukumismitta).

### Miksi Kunosin luisto skaalataan {#why-kunos-slip-is-scaled}

Forzan luisto on normalisoitu niin, että 1 on pidon reuna; mihin se normalisoi, ei ole dokumentoitu. Kunos lähettää
fyysisen luistosuhteen (murto-osa) ja sivuliukukulman (radiaaneja). Jakamalla ne tyypillisellä asfaltin huipulla -
0,12 suhteelle ja 0,14 rad (noin 8 astetta) kulmalle - "yli 1 tarkoittaa liukumista" pätee suunnilleen molemmille
perheille, mikä pitää yhden tulkinnan katselimen näytöille. Se on arvio: todelliset huiput vaihtelevat renkaan ja
pinnan mukaan, ja siksi raakat arvot säilytetään skaalattujen rinnalla, ja katselin mittaa kunkin auton pidon
todellisen päättymiskohdan kierroksista itsestään.

## Mitä katselin johtaa (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Nämä ajetaan katselimessa (`src/race/derive.ts` 3DHeat-katselimessa), eivät tässä repositoriossa.

### Sivuliukukulma, `bodySlip` {#drift-angle-bodyslip}

- **Auton kehyksen nopeudesta**, kun `latVel` ja `longVel` ovat läsnä: `atan2(latVel, |longVel|)`, ja 0 alle
  3 m/s (pysähtynyt sivuttain oleva auto ei luista).
  Sen merkki seuraa pelin sivunopeutta, jonka suunta on dokumentoitu joillekin peleille molempiin suuntiin -
  lue suuruus.
- **Muuten suunnasta suhteessa polkuun**: ajosuunta otetaan sijainneista noin 2 m kummallakin puolella kutakin
  näytettä (`atan2(dx, dz)`); pelin `yaw` sovitetaan siihen merkillä ja siirrolla (jokaisella pelillä on oma nollapiste
  ja pyörimissuunta) käyttäen näytteitä yli 10 m/s, ja se luotetaan vain, jos se sitten täsmää tiukasti (ympyräjakauman
  hajonta enintään 0,05, vähintään 20 näytettä). Sivuliukukulma on erotus, 0 alle 3 m/s.

### Luistosuhde pyöristä {#slip-ratio-from-the-wheels}

Kun kierroksella ei ole `slipRatio.*`-kanavaa mutta on pyörien nopeudet, luistosuhde on
`(wheel - car) / car` renkaittain, lähteinä:

- `wheelSurfaceSpeed.*` (kosketuspisteen nopeus, m/s) suoraan, kun se lähetetään (EA WRC, DiRT, BeamNG);
- muuten `wheelSpeed.*` (pyöriminen, rad/s) kerrottuna **kierroksella mitatulla vierintäsäteellä**: mediaani
  arvoista `speed / |omega|` näytteissä, joissa auto rullaa suoraan (yli 10 m/s, ei ilmassa, kaasu alle 0,3, jarru
  alle 0,05, pituussuuntainen kiihtyvyys alle 3 m/s²); alle 20 tällaisen näytteen kohdalla kaikki näytteet yli
  10 m/s. Säde alle 0,1 m tai yli 1 m hylätään.

Vain kun kaikki neljä pyörää voidaan johtaa; kierroksen `meta.slip` muuttuu silloin arvoksi `physical`. Alle 3 m/s
luisto on 0.

### Ilmassa {#airborne}

`airborne` on 1 siellä, missä jokainen rengas on irti maasta. Sen arvioi ensimmäinen seuraavista, jonka kierros
tarjoaa kaikille neljälle pyörälle:

1. `groundContact.*` (BeamNG): yksikään rengas ei ole yli 0,5;
2. `wheelLoad.*` (AC-pelit, RBR, BeamNG): yksikään rengas ei ole yli 5 % omasta mediaanikuormastaan;
3. `suspension.*` (0..1 matkasta): yksikään rengas ei ole yli 0,02, eli kaikki ovat täysin ojentuneet.

Yksittäinen eristetty ilmassa-näyte poistetaan. Trackmania kirjoittaa `airborne`-kanavan itse.

### Löysä alusta {#loose-ground}

Kun kierroksella on `surfaceRumble.*` (Forza), `loose` on 1 siellä, missä vähintään kaksi rengasta raportoi
tärinää vähintään kolmasosan sekunnin ajan, ja alle sekunnin aukot siltaavat (sileä kohta sorateillä on yhä sorateitä).
Trackmania kirjoittaa `loose`-kanavan itse renkaiden pohjamateriaaleista.

### Kääntymisnopeus {#yaw-rate}

Kun kierroksella on `yaw` mutta ei `yawRate`-kanavaa, se on yaw-muutos naapurinäytteiden yli.

## Mitä tallentimet johtavat itse {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): kaikki tallentimet paitsi Forza (joka lähettää sen) kirjoittavat sen `suspensionM.*`-arvosta
  kohdan mukaan alueella, jota tämä kierros käytti (pienimmästä suurimpaan). Se on autojen jousipalkkeihin ja pyörän
  ilmassa roikkumisen havaitsemiseen; se ei ole absoluuttinen matkan murto-osa.
- **`steer`** Kunos-peleille, skaalattuna kierroskohtaisesti (katso [Assetto Corsa -pelit](telemetry-assetto-corsa.md)).
- **Kiihtyvyydet** BeamNG:lle, maailman nopeuden muutoksesta ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** ja ylösakseli Richard Burns Rallylle, sijainneista ([Rallipelit](telemetry-rally.md)).

## Kätisyys {#handedness}

Siellä, missä pelin maailma on vasenkätinen - Forzan on - rata tulee ulos peilikuvana oikeakätisessä katselimessa;
kierrosten oma ohjaus ja jousitus paljastavat sen. Tallentimet eivät muuta kätisyyttä: Z-ylös-maailma (BeamNG) käännetään
Y-ylös-muotoon kierrolla, mikä säilyttää kätisyyden, ja kaikki muu kirjoitetaan niin kuin peli sen lähettää.
