---
title: "Kaappaus, maskit ja kuvan laatu"
nav_order: 2
lang: "fi"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Kaappaus, maskit ja kuvan laatu {#capture-masks-and-frame-quality}

Koodi: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Mistä kuvat tulevat {#where-frames-come-from}

Lähdekohde on yksi seuraavista:

| Kohde | Lähde | Huomautus |
|---|---|---|
| `monitor:<n>` | koko näyttö, suorana | ikkunan "Whole screen" -valinta, numero kentässä "Which" |
| `window:<title>` | yksi ikkuna, suorana | ikkunan "A window" -valinta ja sen otsikko |
| tiedostopolku | videotiedosto | ikkunan "A video file" -valinta; mikä tahansa muoto, jonka OpenCV lukee |

### Suora kaappaus: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` käyttää `windows-capture`-pakettia, joka kääri **Windows Graphics Capturen**
- julkisen rajapinnan, jota näytön tallentimet käyttävät. Peliin ei injektoida mitään.
Kursoria ei kaapata, eikä keltaista kaappausreunusta piirretä.

Kaappauskirjasto toimittaa kuvat takaisinkutsulle kompositorin säikeessä ja odottaa, että
se palaa heti. Siksi takaisinkutsu vain kopioi kuvan (puskuria käytetään uudelleen), muuntaa
BGRA:sta RGB:hen, muuttaa koon, leimaa sen ja laittaa sen **4 kuvan** jonoon. Kun jono on
täynnä, **vanhin kuva pudotetaan** ja laskuri kasvaa: jälkeenjääminen maksaa kuvia, ei
muistia tai oikeellisuutta, ja suoran näkymän pitää näyttää, missä pelaaja on nyt.
Pudotetut kuvat näkyvät ikkunan tilarivillä, ja jos yli puolet putoaa, ilmestyy vihje.

Jokaisella kuvalla on `t` (sekunteja kaappauksen alusta) ja `monotonic` (raaka
`time.monotonic()` kaappaushetkellä). Telemetriapaketit leimataan samalla kellolla, ja sen
avulla Forzan asennot saadaan kohdistettua kuviin.

`windows-capture` on valinnainen riippuvuustarkistuksessa: ilman sitä videotiedoston
skannaus toimii yhä.

### Videotiedostot {#video-files}

`VideoSource` lukee OpenCV:llä, muuntaa RGB:hen ja muuttaa koon. Säilö ilman kuvataajuutta
käsitellään 30 fps:nä. Aikaleimat ovat kuvan indeksi jaettuna kuvataajuudella; tiedostolla ei
ole seinäkelloaikaa, joten telemetriaa ei voi kohdistaa videoon.

### Resoluutio {#resolution}

Kuvat muutetaan lähteessä siten, että pidempi sivu on esiasetuksen kaappauskoko (Draft 640,
Balanced 960, Detailed 1280 px), alueinterpolaatiolla. 4K-kuva on kolmekymmentä kertaa
enemmän pikseleitä kuin syvyysmalli käyttää.

## Avainkuvat {#keyframes}

Lähes jokainen kuva kaappauksessa on turha: paikallaan seisominen tuottaa sata näkymää
samasta asiasta. Rekonstruointi haluaa *parallaksia*. Kuva siis säilytetään sen mukaan,
**kuinka paljon kuva muuttui edellisestä säilytetystä kuvasta**, ei ajastimen mukaan.

`picture_change(a, b)`:

1. molemmat kuvat harmaiksi ja alas 16 x 16 ruudukoksi lohkojen keskiarvoina (lohkojen
   keskiarvot reagoivat kuvan liikkumiseen, eivät raekokoon, kasvillisuuteen, välkkymiseen tai
   HUD:iin);
2. keskimääräinen absoluuttinen erotus murto-osana 255:stä;
3. kun maailmamaski tunnetaan, jokainen lohko painotetaan sen maailmaan kuuluvalla osuudella
   eikä ohjaamolla, joten puoliksi kojelautaa oleva lohko lasketaan puolikkaana (käytetään,
   kun maski kattaa yli 5 % ruudukon painosta).

Kynnys **mukautuu kaappaukseen**: ensimmäiset 30 kuvaa käyttävät esiasetuksen aloitusarvoa
(0,020 / 0,010 / 0,004), sen jälkeen esiasetuksen kvantiilia (0,85 / 0,65 / 0,40) viimeisten
240 mitatun muutoksen joukosta, ei koskaan alle 0,0001. Kuva säilytetään, kun sen muutos
saavuttaa kynnyksen; ensimmäinen kuva säilytetään aina. Kiinteä kynnys ei toimi eri kohtauksissa:
tumman ohjaamon kierroksen kuvanvaihto on pieni murto-osa kirkkaan, tekstuurisen huoneen
muutoksesta, kun taas "säilytä vilkkain kolmannes" tarkoittaa samaa molemmissa. Käytössä oleva
kynnys menee mukaan jokaiseen edistymispäivitykseen (`ScanProgress.threshold`), ja ikkunan ja
peittokuvan kävelynopeuspalkit mittaavat viimeisintä muutosta sitä vasten
(`ScanProgress.toward_next_view`).

Vain säilytetyt kuvat menevät syvyysmallin ja rekonstruoinnin läpi. Kuvia ei tallenneta, ellei
kutsuja pyydä sitä (`keep_frames`); 160 niistä säilytetään verkon värjäykseen (katso
[väri](reconstruction-fusion-and-texture.md#colour)).

Skannaus päättyy, kun se pysäytetään, kun video loppuu tai kun aika- tai avainkuvaraja täyttyy.

## Mikä ei ole maailmaa {#what-is-not-the-world}

Kaksi asiaa pelikuvassa ei ole tason geometriaa, ja kumpikin pilaa rekonstruoinnin:

- **HUD.** Tähtäin on toistuvin piirre missä tahansa kuvassa. Piirteiden vertailija rakastaa
  sitä: se täsmää täydellisesti jokaisen kuvaparin välillä, ja jokainen osuma on todiste siitä,
  ettei kamera liikkunut - mikä puristaa koko rekonstruoinnin kasaan.
- **Kameraan kiinnitetyt asiat.** Ase, konepelti, ohjaamon runko, kojelauta. Oikeaa geometriaa
  väärässä koordinaattijärjestelmässä: yhdistettynä ne levittyvät koko kävelyreitin pituudelle.

Kaksi tunnistinta löytää ne. Molemmat tuottavat maskin (255 = maailma, 0 = ei maailma) tai
arvon `None`, kun todisteita ei ole tarpeeksi. `None` tarkoittaa aina "käytä kaikkea", ei
"käytä ei mitään".

Maskia käytetään:

- **piirteiden tunnistuksessa** visuaalisessa odometriassa (tähtäimen maskaaminen pois
  ulostulosta samalla kun se saa äänestää asennosta, korjaisi näkyvän oireen ja jättäisi
  vahingollisen);
- **yhdistettyihin pikseleihin**, jotta ohjaamon geometriaa ei yhdistetä;
- **terävyys- ja kirkkausmittaukseen**, koska ohjaamo on aina täysin terävä;
- **kuvanmuutokseen**, joka päättää avainkuvista.

Sitä **ei** käytetä kehyksiin, jotka annetaan offline-VGGT-ratkaisijalle (katso
[Offline-rekonstruointi](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: mikä ei muutu {#screenmask-what-does-not-change}

Käytössä ensimmäisestä avainkuvasta, kunnes FlowMask on valmis.

- Jokainen kuva muutetaan harmaaksi, puolitetaan ja sumennetaan (3 x 3 Gaussin), jotta HUD-elementin
  yhden pikselin värinä ei lue liikkeenä.
- Pikselikohtainen absoluuttinen erotus edelliseen kuvaan kootaan eksponentiaaliseksi
  keskiarvoksi (vaimennus 0,9), joten maski seuraa HUD:ia, joka ilmestyy tai katoaa kesken
  skannauksen.
- Se oppii vain kuvista, joissa kamera tiedetään liikkuvan (skannauksessa: kun vähintään yksi
  kuva on seurattu) - paikallaan oleva kamera tekee kaikesta staattista.
- **12** oppimiskuvan jälkeen pikseli on staattinen, kun sen keskimääräinen muutos on alle
  **0,22** kuvan mediaanimuutoksesta - suhteellinen, joten kynnys seuraa, kuinka nopeasti
  pelaaja liikkuu.
- Jos yli **45 %** kuvasta on staattista, oletus on pettänyt (valikko, välianimaatio), eikä mitään
  peitetä.
- Maski kaventuu yhden pikselin verran (reunapikselit eivät kuulu kumpaankaan puoleen) ja
  skaalataan takaisin täyteen kokoon.

Sen huomautus ikkunassa: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected` tai `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: mikä ei koskaan liiku {#flowmask-what-never-travels}

Ohjaamo ei ole staattinen: neulat heiluvat, kierroslukumittari väpättää, kartta pyörii, joten
muutoksen tunnistin pitää näitä pikseleitä maailmana - ja ne ovat pahimpia piirteitä, mitä
asennonratkaisijalle voi antaa. FlowMask kysyy paremman kysymyksen: **mitkä piirteet pysyvät
paikallaan liikkumatta?**

- Suorassa skannauksessa se oppii kerran, ensimmäisistä **40 avainkuvasta** (harmaasävyinä); sen
  jälkeen se korvaa ScreenMaskin koko loppuskannauksen ajaksi.
- Kuvat leikataan **30 kuvan** ikkunoihin, jotka menevät puoliksi päällekkäin. Jokaisessa
  ikkunassa kylvetään jopa 800 kulmaa (`goodFeaturesToTrack`, laatu 0,01, 8 px välein) ja
  seurataan pyramidaalisella Lucas-Kanadella (21 x 21, 4 tasoa) **eteen-taakse-tarkistuksella**:
  rata, jonka takaisin-virtaus ei osu 1 px:n sisään lähtöpisteestään, pudotetaan, koska
  naapurikuvioon ajautuva seuranta tuottaisi juuri sen "pysyvä mutta paikallaan" -merkin, jota
  etsitään. Alle 20 kuvan ikkunat ohitetaan. Lyhyillä ikkunoilla on merkitystä: pitkässä
  ajossa lähes jokainen maailman piirre poistuu kuvasta, ja todisteet ohenevat olemattomiin.
- Jokaisen säilyneen piirteen nettomatka verrataan **2 %:iin kuvan leveydestä**: alle sen
  piirre on "jumissa", sen yli "liikkuu". Lukuja kerätään **24 x 24** ruudukkoon näyttöruutuihin
  sen mukaan, mistä piirre alkoi.
- Ruutu on estetty, kun siinä on vähintään 2 jumissa olevaa piirrettä ja enemmän jumissa kuin
  liikkuvia, **ja** vähintään 3 sen 8 naapurista on myös estettyjä (yksittäinen ruutu on kohinaa;
  tumma kuvamateriaali tuottaa niitä paljon).
- Vain estetyt alueet, jotka **ovat yhteydessä kuvan reunaan**, säilytetään. Kameraan kiinnitetty
  kaikki ulottuu kuvan reunaan; keskellä oleva ja paikallaan pysyvä on katoamispiste - eteenpäin
  ajettaessa suoraan edessä oleva tie ei liiku ja on se geometria, jota eniten halutaan.
- Säilynyt alue kasvaa yhdellä ruudulla (mittaristo reunan gradientti on osa sitä).
- Jos yli **60 %** kuvasta olisi maskattu, mitään ei maskata: yöllisessä kuvamateriaalissa
  useimmissa ruuduissa ei ole seurattavaa piirrettä, ja se näyttää samalta kuin mittari.

Sen huomautus: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the
frame — it never travels`, tai yli 60 %:n kohdalla viesti, joka selittää, ettei mitään
maskata.

Offline-polku oppii saman FlowMaskin neljästä 90 peräkkäisen kuvan ajosta, jotka jakautuvat
videolle, 960 x 540 -koossa ([Offline](reconstruction-offline.md)).

## Kuvanlaatu ja neuvot {#frame-quality-and-advice}

`QualityWatcher` arvioi jokaisen avainkuvan ja valitsee **yhden** ohjeen, jotta peittokuva voi
sanoa "hidasta" silloin, kun siihen on vielä aikaa.

Jokaisesta kuvasta mitataan maailmapikseleistä (kaikki pikselit, jos maski jättää alle 5 %):

- **terävyys**: Laplacen varianssi - tavallinen yhden kierroksen mitta, ja se reagoi juuri siihen,
  mitä liikehämärä tuhoaa;
- **valoisuus**: keskimääräinen harmaataso, 0-255.

Terävyydellä ei ole absoluuttista asteikkoa (yöosuus ja kirkas katu eroavat suuruusluokan verran,
molemmat tarkkoja), joten sitä arvioidaan **tämän kaappauksen juoksevaa mediaania** vastaan: viimeiset
90 kuvaa, ja arviointi vaatii 20 kuvaa ennen kuin mitään arvioidaan. Jokaista kuvaa verrataan
historiaan *ennen* kuin se lisätään, joten pitkä sumea jakso ei voi vetää mediaania alas
itseensä.

| Ehto | Testi |
|---|---|
| tasainen | terävyys enintään 1,0 (latausruutu, seinä, taivas) |
| tumma | valoisuus alle 26 |
| sumea | terävyys alle 0,55 mediaanista ja ei tasainen |

Neuvo, ensimmäinen osuma voittaa (järjestys sen mukaan, mikä estää skannausta eniten):

| Tilanne | Neuvo | Taso |
|---|---|---|
| alle 20 kuvaa | Tutustutaan kuvaan… | ok |
| tasainen | Ei mitään mitattavaa - suuntaa kamera kenttään, älä taivaaseen. | stop |
| tumma | Liian tumma rekonstruoitavaksi. Ajovalot päälle tai aja tämä osuus päivänvalossa. | stop |
| sumea | Sumea - hidasta. | warn |
| alle puolet kuvista seurattu | Seuranta katoaa - hidasta ja pidä enemmän kenttää näkyvissä. | warn |
| alle 40 % seuratuista kuvista yhdistetty | Sijainnit ovat hyvät, mutta syvyys ei tartu. Aja lähemmäs maisemaa. | warn |
| heikkoja kohtia on | N heikkoa kohtaa - kartta merkitsee ne. | ok |
| muuten | Hyvä - jatka. | ok |

Kenttä värittää peittokuvan neuvon (vihreä / oranssi / punainen). Peittokuvan **terävyyspalkki**
on kuvan terävyys suhteessa mediaaniin. (Koodissa on myös "Blurred, and the camera is not
moving. Check the capture." paikallaan olevalle kameralle; skannaus ilmoittaa aina kameran
liikkuvan, joten sitä ei näytetä.)
