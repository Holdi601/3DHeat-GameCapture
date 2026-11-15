---
title: Skannausikkuna
nav_order: 1
lang: "fi"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Skannausikkuna {#the-scan-window}

```bash
python -m heat3d_capture.ui        # tai kaksoisnapsauta scan.bat
```

Koodi: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Ikkuna on ohut näkymä tiedostoista `scan/session.py` ja `scan/reconstruct.py`; se ei omista
skannaus- eikä geometrialogiikkaa.

## Käynnistys {#starting-up}

1. **Päivitystarkistus** - katso [Päivitykset](updates.md).
2. **Riippuvuustarkistus** - jokainen skannerin tarvitsema paketti tarkistetaan ennen kuin mitään
   tuodaan; puuttuvat listataan sen kanssa, mihin ne ovat ja kuinka suuri lataus on, ja ne asennetaan vain
   painikkeesta "Download and install". Peruuta lopettaa muuttamatta mitään. Katso
   [Ajoaika ja riippuvuudet](runtime.md#first-run-preflight).
3. **Ikkuna** - "3DHeat — Level scanner", 1420 x 900, Qt:n Fusion-tyyli.
4. **Laitteistotarkistus** - paras päättelytaustaohjelma valitaan, syvyysmalli ladataan ja sen suorituskyky
   mitataan 6 kehyksellä; vasemmassa yläkulmassa oleva tuomiolaatikko kertoo, millaista skannaus tulee olemaan
   (katso [Ajoaika](runtime.md#what-to-expect-from-this-machine)).
5. **Globaalit pikanäppäimet** rekisteröidään viimeisinä.

### Kun syvyysmallia ei vielä ole {#when-there-is-no-depth-model-yet}

Jos `models/`-kansiossa ei ole `depth-*.onnx`-tiedostoa, tuomiolaatikossa lukee **"One more thing to set up."**,
Aloita-painike on pois käytöstä, ja ilmestyy painike **Set up the depth model**. Se:

- tarkistaa PyTorchin, `transformers`-kirjaston ja `onnxscript`-paketin (noin 945 MB yhteensä) ja kysyy ennen niiden asentamista;
- ajaa `tools/export_onnx.py --size small` erillisenä prosessina (jotta PyTorch ei koskaan jää skannerin muistiin), 30 minuutin
  rajalla. Ikkuna ei vastaa, kun se on käynnissä;
- onnistuessa ajaa laitteistotarkistuksen uudelleen; epäonnistuessa näyttää muuntajan tulosteen viimeiset 600 merkkiä.

Kun malleja on useita, valinta tehdään **lisenssin mukaan, ei tiedostonimen**: `depth-small-*`
(Apache-2.0, kaupallinen käyttö sallittu) aina, kun sellainen on, sitten Base, sitten Large (molemmat
epäkaupalliset). Tuomiolaatikko ja painikkeiden alla oleva harmaa rivi nimeävät käytössä olevan tiedoston,
sen lisenssin ja muut läsnä olevat mallitiedostot, joita ei käytetä - esimerkiksi `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Jos haluat skannata Basella, siirrä Small-tiedosto pois `models/`-kansiosta.

## Vasen sarake: asetukset {#left-column-settings}

| Ryhmä | Säädin | Oletus | Alue / arvot | Mitä se tekee |
|---|---|---|---|---|
| (yläosa) | Tuomiolaatikko | "Checking your graphics card…" | väritetty vihreä, keltainen tai punainen tason mukaan | Otsikko, `<device> via <API> — N views per second`, yksi huomautus ja `Depth model: <file> (<licence>)` |
| Mitä skannataan | Lähde | Koko näyttö | Koko näyttö, Ikkuna, Videotiedosto | Mistä kehykset tulevat |
| | Mikä | `1` | näytön numero / ikkunan otsikko / polku videoon | `monitor:<n>`, `window:<title>`, tai tiedostopolku |
| | Choose file… | näkyy videolle | `*.mp4 *.mkv *.avi *.mov` | Täyttää polun |
| Kuinka huolellisesti | Esiasetus | Balanced | Draft, Balanced, Detailed | Kaappauksen resoluutio ja kuinka valikoiva avainkehysten valinta on (alla); yhden rivin yhteenveto näkyy sen alla |
| | Pelin näkökenttä | 90° | 30-140° | Pelin **vaakasuuntainen** näkökenttä. Liian kapea, ja taso rekonstruoituu syvemmäksi kuin se on; liian leveä, ja se litistyy. Kilpapelit ovat lähempänä 65°:tta |
| | Pinnan tarkkuus | 0,25 m | 0,05-2,0 m, askel 0,05 | Pinnan voxelikoko. Pienempi on hienompi ja raskaampi |
| Pysähdy kun | Aika | ei rajaa | 0-120 min | Lopettaa skannauksen tämän pituisen ajan jälkeen (0 = ei rajaa) |
| | Säilytetyt näkymät | 3000 | 0-100 000 | Lopettaa skannauksen tämän monen avainkehyksen jälkeen, muistisuojana (0 = ei rajaa) |
| Mitä jätetään huomiotta | Ohita HUD ja kaikki kameralla | päällä | | Oppii ja peittää HUDin, tähtäimen, aseen, konepellin ja ohjaamon ([Kaappaus](reconstruction-capture.md#what-is-not-the-world)). Sen alla oleva rivi kertoo, mitä ilmaisin parhaillaan päättää |
| Pelatessa | Näytä palaute pelin päällä | päällä | | Avaa läpinäkyvän peittokuvan skannauksen ajaksi. Sen alla oleva vihje: aja peli **kehystöntä ikkunoitua** tilaa; täysruudun yksinoikeutta ei voi piirtää minkään päälle |
| Kilpailutelemetria (Forza) | Kuuntele sijaintidataa | pois | | Ottaa kameran reitin Forzan Data Outista kuvan arvioinnin sijaan ([Asento](reconstruction-pose.md#telemetry-poses)) |
| | (portti) | 5300 | 1-65535 | Data Out -portti |
| | (tilarivi) | | | `N packets — poses come from the game, not from the picture`, tai `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Aloittaa tai lopettaa; näyttää pikanäppäimen, kun se rekisteröitiin |
| | **Set up the depth model** | piilossa | | Katso yllä |
| | **Save level…** | pois käytöstä | | Käytössä skannauksen jälkeen, joka tuotti pintavoxeleita; kysyy tiedostonimeä (oletus `scan.glb`) |
| | (harmaa rivi) | | | `Model: <file> (<licence>) · Available: <backends>`, sekä asennusohjeet, kuten `onnxruntime-gpu`-paketin asentaminen |

### Esiasetukset {#the-presets}

| Esiasetus | Kaappauksen pidempi sivu | Säilytyskvantiili | Alkukynnys | Näytetty yhteenveto |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Nopea ja karkea. Hyvä reitin tarkistamiseen ennen varsinaista skannausta. |
| Balanced | 960 px | 0,65 | 0,010 | Tavallinen valinta. Kävele normaalilla vauhdilla. |
| Detailed | 1280 px | 0,40 | 0,004 | Hidas ja perusteellinen. Kävele harkiten ja käänny hitaasti. |

Säilytyskvantiili tarkoittaa "säilytä kehys, kun se muuttui enemmän kuin tämä kvantiili viimeisten 240
kehyksen muutoksista" - Draft säilyttää noin kiireisimmät 15 %, Detailed kiireisimmät 60 %. Katso
[Avainkehykset](reconstruction-capture.md#keyframes).

### Ikkunassa kiinteät asetukset {#settings-that-are-fixed-in-the-window}

Ikkuna rekonstruoi aina skannatessa, käyttää **1,15 m** kameran korkeutta maatason mittakaavalle (kävelyarvo
1,70 m ei ole valittavissa), ja antaa taustaohjelmien portaiden valita GPU:n. Nämä ovat `ScanSettings`-kenttiä
(`camera_height`, `prefer_backend`), joita vain skripti voi muuttaa.

## Oikea sarake: mitä skannaus tekee {#right-column-what-the-scan-is-doing}

| Elementti | Näyttää |
|---|---|
| **What the camera sees** | viimeisen avainkehyksen |
| **Shape it is reading** | sen ennustettu syvyys, väritetty Turbo-värikartalla ja normalisoitu kyseisen kehyksen 2. ja 98. persentiilin välille (niin yksi taivaan pikseli ei litistä aluetta) |
| **Coverage — where you have been, and how well** | pohjapiirros (katso alla) |
| **Worth another look** | heikot kohdat, numeroituna vastaamaan kartan renkaita, kukin ohjeen kanssa; pahin (suurin) ensin, enintään 8; sitten kohdat, jotka merkitsit (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Kävelynopeuspalkki | `walk speed — N% of the way to the next view`: viimeisen kehyksen kuvamuutos jaettuna **käytössä olevalla kynnyksellä** - esiasetuksen alkuarvo ensimmäiset 30 kehystä, sen jälkeen sopeutettu arvo ([Avainkehykset](reconstruction-capture.md#keyframes)) |
| Terveysrivi | seurannan terveys tai kaappausvaroitus (alla) |
| Kokorivi | `Size: ...`, miten tason mittakaava kiinnitettiin tai miksi ei ([Mittakaava](reconstruction-pose.md#scale)) |
| Tilastorivi | `views  frames  dropped  depth-per-second  seconds`, ja rekonstruoidessa `placed  cells  % well seen  metres`, sekä `recovered` ja `loops closed`, kun jompikumpi ei ole nolla |
| Pikanäppäinrivi | rekisteröidyt näppäimet tai syy, miksi niitä ei voitu rekisteröidä |
| Vihjerivi (keltainen) | suora neuvo (alla), skannauksen viimeinen viesti ja merkinnät |

### Kattavuuskartta {#the-coverage-map}

Piirretään uudelleen 900 ms välein taustasäikeellä (ei koskaan käyttöliittymäsäikeellä), 200 x 200
solusta skaalattuna 420 px:ksi:

- kattavuusruudukon jokainen sarake saa paikan **parhaan** havaintolaadun (niin hyvin nähty lattia ei
  maalaudu keltaiseksi sen yläpuolella olevan huonosti nähdyn katon takia);
- väriskaala kulkee punaisesta (huono) keltaisen (ohut) ja kellertävän kautta vihreään (hyvä);
- koskaan nähtämättömät solut ovat erillisen tummanharmaita, jotta tutkimaton nurkka ei näytä huonosti
  skannatulta;
- kuljettu reitti piirretään ohuena vaaleana viivana, nykyinen sijainti valkoisena pisteenä;
- heikot kohdat ovat valkoisia renkaita numeroineen;
- merkitsemäsi kohdat ovat keltaisia neliöitä, joissa lukee `M1`, `M2`, …
[Kattavuus ja laatu](reconstruction-fusion-and-texture.md#coverage) kertoo, miten laatu ja heikot kohdat lasketaan.

### Terveysrivi {#the-health-line}

| Seurannan terveys (sijoitetut kehykset / kehykset) | Teksti | Väri |
|---|---|---|
| ei vielä kehyksiä | Waiting for the first frame. | harmaa |
| 90 % tai enemmän | Tracking well — N of M frames placed. | vihreä |
| 60 % tai enemmän | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | keltainen |
| alle 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | punainen |

Kattavuusruudukon kaappausvaroitus korvaa tämän (punainen, kun skannausta ei arvioida rekonstruoitavaksi,
muuten keltainen): lähes ei lainkaan parallaksia, kaikki nähty yli 25 metristä tai ohut parallaksi. Katso
[Kattavuus](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Vihjerivi {#the-hint-line}

| Ehto | Vihje |
|---|---|
| yli puolet kehyksistä pudotettu, 6 s jälkeen | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| alle 0,3 näkymää säilytetty sekunnissa, 8 s jälkeen | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| yli 8 näkymää säilytetty sekunnissa, 8 s jälkeen | Keeping a lot. Slow down a little for cleaner geometry. |
| skannaus päättyi | session viesti: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, tai `failed: <error>` |

## Pikanäppäimet {#hotkeys}

Rekisteröity Windowsin kanssa (`RegisterHotKey`), joten ne toimivat, kun peli on aktiivinen. Alt-tab
pois täysruudun pelistä on juuri se, mikä pilaa kaappauksen.

| Näppäimet | Toiminto |
|---|---|
| **Ctrl+Alt+F9** | Aloita / lopeta skannaus |
| **Ctrl+Alt+F10** | Merkitse tämä kohta uudelleen käytäväksi (skannatessa) |
| **Ctrl+Alt+F11** | Näytä / piilota peittokuva (vaihtaa "Näytä palaute pelin päällä" -ruudun) |

- Ne rekisteröidään kerran, kun ikkuna avautuu, ja vapautetaan, kun se sulkeutuu; rekisteröitynä nämä
  näppäinyhdistelmät viedään pois jokaiselta muulta ohjelmalta, myös pelistä. F-näppäimet kahdella
  muokkausnäppäimellä valittiin, koska pelit harvoin sitovat niitä.
- Automaattinen toisto on estetty (`MOD_NOREPEAT`), joten näppäimen pitäminen alhaalla ei vaihda skannausta
  kymmeniä kertoja.
- Näppäin, jonka jokin toinen ohjelma jo varaa, ilmoitetaan (`... unavailable: another program already
  has this key`), ja muut toimivat yhä. Painike mainostaa vain näppäintä, joka oikeasti rekisteröitiin.
- Näppäimet ovat kiinteitä koodissa (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); jäsennin hyväksyy
  F1-F12 yhdessä `ctrl`, `alt` ja `shift` kanssa. Windowsin ulkopuolella globaaleja pikanäppäimiä ei ole, ja
  ikkuna kertoo sen.
- **Mark** tallentaa nykyisen kameran sijainnin (viimeisen sijoitetun kehyksen) ja näyttää "Marked MN.
  Marked spots are on the map and saved with the level." Ennen kuin yhtään kehystä on sijoitettu, se sanoo,
  ettei merkittävää paikkaa ole. Merkityt kohdat piirretään ikkunan karttaan ja peittokuvaan keltaisina
  neliöinä, joissa lukee `M1`, `M2`, …, luetellaan heikkojen kohtien alla, lasketaan peittokuvan tilarivillä,
  ja tallennetaan tason kanssa (alla).

## Peittokuva {#the-overlay}

Pieni paneeli kiinnitettynä pelin päälle, jotta palaute on siellä, missä silmät jo ovat.

- Kehyksetön, aina päällä, työkaluikkuna (ei tehtäväpalkissa eikä alt-tabissa), läpinäkyvä syötteelle Qt:ssä ja
  tehty läpiklikattavaksi Windowsissa (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), joten pelille tarkoitettu napsautus ei
  koskaan katoa. Näytetään ilman tarkennuksen ottamista.
- Ensisijaisen näytön oikea yläkulma, 18 px reunoista; 214 x 358 px.
- Avautuu, kun skannaus alkaa (jos "Näytä palaute pelin päällä" on päällä), sulkeutuu, kun se pysähtyy.
- **Vaatii kehyksettömän ikkunoidun tilan**: mikään ei voi piirtyä täysruudun yksinoikeuden päälle - ei tämä,
  ei Steamin peittokuva, ei Discordin.

Ylhäältä alas se näyttää:

| Elementti | Sisältö |
|---|---|
| Kattavuuskartta | 190 px, sama kartta kuin ikkunassa karkeampana 120 x 120, polun, heikkojen kohtien renkaiden ja merkittyjen kohtien kanssa |
| Terveys | sama teksti ja väri kuin ikkunan terveysrivillä |
| Tilasto | `N placed · M to revisit · X m`, ja `· K marked`, kun niitä on |
| **liikkeen** palkki | sama kuin ikkunan kävelynopeuspalkki: viimeisen kehyksen kuvamuutos kynnykseen verrattuna, täynnä, kun seuraava kehys säilytetään |
| **terävyyden** palkki | terävyys suhteessa tämän kaappauksen omaan mediaaniin: vihreä 0,75:stä, keltainen 0,45:stä, punainen alle sen |
| Neuvo | yksi ohje, vihreä / keltainen / punainen (lihavoitu, kun se ei ole "ok") - katso [kehyksen laatu](reconstruction-capture.md#frame-quality-and-advice) |
| Pikanäppäimet | rekisteröidyt näppäimet |

Jos peittokuvan päivitys koskaan heittää virheen, se vaihtuu punaiseksi paneeliksi **"Feedback stopped"**, joka kertoo,
että kaikki aiemmin näytetty on vanhentunutta, että skannaus on yhä käynnissä ja pääikkuna on yhä oikea, ja antaa
virheen ja laskurin. Paneeli, joka jäätyi vihreänä, lukisi muuten jatkuvasti vahvistuksena.

## Tallentaminen {#saving}

**Save level…** kirjoittaa rekonstruktion `.glb`-tiedostona (katso [.glb-tuloste](glb-output.md)).
Jos tilavuus ei tuota pintaa, "Nothing to save" selittää, että seuranta todennäköisesti katosi suurimmaksi
osaksi skannausta. Onnistuessa: "Written to <path> ... Load it in 3DHeat through the Level panel.", ja
nimeää myös merkkitiedoston, kun merkittyjä kohtia on.

Merkityt kohdat kirjoitetaan tason viereen tiedostoon **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` on tason omissa koordinaateissa (GLB:n skaala sovellettuna, joten merkki istuu verkolla, jonka päälle se
tehtiin), `metres` metreissä; `number` vastaa ikkunan `M1`, `M2`, … -merkintöjä. Kun mittakaava löytyi myöhemmältä
avainkehykseltä ([Mittakaava](reconstruction-pose.md#scale)), molemmat sisältävät sen kertoimen.

Skannauksen pysäyttäminen säilyttää kerätyn; uusi **Start** hylkää edellisen skannauksen.
**Ikkunan sulkeminen ei kysy tallentamisesta**: se pysäyttää skannauksen, vapauttaa pikanäppäimet ja sulkee peittokuvan.
