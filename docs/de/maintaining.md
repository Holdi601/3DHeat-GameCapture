---
title: Diese Dokumentation pflegen
nav_order: 96
lang: "de"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Diese Dokumentation pflegen {#maintaining-these-docs}

Die Checkliste für jedes Release, damit Code, die englischen Seiten und ihre Übersetzungen Schritt halten. Die Schritte der Reihe nach ausführen.

1. **Die erzeugten Seiten neu erzeugen.**
   - `python tools/gen_docs_reference.py` schreibt [Befehlsreferenz](../cli-reference.md) aus `--help` und den Spaltenlisten im Code neu. `--check` endet mit 1, wenn die Seite veraltet ist: vor jedem Release ausführen.
   - `python tools/docs_diagrams.py` zeichnet die Diagramme in `docs/assets/img/` neu; `--strings` aktualisiert außerdem `docs/assets/i18n/en.json`, die Beschriftungen, die übersetzt werden.
   - `python tools/sync_wiki.py` erzeugt die Kopie des GitHub-Wikis in `docs/wiki/` neu.
2. **Auflisten, was sich seit dem letzten Release geändert hat.** `git log --oneline v$(cat VERSION)..` (der letzte Tag ist `v` plus die Version in `VERSION`). Für jeden neuen oder geänderten Befehl, jede Option, jede Ausgabespalte und jedes Verhalten: seine Seite aktualisieren und eine Zeile in die Tabelle *Docs* in `CHANGELOG.md` eintragen.
3. **Unabhängige Prüfung.** Jemand, der die Änderung nicht geschrieben hat, liest die geänderten Seiten und Diagramme aus drei Blickwinkeln: ein **Einsteiger** (hat nie eine Kommandozeile benutzt: kann er es installieren und starten?), ein **Achtjähriger** (sagt die Seite mit einfachen Worten, was es ist und warum?), und ein **Profi** (stimmen Optionen, Voreinstellungen und Spalten mit dem Code überein?). Prüfen, dass keine Seite echte Level, Karten, Spieler oder Aufnahmen nennt: Beispiele sind synthetisch, Prüfaussagen nennen nur Methode und Toleranz.
4. **Die Befunde beheben.**
5. **Übersetzen.** Jede übersetzte Seite speichert den Hash der englischen Seite, aus der sie entstand. Die Seiten neu übersetzen, deren englischer Quell-Hash sich geändert hat, und die geänderten Diagramm-Beschriftungen; danach jede Sprache prüfen: verständlich für die drei Leser, Diagramm-Beschriftungen stimmen, Wörter passen zur lokalisierten Oberfläche des Viewers.
6. **Erst nach dem Ok des Eigentümers pushen.** Danach das Release mit `v<VERSION>` taggen.

Neu bei diesen Befehlen? [Bevor du anfängst](before-you-start.md) erklärt Python und das Terminal.

## Übersetzungen: die Befehle {#translations-the-commands}

Die Seite ist in die 40 Sprachen des 3DHeat-Viewers übersetzt: Englisch in `docs/`, jede andere Sprache in `docs/<lang>/` mit denselben Dateinamen. `tools/docs_i18n.py` führt die Buchhaltung:

```bash
python tools/docs_i18n.py hashes             # nach jeder Änderung am Englischen: den Hash jeder Seite festhalten
python tools/docs_i18n.py svg-strings        # nach jeder Bildänderung: die zu übersetzenden Beschriftungen
python tools/docs_i18n.py status             # pro Sprache: aktuell, veraltet, fehlende Seiten
python tools/docs_i18n.py todo --lang de     # die deutschen Seiten zum (Neu-)Übersetzen
python tools/docs_i18n.py svg-build --lang de    # deutsche Bilder aus docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # die deutschen Seiten mit ihrem englischen Hash stempeln
python tools/docs_i18n.py check              # endet mit 1, wenn Hashes oder Beschriftungen veraltet sind
```

Nur übersetzen, was `todo` auflistet: Markdown, Links, Code, Datei- und Spaltennamen bleiben, wie sie sind; Titel und Bildbeschreibungen werden übersetzt; für Schaltflächen und Felder gelten die eigenen Wörter des 3DHeat-Viewers (`src/i18n/locales/<lang>/`). Erzeugte Referenzseiten und Terminal-Bilder bleiben englisch. Auf der Seite sagt eine veraltete Übersetzung das und verlinkt die englische Seite; eine fehlende fällt auf Englisch zurück. Das Sprachmenü der Kopfzeile und die Weiterleitung der Startseite nach Browsersprache kommen aus `docs/_includes/`.
