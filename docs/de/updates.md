---
title: Aktualisierungen
nav_order: 10
lang: "de"
source: updates.md
source_hash: "a442cf97a5c1"
nav_exclude: true
search_exclude: true
---
# Aktualisierungen {#updates}

3DHeat GameCapture prüft beim Start die GitHub-Releases dieses Repositorys, sagt, wenn eine neuere Version da ist, und bietet an, zu aktualisieren. Code: [`heat3d_update/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_update).

## Wann die Prüfung läuft {#when-the-check-runs}

- `python -m heat3d_capture <verb>` - bevor der Befehl läuft.
- `python -m heat3d_capture.ui` (und `scan.bat`) - bevor das Fenster aufgeht.
- `python -m heat3d_update` - auf Anfrage; fragt GitHub jedes Mal neu.

## So funktioniert die Prüfung {#how-the-check-works}

- Die installierte Version ist die Datei `VERSION` im Wurzelordner des Repositorys (zum Beispiel `1.0.1`).
- Das neueste Release wird unter `https://api.github.com/repos/Holdi601/3DHeat-GameCapture/releases/latest` abgefragt, mit einer Zeitgrenze von **5 Sekunden**. Ein langsames Netz hält das Werkzeug nie länger auf.
- Die Antwort wird **6 Stunden** lang in `%LOCALAPPDATA%\3DHeat\update-check-3DHeat-GameCapture.json` zwischengespeichert (`~/.cache/3DHeat/...` ohne `LOCALAPPDATA`). Jedes 3DHeat-Werkzeug hat seine eigene Cache-Datei. „Noch kein Release“ (HTTP 404) wird wie eine Antwort zwischengespeichert; andere Fehler werden nicht zwischengespeichert und bedeuten einfach keinen Hinweis.
- Versionen werden als Zahlen verglichen (`v1.2.3` oder `1.2.3`; alles nach `-` oder `+` wird ignoriert).
- Offline, bei Ratenbegrenzung oder hinter einem Proxy arbeitet das Werkzeug mit der Version weiter, die es hat.

## Was passiert, wenn ein neueres Release da ist {#what-happens-when-a-newer-release-is-out}

Beim Start gibt es auf den Fehlerkanal aus:

```text
[heat3d_capture] 3DHeat GameCapture 1.1.0 is out (this is 1.0.1). https://github.com/...
```

- Ist ein Terminal zum Antworten da, fragt es `Update now? [Y/n]` (Enter, `y`, `yes`, `j` oder `ja` heißen ja). Nach einem erfolgreichen Update **wird derselbe Befehl erneut gestartet**, mit dem neuen Code.
- Ohne Terminal (eine Pipe, ein geplanter Lauf) gibt es `Run python -m heat3d_update in <folder> to update.` aus und läuft unverändert weiter.

## Wie ein Update angewendet wird {#how-an-update-is-applied}

Das hängt davon ab, wie die Werkzeuge installiert wurden:

- **Ein Git-Klon** (ein `.git`-Ordner und `git` im PATH): `git pull --ff-only`. Wird verweigert, solange die Arbeitskopie lokale Änderungen an verfolgten Dateien hat - das ist die Arbeit von jemandem; zuerst committen oder mit `git stash` sichern.
- **Eine heruntergeladene Kopie**: das Quellarchiv des Releases wird geladen, in einen temporären Ordner entpackt (Einträge außerhalb des eigenen Ordners des Archivs werden übersprungen) und **geprüft, ob es die Version ist, die es behauptet**, anhand seiner Datei `VERSION`. Dann werden seine Dateien über diesen Ordner kopiert. Innerhalb der eigenen Python-Pakete des Releases (`heat3d_*`-Ordner oben im Repository und eine Ebene tiefer für das alte Monorepo-Layout) werden `.py`-Module gelöscht, die das Release nicht mehr hat, damit ein veraltetes Modul seinen Ersatz nicht verdecken kann.

Deine eigenen Dateien - Aufnahmen, Rundendateien, Einstellungen, Exporte, die `.venv` - werden nie angefasst: Es werden nur Dateien geschrieben, die zum Release gehören.

## Von Hand {#by-hand}

```bash
python -m heat3d_update            # prüfen und aktualisieren
python -m heat3d_update --check    # nur sagen, ob ein neueres Release da ist
```

Es gibt `Up to date: <version>.`, `No release found ... offline, or nothing published yet.` aus oder die neue Version und was es getan hat. Exitcode 1, wenn das Update nicht angewendet werden konnte.

## Ausschalten {#switching-it-off}

Setze **`HEAT3D_NO_UPDATE=1`** (jeder Wert außer leer, `0`, `false`, `no`). Das schaltet die Prüfung und den Hinweis beim Start ab. `python -m heat3d_update` selbst prüft weiterhin, wenn man es von Hand startet.
