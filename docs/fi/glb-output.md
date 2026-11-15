---
title: ".glb-tuloste"
nav_order: 6
lang: "fi"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# .glb-tuloste {#the-glb-output}

Rekonstruktio kirjoitetaan binaarisena glTF 2.0 -tiedostona (`.glb`). 3DHeat-katselin lataa sen Taustan / kentän -paneelistaan ilman erityiskäsittelyä. Sopimus on sama, jonka Unreal-vientityökalu kirjoittaa. Koodi: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Tiedosto kirjoitetaan käsin eikä glTF-kirjaston kautta. Tulos on kapea osajoukko (yksi puskuri, tiiviisti pakattu, ei animaatiota eikä skinningiä). Riippuvuus, joka osaa kirjoittaa koko glTF:n, toisi muutaman sadan rivin takia versioeroja.

## Mitä skannauksen tiedostossa on {#what-is-in-a-scans-file}

| Osa (solmun ja verkon nimi) | Sisältö |
|---|---|
| `ground:<name>` | kolmiot, jotka osoittavat enintään 35 asteen kulmassa ylöspäin |
| `structure:<name>` | kaikki muu |

`<name>` on tiedostonimi ilman päätettä, kun tallennetaan ikkunasta. Komennolla `reconstruct` se on videon nimi. Osaa, jossa ei ole kolmioita, ei kirjoiteta. Skannaus ei koskaan kirjoita `water:`-osaa. `asset.generator` on `heat3d-capture-scan`.

## Sopimus {#the-contract}

- **Yksi solmu per osa**, nimetty osan tunnisteella. Verkko toistaa nimen. Katselin lukee ensin *solmun* nimen, joten pelkkien verkkojen nimeäminen menettäisi luokituksen.
- Tunniste on `<class>:<name>`, jossa luokka on `ground`, `structure` tai `water`. Katselin tunnistaa etuliitteen (`^(ground|structure|water)\s*[:|]`), joten luokka otetaan sellaisenaan eikä arvata geometriasta. Maa piirretään kiinteänä, rakenteet lähes läpinäkyvinä.
- **Koordinaatit ovat katselimen tilassa**: Y ylös, oikeakätinen, ja **skaalattu senttimetreiksi** (metrit x 100). Näin tallenne ja saman paikan moottorivienti latautuvat samankokoisina samoilla kameran oletuksilla. Tiedoston ylimmän tason `extras.unit_metres` on `0.01` (yksi yksikkö on senttimetri), joten metreissä työskentelevä lukija, kuten [`locate`](locate.md), ottaa sen oikeassa koossa. Forza-telemetrian sijoittama skannaus on poikkeus kätisyydessä: se pysyy pelin omassa maailmassa, Y ylös ja vasenkätisenä, täsmälleen kuten kierrostiedostot. Niiden päälle tallennetut kierrokset osuvat siksi siihen. Kun skannauksen mittakaava löytyi myöhemmältä avainkehykseltä ([Mittakaava](reconstruction-pose.md#scale)), kerroin lasketaan kirjoitettuun mittakaavaan.
- `COLOR_0`-arvon lukee katselin. Se värittää maan sen mukaan, kun Taustan / kentän -paneelin *Tallennettu väri* -kytkin on päällä (oletuksena pois).
- Skannaus, jonka kohtia on merkitty käsin, saa viereensä tiedoston `<name>.marks.json`. Katso [Tallennus](reconstruction-scan-ui.md#saving).
- Jokaista primitiiviä kohti: `POSITION` (float VEC3, mukana `min` ja `max`, joista katselin rajaa kameran), `NORMAL` (float VEC3), valinnainen `COLOR_0` (float VEC3, 0..1), valinnainen `TEXCOORD_0`. Indeksit ovat 16-bittisiä, kun kaikki ovat alle 65,536, muuten 32-bittisiä. Tila on kolmiot.
- Jokainen puskurinäkymä alkaa 4 tavun rajalta. JSON-osa täytetään välilyönneillä ja BIN-osa nollilla 4 tavuun asti.

## Tarkistukset ennen kirjoittamista {#checks-before-writing}

Jokainen osa tarkistetaan. Jos siinä ei ole kärkipisteitä, indeksien määrä ei ole kokonaisia kolmioita, indeksi on alueen ulkopuolella tai negatiivinen, sijainnit eivät ole äärellisiä tai normaalit tai värit eivät vastaa kärkipisteiden määrää, osa hylätään viestillä, joka nimeää sen. Normaalit lasketaan, jos niitä ei ole, ja ne ovat **pinta-alalla painotettuja**. Marching cubes jättää ohuita kolmioita suurten pintojen viereen, ja painottamaton keskiarvo antaisi pienten kolmioiden päättää suuren pinnan suunnasta. Rappeutunut kärkipiste saa suunnan "ylös". Jos osia ei ole lainkaan, kirjoitus on virhe.

Vienti ei palauta mitään, ja ikkuna sanoo "Nothing to save", kun tilavuudesta ei saada pintaa. Tämä on parempi kuin tyhjän tiedoston kirjoittaminen, joka näyttäisi onnistuneelta skannaukselta.

## Tekstuurit {#textures}

Kirjoittaja tukee osakohtaista PNG-peruskuvatekstuuria (UV-koordinaateilla, kaksipuolinen, ei-metallinen, täysin karhea materiaali). Skannaukset eivät käytä sitä; niissä on kärkipistekohtainen väri. Katso [väri](reconstruction-fusion-and-texture.md#colour).

## Vertailutaso {#the-reference-level}

`geometry/reference.py` rakentaa saman kirjoittajan kautta synteettisen tason, jonka koko on tarkasti tunnettu. Siinä on 400 m jaettu maa, kolme 20 x 20 x 12 m rakennusta ja 50 m lammikko 1.5 m maanpinnan alla. Kukin luokka on omalla tasaisella värillään. Katselimen omat testit luovat tason ja jäsentävät sen katselimen oikealla jäsentäjällä. Tiedostomuoto pysyy siis testattuna molemmin puolin ilman peliä ja tallennuslaitteistoa.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
