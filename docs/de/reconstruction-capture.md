---
title: Aufnahme, Masken und Bildqualität
nav_order: 2
lang: de
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Aufnahme, Masken und Bildqualität {#capture-masks-and-frame-quality}

Code: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Woher die Bilder kommen {#where-frames-come-from}

Ein Quellziel ist eines von:

| Ziel | Quelle | Hinweise |
|---|---|---|
| `monitor:<n>` | ein ganzer Monitor, live | die Option „Ganzer Bildschirm“ im Fenster, mit der Nummer unter „Welche“ |
| `window:<title>` | ein Fenster, live | die Option „Ein Fenster“ mit seinem Titel |
| ein Dateipfad | eine Videodatei | die Option „Eine Videodatei“; jedes Format, das OpenCV lesen kann |

### Live-Aufnahme: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` nutzt das Paket `windows-capture`, das **Windows Graphics Capture** umhüllt, die öffentliche
API, die Bildschirmrekorder verwenden. Nichts wird in das Spiel eingeschleust. Der Cursor wird nicht
aufgenommen, und es wird kein gelber Aufnahmerahmen gezeichnet.

Die Aufnahmebibliothek liefert Bilder an einen Rückruf im Thread des Compositors und erwartet, dass er sofort
zurückkehrt. Der Rückruf kopiert deshalb nur das Bild (der Puffer wird wiederverwendet), wandelt BGRA in RGB,
skaliert es, versieht es mit einem Zeitstempel und legt es in eine Warteschlange von **4 Bildern**. Ist die
Schlange voll, wird das **älteste Bild verworfen** und ein Zähler erhöht. Wenn das System hinterherhinkt,
sollen Bilder verloren gehen, nicht Speicher oder Korrektheit, und die Live-Ansicht soll zeigen, wo der
Spieler gerade ist. Verworfene Bilder stehen in der Statistikzeile des Fensters. Werden mehr als die Hälfte
verworfen, erscheint ein Hinweis.

Jedes Bild trägt `t` (Sekunden seit Beginn der Aufnahme) und `monotonic` (der rohe Wert von
`time.monotonic()` bei der Aufnahme). Das ist dieselbe Uhr, mit der auch Telemetrie-Pakete gestempelt
werden. So lassen sich Forza-Posen mit Bildern abgleichen.

`windows-capture` ist bei der Abhängigkeitsprüfung optional. Ohne es lässt sich trotzdem eine Videodatei scannen.

### Videodateien {#video-files}

`VideoSource` liest mit OpenCV, wandelt nach RGB und skaliert. Ein Container ohne Bildrate gilt als 30 fps.
Zeitstempel sind der Bildindex geteilt durch die Bildrate. Eine Datei hat keine Uhrzeit, deshalb lässt sich
Telemetrie nicht mit einem Video abgleichen.

### Auflösung {#resolution}

Bilder werden an der Quelle so skaliert, dass die lange Seite der Vorgabe-Größe entspricht (Entwurf 640,
Ausgewogen 960, Detailliert 1280 px), mit Flächeninterpolation. Ein 4K-Bild hat dreißigmal so viele Pixel,
wie das Tiefenmodell verwendet.

## Schlüsselbilder {#keyframes}

Fast jedes Bild einer Aufnahme ist überflüssig: Wer stillsteht, erzeugt hunderte Ansichten desselben Dings.
Eine Rekonstruktion braucht *Parallaxe*. Deshalb wird ein Bild nicht nach einem Timer behalten, sondern
danach, **wie stark sich das Bild seit dem zuletzt behaltenen Bild verändert hat**.

`picture_change(a, b)`:

1. Beide Bilder werden in Graustufen umgewandelt und auf ein 16 x 16-Raster aus Blockmitteln verkleinert.
   Blockmittel reagieren darauf, dass sich das Bild bewegt, nicht auf Körnung, Laub, Flackern oder das HUD;
2. die mittlere absolute Differenz, als Anteil von 255;
3. ist eine Weltmaske bekannt, wird jeder Block nach dem Anteil gewichtet, der Welt statt Cockpit ist. Ein
   halb mit Armaturenbrett bedeckter Block zählt also halb. Das wird genutzt, sobald die Maske mehr als 5 %
   des Rastergewichts abdeckt.

Der Schwellenwert **passt sich der Aufnahme an**. Für die ersten 30 Bilder ist er der Startwert der
Voreinstellung (0,020 / 0,010 / 0,004). Danach ist er das Quantil der Voreinstellung (0,85 / 0,65 / 0,40)
der letzten 240 gemessenen Veränderungen, nie unter 0,0001. Ein Bild wird behalten, wenn seine Veränderung
den Schwellenwert erreicht. Das erste Bild wird immer behalten. Ein fester Schwellenwert funktioniert über
Szenen hinweg nicht: Die Veränderung von Bild zu Bild in einer dunklen Cockpit-Runde ist nur ein kleiner
Bruchteil der eines hellen, strukturreichen Raums. „Das lebhafteste Drittel behalten“ bedeutet dagegen in
beiden dasselbe. Der verwendete Schwellenwert geht mit jeder Fortschrittsmeldung hinaus
(`ScanProgress.threshold`). Die Balken für die Gehgeschwindigkeit im Fenster und im Overlay messen die
letzte Veränderung dagegen (`ScanProgress.toward_next_view`).

Nur behaltene Bilder laufen durch das Tiefenmodell und die Rekonstruktion. Bilder werden nicht gespeichert,
außer ein Aufrufer verlangt es (`keep_frames`). 160 davon werden behalten, um das Netz einzufärben (siehe
[Farbe](reconstruction-fusion-and-texture.md#colour)).

Ein Scan endet, wenn er angehalten wird, wenn ein Video zu Ende ist, oder an der Zeit- oder der
Schlüsselbild-Grenze.

## Was nicht zur Welt gehört {#what-is-not-the-world}

Zwei Dinge in einem Spielbild sind keine Level-Geometrie, und beide verderben eine Rekonstruktion:

- **Das HUD.** Ein Fadenkreuz ist das am sichersten wiederkehrende Merkmal in jedem Bild. Ein Merkmalsvergleich
  liebt es: Es passt zwischen jedem Bildpaar perfekt, und jede Übereinstimmung ist ein Beleg dafür, dass sich
  die Kamera nicht bewegt hat. Das staucht die ganze Rekonstruktion zusammen.
- **Dinge, die an der Kamera befestigt sind.** Eine Waffe, eine Motorhaube, ein Cockpitrahmen, ein
  Armaturenbrett. Das ist echte Geometrie im falschen Koordinatensystem. Zusammengeführt verschmiert sie
  entlang des ganzen abgefahrenen Weges.

Zwei Detektoren finden sie. Beide erzeugen eine Maske (255 = Welt, 0 = nicht Welt) oder `None`, solange es
zu wenig Belege gibt. `None` bedeutet immer „alles verwenden“, nie „nichts verwenden“.

Die Maske wird angewendet:

- bei der **Merkmalserkennung** der visuellen Odometrie. Ein Fadenkreuz aus der Ausgabe zu maskieren, während
  es die Pose mitbestimmen darf, würde das sichtbare Symptom beheben und das schädliche belassen;
- auf die **zusammengeführten Pixel**, damit keine Cockpit-Geometrie zusammengeführt wird;
- auf das Maß für **Schärfe und Helligkeit**, weil ein Cockpit immer perfekt scharf ist;
- auf die **Bildveränderung**, die über die Schlüsselbilder entscheidet.

Sie wird **nicht** auf die Bilder angewendet, die dem Offline-VGGT-Löser übergeben werden (siehe
[Offline-Rekonstruktion](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: was sich nicht ändert {#screenmask-what-does-not-change}

Wird vom ersten Schlüsselbild an verwendet, bis FlowMask bereit ist.

- Jedes Bild wird in Graustufen umgewandelt, halbiert und weichgezeichnet (3 x 3 Gauß). So gilt ein
  Ein-Pixel-Zittern eines statischen HUD-Elements nicht als Bewegung.
- Die absolute Differenz jedes Pixels zum vorherigen Bild wird in einen exponentiellen Mittelwert gefaltet
  (Abklingfaktor 0,9). So folgt die Maske einem HUD, das mitten im Scan erscheint oder verschwindet.
- Sie lernt nur aus Bildern, in denen sich die Kamera nachweislich bewegt (im Scan: sobald mindestens ein
  Bild verfolgt wurde). Eine geparkte Kamera macht alles statisch.
- Nach **12** Lernbildern ist ein Pixel statisch, wenn seine mittlere Veränderung unter **0,22** der
  medianen Veränderung des Bildes liegt. Der Wert ist relativ, damit der Schwellenwert der Geschwindigkeit
  des Spielers folgt.
- Liest mehr als **45 %** des Bildes als statisch, ist die Annahme gescheitert (ein Menü, eine
  Zwischensequenz), und nichts wird maskiert.
- Die Maske wird um ein Pixel verkleinert (geglättete HUD-Kanten gehören zu keiner Seite) und wieder auf
  volle Größe skaliert.

Ihr Hinweis im Fenster: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` oder
`ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: was sich nie mitbewegt {#flowmask-what-never-travels}

Ein Cockpit ist nicht statisch: Nadeln schwingen, der Drehzahlmesser zuckt, die Minikarte dreht sich. Ein
Änderungsdetektor hält diese Pixel für Welt, und sie sind die schlechtesten Merkmale, die man einem
Posenlöser geben kann. FlowMask stellt die bessere Frage: **Welche Merkmale bleiben bestehen, ohne zu wandern?**

- Im Live-Scan lernt es einmal, aus den ersten **40 Schlüsselbildern** (Graustufen). Danach ersetzt es
  ScreenMask für den Rest des Scans.
- Die Bilder werden in Fenster von **30** Bildern geschnitten, die sich zur Hälfte überlappen. In jedem
  Fenster werden bis zu **800** Ecken gesetzt (`goodFeaturesToTrack`, Qualität 0,01, 8 px Abstand) und mit
  pyramidalem Lucas-Kanade (21 x 21, 4 Ebenen) verfolgt, mit einer **Vorwärts-Rückwärts-Prüfung**. Eine Spur,
  deren Rückwärtsfluss nicht innerhalb von 1 px dort landet, wo sie begann, wird verworfen. Ein Tracker, der
  auf ein benachbartes Muster abdriftet, würde genau die Signatur „bestehend, aber stationär“ erzeugen, nach
  der gesucht wird. Fenster mit weniger als 20 Bildern werden übersprungen. Kurze Fenster sind wichtig: Über
  einen langen Lauf verlässt fast jedes Weltmerkmal das Bild, und die Belege werden dünn.
- Die Nettowanderung jedes überlebenden Merkmals wird mit **2 % der Bildbreite** verglichen. Darunter gilt es
  als „festgefahren“, darüber als „bewegt“. Die Zählungen werden auf einem Raster aus **24 x 24** Zellen
  gesammelt, nach dem Ort, an dem jedes Merkmal begann.
- Eine Zelle ist gesperrt, wenn sie mindestens 2 festgefahrene Merkmale hat und mehr festgefahrene als
  bewegte, **und** mindestens 3 ihrer 8 Nachbarn ebenfalls gesperrt sind. Eine einzelne Zelle ist Rauschen,
  und dunkles Material erzeugt davon viele.
- Nur gesperrte Bereiche, die **mit dem Bildrand verbunden** sind, bleiben erhalten. Alles, was an der Kamera
  befestigt ist, erreicht einen Rand des Bildes. Was in der Mitte liegt und sich nicht bewegt, ist der
  Fluchtpunkt: Beim Vorwärtsfahren hat die Straße geradeaus keinen Fluss, und sie ist die Geometrie, die man
  am meisten braucht.
- Der verbleibende Bereich wird um eine Zelle vergrößert (der Rand eines Armaturenbretts ist ein Gradient).
- Würden mehr als **60 %** des Bildes maskiert, wird nichts maskiert. Bei Nachtmaterial hat die Mehrheit der
  Zellen kein verfolgbares Merkmal, und das sieht genauso aus wie ein Zifferblatt.

Sein Hinweis: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never
travels` oder, über 60 %, eine Meldung, dass nichts maskiert wird.

Der Offline-Weg lernt dieselbe FlowMask aus 4 Läufen zu je 90 aufeinanderfolgenden Bildern, verteilt über
das Video, bei 960 x 540 ([Offline](reconstruction-offline.md)).

## Bildqualität und Hinweise {#frame-quality-and-advice}

`QualityWatcher` beurteilt jedes Schlüsselbild und wählt **eine** Anweisung, damit das Overlay „langsamer
fahren“ sagen kann, solange noch Zeit dafür ist.

Pro Bild misst er nur auf den Weltpixeln (alle Pixel, wenn die Maske weniger als 5 % übrig lässt):

- **Schärfe**: Varianz des Laplace-Filters. Das ist das übliche Einpass-Maß, und es reagiert genau auf das,
  was Bewegungsunschärfe zerstört;
- **Helligkeit**: mittlerer Grauwert, 0-255.

Schärfe hat keine absolute Skala. Eine Nachtetappe und eine helle Straße unterscheiden sich um eine
Größenordnung, und beide sind scharf. Deshalb wird sie am **laufenden Median dieser Aufnahme** gemessen: die
letzten 90 Bilder, und es werden 20 gebraucht, bevor geurteilt wird. Jedes Bild wird mit dem Verlauf
*vor* seiner Aufnahme verglichen. So kann ein langer unscharfer Abschnitt den Median nicht zu sich selbst
herunterziehen.

| Zustand | Prüfung |
|---|---|
| flach | Schärfe höchstens 1,0 (ein Ladebildschirm, eine Wand, der Himmel) |
| dunkel | Helligkeit unter 26 |
| unscharf | Schärfe unter 0,55 des Medians, und nicht flach |

Die Hinweise, der erste Treffer gewinnt (geordnet danach, was den Scan am stärksten blockiert):

| Lage | Hinweis | Stufe |
|---|---|---|
| weniger als 20 Bilder | Man bekommt ein Gefühl für das Bild … | ok |
| flach | Nichts zu messen – die Kamera auf das Level richten, nicht auf den Himmel. | stop |
| dunkel | Zu dunkel zum Rekonstruieren. Scheinwerfer an, oder diesen Abschnitt bei Tageslicht fahren. | stop |
| unscharf | Unscharf – langsamer fahren. | warn |
| weniger als die Hälfte der Bilder verfolgt | Die Spur geht verloren – langsamer fahren und mehr vom Level im Bild behalten. | warn |
| weniger als 40 % der verfolgten Bilder fusioniert | Die Positionen sind gut, die Tiefe hält aber nicht. Näher an die Umgebung heranfahren. | warn |
| es gibt dünne Stellen | N dünne Stellen – die Karte zeigt sie. | ok |
| sonst | Gut – weiter so. | ok |

Das Level färbt den Hinweis im Overlay (grün / gelb / rot). Der Balken der **Schärfe** im Overlay ist die
Schärfe des Bildes relativ zum Median. (Der Code kennt außerdem „Blurred, and the camera is not moving. Check
the capture.“ für eine stehende Kamera. Der Scan meldet die Kamera immer als bewegt, deshalb wird sie nicht
angezeigt.)
