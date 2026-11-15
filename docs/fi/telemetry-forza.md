---
title: "Forza"
nav_order: 1
lang: "fi"
source: telemetry-forza.md
source_hash: "7596c02db7f2"
nav_exclude: true
search_exclude: true
---
# Forza Horizon ja Forza Motorsport {#forza-horizon-and-forza-motorsport}

```bash
python -m heat3d_capture telemetry -o laps                            # peli -> 5300
python -m heat3d_capture telemetry -o laps --forward 127.0.0.1:5301   # ja FH Companion toimii yhä
```

Koodi: [`telemetry/forza.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/forza.py)
(asettelun tunnistus),
[`telemetry/fulllap.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fulllap.py)
(jokainen kanava, kierrostiedostot, välitys).

## Käynnistys pelissä {#switching-it-on-in-the-game}

**Settings -> HUD and Gameplay -> Data Out**: `ON`, IP `127.0.0.1`, portti `5300` (tai mikä tahansa annat
`--port`-valinnalla). Forza Motorsport tarjoaa myös pakettimuodon: sen täytyy olla **Dash**, ei Sled. Sled ei kanna
lainkaan sijaintia, ja tallennin kieltäytyy siitä.

Tallennin sitoutuu osoitteeseen `127.0.0.1`, joten pelin täytyy käydä samalla koneella.

## Mitä peli lähettää ja miten asettelu löydetään {#what-the-game-sends-and-how-the-layout-is-found}

Data Out on yksi UDP-paketti simulaatiotikkiä kohden (noin 60 sekunnissa), litteä little-endian C-rakenne näissä
koissa:

| Pituus | Variantti |
|---|---|
| 232 tavua | Motorsport "Sled": ei sijaintia. Hylätään viestillä, joka kehottaa vaihtamaan Dashiin. |
| 311 tavua | Motorsport "Dash": Sled-lohko plus 79 tavun dash-lohko |
| 324 tavua | Horizon "Dash": sama, kahden lohkon välissä täytetavuja |
| 331 tavua | Forza Motorsport (2023): Dash plus 20 tavua renkaiden kulumista ja radan tunnus |

Sled-lohko (offsetit 0-231) on vakaa. Missä dash-lohko alkaa Horizon-variantissa, kuvataan julkaistuissa
lähteissä ristiriitaisesti, ja väärän arvauksen tekeminen ei kaadu - se tuottaa uskottavia liukulukuja vääristä
kentistä. Siksi alku **selvitetään**:

1. Ehdokasalut kokeillaan järjestyksessä: `length - 79` (dash-lohko päättyy viimeiseen tavuun jokaisessa
   dokumentoidussa variantissa), 232, 244, ja 232:sta 260:een askeleilla 4.
2. Jokainen ehdokas pisteytetään liikkuvan auton paketeilla (nopeuskomponentti yli 1 m/s): Sled-lohkon nopeusvektori
   ja dash-lohkon skalaarinen `Speed` ovat sama suure kahdessa paikassa, joten `| |velocity| - Speed |` on lähellä
   nollaa vain oikealla alulla.
3. Ehdokas, jonka pahin erimielisyys on pienin, voittaa, jos erimielisyys on enintään **1 m/s**. Muuten tunnistus
   jatkaa odottamista.

Auton ollessa pysäköity jokainen ehdokas lukee nollia ja kaikki täsmäävät, mikä ei todista mitään, joten **tunnistus
odottaa, kunnes auto liikkuu**: aja muutama metri ennen kuin odotat tulosta. Odottaessa pidetään enintään 600 pakettia
(karsittuna viimeisiin 300:aan). Kun asettelu on tiedossa, pidetyt paketit dekoodataan myös, joten ensimmäisen kierroksen
alku ei katoa. Muun pituiset paketit kuin tunnistettu asettelu, alle 311 tavun paketit ja ei-äärelliset sijainti- tai
nopeusarvot jätetään pois kierrostiedostoista.

Mikä Forza on, seuraa asettelusta: Horizon-asettelu antaa `"game": "forza-horizon"`, Motorsport- tai 331 tavun asettelu
`"forza-motorsport"` ja muut `"forza"`. Tunnistetun asettelun nimi (`Horizon dash`, `Motorsport dash`, `331-byte dash`)
kirjoitetaan kenttään `layout`.

## Kirjatut kanavat {#channels-recorded}

Jokainen paketin kenttä dekoodataan (`decode_full`) ja muunnetaan:

- pedaalit `throttle`, `brake`, `clutch`, `handbrake` arvosta 0..255 arvoon 0..1;
- `steer` arvosta -127..127 arvoon -1..1; `drivingLine` ja `aiBrakeDifference` samoin jaettuna 127:llä;
- `tireTemp.FL` ... `.RR` Fahrenheitista Celsiukseen;
- `latAcc`, `longAcc`, `vertAcc` ja `yawRate` ovat kopioita kentistä `accelX`, `accelZ`, `accelY` ja `angVelY` kanonisilla
  nimillä (auton kehys: x oikealle, y ylös, z eteen);
- Sled-nopeus, joka on auton omassa kehyksessä (x oikealle, y ylös, z eteen - ei maailman), kirjoitetaan suoraan kanonisilla
  nimillä `latVel`, `vertVel` ja `longVel`, joten katselin lukee sivuliukukulman siitä sen sijaan, että arvioisi sen suunnasta ja
  polusta.

Kierrostiedoston kanavat ovat kaikki nämä paitsi kierroskohtaiset kentät:

| Ryhmä | Kanavat |
|---|---|
| Aika ja paikka | `time`, `distance`, `x`, `y`, `z`, `distanceTravelled`, `currentLap`, `lapNumber`, `racePosition`, `timestampMs`, `raceTime`, `bestLap`, `lastLap` |
| Liike | `speed`, `yaw`, `pitch`, `roll`, `accelX/Y/Z`, `latVel`, `vertVel`, `longVel`, `angVelX/Y/Z`, `latAcc`, `longAcc`, `vertAcc`, `yawRate` |
| Moottori | `rpm`, `power` (W), `torque` (N m), `boost`, `fuel` |
| Kuljettaja | `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `gear`, `drivingLine`, `aiBrakeDifference` |
| Renkaittain (`.FL .FR .RL .RR`) | `suspension` (0 venynyt .. 1 puristunut), `suspensionM` (m), `slipRatio`, `slipAngle`, `combinedSlip` (normalisoitu: yli 1 tarkoittaa, että rengas päästää irti), `wheelSpeed` (rad/s), `rumble` (tärisyttävällä reunakivellä), `surfaceRumble`, `puddle` (0..1), `tireTemp` (°C) |
| Vain Forza Motorsport 2023 | `tireWear.FL` ... `.RR` |

`time` on pelin nykyisen kierroksen ajastin miinus sen arvo kierroksen ensimmäisellä näytteellä; `distance` on pelin
ajettu matka miinus sen ensimmäinen arvo. Sijainnit ovat Forzan maailmakoordinaatteja metreinä, muuttamattomina (y on
ylös; maailma on vasenkätinen).

Kerran kierrosta kohden, näytteen sijaan, kirjataan kohdan `car` alle: `carOrdinal`, `carClass`, `carPI`, `drivetrain`,
`cylinders`, `rpmMax`, `rpmIdle`. FM2023:n radan tunnus menee kerran myös kenttään `lap.trackOrdinal`. Ei näytekohtaisesti
tallenneta: `isRaceOn` (1 jokaisessa kierroksen kuvassa). `timestampMs`, `raceTime`, `bestLap` ja `lastLap` säilytetään kanavina.

Loppu tiedostosta täytetään kuten muiden tallentimien:

- `"track": null` - Forza Horizon ei nimeä rataa, ja Forza Motorsport vain numeroi sen;
- `"meta": {"slip": "peak", "discipline": "circuit"}` - luistokanavat on normalisoitu niin, että yli 1 tarkoittaa, että
  rengas päästää irti;
- `units` luettelee vain ne kanavat, jotka tiedostossa on (renkaittain olevat nimensä perusnimellä);
- arvo, joka ei ole äärellinen luku, kirjoitetaan muodossa `null`, ei koskaan `NaN`.

Katso [heat3d-lap-tiedosto](lap-format.md).

## Miten kierrokset jaetaan {#how-laps-are-split}

`LapSplitter` (katso [Kierrosten ja osuuksien jakaminen](lap-splitting.md)): kierros sulkeutuu, kun pelin kierroslaskuri
siirtyy eteenpäin, ja sen aika on silloin pelin oma `lastLap` (se, minkä peli näyttää). Pistemäinen kilpa tai istunto, joka
päättyy kesken kierroksen, sulkeutuu, kun peli poistuu kilpailusta (`isRaceOn` putoaa), kun paketit pysähtyvät 2 sekunniksi
tai kun pelin aikaleima hyppää taaksepäin; se säilytetään `run`-kierroksena, jos se kattoi vähintään 400 m.

## Välitys FH Companionille {#relaying-to-fh-companion}

Peli lähettää Data Outin vain yhteen osoitteeseen. Kun annat `--forward host:port`, tallennin välittää **jokaisen vastaanottamansa
paketin muuttumattomana**, ennen kuin dekoodaa mitään (myös silloin, kun se vielä odottaa asettelun tunnistusta), joten toinen
syötettä lukeva sovellus toimii yhä: aseta peli porttiin 5300, toinen sovellus porttiin 5301 ja aja `--forward 127.0.0.1:5301`.

FH Companion on erillinen sovellus, ei osa 3DHeatia. Se pitää kierroskirjastoa kansiossa `%LOCALAPPDATA%\FHCompanion\laps`:
kansio per rata, yksi kierrostiedosto per kierros, otettuna noin joka viiden metrin välein, ja jokaisen kierrostiedoston
vieressä `<lap>.json.tele.gz`, kierroksen koko Data Out pelin nopeudella. 3DHeat lukee molemmat:

- **Katselin lukee `.tele.gz`-tiedostot suoraan**, kun pudotat ne (joko yksinään tai kierrostiedoston kanssa) Kisa-analyysi-välilehdelle.
  Se kuvaa Forzan omat kenttänimet (`PositionX`, `VelocityX`, `TireSlipRatio` + pyörä, ...) kanonisille kanaville, muuttaa auton
  paikalliset `VelocityX/Y/Z` arvoiksi `latVel`, `vertVel`, `longVel`, muuntaa renkaiden lämpötilat Fahrenheitista, pudottaa rivit,
  jotka toistavat edellisen rivin paitsi tallentimen kellon osalta, ja merkitsee luiston arvoksi `peak`. Kun kierrostiedosto on myös
  annettu, kierros ottaa auton ja kierrosajan sieltä. Tämä lukija on katselimessa (`src/race/adapters.ts`, `readForzaTelemetry`),
  ei tässä repositoriossa.
- **`laps`-komento** lukee kierroskirjaston ja kirjoittaa radan reitin ja CSV:n jokaisesta näytteestä; katso
  [Komentoviite](commands.md#laps).

## Muut käytöt samalle syötteelle {#other-uses-of-the-same-feed}

- `python -m heat3d_capture route` tallentaa vain sijainnit, tallennettuna pari sekuntia välein ajon aikana; katso
  [Komentoviite](commands.md#route).
- Skannausikkunan "Racing telemetry (Forza)" -valinta käyttää syötettä tarkkoina kameran asentoina rekonstruointiin; katso
  [Kameran asento ja mittakaava](reconstruction-pose.md#telemetry-poses).

## Huomautukset ja varoitukset {#notes-and-caveats}

- Mihin Forza normalisoi luistonsa, ei ole dokumentoitu. `1` luetaan pidon reunaksi, mutta katselin mittaa, missä kunkin auton
  pito todella heikkenee.
- Sled-nopeus on auton paikallinen, kuten Forzan Data Out -dokumentaatio sanoo ja tallennetut kierrokset vahvistavat (sen
  etukomponentti kantaa nopeuden, sivusuuntainen pysyy lähellä nollaa). Asettelun tunnistus käyttää vain sen pituutta, joka on
  sama missä tahansa kehyksessä.
- Sijainnit ovat pelin maailmaa, Y ylös ja vasenkätinen. `yaw`, `pitch` ja `roll` merkitykset tarkistettiin tallennetuilla kierroksilla:
  yaw on yhtä kuin ajosuunta `atan2(dx, dz)`, positiivinen pitch on nokka alas, ja positiivinen roll laskee oikean puolen.
