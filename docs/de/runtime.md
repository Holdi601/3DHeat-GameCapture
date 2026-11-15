---
title: Laufzeit und Abhängigkeiten
nav_order: 8
lang: de
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Laufzeit, Abhängigkeiten und Leistung {#runtime-dependencies-and-performance}

Code: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Doppelklick darauf. Es tut selbst nur zwei Dinge:

1. **Findet Python** (zuerst `python`, dann `py`). Gibt es keins, fragt es
   `Install it now with winget [Y,N]?`. Bei Y führt es
   `winget install -e --id Python.Python.3.12` aus und bittet, das Fenster zu schließen und
   `scan.bat` erneut zu starten, damit Windows den neuen PATH übernimmt. Bei N wird nichts installiert.
2. **Legt eine private Umgebung an**, `.venv` neben `scan.bat`, falls keine existiert, und aktualisiert
   ihr pip. So wird nichts in das System-Python installiert.

Dann startet es `.venv\Scripts\python.exe -m heat3d_capture.ui`. Alles Übrige (herausfinden, was fehlt,
erklären, wofür es ist, fragen) geschieht in Python, als Dialog.

## Vorab-Prüfung beim ersten Start {#first-run-preflight}

Bevor das Fenster etwas Schweres importiert, wird jede Anforderung geprüft (mit
`importlib.util.find_spec`, damit ein halb entferntes Paket als fehlend zählt). Die Regeln:

- **Zuerst wird alles geprüft.** Die volle Liste wird gesammelt, bevor etwas gesagt wird, damit das
  Beheben eines Pakets nicht direkt zum nächsten Fehler führt.
- **Fragen, nie annehmen.** Der Dialog nennt jedes fehlende Paket, wofür es ist, und den Gesamtdownload,
  und tut nichts ohne **Download and install**. Abbrechen beendet: „Nothing was installed and nothing was changed.“
- **Schweigen ist keine Zustimmung.** Ohne Qt greift die Prüfung auf die Konsole zurück und fragt
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` heißen ja). Ohne Terminal, das antworten kann
  (Ende der Eingabe), installiert sie nichts.
- **In die eigene Umgebung dieses Werkzeugs.** Die Installation ist `<laufendes python> -m pip install ...`
  als Unterprozess, bei `scan.bat` die private `.venv`. Schlägt sie fehl, zeigt der Dialog die letzte Zeile
  der pip-Ausgabe und den Befehl, den man von Hand versuchen kann.

| Paket | Importiert als | Angezeigt als, wofür es ist | Ungefährer Download |
|---|---|---|---|
| numpy | `numpy` | die Arithmetik, auf der alles andere aufbaut | 20 MB |
| opencv-python | `cv2` | Lesen von Videodateien und Kamerabildern | 40 MB |
| onnxruntime-directml unter Windows, sonst onnxruntime | `onnxruntime` | Ausführen des Tiefenmodells auf deiner Grafikkarte | 120 MB |
| PySide6-Essentials | `PySide6` | das Fenster und seine Bedienelemente | 90 MB |
| scipy | `scipy` | Glätten der rekonstruierten Oberfläche | 45 MB |
| scikit-image | `skimage` | Umwandeln von Messungen in eine 3D-Oberfläche | 30 MB |
| windows-capture | `windows_capture` | Live-Aufnahme eines Spielfensters (optional: ohne es funktionieren Videodateien trotzdem) | 5 MB |

Das Konvertieren des Tiefenmodells braucht drei weitere Pakete, die getrennt und nur auf „Set up the depth model“ hin
erfragt werden: `torch` (etwa 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Der Scanner selbst importiert sie nie.

Der Offline-Befehl `reconstruct` hat eine eigene Prüfung. Sie läuft, nachdem er die Lizenzzeile ausgegeben hat, und nur im Terminal:
`torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, und `vggt` aus Metas GitHub-Repository
(mit `--no-deps` installiert, weil seine Metadaten numpy unter 2 festlegen). Dieselbe Liste steht in `requirements-offline.txt`; siehe
[Offline-Rekonstruktion](reconstruction-offline.md#requirements).

Das angebotene ONNX-Runtime-Paket ist das, das `requirements.txt` für die Plattform wählt:
`onnxruntime-directml` unter Windows, `onnxruntime` sonst. Ist `onnxruntime` bereits importierbar (etwa `onnxruntime-gpu`), wird nichts
installiert: Die Prüfung erfolgt über den Modulnamen.

## Von Hand installieren {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` legt fest: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (nur Windows), `scipy>=1.11`,
`scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` unter Windows und `onnxruntime>=1.19`
sonst.

`requirements-offline.txt` ergänzt, was nur `reconstruct` braucht: `transformers`, `einops`, `safetensors`, `huggingface_hub` und `Pillow`,
mit der Installationszeile für `vggt` (`--no-deps`) und dem Hinweis zur VGGT-Lizenz in seinem Kopf. PyTorch steht darin auch nicht, aus dem Grund unten.

**PyTorch fehlt absichtlich.** Das passende Wheel hängt von der GPU und der CUDA-Version ab. Ein fester Eintrag würde auf den Rechnern, die
die GPU-Version am dringendsten brauchen, eine CPU-Version installieren. Wenn du es willst (Modellkonvertierung, der Offline-Befehl
`reconstruct`), installiere es **vor** `requirements.txt`. Die torch-Wheels können sich auf numpy 1.x festlegen, und scipy verweigert dann den
Lauf. Der Fehler zeigt sich als `module numpy has no attribute long` aus scipy heraus, weit weg von seiner Ursache.

`onnxruntime-directml` und `onnxruntime-gpu` kollidieren. Installiere nur eines davon.

Vom Entwickler geprüft: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, auf einer NVIDIA RTX 5080, und dieselbe Umgebung ohne
NVIDIA-spezifisches Paket.

## Inferenz-Backends {#inference-backends}

ONNX Runtime erreicht GPUs über Ausführungsanbieter. Welche es gibt, hängt davon ab, wie onnxruntime installiert wurde, nicht von der
Hardware. Deshalb wird die Verfügbarkeit ermittelt, die beste zuerst:

| Rang | Anbieter | Angezeigt als | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | jede GPU mit Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | alles |

**DirectML ist die Standardinstallation**, weil es AMD- und Intel-GPUs ebenso erreicht wie NVIDIA. NVIDIA ist mit eigenen Anbietern
schneller: Die Installation von `onnxruntime-gpu` fügt CUDA hinzu, und das Fenster sagt es, wenn es eine NVIDIA-Karte unter DirectML
sieht. Aber NVIDIA darf nicht die einzige Option sein. CPU kommt immer zuletzt. So bekommt ein Rechner ohne brauchbare GPU einen langsamen
Scan statt keinem, und sie wird als Ausweichlösung angehängt, wenn eine GPU-Sitzung angelegt wird.

Der Name des Adapters wird aus dem Registry-Schlüssel der Windows-Anzeigeadapter gelesen (nicht aus einem Hersteller-Werkzeug wie
`nvidia-smi`, das nur auf manchen Rechnern existiert). Herstellergebundene Anbieter benennen den passenden Adapter. DirectML wird auf dem
ersten aufgezählten Adapter angezeigt, das ist der Systemstandard. Der Name dient nur der Anzeige.

`ScanSettings.prefer_backend` (nur für Skripte) kann einen Anbieter oder einen Kurznamen nennen.

## Was du auf diesem Rechner erwarten kannst {#what-to-expect-from-this-machine}

Das Fenster misst den tatsächlichen Durchsatz des Tiefenmodells auf diesem Rechner beim Start (6 Bilder nach einem Aufwärmen), statt die
GPU in einer Tabelle nachzuschlagen. Thermik, Energieprofile von Laptops und Treiberversionen verändern das zu stark. Es sagt, wie ein Scan
sein wird, bevor etwas starten kann:

| Gemessene Ansichten pro Sekunde | Stufe | Überschrift | Hinweis |
|---|---|---|---|
| 25 oder mehr | Echtzeit | Live-Scan in voller Detailtiefe. | In normalem Tempo gehen; das Overlay bleibt mit. |
| 12 bis 25 | machbar | Live-Scan, mit weniger behaltenen Ansichten als bei voller Geschwindigkeit. | Langsam gehen und sanft drehen; schnelle Drehungen lassen Lücken. Entwurf behält weniger Ansichten, das hilft dem Tiefenmodell mitzuhalten. |
| 2 bis 12 | langsam | Erst aufnehmen, dann rekonstruieren. | Ein Video vom Weg aufnehmen und danach aus der Datei rekonstruieren. Das Ergebnis ist identisch; nur das Feedback ist nicht live. |
| unter 2 | unpraktisch | Dieser Rechner ist zu langsam für einen sinnvollen Scan. | Eine kürzere Strecke oder ein kleineres Modell. **Der Start ist deaktiviert.** |

Bei CPU ergänzt der Hinweis, dass die Installation von `onnxruntime-directml` unter Windows es meist behebt. Nichts ändert die
Aufnahmeauflösung von selbst. Das würde nicht helfen, denn das Tiefenmodell läuft in seiner festen Eingabegröße, egal was man ihm gibt.
Was einen langsameren Rechner oben hält, ist, weniger Ansichten zu behalten, und genau das tut Entwurf.

### Vom Entwickler gemessen {#measured-by-the-developer}

Dieselbe ONNX-Datei, dieselbe Ausgabe, RTX 5080:

| Backend | Tiefendurchsatz |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Ein Testclip durch den mitgelieferten ONNX-Weg:

| Voreinstellung | Behaltene Ansichten | Tiefendurchsatz |
|---|---|---|
| Entwurf | etwa 1 von 7 | etwa 50 /s |
| Ausgewogen | etwa 1 von 4 | etwa 50 /s |
| Detailliert | etwa 1 von 2 | etwa 40 /s |

Die Tiefe ist bequem schneller als die Aufnahme, also ist der Live-Scan nicht von der Tiefe begrenzt. Die Umgebung der App ist etwa 349 MiB
ohne PyTorch, gegenüber etwa 3,5 GB für torch mit CUDA.

Der Offline-Weg `reconstruct` ist anders: Minuten pro 16-Bild-Fenster auf einer Desktop-GPU.

## Speicher {#memory}

- Bilder werden nach der Fusion nicht behalten, außer **160** für die Einfärbung des Netzes.
- Ein Scan hält standardmäßig bei **3000** behaltenen Ansichten an („Views kept“), als Schutz.
- Die Live-Aufnahme-Warteschlange hält 4 Bilder, der Telemetrie-Posenpuffer 30 Sekunden.
- Beide Voxelgitter sind dünn besetzt, und das Netz wird blockweise extrahiert. Der Speicher folgt also dem, was gescannt wurde, nicht dem Begrenzungsquader.

## Plattform {#platform}

Der Scanner und die Assetto-Corsa-Recorder laufen in der Praxis nur unter Windows: Die Live-Aufnahme nutzt Windows Graphics Capture, die
Tastenkürzel und das klickdurchlässige Overlay nutzen die Win32-API, und die Kunos-Seiten sind gemeinsamer Speicher von Windows. Videodateien
lassen sich scannen, und die UDP-Recorder laufen anderswo, das ist aber nicht geprüft.
