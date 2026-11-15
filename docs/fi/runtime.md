---
title: "Suoritusympäristö ja riippuvuudet"
nav_order: 8
lang: "fi"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Suoritusympäristö, riippuvuudet ja suorituskyky {#runtime-dependencies-and-performance}

Koodi: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Kaksoisnapsauta sitä. Se tekee itse vain kaksi asiaa:

1. **Etsii Pythonin** (`python`, sitten `py`). Jos sitä ei ole, se kysyy
   `Install it now with winget [Y,N]?`; kyllä-vastauksella se ajaa
   `winget install -e --id Python.Python.3.12`, ja pyytää sitten sulkemaan ikkunan ja ajamaan
   `scan.bat` uudelleen, jotta Windows ottaa uuden PATH:n käyttöön. Ei-vastauksella mitään ei asenneta.
2. **Luo yksityisen ympäristön**, `.venv`-kansion `scan.bat`:n viereen, jos sitä ei ole, ja päivittää sen pipin -
   joten mitään ei asenneta järjestelmän Pythoniin.

Sen jälkeen se ajaa `.venv\Scripts\python.exe -m heat3d_capture.ui`. Kaikki muu - puuttuvan selvittäminen,
sen selittäminen ja kysyminen - tapahtuu Pythonissa, dialogina.

## Ensimmäisen ajon tarkistus {#first-run-preflight}

Ennen kuin ikkuna tuo mitään raskasta, jokainen vaatimus tarkistetaan (`importlib.util.find_spec`:llä, joten
puoliksi poistettu paketti lasketaan puuttuvaksi). Säännöt:

- **Kaikki tarkistetaan ensin.** Koko lista kootaan ennen kuin mitään sanotaan, joten yhden paketin korjaaminen ei
  johda suoraan seuraavaan virheeseen.
- **Kysy, älä oleta.** Dialogi listaa jokaisen puuttuvan paketin, mihin se on tarkoitettu, ja kokonaislatauksen, eikä
  tee mitään ilman **Download and install** -painiketta. Peruuta lopettaa: "Nothing was installed and nothing was
  changed."
- **Hiljaisuus ei ole suostumus.** Ilman Qt:ta tarkistus siirtyy konsoliin ja kysyy `Install them now? [Y/n]`
  (Enter, `y`, `yes`, `j`, `ja` tarkoittavat kyllä); ilman terminaalia, josta vastata (syötteen loppu), se ei asenna
  mitään.
- **Tämän työkalun omaan ympäristöön.** Asennus on `<käynnissä oleva python> -m pip install ...` aliprosessina - `scan.bat`:n
  kanssa yksityiseen `.venv`-ympäristöön. Jos se epäonnistuu, dialogi näyttää pipin tulosteen viimeisen rivin ja
  komennon, jonka voi yrittää käsin.

| Paketti | Tuodaan nimellä | Näytetään tehtävänä | Likimääräinen lataus |
|---|---|---|---|
| numpy | `numpy` | aritmetiikka, jonka päällä kaikki muu on rakennettu | 20 MB |
| opencv-python | `cv2` | videotiedostojen ja kameran kuvien lukeminen | 40 MB |
| onnxruntime-directml Windowsilla, muualla onnxruntime | `onnxruntime` | syvyysmallin ajaminen näytönohjaimella | 120 MB |
| PySide6-Essentials | `PySide6` | ikkuna ja sen säätimet | 90 MB |
| scipy | `scipy` | rekonstruoidun pinnan tasoittaminen | 45 MB |
| scikit-image | `skimage` | mittausten muuttaminen 3D-pinnaksi | 30 MB |
| windows-capture | `windows_capture` | elävä pelikuvan kaappaus ikkunasta (valinnainen: ilman sitä videotiedostot toimivat yhä) | 5 MB |

Syvyysmallin muuntaminen tarvitsee kolme lisää, pyydetään erikseen ja vain, kun painat "Set up the depth model":
`torch` (noin 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Skanneri itse ei tuo niitä koskaan.

Offline-komennolla `reconstruct` on oma tarkistus: se ajetaan lisenssirivin tulostuksen jälkeen ja vain
terminaalissa: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, ja
`vggt` Metan GitHub-repositoriosta (asennettu `--no-deps`-valinnalla, koska sen metatiedot lukitsevat numpyn alle
2:n). Sama lista on `requirements-offline.txt`-tiedostossa; katso [Offline-rekonstruointi](reconstruction-offline.md#requirements).

ONNX Runtime -paketti, joka tarjotaan, on se, jonka `requirements.txt` valitsee alustalle: `onnxruntime-directml`
Windowsilla, `onnxruntime` muualla. Jos `onnxruntime` on jo tuotavissa (esimerkiksi `onnxruntime-gpu`), mitään ei
asenneta: tarkistus tehdään moduulin nimellä.

## Asentaminen käsin {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` lukitsee: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(vain Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` Windowsilla ja `onnxruntime>=1.19` muualla.

`requirements-offline.txt` lisää sen, mitä vain `reconstruct` tarvitsee: `transformers`, `einops`,
`safetensors`, `huggingface_hub` ja `Pillow`, `vggt`-asennusrivin (`--no-deps`) ja VGGT:n lisenssihuomautuksen
otsikossaan. PyTorch ei ole siinäkään, syystä jonka alla.

**PyTorch on tarkoituksella poissa.** Oikea wheel riippuu GPU:sta ja CUDA-versiosta, ja sen lukitseminen
asentaisi CPU-version koneisiin, jotka tarvitsevat GPU-version eniten. Jos haluat sen (mallin muunnos, offline-polku
`reconstruct`), asenna se **ennen** `requirements.txt`-tiedostoa: torch-wheelit voivat valita numpy 1.x:n, jota
scipy ei sitten suostu ajamaan, ja virhe näkyy muodossa `module numpy has no attribute long` scipyn sisältä, kaukana
syystään.

`onnxruntime-directml` ja `onnxruntime-gpu` ovat ristiriidassa: asenna vain toinen.

Kehittäjän todentama: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, NVIDIA RTX 5080:llä, ja sama ympäristö
ilman NVIDIA-kohtaista pakettia.

## Päättelytaustat {#inference-backends}

ONNX Runtime pääsee GPU:hin execution providerien kautta, ja se, mitä niitä on, riippuu siitä, miten onnxruntime
asennettiin, ei laitteistosta. Siksi saatavuus selvitetään, paras ensin:

| Sija | Provider | Näkyy nimellä | Laitteisto |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | mikä tahansa Direct3D 12 -GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | mikä tahansa |

**DirectML on oletusasennus**, koska se tavoittaa AMD- ja Intel-GPU:t NVIDIA:n lisäksi. NVIDIA on nopeampi omilla
providereillaan - `onnxruntime-gpu`:n asentaminen lisää CUDA:n, ja ikkuna kertoo sen, kun se näkee NVIDIA-kortin
DirectMLllä ajamassa - mutta NVIDIA ei saa olla ainoa vaihtoehto. CPU on aina viimeisenä, joten kone ilman
käyttökelpoista GPU:ta saa hitaan skannauksen eikä mitään, ja se lisätään varalla, kun GPU-istunto luodaan.

Näyttösovittimen nimi luetaan Windowsin näyttösovitinluokan rekisteriavaimesta (ei valmistajan työkalusta, kuten
`nvidia-smi`:stä, joka on vain joillakin koneilla), ohittaen Basic Render Driverin. Valmistajakohtaiset providerit
nimeävät vastaavan sovittimen; DirectML näytetään ensimmäisellä luetellulla sovittimella, joka on järjestelmän
oletus. Nimi on vain näyttöä varten.

`ScanSettings.prefer_backend` (vain skripteille) voi nimetä providerin tai lyhyen nimen.

## Mitä tältä koneelta voi odottaa {#what-to-expect-from-this-machine}

Ikkuna mittaa syvyysmallin todellisen läpimenon tällä koneella käynnistyksessä (6 kuvaa lämmittelyn jälkeen) sen
sijaan, että katsoisi GPU:n taulukosta - lämpötila, kannettavan virtaprofiilit ja ajuriversiot liikuttavat sitä liikaa -
ja kertoo, millainen skannaus tulee olemaan ennen kuin mitään voi aloittaa:

| Mitattu kuvaa sekunnissa | Taso | Otsikko | Neuvo |
|---|---|---|---|
| 25 tai enemmän | reaaliaikainen | Elävä skannaus täydellä tarkkuudella. | Kävele normaalilla vauhdilla; peittokuva pysyy mukana. |
| 12-25 | toimiva | Elävä skannaus, vähemmän säilytettyjä kuvia kuin täydellä nopeudella. | Kävele hitaasti ja käänny hellästi - nopeat käännökset jättävät aukkoja. Draft säilyttää vähemmän kuvia, mikä auttaa syvyysmallia pysymään mukana. |
| 2-12 | hidas | Tallenna ensin, rekonstruoi jälkikäteen. | Tallenna video kävelystä ja rekonstruoi tiedostosta myöhemmin. Tulos on sama; vain palaute ei ole elävä. |
| alle 2 | epäkäytännöllinen | Tämä kone on liian hidas hyödylliseen skannaukseen. | Lyhyempi reitti tai pienempi malli. **Aloitus on pois käytöstä.** |

CPU:lla huomautus lisää, että `onnxruntime-directml`:n asentaminen yleensä korjaa tilanteen Windowsilla. Mikään ei
muuta kaappauksen resoluutiota itsestään: se ei auttaisi, koska syvyysmalli ajaa kiinteällä sisääntulokoollaan siitä
riippumatta, mitä sille annetaan; hitaampaa konetta pitää mukana vähempi säilytettyjä kuvia, mitä Draft tekee.

### Kehittäjän mittaukset {#measured-by-the-developer}

Sama ONNX-tiedosto, sama tulos, RTX 5080:

| Taustaosa | Syvyyden läpimeno |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Testileike ONNX-polun läpi:

| Esiasetus | Säilytetyt kuvat | Syvyyden läpimeno |
|---|---|---|
| Draft | noin 1/7 | noin 50 /s |
| Balanced | noin 1/4 | noin 50 /s |
| Detailed | noin 1/2 | noin 40 /s |

Syvyys on selvästi nopeampi kuin kaappaus, joten elävä skannaus ei ole syvyydestä kiinni. Sovelluksen
ympäristö on noin 349 MiB ilman PyTorchia, kun torch CUDA:lla on noin 3,5 GB.

Offline-polku `reconstruct` on toinen asia: minuutteja 16 kuvan ikkunaa kohden pöytäkoneen GPU:lla.

## Muisti {#memory}

- Kuvia ei säilytetä yhdistämisen jälkeen, paitsi **160** kappaletta kierrosten värjäykseen.
- Skannaus pysähtyy oletuksena **3000** säilytettyyn kuvaan ("Views kept"), suojana.
- Elävän kaappauksen jono pitää 4 kuvaa; telemetrian asentopuskuri pitää 30 sekuntia.
- Molemmat voxelruudukot ovat harvoja, ja verkko puretaan lohko kerrallaan, joten muisti seuraa skannattua
  aluetta, ei rajauslaatikkoa.

## Alusta {#platform}

Skanneri ja Assetto Corsa -tallentimet ovat käytännössä vain Windowsilla: elävä kaappaus käyttää Windows Graphics
Capturea, pikanäppäimet ja läpinäkyvä peittokuva käyttävät Win32-rajapintaa, ja Kunos-sivut ovat Windowsin jaettua
muistia. Videotiedostoja voi skannata ja UDP-tallentimet toimivat muualla, mutta sitä ei ole tarkistettu.
