---
title: "Kameran asento ja mittakaava"
nav_order: 4
lang: "fi"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kameran asento ja mittakaava {#camera-pose-and-scale}

Syvyyskartta kertoo, kuinka kaukana asiat ovat *yhdestä* näkökulmasta. Monen sellaisen
muuttaminen yhdeksi tasoksi vaatii tietää, missä kukin näkökulma oli ja missä yksiköissä. Tämä sivu
käsittelee elävät polut; offline-yhdistävä ratkaisu on sivulla [Offline-rekonstruointi](reconstruction-offline.md).

Koodi: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Kameramalli {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` rakentaa reiän kameran ikkunassa asetetusta **vaakasuuntaisesta
näkökentästä**: `fx = (width / 2) / tan(fov / 2)`, neliömäiset pikselit (`fy = fx`), pääpiste kuvan
keskellä. Peli ei julkaise projektiotaan, joten tämä on ainoa oletettu luku: liian kapea, ja kohtaus
näyttää syvemmältä kuin on. Offline-polku käyttää 65 astetta.

`Pose` tallennetaan **maailmasta-kameraan**: `rotation` (3 x 3) ja `translation` = kameran keskipiste
maailmassa, mitä radan, kattavuuskartan ja peittokuvan kaikki haluavat.

## Visuaalinen odometria (oletus) {#visual-odometry-the-default}

`VisualOdometry` seuraa jokaista avainkuvaa edellistä vasten:

1. **Piirteet**: ORB, enintään 1500 kuvaa kohden, havaitaan vain maailmamaskilla (katso
   [Kaappaus](reconstruction-capture.md#what-is-not-the-world)).
2. **Osumat** edelliseen avainkuvaan: raa'a haku, Hamming-etäisyys, ristiintarkistus (vain
   molemmin päin parhaat parit).
3. **Nosto 3D:hen**: edellisen kuvan syvyys on jo maailmayksiköissä, joten sen osuneet pikselit
   muuttuvat maailmapisteiksi.
4. **Kameran paikka**: `solvePnPRansac` näiden pisteiden joukossa (uudelleenprojektiovirhe 3 px,
   luottamus 0,999, 200 iteraatiota). Siirto tulee samoissa yksiköissä, joten **mittakaava ylittää
   välin**.
5. **Tämän kuvan syvyyden ankkurointi**: sen oma ennustettu käänteinen syvyys sovitetaan (`fit_scale`)
   PnP:n sisäpisteiden syvyyksiä vasten, ja kierto toistuu.

**Ensimmäinen kuva** on origo: identiteettiasento, ja sen syvyyden affiini on joko alla oleva
maakalibrointi tai ilman sitä identiteetti (rekonstruointi on silloin sisäisesti yhtenäinen mutta
yksikötön).

Asento tarvitsee vähintään **18 RANSAC-sisäpistettä** - selvästi enemmän kuin PnP:n minimi, kuusi, koska
ratkaisu juuri riittävästä pistemäärästä on täsmälleen se, joka on varmasti väärässä.

### Luottamus {#confidence}

Jokaiselle sijoitetulle kuvalle annetaan luottamus välillä 0..1, joka painottaa sen yhdistämistä ja
kattavuutta:

| Asento tulee | Luottamus |
|---|---|
| telemetria | 1,0 |
| syötteen ratkaisu | 0,85 |
| visuaalinen seuranta | `sisäpisteet / osumat x min(1, sisäpisteet / 60)` |

### Kun seuranta katkeaa {#when-tracking-breaks}

Kuvaa, jota ei voi sijoittaa, raportoidaan eikä arvata: `no features in the frame (N found)`,
`too few matches to place the camera`, `could not relocalise`. Asentoa ei kirjata, eikä mitään yhdistetä.
Viimeisestä asennosta jatkaminen tai uuden origon aloittaminen asettaisi seuraavan kentän osan mielivaltaiseen
siirtymään - saumaan, joka näyttää todelliselta geometrialta.

Katkoksen jälkeen jokainen uusi kuva **paikannetaan uudelleen** menneiden avainkuvien tietokantaa vasten
(joka 4. seurattu kuva lisätään, enintään 120, vanhin pudotetaan), uusin ensin, samalla osumien ja
PnP:n vaiheella. Kunnes yksi onnistuu, kuvat pudotetaan. Palautunut kuva jatkuu samassa koordinaatistossa.
Palautumiset lasketaan ja näytetään ikkunassa (`N recovered`).

### Silmukan sulkeminen: pois päältä {#loop-closure-off}

Sama tietokanta tukee silmukan sulkemista: vertaus paljon aiempiin avainkuviin revisiitin tunnistamiseksi ja
radan kiinnittämiseksi siihen. **Se on oletuksena pois päältä, eikä skanneri koskaan kytke sitä päälle**
(`Reconstructor(loop_closure=False)`). Toistuvassa maisemassa - rallireitti, käytävä, puurivi - jokainen
osuus näyttää kaikilta muilta, ja piirteiden vertailu vahvistaa väärät revisiitit, mikä pitää kameran lähellä
lähtöpistettä, vaikka se ajaisi eteenpäin. Sen kunnollinen tekeminen vaatii paikantunnistuksen (sanasto- tai
oppiva kuvaaja) ja geometrisen todentamisen karttaa vasten, eikä sitä ole rakennettu.

Kun se on käytössä koodista, sulkeminen tarvitsee: avainkuvan, joka on vähintään 60 avainkuvaa vanha, vähintään 6 m
nykyisestä asennosta, sovitettuna vähintään 90 sisäpisteellä, ja joka siirtää asentoa yli 0,02 m mutta alle 6 m.
Silloinkaan se vain korvaa nykyisen asennon; se ei ole asentograafi eikä siirrä aiempia kuvia tai sulautettua
geometriaa.

## Telemetriasta asennot {#telemetry-poses}

Kun **Racing telemetry (Forza) -> Listen for position data** on päällä, kameran polku tulee Forzan Data Outista
kuvien sijasta (`ForzaPoseSource`):

- Säie kuuntelee osoitetta `127.0.0.1:<port>` (oletus 5300) samalla kerrostunnistuksella kuin tallentimet
  ([Forza](telemetry-forza.md)); paketteja käytetään, kun `isRaceOn` on asetettu. Varattu portti ilmoitetaan,
  ei nosteta virheeksi: telemetria on päivitys, ja skannaus jatkuu visuaalisesti.
- Jokainen paketti leimataan **monotonisella ajalla, jolloin se saapui** - samalla kellolla, jolla kaappaus
  leimaa kuvat. Pelin oma aikaleima laskee jostain muusta, joten sitä ei käytetä kohdistukseen. Muutaman
  millisekunnin silmukkavärinä on noin 6 cm 200 km/h nopeudella.
- Puskuri pitää viimeiset 30 sekuntia. Kuvan asento **interpoloidaan** näytteistä kuvan kaappausajan
  kummallakin puolella: sijainti lineaarisesti, kierto pallomaisesti (sekoitettu matriisi ei ole kierto ja
  vääristäisi jokaisen pisteen). Yli **0,35 s** aukon yli tai puskurin ulkopuolella ei ole asentoa.
- `pose_from_forza`: kamera sijoitetaan auton kohdalle (takakameran siirtymää ei julkaista). **Sijainnit
  säilytetään täsmälleen niin kuin peli ne lähettää**: Forzan maailma on jo Y ylös (x ja z kartan poikki, y
  korkeus), ja se on tapa, jolla radat ja reitit kirjoitetaan, joten pinta osuu samoihin koordinaatteihin kuin
  sen päälle tallennetut kierrokset. (Aiempi versio vaihtoi y:n ja z:n "Z-ylös"-maailmalle ja makasi radan
  kyljellään.)
- Kierto on yaw, sitten pitch, sitten roll, ja merkitykset on luettu tallennetuista kierroksista: ajosuunta
  `atan2(dx, dz)` on yhtä kuin yaw, nousun kulma on yhtä kuin miinus pitch (positiivinen on nokka alas), ja roll on
  positiivinen, kun oikean puolen jousitus on puristunut (positiivinen laskee oikean puolen). Auton akselit (x
  oikealle, y ylös, z eteen) käännetään kameran akseleiksi (x oikealle, y alas, z eteen) kääntämällä y.
- Forzan maailma on **vasenkätinen** ja kameran kehys ei ole, joten tuloksena oleva maailmasta-kameraan-matriisi
  on heijastus (determinantti -1), ja skannaus tulee ulos vasenkätisenä kuten kierrostiedostot. Interpolointi ei
  muutu (kahden tällaisen asennon välinen käännös on oikea kierto).
- Kun kehykselle ei ole telemetria-asentoa (aukko), rekonstruoija palaa **visuaaliseen seurantaan** kyseiselle
  kehykselle jatkaen viimeisestä telemetria-asennosta, ja palaa syötteen asentoihin heti, kun ne taas tulevat.
  PnP palauttaa vain kiertoja, joten peilautuneessa maailmassa se ratkaistaan peilaamalla maailma z:n yli ja
  kääntämällä peilaus takaisin; kehys osuu pelin koordinaatteihin. Vain jos visuaalinen seuranta epäonnistuu
  myös, kehys on seuraamaton.

### Syvyyden mittakaava telemetriasta {#depth-scale-from-telemetry}

Peli kertoo, missä kamera on, ei kuinka kaukana kaikki on, joten jokaisen kehyksen syvyys täytyy silti
ankkuroida - mutta ei ketjuttamalla nollasta kehyksestä, jonka yksikkö on mielivaltainen, kun asennot ovat
metreissä. Sen sijaan piirteet, jotka täsmäävät edellisen ja nykyisen kehyksen välillä (vähintään 8), **kolmiomitataan
suoraan kahdesta tunnetusta asennosta** metreissä, ja syvyyskartta sovitetaan kameran edessä oleviin pisteisiin.
Jokainen kehys ankkuroidaan telemetriaa vasten, joten ketjua ei ole, joka ajautuisi.

Jos kaksi asentoa ovat alle **0,05 m** päässä toisistaan, säteet ovat lähes yhdensuuntaisia ja kolmiomittaus on
kohinaa, joten kehys jää ankkuroimatta: täsmälleen sijoitettu, mutta ei yhdistetty ("positioned, but its depth has
no scale yet"). Siksi ikkuna laskee *sijoitetut* ja *yhdistetyt* kehykset erikseen.

## Mittakaava {#scale}

Visuaalinen odometria ketjuttaa suhteellisen mittakaavan oikein, mutta koko kenttä kelluu yhden tuntemattoman
kertoimen varassa. Depth Anythingin suhteellinen tulos tulee mielivaltaisissa yksiköissä, joten jos ensimmäinen
kuva jätetään identiteetiksi, maailma on metrien sisällä kamerasta mielivaltaisessa koossa.

`GroundCalibrator` kiinnittää tämän kertoimen sen perusteella, **kuinka korkealla kamera on maasta**, mitattuna
**ensimmäisestä avainkuvasta** ja, kun sillä ei ole käyttökelpoista maata, sitä seuraavista:

- Kameran korkeus: **1,15 m** (kuljettajan silmänkorkeus) - ikkuna käyttää aina tätä; skriptit voivat antaa
  1,70 m (`WALKING_HEIGHT`, seisova pelaaja) tai `None` (ei kalibrointia).
- Maanäyte: rivit 62-92 % kuvan korkeudesta (horisontin alla, konepellin tai aseen yläpuolella) ja sarakkeet
  30-70 % leveydestä (poissa reunoilta).
- Jokainen pikseli siellä, jolla on käyttökelpoinen ennuste, nostetaan syvyydellä `1 / predicted` verkon
  yksiköissä; optisen akselin alapuoliset pisteet antavat korkeuden kameran alapuolella. Niiden mediaani on
  kameran korkeus verkon yksiköissä, joten `metres per unit = 1.15 / median`, ja kehyksen affiini on
  `scale = 1 / metres_per_unit`, siirto 0.
- Luotetaan vain, kun maanäytteitä on vähintään 200 ja **hajonta** (mediaaniabsoluuttinen poikkeama jaettuna
  mediaanilla) on alle **0,60**.
- Ensimmäisessä avainkuvassa sovitus tulee origon yksiköksi, joten skannaus on metreissä alusta alkaen. Kun
  ensimmäisessä avainkuvassa ei ole käyttökelpoista maata, skannaus alkaa yksikötönä ja jokainen myöhempi
  seurattu avainkuva yritetään, enintään **30 kehystä** yhteensä. Ensimmäinen, joka kalibroituu, antaa *metriä
  per yksikkö*: maa-alueen mediaani niiden syvyyksien yli, jotka maa antaa, jaettuna ketjun antamalla syvyydellä
  kyseiselle kehykselle. Kaikki jo yhdistetty on ensimmäisen kehyksen yksikössä, joten kerrointa ei syötetä takaisin
  ketjuun; se sovelletaan koko kenttään (ja merkittyihin kohtiin) kirjoitettaessa ja näytettävään etäisyyteen
  sillä välin. Voxelin koko on silloin ensimmäisen kehyksen yksiköissä, joten sen koko metreissä eroaa asetuksesta
  tuon kertoimen verran.
- 30 kehyksen jälkeen ilman maata skannaus pysyy yksikkötönä ja sanoo niin.
- Telemetrian kanssa myöhempiä avainkuvia ei yritetä: syvyys ankkuroidaan telemetrian metreihin.

Olla kymmenen prosentin päässä todellisesta koosta on parempi kuin olla tuhannen kertoimen päässä; telemetria
tekee tästä tarpeettoman, kun se on saatavilla. Huomautus näkyy ikkunassa seurannan rivin alla muodossa
`Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`,
`scaled from a 1.15 m camera height, ...` (kun se tuli myöhemmin, `found on frame N, so the level is scaled by F
when it is written`), `no usable ground in the first N frames - sizes are relative, not metres`, tai
`in metres, from the telemetry's positions`.

## Kimppasäätö ja pitkät radat (ei kytketty) {#bundle-adjustment-and-long-tracks-not-wired-in}

Kaksi osaa on olemassa tulevaa ikkunoitua ratkaisijaa varten, eikä **skanneri käytä niitä**:

- **`FeatureTracks`** säilyttää piirteiden identiteetin satojen kuvien yli Lucas-Kanade-seurannalla (600
  piirrettä, kylvetään uudelleen alle 60 %:n kohdalla, eteen-taakse-toleranssi 1 px, uudet piirteet 10 px:n
  päässä olemassa olevista), mitä kimppasäätö tarvitsee - peräkkäisten kuvien piirteiden vertailu antaa vain pareja.
- **`bundle_adjust`** tarkentaa kuvaikkunan asentoja ja pisteitä yhdessä `scipy.optimize.least_squares`-funktiolla
  (luottamusalue, soft-L1-häviö 2 px:n skaalalla, eksplisiittinen Jacobin harvuusrakenne, kiinteät kamerat
  palautettu tarkasti). Testattu tunnettua totuutta vastaan tiedostossa `tests/test_bundle.py`.

`WindowedOdometry` yhdistää ne (12 avainkuvan ikkunat, ratkaisu joka 3. avainkuvalla, kaksi ensimmäistä kameraa
kiinteinä, yli 6 px:n virheen pisteet pudotetaan, yli 6-kertaiset viimeaikaisen askeleen hypyt hylätään). Sen
docstring kirjaa, että oikealla kuvamateriaalilla se **romahdutti polun ja oli paljon hitaampi** kuin kehys
kehykseltä -seuranta, ja tunnettuina syinä mainitaan mittakaavan vapaus (gauge freedom) ja syvyyspohjainen
käynnistys, sekä kolmas syy, jota ei ole tunnistettu. Frame-to-frame-odometria pysyy siis oletuksena; koodin
mainitsema todennäköinen korjaus on kahden näkymän olennaismatriisin käynnistys, jonka kantaväli on kiinnitetty
maatasokalibroinnista.
