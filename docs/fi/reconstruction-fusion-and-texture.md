---
title: "Yhdistäminen, kattavuus ja väri"
nav_order: 5
lang: "fi"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Yhdistäminen, kattavuus ja väri {#fusion-coverage-and-colour}

Koodi: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Jokainen sijoitettu avainkuva päivittää kahta harvaa ruudukkoa kerralla: **pintatilavuus**, josta
verkko tulee, ja **kattavuusruudukko**, joka kertoo, kuinka paljon siihen voi luottaa ja mihin
palata. Molemmat päivitetään kuva kerrallaan, ei lopussa, koska kattavuuskartta on se, jolla
pelaaja ohjaa.

## Syvyydestä pisteisiin {#from-depth-to-points}

Jokaiselle avainkuvalle, jonka asento tunnetaan **ja** jonka syvyydellä on mittakaava:

1. Joka toinen pikseli kummassakin suunnassa käytetään (`PIXEL_STRIDE = 2`; saman pinnan
   naapuripikselit eivät ole riippumattomia mittauksia).
2. Syvyys muutetaan metreiksi kuvan affiinisovituksella.
3. Pidetään vain väliltä **0,35 m** (lähempänä on ase, HUD, konepelti) ja **60 m** (yksisilmäinen
   virhe kasvaa suunnilleen etäisyyden neliön mukaan, joten kaukaiset pisteet ovat kohinaa, joka
   näyttää geometrialta), ja vain maskin maailmapikseleillä.
4. Nostetaan kameramallin läpi ja siirretään maailmaan asennon mukaan.
5. Jokainen piste kantaa pikselin värin.

Kuva, joka on sijoitettu mutta jolla ei ole syvyyden mittakaavaa, lasketaan *sijoitetuksi* mutta
ei *yhdistetyksi*.

## Pintatilavuus {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxel on ikkunan "Surface detail" -asetus.

### Painotettu miehitys, ei TSDF:ää {#weighted-occupancy-not-a-tsdf}

Katkaistu etäisyyskenttä (TSDF) leikkaa jokaista pikselisädettä pitkin ja saa ohuet rakenteet ja
puhtaan tyhjän tilan oikein, koska se tietää säteen kulkeneen *läpi* tyhjästä tilasta. Se tarkoittaa
säteen kulkemista jokaisen satojen miljoonien pikselien kohdalla. Tämä tilavuus sen sijaan kerää
**painotettua miehitystä** voxelkohtaisesti ja ajaa marching cubesin tasoitetulle tulokselle: tarpeeksi
nopeasti ajettavaksi skannauksen aikana ilman käyttökelpoista GPU:ta, ja tulos on suljettu pinta eikä
pistepilvi. Hinta: ohuet rakenteet ja tyhjä tila ovat huonompia kuin TSDF saisi.

### Kehyksen integrointi {#integrating-a-frame}

- Pisteet lajitellaan voxeleihin (`floor(point / voxel)`).
- Jokainen kosketettu voxel saa `paino x sqrt(määrä / max_määrä)`, missä `määrä` on kuinka monta
  kehyksen pistettä osui siihen ja `paino = max(0.1, asennon luottamus)`. Neliöjuuri: tietystä
  pisteestä eteenpäin saman pinnan lisäpikselit samasta paikasta eivät enää ole todiste; asennon
  luottamukseen painottaminen pitää epävarman asennon työntämästä pintaa.
- Väri on juokseva painotettu keskiarvo voxelkohtaisesti.

Ruudukko on **harva**: kävelty reitti koskettaa pienen murto-osan rajauslaatikostaan. Voxelkoordinaatit
pakataan yhdeksi 64-bittiseksi avaimeksi (21 bittiä akselia kohden, enintään ±1 048 575 voxelia - 0,25 m:llä
noin ±262 km) ja haetaan lajitellusta taulukosta binäärihaulla, täysin vektoroituna.

### Verkon purku {#extracting-the-mesh}

1. Voxelit, joiden paino on alle **0,35**, pudotetaan (irralliset yksittäiset pisteet siluetin
   reunoilla muuttuisivat piikeiksi).
2. Painot skaalataan skannauksen **75. prosenttipisteen** mukaan ja rajataan arvoon 1.
3. Miehitetty tila leikataan **64 voxelin kokoisiin lohkoihin** per sivu, ja kukin lohko toteutetaan
   **3 voxelin haalla** naapureidensa datasta (ilman sitä jokainen lohkon raja sulkeutuisi seinäksi,
   ja tie tulisi ulos laatikoiden rivinä).
4. Jokaisen lohkon kenttä tasoitetaan Gaussin suodattimella (sigma 0,8 voxel), jotta syvyyskohina
   jättämä rypyt poistuvat.
5. **Ensimmäinen vaihe**: tasoitetun kentän 99. prosenttipiste kaikista lohkoista (enintään 2 miljoonaa
   arvoa) asettaa yhden globaalin tasomittakaavan. Normalisointi lohkokohtaisesti nostaisi yksittäisen
   poikkeaman täyteen pintaan omassa tyhjässä lohkossaan.
6. **Toinen vaihe**: jokaisen lohkon kenttä jaetaan tällä mittakaavalla, marching cubes tasolla **0,5**.
   Kolmio kuuluu lohkoon, johon sen **painopiste** osuu, joten saumoja ylittävät kolmiot syntyvät
   täsmälleen kerran.
7. Kärjet siirretään maailmayksiköihin voxelien keskipisteissä; jokainen kärki saa voxelinsa värin
   (keskiharmaa, jos se osuu tyhjään voxeliin).

Lohkokohtainen purku on se, mikä tekee kilometrin mittaisen radan skannauksen mahdolliseksi: yksi tiheä
taulukko kilometrin neliön laatikosta 0,25 m:n tarkkuudella olisi miljardeja soluja. Testi
`tests/test_track_scale.py` varmistaa, että tämä toimii siinä mittakaavassa muistilla, joka on
verrannollinen skannattuun alaan.

### Maa ja rakenne {#ground-and-structure}

`classify` merkitsee jokaisen kolmion normaalinsa mukaan (suunnattu purettujen kärkien normaaleilla):
**35 asteen** sisällä suoraan ylös on `ground`, kaikki muu on `structure`. Katselin piirtää maan
kiinteänä ja rakenteet lähes läpinäkyvinä. **Vettä ei koskaan merkitä** - sitä ei voi erottaa tasaisesta
maasta muodon perusteella, ja väärä merkintä piirtäisi pihan järveksi. Jokainen merkintä muuttuu yhdeksi
`.glb`:n osaksi ([.glb-tuloste](glb-output.md)).

## Kattavuus {#coverage}

`CoverageGrid(voxel=0.5)` kirjaa jokaiselle puolen metrin solulle neljä asiaa, jotka eivät ole sama
asia:

| Termi | Tallennettu | Pistemäärä (kukin rajattu välille 0..1) | Miksi lasketaan erikseen |
|---|---|---|---|
| Kuinka monta kertaa nähty | niiden avainkuvien määrä, jotka näkivät solun | `count / 3` | kerran on arvaus, jota ei ole mihin verrata |
| Kuinka monesta suunnasta | yksikköavaussuuntien summa | `(1 - spread) / (1 - 0,93)`, missä spread = summan pituus / määrä | kaksikymmentä kuvaa suoraan seinää kohti ei tuota parallaksia; kaksi näkymää kolmenkymmenen asteen erolla arvoaan enemmän |
| Kuinka kaukaa | lähin katseluetäisyys | `1 - nearest / 40 m` | syvyysvirhe kasvaa suunnilleen etäisyyden neliöllä |
| Kuinka hyvin kamera paikannettiin | paras asennon luottamus | luottamus itse | pinnat, jotka yhdistettiin epävarmaan asentoon, päätyvät väärään paikkaan |

Kehyksen pisteet ryhmitellään ensin solujen mukaan, joten kymmenentuhatta yhden seinän pikseliä
lasketaan yhdeksi havainnoksi yhdestä suunnasta.

**Laatu = neljän termin tulo**, ei keskiarvo: ne ovat ehtoja, joiden kaikkien on pidettävä. Paikka,
joka on nähty kahdellasadalla kerralla yhdestä suunnasta kuudenkymmenen metrin päästä, on huonosti
havaittu, ja keskiarvo piilottaisi sen yhden erinomaisen termin taakse.

Yhteenvetoluvut (`summary`): miehitetyt solut, osuus, jonka laatu on vähintään 0,5 ("% well seen"
ikkunassa), keskilaatu ja tilavuus.

### Heikot kohdat {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. solut, joiden laatu on alle 0,35, ovat heikkoja;
2. heikot solut ryhmitellään **yhteyden** mukaan (26-naapuristo, union-find vain miehitettyjen solujen
   yli - ei rasterissa rajauslaatikon yli, mikä pitkällä ajolla on miljoonia tyhjiä soluja);
3. alle 8 solun ryhmät ohitetaan;
4. ryhmän syy on sen soluista yleisin *heikoin termi*, ja sen sijainti on solujen keskiarvo;
5. lajitellaan suurimmasta pienimpään (sitten huonoimman laadun mukaan), enintään 8.

| Syy | Näytettävä neuvo |
|---|---|
| few views | Nähty vain kerran tai kahdesti - kävele ohi uudelleen. |
| one direction | Nähty vain yhdestä kulmasta. Astu sivulle ja katso uudelleen. |
| distant | Nähty vain kaukaa. Mene lähemmäs. |
| poor tracking | Kameraa ei paikannettu hyvin tässä kohdassa. Lähesty hitaammin. |

Yhteydellä on merkitystä: kiinteä lohkoruudukko raportoisi yhden unohdetun sivuhuoneen monena
erillisenä renkaana, eikä kukaan voisi erottaa kahdeksaa paikkaa yhdestä paikasta, joka on laskettu
kahdeksan kertaa.

### Pohjakuva {#the-plan-view}

`top_down(resolution)` projisoi solut x/z-tasoon ja säilyttää **parhaan** laadun kussakin pystyrivissä
(joku huoneessa seisova näkee katon huonosti ja lattian erinomaisesti; keskiarvo maalaisi huoneen
keltaiseksi). Näkemättömät rivit merkitään erikseen. Ikkuna piirtää sen 200 x 200:na, peittokuva
120 x 120:na ([Skannausikkuna](reconstruction-scan-ui.md#the-coverage-map)).

### Onko tämä rekonstruoitavissa? {#is-this-reconstructable}

Joka 25. yhdistetyn kuvan kohdalla, kun solut ovat vähintään 500:

| Havainto | Tuomio | Viesti (lyhennetty) |
|---|---|---|
| alle 2 % soluista on näkymän hajonta alle 0,93 | ei rekonstruoitavissa | Lähes ei lainkaan parallaksia. Joko kamera ei koskaan katso sivuun, tai seuranta ajautuu, joten sama pinta ei osu koskaan kahdesti samaan paikkaan. Tarkista sijoitettujen kuvien määrä: jos se on korkea, kyse on ajautumisesta. |
| solujen lähimmän etäisyyden mediaani yli 25 m | ei rekonstruoitavissa | Kaikki nähtiin N m:n päästä tai kauempaa ... Mene lähemmäs sitä, mitä haluat. |
| alle 6 % hyvällä hajonnalla | rekonstruoitavissa, varoitus | Ohut parallaksi - geometria on karkea. Liike sivulle suhteessa siihen, mitä katsot, auttaa eniten. |

Matala parallaksi on kahden syyn tulos, joita tämä ei osaa erottaa toisistaan, ja siksi viesti
nimeää molemmat.

## Väri {#colour}

Yhdistämisen voxelikohtainen väri on halpa ja elävä, mutta sumea: jokainen pikseli neljänneksen
metrin solussa keskiarvoistetaan, mukaan lukien ne, jotka nähtiin sivusta kolmenkymmenen metrin päästä.
Siksi vientivaiheessa verkko väritetään uudelleen kerran, suoraan kuvista:

- **Säilytetyt kuvat**: enintään **160** avainkuvaa (kuva ja asento), valittu säiliönäytteenotolla
  niin, että ne jakautuvat koko skannaukseen eikä vain sen loppuun.
- **Kärkikohtaisesti** (`project_colours`) jokainen säilytetty kuva antaa panoksensa, jos kärki on
  kameran edessä ja kuvan sisällä, pinta kääntyy enintään noin 70 astetta pois suoraan kameraan päin
  (`|normal . view| > 0.34`), se on lähempänä kuin **35 m**, eikä mikään sitä lähempänä ollut sen
  edessä (alla).
- Jokainen tällainen näkymä pisteytetään `facing x (1 - distance / 35)`, joten lähellä suoraan
  edestä katsottu näkymä voittaa kaukaisen vinon. **4 korkeimmin pisteytettyä** näkymää per kärki
  säilytetään - kuvien järjestyksestä riippumatta, paremman näkymän korvatessa heikoimman neljästä -
  ja ne sekoitetaan saman pisteytyksen painottamina.
- **Peittyminen**: jokaisessa kuvassa verkon omat näkyvät kärjet piirretään syvyyspuskuriin 2 pikselin
  soluihin, pitäen lähimmän solussa. Kärki, joka on yli `0,3 m + 5 %` etäisyydestään lähimmän takana
  solussaan, oli piilossa kyseisessä kuvassa - seinä kameran ja tien välissä - ja näkymä ei laske siinä
  kuvassa. Testi tuntee vain verkon: peittäjää, jota ei koskaan yhdistetty (ohi ajava auto, ohjaamon
  pilari HUD-maskin ulkopuolella), ei havaita.
- Kärki, jota yksikään kuva ei nähnyt, säilyttää voxeliväriään; kärki, jolla ei ole kumpaakaan, on
  keskiharmaa (musta lukisi reikänä).

Väri kirjoitetaan kärkikohtaisena `COLOR_0`-attribuuttina, ei tekstuuriatlasina. Katselimen oletusilme
on harmaa kartta kylläisen lämmön alla; väri on siellä löytääkseen tien skannatulta radalta, jossa pelkkä
geometria ei erota sitä reunasta, ja se näytetään katselimen *Tallennettu väri* -kytkimen takana, sen
Tausta / kenttä -paneelissa. Atlas kasvattaisi tiedoston kokoa ja tarvitsisi purkajan näkymälle, joka on
tarkoituksella muu kuin oletus. Blender ja muut glTF-työkalut lukevat `COLOR_0`-arvon.
