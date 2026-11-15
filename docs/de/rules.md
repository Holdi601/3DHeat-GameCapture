---
title: Die Regeln dieses Werkzeugs
nav_order: 2
lang: "de"
source: rules.md
source_hash: "88d5b7041a49"
nav_exclude: true
search_exclude: true
---
# Die Regeln, unter denen dies gebaut ist {#the-rules-this-is-built-under}

Jeder Teil von 3DHeat GameCapture folgt denselben Zwängen. Sie sind Entwurfsentscheidungen, keine Haftungsausschlüsse, und mehrere davon kosten bewusst Genauigkeit.

## Nichts wird eingeschleust, nichts wird abgefangen {#nothing-is-injected-nothing-is-hooked}

Kein Teil davon hängt sich an einen Spielprozess, liest dessen Speicher oder greift auf seine Grafik-API zu.

- **Bilder** kommen von Windows Graphics Capture, der öffentlichen API, die Bildschirmrecorder nutzen (über das Paket `windows-capture`), oder aus einer Videodatei. Siehe [Aufnahme, Masken und Bildqualität](reconstruction-capture.md).
- **Telemetrie** kommt nur aus Schnittstellen, die die Spiele dafür veröffentlichen:
  - Forzas Data-Out-UDP-Strom, im Spiel in den Einstellungen eingeschaltet;
  - die benannten Shared-Memory-Seiten, die Kunos-Spiele für Apps veröffentlichen (`Local\acpmf_physics` und Verwandte). Sie werden schreibgeschützt mit `mmap` geöffnet; das ist der dokumentierte Weg, auf dem Apps sie lesen, kein Auslesen des Speichers des Spielprozesses;
  - die UDP-Telemetrie, die EA SPORTS WRC, die DiRT-Spiele und Richard Burns Rally (über das RSF/NGP-Plugin) senden, wenn sie in ihren eigenen Einstellungsdateien eingeschaltet ist;
  - die Protokollschnittstelle von BeamNG, über einen kleinen Lua-„Protokoll“-Mod, den die eigene `lua/vehicle/protocols.lua` des Spiels lädt und sendet;
  - die Openplanet-Plugin-Schnittstelle von Trackmania, über ein Plugin, das nur liest, was Openplanet freigibt, und Dateien schreibt;
  - die eigenen `.ibt`-Telemetriedateien von iRacing.

## Warum das wichtig ist {#why-it-matters}

Das Spiel kennt die Tiefe jedes Pixels genau, und ein abgefangener Tiefenpuffer würde die Level-Rekonstruktion nahezu perfekt und trivial machen. Es hieße aber auch, in Prozesse einzugreifen, die durch Anti-Cheat geschützt sein können, was das Konto jedes Nutzers riskiert. Deshalb wird die Tiefe stattdessen aus dem Bild *geschätzt* ([Tiefe](reconstruction-depth.md)), und ein großer Teil der Rekonstruktions-Pipeline dient dazu, so viel der verlorenen Genauigkeit wie möglich aus Quellen zurückzuholen, die frei nutzbar sind: Telemetrie-Posen, wo ein Spiel sie veröffentlicht, ein Maßstab über die Bodenebene, wo es das nicht tut, und Masken, die HUD und Cockpit aus der Lösung heraushalten.

Der Tiefenpuffer von ReShade wurde erwogen und nicht genutzt. ReShade sperrt den Tiefenzugriff in Mehrspielersitzungen absichtlich, daher würde er nur Einzelspieler-Titel helfen (siehe [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## Was das Werkzeug auf deinem Rechner ändert, und nur auf Anfrage {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Aktion | Wann | Was genau |
|---|---|---|
| Installiert Python-Pakete | beim ersten Start des Scan-Fensters, nach einem Dialog und einem Ja | `pip install` in den Interpreter, der das Werkzeug ausführt - mit `scan.bat` in die private `.venv` daneben. Nie systemweit von selbst. |
| Konvertiert das Tiefenmodell | Schaltfläche „Set up the depth model“, nach einem zweiten Dialog für PyTorch und Verwandte | schreibt `models/depth-small-518.onnx` |
| Bearbeitet die `config.json` von EA SPORTS WRC | `telemetry --game wrc --configure <file>` | schaltet das Paket `wrc` / `session_update` auf 127.0.0.1; die alte Datei wird als `config.json.bak` aufbewahrt |
| Kopiert den BeamNG-Mod | `telemetry --game beamng --install` | `mods/beamng/heat3d` nach `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (ersetzt eine ältere Kopie) |
| Kopiert das Trackmania-Plugin | `telemetry --game trackmania --install` | `mods/trackmania/Heat3dRecorder` nach `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (ersetzt eine ältere Kopie) |
| Registriert globale Tastenkürzel | solange das Scan-Fenster offen ist (Windows) | Strg+Alt+F9 / F10 / F11, freigegeben, wenn das Fenster schließt |
| Aktualisiert das Werkzeug | nachdem du der Update-Abfrage zugestimmt hast, oder bei `python -m heat3d_update` | siehe [Aktualisierungen](updates.md) |

Die `hardware_settings_config.xml` der DiRT-Spiele und die `RichardBurnsRally.ini` von Richard Burns Rally werden vom Werkzeug **nicht** bearbeitet; du schaltest ihre UDP-Ausgabe selbst ein (siehe [Rally-Spiele](telemetry-rally.md)).

## Was in der Verantwortung des Nutzers bleibt {#what-stays-the-users-responsibility}

Worauf ein Nutzer die Werkzeuge richtet, unterliegt weiterhin der Lizenz und der EULA des Spiels. Rundendateien, Aufnahmen, Rekonstruktionen und exportierte Strecken gehören dem, dem das Spiel und die Daten gehören; die `.gitignore` des Repositorys hält Aufnahmen, Rundendateien, Netze, Modellgewichte und Videos nach Ordner und Dateityp aus der Versionskontrolle heraus.
