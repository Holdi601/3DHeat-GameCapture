---
title: Kamerapose und Skala
nav_order: 4
lang: de
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Kamerapose und Skala {#camera-pose-and-scale}

Eine Tiefenkarte sagt, wie weit Dinge von *einem* Blickpunkt entfernt sind. Um viele davon zu einem Level zu machen,
muss man wissen, wo jeder Blickpunkt war und in welchen Einheiten. Diese Seite behandelt die Live-Wege. Die Offline-Schätzung
der Feed-Forward-Posen steht auf [Offline-Rekonstruktion](reconstruction-offline.md).

Code: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Das Kameramodell {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` baut eine Lochkamera aus dem **horizontalen Sichtfeld**, das man im Fenster
einstellt: `fx = (Breite / 2) / tan(fov / 2)`, quadratische Pixel (`fy = fx`), der Hauptpunkt in der Bildmitte. Ein Spiel
veröffentlicht seine Projektion nicht, deshalb ist dies die eine angenommene Zahl. Ist sie zu eng, wirkt die Szene tiefer,
als sie ist. Der Offline-Weg nutzt 65 Grad.

Eine `Pose` wird als **Welt-von-Kamera** gespeichert: `rotation` (3 x 3) und `translation` = das Zentrum der Kamera in der Welt.
Das wollen die Strecke, die Abdeckungskarte und das Overlay alle.

## Visuelle Odometrie (die Vorgabe) {#visual-odometry-the-default}

`VisualOdometry` verfolgt jedes Schlüsselbild gegen das vorherige:

1. **Merkmale**: ORB, bis zu 1500 pro Bild, nur auf der Weltmaske erkannt (siehe
   [Aufnahme](reconstruction-capture.md#what-is-not-the-world)).
2. **Paarungen** zum vorherigen Schlüsselbild: Brute Force, Hamming-Abstand, gegenseitig geprüft (nur wechselseitig beste Paare).
3. **Heben in 3D**: Die Tiefe des vorherigen Bildes ist bereits in Welteinheiten, also werden seine gepaarten Pixel zu Weltpunkten.
4. **Kamera platzieren**: `solvePnPRansac` unter diesen Punkten (Reprojektionsfehler 3 px, Vertrauen 0,999, 200 Iterationen).
   Die Verschiebung kommt in denselben Einheiten heraus, **die Skala überquert also die Lücke**.
5. **Tiefe dieses Bildes verankern**: Seine eigene vorhergesagte inverse Tiefe wird (`fit_scale`) an die Tiefen der PnP-Inlier
   angepasst, und der Zyklus wiederholt sich.

Das **erste Bild** ist der Ursprung: identische Pose, und seine Tiefenaffine ist entweder die Bodenkalibrierung unten oder, ohne
eine solche, die Identität (die Rekonstruktion ist dann in sich stimmig, aber ohne Einheit).

Eine Pose braucht mindestens **18 RANSAC-Inlier**. Das liegt klar über PnPs Minimum von sechs, denn eine Lösung aus knapp genug
Punkten ist genau die, die mit Zuversicht falsch ist.

### Vertrauen {#confidence}

Jedes platzierte Bild erhält ein Vertrauen von 0..1, das seine Fusion und seine Abdeckung gewichtet:

| Pose stammt aus | Vertrauen |
|---|---|
| Telemetrie | 1,0 |
| einer Feed-Forward-Lösung | 0,85 |
| visueller Verfolgung | `Inlier / Paarungen x min(1, Inlier / 60)` |

### Wenn die Verfolgung bricht {#when-tracking-breaks}

Ein Bild, das nicht platziert werden kann, wird gemeldet, nie geraten: `no features in the frame (N found)`, `too few matches to
place the camera`, `could not relocalise`. Es wird keine Pose aufgezeichnet, und nichts wird fusioniert. Von der letzten Pose
weiterzumachen oder einen neuen Ursprung zu beginnen, würde das nächste Stück Level an einen beliebigen Versatz setzen, eine Naht,
die wie echte Geometrie aussieht.

Nach einem Bruch wird jedes neue Bild gegen eine Datenbank vergangener Schlüsselbilder **relokalisiert** (jedes vierte verfolgte
Bild wird aufgenommen, bis zu 120, das älteste fällt heraus), das jüngste zuerst, mit demselben Paarungs- und PnP-Schritt. Bis
eine Relokalisierung gelingt, werden Bilder verworfen. Ein wiedergefundenes Bild setzt sich im selben Koordinatensystem fort.
Wiederfindungen werden gezählt und im Fenster angezeigt (`N recovered`).

### Schleifenschluss: aus {#loop-closure-off}

Dieselbe Datenbank unterstützt Schleifenschluss: Man vergleicht mit Schlüsselbildern aus viel früher, erkennt einen Wiederbesuch
und schnappt die Strecke darauf zurück. **Er ist standardmäßig aus, und der Scanner schaltet ihn nie ein**
(`Reconstructor(loop_closure=False)`). Bei wiederholter Umgebung, einer Rallye-Etappe, einem Korridor, einer Reihe Bäume, sieht jeder
Abschnitt wie jeder andere aus. Der Merkmalsvergleich bestätigt dann falsche Wiederbesuche, die die Kamera nahe ihrem Start
festhalten, während sie weiterfährt. Es richtig zu machen braucht Ortserkennung (ein Wortvokabular oder einen gelernten Deskriptor)
und eine geometrische Prüfung gegen eine Karte, und das ist nicht gebaut.

Aus dem Code eingeschaltet, braucht ein Schleifenschluss: ein Schlüsselbild, mindestens 60 Schlüsselbilder alt, innerhalb von 6 m der
aktuellen Pose, mit mindestens 90 Inliern gepaart, das die Pose um mehr als 0,02 m und weniger als 6 m verschiebt. Selbst dann ersetzt
er nur die aktuelle Pose. Er ist kein Posengraph und bewegt weder frühere Bilder noch die fusionierte Geometrie.

## Telemetrie-Posen {#telemetry-poses}

Mit **Renn-Telemetrie (Forza)** -> **Auf Positionsdaten hören** eingeschaltet kommt der Kamerapfad aus Forzas Data Out statt aus den
Bildern (`ForzaPoseSource`):

- Ein Thread lauscht auf `127.0.0.1:<port>` (standardmäßig 5300) mit derselben Layouterkennung wie die Recorder
  ([Forza](telemetry-forza.md)). Pakete werden genutzt, solange `isRaceOn` gesetzt ist. Ein belegter Port wird gemeldet, nicht
  ausgelöst: Telemetrie ist eine Verbesserung, und der Scan läuft visuell weiter.
- Jedes Paket wird mit der **monotonen Zeit seiner Ankunft** gestempelt, derselben Uhr, mit der die Aufnahme ihre Bilder stempelt.
  Die Zeit des Spiels hat einen eigenen Nullpunkt, deshalb wird sie zum Abgleich nicht genutzt. Ein Jitter der Loopback-Schnittstelle
  von ein bis zwei Millisekunden sind bei 200 km/h etwa 6 cm.
- Ein laufender Puffer von 30 Sekunden wird gehalten. Die Pose eines Bildes wird aus den Messpunkten beidseits seines Aufnahmezeitpunkts
  **interpoliert**: Position linear, Rotation sphärisch (eine gemischte Matrix ist keine Rotation und würde jeden Punkt verzerren). Über
  eine Lücke von mehr als **0,35 s** hinaus, oder außerhalb des Puffers, gibt es keine Pose.
- `pose_from_forza`: Die Kamera wird am Auto platziert (der Versatz einer Verfolgerkamera wird nicht veröffentlicht). **Die Positionen
  bleiben genau so, wie das Spiel sie sendet**: Forzas Welt ist bereits Y-oben (x und z über die Karte, y die Höhe), so wie die Rundendateien
  und Routendateien sie schreiben. So landet die Oberfläche auf denselben Koordinaten wie die Runden, die darüber aufgezeichnet wurden.
  (Eine frühere Version tauschte y und z für eine „Z-oben“-Welt und legte die Strecke auf die Seite.)
- Die Rotation ist Gieren, dann Nicken, dann Rollen, mit den Richtungen, die an aufgezeichneten Runden abgelesen wurden: Die Fahrtrichtung
  `atan2(dx, dz)` ist gleich dem Gieren, die bergauf gefahrene Steigung ist gleich minus dem Nicken (positiv ist Nase nach unten), und das
  Rollen ist positiv, wenn die rechte Federung eingefedert ist (positiv senkt die rechte Seite). Die Achsen des Autos (x rechts, y oben,
  z vorn) werden dann durch Umdrehen von y in die der Kamera (x rechts, y unten, z vorn) gedreht.
- Forzas Welt ist **linkshändig**, und das Koordinatensystem der Kamera ist es nicht. Die resultierende Welt-von-Kamera-Matrix ist also
  eine Spiegelung (Determinante -1), und der Scan wird linkshändig wie die Rundendateien. Die Interpolation ist davon nicht betroffen
  (die Drehung zwischen zwei solchen Posen ist eine echte Rotation).
- Hat ein Bild keine Telemetrie-Pose (eine Lücke), fällt der Rekonstruktor für dieses Bild auf **visuelle Verfolgung** zurück und setzt
  von der letzten Telemetrie-Pose fort. Sobald der Feed wieder antwortet, geht er zu dessen Posen zurück. PnP liefert nur Rotationen. In
  einer gespiegelten Welt wird es deshalb mit an z gespiegelter Welt gelöst, und die Spiegelung wird wieder hineingefaltet. Das Bild landet
  in den Koordinaten des Spiels. Nur wenn auch die visuelle Verfolgung scheitert, ist das Bild nicht verfolgt.

### Tiefenskala aus der Telemetrie {#depth-scale-from-telemetry}

Das Spiel sagt, wo die Kamera ist, nicht wie weit alles entfernt ist. Jedes Bild braucht also trotzdem eine Verankerung der Tiefe. Aber
nicht durch Verkettung ab Bild null, dessen Einheit beliebig ist, während die Posen in Metern sind. Stattdessen werden Merkmale, die
zwischen dem vorherigen und dem aktuellen Bild gepaart wurden (mindestens 8), **direkt aus den beiden bekannten Posen trianguliert**, in
Metern, und die Tiefenkarte wird an die Punkte vor der Kamera angepasst. Jedes Bild wird gegen die Telemetrie verankert, es gibt also keine
Kette, die driften könnte.

Liegen die beiden Posen weniger als **0,05 m** auseinander, sind die Strahlen nahezu parallel, und die Triangulation ist Rauschen. Dann bleibt
das Bild unverankert: exakt positioniert, aber nicht fusioniert („positioned, but its depth has no scale yet“). Deshalb zählt das Fenster
*platzierte* und *fusionierte* Bilder getrennt.

## Skala {#scale}

Die visuelle Odometrie verkettet die relative Skala richtig, aber das ganze Level schwimmt auf einem unbekannten Faktor. Die relative
Ausgabe von Depth Anything hat beliebige Einheiten. Lässt man das erste Bild auf der Identität, steht die Welt im beliebigen Maßstab
innerhalb von Metern um die Kamera.

`GroundCalibrator` legt diesen Faktor aus **der Höhe der Kamera über dem Boden** fest, gemessen am **ersten Schlüsselbild** und, wenn dort
kein brauchbarer Boden ist, an den folgenden:

- Kamerahöhe: **1,15 m** (Augenhöhe eines Fahrers). Das Fenster nutzt immer diesen Wert. Skripte können 1,70 m übergeben
  (`WALKING_HEIGHT`, ein stehender Spieler) oder `None` (keine Kalibrierung).
- Bodenprobe: Zeilen 62-92 % von oben im Bild (unter dem Horizont, über Motorhaube oder Waffe) und Spalten 30-70 % quer (abseits der Ränder).
- Jeder Pixel dort mit einer brauchbaren Vorhersage wird mit der Tiefe `1 / vorhergesagt` in den Einheiten des Netzes gehoben. Punkte unter der
  optischen Achse ergeben eine Höhe unter der Kamera. Ihr Median ist die Kamerahöhe in Netzeinheiten. Also gilt `Meter pro Einheit = 1,15 / Median`,
  und die Affine des Bildes ist `Skala = 1 / Meter pro Einheit`, Versatz 0.
- Nur vertrauenswürdig mit mindestens 200 Bodenproben und einer **Streuung** (mittlere absolute Abweichung über Median) unter **0,60**.
- Beim ersten Schlüsselbild wird die Anpassung zur Einheit des Ursprungs, damit der Scan von Anfang an in Metern ist. Hat das erste Schlüsselbild
  keinen brauchbaren Boden, startet der Scan ohne Einheit, und jedes spätere verfolgte Schlüsselbild wird versucht, bis insgesamt **30 Bilder**.
  Die erste, die kalibriert, liefert *Meter pro Einheit*: den Median über das Bodenband der Tiefe, die sein Boden ergibt, geteilt durch die Tiefe,
  die die Kette für dieses Bild ergab. Alles schon Fusionierte liegt in der Einheit des ersten Bildes, deshalb wird der Faktor nicht in die Kette
  zurückgeführt. Er wird auf das ganze Level angewendet (und auf die markierten Stellen), wenn es geschrieben wird, und auf die angezeigte Entfernung
  inzwischen. Die Voxelgröße liegt dann in den Einheiten des ersten Bildes, ihre Größe in Metern unterscheidet sich von der Einstellung um diesen Faktor.
- Nach 30 Bildern ohne Boden bleibt der Scan ohne Einheit, und er sagt es.
- Mit Telemetrie werden spätere Schlüsselbilder nicht versucht: Die Tiefe ist an die Meter der Telemetrie verankert.

Innerhalb von zehn Prozent der wahren Größe zu liegen, ist besser, als um einen Faktor tausend danebenzuliegen. Telemetrie macht es, wo
vorhanden, überflüssig. Der Hinweis wird im Fenster unter der Verfolgungszeile angezeigt, als `Size: ...`: `measuring the ground`, `no flat
ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (mit `found on frame N, so the level is scaled
by F when it is written`, wenn es später kam), `no usable ground in the first N frames - sizes are relative, not metres` oder `in metres, from
the telemetry's positions`.

## Bündelausgleich und lange Spuren (nicht verdrahtet) {#bundle-adjustment-and-long-tracks-not-wired-in}

Zwei Teile existieren für einen künftigen Fenster-Löser und sind **im Scanner nicht genutzt**:

- **`FeatureTracks`** hält die Identität von Merkmalen über Hunderte Bilder mit Lucas-Kanade-Verfolgung (600 Merkmale, neu gesät unter
  60 %, Vorwärts-Rückwärts-Toleranz 1 px, neue Merkmale 10 px von bestehenden entfernt). Das braucht der Bündelausgleich, denn die Deskriptor-
  Paarung zwischen aufeinanderfolgenden Bildern liefert nur Paare.
- **`bundle_adjust`** verfeinert ein Fenster aus Posen und Punkten zusammen mit `scipy.optimize.least_squares` (Vertrauensbereich, Soft-L1-Verlust
  mit 2 px Skala, ein explizites Muster der Jacobi-Dünnbesetzung, feste Kameras exakt wiederhergestellt). Getestet gegen bekannte Wahrheit in
  `tests/test_bundle.py`.

`WindowedOdometry` kombiniert beides (Fenster von 12 Schlüsselbildern, ein Löser alle 3 Schlüsselbilder, die ersten zwei Kameras fest, Punkte
mit mehr als 6 px Fehler verworfen, Sprünge über das 6-fache des letzten Schritts abgelehnt). Seine Dokumentation hält fest, dass er auf echtem
Material den **Weg kollabieren ließ und viel langsamer war** als die Verfolgung von Bild zu Bild. Bekannte Ursachen sind die Eichfreiheit (Skala) und
eine Bootstrap-Tiefe, eine dritte Ursache ist unbekannt. Deshalb bleibt die Odometrie von Bild zu Bild die Vorgabe. Die im Code genannte wahrscheinliche
Korrektur ist ein Zwei-Ansicht-Bootstrap über die Essentialmatrix, mit der festen Basislinie aus der Bodenebenen-Kalibrierung.
