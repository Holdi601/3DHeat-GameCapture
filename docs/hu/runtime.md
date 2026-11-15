---
title: "Futtatás és függőségek"
nav_order: 8
lang: "hu"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Futtatás, függőségek és teljesítmény {#runtime-dependencies-and-performance}

Kód: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dupla kattintással indítsd. Csak kétféle dolgot csinál maga:

1. **Megkeresi a Pythont** (`python`, majd `py`). Ha nincs, megkérdezi: `Install it now with winget [Y,N]?` (Telepítsem most a winget segítségével? [I/N]). Igen esetén lefuttatja a `winget install -e --id Python.Python.3.12` parancsot, majd kéri, hogy zárd be az ablakot, és futtasd újra a `scan.bat`-ot, hogy a Windows felvegye az új PATH-et. Nem esetén semmi nem települ.
2. **Létrehoz egy privát környezetet**, a `.venv`-et a `scan.bat` mellé, ha nincs még, és frissíti a pip-jét – így semmi nem települ a rendszer Pythonjába.

Ezután lefuttatja a `.venv\Scripts\python.exe -m heat3d_capture.ui` parancsot. Minden más – a hiányzók megállapítása, magyarázat arról, mire kellenek, kérdezés – a Pythonban történik, párbeszédablakban.

## Első indítás előtti ellenőrzés {#first-run-preflight}

Mielőtt az ablak bármi nehezet importálna, minden követelményt ellenőrzünk (`importlib.util.find_spec`-kel, így egy félig eltávolított csomag hiányzónak számít). A szabályok:

- **Mindent először ellenőrzünk.** A teljes lista összegyűlik, mielőtt bármit mondanánk, így egy csomag javítása nem vezet közvetlenül a következő hibához.
- **Kérdezünk, sosem feltételezünk.** A párbeszédablak minden hiányzó csomagot felsorol, megmondja, mire kell, és a teljes letöltési méretet, és a **Download and install** (Letöltés és telepítés) gomb nélkül nem csinál semmit. A Mégse kilép: „Nothing was installed and nothing was changed.” (Semmi nem települt, és semmi nem változott.)
- **A hallgatás nem beleegyezés.** Qt nélkül az ellenőrzés a konzolra esik vissza, és megkérdezi: `Install them now? [Y/n]` (Telepítsem most? [I/n]) (Enter, `y`, `yes`, `j`, `ja` mind igent jelent); terminál nélkül, ahol válaszolni lehetne (bemenet vége), nem telepít semmit.
- **Ebbe az eszköz saját környezetébe.** A telepítés `<futó python> -m pip install ...` alfolyamatként – a `scan.bat`-tal a privát `.venv`-be. Ha elbukik, a párbeszédablak megmutatja a pip kimenetének utolsó sorát, és a parancsot, amellyel kézzel próbálhatod.

| Csomag | Importálva mint | Megjelenítve úgy, mire való | Hozzávetőleges letöltés |
|---|---|---|---|
| numpy | `numpy` | az aritmetika, amelyre minden más épül | 20 MB |
| opencv-python | `cv2` | videófájlok és kamerakockák olvasása | 40 MB |
| onnxruntime-directml Windowson, egyébként onnxruntime | `onnxruntime` | a mélységmodell futtatása a grafikus kártyán | 120 MB |
| PySide6-Essentials | `PySide6` | az ablak és a vezérlői | 90 MB |
| scipy | `scipy` | a rekonstruált felület simítása | 45 MB |
| scikit-image | `skimage` | mérések átalakítása 3D-felületté | 30 MB |
| windows-capture | `windows_capture` | játékablak élő rögzítése (opcionális: nélküle a videófájlok továbbra is működnek) | 5 MB |

A mélységmodell átalakításához további három kell, külön kérve, és csak akkor, ha megnyomod a „Set up the depth model” (Mélységmodell beállítása) gombot: `torch` (körülbelül 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). A szkenner maga soha nem importálja őket.

Az offline `reconstruct` parancsnak saját ellenőrzése van, amely a licencsor kiírása után fut, és csak a terminálban: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, és a `vggt` a Meta GitHub-tárolójából (`--no-deps`-szel telepítve, mert a metaadatai a numpy-t 2 alá szorítják). Ugyanez a lista a `requirements-offline.txt`; lásd [Offline rekonstrukció](reconstruction-offline.md#requirements).

Az ONNX Runtime csomag, amelyet kínálnak, az, amelyet a `requirements.txt` választ a platformra: Windowson `onnxruntime-directml`, máshol `onnxruntime`. Ha az `onnxruntime` már importálható (például `onnxruntime-gpu`), semmi nem települ: az ellenőrzés modulnév szerint történik.

## Kézi telepítés {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

A `requirements.txt` rögzíti: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (csak Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` Windowson és `onnxruntime>=1.19` máshol.

A `requirements-offline.txt` azt teszi hozzá, amire csak a `reconstruct` van szüksége: `transformers`, `einops`, `safetensors`, `huggingface_hub` és `Pillow`, a `vggt` telepítési sorral (`--no-deps`) és a VGGT licencmegjegyzéssel a fejlécében. A PyTorch sincs benne, az alábbi okból.

**A PyTorch szándékosan hiányzik.** A megfelelő wheel a GPU-tól és a CUDA-verziótól függ, és egy rögzítése CPU-s buildet telepítene azokra a gépekre, amelyeknek leginkább a GPU-s kell. Ha kell (modellátalakítás, az offline `reconstruct` út), a PyTorchot **a** `requirements.txt` előtt telepítsd: a torch wheelek numpy 1.x-re állhatnak, amellyel a scipy nem hajlandó futni, és a hiba így jelenik meg: `module numpy has no attribute long`, a scipy belsejéből, messze az okától.

Az `onnxruntime-directml` és az `onnxruntime-gpu` ütközik: csak az egyiket telepítsd.

A fejlesztő által ellenőrizve: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, NVIDIA RTX 5080-on, és ugyanez a környezet NVIDIA-specifikus csomag nélkül.

## Következtetési háttérprogramok {#inference-backends}

Az ONNX Runtime a GPU-khoz végrehajtó szolgáltatókon (execution provider) keresztül jut el, és az, hogy melyek léteznek, attól függ, hogyan telepítették az onnxruntime-ot, nem a hardvertől. Ezért az elérhetőséget megtaláljuk, a legjobbtól kezdve:

| Rang | Szolgáltató | Megjelenítve úgy | Hardver |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | bármely Direct3D 12 GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | bármi |

A **DirectML az alapértelmezett telepítés**, mert AMD- és Intel-GPU-kat is elér, nem csak NVIDIA-kat. Az NVIDIA saját szolgáltatóival gyorsabb – az `onnxruntime-gpu` telepítése CUDA-t ad, és az ablak megmondja, ha NVIDIA-kártyát lát DirectML-en futni –, de az NVIDIA nem lehet az egyetlen választás. A CPU mindig az utolsó, így egy használható GPU nélküli gép lassú szkennelést kap, nem semmit, és a GPU-s munkamenet létrehozásakor tartalékként hozzá van fűzve.

Az adapter neve a Windows megjelenítőadapter-osztály regiszterkulcsából olvasódik (nem egy gyártói eszközből, mint az `nvidia-smi`, amely csak néhány gépen létezik), a Basic Render Driver-t kihagyva. A gyártóhoz kötött szolgáltatók a megfelelő adaptert nevezik meg; a DirectML az első felsorolt adapteren látszik, amely a rendszer alapértelmezett. A név csak megjelenítésre szolgál.

A `ScanSettings.prefer_backend` (csak szkriptekből) megnevezhet egy szolgáltatót vagy egy rövid nevet.

## Mit várj ettől a géptől {#what-to-expect-from-this-machine}

Az ablak indításkor a bemelegítés utáni 6 képkockán méri a mélységmodell tényleges átviteli sebességét ezen a gépen, ahelyett, hogy a GPU-t egy táblázatban keresné fel (a hőállapot, a laptop energiaprofiljai és az illesztőprogram-verziók túl sokat mozgatják), és a szkennelés előtt megmondja, milyen lesz: 

| Mért képkocka másodpercenként | Szint | Címsor | Tanács |
|---|---|---|---|
| 25 vagy több | valós idejű | Élő szkennelés teljes részletességgel. | Normál tempóban sétálj; az átfedés lépést tud tartani. |
| 12 és 25 között | működőképes | Élő szkennelés, kevesebb megtartott nézettel, mint teljes sebességnél. | Sétálj lassan, és fordulj finoman – a gyors fordulók hézagokat hagynak. A Draft kevesebb nézetet tart meg, ami segít a mélységmodellnek lépést tartani. |
| 2 és 12 között | lassú | Először rögzíts, utána rekonstruálj. | Vegyél fel egy videót a sétáról, és utána a fájlból rekonstruálj. Az eredmény azonos; csak a visszajelzés nem élő. |
| 2 alatt | kivitelezhetetlen | Ez a gép túl lassú a hasznos szkenneléshez. | Rövidebb útvonal, vagy kisebb modell. **Az indítás le van tiltva.** |

A CPU-n a megjegyzés hozzáteszi, hogy a `onnxruntime-directml` telepítése Windowson általában megoldja. Semmi nem változtatja meg önmagában a rögzítési felbontást: nem segítene, mert a mélységmodell bármit is kap, a fix bemeneti méretén fut; a lassúbb gépet az tartja fenn, ha kevesebb nézetet tartunk meg, ezt csinálja a Draft.

### A fejlesztő által mérve {#measured-by-the-developer}

Ugyanaz az ONNX-fájl, ugyanaz a kimenet, RTX 5080:

| Háttér | Mélységi átvitel |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Egy teszt-felvétel a kiszállított ONNX-úton:

| Preset | Megtartott nézetek | Mélységi átvitel |
|---|---|---|
| Draft | körülbelül 1 a 7-ből | körülbelül 50 /s |
| Balanced | körülbelül 1 a 4-ből | körülbelül 50 /s |
| Detailed | körülbelül 1 a 2-ből | körülbelül 40 /s |

A mélység kényelmesen gyorsabb, mint a rögzítés, így az élő szkennelést nem a mélység korlátozza. Az alkalmazás környezete körülbelül 349 MiB PyTorch nélkül, szemben a CUDA-s torch körülbelül 3,5 GB-jával.

Az offline `reconstruct` út más: percek egy 16 képkockás ablakonként egy asztali GPU-n.

## Memória {#memory}

- A képkockák összeolvasztás után nincsenek megtartva, kivéve **160**-at a háló színezéséhez.
- A szkennelés alapértelmezetten **3000** megtartott nézetnél megáll („Views kept” – Megtartott nézetek), védelemként.
- Az élő rögzítési sor 4 képkockát tart; a telemetriapóz-puffer 30 másodpercet.
- Mindkét voxelrács ritka, és a háló blokkonként kerül kinyerésre, így a memória a beszkennelt területet követi, nem a befoglaló téglatestet.

## Platform {#platform}

A szkenner és az Assetto Corsa rögzítők gyakorlatilag csak Windowson működnek: az élő rögzítés a Windows Graphics Capture-t használja, a gyorsbillentyűk és a kattintásáteresztő átfedés a Win32 API-t, az Assetto Corsa oldalak pedig Windows megosztott memóriát. A videófájlok átvizsgálhatók, és az UDP-rögzítők máshol is futnak, de ezt nem ellenőriztük.
