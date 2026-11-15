---
title: Die .glb-Ausgabe
nav_order: 6
lang: "de"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Die .glb-Ausgabe {#the-glb-output}

Eine Rekonstruktion wird als binäre glTF-2.0-Datei (`.glb`) geschrieben, die der 3DHeat-Viewer über sein Panel „Hintergrund / Level“ ohne Sonderbehandlung lädt - derselbe Vertrag, den auch der Unreal-Exporter schreibt. Code: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Sie wird von Hand geschrieben statt über eine glTF-Bibliothek: Die Ausgabe ist eine schmale Teilmenge (ein Puffer, dicht gepackt, keine Animation, kein Skinning), und eine Abhängigkeit, die das ganze glTF schreiben kann, brächte für ein paar hundert Zeilen ihre eigene Versionsdrift mit.

## Was in der Datei eines Scans steckt {#what-is-in-a-scans-file}

| Teil (Knoten- und Mesh-Name) | Inhalt |
|---|---|
| `ground:<name>` | Dreiecke, die bis 35 Grad nach oben zeigen |
| `structure:<name>` | alles andere |

`<name>` ist der Dateiname ohne Endung, wenn im Fenster gespeichert wird, oder der Name des Videos bei `reconstruct`. Ein Teil ohne Dreiecke fehlt. Ein Scan schreibt nie einen `water:`-Teil. `asset.generator` ist `heat3d-capture-scan`.

## Der Vertrag {#the-contract}

- **Ein Knoten pro Teil**, benannt mit der Bezeichnung des Teils; das Mesh wiederholt den Namen. Der Viewer liest zuerst den *Knoten*-Namen, daher würde das bloße Benennen der Meshes die Einordnung verlieren.
- Die Bezeichnung ist `<Klasse>:<Name>` mit der Klasse `ground`, `structure` oder `water` - das Präfix, auf das der Viewer prüft (`^(ground|structure|water)\s*[:|]`), um die Klasse wörtlich zu übernehmen, statt sie aus der Geometrie zu raten. Boden wird voll gezeichnet, Bauten fast durchsichtig.
- **Die Koordinaten sind im Viewer-Raum**: Y nach oben, rechtshändig, und **in Zentimeter umgerechnet** (Meter x 100), damit sie zum Unreal-Exporter passen. So laden eine Aufnahme und ein Engine-Export desselben Ortes in gleicher Größe mit denselben Kamera-Voreinstellungen. Der oberste Eintrag `extras.unit_metres` der Datei ist `0.01` (eine Einheit ist ein Zentimeter), daher nimmt ein Leser, der in Metern arbeitet, etwa [`locate`](locate.md), sie in ihrer wahren Größe. Ein Scan, den Forza-Telemetrie platziert, ist die Ausnahme bei der Händigkeit: Er bleibt in der eigenen Welt des Spiels, Y nach oben und linkshändig, genau wie die Rundendateien, sodass die Runden, die darüber aufgezeichnet wurden, dort landen. Wenn der Maßstab eines Scans auf einem späteren Keyframe gefunden wurde ([Maßstab](reconstruction-pose.md#scale)), fließt dieser Faktor in den geschriebenen Maßstab ein.
- `COLOR_0` liest der Viewer; er färbt damit den Boden, wenn im Panel „Hintergrund / Level“ der Schalter *Erfasste Farbe* eingeschaltet ist (standardmäßig aus).
- Ein Scan mit von Hand markierten Stellen bekommt daneben eine `<name>.marks.json`; siehe [Speichern](reconstruction-scan-ui.md#saving).
- Je Primitive: `POSITION` (float VEC3, mit `min` und `max`, woraus der Viewer seine Kamera einrahmt), `NORMAL` (float VEC3), optional `COLOR_0` (float VEC3, 0..1), optional `TEXCOORD_0`; Indizes als 16 Bit, wenn jeder Index unter 65.536 liegt, sonst 32 Bit; Modus Dreiecke.
- Jede Pufferansicht beginnt 4-Byte-ausgerichtet; der JSON-Block wird mit Leerzeichen, der BIN-Block mit Nullen auf 4 Byte aufgefüllt.

## Prüfungen vor dem Schreiben {#checks-before-writing}

Jeder Teil wird geprüft und mit einer Meldung abgelehnt, die ihn nennt, wenn er keine Eckpunkte hat, eine Indexzahl, die keine ganzen Dreiecke ergibt, einen Index außerhalb des Bereichs oder negativ, nicht endliche Positionen, oder Normalen oder Farben, die nicht zur Eckpunktzahl passen. Normalen werden berechnet, wenn sie fehlen, **flächengewichtet** (Marching Cubes lässt Splitter neben großen Flächen zurück, und ein ungewichteter Mittelwert lässt winzige Dreiecke die Fläche überstimmen, auf der sie sitzen); ein entarteter Eckpunkt bekommt „oben“. Ohne jeden Teil zu schreiben ist ein Fehler.

Der Export liefert nichts zurück - und das Fenster meldet „Nothing to save“ - wenn das Volumen keine Oberfläche ergibt, statt eine leere Datei zu schreiben, die wie ein erfolgreicher Scan aussähe.

## Texturen {#textures}

Der Schreiber unterstützt pro Teil eine PNG-Grundfarben-Textur (mit UVs, einem beidseitigen, nicht metallischen, vollständig rauen Material). Scans nutzen sie nicht; sie tragen Farbe pro Eckpunkt. Siehe [Farbe](reconstruction-fusion-and-texture.md#colour).

## Das Referenz-Level {#the-reference-level}

`geometry/reference.py` baut über denselben Schreiber ein synthetisches Level von genau bekannter Größe: einen 400 m großen, unterteilten Boden, drei Gebäude von 20 x 20 x 12 m und einen 50 m großen Teich 1,5 m unter dem Boden, jede Klasse in einer eigenen flachen Farbe. Die eigenen Tests des Viewers erzeugen es und lesen es mit dem echten Parser des Viewers, sodass das Dateiformat auf beiden Seiten getestet bleibt, ohne Spiel und ohne Aufnahmehardware.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
