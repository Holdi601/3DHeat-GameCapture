---
title: "Kørsel, afhængigheder og ydeevne"
nav_order: 8
lang: "da"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Kørsel, afhængigheder og ydeevne {#runtime-dependencies-and-performance}

Kode: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dobbeltklik på den. Den gør kun to ting selv:

1. **Finder Python** (`python`, derefter `py`). Findes der ingen, spørger den `Install it now with winget [Y,N]?`; ved Y kører den `winget install -e --id Python.Python.3.12` og beder dig så lukke vinduet og køre `scan.bat` igen, så Windows opfanger den nye PATH. Ved N installeres intet.
2. **Opretter et privat miljø**, `.venv` ved siden af `scan.bat`, hvis der ikke er et, og opgraderer dets pip - så intet installeres i systemets Python.

Derefter kører den `.venv\Scripts\python.exe -m heat3d_capture.ui`. Alt andet - at finde ud af, hvad der mangler, forklare hvad det er til, spørge - sker i Python, som en dialog.

## Første-gangs-tjek {#first-run-preflight}

Før vinduet importerer noget tungt, tjekkes alle krav (med `importlib.util.find_spec`, så en halvt fjernet pakke tæller som manglende). Reglerne:

- **Alt tjekkes først.** Hele listen samles, før noget siges, så en rettelse af én pakke aldrig fører direkte til den næste fejl.
- **Spørg, gæt aldrig.** Dialogen lister hver manglende pakke, hvad den er til, og den samlede download, og gør ingenting uden **Download and install**. Annuller afslutter: "Nothing was installed and nothing was changed."
- **Tavshed er ikke samtykke.** Uden Qt falder tjekket tilbage til konsollen og spørger `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betyder ja); uden en terminal at svare i (slutningen af input) installeres intet.
- **Ind i dette værktøjs eget miljø.** Installationen er `<kørende python> -m pip install ...` som en underproces - med `scan.bat` det private `.venv`. Hvis den fejler, viser dialogen den sidste linje af pips output og kommandoen at prøve i hånden.

| Pakke | Importeret som | Vist som hvad den er til | Ca. download |
|---|---|---|---|
| numpy | `numpy` | den aritmetik alt andet er bygget på | 20 MB |
| opencv-python | `cv2` | læsning af videofiler og kamerabilleder | 40 MB |
| onnxruntime-directml på Windows, onnxruntime ellers | `onnxruntime` | kørsel af dybdemodellen på dit grafikkort | 120 MB |
| PySide6-Essentials | `PySide6` | vinduet og dets kontroller | 90 MB |
| scipy | `scipy` | udjævning af den rekonstruerede overflade | 45 MB |
| scikit-image | `skimage` | omdannelse af målinger til en 3D-overflade | 30 MB |
| windows-capture | `windows_capture` | live-optagelse af et spilvindue (valgfri: uden den virker videofiler stadig) | 5 MB |

Konvertering af dybdemodellen kræver tre mere, spurgt om særskilt og kun når du trykker "Set up the depth model": `torch` (cirka 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Selve scanneren importerer dem aldrig.

Den offline `reconstruct`-kommando har et tjek for sig selv, kørt efter den skriver licenslinjen og kun i terminalen: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, og `vggt` fra Metas GitHub-repository (installeret med `--no-deps`, fordi dets metadata fastlægger numpy under 2). Den samme liste findes i `requirements-offline.txt`; se [Offline-rekonstruktion](reconstruction-offline.md#requirements).

ONNX Runtime-pakken, der tilbydes, er den, `requirements.txt` vælger for platformen: `onnxruntime-directml` på Windows, `onnxruntime` ellers. Hvis `onnxruntime` allerede kan importeres (for eksempel `onnxruntime-gpu`), installeres intet: tjekket sker på modulnavn.

## Installation i hånden {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fastlægger: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (kun Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` på Windows og `onnxruntime>=1.19` ellers.

`requirements-offline.txt` tilføjer det, kun `reconstruct` har brug for: `transformers`, `einops`, `safetensors`, `huggingface_hub` og `Pillow`, med installationslinjen for `vggt` (`--no-deps`) og VGGT-licensnoten i sin header. PyTorch er heller ikke med i den, af grunden nedenfor.

**PyTorch er bevidst udeladt.** Det rigtige hjul afhænger af GPU'en og CUDA-versionen, og at fastlægge ét ville installere en CPU-build på de maskiner, der mest har brug for GPU-builden. Vil du have den (modelkonvertering, den offline `reconstruct`-sti), så installér den **før** `requirements.txt`: torch-hjulene kan lande på numpy 1.x, som scipy så nægter at køre mod, og fejlen viser sig som `module numpy has no attribute long` inde fra scipy, langt fra årsagen.

`onnxruntime-directml` og `onnxruntime-gpu` er i konflikt: installér kun den ene.

Verificeret af udvikleren: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, på en NVIDIA RTX 5080, og det samme miljø uden nogen NVIDIA-specifik pakke.

## Inferensbackends {#inference-backends}

ONNX Runtime når GPU'er gennem udbydere (execution providers), og hvilke der findes, afhænger af hvordan onnxruntime blev installeret, ikke af hardwaren. Så tilgængelighed opdages, bedste først:

| Rang | Udbyder | Vist som | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | enhver Direct3D 12-GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | alt |

**DirectML er standardinstallationen**, fordi den også når AMD- og Intel-GPU'er ud over NVIDIA. NVIDIA er hurtigere med sine egne udbydere - installation af `onnxruntime-gpu` tilføjer CUDA, og vinduet siger det, når det ser et NVIDIA-kort køre på DirectML - men NVIDIA må ikke være den eneste mulighed. CPU står altid sidst, så en maskine uden en brugbar GPU får en langsom scanning frem for ingen, og den tilføjes som reserve, når en GPU-session oprettes.

Adapterens navn læses fra Windows' display-adapterklasse i registret (ikke fra et leverandørværktøj som `nvidia-smi`, som kun findes på nogle maskiner), og Basic Render Driver springes over. Leverandørlåste udbydere navngiver den matchende adapter; DirectML vises på den første opregnede adapter, som er systemstandarden. Navnet er kun til visning.

`ScanSettings.prefer_backend` (kun scripts) kan navngive en udbyder eller et kort navn.

## Hvad du kan forvente af denne maskine {#what-to-expect-from-this-machine}

Vinduet måler dybdemodellens faktiske gennemløb på denne maskine ved opstart (6 billeder efter en opvarmning) i stedet for at slå GPU'en op i en tabel - termisk tilstand, bærbare strømprofiler og driverversioner flytter den for meget - og siger, hvordan en scanning vil være, før noget kan starte:

| Målte billeder pr. sekund | Niveau | Overskrift | Råd |
|---|---|---|---|
| 25 eller mere | realtid | Live scanning at full detail. | Gå i et normalt tempo; overlayet følger med. |
| 12 til 25 | brugbar | Live scanning, with fewer views kept than at full speed. | Gå langsomt og drej blidt - hurtige sving efterlader huller. Draft beholder færre billeder, hvilket hjælper dybdemodellen med at følge med. |
| 2 til 12 | langsom | Record first, reconstruct afterwards. | Optag en video af turen og rekonstruér fra filen bagefter. Resultatet er identisk; kun feedbacken er ikke live. |
| under 2 | upraktisk | This machine is too slow to scan usefully. | En kortere rute, eller en mindre model. **Start er deaktiveret.** |

På CPU tilføjer noten, at installation af `onnxruntime-directml` normalt retter det på Windows. Intet ændrer optageopløsningen af sig selv: det ville ikke hjælpe, fordi dybdemodellen kører i sin faste inputstørrelse, uanset hvad den får; det, der holder en langsommere maskine oppe, er færre beholdte billeder, og det er det, Draft gør.

### Målt af udvikleren {#measured-by-the-developer}

Samme ONNX-fil, samme output, RTX 5080:

| Backend | Dybdegennemløb |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Et testklip gennem den leverede ONNX-sti:

| Forudindstilling | Beholdte billeder | Dybdegennemløb |
|---|---|---|
| Draft | cirka 1 ud af 7 | cirka 50 /s |
| Balanced | cirka 1 ud af 4 | cirka 50 /s |
| Detailed | cirka 1 ud af 2 | cirka 40 /s |

Dybde er komfortabelt hurtigere end optagelse, så live-scanning er ikke bundet af dybden. Appens miljø er cirka 349 MiB uden PyTorch, mod cirka 3,5 GB for torch med CUDA.

Den offline `reconstruct`-sti er anderledes: minutter pr. 16-billeders vindue på en desktop-GPU.

## Hukommelse {#memory}

- Billeder gemmes ikke efter fusion, undtagen **160** til farvning af mesh'en.
- En scanning stopper ved **3000** beholdte visninger som standard ("Views kept"), som en beskyttelse.
- Optageoptagelseskøen holder 4 billeder; telemetri-positionsbufferen 30 sekunder.
- Begge voxelgitre er sparsede, og mesh'en udtrækkes blok for blok, så hukommelsen følger det, der er scannet, ikke den omsluttende boks.

## Platform {#platform}

Scanneren og Assetto Corsa-optagerne er i praksis kun til Windows: live-optagelse bruger Windows Graphics Capture, genvejstasterne og det klik-igennem-overlay bruger Win32-API'et, og Kunos-siderne er Windows-delt hukommelse. Videofiler kan scannes, og UDP-optagerne kører andre steder, men det er ikke kontrolleret.
