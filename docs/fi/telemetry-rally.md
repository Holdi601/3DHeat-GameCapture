---
title: "Rallipelit"
nav_order: 3
lang: "fi"
source: telemetry-rally.md
source_hash: "f7b3236cdfc9"
nav_exclude: true
search_exclude: true
---
# Rallipelit {#ea-sports-wrc-dirt-rally-20--dirt-rally--dirt-4-richard-burns-rally}

```bash
python -m heat3d_capture telemetry --game wrc --configure "%USERPROFILE%\Documents\My Games\WRC\telemetry\config.json" -o laps
python -m heat3d_capture telemetry --game dirtrally2 -o laps     # tai dirtrally, dirt4
python -m heat3d_capture telemetry --game rbr -o laps
python -m heat3d_capture telemetry --game wrc -o laps --surface tarmac
```

Koodi: [`telemetry/rally.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/rally.py),
[`telemetry/lapfile.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/lapfile.py).
Testit: `tests/test_rally.py`, dokumentoiduista asetteluista tehdyillä paketeilla. **Ei vielä ajettu oikeita pelejä vastaan.**

Kaikki lähettävät UDP:tä, jonka peli kytkee päälle omista asetustiedostoistaan. Tallennin kuuntelee kaikkia liittymiä
(`0.0.0.0`) pelin oletusportissa, ellei `--port` anna toista: **20777** `wrc`:lle, `dirtrally2`:lle, `dirtrally`:lle ja
`dirt4`:lle; **6776** `rbr`:lle.

## EA SPORTS WRC {#ea-sports-wrc}

### Käynnistys {#switching-it-on}

Peli lukee tiedostoa `Documents\My Games\WRC\telemetry\config.json`. Oletus-`wrc`-rakenteen `session_update`-paketti täytyy
kytkeä päälle tälle koneelle:

```bash
python -m heat3d_capture telemetry --game wrc --configure "<path to config.json>"
```

`--configure` (funktio `configure_wrc`):

- lukee JSONin, etsii kohdan `udp.packets` ja merkinnän, jossa `"structure": "wrc"` ja `"packet": "session_update"`;
- jos se on jo kytketty `127.0.0.1`- tai `localhost`-osoitteeseen käytetyllä portilla, tulostaa `already on` eikä muuta mitään;
- muuten asettaa `"ip": "127.0.0.1"`, `"port": <port>`, `"bEnabled": true` ja säilyttää merkinnän `frequencyHz`-arvon (tai `-1`, jos
  sitä ei ole); jos merkintää ei ole, se lisätään;
- kirjoittaa alkuperäisen tekstin `config.json.bak`-tiedostoon sen viereen ja kirjoittaa sitten uuden tiedoston (4 välilyönnin sisennys).

Käynnistä peli uudelleen tiedoston muuttamisen jälkeen, jos se ei huomaa muutosta (ei tarkistettu).

### Mitä se lähettää {#what-it-sends}

Oletus-`wrc`-rakenne on 237 tavua, little-endian, ilman otsikkoa: maailman sijainti, nopeus ja kiihtyvyys (X vasemmalle,
Y ylös, Z eteenpäin), auton vasen/eteen/ylös-yksikkövektorit, renkaittain (takavasen, takaoikea, etuvasen, etuoikea) pyörän
keskiön korkeus ja pystynopeus sekä kosketuspisteen eteennopeus, jarrujen lämpötilat, pedaalit avustusten jälkeen, ohjaus
(-1 vasen, +1 oikea), käsijarru, rpm, vaihde sekä osuuskello, matka ja pituus. Alle 237 tavun paketti jätetään huomiotta ja
ilmoitetaan kerran.

| Kanava | Lähde |
|---|---|
| `x`, `y`, `z` | maailman sijainti |
| `speed` | `speed` |
| `longVel`, `latVel`, `vertVel` | maailman nopeus projisoituna eteen, miinus vasen (joten positiivinen on oikealle), ylös |
| `longAcc`, `latAcc`, `vertAcc` | maailman kiihtyvyys projisoituna samalla tavalla |
| `yaw` | `atan2(forward.x, forward.z)` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer` | sellaisenaan |
| `gear` | `gear_index`; -1, kun se on sama kuin peruutusindeksi, 0, kun se on sama kuin vapaaindeksi |
| `rpm` | `rpm` |
| `stageDistance` | `stage_distance` |
| `suspensionM.*` | keskiön sijainti |
| `wheelSurfaceSpeed.*` | kosketuspisteen eteennopeus |
| `brakeTemp.*` | jarrun lämpötila |

Tarkistus: jos `speed` on yli 10 ja maailman nopeusvektorin pituus eroaa siitä yli 20 %, tallennin tulostaa kerran, että
asettelu ei ehkä ole oletus-`wrc`-rakenne.

Osuus on **maalissa**, kun osuuden pituus on positiivinen ja matka on saavuttanut pituuden miinus 0,5 m. Jakamiseen ja `time`-kenttään
käytetty kello on `stage_time`.

Lähteet: EA:n UDP Telemetry Guide v1.3; kanavaluettelo, jonka peli kirjoittaa tiedostoon `readme/channels.json`; offsetit, kuten
nobonobo/obs-codemasters-telemetry ja SpaceMonkey ne ovat purkaneet. Oletusporttia ei ole dokumentoitu; tallennin käyttää 20777:ää.

## DiRT Rally 2.0, DiRT Rally, DiRT 4 {#dirt-rally-20-dirt-rally-dirt-4}

### Käynnistys {#switching-it-on-1}

Muokkaa tiedostoa `Documents\My Games\DiRT Rally 2.0\hardwaresettings\hardware_settings_config.xml` (DiRT Rally ja DiRT 4
käyttävät myös tiedostoa `hardware_settings_config.xml`; niiden tarkkaa kansiota ei ole tarkistettu tässä) niin, että
`udp`-elementti kuuluu:

```xml
<udp enabled="true" extradata="3" ip="127.0.0.1" port="20777" delay="1" />
```

`extradata="3"` on se, mikä laittaa sijainnit, pyörät ja osuuden pituuden pakettiin. Tallennin ei muokkaa tätä tiedostoa.

### Mitä se lähettää {#what-it-sends-1}

66 little-endian-liukulukua (DiRT Rally: 64); alle 64 liukuluvun paketit jätetään huomiotta, ja 64 liukuluvun paketti täydennetään
nollilla. Käytetyt indeksit:

| Indeksi | Kenttä | Kanava |
|---|---|---|
| 1 | osuuden (kierroksen) aika | jakamisen kello ja `time` |
| 2 | kierrosmatka | `stageDistance` |
| 4-6 | maailman sijainti | `x`, `y`, `z` |
| 7 | nopeus | `speed` |
| 8-10 | maailman nopeus | `longVel` (eteen), `latVel` (sivuvektorilla) |
| 11-13 | sivuvektori | |
| 14-16 | eteenpäin-vektori | `yaw = atan2(forward.x, forward.z)` |
| 17-20 | jousituksen asema TV TO TV OO... RL RR FL FR | `suspensionM.*` |
| 25-28 | pyöräkosketuksen nopeus RL RR FL FR | `wheelSurfaceSpeed.*` |
| 29-33 | kaasu, ohjaus, jarru, kytkin, vaihde | `throttle`, `steer`, `brake`, `clutch`, `gear` (10 tai enemmän tarkoittaa peruutusta, kirjoitetaan -1:ksi) |
| 34, 35 | sivu- ja pituus-g | `latAcc`, `longAcc` (kerrottuna 9,80665:llä) |
| 37 | rpm / 10 | `rpm` (kerrottuna 10:llä) |
| 51-54 | jarrujen lämpötilat | `brakeTemp.*` |
| 59, 60, 61, 62 | suoritetut kierrokset, kierrosten määrä, radan pituus, viimeisen kierroksen aika | jakaminen |

**Käsijarrukanavaa ei ole.** Sivuvektorin suunta on dokumentoitu molempiin suuntiin, joten `latVel`:n merkkiin ei voi luottaa
(katselin lukee sivuliukukulman suuruuden).

Osuus on **maalissa**, kun suoritettujen kierrosten määrä nousee sen alkuarvon yläpuolelle (rallicross-kierros aina, kun se
tapahtuu), tai yhden kierroksen tapahtumassa, kun kierrosmatka saavuttaa 99,9 % radan pituudesta. Osuuden aika on pelin viimeinen
kierrosaika, kun se on positiivinen. Tarkistus: nopeutta vastaan verrattu nopeus kuten EA WRC:ssä, viestillä "is extradata set to 3?".

Lähteet: Codemasterin DiRT 4 UDP -dokumentti; ErlerPhilipp/dr2_logger; soong-construction/dirt-rally-time-recorder.

## Richard Burns Rally (RSF / NGP) {#richard-burns-rally-rsf--ngp}

### Käynnistys {#switching-it-on-2}

Tiedostossa `RichardBurnsRally.ini`, osiossa `[NGP]`: `udpTelemetry=1` ja päätepiste (127.0.0.1, portti 6776, ellei annettu
toista `--port`-arvoa). Tallennin ei muokkaa tätä tiedostoa.

### Mitä se lähettää {#what-it-sends-2}

664 tavua (`Plugins/NGP/sdk/rbr.telemetry.data.TelemetryData.h`): osuuskello ja matka loppuun, pedaalit, ohjaus, vaihde, maailman
sijainti, asento, auton omat nopeudet (eteen, sivuttain, pysty), kiihtyvyydet, rpm sekä neljä 128 tavun pyöräohjainlohkoa (LF, RF,
LB, RB) jousen painumalla ja jousivoimalla. Ei pyörien nopeuksia.

| Kanava | Lähde |
|---|---|
| `x`, `y`, `z` | sijainti, akselit sellaisina kuin ne lähetetään, sitten järjestettynä uudelleen (alla) |
| `longVel`, `latVel`, `vertVel` | eteen-, sivu- ja pystynopeus |
| `longAcc`, `latAcc` | kiihtyvyys x, y |
| `throttle`, `brake`, `handbrake`, `clutch`, `steer` | sellaisenaan |
| `gear` | `gear - 1` (0 peruutus, 1 vapaa, 2 ensimmäinen) |
| `rpm` | `rpm` |
| `stageDistance` | `drive_line` |
| `suspensionM.*` | jousen painuma |
| `wheelLoad.*` | jousivoima |
| `speed` | **lasketaan sijainneista** ±2 näytteen yli, ei oteta paketista |

RBR:n sijaintiakselit, asennon yksiköt ja nopeusyksikkö eivät ole dokumentoituja, joten kun osuus kirjoitetaan: akseli, jonka
suhteen osuus vaihtelee vähiten, otetaan ylöspäin ja vaihdetaan kohtaan `y` (`orient_up`, tarvitsee vähintään 10 näytettä), ja
nopeus lasketaan uudelleen sijainneista (`speed_from_positions`). Asentoa ei kirjoiteta, vaan se dekoodataan, joten RBR-tiedostoissa
ei ole `yaw`-kenttää.

Osuus on **maalissa**, kun kilpakello käy ja matka loppuun on saavuttanut nollan. Kello on `race_time`.

Lähteet: NGP:n `rbr.telemetry.data.TelemetryData.h`, mika-n/RBRUDPTelemetryLogger ja groybe/rbr-udp-telem kautta.

## Osuudet {#stages}

Kaikki viisi käyttävät `StageSplitter`ia pelin osuuskellolla: osuus avautuu, kun kello käynnistyy, ja sulkeutuu päätettynä, kun
peli sanoo auton olevan maalissa. Kello, joka menee taaksepäin (uudelleenkäynnistys tai seuraava osuus), hylkää avoimen osuuden - se
säilytetään `_partial`-tiedostona, jos siinä on yli 10 näytettä ja vähintään 300 m. Päätettyjä alle 300 m pituisia osuuksia ei kirjoiteta.
Yksityiskohdat: [Kierrosten ja osuuksien jakaminen](lap-splitting.md).

## Kierrostiedosto {#the-lap-file}

`game` on `ea-sports-wrc`, `dirt-rally-2`, `dirt-rally`, `dirt-4` tai `richard-burns-rally`.
`meta` on `{"discipline": "rally", "slip": null}`, ja lisäksi `"surface": "<value>"`, kun `--surface` annettiin. `slip` on null, koska
mikään näistä peleistä ei lähetä renkaiden luistoa. Sen sijaan tiedostoon tulee kunkin pyörän kosketuspisteen nopeus (EA WRC, DiRT), ja
katselin johtaa luiston ja sivuliukukulman siitä ja auton akseleista; katso [Luisto, sivuliuku ja johdetut kanavat](slip-and-drift.md).
Kanavat `suspension.*` (0..1 käytetystä matkasta) lisätään kohdasta `suspensionM.*`.

Kun `--surface`-valintaa ei anneta, tiedostossa ei ole pintatietoa lainkaan, tarkoituksella: tässä kirjoitettu oletus ohittaisi katselimen
oman päätelmän. Katselin päättelee pinnan silloin osuuden tai tapahtuman nimestä (asfalttirallit, talviset, Monte mixed-tyyppisenä),
muuten siitä, miten autoa on ajettu siinä (kova kaarteiden ajo pienillä sivuliukukulmilla on asfalttia), ja löysä, kun mikään ei kerro -
mitä rallin osuus useimmiten on. Anna `--surface`, kun tiedät paremmin.
