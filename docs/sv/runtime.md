---
title: "Körmiljö, beroenden och prestanda"
nav_order: 8
lang: "sv"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Körmiljö, beroenden och prestanda {#runtime-dependencies-and-performance}

Kod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dubbelklicka den. Den gör bara två saker själv:

1. **Hittar Python** (`python`, sedan `py`). Finns ingen frågar den `Install it now with winget [Y,N]?`. Vid Y körs `winget install -e --id Python.Python.3.12`, och sedan ber den dig stänga fönstret och köra `scan.bat` igen så att Windows plockar upp den nya PATH:en. Vid N installeras inget.
2. **Skapar en privat miljö**, `.venv` bredvid `scan.bat`, om det inte finns någon, och uppgraderar dess pip. Så installeras ingenting i systemets Python.

Sedan kör den `.venv\Scripts\python.exe -m heat3d_capture.ui`. Allt annat (ta reda på vad som saknas, säga vad det är till för, fråga) sker i Python, som en dialog.

## Första körningens kontroll {#first-run-preflight}

Innan fönstret importerar något tungt kontrolleras varje krav (med `importlib.util.find_spec`, så ett halvt borttaget paket räknas som saknat). Reglerna:

- **Allt kontrolleras först.** Hela listan samlas innan något sägs, så att ett fixat paket aldrig leder direkt till nästa fel.
- **Fråga, anta aldrig.** Dialogen listar varje saknat paket, vad det är till för och den totala nedladdningen, och gör ingenting utan **Download and install**. Avbryt avslutar: "Nothing was installed and nothing was changed."
- **Tystnad är inte samtycke.** Utan Qt faller kontrollen tillbaka till konsolen och frågar `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` betyder ja). Utan terminal att svara i (slut på indata) installeras ingenting.
- **I verktygets egen miljö.** Installationen är `<körande python> -m pip install ...` som en underprocess. Med `scan.bat` är det den privata `.venv`. Om den misslyckas visar dialogen sista raden av pips utdata och kommandot att prova för hand.

| Paket | Importeras som | Visas som | Ungefärlig nedladdning |
|---|---|---|---|
| numpy | `numpy` | aritmetiken allt annat bygger på | 20 MB |
| opencv-python | `cv2` | läser videofiler och kamerabildrutor | 40 MB |
| onnxruntime-directml på Windows, onnxruntime annars | `onnxruntime` | kör djupmodellen på ditt grafikkort | 120 MB |
| PySide6-Essentials | `PySide6` | fönstret och dess kontroller | 90 MB |
| scipy | `scipy` | jämnar ut den rekonstruerade ytan | 45 MB |
| scikit-image | `skimage` | gör mätningar till en 3D-yta | 30 MB |
| windows-capture | `windows_capture` | fångar ett spelfönster live (valfri: utan det fungerar videofiler ändå) | 5 MB |

Att konvertera djupmodellen kräver tre till, som frågas efter separat och bara när du trycker på "Set up the depth model": `torch` (ungefär 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Skannern själv importerar dem aldrig.

Det offline-`reconstruct`-kommandot har en egen kontroll, som körs efter att det skrivit ut licensraden och bara i terminalen: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, och `vggt` från Metas GitHub-repo (installerad med `--no-deps`, eftersom dess metadata låser numpy under 2). Samma lista finns i `requirements-offline.txt`; se [Offline-rekonstruktion](reconstruction-offline.md#requirements).

ONNX Runtime-paketet som erbjuds är det `requirements.txt` väljer för plattformen: `onnxruntime-directml` på Windows, `onnxruntime` annars. Om `onnxruntime` redan går att importera (till exempel `onnxruntime-gpu`) installeras ingenting, eftersom kontrollen sker på modulnamn.

## Installera för hand {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fastställer: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (bara Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` på Windows och `onnxruntime>=1.19` annars.

`requirements-offline.txt` lägger till det bara `reconstruct` behöver: `transformers`, `einops`, `safetensors`, `huggingface_hub` och `Pillow`, med installationsraden för `vggt` (`--no-deps`) och VGGT-licensnoten i sin rubrik. PyTorch finns inte i den heller, av skälet nedan.

**PyTorch är medvetet utelämnat.** Rätt wheel beror på GPU:n och CUDA-versionen, och att fästa en skulle installera en CPU-build på de maskiner som behöver GPU-versionen mest. Vill du ha den (modellkonvertering, den offline `reconstruct`-vägen) installerar du den **före** `requirements.txt`: torch-wheels kan landa på numpy 1.x, som scipy då vägrar köra mot. Felet visar sig som `module numpy has no attribute long` inifrån scipy, långt från orsaken.

`onnxruntime-directml` och `onnxruntime-gpu` står i konflikt: installera bara en.

Verifierat av utvecklaren: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, på en NVIDIA RTX 5080, och samma miljö utan NVIDIA-specifikt paket i den.

## Inferensbackends {#inference-backends}

ONNX Runtime når GPU:er via execution providers, och vilka som finns beror på hur onnxruntime installerades, inte på hårdvaran. Så tillgängligheten upptäcks, bäst först:

| Rang | Leverantör | Visas som | Hårdvara |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | alla Direct3D 12-GPU:er: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | vad som helst |

**DirectML är standardinstallationen**, eftersom den når AMD- och Intel-GPU:er såväl som NVIDIA. NVIDIA är snabbare med sina egna leverantörer: att installera `onnxruntime-gpu` lägger till CUDA, och fönstret säger det när det ser ett NVIDIA-kort som kör på DirectML. Men NVIDIA får inte vara det enda alternativet. CPU är alltid sist, så en dator utan användbar GPU får en långsam skanning i stället för ingen, och den läggs till som reserv när en GPU-session skapas.

Adapterns namn läses från Windows display-adapter-klassnyckeln i registret (inte från ett leverantörsverktyg som `nvidia-smi`, som bara finns på vissa datorer), och Basic Render Driver hoppas över. Leverantörslåsta leverantörer namnger den matchande adaptern. DirectML visas på den första uppräknade adaptern, som är systemets standard. Namnet är bara för visning.

`ScanSettings.prefer_backend` (bara för skript) kan namnge en leverantör eller ett kort namn.

## Vad du kan förvänta dig på den här datorn {#what-to-expect-from-this-machine}

Fönstret mäter djupmodellens faktiska genomströmning på den här datorn vid start (6 bildrutor efter en uppvärmning) i stället för att slå upp GPU:n i en tabell. Termiskt läge, batteriprofiler i bärbara datorer och drivrutinsversioner rör den för mycket för det. Det anger hur en skanning kommer att bli innan något kan starta:

| Uppmätta vyer per sekund | Nivå | Rubrik | Råd |
|---|---|---|---|
| 25 eller fler | realtid | Live-skanning i full detalj. | Gå i normal takt; overlayn hinner med. |
| 12 till 25 | hanterbar | Live-skanning, med färre behållna vyer än i full hastighet. | Gå långsamt och sväng mjukt. Snabba svängar lämnar luckor. Draft behåller färre vyer, vilket hjälper djupmodellen att hinna med. |
| 2 till 12 | långsam | Spela in först, rekonstruera sedan. | Spela in en video av gången och rekonstruera från filen efteråt. Resultatet är identiskt; bara återkopplingen är inte live. |
| under 2 | opraktisk | Den här datorn är för långsam för att skanna användbart. | En kortare rutt, eller en mindre modell. **Start är inaktiverad.** |

På CPU lägger noten till att installation av `onnxruntime-directml` brukar åtgärda det på Windows. Ingenting ändrar själv captureupplösningen. Det skulle inte hjälpa, eftersom djupmodellen körs i sin fasta indatastorlek oavsett vad den får. Det som håller uppe en långsammare dator är att behålla färre vyer, vilket Draft gör.

### Uppmätt av utvecklaren {#measured-by-the-developer}

Samma ONNX-fil, samma utdata, RTX 5080:

| Backend | Djupgenomströmning |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Ett testklipp genom den levererade ONNX-vägen:

| Förinställning | Vyer behållna | Djupgenomströmning |
|---|---|---|
| Draft | ungefär 1 av 7 | ungefär 50 /s |
| Balanced | ungefär 1 av 4 | ungefär 50 /s |
| Detailed | ungefär 1 av 2 | ungefär 40 /s |

Djupet är gott om tid snabbare än fångsten, så live-skanning är inte bundet av djupet. Appens miljö är ungefär 349 MiB utan PyTorch, mot ungefär 3,5 GB för torch med CUDA.

Den offline-`reconstruct`-vägen är annorlunda: minuter per 16-bildrutors fönster på en stationär GPU.

## Minne {#memory}

- Bildrutor sparas inte efter fusion, utom **160** för att färglägga nätet.
- En skanning stoppar vid **3000** behållna vyer som standard ("Views kept"), som ett skydd.
- Fångstkön håller 4 bildrutor; telemetriposbufferten 30 sekunder.
- Båda voxelrutnäten är glesa, och nätet extraheras block för block. Minnet följer alltså vad som skannats, inte den omslutande lådan.

## Plattform {#platform}

Skannern och Assetto Corsa-inspelarna är bara Windows i praktiken: live-fångst använder Windows Graphics Capture, genvägarna och det klicktransparenta overlayt använder Win32-API:et, och Kunos-sidorna är Windows-delat minne. Videofiler kan skannas och UDP-inspelarna körs på andra plattformar, men det har inte kontrollerats.
