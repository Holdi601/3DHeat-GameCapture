---
title: "Tason rekonstruktio"
nav_order: 6
lang: "fi"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Tason rekonstruktio pelitallenteesta {#level-reconstruction-from-gameplay}

Kävele tasossa hitaasti tai aja rata. Skanneri muuttaa sen, mitä ruudulla näkyi, `.glb`-tiedostoksi, jonka 3DHeat-katselin lataa telemetrian taustaksi. Tiedostosopimus on sama, jonka Unreal-vienti kirjoittaa. Tämä on tilanteeseen, jossa kukaan ei ole viennyt karttaa eikä pelin tiedostoja voi lukea. Moottorivienti tai pelitiedostojen vienti on tarkka, tämä on arvio.

## Putki {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Vaihe | Live-skannaus (`heat3d_capture.ui`) | Offline (`reconstruct`) | Sivu |
|---|---|---|---|
| Kehykset | näyttö, ikkuna tai video, skaalattu esiasetuksen pidemmälle sivulle | video, otettu kahdesti (ratkaisusuunnitelma ja fuusiovälin mukaan) | [Tallennus](reconstruction-capture.md) |
| Avainkehykset | säilytetään sen mukaan, kuinka paljon kuva muuttui; kynnys sovitetaan tallennukseen | joka `--fuse-interval`-sekunti | [Tallennus](reconstruction-capture.md#keyframes) |
| Maskit | muutokseen perustuva `ScreenMask`, sitten virtaukseen perustuva `FlowMask` 40 avainkehyksen jälkeen | `FlowMask` opittu videon neljästä ajosta; ei sovelleta ratkaisijaan | [Tallennus](reconstruction-capture.md#what-is-not-the-world) |
| Syvyys | ONNX-malli parhaalla GPU-taustaohjelmalla | PyTorch Depth Anything V2 Small | [Syvyys](reconstruction-depth.md) |
| Asento | visuaalinen odometria tai tarkka Forza-telemetria | VGGT-ikkunat liitettynä yhdeksi poluksi ja interpoloituna | [Asento](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Mittakaava | kameran korkeus maasta (1.15 m) kerran tai telemetria | ratkaistun polun omat yksiköt | [Asento](reconstruction-pose.md#scale) |
| Fuusio | painotettu miehitys, harvat voksonit; peittoruudukko | sama | [Fuusio](reconstruction-fusion-and-texture.md) |
| Tulos | `.glb`, maa- ja rakenneosat, kärkipisteväri, senttimetrit | sama | [.glb-tuloste](glb-output.md) |

Koodi: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan) (`session.py` - skannauksen asetukset ja rytmitys; `reconstruct.py` - avainkehykset geometriaksi; `offline.py` - offline-polku). Vaiheet ovat kansioissa `capture/`, `depth/`, `pose/`, `fusion/` ja `geometry/`.

## Mistä tarkkuus tulee {#where-accuracy-comes-from}

Yksisilmäinen syvyys pitää paikkansa vain tuntemattomaan mittakaavaan asti. Huoneen valokuva ja nukkekodin valokuva ovat sama kuva. Siksi verkko saa tehdä sen, missä se on hyvä: suhteellisen muodon, reunat ja ohuet rakenteet. Mittakaava ja kameran polku tulevat jostain, joka ne tuntee:

| Peli | Kameran polku | Mittakaava |
|---|---|---|
| Forza Horizon / Motorsport, telemetria päällä | tarkka, Data Outista, interpoloituna kunkin kehyksen tallennusajankohtaan | tarkka: syvyys ankkuroidaan kolmiomittaamalla piirteitä kahden tunnetun asennon välillä |
| Muu peli, live | visuaalinen odometria, ketjutettuna kehyksestä kehykseen | kiinnitetään kerran oletetusta kameran korkeudesta maasta |
| Tallenne, offline | VGGT, ratkaistu päällekkäisillä ikkunoilla | ratkaisun omat yksiköt (ei metrinen) |

Ainoa luku, jonka skanneri saa tiedoksi eikä mittaa, on pelin **vaakasuuntainen näkökenttä**. Ikkunan oletus on 90 astetta, ja kilpailupelit ovat lähempänä 65:tä. Liian kapea näkökenttä rekonstruoi tason syvemmäksi kuin se on. Liian leveä litistää sen.

## Kerrotaan käyttäjälle ajoissa {#telling-the-user-early}

Skannaus on fyysinen teko: joku kävelee tasossa useita minuutteja. Kallis virhe on kävellä loppuun ja huomata, ettei se kelvannut. Siksi ikkuna mittaa tämän koneen syvyyden läpimenon ennen kuin mitään voi alkaa, ja kertoo, millainen skannauksesta tulee ([Ajoaika](runtime.md#what-to-expect-from-this-machine)). Skannauksen aikana se näyttää peittokartan, jossa on numeroidut heikot kohdat. Lisäksi se näyttää seurannan kunnon, kävelynopeuspalkin, terävyyspalkin ja yhden ohjeen kerrallaan. Tämä näkyy ikkunassa ja pelin päällä klikkautuvassa peittokuvassa ([Skannausikkuna](reconstruction-scan-ui.md)).

## Mitattu synteettisellä vertailutiedolla {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` renderöi 12 x 8 m huoneen (4 m korkea) tunnetusta kameran polusta. Syvyys on analyyttinen, ei verkon, ja rekonstruointi tehdään 0.2 m vokseleilla. Testi vahvistaa seuraavat asiat:

- yli 90 % kehyksistä sijoittuu;
- keskimääräinen polkuvirhe on alle 0.35 m, pahin alle 1 m;
- kuljettu matka on 10 %:n sisällä totuudesta;
- huone tulee oikean levyisenä 1.5 m:n tarkkuudella;
- yli 75 % seinäpinnasta on 0.45 m:n päässä oikeasta seinästä;
- tutkimuskävely saa selvästi paremman peiton kuin suoraan eteenpäin kävely;
- piirteetön kohtaus hylätään sen sijaan, että se keksittäisiin.

Analyyttinen syvyys eristää asennon, mittakaavan ja fuusion verkosta. Se, miten verkko pärjää oikealla pelaamisella, on eri kysymys, johon mikään synteettinen kohtaus ei vastaa. `tests/test_track_width.py` tarkistaa, että tien keskustasta sivuun ajettu kierros rekonstruoi tien leveyden, ei vain ajettua linjaa.

## Sivut {#pages}

- [Skannausikkuna](reconstruction-scan-ui.md) - jokainen säädin, pikanäppäin ja peittoelementti
- [Tallennus, maskit ja kehyksen laatu](reconstruction-capture.md)
- [Syvyys](reconstruction-depth.md)
- [Kameran asento ja mittakaava](reconstruction-pose.md)
- [Fuusio, peitto ja väri](reconstruction-fusion-and-texture.md)
- [.glb-tuloste](glb-output.md)
- [Offline-rekonstruktio](reconstruction-offline.md)
