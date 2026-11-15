---
title: "Runtime dhe varësitë"
nav_order: 8
lang: "sq"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, varësitë dhe performanca {#runtime-dependencies-and-performance}

Kodi: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Kliko dy herë mbi të. Vetë ai bën vetëm dy gjëra:

1. **Gjen Python** (`python`, pastaj `py`). Nëse nuk ka, pyet
   `Install it now with winget [Y,N]?`; me Y ekzekuton
   `winget install -e --id Python.Python.3.12`, pastaj të kërkon ta mbyllësh dritaren dhe të ekzekutosh
   `scan.bat` përsëri që Windows të marrë PATH-in e ri. Me N nuk instalohet asgjë.
2. **Krijon një mjedis privat**, `.venv` pranë `scan.bat`, nëse nuk ka, dhe përditëson
   pip-in e tij - kështu që asgjë nuk instalohet në Python-in e sistemit.

Pastaj ekzekuton `.venv\Scripts\python.exe -m heat3d_capture.ui`. Çdo gjë tjetër - zbulimi i asaj që
mungon, të thuhet për çfarë shërben, pyetja - ndodh në Python, si dialog.

## Kontrolli paraprak në ekzekutimin e parë {#first-run-preflight}

Para se dritarja të importojë ndonjë gjë të rëndë, kontrollohet çdo kërkesë (me
`importlib.util.find_spec`, kështu që një paketë e hequr përgjysmë numërohet si e munguar). Rregullat:

- **Gjithçka kontrollohet e para.** Lista e plotë mblidhet para se të thuhet ndonjë gjë, kështu që rregullimi i
  një pakete nuk të çon drejtpërdrejt te gabimi tjetër.
- **Pyet, mos supozo kurrë.** Dialogu liston çdo paketë që mungon, për çfarë shërben, dhe shkarkimin
  total, dhe nuk bën asgjë pa **Download and install**. Anulimi del: "Nothing was
  installed and nothing was changed."
- **Heshtja nuk është pëlqim.** Pa Qt kontrolli kalon te konsola dhe pyet
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` do të thonë po); pa terminal për të përgjigjur
  (fund i hyrjes), nuk instalon asgjë.
- **Në mjedisin e vetë këtij mjeti.** Instalimi është `<running python> -m pip install ...` si
  nënproces - me `scan.bat`, `.venv` privat. Nëse dështon, dialogu tregon rreshtin e fundit
  të daljes së pip dhe komandën për ta provuar me dorë.

| Paketa | Importohet si | Shfaqet si ajo për çfarë shërben | Shkarkim përafërsisht |
|---|---|---|---|
| numpy | `numpy` | aritmetika mbi të cilën është ndërtuar gjithçka tjetër | 20 MB |
| opencv-python | `cv2` | leximi i skedarëve video dhe i kuadrove të kamerës | 40 MB |
| onnxruntime-directml në Windows, onnxruntime gjetkë | `onnxruntime` | ekzekutimi i modelit të thellësisë në kartën tënde grafike | 120 MB |
| PySide6-Essentials | `PySide6` | dritarja dhe kontrollet e saj | 90 MB |
| scipy | `scipy` | zbutja e sipërfaqes së rindërtuar | 45 MB |
| scikit-image | `skimage` | kthimi i matjeve në një sipërfaqe 3D | 30 MB |
| windows-capture | `windows_capture` | kapja e drejtpërdrejtë e dritares së një loje (opsionale: pa të, skedarët video funksionojnë prapë) | 5 MB |

Konvertimi i modelit të thellësisë ka nevojë për tri të tjera, të kërkuara veçmas dhe vetëm kur shtyp "Set up
the depth model": `torch` (rreth 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Vetë skaneri
nuk i importon kurrë.

Komanda offline `reconstruct` ka një kontroll të vetin, që ekzekutohet pasi printon rreshtin e licencës
dhe vetëm në terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, dhe `vggt` nga depoja GitHub e Meta (instaluar me `--no-deps`,
sepse metadatat e tij fiksojnë numpy nën 2). E njëjta listë është `requirements-offline.txt`; shih
[Rindërtimi offline](reconstruction-offline.md#requirements).

Paketa ONNX Runtime që ofrohet është ajo që `requirements.txt` zgjedh për platformën:
`onnxruntime-directml` në Windows, `onnxruntime` gjetkë. Nëse `onnxruntime` importohet tashmë
(për shembull `onnxruntime-gpu`), nuk instalohet asgjë: kontrolli bëhet sipas emrit të modulit.

## Instalimi me dorë {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fikson: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(vetëm Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` në Windows dhe `onnxruntime>=1.19` gjetkë.

`requirements-offline.txt` shton atë që i duhet vetëm `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` dhe `Pillow`, me rreshtin e instalimit të `vggt` (`--no-deps`) dhe
shënimin e licencës VGGT në kokën e tij. As PyTorch nuk është në të, për arsyen më poshtë.

**PyTorch mungon qëllimisht.** Rrota e duhur varet nga GPU-ja dhe versioni i CUDA, dhe fiksimi i
njërës do të instalonte një version CPU në makinat që kanë më shumë nevojë për atë GPU. Nëse e do (konvertimin e modelit,
rrugën offline `reconstruct`), instaloje **para** `requirements.txt`: rrotat e torch
mund të ngulen te numpy 1.x, me të cilin scipy refuzon pastaj të punojë, dhe dështimi shfaqet si
`module numpy has no attribute long` nga brenda scipy, larg shkakut të vet.

`onnxruntime-directml` dhe `onnxruntime-gpu` përplasen: instalo vetëm njërin.

Verifikuar nga zhvilluesi: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, në një NVIDIA
RTX 5080, dhe i njëjti mjedis pa asnjë paketë specifike NVIDIA në të.

## Backend-et e inferencës {#inference-backends}

ONNX Runtime arrin GPU-të përmes ofruesve të ekzekutimit, dhe cilët ekzistojnë varet nga mënyra si u instalua
onnxruntime, jo nga hardueri. Prandaj disponueshmëria zbulohet, më i miri i pari:

| Rendi | Ofruesi | Shfaqet si | Hardueri |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | çdo GPU Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | çdo gjë |

**DirectML është instalimi i paracaktuar** sepse arrin GPU-të AMD dhe Intel po aq sa NVIDIA.
NVIDIA është më e shpejtë me ofruesit e vet - instalimi i `onnxruntime-gpu` shton CUDA, dhe dritarja
e thotë këtë kur sheh një kartë NVIDIA që punon në DirectML - por NVIDIA nuk lejohet të jetë e vetmja
mundësi. CPU është gjithmonë e fundit, kështu që një makinë pa GPU të përdorshme merr një skanim të ngadaltë dhe jo asnjë, dhe
shtohet si rezervë kur krijohet një seancë GPU.

Emri i adaptorit lexohet nga çelësi i klasës së adaptorëve të ekranit të Windows në regjistër (jo nga një
mjet i prodhuesit si `nvidia-smi`, që ekziston vetëm në disa makina), duke anashkaluar Basic Render
Driver. Ofruesit e lidhur me prodhuesin emërtojnë adaptorin përkatës; DirectML shfaqet në adaptorin e parë
të numëruar, që është ai i paracaktuar i sistemit. Emri është vetëm për shfaqje.

`ScanSettings.prefer_backend` (vetëm skriptet) mund të emërtojë një ofrues ose një emër të shkurtër.

## Çfarë të presësh nga kjo makinë {#what-to-expect-from-this-machine}

Dritarja mat xhirimin real të modelit të thellësisë në këtë makinë në nisje (6 kuadro pas
ngrohjes) në vend që ta kërkojë GPU-në në një tabelë - gjendja termike, profilet e energjisë të laptopëve dhe
versionet e drajverëve e lëvizin shumë - dhe thotë si do të jetë një skanim para se të nisë ndonjë gjë:

| Pamje të matura në sekondë | Niveli | Titulli | Këshilla |
|---|---|---|---|
| 25 ose më shumë | realtime | Live scanning at full detail. | Walk at a normal pace; the overlay will keep up. |
| 12 deri 25 | workable | Live scanning, with fewer views kept than at full speed. | Walk slowly and turn gently — fast turns will leave gaps. Draft keeps fewer views, which helps the depth model keep up. |
| 2 deri 12 | slow | Record first, reconstruct afterwards. | Record a video of the walk and reconstruct from the file afterwards. The result is identical; only the feedback is not live. |
| nën 2 | impractical | This machine is too slow to scan usefully. | A shorter route, or a smaller model. **Start is disabled.** |

Në CPU shënimi shton se instalimi i `onnxruntime-directml` zakonisht e rregullon në Windows. Asgjë
nuk e ndryshon vetë rezolucionin e kapjes: nuk do të ndihmonte, sepse modeli i thellësisë punon në madhësinë e vet
të fiksuar të hyrjes çfarëdo që t'i jepet; ajo që e mban një makinë më të ngadaltë në nivel është mbajtja e më
pak pamjeve, gjë që bën Draft.

### Matur nga zhvilluesi {#measured-by-the-developer}

I njëjti skedar ONNX, e njëjta dalje, RTX 5080:

| Backend | Xhirimi i thellësisë |
|---|---|
| DirectML | 54 fps |
| CPU | 3.5 fps |

Një klip testues nëpër rrugën ONNX të shpërndarë:

| Paracaktimi | Pamje të mbajtura | Xhirimi i thellësisë |
|---|---|---|
| Draft | rreth 1 nga 7 | rreth 50 /s |
| Balanced | rreth 1 nga 4 | rreth 50 /s |
| Detailed | rreth 1 nga 2 | rreth 40 /s |

Thellësia është rehatshëm më e shpejtë se kapja, prandaj skanimi i drejtpërdrejtë nuk kufizohet nga thellësia. Mjedisi i
aplikacionit është rreth 349 MiB pa PyTorch, kundrejt rreth 3.5 GB për torch me CUDA.

Rruga offline `reconstruct` është ndryshe: minuta për çdo dritare 16-kuadroshe në një GPU desktopi.

## Memoria {#memory}

- Kuadrot nuk mbahen pas bashkimit, përveç **160** për ngjyrosjen e rrjetës.
- Një skanim ndalon në **3000** pamje të mbajtura si e paracaktuar ("Views kept"), si mbrojtje.
- Radha e kapjes së drejtpërdrejtë mban 4 kuadro; buferi i pozave të telemetrisë 30 sekonda.
- Të dy rrjetat e voxel-eve janë të rralla, dhe rrjeta nxirret bllok pas blloku, kështu që memoria ndjek atë që
  u skanua, jo kutinë kufizuese.

## Platforma {#platform}

Skaneri dhe regjistruesit e Assetto Corsa janë vetëm për Windows në praktikë: kapja e drejtpërdrejtë përdor Windows
Graphics Capture, tastet e shpejta dhe overlay që kalon klikimet përdorin API-n Win32, dhe faqet Kunos
janë memorie e përbashkët e Windows. Skedarët video mund të skanohen dhe regjistruesit UDP punojnë gjetkë, por kjo
nuk është kontrolluar.
