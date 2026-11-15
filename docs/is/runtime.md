---
title: "Keyrsluumhverfi og ósjálfstæði"
nav_order: 8
lang: "is"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Keyrsluumhverfi, ósjálfstæði og afköst {#runtime-dependencies-and-performance}

Kóði: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Tvísmelltu á hana. Hún gerir aðeins tvennt sjálf:

1. **Finnur Python** (`python`, svo `py`). Ef ekkert er til spyr hún
   `Install it now with winget [Y,N]?`; við Y keyrir hún
   `winget install -e --id Python.Python.3.12`, biður þig síðan að loka glugganum og keyra
   `scan.bat` aftur svo Windows taki upp nýja PATH. Við N er engu sett upp.
2. **Býr til einkaumhverfi**, `.venv` við hlið `scan.bat`, ef ekkert er til, og uppfærir
   pip þess - svo engu er sett upp í kerfis-Python.

Síðan keyrir hún `.venv\Scripts\python.exe -m heat3d_capture.ui`. Allt annað - að finna út hvað
vantar, segja til hvers það er, spyrja - gerist í Python, sem gluggi.

## Forathugun við fyrstu keyrslu {#first-run-preflight}

Áður en glugginn flytur inn nokkuð þungt er hver krafa athuguð (með
`importlib.util.find_spec`, svo hálffjarlægður pakki telst vanta). Reglurnar:

- **Allt er athugað fyrst.** Allur listinn er safnaður áður en nokkuð er sagt, svo að laga
  einn pakka leiði ekki beint í næstu villu.
- **Spyrja, aldrei gera ráð fyrir.** Glugginn telur upp hvern pakka sem vantar, til hvers hann er og heildar
  niðurhalið, og gerir ekkert án **Download and install**. Hætta við lokar: „Nothing was
  installed and nothing was changed.“
- **Þögn er ekki samþykki.** Án Qt fellur athugunin aftur á skipanalínuna og spyr
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` þýða já); með ekkert Terminal til að svara í
  (lok inntaks) setur hún ekkert upp.
- **Í eigið umhverfi tólsins.** Uppsetning er `<running python> -m pip install ...` sem
  undirferli - með `scan.bat`, einkaumhverfið `.venv`. Ef hún mistekst sýnir glugginn síðustu línu
  úr úttaki pip og skipunina til að prófa í höndunum.

| Pakki | Fluttur inn sem | Sýnt sem til hvers hann er | Áætlað niðurhal |
|---|---|---|---|
| numpy | `numpy` | reikningurinn sem allt annað byggir á | 20 MB |
| opencv-python | `cv2` | að lesa myndbandsskrár og myndavélarramma | 40 MB |
| onnxruntime-directml á Windows, onnxruntime annars staðar | `onnxruntime` | að keyra dýptarlíkanið á skjákortinu þínu | 120 MB |
| PySide6-Essentials | `PySide6` | glugginn og stýringar hans | 90 MB |
| scipy | `scipy` | að slétta endurgerða yfirborðið | 45 MB |
| scikit-image | `skimage` | að breyta mælingum í 3D yfirborð | 30 MB |
| windows-capture | `windows_capture` | að taka upp leikjaglugga í beinni (valfrjálst: án hans virka myndbandsskrár samt) | 5 MB |

Til að umbreyta dýptarlíkaninu þarf þrjá í viðbót, beðið um sér og aðeins þegar þú ýtir á „Set up
the depth model“: `torch` (um 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Skanninn
sjálfur flytur þá aldrei inn.

Offline `reconstruct` skipunin hefur sína eigin athugun, keyrða eftir að hún prentar leyfislínuna
og aðeins í Terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, og `vggt` úr GitHub geymslu Meta (sett upp með `--no-deps`,
því lýsigögn hans festa numpy undir 2). Sami listi er `requirements-offline.txt`; sjá
[Offline endurgerð](reconstruction-offline.md#requirements).

ONNX Runtime pakkinn sem boðinn er er sá sem `requirements.txt` velur fyrir kerfið:
`onnxruntime-directml` á Windows, `onnxruntime` annars staðar. Ef `onnxruntime` er þegar
hægt að flytja inn (til dæmis `onnxruntime-gpu`) er engu sett upp: athugunin er eftir heiti einingarinnar.

## Uppsetning í höndunum {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` festir: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(aðeins Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` á Windows og `onnxruntime>=1.19` annars staðar.

`requirements-offline.txt` bætir við því sem aðeins `reconstruct` þarf: `transformers`, `einops`,
`safetensors`, `huggingface_hub` og `Pillow`, með `vggt` uppsetningarlínunni (`--no-deps`) og
athugasemd um VGGT leyfið í haus sínum. PyTorch er ekki í honum heldur, af ástæðunni hér að neðan.

**PyTorch vantar viljandi.** Rétta wheel-skráin fer eftir skjákortinu og CUDA útgáfu, og að festa
eina myndi setja upp CPU útgáfu á vélunum sem þurfa mest á GPU útgáfunni að halda. Ef þú vilt það (umbreyting líkans,
offline `reconstruct` leiðin), settu það upp **á undan** `requirements.txt`: torch
wheel-skrárnar geta endað á numpy 1.x, sem scipy neitar þá að keyra gegn, og bilunin birtist sem
`module numpy has no attribute long` innan úr scipy, víðs fjarri orsökinni.

`onnxruntime-directml` og `onnxruntime-gpu` rekast á: settu aðeins upp annan.

Staðfest af þróunaraðila: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, á NVIDIA
RTX 5080, og sama umhverfi án nokkurs NVIDIA-sértæks pakka.

## Ályktunarbakendar {#inference-backends}

ONNX Runtime nær í skjákort um keyrsluveitendur (execution providers), og hverjir eru til fer eftir því hvernig
onnxruntime var sett upp, ekki eftir vélbúnaðinum. Því er framboð uppgötvað, besti fyrst:

| Sæti | Veitandi | Sýnt sem | Vélbúnaður |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | hvaða Direct3D 12 skjákort sem er: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | hvað sem er |

**DirectML er sjálfgefin uppsetning** því það nær til AMD og Intel skjákorta jafnt sem NVIDIA.
NVIDIA er hraðara með eigin veitendur - að setja upp `onnxruntime-gpu` bætir við CUDA, og glugginn
segir frá því þegar hann sér NVIDIA kort keyra á DirectML - en NVIDIA má ekki vera eini
kosturinn. CPU er alltaf síðast, svo vél án nothæfs skjákorts fær hæga skönnun frekar en enga, og
honum er bætt við sem varaleið þegar GPU seta er búin til.

Heiti millistykkisins er lesið úr Windows skjámillistykkis-lyklinum í registry (ekki úr
framleiðandaverkfæri eins og `nvidia-smi`, sem er aðeins til á sumum vélum), og Basic Render
Driver sleppt. Veitendur bundnir framleiðanda nefna samsvarandi millistykki; DirectML er sýnt á fyrsta
talda millistykkinu, sem er kerfissjálfgefið. Heitið er aðeins til sýnis.

`ScanSettings.prefer_backend` (aðeins skriftur) getur nefnt veitanda eða stutt heiti.

## Hverju á að búast við frá þessari vél {#what-to-expect-from-this-machine}

Glugginn mælir raunverulega afkastagetu dýptarlíkansins á þessari vél við ræsingu (6 rammar eftir
upphitun) í stað þess að fletta skjákortinu upp í töflu - hitastaða, orkusnið fartölvu og
rekilsútgáfur hreyfa það of mikið - og segir hvernig skönnun verður áður en nokkuð getur byrjað:

| Mældar sýnir á sekúndu | Stig | Fyrirsögn | Ráð |
|---|---|---|---|
| 25 eða fleiri | realtime | Live scanning at full detail. | Walk at a normal pace; the overlay will keep up. |
| 12 til 25 | workable | Live scanning, with fewer views kept than at full speed. | Walk slowly and turn gently — fast turns will leave gaps. Draft keeps fewer views, which helps the depth model keep up. |
| 2 til 12 | slow | Record first, reconstruct afterwards. | Record a video of the walk and reconstruct from the file afterwards. The result is identical; only the feedback is not live. |
| undir 2 | impractical | This machine is too slow to scan usefully. | A shorter route, or a smaller model. **Start er óvirkt.** |

Á CPU bætir athugasemdin við að uppsetning `onnxruntime-directml` lagar það yfirleitt á Windows. Ekkert
breytir upptökuupplausn sjálfkrafa: það myndi ekki hjálpa, því dýptarlíkanið keyrir á
fastri inntaksstærð sinni hvað sem því er gefið; það sem heldur hægari vél á floti er að geyma færri sýnir,
sem er það sem Draft gerir.

### Mælt af þróunaraðila {#measured-by-the-developer}

Sama ONNX skrá, sama úttak, RTX 5080:

| Bakendi | Dýptarafköst |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Prufumyndskeið í gegnum ONNX leiðina sem fylgir með:

| Forstilling | Sýnir geymdar | Dýptarafköst |
|---|---|---|
| Draft | um 1 af 7 | um 50 /s |
| Balanced | um 1 af 4 | um 50 /s |
| Detailed | um 1 af 2 | um 40 /s |

Dýpt er þægilega hraðari en upptakan, svo bein skönnun er ekki bundin af dýpt. Umhverfi forritsins
er um 349 MiB án PyTorch, á móti um 3,5 GB fyrir torch með CUDA.

Offline `reconstruct` leiðin er önnur: mínútur á hvern 16 ramma glugga á skjáborðsskjákorti.

## Minni {#memory}

- Rammar eru ekki geymdir eftir samruna, nema **160** til að lita möskvann.
- Skönnun stöðvast við **3000** geymdar sýnir sjálfgefið („Views kept“), sem varnagli.
- Biðröð beinnar upptöku geymir 4 ramma; stöðubiðminni mælingagagna 30 sekúndur.
- Bæði voxelristin eru gisin og möskvinn er unninn út blokk fyrir blokk, svo minni fylgir því sem
  var skannað, ekki umlykjandi kassanum.

## Stýrikerfi {#platform}

Skanninn og Assetto Corsa upptökutækin eru í reynd aðeins fyrir Windows: bein upptaka notar Windows
Graphics Capture, flýtilyklarnir og yfirlagið sem hleypir smellum í gegn nota Win32 API, og Kunos blöðin
eru Windows sameiginlegt minni. Hægt er að skanna myndbandsskrár og UDP upptökutækin keyra annars staðar, en það
hefur ekki verið athugað.
