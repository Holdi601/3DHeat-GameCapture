---
title: Komentoviite
nav_order: 5
lang: "fi"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Komentoviite {#command-reference}

Kaikki komennot ajetaan tietovaraston kansiosta, projektin ympäristössä:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Komento | Tekee |
|---|---|
| [`route`](#route) | Tallentaa vain Forza-kierroksen sijainnit, jotta kartta löytyy pelin tiedostoista |
| [`telemetry`](#telemetry) | Tallentaa jokaisen kanavan, yhden kierrostiedoston kierrosta kohden, Kilpa-analyysi-välilehteä varten |
| [`laps`](#laps) | Lukee FH Companion -kierroskirjaston ja kirjoittaa yhden radan reitin ja näytteet |
| [`reconstruct`](#reconstruct) | Ratkaisee tallenteen offline-tilassa ja kirjoittaa `.glb`-tiedoston |
| [`hud`](#hud) | Lukee pelaajan omat toiminnot, kuolemat ja pienoiskartan radan sekä tappolokin tallenteesta |
| [`locate`](#locate) | Missä kukin tallenteen kuva on otettu, verrattuna tason renderöintiin |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Skannausikkuna |
| [`python -m heat3d_update`](#updates) | Tarkistaa päivityksen ja asentaa sen |
| [`python tools/export_onnx.py`](#the-model-converter) | Muuntaa syvyysmallin ONNX-muotoon |

Kun ohjelma käynnistetään komennolla `python -m heat3d_capture`, se tarkistaa ensin, onko uudempi
julkaisu saatavilla (katso [Päivitykset](updates.md); `HEAT3D_NO_UPDATE=1` kytkee tarkistuksen pois).
Minkä tahansa komennon `--help` näyttää sen asetukset:

![heat3d_capture --help](../assets/img/cli-help.svg)

Koodi: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Kuuntelee Forza Data Outia ja tallentaa vain auton sijainnit, ei muuta: ei syvyysmallia, ei
näytönohjainta eikä kaappausta. Koodi: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Asetus | Oletus | Merkitys |
|---|---|---|
| `-o`, `--out` | pakollinen | Tulostiedosto; sen pääte vaihdetaan, joten `-o lap` kirjoittaa `lap.npz` ja `lap.json`. |
| `--port` | `5300` | Portti, johon peli lähettää (sidottu osoitteeseen 127.0.0.1). |
| `--seconds` | `0` | Pysähtyy tämän monen sekunnin jälkeen; `0` jatkuu, kunnes painat Ctrl+C. |

Sijainti tallennetaan vain, kun peli ilmoittaa kilpailun käynnissä olevaksi (`isRaceOn`), auto liikkuu
nopeammin kuin 0,5 m/s ja sijainti on vähintään 0,5 m edellisestä tallennetusta. Muuten valikossa
istuminen 60 paketilla sekunnissa täyttäisi tiedoston lähtöviivalla. Kunkin näytteen aika on pelin
kilpailuaika tai, jos se on 0, seinäkellon aika. Asettelu tunnistetaan samoin kuin `telemetry`-komennossa
(auton täytyy liikkua ensin; katso [Forza](telemetry-forza.md)).

Sekunnin välein tulostetaan vastaanotetut paketit, tallennetut sijainnit ja nykyinen sijainti, tai
teksti `nothing on port 5300 yet - is Data Out on?`. Reitti **tallennetaan ajon aikana**: kahden
sekunnin välein, kun uusi sijainti on tullut (väli kasvaa kaksikymmenkertaiseksi edellisen tallennuksen
kestoon nähden, joten hyvin pitkä istunto ei käytä kuin kahdeskymmenesosan ajastaan kirjoittamiseen),
ja vielä kerran, kun tallennin pysähtyy mistä syystä tahansa: Ctrl+C, `--seconds` tai poikkeus.
Jokainen tallennus kirjoittaa ensin tiedostot `lap.npz.partial` ja `lap.json.partial` ja siirtää ne sitten
oikeiden tiedostojen päälle, joten levyllä olevat tiedostot ovat aina ehjiä. Kaatuminen tai tapettu
prosessi menettää enintään viimeiset muutaman sekunnin. Jos mitään ei tallennettu, ohjelma kertoo,
miten Data Out kytketään päälle, ja päättyy koodilla 1.

Tuloste:

- `lap.npz` - NumPy-taulukot `positions` (n x 3, metriä), `times` ja `speeds` (m/s);
- `lap.json` - luettavissa ilman tätä projektia:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Sijainnit ovat pelin omia maailmakoordinaatteja. Juuri ne tekevät niistä kahvan, jolla sama maa löytyy
pelin tiedostoista: [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) -työkalun
`course`-komento lukee tämän JSON-tiedoston ja vie radan, jonka kierros kulki.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Jokainen asetus ja peli on kuvattu sivulla [Telemetriatallentimet](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Lukee FH Companionin ylläpitämän kierroskirjaston ja kirjoittaa yhdestä radasta kaksi tiedostoa: reitin,
joka kertoo, mikä pala karttaa leikataan pelin arkistosta, sekä taulukon jokaisesta kierroksen
näytteestä. Tiedostot kirjoitetaan yhtä aikaa, jotta ne eivät voi jäädä erilleen. Koodi:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Asetus | Oletus | Merkitys |
|---|---|---|
| `course` | ei mitään | Radan nimi, haetaan löyhästi. Jätä pois, niin kirjasto listataan. |
| `-o`, `--out` | radan nimi pienillä kirjaimilla, välilyönnit `_`-merkkinä | Tulostepolku; `.json` ja `.csv` kirjoitetaan rinnakkain. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Missä radan kansiot ovat. |
| `--margin` | `80` | Metriä, jotka lisätään radan ulottuvuuteen x- ja z-suunnassa reitin `bounds`-arvoon. |

### Listaus {#listing}

Ilman rataa ohjelma tulostaa radan kansioiden määrän ja jokaisesta laskun laps-tiedostojen määrän
(`*.json` kaikkialta kansion alta paitsi `course.json`) ja radan nimen. Lopuksi se kirjoittaa
`Name one to write it out:  -o <file> <course>`.

### Radan löytäminen {#finding-a-course}

Radan kansiot on nimetty muodossa `<name> (course_<x>_<z>_to_<x>_<z>)` - lähtö ja maali pyöristettyinä.
Rata haetaan tässä järjestyksessä: tarkka kansion nimi; kansion nimen osa, kirjainkoolla välittämättä;
yksikäsitteinen kansio, jonka nimi sisältää tekstin. Useampi osuma on virhe, ja se luettelee ne.

### Lukeminen {#reading-it}

- `course.json` kansiossa, kun se on luettavissa, antaa nimen ja pyöristämättömät lähdön ja maalin
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); muuten ne tulevat kansion nimestä. Rata
  ilmoitetaan kiertoratana, kun lähtö ja maali ovat alle 10 m päässä toisistaan.
- Jokainen muu `*.json` kansion alla on kierros (kierrokset ovat useiden kansioiden syvyydessä -
  luokan, auton, säädön, merkin mukaan - ja haku on yksinkertaisesti rekursiivinen). Tiedostot luetaan
  UTF-8-muodossa, jossa on tavumerkki (BOM). Lukematon kierros ohitetaan. Kierrokset järjestetään
  tallennusajan mukaan.
- Kierros kohden: `Lap.samples` (kukin `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`,
  `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), sekä auton luokka,
  järjestysnumero, suorituskykyindeksi, kierrosaika, pituus, tallennusaika ja lähtö paikaltaan.

Ohjelma tulostaa yhteenvedon (kierrokset, näytteet, paras kierros ja sen luokka, x/y/z-ulottuvuus).

### Tuloste {#output}

**`<out>.json`** - sama reittirakenne kuin `route` kirjoittaa, joten karttapurkaja ottaa kumman tahansa:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (laajennettuna `--margin`-arvolla x- ja
z-suunnassa) sekä `positions` **nopeimmasta** kierroksesta (yksi viiva eikä sumu kaikista kierroksista).

**`<out>.csv`** - jokainen näyte jokaiselta kierrokselta, yksi rivi kukin:

| Sarake | Merkitys |
|---|---|
| `course` | radan nimi |
| `lap` | kierroksen nimi: tallennuspäivä ja -aika minuutin tarkkuudella sekä kierrosaika |
| `car` | auton järjestysnumero |
| `car_class` | suorituskykyluokan kirjain |
| `pi` | suorituskykyindeksi |
| `lap_seconds` | kierroksen aika |
| `speed_kmh` | nopeus km/h |
| `x`, `y`, `z` | maailmasijainti metreinä, 3 desimaalia |
| `speed_ms` | nopeus, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | sellaisina kuin FH Companion ne tallentaa |
| `metres` | matka kierroksen varrella, 3 desimaalia |
| `elapsed` | sekunnit kierroksen omasta alusta, 3 desimaalia |

Muut kuin sijaintiarvot kirjoitetaan 4 merkitsevällä numerolla; sijainnit saavat kiinteät desimaalit,
koska 4 merkitsevää numeroa kiinnittäisi radan metrin ruudukkoon. Sarakkeiden nimet on valittu niin,
että katselin ymmärtää tiedoston ilman ohjeita: `lap` tulee istunnoksi (kaksi samaa autoa tekemää
kierrosta ei koskaan yhdisty), `car` on liikkuva asia, `car_class` ryhmä, jonka mukaan värjätään,
ja `elapsed` aika-akseli (jokainen kierros alkaa omasta lähdöstään).

Lopuksi ohjelma tulostaa vihjeen, miten kartta leikataan pelistä GameFilesilla, reittitiedoston tai
oman laatikon avulla.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rakentaa tallenteen uudelleen offline-tilassa, ja kameran reitti ratkaistaan kerralla VGGT:llä. Hidas:
minuutteja ikkunaa kohden pöytätietokoneen näytönohjaimella. Tarvitsee PyTorchin, Hugging Face
`transformers`-kirjaston ja `vggt`-paketin, joita skanneri ei tarvitse: ne on listattu tiedostossa
`requirements-offline.txt`, ja komento tarkistaa ne lisenssirivin tulostamisen jälkeen ja tarjoaa
puuttuvien asentamista (koodi 1, jos kieltäydyt). Täydellinen kuvaus:
[Offline-rakentaminen](reconstruction-offline.md).

| Asetus | Oletus | Merkitys |
|---|---|---|
| `video` | pakollinen | Tallenne. Koodi 2, jos sitä ei ole. |
| `-o`, `--out` | pakollinen | Kirjoitettava `.glb`. |
| `--solve-budget` | `260` | Suurin määrä kehyksiä, jotka annetaan ratkaisijalle. Ne jaetaan sen mukaan, kuinka paljon kuva liikkuu, eikä kellon mukaan. Enemmän on tarkempaa ja paljon hitaampaa. Yli 400 suunniteltua kehystä hylätään. |
| `--fuse-interval` | `0.4` | Sekunnit kehysten välillä, jotka yhdistetään geometriaan. |
| `--model` | `vggt-1b` | Mitkä VGGT-painot ratkaisussa käytetään: `vggt-1b` (`facebook/VGGT-1B`, ei kaupalliseen käyttöön) tai `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, rajattu; Metan on myönnettävä käyttöoikeus). Ensin tulostettava lisenssirivi on tuon mallin. |

Ensin se tulostaa mallin lisenssirivin, sitten jokaisen vaiheen (`masking`, `planning`, `solving`,
`fusing`, `exporting`) kuluneine sekunteineen ja edistymisineen, ja lopuksi yhteenvedon: ratkaistut
kamerat, sulkuvirhe, pahin saumavirhe, huomautukset ja kirjoitettu tiedosto. Paluukoodi on 0 vain, jos
tiedosto kirjoitettiin.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Lukee pelin HUDin pelaajan oman tallenteen pelin jälkeen: pelaajan omat toiminnot pistepopupista,
kuolemat ja elvytykset kuolemis- ja käyttöönottoruuduista, pienoiskartan radan ja tappolokin. Kirjoittaa
`<out>.parquet` (rata ja tapahtumat, 3DHeat-taulukko), `<out>.events.jsonl`, `<out>.summary.json` sekä
`<out>.map.png` ja `.map.json` (pienoiskartan mosaiikki ja sen ankkurit katselimen Karttakuva-kohtaan).
Battlefield 6 (`bf6`) on toistaiseksi ainoa profiili.

Tarvitsee **ffmpegin ja ffprobe-ohjelman** `PATH`-polulle (`winget install Gyan.FFmpeg`, sitten uusi
terminaali).

| Asetus | Oletus | Merkitys |
|---|---|---|
| `video` | pakollinen | Tallenne. |
| `-o`, `--out` | videon nimi | Tulostepolku ilman tiedostopäätettä. |
| `--game` | `bf6` | Minkä pelin HUD luetaan. |
| `--player` | arvataan | Pelaajan nimi sellaisena kuin tappolokki sen näyttää, haetaan löyhästi. |
| `--fps` | `5` | Pienoiskartan näytteitä sekunnissa. |
| `--start`, `--seconds` | koko video | Osa tallenteesta, joka luetaan. |
| `--metres-per-pixel` | ei mitään | Pienoiskartan mittakaava, kun se tunnetaan; ilman sitä sijainnit ovat pienoiskartan pikseleissä. |
| `--cpu` | pois | Dekoodaa prosessorilla, vaikka NVIDIA-näytönohjain on käytettävissä. |

Edistyminen tulostetaan viiden sekunnin välein; lopussa tulostetaan pelaaja, tappo, kuolemat, elämät
ja kirjoitetut tiedostot.

Täydellinen kuvaus: [HUDin lukeminen tallenteesta](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderöi tason jokaisesta paikasta, johon pelaaja voi seisoa, ja indeksoi renderöinnit; `frames`
paikantaa jokaisen otetun kehyksen tallenteesta tason suhteen kuvan perusteella, ja `hud`-komennon
pienoiskartan rata on varareitti; `eval` vertaa tulosta tunnettuihin kameran asentoihin; `train`
opettaa paikkakohtaisen mallin tason renderöinneistä (ja kehyksistä, jotka ajo jo paikansi) komennolle
`build --head`; `refmap` asettaa pelin oman kartan (sen käyttöönottoruudun) tasoon, ja `minimap` lukee
tallenteen pienoiskartan sitä vasten kehys kerrallaan - sen `frames --minimap` voi ottaa. Tarvitsee
PyTorchin ja tiedoston `requirements-locate.txt`. **Kokeellinen:** oikeilla tallenteilla se paikantaa
toistaiseksi vain pienen osan kehyksistä. Kaikki asetukset, tulosteet ja menetelmä:
[Kehysten paikantaminen tasossa](locate.md); koko asetuslista: [Komentoviite](../cli-reference.md).

## Skannausikkuna {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

tai kaksoisnapsauta `scan.bat`-tiedostoa. Ei asetuksia. Katso [Skannausikkuna](reconstruction-scan-ui.md).

## Päivitykset {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Katso [Päivitykset](updates.md).

## Mallimuunnin {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Muuntaa Depth Anything V2 -tarkistuspisteen ONNX-tiedostoksi, jota skanneri ajaa. Tarvitsee PyTorchin,
`transformers`-kirjaston ja `onnxscript`-paketin. Katso [Syvyys](reconstruction-depth.md#building-the-model).
