---
title: "Mallit ja lisenssit"
nav_order: 7
lang: "fi"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Mallit ja lisenssit {#models-and-licences}

Kaikki tälle repositoriolle kirjoitettu on **MIT-lisenssin** alla ([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). MIT ei kata sitä, mitä työkalut ajavat: niiden tuomia paketteja, rekonstruktion käyttämiä malleja ja pelejä, joita ne lukevat. Täydellinen luettelo lähteineen on tiedostossa [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md). Lisenssit luettiin paketin metatiedoista ja mallikorteista syyskuussa 2026. Jos komponentin ehdot ovat sen jälkeen muuttuneet, lähde on ratkaiseva, ei tämä sivu. Mikään tässä ei ole lakineuvontaa.

## Syvyysmalli - se, joka ratkaisee kaupallisen käytön {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **ei ole lisensoitu samalla tavalla kaikissa kooissaan**. Rekonstruktio perii sen mallin lisenssin, joka sen teki:

| Malli | Lisenssi | Kaupallinen käyttö | Käyttäjä |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **sallittu** | oletus: skannerin muunnettu malli (`tools/export_onnx.py` käyttää sitä oletuksena, ja ikkunan "Set up the depth model" rakentaa sen aina) sekä offline-polun syvyys (fuusio). VGGT antaa sen asennot |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | vain ei-kaupallinen | vain jos muunnat sen itse (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | vain ei-kaupallinen | vain jos muunnat sen itse (`--size large`) |

Base ja Large antavat paremman syvyyden. Niiden muuntaminen on sallittua. Se tekee kyseisestä mallitiedostosta ja kaikista sillä tehdyistä rekonstruktioista ei-kaupallisia. Päätös kuuluu sille, joka sen ajaa, eikä se ole oletus, joka periytyy. Skanneri valitsee tiedostoista `models/depth-*.onnx` **lisenssin, ei nimen, mukaan**. Se valitsee `depth-small-*`-tiedoston aina, kun sellainen on, sitten Basen ja sitten Large-mallin (`choose_model` tiedostossa [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). Ikkuna kertoo, minkä tiedoston se otti, sen lisenssin ja muut löytämänsä mallitiedostot, joita se ei käyttänyt. Jos haluat skannata Base-mallilla, siirrä Small-tiedosto pois kansiosta `models/`.

## VGGT - vain offline-rekonstruktio {#vggt---offline-reconstruction-only}

| Malli | Lisenssi | Saatavuus |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - vain ei-kaupallinen**; sillä tehdyt rekonstruktiot perivät sen | julkinen; oletus |
| `facebook/VGGT-1B-Commercial` | erikseen lisensoitu; tarkista saamasi ehdot | rajoitettu: pääsyn pyytää Metalta, ja se myönnetään tilikohtaisesti. Ilman sitä lataus epäonnistuu. Valitaan komennolla `reconstruct --model vggt-1b-commercial` |

VGGT:tä käyttää vain `python -m heat3d_capture reconstruct`. Livenä toimiva skanneri ei koskaan lataa sitä. Komento tulostaa lisenssirivin ennen käynnistymistään. Videosta rekonstruointi on se osa tätä projektia, jonka pelaaja ajaisi, ja ei-kaupalliset ehdot sopivat siihen. Kaupallisessa työssä reitti on moottorivienti tai pelitiedostojen vienti, ja molemmat ovat joka tapauksessa tarkkoja.

## Kehysten paikantaminen - `locate` {#locating-frames---locate}

| Malli | Lisenssi | Tehtävä |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | löytää renderöinnit, jotka näyttävät saman paikan |
| ALIKED `aliked-n16` | BSD-3-Clause | avainpisteet ja kuvaajat |
| LightGlue (ALIKED-variantti) | Apache-2.0 | sovittaa ne |

Kaikki kolme sallivat kaupallisen käytön, ja ne haetaan ensimmäisellä käyttökerralla. SuperPointia, LightGluen tavallista paria, ei käytetä, koska sen painot ovat ei-kaupallisia. Katso [Kehysten paikantaminen tasossa](locate.md).

## Python-paketit {#python-packages}

| Paketti | Lisenssi | Tehtävä |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | laskenta, tasoitus, marching cubes |
| opencv-python | Apache-2.0 | video, piirteet, optinen virtaus |
| onnxruntime, onnxruntime-directml | MIT | syvyyspäätelmä |
| windows-capture | MIT | live-tallennus Windows Graphics Capturella |
| **PySide6-Essentials** | **LGPL-3.0** | ikkuna |
| pytest | MIT | vain kehitys |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | kertaluonteinen mallimuunnos; offline-polku |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | offline-polku (`requirements-offline.txt`) |
| vggt | Metan "VGGT License" (tutkimusmateriaalien sopimus ja hyväksyttävän käytön käytäntö) | offline-polku; asennetaan GitHubista komennolla `--no-deps` |
| moderngl, glcontext | MIT | `locate`: tason renderöinti näkymän ulkopuolella (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: avainpisteet ja sovitus |

**PySide6:lla on ehtoja.** LGPL-3.0 sallii suljetun ja kaupallisen käytön, kunhan Qt pysyy *korvattavana* kirjastona. Tässä sitä käytetään tavallisena dynaamisesti linkitettynä tuontina. Tämä täyttää ehdon, ja sen lisenssi-ilmoituksen täytyy kulkea mukana jokaisessa jakelussa. Jos työkalu paketoitaisiin yhdeksi suoritettavaksi tiedostoksi, Qt:n pitäisi silti pysyä korvattavana.

`vggt`-paketin oma lisenssi luettiin sen tiedostosta `LICENSE.txt`, ja se on kirjattu tiedostoon `LICENSES.md`. Se koskee koodia erikseen. Painot ovat CC-BY-NC-4.0:n alla.

## Pelit {#the-games}

Telemetria tulee vain rajapinnoista, jotka pelit julkaisevat. Kehykset tulevat ruudulta. Katso [Säännöt](rules.md). Pelistä ei toimiteta eikä levitetä mitään, ja se, mitä työkalut tuottavat, jää käyttäjän koneelle. 3DHeat GameCapture ei ole sidoksissa mihinkään pelijulkaisijaan eikä minkään julkaisijan hyväksymä; pelien nimet ja niihin liittyvät tavaramerkit kuuluvat omistajilleen.
