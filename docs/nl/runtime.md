---
title: "Runtime en afhankelijkheden"
nav_order: 8
lang: "nl"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, afhankelijkheden en prestaties {#runtime-dependencies-and-performance}

Code: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py), [`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py), [`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat), [`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dubbelklik erop. Het doet zelf maar twee dingen:

1. **Zoekt Python** (`python`, dan `py`). Is er geen, dan vraagt het `Install it now with winget [Y,N]?`; bij J draait het `winget install -e --id Python.Python.3.12`, en vraagt het je het venster te sluiten en `scan.bat` opnieuw te starten, zodat Windows het nieuwe PATH oppikt. Bij N wordt niets geïnstalleerd.
2. **Maakt een privéomgeving aan**, `.venv` naast `scan.bat`, als die er niet is, en werkt de pip ervan bij - zodat niets in de systeem-Python wordt geïnstalleerd.

Daarna draait het `.venv\Scripts\python.exe -m heat3d_capture.ui`. Al het andere - uitzoeken wat ontbreekt, uitleggen waarvoor het dient, vragen - gebeurt in Python, als dialoogvenster.

## Eerste-keer-controle {#first-run-preflight}

Voordat het venster iets zwaars importeert, wordt elke vereiste gecontroleerd (met `importlib.util.find_spec`, zodat een half verwijderd pakket als ontbrekend telt). De regels:

- **Alles wordt eerst gecontroleerd.** De volledige lijst wordt verzameld voordat er iets wordt gezegd, zodat het repareren van één pakket niet meteen naar de volgende fout leidt.
- **Vragen, nooit aannemen.** Het dialoogvenster toont elk ontbrekend pakket, waarvoor het dient, en het totale te downloaden volume, en doet niets zonder **Download and install**. Annuleren sluit af: "Nothing was installed and nothing was changed."
- **Stilte is geen toestemming.** Zonder Qt valt de controle terug op de console en vraagt `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betekenen ja); zonder terminal om te antwoorden (einde van de invoer) installeert het niets.
- **In de eigen omgeving van deze tool.** Installeren is `<draaiende python> -m pip install ...` als subproces - met `scan.bat` de eigen `.venv`. Mislukt het, dan toont het dialoogvenster de laatste regel van de uitvoer van pip en het commando om het met de hand te proberen.

| Pakket | Geïmporteerd als | Getoond als waarvoor het dient | Ongeveer te downloaden |
|---|---|---|---|
| numpy | `numpy` | de rekenkern waar al het andere op rust | 20 MB |
| opencv-python | `cv2` | videobestanden en cameraframes lezen | 40 MB |
| onnxruntime-directml op Windows, onnxruntime elders | `onnxruntime` | het dieptemodel op je videokaart draaien | 120 MB |
| PySide6-Essentials | `PySide6` | het venster en de bedieningselementen | 90 MB |
| scipy | `scipy` | het gereconstrueerde oppervlak gladstrijken | 45 MB |
| scikit-image | `skimage` | metingen omzetten naar een 3D-oppervlak | 30 MB |
| windows-capture | `windows_capture` | een spelvenster live opnemen (optioneel: zonder dit werken videobestanden nog steeds) | 5 MB |

Het omzetten van het dieptemodel vraagt er drie meer, apart gevraagd en alleen als je op "Set up the depth model" drukt: `torch` (ongeveer 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). De scanner zelf importeert ze nooit.

Het offline commando `reconstruct` heeft een eigen controle, die na het afdrukken van de licentieregel draait en alleen in de terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, en `vggt` van Meta's GitHub-repository (geïnstalleerd met `--no-deps`, omdat de metadata numpy onder 2 vastzet). Dezelfde lijst staat in `requirements-offline.txt`; zie [Offline reconstructie](reconstruction-offline.md#requirements).

Het ONNX Runtime-pakket dat wordt aangeboden, is het pakket dat `requirements.txt` voor het platform kiest: `onnxruntime-directml` op Windows, `onnxruntime` elders. Als `onnxruntime` al importeerbaar is (bijvoorbeeld `onnxruntime-gpu`), wordt niets geïnstalleerd: de controle is op modulenaam.

## Met de hand installeren {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` vastzet: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (alleen Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` op Windows en `onnxruntime>=1.19` elders.

`requirements-offline.txt` voegt toe wat alleen `reconstruct` nodig heeft: `transformers`, `einops`, `safetensors`, `huggingface_hub` en `Pillow`, met de installatieregel van `vggt` (`--no-deps`) en de VGGT-licentienotitie in de kop. PyTorch zit er ook niet in, om de reden hieronder.

**PyTorch staat er opzettelijk niet in.** Het juiste wiel hangt af van de GPU en de CUDA-versie, en er één vastzetten zou op de machines die de GPU-versie het hardst nodig hebben een CPU-build installeren. Als je het wilt (modelconversie, het offline pad `reconstruct`), installeer het **vóór** `requirements.txt`: de torch-wielen kunnen op numpy 1.x uitkomen, waar scipy dan niet mee wil draaien, en de fout verschijnt als `module numpy has no attribute long` binnen scipy, ver weg van de oorzaak.

`onnxruntime-directml` en `onnxruntime-gpu` botsen: installeer er maar één.

Geverifieerd door de ontwikkelaar: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, op een NVIDIA RTX 5080, en dezelfde omgeving zonder NVIDIA-specifiek pakket erin.

## Inferentiebackends {#inference-backends}

ONNX Runtime bereikt GPU's via execution providers, en welke er bestaan hangt af van hoe onnxruntime is geïnstalleerd, niet van de hardware. Dus wordt de beschikbaarheid ontdekt, de beste eerst:

| Rang | Provider | Getoond als | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | elke Direct3D 12-GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | alles |

**DirectML is de standaardinstallatie** omdat het ook AMD- en Intel-GPU's bereikt, naast NVIDIA. NVIDIA is sneller met de eigen providers - `onnxruntime-gpu` voegt CUDA toe, en het venster zegt dat wanneer het een NVIDIA-kaart ziet die op DirectML draait - maar NVIDIA mag niet de enige optie zijn. CPU staat altijd onderaan, dus een machine zonder bruikbare GPU krijgt een trage scan in plaats van geen, en het wordt als terugval toegevoegd wanneer een GPU-sessie wordt aangemaakt.

De naam van de adapter wordt gelezen uit de sleutel van de Windows-klasse voor beeldschermadapters in het register (niet uit een leverancierstool zoals `nvidia-smi`, die op sommige machines alleen bestaat), met overslag van de Basic Render Driver. Leverancier-gebonden providers noemen de bijpassende adapter; DirectML wordt op de eerste opgesomde adapter getoond, die de systeemstandaard is. De naam is alleen voor weergave.

`ScanSettings.prefer_backend` (alleen scripts) kan een provider noemen, volledig of kort.

## Wat je van deze machine kunt verwachten {#what-to-expect-from-this-machine}

Het venster meet bij het opstarten de werkelijke doorvoer van het dieptemodel op deze machine (6 frames na een opwarming) in plaats van de GPU in een tabel op te zoeken - de warmtetoestand, energieprofielen van laptops en stuurprogrammaversies bewegen het te veel - en zegt wat een scan zal zijn voordat er iets kan beginnen. De teksten in de tabel zijn wat het venster in het Engels toont:

| Gemeten beelden per seconde | Niveau | Kop | Advies |
|---|---|---|---|
| 25 of meer | realtime | Live scanning at full detail. | Walk at a normal pace; the overlay will keep up. |
| 12 tot 25 | workable | Live scanning, with fewer views kept than at full speed. | Walk slowly and turn gently — fast turns will leave gaps. Draft keeps fewer views, which helps the depth model keep up. |
| 2 tot 12 | slow | Record first, reconstruct afterwards. | Record a video of the walk and reconstruct from the file afterwards. The result is identical; only the feedback is not live. |
| minder dan 2 | impractical | This machine is too slow to scan usefully. | A shorter route, or a smaller model. **Start is disabled.** |

Op de CPU voegt de notitie toe dat het installeren van `onnxruntime-directml` op Windows dat meestal oplost. Niets verandert de opnameresolutie op zichzelf: dat zou niet helpen, omdat het dieptemodel op zijn vaste invoergrootte draait wat het ook krijgt; wat een tragere machine overeind houdt, is minder beelden houden, wat Draft doet.

### Gemeten door de ontwikkelaar {#measured-by-the-developer}

Zelfde ONNX-bestand, zelfde uitvoer, RTX 5080:

| Backend | Doorvoer van diepte |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Een testclip door het uitgeleverde ONNX-pad:

| Preset | Bewaarde beelden | Doorvoer van diepte |
|---|---|---|
| Draft | ongeveer 1 op 7 | ongeveer 50 /s |
| Balanced | ongeveer 1 op 4 | ongeveer 50 /s |
| Detailed | ongeveer 1 op 2 | ongeveer 40 /s |

Diepte is ruim sneller dan opname, dus is live scannen niet door diepte beperkt. De omgeving van de app is ongeveer 349 MiB zonder PyTorch, tegenover ongeveer 3,5 GB voor torch met CUDA.

Het offline commando `reconstruct` is anders: minuten per venster van 16 frames op een desktop-GPU.

## Geheugen {#memory}

- Frames worden na het samenvoegen niet bewaard, behalve **160** voor het inkleuren van het mesh.
- Een scan stopt standaard bij **3000** bewaarde beelden ("Views kept"), als bewaking.
- De wachtrij van de live opname houdt 4 frames; de telemetriepose-buffer 30 seconden.
- Beide voxelroosters zijn schaars, en het mesh wordt blok voor blok geëxtraheerd, dus het geheugen volgt wat er gescand is, niet het begrenzingsvak.

## Platform {#platform}

De scanner en de Assetto Corsa-opnemers werken in de praktijk alleen op Windows: live opname gebruikt Windows Graphics Capture, de sneltoetsen en de klik-doorheen-overlay gebruiken de Win32-API, en de Kunos-pagina's zijn gedeeld geheugen van Windows. Videobestanden kunnen worden gescand en de UDP-opnemers draaien ook elders, maar dat is niet gecontroleerd.
