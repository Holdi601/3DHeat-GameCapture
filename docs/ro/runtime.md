---
title: "Rulare și dependențe"
nav_order: 8
lang: "ro"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Rulare, dependențe și performanță {#runtime-dependencies-and-performance}

Cod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Faceți dublu clic pe el. Face doar două lucruri singur:

1. **Găsește Python** (`python`, apoi `py`). Dacă nu există, întreabă `Install it now with winget [Y,N]?`; la Y rulează `winget install -e --id Python.Python.3.12`, apoi vă cere să închideți fereastra și să rulați din nou `scan.bat`, ca Windows să preia noul PATH. La N nu se instalează nimic.
2. **Creează un mediu privat**, `.venv` lângă `scan.bat`, dacă nu există, și își actualizează pip-ul - deci nimic nu se instalează în Python-ul de sistem.

Apoi rulează `.venv\Scripts\python.exe -m heat3d_capture.ui`. Tot restul - aflarea a ce lipsește, spunerea la ce servește, întrebarea - se întâmplă în Python, ca o fereastră de dialog.

## Verificarea de pornire {#first-run-preflight}

Înainte ca fereastra să importe ceva greu, fiecare cerință este verificată (cu `importlib.util.find_spec`, deci un pachet pe jumătate șters contează ca lipsă). Regulile:

- **Totul este verificat întâi.** Lista completă este strânsă înainte de a se spune ceva, astfel încât repararea unui pachet să nu ducă direct la următoarea eroare.
- **Se întreabă, nu se presupune.** Dialogul listează fiecare pachet lipsă, la ce servește și descărcarea totală, și nu face nimic fără **Download and install**. Cancel iese: „Nothing was installed and nothing was changed."
- **Tăcerea nu este consimțământ.** Fără Qt, verificarea trece în consolă și întreabă `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` înseamnă da); fără un terminal la care să răspundă (sfârșitul intrării), nu instalează nimic.
- **În mediul propriu al acestui instrument.** Instalarea este `<python care rulează> -m pip install ...` ca subproces - cu `scan.bat`, `.venv`-ul privat. Dacă eșuează, dialogul arată ultima linie a ieșirii pip și comanda de încercat manual.

| Pachet | Importat ca | Afișat ca ce servește | Descărcare aproximativă |
|---|---|---|---|
| numpy | `numpy` | aritmetica pe care este construit tot restul | 20 MB |
| opencv-python | `cv2` | citirea fișierelor video și a cadrelor de cameră | 40 MB |
| onnxruntime-directml pe Windows, onnxruntime în rest | `onnxruntime` | rularea modelului de adâncime pe placa grafică | 120 MB |
| PySide6-Essentials | `PySide6` | fereastra și comenzile ei | 90 MB |
| scipy | `scipy` | netezirea suprafeței reconstruite | 45 MB |
| scikit-image | `skimage` | transformarea măsurătorilor într-o suprafață 3D | 30 MB |
| windows-capture | `windows_capture` | capturarea în direct a unei ferestre de joc (opțional: fără el, fișierele video funcționează tot) | 5 MB |

Conversia modelului de adâncime are nevoie de trei altele, cerute separat și doar când apăsați „Set up the depth model": `torch` (aproximativ 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Scanerul în sine nu le importă niciodată.

Comanda offline `reconstruct` are o verificare proprie, rulată după ce afișează linia de licență și doar în terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, și `vggt` din depozitul GitHub al Meta (instalat cu `--no-deps`, pentru că metadatele sale fixează numpy sub 2). Aceeași listă este în `requirements-offline.txt`; vezi [Reconstrucție offline](reconstruction-offline.md#requirements).

Pachetul ONNX Runtime oferit este cel ales de `requirements.txt` pentru platformă: `onnxruntime-directml` pe Windows, `onnxruntime` în rest. Dacă `onnxruntime` poate fi deja importat (de exemplu `onnxruntime-gpu`), nu se instalează nimic: verificarea se face după numele modulului.

## Instalare manuală {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fixează: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (doar Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` pe Windows și `onnxruntime>=1.19` în rest.

`requirements-offline.txt` adaugă ce are nevoie doar `reconstruct`: `transformers`, `einops`, `safetensors`, `huggingface_hub` și `Pillow`, cu linia de instalare `vggt` (`--no-deps`) și nota de licență VGGT în antet. Nici PyTorch nu este în el, din motivul de mai jos.

**PyTorch este intenționat absent.** Roata potrivită depinde de GPU și de versiunea CUDA, iar fixarea uneia ar instala o versiune doar pentru CPU pe mașinile care au cel mai mult nevoie de cea pentru GPU. Dacă îl doriți (conversia modelului, calea offline `reconstruct`), instalați-l **înainte** de `requirements.txt`: roțile torch pot alege numpy 1.x, pe care scipy îl refuză, iar eșecul apare ca `module numpy has no attribute long` din interiorul scipy, departe de cauza sa.

`onnxruntime-directml` și `onnxruntime-gpu` sunt în conflict: instalați doar unul.

Verificat de dezvoltator: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, pe un NVIDIA RTX 5080, și același mediu fără niciun pachet specific NVIDIA.

## Backend-uri de inferență {#inference-backends}

ONNX Runtime ajunge la GPU-uri prin furnizori de execuție, iar cei care există depind de cum a fost instalat onnxruntime, nu de hardware. Deci disponibilitatea se descoperă, cel mai bun primul:

| Rang | Furnizor | Afișat ca | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | orice GPU Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | orice |

**DirectML este instalarea implicită** pentru că ajunge și la GPU-urile AMD și Intel, nu doar la NVIDIA. NVIDIA merge mai repede cu furnizorii săi - instalarea `onnxruntime-gpu` adaugă CUDA, iar fereastra spune asta când vede o placă NVIDIA rulând pe DirectML - dar NVIDIA nu are voie să fie singura opțiune. CPU este mereu ultimul, deci o mașină fără GPU utilizabil primește o scanare lentă, nu niciuna, iar este adăugat ca rezervă când se creează o sesiune GPU.

Numele adaptorului este citit din cheia de registru a clasei de adaptoare de afișare Windows (nu dintr-un instrument al furnizorului, precum `nvidia-smi`, care există doar pe unele mașini), sărind peste Basic Render Driver. Furnizorii legați de un anumit producător numesc adaptorul corespunzător; DirectML este afișat pe primul adaptor enumerat, care este cel implicit al sistemului. Numele este doar pentru afișare.

`ScanSettings.prefer_backend` (doar pentru scripturi) poate numi un furnizor sau un nume scurt.

## Ce să așteptați de la această mașină {#what-to-expect-from-this-machine}

Fereastra măsoară debitul real al modelului de adâncime pe această mașină la pornire (6 cadre după o încălzire), în loc să caute GPU-ul într-un tabel - starea termică, profilurile de energie ale laptopurilor și versiunile driverelor îl mișcă prea mult - și spune cum va fi o scanare înainte ca ceva să poată porni:

| Vederi măsurate pe secundă | Nivel | Titlu | Sfat |
|---|---|---|---|
| 25 sau mai mult | în timp real | Scanare în direct la detaliu complet. | Mergeți într-un ritm normal; overlay-ul va ține pasul. |
| 12 până la 25 | utilizabil | Scanare în direct, cu mai puține vederi păstrate decât la viteză maximă. | Mergeți încet și întoarceți-vă blând - virajele rapide lasă goluri. Draft păstrează mai puține vederi, ceea ce ajută modelul de adâncime să țină pasul. |
| 2 până la 12 | lent | Înregistrați întâi, reconstruiți după. | Înregistrați un video al plimbării și reconstruiți din fișier după aceea. Rezultatul este identic; doar feedback-ul nu este în direct. |
| sub 2 | impractic | Această mașină este prea lentă pentru o scanare utilă. | Un traseu mai scurt, sau un model mai mic. **Pornirea este dezactivată.** |

Pe CPU, nota adaugă că instalarea `onnxruntime-directml` de obicei rezolvă asta pe Windows. Nimic nu schimbă de la sine rezoluția capturii: nu ar ajuta, pentru că modelul de adâncime rulează la dimensiunea sa fixă de intrare, orice i s-ar da; ce ține o mașină mai lentă în frunte este păstrarea mai puținelor vederi, adică ce face Draft.

### Măsurat de dezvoltator {#measured-by-the-developer}

Același fișier ONNX, aceeași ieșire, RTX 5080:

| Backend | Debitul adâncimii |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Un clip de test prin calea ONNX livrată:

| Presetare | Vederi păstrate | Debitul adâncimii |
|---|---|---|
| Draft | aproximativ 1 din 7 | aproximativ 50 /s |
| Balanced | aproximativ 1 din 4 | aproximativ 50 /s |
| Detailed | aproximativ 1 din 2 | aproximativ 40 /s |

Adâncimea este suficient de rapidă față de captură, deci scanarea în direct nu este legată de adâncime. Mediul aplicației are aproximativ 349 MiB fără PyTorch, față de aproximativ 3,5 GB pentru torch cu CUDA.

Calea offline `reconstruct` este diferită: minute per fereastră de 16 cadre pe un GPU de desktop.

## Memorie {#memory}

- Cadrele nu sunt păstrate după fuziune, cu excepția a **160** pentru colorarea mesh-ului.
- O scanare se oprește la **3000** de vederi păstrate implicit („Views kept"), ca o protecție.
- Coada de captură în direct ține 4 cadre; bufferul de poziții din telemetrie 30 de secunde.
- Ambele grile de voxeli sunt rare, iar mesh-ul este extras bloc cu bloc, deci memoria urmărește ce s-a scanat, nu caseta de încadrare.

## Platforma {#platform}

Scanerul și înregistratoarele Assetto Corsa sunt, în practică, doar pentru Windows: captura în direct folosește Windows Graphics Capture, tastele rapide și overlay-ul transparent la clic folosesc API-ul Win32, iar paginile Kunos sunt memorie partajată Windows. Fișierele video pot fi scanate, iar înregistratoarele UDP rulează și în alte părți, dar asta nu a fost verificat.
