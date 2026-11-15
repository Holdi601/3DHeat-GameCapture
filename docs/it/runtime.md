---
title: Runtime e dipendenze
nav_order: 8
lang: "it"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, dipendenze e prestazioni {#runtime-dependencies-and-performance}

Codice: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Fai doppio clic. Fa solo due cose:

1. **Trova Python** (`python`, poi `py`). Se non c'è, chiede
   `Install it now with winget [Y,N]?`; con Y esegue
   `winget install -e --id Python.Python.3.12`, poi ti chiede di chiudere la finestra e
   rieseguire `scan.bat` così Windows aggiorna il PATH. Con N non viene installato nulla.
2. **Crea un ambiente privato**, `.venv` accanto a `scan.bat`, se non esiste, e aggiorna il suo
   pip - così nulla viene installato nel Python di sistema.

Poi esegue `.venv\Scripts\python.exe -m heat3d_capture.ui`. Tutto il resto - capire cosa manca,
spiegare a cosa serve, chiedere - avviene in Python, in una finestra di dialogo.

## Controllo preliminare al primo avvio {#first-run-preflight}

Prima che la finestra importi qualsiasi cosa di pesante, ogni requisito viene controllato (con
`importlib.util.find_spec`, così un pacchetto rimosso a metà conta come mancante). Le regole:

- **Si controlla tutto per primo.** L'elenco completo viene raccolto prima di dire qualcosa, così
  sistemare un pacchetto non porta subito all'errore successivo.
- **Chiedi, mai presumere.** La finestra elenca ogni pacchetto mancante, a cosa serve e il download
  totale, e non fa nulla senza **Download and install**. Annulla esce: "Nothing was installed and
  nothing was changed."
- **Il silenzio non è consenso.** Senza Qt il controllo ricade sulla console e chiede
  `Install them now? [Y/n]` (Invio, `y`, `yes`, `j`, `ja` significano sì); senza un terminale a cui
  rispondere (fine dell'input), non installa nulla.
- **Nell'ambiente di questo strumento.** L'installazione è `<python in esecuzione> -m pip install ...`
  come sottoprocesso - con `scan.bat`, il `.venv` privato. Se fallisce, la finestra mostra l'ultima
  riga dell'output di pip e il comando da provare a mano.

| Pacchetto | Importato come | Mostrato come a cosa serve | Download approssimativo |
|---|---|---|---|
| numpy | `numpy` | l'aritmetica su cui si basa tutto il resto | 20 MB |
| opencv-python | `cv2` | lettura di file video e fotogrammi della camera | 40 MB |
| onnxruntime-directml su Windows, onnxruntime altrove | `onnxruntime` | esecuzione del modello di profondità sulla scheda grafica | 120 MB |
| PySide6-Essentials | `PySide6` | la finestra e i suoi controlli | 90 MB |
| scipy | `scipy` | levigatura della superficie ricostruita | 45 MB |
| scikit-image | `skimage` | trasformazione delle misure in una superficie 3D | 30 MB |
| windows-capture | `windows_capture` | cattura di una finestra di gioco in diretta (facoltativo: senza di esso, i file video funzionano comunque) | 5 MB |

La conversione del modello di profondità ne richiede altri tre, chiesti a parte e solo quando premi
"Set up the depth model": `torch` (circa 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Lo
scanner stesso non li importa mai.

Il comando offline `reconstruct` ha un controllo proprio, eseguito dopo che ha stampato la riga della
licenza e solo nel terminale: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, e `vggt` dal repository GitHub di Meta (installato con `--no-deps`, perché
i suoi metadati fissano numpy sotto la 2). La stessa lista è in `requirements-offline.txt`; vedi
[Ricostruzione offline](reconstruction-offline.md#requirements).

Il pacchetto ONNX Runtime offerto è quello che `requirements.txt` sceglie per la piattaforma:
`onnxruntime-directml` su Windows, `onnxruntime` altrove. Se `onnxruntime` è già importabile (per
esempio `onnxruntime-gpu`), non viene installato nulla: il controllo è per nome del modulo.

## Installazione a mano {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fissa: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(solo Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` su Windows e `onnxruntime>=1.19` altrove.

`requirements-offline.txt` aggiunge ciò che serve solo a `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` e `Pillow`, con la riga di installazione di `vggt` (`--no-deps`) e la
nota sulla licenza di VGGT nella sua intestazione. Anche PyTorch non è incluso, per la ragione qui sotto.

**PyTorch è deliberatamente assente.** La ruota giusta dipende dalla GPU e dalla versione di CUDA, e
fissarne una installerebbe una build per CPU sulle macchine che più hanno bisogno di quella per GPU. Se
lo vuoi (conversione del modello, il percorso offline `reconstruct`), installalo **prima** di
`requirements.txt`: le ruote di torch possono stabilizzarsi su numpy 1.x, che scipy poi rifiuta di
eseguire, e il guasto si manifesta come `module numpy has no attribute long` dall'interno di scipy,
lontano dalla sua causa.

`onnxruntime-directml` e `onnxruntime-gpu` sono in conflitto: installane uno solo.

Verificato dallo sviluppatore: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, su una NVIDIA
RTX 5080, e lo stesso ambiente senza alcun pacchetto specifico NVIDIA.

## Backend di inferenza {#inference-backends}

ONNX Runtime raggiunge le GPU tramite i provider di esecuzione, e quali esistono dipende da come è
stato installato onnxruntime, non dall'hardware. Quindi la disponibilità viene scoperta, dal migliore:

| Rango | Provider | Mostrato come | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | qualunque GPU Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | qualunque cosa |

**DirectML è l'installazione predefinita** perché raggiunge le GPU AMD e Intel oltre a quelle NVIDIA.
NVIDIA è più veloce con i suoi provider - installando `onnxruntime-gpu` si aggiunge CUDA, e la finestra
lo dichiara quando vede una scheda NVIDIA che gira su DirectML - ma NVIDIA non può essere l'unica opzione.
La CPU è sempre l'ultima, quindi una macchina senza una GPU utilizzabile ottiene una scansione lenta invece
di nessuna, ed è aggiunta come ripiego quando viene creata una sessione su GPU.

Il nome della scheda viene letto dalla chiave di classe del registro di Windows per gli adattatori di
visualizzazione (non da uno strumento del produttore come `nvidia-smi`, che esiste solo su alcune macchine),
saltando il Basic Render Driver. I provider legati a un solo produttore indicano l'adattatore corrispondente;
DirectML viene mostrato sul primo adattatore enumerato, che è quello di sistema predefinito. Il nome serve
solo alla visualizzazione.

`ScanSettings.prefer_backend` (solo per gli script) può indicare un provider o un nome breve.

## Cosa aspettarsi da questa macchina {#what-to-expect-from-this-machine}

La finestra misura al volo la velocità effettiva del modello di profondità su questa macchina all'avvio (6
fotogrammi dopo un riscaldamento) invece di cercare la GPU in una tabella - lo stato termico, i profili di
alimentazione dei portatili e le versioni dei driver spostano troppo il risultato - e dichiara com'è una
scansione prima che possa partire:

| Viste al secondo misurate | Fascia | Titolo | Consiglio |
|---|---|---|---|
| 25 o più | tempo reale | Scansione in diretta a piena qualità. | Cammina a un passo normale; la sovrapposizione terrà il passo. |
| da 12 a 25 | utilizzabile | Scansione in diretta, con meno viste tenute che alla piena velocità. | Cammina piano e gira dolcemente - le svolte rapide lasceranno buchi. Draft tiene meno viste, il che aiuta il modello di profondità a tenere il passo. |
| da 2 a 12 | lenta | Registra prima, ricostruisci dopo. | Registra un video della passeggiata e ricostruisci dal file dopo. Il risultato è identico; solo il riscontro non è in diretta. |
| sotto 2 | impraticabile | Questa macchina è troppo lenta per una scansione utile. | Un percorso più corto, o un modello più piccolo. **L'avvio è disabilitato.** |

Su CPU la nota aggiunge che installare `onnxruntime-directml` di solito risolve su Windows. Abbassare solo la risoluzione di cattura non servirebbe, perché il modello di profondità gira alla sua dimensione
d'ingresso fissa qualunque cosa riceva; ciò che tiene in piedi una macchina più lenta è tenere meno viste,
che è ciò che fa Draft.

### Misurato dallo sviluppatore {#measured-by-the-developer}

Stesso file ONNX, stesso output, RTX 5080:

| Backend | Velocità della profondità |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Un clip di prova attraverso il percorso ONNX fornito:

| Preset | Viste tenute | Velocità della profondità |
|---|---|---|
| Draft | circa 1 su 7 | circa 50 /s |
| Balanced | circa 1 su 4 | circa 50 /s |
| Detailed | circa 1 su 2 | circa 40 /s |

La profondità è comodamente più veloce della cattura, quindi la scansione in diretta non è limitata dalla
profondità. L'ambiente dell'app pesa circa 349 MiB senza PyTorch, contro circa 3,5 GB per torch con CUDA.

Il percorso offline `reconstruct` è diverso: minuti per finestra di 16 fotogrammi su una GPU da desktop.

## Memoria {#memory}

- I fotogrammi non vengono conservati dopo la fusione, tranne **160** per colorare la mesh.
- Una scansione si ferma a **3000** viste tenute per impostazione predefinita ("Views kept"), come
  protezione.
- La coda di cattura in diretta contiene 4 fotogrammi; il buffer delle pose della telemetria 30 secondi.
- Entrambe le griglie di voxel sono sparse, e la mesh viene estratta blocco per blocco, quindi la memoria
  segue ciò che è stato scansionato, non il bounding box.

## Piattaforma {#platform}

Lo scanner e i registratori per Assetto Corsa sono di fatto solo per Windows: la cattura in diretta usa
Windows Graphics Capture, le scorciatoie e la sovrapposizione trasparente ai clic usano l'API Win32, e le
pagine Kunos sono memoria condivisa di Windows. I file video possono essere scansionati e i registratori UDP
girano altrove, ma non è stato verificato.
