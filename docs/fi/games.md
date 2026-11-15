---
title: "Pelit: tallennus ja radat"
nav_order: 4
lang: "fi"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Pelit: tallennus ja radat {#games-recording-and-courses}

Miten jokainen tuettu peli tallennetaan, mitä se lähettää ja mitkä sen radoista
voidaan viedä pelin omista tiedostoista.

Säännöt ovat samat jokaiselle pelille: rata tulee käyttäjän omista tiedostoista
tai rakennetaan käyttäjän omasta pelaamisesta. Salatut arkistot avautuvat vain
avaimella, jonka käyttäjä jo hallitsee - tässä ei toimiteta avaimia eikä
palauteta niitä, eikä mitään injektoida pelin prosessiin. Telemetria tulee vain
niiden rajapintojen kautta, jotka pelit itse julkaisevat (UDP-ulostulot, jaettu
muisti, niiden oma modi- ja liitännäisrajapinta). Mihin työkaluihin käyttäjä
osoittaa, on edelleen kyseisen pelin lisenssin alainen.

## Telemetria {#telemetry}

Jokainen peli päätyy `heat3d-lap`-tiedostoiksi ([`lap-format.md`](lap-format.md)).
Kanavien nimet ovat yhtenäiset, ja `meta`-lohko kertoo, mitä lukemat tarkoittavat:
miten luisto on skaalattu, onko kyse radasta, rallista vai arcade-ajosta, ja pinnan,
kun se tiedetään. Lukija käsittelee kaikkia niitä samalla tavalla. Kaikki komennot
ovat muotoa `python -m heat3d_capture ...` tässä repositoriossa.

| Peli | Miten tallennetaan | Sijainti | Renkaat ja luisto | Sivuliukukulma | Tila |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out UDP:nä: `heat3d_capture telemetry` (välittää FH Companionille) - tai FH Companionin oma `.tele.gz` jokaisen kierroksen vieressä, ladattuna kierrostiedoston mukana | maailman XYZ | luistosuhde, luistokulma ja yhdistetty luisto renkaittain, normalisoitu; pinnan tärinä | auton kehysvektorin nopeus | tallennin testattu; `.tele.gz`-lukija tarkistettu oikeilla kierroksilla |
| Forza Motorsport (2023 mukaan lukien) | sama; erotetaan paketin pituudesta | maailman XYZ | sama | sama | tallennin testattu |
| Assetto Corsa, ACC, AC EVO | jaettu muisti: `telemetry --game ac / acc / acevo` | renkaiden kosketuspisteiden keskiarvo | luistosuhde ja -kulma (fyysinen, skaalattu asfaltin tyypillisellä huipulla); ABS ja TC toiminnassa (ACC, EVO) | auton kehysvektorin nopeus | tallennin testattu synteettisillä sivuilla |
| Assetto Corsa Rally | `telemetry --game acrally` | sama | sama; pyöräkuormat; lämpötilat muunnettu kelvinistä | auton kehysvektorin nopeus | tallennin testattu synteettisillä sivuilla |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` kytkee oletus-`wrc`-paketin päälle (tiedosto varmuuskopioidaan ensin) | maailman XYZ | kosketuspisteen nopeus renkaittain; luisto johdettu | auton akseleiden ja nopeuden perusteella | tallennin testattu dokumentoidun rakenteen mukaan tehdyillä paketeilla |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: aseta `<udp enabled="true" extradata="3" port="20777" delay="1" />` tiedostoon `hardware_settings_config.xml`, sitten `telemetry --game dirtrally2` (tai `dirtrally`, `dirt4`) | maailman XYZ | kosketuspisteen nopeus renkaittain; luisto johdettu. Ei käsijarrukanavaa | auton akseleiden ja nopeuden perusteella | sama |
| Richard Burns Rally (RSF/NGP) | NGP:n UDP-telemetria (`udpTelemetry=1`): `telemetry --game rbr` | maailma; ylösakseli selvitetään osuudelta | jousen painuma ja voima renkaittain; ei pyörien nopeuksia | auton omat nopeudet | sama; akselit ja nopeusyksiköt eivät ole dokumentoituja, joten ne päätellään datasta |
| BeamNG.drive | `heat3d`-protokollamodi: `telemetry --game beamng --install`, sitten Options > Other > Protocols > "others" | maailma, käännetty Y ylös | pyörän pintanopeus, pyöriminen, kuorma ja maakosketus; luisto johdettu | auton akseleiden ja nopeuden perusteella | tallennin testattu modin rakenteesta tehdyillä paketeilla; modi testaamatta pelissä |
| Trackmania (2020) | Openplanet-liitännäinen `Heat3dRecorder`: `telemetry --game trackmania --install`, ladataan Openplanetin kehittäjätilassa; yksi CSV ajoa kohden sen tallennuskansiossa | maailman XYZ | Trackmanian oma luistokerroin renkaittain; löysä alusta renkaiden materiaaleista; ilmassa | etu- ja sivunopeus | lukija testattu; liitännäinen testaamatta pelissä |
| iRacing | sen omat `.ibt`-tiedostot; tallenninta ei tarvita | leveys-, pituus- ja korkeusaste, sijoitettuna tangenttitasoon | ei luistoa (ei kirjata); kääntymisnopeus ja sivukiihtyvyys | kääntymisnopeudesta suhteessa ajolinjaan | lukija testattu synteettisellä tiedostolla |

Mitä yksikään rallipeli ei lähetä - renkaiden luiston - sen lukija laskee: renkaan
kosketuspisteen tai pintanopeuden ja auton nopeuden erotuksesta, kun peli lähettää
jomman kumman (`(wheel - car) / car`), tai pyörimisestä ja kierroksella itse
mitatusta vierintäsäteestä, kun peli lähettää vain pyörimisen. Sivuliukukulma tulee
auton omasta nopeudesta (Forza, AC-pelit, Trackmania, RBR), maailman nopeudesta
projisoituna auton akseleille (EA WRC, DiRT, BeamNG) tai suunnan ja radan suunnan
erotuksesta. Onko auto ilmassa, selviää renkaiden kosketuksesta, kuormista tai
jousituksesta.

Jos pelin maailma on vasenkätinen - Forzan on - rata tulee katselimessa peilikuvana
oikeakätiseen katselimeen; kierrosten oma ohjaus ja jousitus paljastavat sen. Pelit,
joiden kätisyyttä ei ole dokumentoitu (RBR, BeamNG, Trackmania), käsitellään samalla
tavalla: mitataan, ei oleteta.

Ajokanavien lisäksi tallentimet säilyttävät, mitä kukin peli lisää: AC-pelien ABS- ja
ajonvakautusjärjestelmien toiminnan, jarrutasapainon, DRS:n, huoltokaistan rajoittimen,
turbon sekä jarrupalojen ja -levyjen kulumisen; iRacingin avustusasetukset,
jarrutasapainon, polttoaine-, öljy- ja vesilämpötilat sekä kaikki muut kanavat omilla
nimillään.

### Lähteet ja mikä ei ole vielä varmistettu {#sources-and-what-is-not-yet-confirmed}

- **Forza:** Forzan virallinen Data Out -dokumentaatio (Forza Motorsport; Forza Horizon 6)
  kentille, niiden yksiköille ja auton kehykselle (x oikealle, y ylös, z eteen -
  vasenkätinen). Mihin Forza normalisoi luistonsa, ei ole dokumentoitu: mittaa, missä
  kunkin auton pito oikeasti heikkenee, älä oleta, että 1 on raja.
- **Kunos:** AC1 SDK, ACC:n jaetun muistin dokumentaatio v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, mitattu; AC Rally käyttää ACC:n asettelua,
  "vahvistettu tavu tavulta -tutkimuksella"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Puoli, johon auton kehyksen x-akseli osoittaa, on dokumentoitu molempiin suuntiin:
  käytä sivuliukukulman suuruutta, ei sen merkkiä.
- **EA SPORTS WRC:** EA:n UDP Telemetry Guide v1.3 ja kanavaluettelo, jonka peli kirjoittaa
  tiedostoon `readme/channels.json`; oletus-`wrc`-paketin siirtymät, kuten
  nobonobo/obs-codemasters-telemetry ne on purkanut. Oletusporttia ei ole dokumentoitu;
  tallennin kytkee paketin päälle portissa 20777.
- **DiRT:** Codemasterin DiRT 4 UDP -dokumentti, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Sivuvektorin suunta ja jousituksen aseman
  yksikkö on dokumentoitu molempiin suuntiin; kumpikaan ei ratkaise yhtään havaintoa.
- **RBR:** NGP:n `rbr.telemetry.data.TelemetryData.h` (mika-n/RBRUDPTelemetryLogger ja
  groybe/rbr-udp-telem kautta). Sijaintiakselit, asennon yksiköt ja nopeusyksikkö eivät
  ole dokumentoituja: tallennin ottaa ylöspäin osuudelta ja nopeuden sijainneista.
- **BeamNG:** documentation.beamng.com (protokollat; refNodes: ajoneuvo +X vasemmalle,
  -Y eteenpäin, Z ylös) sekä pelin omat `lua/vehicle/protocols.lua` ja `wheels.lua`.
  OutSim on tyhjä stub nykyversioissa; OutGaugessa ei ole sijaintia eikä MotionSimissä
  pyöriä, siksi modi.
- **Trackmania:** Openplanetin `CSceneVehicleVisState` ja VehicleState-liitännäinen sekä
  `CSmScriptPlayer`-kilpa-aika. Openplanetin liitännäiset eivät voi lähettää UDP:tä, joten
  liitännäinen kirjoittaa tiedostoja. Allekirjoittamattomat liitännäiset latautuvat vain
  kehittäjätilassa, mikä rajoittaa verkkopeliä; liitännäisen voi allekirjoittaa osoitteessa
  openplanet.dev.

Yhtäkään tallenninta ei ole vielä ajettu oikeita pelejä vastaan täällä. Jokaisen
ensimmäinen oikea sessio on ratkaiseva testi, ja `tests/test_kunos.py`,
`test_rally.py` ja `test_beamng.py` lukitsevat asettelut, joihin ne rakennettiin.
Jokainen tallennin tarkistaa paketit heti, kun ne tulevat - nopeuden ja rakenteen koon -
ja kertoo, jos asettelu ei täsmää.

## Radat: mitä viedään pelikohtaisesti {#courses-what-is-exported-per-game}

Rata lisää reunakivet, seinät ja ajoalueen, jotka selittävät linjan. Radat viedään
[3DHeat GameFilesilla](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <lap>`) pelin omista tiedostoista siinä, missä se on
rakennettu ja tarkistettu asennetusta kopiosta. Yksityiskohdat ovat
[GameFiles-dokumentaatiossa](https://holdi601.github.io/3DHeat-GameFiles/).

| Peli | Rata kierroksesta |
|---|---|
| Forza Horizon | kyllä |
| BeamNG.drive | kyllä |
| Assetto Corsa Rally | kyllä |
| Assetto Corsa EVO | ei: sen sisältö ei ole luettavissa tiedostoina |
| iRacing | ei: radat ovat suojatussa muodossa |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ei vielä: jokainen tarvitsee asennetun kopion, jotta rakentaminen ja tarkistaminen onnistuu |

Alla oleva pelaamisreitti toimii siihen asti kaikille.

## Reitti, joka toimii jokaiselle pelille {#the-route-that-works-for-every-game}

GameCapture rekonstruoi kentän pelivideosta. Sen vaikein osa on kameran rata, ja
Forzalle se on tarkka, koska telemetria antaa auton asennon joka kuvalta. Jokaisella
yllä olevalla pelillä on nyt sama: sijainti ja asento reaaliajassa dokumentoidusta
rajapinnasta. Niiden syöttäminen `pose/telemetry_pose.py`:hyn Forzan tilalle on yksi
osa, joka tekee pelaamisreitistä tarkan kaikille peleille. Muu putki (syvyys, yhdistäminen,
teksturointi) ei välitä siitä, minkä pelin kuvat piirrettiin.
