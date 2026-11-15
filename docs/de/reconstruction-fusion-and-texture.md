---
title: Fusion, Abdeckung und Farbe
nav_order: 5
lang: "de"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusion, Abdeckung und Farbe {#fusion-coverage-and-colour}

Code: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Jedes platzierte Schlüsselbild aktualisiert zwei dünn besetzte Gitter zugleich: das **Oberflächenvolumen**, aus dem
das Netz wird, und das **Abdeckungsgitter**, das sagt, wie sehr man ihm trauen darf und wohin man zurückkehren
soll. Beide werden pro Schlüsselbild aktualisiert und nicht erst am Ende, weil die Abdeckungskarte ist, woran sich
der Spieler orientiert.

## Von der Tiefe zu Punkten {#from-depth-to-points}

Für jedes Schlüsselbild, dessen Pose bekannt **und** dessen Tiefe skaliert ist:

1. Es wird jeder zweite Pixel in jeder Richtung verwendet (`PIXEL_STRIDE = 2`). Benachbarte Pixel derselben Oberfläche
   sind keine unabhängigen Messungen.
2. Die Tiefe wird über die affine Anpassung des Bildes in Meter umgerechnet.
3. Behalten werden nur Tiefen zwischen **0,35 m** (näher ist die Waffe, das HUD, die Motorhaube) und **60 m**
   (der Fehler einer monokularen Messung wächst ungefähr mit dem Quadrat der Entfernung, weit entfernte Punkte sind
   also Rauschen in der Form von Geometrie), und nur auf Weltpixeln der Maske.
4. Die Punkte werden durch das Kameramodell gehoben und mit der Pose in die Welt gebracht.
5. Jeder Punkt trägt die Farbe seines Pixels.

Ein Bild, das positioniert ist, aber keine Tiefenskala hat, zählt als *platziert*, aber nicht als *fusioniert*.

## Das Oberflächenvolumen {#the-surface-volume}

`SurfaceVolume(voxel=0.25)`. Die Voxelgröße ist die Einstellung „Surface detail“ im Fenster.

### Gewichtete Belegung, kein TSDF {#weighted-occupancy-not-a-tsdf}

Ein abgeschnittenes vorzeichenbehaftetes Distanzfeld (TSDF) schneidet entlang jedes Pixelstrahls und erfasst dünne
Strukturen und sauberen freien Raum richtig, denn es weiß, dass ein Strahl *durch* leeren Raum ging. Das heißt, für
jeden von Hunderten Millionen Pixeln den Strahl abzugehen. Dieses Volumen sammelt stattdessen **gewichtete Belegung**
pro Voxel und führt Marching Cubes auf dem geglätteten Ergebnis aus. Das ist schnell genug, um während des Scans zu
laufen, auf einem Rechner ohne brauchbare GPU, und die Ausgabe ist eine geschlossene Oberfläche statt einer Punktwolke.
Der Preis: Dünne Strukturen und freier Raum sind schlechter als bei einem TSDF.

### Ein Bild einfügen {#integrating-a-frame}

- Die Punkte werden in Voxel einsortiert (`floor(Punkt / Voxel)`).
- Jeder berührte Voxel erhält `Gewicht x sqrt(Anzahl / max. Anzahl)`. Dabei ist `Anzahl` die Zahl der Punkte des Bildes,
  die in ihn fielen, und `Gewicht = max(0,1; Posenvertrauen)`. Die Wurzel bedeutet: Ab einem Punkt zählen weitere Pixel
  derselben Oberfläche vom selben Ort nicht mehr als Beleg. Die Gewichtung nach Posenvertrauen verhindert, dass eine
  zweifelhafte Pose die Oberfläche verschiebt.
- Die Farbe ist ein laufender gewichteter Mittelwert pro Voxel.

Das Gitter ist **dünn besetzt**: Eine gefahrene Strecke berührt nur einen winzigen Bruchteil ihres Begrenzungsquaders.
Die Voxelkoordinaten werden in einen 64-Bit-Schlüssel gepackt (21 Bit pro Achse, bis zu +-1.048.575 Voxel, bei 0,25 m
etwa +-262 km) und mit einem sortierten Array und binärer Suche nachgeschlagen, vollständig vektorisiert.

### Das Netz extrahieren {#extracting-the-mesh}

1. Voxel mit einem Gewicht unter **0,35** werden verworfen. Einzelne verstreute Punkte an Silhouettenkanten würden
   sonst zu Spitzen.
2. Die Gewichte werden mit dem **75. Perzentil** über den ganzen Scan skaliert und auf 1 begrenzt.
3. Der belegte Raum wird in **Blöcke von 64 Voxeln** pro Seite zerlegt. Jeder Block wird mit einem **3-Voxel-Halo**
   aus den Daten seiner Nachbarn gebildet. Ohne ihn würde sich jede Blockgrenze zu einer Wand schließen, und eine
   Straße käme als Reihe von Kisten heraus.
4. Das Feld jedes Blocks wird mit einem Gauß (Sigma 0,8 Voxel) geglättet, um die Runzeln zu entfernen, die Tiefenrauschen
   hinterlässt.
5. **Durchgang eins**: Das 99. Perzentil des geglätteten Feldes, über alle Blöcke gesammelt (höchstens 2 Millionen
   Werte), legt eine globale Pegelskala fest. Würde man pro Block normieren, würde ein einzelner Ausreißer im eigenen
   leeren Block zu einer vollen Oberfläche befördert.
6. **Durchgang zwei**: Das Feld jedes Blocks wird durch diese Skala geteilt, Marching Cubes bei **0,5**. Ein Dreieck
   gehört zu dem Block, in dem sein **Schwerpunkt** liegt. So wird ein Dreieck, das über eine Nahtstelle reicht, genau
   einmal ausgegeben.
7. Die Eckpunkte werden in Weltmaße an den Voxelmitten gesetzt. Jeder Eckpunkt erhält die Farbe seines Voxels
   (mittelgrau, wo er außerhalb eines belegten Voxels liegt).

Die blockweise Extraktion macht einen streckengroßen Scan möglich. Ein dichtes Array über einen Kilometer-großen
Quadrat-Bereich bei 0,25 m wären Milliarden Zellen. `tests/test_track_scale.py` stellt sicher, dass es in diesem Maßstab
funktioniert, mit einem Speicherbedarf proportional zum Gescannten.

### Boden und Struktur {#ground-and-structure}

`classify` ordnet jedes Dreieck nach seiner Normalen zu (ausgerichtet an den extrahierten Eckpunktnormalen): innerhalb
von **35 Grad senkrecht nach oben** ist es `ground`, alles andere `structure`. Der Viewer zeichnet Boden massiv und
Strukturen nahezu transparent. **Wasser wird nie beansprucht.** Es lässt sich nach der Form nicht von ebenem Boden
unterscheiden, und ein falsches Label würde einen Innenhof als See darstellen. Jedes Label wird ein Teil der `.glb`-Datei
([Die .glb-Ausgabe](glb-output.md)).

## Abdeckung {#coverage}

`CoverageGrid(voxel=0.5)` erfasst pro halbmeter-großer Zelle vier Dinge, die nicht dasselbe sind:

| Größe | Gespeichert | Wertung (je auf 0..1 begrenzt) | Warum sie getrennt zählt |
|---|---|---|---|
| Wie oft gesehen | Zahl der Schlüsselbilder, die die Zelle gesehen haben | `Anzahl / 3` | einmal ist eine Vermutung ohne etwas, woran man sie messen könnte |
| Aus wie vielen Richtungen | Summe der Blickrichtungs-Einheitsvektoren | `(1 - Streuung) / (1 - 0,93)`, mit Streuung = Länge der Summe / Anzahl | zwanzig Bilder, die geradeaus auf eine Wand zulaufen, haben keine Parallaxe untereinander; zwei Ansichten im Abstand von dreißig Grad sind mehr wert |
| Aus welcher Entfernung | nächste Blickentfernung | `1 - nächste / 40 m` | der Tiefenfehler wächst ungefähr mit dem Quadrat der Entfernung |
| Wie gut die Kamera platziert war | bestes Posenvertrauen | das Vertrauen selbst | Geometrie, die mit einer zweifelhaften Pose fusioniert wurde, landet am falschen Ort |

Die Punkte eines Bildes werden zuerst pro Zelle gruppiert. So zählen zehntausend Pixel einer Wand als eine
Beobachtung aus einer Richtung.

**Qualität = das Produkt der vier Glieder**, nicht ihr Mittelwert. Sie sind Bedingungen, die alle erfüllt sein müssen.
Eine Stelle, die zweihundertmal aus einer Richtung auf sechzig Meter gesehen wurde, ist schlecht beobachtet, und ein
Mittelwert würde das hinter einem ausgezeichneten Glied verstecken.

Die wichtigsten Zahlen (`summary`): belegte Zellen, der Anteil mit einer Qualität von mindestens 0,5 („% well seen“ im
Fenster), die mittlere Qualität und das Volumen.

### Dünne Stellen {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. Zellen mit Qualität unter 0,35 sind dünn;
2. dünne Zellen werden nach **Zusammenhang** gruppiert (26er-Nachbarschaft, Union-Find nur über die belegten Zellen,
   nicht über ein Raster des Begrenzungsquaders, das bei einer langen Fahrt Millionen leerer Zellen wären);
3. Gruppen mit weniger als 8 Zellen werden ignoriert;
4. Der Grund jeder Gruppe ist der häufigste *schwächste Teilwert* ihrer Zellen, und ihre Position ist der Mittelwert
   ihrer Zellen;
5. sortiert nach Größe (größte zuerst, dann nach schlechtester Qualität), höchstens 8.

| Grund | angezeigter Hinweis |
|---|---|
| wenige Ansichten | Nur ein- oder zweimal gesehen – geh noch einmal daran vorbei. |
| eine Richtung | Nur aus einem Winkel gesehen. Seitlich gehen und es noch einmal ansehen. |
| entfernt | Nur aus großer Entfernung gesehen. Näher herangehen. |
| schlechtes Tracking | Die Kamera war hier nicht gut verortet. Langsamer heranfahren. |

Der Zusammenhang ist wichtig: Eine Gruppierung nach einem festen Blockraster würde einen vernachlässigten Nebenraum
als viele getrennte Ringe melden. Niemand könnte dann acht Orte von einem unterscheiden, der achtmal gezählt wurde.

### Die Draufsicht {#the-plan-view}

`top_down(resolution)` projiziert die Zellen auf x/z und behält pro Spalte die **beste** Qualität. Wer in einem Raum
steht, hat eine schlechte Abdeckung der Decke und eine ausgezeichnete des Bodens. Ein Mittelwert würde den Raum gelb
färben. Nie beobachtete Spalten werden gesondert markiert. Das Fenster zeichnet sie mit 200 x 200, das Overlay mit
120 x 120 ([Die Scan-Oberfläche](reconstruction-scan-ui.md#the-coverage-map)).

### Ist das rekonstruierbar? {#is-this-reconstructable}

Alle 25 fusionierten Bilder, sobald es mindestens 500 Zellen gibt:

| Befund | Urteil | Meldung (gekürzt) |
|---|---|---|
| weniger als 2 % der Zellen haben eine Blickstreuung unter 0,93 | nicht rekonstruierbar | Kaum Parallaxe. Entweder schaut die Kamera nie zur Seite, oder das Tracking driftet, sodass dieselbe Oberfläche nie zweimal an derselben Stelle landet. Prüf die Zahl der platzierten Bilder: Ist sie hoch, ist es Drift. |
| mediane nächste Entfernung über 25 m | nicht rekonstruierbar | Alles wurde aus N m oder weiter gesehen … Geh näher an das heran, was du erfassen willst. |
| weniger als 6 % mit guter Streuung | rekonstruierbar, mit Warnung | Dünne Parallaxe – die Geometrie wird grob. Seitlich zu dem gehen, was man ansieht, hilft am meisten. |

Geringe Parallaxe hat zwei Ursachen, die dies nicht unterscheiden kann. Deshalb nennt die Meldung beide.

## Farbe {#colour}

Die Farbe pro Voxel bei der Fusion ist billig und live, aber verwaschen: Jeder Pixel einer Viertelmeter-Zelle wird
gemittelt, auch jene, die von dreißig Metern seitlich gesehen wurden. Deshalb wird das Netz beim Export noch einmal
gefärbt, einmal, aus den Bildern selbst:

- **Behaltene Bilder**: bis zu **160** Schlüsselbilder (Bild und Pose), mit Reservoir-Sampling ausgewählt, damit sie
  sich über den ganzen Scan verteilen und nicht nur auf sein Ende entfallen.
- **Pro Eckpunkt** (`project_colours`) trägt jedes behaltene Bild bei, wenn der Eckpunkt vor der Kamera liegt und im
  Bild ist, die Oberfläche höchstens etwa 70 Grad von einer frontalen Ansicht abgewandt ist (`|Normale . Blickrichtung| > 0,34`),
  er näher als **35 m** ist, und nichts Näheres davor stand (unten).
- Jede solche Ansicht wird mit `Frontalität x (1 - Entfernung / 35)` bewertet, damit eine nahe, frontale Ansicht eine
  ferne, schräge schlägt. Die **4 am höchsten bewerteten** Ansichten jedes Eckpunkts werden behalten (unabhängig von der
  Reihenfolge der Bilder: Eine bessere Ansicht ersetzt die schwächste der vier) und mit derselben Wertung gewichtet
  gemischt.
- **Verdeckung**: In jedem Bild werden die eigenen Eckpunkte des Netzes, die im Blick liegen, in einen Tiefenpuffer aus
  2-Pixel-Zellen gezeichnet, und pro Zelle wird der nächste behalten. Liegt ein Eckpunkt mehr als `0,3 m + 5 %` seiner
  Entfernung hinter dem nächsten in seiner Zelle, war er in diesem Bild verdeckt, etwa durch eine Wand zwischen Kamera
  und Straße dahinter. Diese Ansicht zählt dann nicht. Der Test kennt nur das Netz: Ein Verdecker, der nie fusioniert
  wurde (ein vorbeifahrendes Auto, ein Cockpitpfosten außerhalb der HUD-Maske), wird nicht erkannt.
- Ein Eckpunkt, den kein Bild gesehen hat, behält seine Voxelfarbe. Hat er auch die nicht, ist er mittelgrau. Schwarz
  würde wie ein Loch wirken.

Die Farbe wird als pro Eckpunkt `COLOR_0` geschrieben, nicht als Texturatlas. Die Standardansicht des Viewers ist eine
graue Karte unter gesättigter Hitze. Die Farbe ist dafür da, auf einer gescannten Rundstrecke die Straße zu finden, wo die
Geometrie allein sie nicht vom Randstreifen trennt. Sie wird mit dem Schalter
„Erfasste Farbe“ im Panel „Hintergrund / Level“ eingeschaltet. Ein Atlas würde die Dateigröße
vervielfachen und einen Unwrapper brauchen, für eine Ansicht, die bewusst nicht die Vorgabe ist. Blender und andere
glTF-Werkzeuge lesen `COLOR_0`.
