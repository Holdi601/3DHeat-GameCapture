---
title: Rajat ja todentaminen
nav_order: 9
lang: "fi"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Rajat ja mitä on todennettu {#limits-and-what-is-verified}

Rehellinen luettelo: mitä työkalut eivät tee, ja mitä ei ole tarkistettu pyörivää peliä vastaan.

## Telemetria {#telemetry}

| Tallennin | Tila |
|---|---|
| Forza | Rakennettu Data Out -virallisen dokumentaation pohjalta; asettelu tunnistetaan suoraan paketeista. Katselimen FH Companion -lukija `.tele.gz` on tarkistettu oikeilla kierroksilla. |
| AC, ACC, AC EVO, AC Rally | Testattu synteettisillä sivuilla, jotka on tehty julkaistuista asetteluista. **Ei vielä ajettu oikeita pelejä vastaan.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testattu paketeilla, jotka on tehty dokumentoiduista asetteluista. **Ei vielä ajettu oikeita pelejä vastaan.** RBR:n akselit, asenne ja nopeusyksiköt eivät ole dokumentoituja, ja ne käsitellään datasta. |
| BeamNG.drive | Tallennin on testattu paketeilla, jotka on tehty modin rakenteesta. **Modia ei ole ajettu pelissä.** |
| Trackmania | Katselimen CSV-lukija on testattu. **Liitännäistä ei ole ajettu pelissä.** Se latautuu vain Openplanetin kehittäjätilassa. |
| iRacing | Katselimen `.ibt`-lukija on testattu synteettisellä tiedostolla. |

Muut telemetrian rajat:

- Forzan liukuman normalisointi ei ole dokumentoitu; Kunosin liukuma skaalataan tyypillisellä asfalttihuipulla, joka on arvio.
- Joidenkin auton rungon sivuakselien suunta (Kunos, DiRT) on dokumentoitu kahteen suuntaan; liukumakulman koko on luotettava, merkki ei.
- Yksikään ralli-peli ei lähetä renkaan liukumaa; se johdetaan katselimessa. RBR ei lähetä pyörien nopeuksia.
- Rallierikoisen pinta kirjoitetaan vain, kun `--surface` annetaan; muuten tiedosto ei nimeä sitä ja katselin päättelee sen (erikoisen tai tapahtuman nimestä, sitten ajotyylistä, oletuksena löyhästi).
- Kierroksen tunnistus ilman kierroslaskuria (AC EVO, AC Rally, BeamNG) käyttää kohtaa, josta tallennus alkoi, viivana, joten aloita tallennus lähtöviivalta.
- BeamNG-ajoneuvon nollaus sulkee avoimen kierroksen siinä hetkessä: se kirjoitetaan osittaisena ajona, kun se kattoi vähimmäismatkan (300 m), ja muuten hylätään.
- `route` tallentaa noin 2 sekunnin välein ajon aikana; kaatuminen tai tapettu prosessi menettää enintään viimeisen tallennuksen jälkeiset sijainnit.
- Forza Horizon ei lähetä radan nimeä, joten Forza-kierrostiedostoissa on `"track": null`; Forza Motorsport (2023) lähettää vain numeron, joka säilytetään nimellä `lap.trackOrdinal`.

## Rekonstruktio {#reconstruction}

- **Syvyys arvioidaan, ei lueta.** Koko lähestymistavan katto, ja hinta siitä, ettei peliprosessiin koskaan kosketa.
- **Näkökenttä oletetaan, ei mitata.** Liian kapea, ja taso rekonstruoituu syvemmäksi kuin se on.
- **Globaali mittakaava** tulee oletetusta kameran korkeudesta (1,15 m ikkunassa) tai telemetriasta. Se mitataan ensimmäisestä avainkehyksestä; kun siinä ei ole käyttökelpoista maata, seuraavia avainkehyksiä kokeillaan (enintään 30 kehystä), ja myöhemmin löytynyt mittakaava sovelletaan koko tasoon, kun se kirjoitetaan. Ikkunan rivi `Size:` kertoo, mitä tapahtui; jos maata ei löydy lainkaan, skannaus pysyy ilman yksiköitä. Tässä tapauksessa voxelikoko on ensimmäisen kehyksen yksiköissä, joten sen koko metreinä eroaa asetuksesta. Offline-rekonstruktiot ovat ratkaisun omissa yksiköissä.
- **Silmukan sulkeminen on pois päältä**, eikä se ole pistekaavio, kun se kytketään päälle koodissa; ajautumaa rajoittaa vain kehykseltä kehykselle -seurannan laatu.
- **Ikkunoitu nipun säätö on olemassa, mutta sitä ei ole kytketty**; se romahti oikealla materiaalilla.
- **Pinta on painotettu tilavuustiheys, ei TSDF**: ohuet rakenteet ja tyhjä tila ovat huonompia kuin TSDF antaisi.
- **Ei tekstuuriatlasta.** Väri on per kärki (`COLOR_0`), sekoitettuna 4 parhaasta näkymästä 160 säilytetystä kehyksestä. Peittotesti on karkea: se testaa verkon omia kärkiä vastaan 2 pikselin syvyyspuskurissa, joten peittävää kohdetta, jota verkko ei sisällä (ohi ajava auto), ei havaita.
- **Vettä ei koskaan merkitä**; kaikki on maata tai rakennelmaa.
- **Syötteestä eteenpäin ratkaiseminen ei ole reaaliaikaista**: se tarvitsee ensin tallenteen. Vaikeiden osuuksien adaptiivista uudelleenratkaisua ei ole rakennettu.
- **Telemetria-asennot** asettavat kameran autoon (seuraavan kameran siirtymä on tuntematon). Sijainnit otetaan sellaisina kuin Forza ne lähettää (Y ylös, kuten kierrostiedostoissa); suuntien yaw, pitch ja roll on luettu tallennetuista kierroksista (ajosuunta, rinne, se puoli, jonka jousitus painuu), ei käynnissä olevan pelin kamerasta.
- Peittokuva ei voi piirtyä **täysruudun yksinoikeudella** (exclusive fullscreen); käytä kehystöntä ikkunoitua tilaa.
- Globaalit pikanäppäimet, läpinäkyvä peittokuva ja live-kaappaus toimivat vain **Windowsissa**.
- Ikkunan sulkeminen ei kysy, halutaanko tallentaa.

## Mitä mitataan {#what-is-measured}

- `tests/test_accuracy.py`: synteettinen huone, jonka polku ja analyyttinen syvyys tunnetaan - kehykset sijoitettu, polun virhe, kuljettu matka, huoneen koko, pinta seinillä ([Tason rekonstruktio](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: tie, jonka leveys tunnetaan, ajetaan keskeltä pois, ja se rekonstruoi leveytensä.
- `tests/test_track_scale.py`: pinnan irrotus radan mittakaavassa, muisti suhteessa skannattuun alaan, lohkojen yhdistyminen yhdeksi pinnaksi.
- `tests/test_glb.py` sekä katselimen omat testit: `.glb`-sopimus molemmilta puolilta.
- Syvyysverkko suoriutuu oikeassa pelattavuudessa tavalla, jota synteettinen kohtaus ei voi vastata, eikä testisarja mittaa sitä.
