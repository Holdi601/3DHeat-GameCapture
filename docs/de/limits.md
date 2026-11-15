---
title: "Grenzen und Überprüfung"
nav_order: 9
lang: "de"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Grenzen und was überprüft ist {#limits-and-what-is-verified}

Eine ehrliche Liste: was die Werkzeuge nicht tun und was nicht gegen ein laufendes Spiel geprüft wurde.

## Telemetrie {#telemetry}

| Recorder | Status |
|---|---|
| Forza | Auf der offiziellen Data-Out-Dokumentation aufgebaut; das Layout wird aus den Paketen selbst erkannt. Der `.tele.gz`-Leser von FH Companion im Viewer wurde an echten Runden geprüft. |
| AC, ACC, AC EVO, AC Rally | Getestet an synthetischen Seiten, aus den veröffentlichten Layouts gebaut. **Noch nicht gegen die laufenden Spiele getestet.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Getestet an Paketen, die aus den dokumentierten Layouts gebaut wurden. **Noch nicht gegen die laufenden Spiele getestet.** Die Achsen, die Lage und die Geschwindigkeitseinheiten von RBR sind undokumentiert und werden aus den Daten behandelt. |
| BeamNG.drive | Der Recorder ist an Paketen getestet, die aus der Struktur des Mods gebaut wurden. **Der Mod wurde noch nicht im Spiel ausgeführt.** |
| Trackmania | Der CSV-Leser des Viewers ist getestet. **Das Plugin wurde noch nicht im Spiel ausgeführt.** Es lädt nur im Entwicklermodus von Openplanet. |
| iRacing | Der `.ibt`-Leser des Viewers ist an einer synthetischen Datei getestet. |

Weitere Grenzen der Telemetrie:

- Die Schlupf-Normierung von Forza ist undokumentiert; Kunos-Schlupf wird mit einem typischen Asphalt-Maximum
  skaliert, eine Näherung.
- Der Richtungssinn einiger seitlicher Achsen im Fahrzeug (Kunos, DiRT) ist in beide Richtungen dokumentiert; die
  Größe des Driftwinkels ist verlässlich, sein Vorzeichen nicht.
- Keines der Rallyespiele sendet den Reifenschlupf; er wird im Viewer abgeleitet. RBR sendet keine Radgeschwindigkeiten.
- Der Untergrund einer Rallye-Etappe wird nur geschrieben, wenn `--surface` angegeben ist; sonst nennt die Datei keinen,
  und der Viewer schließt ihn aus dem Etappen- oder Eventnamen, dann aus dem Fahrstil, standardmäßig unscharf.
- Rundenerkennung ohne Rundenzähler (AC EVO, AC Rally, BeamNG) nimmt den Punkt, an dem die Aufnahme begann, als Linie;
  deshalb an der Startlinie mit der Aufnahme beginnen.
- Ein Zurücksetzen des BeamNG-Fahrzeugs schließt die offene Runde in diesem Moment: Sie wird als Teillauf geschrieben,
  wenn sie die Mindeststrecke (300 m) abgedeckt hat, und sonst verworfen.
- `route` speichert etwa alle 2 Sekunden während der Fahrt; ein Absturz oder ein beendeter Prozess verliert höchstens
  die Positionen seit dem letzten Speichern.
- Forza Horizon sendet keinen Streckennamen, daher haben Forza-Rundendateien `"track": null`; Forza Motorsport (2023)
  sendet nur eine Zahl, die als `lap.trackOrdinal` behalten wird.

## Rekonstruktion {#reconstruction}

- **Die Tiefe wird geschätzt, nicht gelesen.** Die Obergrenze des ganzen Ansatzes und der Preis dafür, dass der
  Spielprozess nie berührt wird.
- **Das Sichtfeld wird angenommen, nicht gemessen.** Ist es zu eng, wird das Level tiefer rekonstruiert, als es ist.
- **Der globale Maßstab** kommt aus einer angenommenen Kamerahöhe (1,15 m im Fenster) oder aus der Telemetrie. Er wird am
  ersten Schlüsselbild gemessen; hat dieses keinen brauchbaren Boden, werden die nächsten Schlüsselbilder versucht (bis zu
  30 Bilder), und ein später gefundener Maßstab wird beim Schreiben auf das ganze Level angewandt. Die Zeile „Size:“ des
  Fensters sagt, was geschehen ist; wurde gar kein Boden gefunden, bleibt der Scan ohne Einheit. Die Voxelgröße ist dann in
  den Einheiten des ersten Bildes, daher unterscheidet sich ihre Größe in Metern von der Einstellung. Offline-Rekonstruktionen
  sind in den eigenen Einheiten der Lösung.
- **Die Schleifenschließung ist aus** und ist, wenn sie im Code eingeschaltet wird, kein Posengraph; die Drift wird nur
  durch die Qualität des Verfolgens von Bild zu Bild begrenzt.
- **Fensterweise Bündelausgleich existiert, ist aber nicht eingebunden**; er brach bei echtem Material zusammen.
- **Die Oberfläche ist eine gewichtete Belegung, kein TSDF**: dünne Strukturen und freier Raum sind schlechter, als ein TSDF
  sie erfassen würde.
- **Kein Textur-Atlas.** Die Farbe liegt pro Eckpunkt (`COLOR_0`) an und wird aus den 4 besten Ansichten unter 160 behaltenen
  Bildern gemischt. Der Verdeckungstest ist grob: Er prüft gegen die eigenen Eckpunkte des Netzes in einem Tiefenpuffer mit
  2 Pixeln, daher wird ein Verdecker, den das Netz nicht enthält (ein vorbeifahrendes Auto), nicht erkannt.
- **Wasser wird nie beschriftet**; alles ist Boden oder Struktur.
- **Die Vorwärtslösung ist nicht live**: Sie braucht zuerst die Aufnahme. Die adaptive Nachlösung schwieriger Abschnitte
  ist nicht gebaut.
- **Telemetrie-Posen** setzen die Kamera an das Auto (der Versatz einer Verfolgerkamera ist unbekannt). Die Positionen
  werden so übernommen, wie Forza sie sendet (Y nach oben, wie in den Rundendateien); der Richtungssinn von Gier, Nick und
  Rollen wurde an aufgezeichneten Runden abgelesen (Fahrtrichtung, Steigung, welche Seite die Federung einfedert), nicht an
  der laufenden Kamera des Spiels.
- Das Overlay kann nicht über **exklusives Vollbild** zeichnen; den Fenstermodus „Randlos“ (borderless) verwenden.
- Globale Tastenkürzel, das durchklickbare Overlay und die Live-Aufnahme gibt es nur **unter Windows**.
- Beim Schließen des Fensters wird nicht nach dem Speichern gefragt.

## Was gemessen wird {#what-is-measured}

- `tests/test_accuracy.py`: ein synthetischer Raum mit bekanntem Weg und analytischer Tiefe - platzierte Bilder,
  Fehler des Weges, zurückgelegte Strecke, Raumgröße, Oberfläche an den Wänden ([Level-Rekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: eine Straße mit bekannter Breite, außermittig befahren, wird in ihrer Breite rekonstruiert.
- `tests/test_track_scale.py`: Oberflächenextraktion im Rennstreckenmaßstab, Speicher proportional zu dem, was gescannt
  wurde, Blöcke, die sich zu einer Oberfläche verbinden.
- `tests/test_glb.py` plus die eigenen Tests des Viewers: der `.glb`-Vertrag von beiden Seiten.
- Wie das Tiefennetz bei echtem Gameplay abschneidet, kann keine synthetische Szene beantworten, und das wird durch die
  Testsuite nicht gemessen.
