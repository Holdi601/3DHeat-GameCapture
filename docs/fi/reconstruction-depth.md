---
title: "Syvyys"
nav_order: 3
lang: "fi"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Syvyys {#depth}

Ulkoinen kaappaus ei voi antaa yhtä asiaa: geometriaa. Peli tietää jokaisen pikselin syvyyden,
ja se on puskurissa, johon tämä projekti tarkoituksella ei koske, joten syvyys **päätellään
kuvasta**. Se on koko lähestymistavan tarkkuuden katto.

Koodi: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(mitä skanneri ajaa),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(PyTorch-polku ja mittakaavasovitus),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Malli {#the-model}

**Depth Anything V2**, suhteellinen variantti. Se ennustaa *suhteellisen käänteisen syvyyden*:
epäsuoran etäisyyskentän, joka on oikea vain tuntemattomaan affiiniin muunnokseen asti,
`metric_disparity = a * predicted + b`, ja eri jokaiselle kuvalle. Verkko on hyvä siinä, mikä on
vaikeaa yksittäisestä kuvasta (suhteellinen muoto, reunat, ohut rakenne), ja vaiti siitä, mitä
se ei voi tietää (mittakaava). Mittakaava tulee muualta - katso [Kameran asento ja mittakaava](reconstruction-pose.md).

| Koko | Hugging Face -tunnus | Lisenssi |
|---|---|---|
| **Small** (oletus) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - kaupallinen käyttö sallittu |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - vain ei-kaupalliseen käyttöön |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - vain ei-kaupalliseen käyttöön |

Rekonstruointi perii sen mallin lisenssin, joka sen teki. Small on oletus kaikkialla juuri siksi,
että skannaus ei kanna rajoitusta, ellei joku valitse toisin. Mittaavat variantit
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) on nimetty koodissa, mutta
skanneri ei käytä niitä. Katso [Mallit ja lisenssit](models-and-licences.md).

## Mallin rakentaminen {#building-the-model}

Skanneri ajaa ONNX-tiedostoa eikä tuo PyTorchia koskaan. Tiedosto pitää tehdä kerran:

- **Ikkunasta**: "Set up the depth model" (katso [Skannausikkuna](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), joka
  ajaa alla olevan komennon valitsemalla `--size small`.
- **Käsin**, ympäristössä, jossa on PyTorch, `transformers` ja `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Valinta | Oletus | Merkitys |
|---|---|---|
| `--size` | `small` | `small`, `base` tai `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | tulostiedosto |
| `--side` | `518` | neliön sisääntulokoko; pitää olla 14:n monikerta (ViT-lappukoko); 518 = 14 x 37 on koulutusresoluutio |
| `--opset` | `17` | ONNX-opset; 17 on laajasti tuettu DirectML:llä ja CUDA:lla |

Muunnin tekee seuraavaa:

- Lataa tarkistuspisteen Hugging Facesta (`AutoModelForDepthEstimation`).
- Kääri mallin niin, että **ImageNet-normalisointi on graafin sisällä**: malli ottaa RGB:n
  alueella 0-255 liukulukuna (`pixels`, muoto `batch x 3 x side x side`) ja antaa
  `inverse_depth`-tuloksen. Keskiarvo ja keskihajonta on yhdessä kopiossa, joten ne eivät voi
  erota tarkistuspisteestä.
- **Kiinteä tilakoko**, dynaaminen erä. DirectML ja TensorRT kääntävät muodon mukaan; dynaaminen
  korkeus ja leveys kääntäisi uudelleen jokaisen uuden resoluution ensimmäisellä kuvalla, mikä
  näkyisi elävässä kaappauksessa pysähdyksenä.
- Vie **TorchScript-polun** kautta (`dynamo=False`): dynamo-graafi epäonnistui DirectML:llä
  Reshape-solmussa, ja se kirjoittaa painot erilliseen `.onnx.data`-tiedostoon. TorchScript-polku
  tuottaa yhden itsenäisen tiedoston.
- Tulostaa tiedoston ja sen koon. Jäljittäjän varoitukset kiinteistä muodoista ovat odotettuja.

Skanneri etsii tiedostoja `models/depth-*.onnx` ja valitsee lisenssin perusteella, ei tiedoston
nimen: Small aina, kun se on olemassa, suurempi koko vain, jos se on ainoa. Skannausikkunan rivi
kertoo tiedoston, sen lisenssin ja muut käyttämättä jääneet mallit.

## Ajaminen: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` rakentaa yhden ONNX Runtime -istunnon laiskasti, täydellä graafin
optimoinnilla, valitussa taustaosassa, ja CPU lisätään varalla, jotta provider, joka epäonnistuu
istunnon luonnissa (vanha ajuri), tarkoittaa hidasta skannausta eikä kaatumista. Katso
[Suoritusympäristö ja riippuvuudet](runtime.md#inference-backends).

- `warm_up()` rakentaa istunnon ja ajaa yhden tyhjän kuvan (ensimmäinen päättely uudelle graafille
  on useita kertoja hitaampi kuin vakaa tila).
- `measure_throughput(frames)` mittaa niin monta tyhjää kuvaa lämmittelyn jälkeen; ikkuna käyttää
  6:ta ja ilmoittaa tuloksen kuvina sekunnissa.

### Letterboxing, ei venyttämistä {#letterboxing-not-stretching}

Graafi ottaa kiinteän neliön, ja pelikuva on 16:9. Kuvan puristaminen neliöksi muuttaisi kaiken
näennäisen muodon, ja koska tulos on geometrinen arvio, se yhdistettäisiin oikeana vääränä
geometriana. Joten jokainen kuva tehdään näin:

1. skaalataan mahtumaan neliöön säilyttäen kuvasuhde (alueinterpolaatio alaspäin, kuutio ylöspäin);
2. täytetään **keskiharmaalla (114)** - musta tai valkoinen lukee vahvana reunana ja vuotaa
   väärän syvyysepäjatkuvuuden viereiseen sisältöön;
3. ajetaan malli;
4. täyte leikataan ennusteesta **ennen** kuin se skaalataan takaisin (kuutio) kuvan resoluutioon,
   joten marginaali ei vuoda todellisiin pikseleihin.

Tulos on `DepthMap` jossa `metric=False` lähdekuvan koossa.

## PyTorch-polku {#the-pytorch-path}

`DepthEstimator` ajaa Hugging Face -mallin suoraan (fp16 CUDA:lla, fp32 CPU:lla), erätetään
kuvakoon mukaan, ja jokainen ennuste skaalataan takaisin kuutiointerpolaatiolla. Skanneri ei käytä
sitä; offline-komento `reconstruct` käyttää (katso [Offline-rekonstruointi](reconstruction-offline.md)),
ja se on yksi syy, miksi tuo komento tarvitsee PyTorchin ja `transformers`-kirjaston.

## Suhteellisesta metriseen: `fit_scale` ja `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Ennustetun käänteisen syvyyden muuttaminen metreiksi vaatii affiinin `scale * predicted + shift`.
Kun tunnetun syvyyden ankkureita on saatavilla (piirteet, jotka on kolmiomitattu tunnetuista
asennoista, tai edellisen kuvan ankkuroitu syvyys), `fit_scale` ratkaisee sen:

- pienimmän neliösumman **levyydessä**, ei syvyydessä - verkon virhe on suunnilleen tasainen
  levyydessä, kun taas syvyydessä muutama kaukainen ankkuri (jossa yksi pikseli levyydessä on
  kymmeniä metrejä) hallitsisi;
- **iteratiivisesti painotettu** (12 iteraatiota, Cauchy-tyyppiset painot `1 / (1 + (r / 3 MAD)^2)`),
  koska ankkureissa on rajuja poikkeamia (liikkuvan auton osuma, seurantavirhe), ja yksi tällainen
  ankkuri tavallisessa sovituksessa vetäisi koko kuvan mukanaan;
- tarvitsee vähintään 2 käyttökelpoista ankkuria; raportoi mediaanin absoluuttisen jäännöksen ja
  sisäpisteiden määrän (jäännös 3 x mediaanin sisällä).

`AffineFit.apply` palauttaa syvyyden metreinä, ja taivaalle **+inf**. Se tarkistaa myös ennustetun
arvon ankkuroidun arvon lisäksi: taivaspikseli, joka ennustaa nollan, tulee ulos arvolla `shift` -
pienenä, positiivisena ja äärellisenä - ja muuten jokainen taivaspikseli laskeutuisi haamukuoreen
yhdelle etäisyydelle. Kaikki, mikä ennustetaan arvoon `1e-4` tai sen alle, on taivasta, mitä
sovitus sitten sanookin.

Yhdistäminen pitää sitten vain syvyydet väliltä 0,35 m - 60 m (katso
[Yhdistäminen](reconstruction-fusion-and-texture.md#from-depth-to-points)).
