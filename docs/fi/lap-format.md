---
title: "heat3d-lap-tiedosto"
nav_order: 9
lang: "fi"
source: lap-format.md
source_hash: "0b65cc8a0c81"
nav_exclude: true
search_exclude: true
---
# `heat3d-lap`-tiedosto {#the-heat3d-lap-file}

Jokainen telemetriatallennin tässä repositoriossa kirjoittaa yhden tiedoston kierrosta
tai rallin osuutta kohden, samassa muodossa pelistä riippumatta. [3DHeat GameFilesin](https://github.com/Holdi601/3DHeat-GameFiles)
radan vienti lukee sen takaisin selvittääkseen pelin, kentän ja ajetun linjan. Kaikki,
mikä lukee JSONia, voi lukea sen.

![Synteettisestä Forza-syötteestä kirjoitetun kierrostiedoston kentät ja kanavat](../assets/img/lap-file.svg)

## Dokumentti {#the-document}

Yksi JSON-olio. Kanavat on tallennettu sarakkeina: yksi taulukko kanavaa kohden, kaikki
samanpituisia, yksi arvo näytettä kohden.

```json
{
  "format": "heat3d-lap",
  "version": 1,
  "game": "assetto-corsa-rally",
  "track": "stage name, when the game says",
  "recordedAt": "2026-09-21T12:48:59+02:00",
  "car": {},
  "lap": {"number": 3, "seconds": 52.103, "complete": true, "metres": 1908.9},
  "meta": {"slip": "scaled", "discipline": "rally", "surface": "loose"},
  "units": {"speed": "m/s", "tireTemp": "degC"},
  "channels": {
    "time": [0.0, 0.0167],
    "distance": [0.0, 0.41],
    "x": [], "y": [], "z": [],
    "speed": [],
    "tireTemp.FL": [], "tireTemp.FR": [], "tireTemp.RL": [], "tireTemp.RR": []
  }
}
```

| Kenttä | Merkitys |
|---|---|
| `format`, `version` | `heat3d-lap`, `1` |
| `game` | mistä pelistä kierros on; katso alla oleva luettelo |
| `track` | radan, osuuden tai kartan nimi, kun peli sen lähettää |
| `layout` | vain Forza: mikä Data Out -paketin asettelu tulkittiin |
| `car` | kaikki, mitä peli sanoo autosta; vapaamuotoinen |
| `lap` | kierroksen numero, sen aika pelin laskemana (tai näytteiden väli), oliko se päätetty ja sen pituus |
| `meta` | miten lukemat luetaan; katso alla |
| `units` | kunkin läsnä olevan kanavan yksikkö lukijalle, joka ei tunne alla olevaa taulukkoa |
| `channels` | näytteet |
| `unparsed` | vain Forza, kun paketissa on tavuja, joille ei ole nimettyä kenttää: `ranges` (niiden `[start, end)`-tavuoffsetit paketissa) ja `hex` (näytettä kohden nuo tavut heksadesimaalina), joten pelkkä tiedosto sisältää koko paketin |

`game` on yksi seuraavista: `forza-horizon`, `forza-motorsport`, `forza` (asettelua ei
erotettu), `assetto-corsa`, `assetto-corsa-competizione`, `assetto-corsa-evo`,
`assetto-corsa-rally`, `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4`,
`richard-burns-rally`, `beamng`, `trackmania`.

`meta` kertoo, mitä luvut tarkoittavat siellä, missä pelit eroavat:

- `slip`: mitä luistokanavat sisältävät, jos peli niitä lähettää - `peak` (normalisoitu,
  yli 1 tarkoittaa, että rengas päästää irti: Forza), `scaled` (fyysinen luisto jaettuna
  tyypillisellä asfaltin huipulla: Assetto Corsa -pelit), `physical` (murto-osa ja
  radiaaneja), `index` (0..1 liukumismitta: Trackmania);
- `discipline`: `circuit`, `rally` tai `arcade`;
- `surface`: `tarmac`, `loose`, `snow`, `ice` tai `mixed`, kun tiedetään (rallitallentimet
  ottavat sen valinnasta `--surface`).

## Kanavat {#channels}

Kanava, jota peli ei lähetä, puuttuu kokonaan eikä sitä täytetä nollilla. Renkaakohtaiset
kanavat kantavat pyörän nimen pisteen jälkeen: `.FL`, `.FR`, `.RL`, `.RR`.

Sijainnit ovat pelin maailmassa metreinä, `y` ylöspäin. Peli, jonka maailma on Z ylös,
käännetään tallentimessa Y ylös -muotoon; muuta ei muuteta, joten vasenkätinen maailma
(Forzan) pysyy vasenkätisenä.

| Kanava | Yksikkö | Merkitys |
|---|---|---|
| `time` | s | kierroksen ensimmäisestä näytteestä lähtien |
| `distance` | m | ajetulla polulla ensimmäisestä näytteestä lähtien |
| `x`, `y`, `z` | m | sijainti; `y` on korkeus |
| `speed` | m/s | |
| `throttle`, `brake`, `clutch`, `handbrake` | 0..1 | pedaalit ja vipu |
| `steer` | -1..1 | positiivinen oikealle |
| `gear` | | niin kuin peli ne laskee |
| `latAcc`, `longAcc`, `vertAcc` | m/s² | auton kehyksessä |
| `yaw`, `pitch`, `roll` | rad | suunta ja asento |
| `yawRate` | rad/s | |
| `latVel`, `longVel`, `vertVel` | m/s | nopeus auton kehyksessä: oikealle, eteenpäin, ylös |
| `bodySlip` | rad | sivuliukukulma, kun peli sen lähettää |
| `loose` | 0/1 | löysällä alustalla (Trackmania) |
| `airborne` | 0/1 | yksikään rengas ei ole maassa |
| `rpm` | rpm | |
| `power`, `torque` | W, N m | |
| `boost`, `fuel` | | niin kuin peli ne lähettää |
| `waterTemp`, `oilTemp` | °C | |
| `absActive`, `tcActive`, `drs`, `pitLimiter` | 0/1 | avustusjärjestelmä toiminnassa, järjestelmä päällä |
| `absLevel`, `tcLevel` | | avustusasetukset |
| `brakeBias` | 0..1 | etuosan osuus |
| `tireTemp`, `tireTempInner`, `tireTempMiddle`, `tireTempOuter` | °C | renkaittain |
| `tirePressure` | psi | renkaittain |
| `tireWear` | 0..1 | renkaittain |
| `slipRatio`, `slipAngle`, `combinedSlip` | katso `meta.slip` | renkaittain |
| `slipIndex` | 0..1 | renkaittain oleva liukumismitta (Trackmania) |
| `camber` | rad | renkaittain |
| `brakeTemp` | °C | renkaittain |
| `padLife`, `discLife` | | renkaittain |
| `suspensionM` | m | renkaittain jousen matka |
| `suspension` | 0..1 | renkaittain jousen matka sen alueen mukaan, jota tämä kierros käytti |
| `wheelLoad` | N | renkaittain |
| `wheelSpeed` | rad/s | renkaittain pyörimisnopeus |
| `wheelSurfaceSpeed` | m/s | renkaittain kosketuspisteen nopeus |
| `groundContact` | 0/1 | renkaittain |
| `rumble`, `surfaceRumble` | | renkaittain: tärisyttävällä reunakivellä; pinnan tärinä |
| `puddle` | | renkaittain seisovan veden syvyys |

Tallennin voi lisätä omia kanavia muilla nimillä; lukija säilyttää ne, joita se ei tunne.

Mikään rallipeli ei lähetä renkaiden luistoa. Lukija voi laskea sen kunkin renkaan
kosketuspisteen tai pintanopeuden ja auton nopeuden erotuksesta,
`(wheel - car) / car`, tai pyörimisestä ja kierroksella itse mitatusta vierintäsäteestä,
jos peli lähettää vain pyörimisen. Sivuliukukulma tulee auton omasta nopeudesta
(`latVel`, `longVel`), kun se on lähetetty, tai maailman nopeudesta projisoituna auton
akseleille.

## CSV-muoto {#the-csv-form}

Trackmania-liitännäinen kirjoittaa sen sijaan `heat3d-lap-csv`-muotoa: ensimmäinen rivi
alkaa merkillä `# ` ja sen jälkeen JSON-olio (`format`, `version`, `game`, `track`,
`complete`, `seconds`, `meta`), sitten rivi kanavien nimiä ja yksi rivi näytettä kohden.
Kanavien nimet ovat samat kuin yllä.

## Mitä kukin tallennin todella kirjoittaa {#what-each-recorder-actually-writes}

Yllä oleva muoto on sopimus; tallentimet täyttävät sen hieman eri tavoin, ja lukijan
pitää sietää kaikki nämä (tarkistettu koodista):

| Tallennin | `track` | `layout` | `meta` | `units` | Kanavat taulukon lisäksi |
|---|---|---|---|---|---|
| Forza (`fulllap.py`) | `null` (Forza Motorsport 2023:n radan numero on `lap.trackOrdinal`) | havaittu paketin asettelu | `slip: peak`, `discipline: circuit` | vain läsnä olevien kanavien yksiköt | `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `accelX/Y/Z`, `angVelX/Y/Z`, `drivingLine`, `aiBrakeDifference`, pelin oma kello `timestampMs`, `raceTime`, `bestLap`, `lastLap`; auton paikallinen nopeus on kanonisilla nimillä `latVel`, `vertVel`, `longVel`; `unparsed` kanavien vieressä |
| Assetto Corsa -pelit (`kunos.py`) | staattisesta sivusta tai `null` | puuttuu | `slip: scaled`, `discipline: circuit` tai `rally` | kiinteä lista | `slipRatioRaw.*`, `slipAngleRaw.*`, `packetId`, `steerAngle` (lähetettynä), `worldVelX/Y/Z`, `angVelX`, `angVelZ`, `tcActing`, `absActing`, `wheelSlip.*`, `contactX/Y/Z.*` |
| Rallipelit (`rally.py` `lapfile.py`:n kautta) | `null` | puuttuu | `discipline: rally`, `slip: null`, `surface` vain, kun `--surface` annettiin (muuten katselin päättelee sen) | vain läsnä olevien kanavien yksiköt | `stageDistance`; WRC `gameTime`, `gameDelta`, `packetUid`, `gearIndex`, `transmissionSpeed`, `rpmMax`, `rpmIdle`, `stageLength`, `hubVel.*`, `worldVel/worldAcc/left/forward/up` `X/Y/Z`; DiRT `totalTime`, `lapNumber`, `lapsCompleted`, `totalLaps`, `stageLength`, `lastLapTime`, `suspensionVel.*`, `worldVel/side/forward` `X/Y/Z`, `float<i>` niille liukuluvuille, joille ei ole vakiintunutta nimeä; RBR `attitudeX/Y/Z`, `totalSteps`, `stageIndex`, `progress`, `raceTime`, `distanceToEnd`, `speedRaw`, `accelZ` |
| BeamNG (`beamng.py` `lapfile.py`:n kautta) | `null` | puuttuu | `discipline: circuit` | vain läsnä olevien kanavien yksiköt | `wheelSurfaceSpeedRaw.*`, `wheelMaterial.*`, `forward/up/worldVel` `X/Y/Z` |
| Trackmania-liitännäinen (CSV) | kartan nimi | - | `slip: index`, `discipline: arcade` | - | `respawns` |

`car` on Forzan autolohko (`carOrdinal`, `carClass`, `carPI`, `drivetrain`, `cylinders`,
`rpmMax`, `rpmIdle`), Kunos-peleissä `{"name": ...}`, kun staattinen sivu nimeää auton, ja
muuten `{}`. `lap.metres` on Forzalla pelin matkamittarin erotus ja muualla näytteiden
välinen summattu 3D-etäisyys. Arvot pyöristetään kirjoittaessa: `time` 4 desimaaliin,
`distance` 3 desimaaliin ja muut liukuluvut 5 desimaaliin. JSON kirjoitetaan tiiviinä
(ilman välilyöntejä).

Jokainen paketti tai sivu, jonka tallennin vastaanotti - ei vain kierrosten - säilytetään
kokonaisena kierrostiedostojen vieressä tiedostossa `<stamp>_<game>.raw.parquet`, ja
itsetarkistus on tiedostossa `<stamp>_<game>.summary.json` (README:n osio "Completeness").

Näyte, jolle kanavalla ei ole arvoa - puuttuu kehyksestä tai peli ei lähettänyt äärellistä
lukua - kirjoitetaan jokaisella tallentimella muotoon `null` (`lapfile.clean`), ja siitä
johdettu jousen osuus on myös `null`. `NaN` ja `Infinity` eivät koskaan kirjoitu: ne eivät
ole JSONia, ja selaimen `JSON.parse` hylkää koko tiedoston yhdenkin takia. Lukijan pitää
odottaa `null`-arvoja kanavan taulukossa.

Forza-tiedostoissa on `"game": "forza-horizon"`, `"forza-motorsport"` tai `"forza"` havaitun
asettelun mukaan. Katselimen lukija FH Companionin `.tele.gz`-tiedostoille tuottaa kierroksia,
joissa on `"game": "forza-horizon"` ja `meta.slip = "peak"`; se lukija on katselimessa, ei
täällä. iRacing-kierrokset (luettu `.ibt`-tiedostoista katselimessa) kantavat
`"game": "iracing"`, joka ei ole yllä olevassa luettelossa, koska mikään tallennin ei kirjoita
sitä.

Katso [Kierrosten ja osuuksien jakaminen](lap-splitting.md), miten `lap.number`, `lap.seconds`
ja `lap.complete` päätetään, ja [Luisto, sivuliuku ja johdetut kanavat](slip-and-drift.md),
mitä katselin johtaa näistä kanavista.
