---
title: "Spiele: Aufnahme und Strecken"
nav_order: 4
lang: "de"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Spiele: Aufnahme und Strecken {#games-recording-and-courses}

So wird jedes unterstützte Spiel aufgenommen, was es sendet und welche seiner Strecken
sich aus den eigenen Dateien des Spiels exportieren lassen.

Für alle Spiele gelten dieselben Regeln: Eine Strecke kommt aus Dateien, die dem Nutzer
gehören, oder wird aus der eigenen Fahrt des Nutzers rekonstruiert. Verschlüsselte Archive
öffnen sich nur mit einem Schlüssel, den der Nutzer schon besitzt. Hier wird kein Schlüssel
mitgeliefert oder wiederhergestellt, und nichts wird in den Prozess eines Spiels eingeschleust.
Telemetrie kommt nur aus den Schnittstellen, die die Spiele dafür veröffentlichen (UDP-Ausgaben,
gemeinsamer Speicher, eigene Mod- und Plugin-Schnittstellen). Was ein Nutzer mit den Werkzeugen
anschaut, unterliegt weiterhin der Lizenz dieses Spiels.

## Telemetrie {#telemetry}

Jedes Spiel landet als `heat3d-lap`-Dateien ([`lap-format.md`](lap-format.md)), mit einheitlichen
Kanalnamen und einem `meta`-Block, der sagt, was seine Zahlen bedeuten: wie sein Schlupf skaliert
ist, ob Rundstrecke, Rallye oder Arcade, und der Untergrund, wenn bekannt. So behandelt jeder Leser
alle gleich. Alle Befehle sind `python -m heat3d_capture ...` in diesem Repository.

| Spiel | So wird aufgenommen | Position | Reifen und Schlupf | Driftwinkel | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out über UDP: `heat3d_capture telemetry` (leitet an FH Companion weiter) - oder die `.tele.gz`-Datei von FH Companion neben jeder Runde, zusammen mit der Rundendatei geladen | Welt-XYZ | Schlupfrate, Schräglaufwinkel, kombinierter Schlupf je Rad, normiert; Fahrbahnrumpeln | Geschwindigkeit im Fahrzeugsystem | Recorder getestet; `.tele.gz`-Leser an echten Runden geprüft |
| Forza Motorsport (inkl. 2023) | dasselbe; unterschieden über die Paketlänge | Welt-XYZ | dasselbe | dasselbe | Recorder getestet |
| Assetto Corsa, ACC, AC EVO | gemeinsamer Speicher: `telemetry --game ac / acc / acevo` | Mittelwert der Reifen-Aufstandspunkte | Schlupfrate und -winkel (physikalisch, mit einem typischen Asphalt-Spitzenwert skaliert); ABS und TC greifen ein (ACC, EVO) | Geschwindigkeit im Fahrzeugsystem | Recorder an synthetischen Seiten getestet |
| Assetto Corsa Rally | `telemetry --game acrally` | dasselbe | dasselbe; Radlasten; Temperaturen von Kelvin umgerechnet | Geschwindigkeit im Fahrzeugsystem | Recorder an synthetischen Seiten getestet |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Dokumente>/My Games/WRC/telemetry/config.json"` schaltet das Standardpaket `wrc` ein (die Datei wird vorher gesichert) | Welt-XYZ | Geschwindigkeit der Aufstandsfläche je Rad; Schlupf abgeleitet | Aus den Achsen des Autos und seiner Geschwindigkeit | Recorder an Paketen getestet, die aus dem dokumentierten Aufbau gebaut wurden |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: `<udp enabled="true" extradata="3" port="20777" delay="1" />` in `hardware_settings_config.xml` setzen, dann `telemetry --game dirtrally2` (oder `dirtrally`, `dirt4`) | Welt-XYZ | Geschwindigkeit der Aufstandsfläche je Rad; Schlupf abgeleitet. Kein Handbremskanal | Aus den Achsen des Autos und seiner Geschwindigkeit | dasselbe |
| Richard Burns Rally (RSF/NGP) | UDP-Telemetrie von NGP (`udpTelemetry=1`): `telemetry --game rbr` | Welt; die Hochachse wird aus der Etappe ermittelt | Federweg und Federkraft je Rad; keine Radgeschwindigkeiten | Die eigenen Geschwindigkeiten des Autos | dasselbe; Achsen und Geschwindigkeitseinheiten sind undokumentiert und werden aus den Daten bestimmt |
| BeamNG.drive | die Mod für das `heat3d`-Protokoll: `telemetry --game beamng --install`, dann Options > Other > Protocols > "others" | Welt, auf Y nach oben gedreht | Geschwindigkeit der Radoberfläche, Drehung, Last, Bodenkontakt; Schlupf abgeleitet | Aus den Achsen des Autos und seiner Geschwindigkeit | Recorder an Paketen getestet, die aus dem Struct der Mod gebaut wurden; die Mod ist im Spiel nicht getestet |
| Trackmania (2020) | das Openplanet-Plugin `Heat3dRecorder`: `telemetry --game trackmania --install`, geladen im Entwicklermodus von Openplanet; eine CSV-Datei pro Lauf im Speicherordner | Welt-XYZ | Schlupfkoeffizient von Trackmania je Rad; loser Untergrund aus den Materialien der Räder; in der Luft | Geschwindigkeit nach vorn und zur Seite | Leser getestet; das Plugin ist im Spiel nicht getestet |
| iRacing | eigene `.ibt`-Dateien; kein Recorder nötig | Breitengrad/Längengrad/Höhe, auf eine Tangentialebene gelegt | kein Schlupf (nicht protokolliert); Gierrate und Querbeschleunigung | Aus der Gierrate gegen den Weg | Leser an einer synthetischen Datei getestet |

Was keines der Rallyespiele sendet, nämlich Reifenschlupf, errechnet ein Leser: aus der
Aufstandsflächen- oder Radoberflächengeschwindigkeit jedes Rades gegen die Geschwindigkeit des
Autos, wo ein Spiel eine solche sendet (`(Rad - Auto) / Auto`), und aus der Raddrehung mit einem
Rollradius, der auf der Runde selbst gemessen wird, wo nur die Drehung gesendet wird. Der
Driftwinkel kommt aus der eigenen Geschwindigkeit des Autos (Forza, die AC-Spiele, Trackmania,
RBR), aus der Weltgeschwindigkeit, projiziert auf die Achsen des Autos (EA WRC, DiRT, BeamNG),
oder aus der Richtung gegen den Weg. Ob das Auto in der Luft ist, ergibt sich aus dem
Bodenkontakt, den Lasten oder der Federung seiner Räder.

Ist die Welt eines Spiels linkshändig, wie die von Forza, wird die Strecke in einem rechtshändigen
Viewer gespiegelt. Die eigene Lenkung und Federung der Runden verraten das. Spiele, deren
Händigkeit nicht dokumentiert ist (RBR, BeamNG, Trackmania), werden genauso behandelt: gemessen,
nicht angenommen.

Über die Fahrkanäle hinaus behalten die Recorder, was jedes Spiel zusätzlich mitliefert: bei den
AC-Spielen das Eingreifen von ABS und Traktionskontrolle, die Bremsbalance, DRS, den Boxenbegrenzer,
Boost sowie die Lebensdauer von Bremsbelägen und Bremsscheiben; bei iRacing die Hilfeeinstellungen,
die Bremsbalance, Kraftstoff, Öl- und Wassertemperaturen und jeden anderen Kanal, den es unter
seinem eigenen Namen protokolliert.

### Quellen und was noch nicht bestätigt ist {#sources-and-what-is-not-yet-confirmed}

- **Forza:** die offizielle Data-Out-Dokumentation (Forza Motorsport; Forza Horizon 6) für die
  Felder, ihre Einheiten und das Fahrzeugsystem (x nach rechts, y nach oben, z nach vorn - linkshändig).
  Womit Forza seinen Schlupf normiert, ist nicht dokumentiert: man misst, wo der Grip jedes Autos
  tatsächlich nachlässt, statt anzunehmen, dass 1 die Grenze ist.
- **Kunos:** das AC1-SDK, die Dokumentation des gemeinsamen Speichers von ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, gemessen; AC Rally nutzt das Layout von ACC, „confirmed via
  byte-by-byte probe“), `LuizZak/AssettoCorsaRallyTelemetryReader`. Auf welche Seite die
  x-Achse des Fahrzeugs zeigt, ist in beiden Richtungen dokumentiert: man nutzt die Größe des
  Driftwinkels, nicht sein Vorzeichen.
- **EA SPORTS WRC:** EAs UDP Telemetry Guide v1.3 und die Kanalliste, die das Spiel nach
  `readme/channels.json` schreibt; Offsets des Standardpakets `wrc`, wie sie nobonobo/obs-codemasters-telemetry
  dekodiert. Der Standardport des Spiels ist nicht dokumentiert; der Recorder schaltet das Paket auf 20777.
- **DiRT:** Codemasters' UDP-Dokument zu DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Die Richtung des Seitenvektors und die Einheit der
  Federwegposition sind in beiden Richtungen dokumentiert; keines von beiden entscheidet einen Befund.
- **RBR:** NGPs `rbr.telemetry.data.TelemetryData.h` (über mika-n/RBRUDPTelemetryLogger,
  groybe/rbr-udp-telem). Positionsachsen, Einheiten der Lage und die Geschwindigkeitseinheit sind nicht
  dokumentiert: der Recorder nimmt die Hochachse von der Etappe und die Geschwindigkeit aus den Positionen.
- **BeamNG:** documentation.beamng.com (Protokolle; refNodes: Fahrzeug +X links, -Y vorwärts,
  Z oben) und die eigenen Dateien des Spiels `lua/vehicle/protocols.lua` und `wheels.lua`. OutSim ist in
  aktuellen Versionen ein Stub; OutGauge hat keine Position und MotionSim keine Räder, deshalb die Mod.
- **Trackmania:** `CSceneVehicleVisState` und das VehicleState-Plugin von Openplanet, die Rundenzeit
  `CSmScriptPlayer`. Openplanet-Plugins können kein UDP senden, deshalb schreibt das Plugin Dateien.
  Nicht signierte Plugins laden nur im Entwicklermodus, was Online-Spiel einschränkt; das Plugin kann auf
  openplanet.dev signiert werden.

Keiner der Recorder wurde bisher gegen die hier vorhandenen Spiele im Live-Betrieb laufen gelassen. Die
erste echte Sitzung jedes Recorders ist der Test, der zählt. `tests/test_kunos.py`, `test_rally.py` und
`test_beamng.py` halten die Layouts fest, für die sie gebaut wurden. Jeder Recorder prüft seine Pakete,
sobald sie ankommen - die Geschwindigkeit gegen das Tempo, die Größe des Structs - und meldet, wenn ein
Layout nicht passt.

## Strecken: was pro Spiel exportiert wird {#courses-what-is-exported-per-game}

Eine Strecke ergänzt die Randsteine, Mauern und Auslaufzonen, die eine Linie erklären. Strecken exportiert
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`)
aus den eigenen Dateien des Spiels, wo das gebaut und an einer installierten Kopie geprüft wurde. Details stehen in der
[GameFiles-Dokumentation](https://holdi601.github.io/3DHeat-GameFiles/).

| Spiel | Strecke aus einer Runde |
|---|---|
| Forza Horizon | ja |
| BeamNG.drive | ja |
| Assetto Corsa Rally | ja |
| Assetto Corsa EVO | nein: der Inhalt ist nicht als Dateien lesbar |
| iRacing | nein: Streckenmodelle liegen in einem geschützten Format vor |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | noch nicht: jede braucht eine installierte Kopie, um gebaut und geprüft zu werden |

Der Weg über die Fahrt unten funktioniert bis dahin für alle.

## Der Weg, der für jedes Spiel funktioniert {#the-route-that-works-for-every-game}

GameCapture rekonstruiert ein Level aus Gameplay-Video. Der schwierige Teil ist der Kamerapfad, und bei
Forza ist er exakt, weil die Telemetrie die Pose des Autos in jedem Bild liefert. Jedes der oben genannten
Spiele hat jetzt dasselbe: Position und Lage, live, aus einer dokumentierten Schnittstelle. Speist man diese
in `pose/telemetry_pose.py` anstelle der von Forza, ist das der eine Schritt, der den Weg über die Fahrt für
alle exakt macht. Der Rest der Pipeline (Tiefe, Fusion, Texturierung) kümmert sich nicht darum, welches Spiel
die Bilder gezeichnet hat.
