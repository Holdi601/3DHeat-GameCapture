---
title: "Kjøretid, avhengigheter og ytelse"
nav_order: 8
lang: "no"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Kjøretid, avhengigheter og ytelse {#runtime-dependencies-and-performance}

Kode: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dobbeltklikk på den. Den gjør bare to ting selv:

1. **Finner Python** (`python`, deretter `py`). Finnes ingen, spør den
   `Install it now with winget [Y,N]?`; på J kjører den
   `winget install -e --id Python.Python.3.12`, og ber deretter deg lukke vinduet og kjøre
   `scan.bat` igjen, slik at Windows plukker opp den nye PATH-en. På N installeres ingenting.
2. **Lager et privat miljø**, `.venv` ved siden av `scan.bat`, hvis det ikke finnes, og oppgraderer
   pip-en - så ingenting installeres i systempython.

Deretter kjører den `.venv\Scripts\python.exe -m heat3d_capture.ui`. Alt annet - å finne ut hva som mangler,
si hva det er til for, spørre - skjer i Python, som en dialog.

## Forhåndssjekk ved første kjøring {#first-run-preflight}

Før vinduet importerer noe tungt, sjekkes hvert krav (med `importlib.util.find_spec`, så en halvt fjernet pakke
regnes som manglende). Reglene:

- **Alt sjekkes først.** Hele listen samles før noe sies, så det å fikse én pakke aldri fører rett til neste feil.
- **Spør, anta aldri.** Dialogen lister hver manglende pakke, hva den er til for, og den samlede nedlastingen, og gjør ingenting
  uten **Download and install**. Avbryt avslutter: "Nothing was installed and nothing was changed."
- **Stillhet er ikke samtykke.** Uten Qt faller sjekken tilbake til konsollen og spør `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`,
  `ja` betyr ja); uten terminal å svare i (slutt på inndata), installeres ingenting.
- **Inn i verktøyets eget miljø.** Installasjonen er `<kjørende python> -m pip install ...` som en underprosess - med `scan.bat`, den
  private `.venv`. Hvis den feiler, viser dialogen siste linje i pips utdata og kommandoen å prøve for hånd.

| Pakke | Importert som | Vist som hva den er til for | Ca. nedlasting |
|---|---|---|---|
| numpy | `numpy` | regnearbeidet alt annet er bygget på | 20 MB |
| opencv-python | `cv2` | lese videofiler og kamerabilder | 40 MB |
| onnxruntime-directml på Windows, onnxruntime ellers | `onnxruntime` | kjøre dybdemodellen på grafikkortet | 120 MB |
| PySide6-Essentials | `PySide6` | vinduet og kontrollene | 90 MB |
| scipy | `scipy` | glatte den rekonstruerte flaten | 45 MB |
| scikit-image | `skimage` | gjøre målinger om til en 3D-flate | 30 MB |
| windows-capture | `windows_capture` | å fange et spillvindu live (valgfri: uten den fungerer videofiler likevel) | 5 MB |

Konvertering av dybdemodellen trenger tre til, spurt om separat og bare når du trykker "Set up
the depth model": `torch` (ca. 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Skanneren
importerer dem aldri selv.

Den offline `reconstruct`-kommandoen har en egen sjekk, kjørt etter at den har skrevet ut lisenslinjen
og bare i terminalen: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, og `vggt` fra Metas GitHub-depot (installert med `--no-deps`,
fordi metadataene låser numpy under 2). Den samme listen står i `requirements-offline.txt`; se
[Offline rekonstruksjon](reconstruction-offline.md#requirements).

Pakken for ONNX Runtime som tilbys er den `requirements.txt` velger for plattformen:
`onnxruntime-directml` på Windows, `onnxruntime` ellers. Hvis `onnxruntime` allerede kan importeres
(for eksempel `onnxruntime-gpu`), installeres ingenting: sjekken er på modulnavn.

## Installere for hånd {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` låser: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(bare Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` på Windows og `onnxruntime>=1.19` ellers.

`requirements-offline.txt` legger til det bare `reconstruct` trenger: `transformers`, `einops`,
`safetensors`, `huggingface_hub` og `Pillow`, med installasjonslinjen for `vggt` (`--no-deps`) og
VGGT-lisensmerknaden i toppen. PyTorch står heller ikke der, av grunnen under.

**PyTorch er bevisst utelatt.** Det riktige hjulet avhenger av GPU-en og CUDA-versjonen, og å låse
én ville installert en CPU-bygg på maskinene som trenger GPU-bygget mest. Vil du ha den (modellkonvertering,
den offline `reconstruct`-banen), installer den **før** `requirements.txt`: torch-hjulene kan havne på numpy 1.x,
som scipy da nekter å kjøre mot, og feilen viser seg som `module numpy has no attribute long` inne i scipy, langt
fra årsaken.

`onnxruntime-directml` og `onnxruntime-gpu` er i konflikt: installer bare én av dem.

Verifisert av utvikleren: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, på en NVIDIA
RTX 5080, og det samme miljøet uten NVIDIA-spesifikk pakke.

## Inferensbackender {#inference-backends}

ONNX Runtime når GPU-er via utførelsesleverandører, og hvilke som finnes avhenger av hvordan onnxruntime
ble installert, ikke av maskinvaren. Så tilgjengelighet oppdages, best først:

| Rang | Leverandør | Vist som | Maskinvare |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | enhver Direct3D 12-GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | alt |

**DirectML er standardinstallasjonen** fordi den når AMD- og Intel-GPU-er i tillegg til NVIDIA. NVIDIA er raskere
med sine egne leverandører - å installere `onnxruntime-gpu` legger til CUDA, og vinduet sier det når det ser et NVIDIA-kort
som kjører på DirectML - men NVIDIA har ikke lov til å være det eneste valget. CPU er alltid sist, så en maskin uten brukbar
GPU får en treg skanning i stedet for ingen, og den legges til som reserve når en GPU-sesjon opprettes.

Adapterens navn leses fra Windows' skjermadapterklasse i registeret (ikke fra et leverandørverktøy som `nvidia-smi`, som bare
finnes på noen maskiner), og hopper over Basic Render Driver. Leverandørlåste leverandører peker ut den tilsvarende adapteren;
DirectML vises på den første oppregnede adapteren, som er systemstandarden. Navnet er bare for visning.

`ScanSettings.prefer_backend` (bare skript) kan nevne en leverandør eller et kortnavn.

## Hva du kan forvente på denne maskinen {#what-to-expect-from-this-machine}

Vinduet måler dybdemodellens faktiske gjennomstrømning på denne maskinen ved oppstart (6 bilder etter en oppvarming) i stedet for å slå opp
GPU-en i en tabell - termisk tilstand, bærbare strømprofiler og driverversjoner flytter den for mye - og sier hva en skanning blir
før noe kan starte:

| Målte bilder per sekund | Nivå | Overskrift | Råd |
|---|---|---|---|
| 25 eller mer | sanntid | Live skanning i full detalj. | Gå i normalt tempo; overlegget henger med. |
| 12 til 25 | brukbar | Live skanning, med færre bilder beholdt enn ved full fart. | Gå sakte og sving forsiktig - raske svinger gir hull. Utkast beholder færre bilder, noe som hjelper dybdemodellen å henge med. |
| 2 til 12 | treg | Ta opp først, rekonstruer etterpå. | Ta opp en video av turen og rekonstruer fra filen etterpå. Resultatet er identisk; bare tilbakemeldingen er ikke live. |
| under 2 | upraktisk | Denne maskinen er for treg til å skanne nyttig. | En kortere rute, eller en mindre modell. **Start er deaktivert.** |

På CPU legger notatet til at å installere `onnxruntime-directml` vanligvis fikser det på Windows. Ingenting endrer
opptaksoppløsningen av seg selv: det ville ikke hjulpet, fordi dybdemodellen kjører på sin faste inndatastørrelse uansett
hva den får; det som holder en tregere maskin oppe er å beholde færre bilder, som Utkast gjør.

### Målt av utvikleren {#measured-by-the-developer}

Samme ONNX-fil, samme utdata, RTX 5080:

| Backend | Dybdegjennomstrømning |
|---|---|
| DirectML | 54 bps |
| CPU | 3,5 bps |

Et testklipp gjennom den leverte ONNX-banen:

| Forhåndsinnstilling | Bilder beholdt | Dybdegjennomstrømning |
|---|---|---|
| Utkast | omtrent 1 av 7 | omtrent 50 /s |
| Balansert | omtrent 1 av 4 | omtrent 50 /s |
| Detaljert | omtrent 1 av 2 | omtrent 40 /s |

Dybde er komfortabelt raskere enn opptak, så live skanning er ikke begrenset av dybde. Appens miljø er omtrent 349 MiB uten
PyTorch, mot rundt 3,5 GB for torch med CUDA.

Den offline `reconstruct`-banen er annerledes: minutter per 16-bilders vindu på en stasjonær GPU.

## Minne {#memory}

- Bilder beholdes ikke etter sammensmelting, bortsett fra **160** for å farge nettet.
- En skanning stopper ved **3000** beholdte visninger som standard ("Views kept"), som en vakt.
- Den live opptakskøen holder 4 bilder; telemetriposisjonsbufferen 30 sekunder.
- Begge voxelrutenettene er glisne, og nettet trekkes ut blokk for blokk, så minnet følger det som ble skannet,
  ikke avgrensningsboksen.

## Plattform {#platform}

Skanneren og Assetto Corsa-opptakerne er i praksis bare for Windows: live opptak bruker Windows Graphics Capture,
hurtigtastene og det klikk-gjennomsiktige overlegget bruker Win32-API-et, og Kunos-sidene er delt minne i Windows. Videofiler
kan skannes, og UDP-opptakerne kjører andre steder, men det er ikke kontrollert.
