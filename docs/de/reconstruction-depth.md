---
title: Tiefe
nav_order: 3
lang: de
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Tiefe {#depth}

Was die externe Aufnahme niemals liefern kann, ist Geometrie. Das Spiel kennt die Tiefe jedes Pixels, sie liegt
aber in einem Puffer, den dieses Projekt bewusst nicht anfasst. Deshalb wird die Tiefe **aus dem Bild erschlossen**.
Das ist die Genauigkeitsgrenze des gesamten Ansatzes.

Code: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(was der Scanner ausführt),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(der PyTorch-Weg und die Skalenanpassung),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Das Modell {#the-model}

**Depth Anything V2**, Variante relativ. Es sagt *relative inverse Tiefe* voraus, ein Feld, das einer Disparität
ähnelt und nur bis auf eine unbekannte affine Transformation stimmt,
`metrische Disparität = a * vorhergesagt + b`, und diese ist bei jedem Bild anders. Das Netz ist gut bei dem, was
aus einem einzelnen Bild schwer ist (relative Form, Kanten, feine Strukturen), und schweigt, wo es nichts
wissen kann: bei der Skala. Die Skala kommt von anderswo, siehe [Kamerapose und Skala](reconstruction-pose.md).

| Größe | Hugging-Face-Kennung | Lizenz |
|---|---|---|
| **Small** (Vorgabe) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0**, kommerzielle Nutzung erlaubt |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0, nur nicht kommerziell |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0, nur nicht kommerziell |

Eine Rekonstruktion erbt die Lizenz des Modells, das sie erzeugt hat. Small ist überall die Vorgabe, gerade damit
ein Scan keine Einschränkung trägt, solange niemand etwas anderes wählt. Die metrischen Varianten
(`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) sind im Code genannt, aber der Scanner nutzt
sie nicht. Siehe [Modelle und Lizenzen](models-and-licences.md).

## Das Modell bauen {#building-the-model}

Der Scanner führt eine ONNX-Datei aus und importiert PyTorch nie. Die Datei muss einmal erzeugt werden:

- **Aus dem Fenster**: „Set up the depth model“ (siehe [Das Scan-Fenster](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)).
  Das führt den Befehl unten mit `--size small` aus.
- **Von Hand**, in einer Umgebung mit PyTorch, `transformers` und `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Option | Vorgabe | Bedeutung |
|---|---|---|
| `--size` | `small` | `small`, `base` oder `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | Ausgabedatei |
| `--side` | `518` | quadratische Eingabegröße; muss ein Vielfaches von 14 sein (die Patch-Größe des ViT); 518 = 14 x 37 ist die Trainingsauflösung |
| `--opset` | `17` | ONNX-Opset; 17 wird von DirectML und CUDA breit unterstützt |

Was der Konverter tut:

- Lädt den Checkpoint von Hugging Face (`AutoModelForDepthEstimation`).
- Umhüllt ihn so, dass die ImageNet-Normierung **im Graphen** steckt: Das Modell nimmt RGB im Bereich 0-255 als
  Float (`pixels`, Form `Batch x 3 x Seite x Seite`) und gibt `inverse_depth` aus. Es gibt genau eine Kopie von
  Mittelwert und Standardabweichung, die also nicht vom Checkpoint abweichen können.
- **Feste räumliche Größe**, dynamischer Batch. DirectML und TensorRT kompilieren pro Form. Eine dynamische Höhe
  und Breite würde beim ersten Bild jeder neuen Auflösung neu kompilieren, ein sichtbares Stocken in einer
  Live-Aufnahme.
- Exportiert über den **TorchScript-Weg** (`dynamo=False`). Der Dynamo-Graph scheiterte auf DirectML an einem
  Reshape-Knoten, und er schreibt die Gewichte in eine eigene Datei `.onnx.data`. Der TorchScript-Weg erzeugt eine
  einzige, in sich geschlossene Datei.
- Gibt die Datei und ihre Größe aus. Die Warnungen des Tracers über eingebackene Formen sind erwartet.

Der Scanner sucht nach `models/depth-*.onnx` und wählt nach der Lizenz, nicht nach dem Dateinamen: Small, wenn es
vorhanden ist, eine größere Größe nur, wenn sie die einzige ist. Die Zeile des Scan-Fensters nennt die Datei, ihre
Lizenz und jedes andere Modell, das ungenutzt blieb.

## Ausführung: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` baut eine ONNX-Runtime-Sitzung, verzögert, mit voller Graph-Optimierung, auf dem Backend, das
die Leiter gewählt hat. CPU wird als Ausweichlösung angehängt, damit ein Anbieter, der beim Anlegen der Sitzung
scheitert (ein alter Treiber), eine langsame Aufnahme bedeutet und keinen Absturz. Siehe
[Laufzeit und Abhängigkeiten](runtime.md#inference-backends).

- `warm_up()` baut die Sitzung und führt ein leeres Bild aus (die erste Inferenz auf einem frischen Graphen ist
  um ein Vielfaches langsamer als der Dauerbetrieb).
- `measure_throughput(frames)` misst so viele leere Bilder nach dem Aufwärmen. Das Fenster nutzt 6 und gibt das
  Ergebnis als Ansichten pro Sekunde an.

### Einpassen statt Strecken {#letterboxing-not-stretching}

Der Graph nimmt ein festes Quadrat, Gameplay ist 16:9. Ein Bild in ein Quadrat zu quetschen würde die scheinbare
Form von allem verändern. Da die Ausgabe eine geometrische Schätzung ist, würde sie als echte, falsche Geometrie
zusammengeführt. Deshalb wird jedes Bild so behandelt:

1. Es wird so skaliert, dass es ins Quadrat passt, unter Beibehaltung des Seitenverhältnisses (Flächeninterpolation
   beim Verkleinern, kubisch beim Vergrößern);
2. es wird mit **mittlerem Grau (114)** aufgefüllt. Schwarz oder Weiß wirkt wie eine starke Kante und trägt eine
   falsche Tiefensprungstelle in den Inhalt daneben;
3. es läuft durch das Modell;
4. die Auffüllung wird aus der Vorhersage herausgeschnitten, **bevor** sie (kubisch) auf die Auflösung des Bildes
   zurückskaliert wird. So bleibt der Rand nie in echten Pixeln.

Das Ergebnis ist ein `DepthMap` mit `metric=False` in der Größe des Quellbildes.

## Der PyTorch-Weg {#the-pytorch-path}

`DepthEstimator` führt das Hugging-Face-Modell direkt aus (fp16 auf CUDA, fp32 auf CPU), gestapelt nach
Bildgröße, jede Vorhersage bikubisch zurückskaliert. Der Scanner nutzt ihn nicht. Der Offline-Befehl
`reconstruct` nutzt ihn (siehe [Offline-Rekonstruktion](reconstruction-offline.md)). Das ist ein Grund, warum
dieser Befehl PyTorch und `transformers` braucht.

## Von relativ zu metrisch: `fit_scale` und `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Um vorhergesagte inverse Tiefe in Meter zu verwandeln, braucht man die affine Abbildung `Skala * vorhergesagt + Versatz`.
Wenn Anker mit bekannter Tiefe vorliegen (Merkmalspunkte, die zwischen bekannten Posen trianguliert wurden, oder die
verankerte Tiefe des vorherigen Bildes), löst `fit_scale` sie:

- Kleinste Quadrate **in der Disparität**, nicht in der Tiefe. Der Fehler des Netzes ist ungefähr gleichmäßig in der
  Disparität. In der Tiefe würden wenige weit entfernte Anker, bei denen ein Pixel Disparität zig Meter bedeutet,
  alles dominieren;
- **iterativ neu gewichtet** (12 Iterationen, Cauchy-artige Gewichte `1 / (1 + (r / 3 MAD)^2)`). Anker enthalten
  grobe Ausreißer, etwa einen Treffer auf ein fahrendes Auto oder einen Verfolgungsfehler. Ein einziger solcher Anker
  zieht in einer einfachen Anpassung das ganze Bild mit sich;
- braucht mindestens 2 brauchbare Anker. Sie meldet den mittleren absoluten Residuenwert und die Zahl der Inlier
  (Residuum innerhalb von 3 x dem Median).

`AffineFit.apply` gibt die Tiefe in Metern zurück, mit **+inf** für den Himmel. Er prüft den vorhergesagten Wert
ebenso wie den verankerten: Ein Himmelspixel, das null vorhersagt, käme bei `shift` heraus, klein, positiv und
endlich. Sonst würden alle Himmelspixel auf einer Phantomschale in einer Entfernung landen. Alles, was auf oder
unter `1e-4` vorhergesagt wird, ist Himmel, was auch immer die Anpassung sagt.

Die Fusion behält danach nur Tiefen zwischen 0,35 m und 60 m (siehe
[Fusion](reconstruction-fusion-and-texture.md#from-depth-to-points)).
