---
title: Deze documentatie bijhouden
nav_order: 96
lang: "nl"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Deze documentatie bijhouden {#maintaining-these-docs}

De checklist voor elke release, zodat de code, de Engelse pagina's en hun vertalingen gelijk blijven. Doe de stappen in volgorde.

1. **Genereer de gegenereerde pagina's opnieuw.**
   - `python tools/gen_docs_reference.py` schrijft de [Opdrachtreferentie](../cli-reference.md) opnieuw vanuit `--help` en de kolomlijsten in de code. `--check` eindigt met 1 wanneer de pagina verouderd is: draai dit voor elke release.
   - `python tools/docs_diagrams.py` tekent de diagrammen in `docs/assets/img/` opnieuw; `--strings` ververst ook `docs/assets/i18n/en.json`, de labels om te vertalen.
   - `python tools/sync_wiki.py` maakt de kopie van de GitHub-wiki in `docs/wiki/` opnieuw.
2. **Zet op een rij wat er sinds de vorige release is veranderd.** `git log --oneline v$(cat VERSION)..` (de laatste tag is `v` + de versie in `VERSION`). Voor elke nieuwe of gewijzigde opdracht, optie, uitvoerkolom of gedraging: werk de pagina bij en voeg een rij toe aan de tabel *Docs* in `CHANGELOG.md`.
3. **Onafhankelijke controle.** Iemand die de wijziging niet heeft geschreven, leest de gewijzigde pagina's en diagrammen als drie lezers: een **beginner** (heeft nog nooit een opdrachtregel gebruikt: kan die het installeren en draaien?), een **8-jarige** (zegt de pagina in gewone woorden wat het is en waarom?), en een **pro** (komen de opties, standaardwaarden en kolommen overeen met de code?). Controleer dat geen enkele pagina echte levels, maps, spelers of opnames noemt: voorbeelden zijn synthetisch, en verificatieclaims geven alleen de methode en de tolerantie.
4. **Verhelp de bevindingen.**
5. **Vertaal.** Elke vertaalde pagina houdt de hash bij van de Engelse pagina waarvan ze is gemaakt. Vertaal de pagina's opnieuw waarvan de Engelse bronhash is veranderd, en de diagramlabels die zijn veranderd; controleer daarna elke taal: duidelijk voor de drie lezers, diagramlabels kloppen, woorden passen bij de gelokaliseerde interface van de viewer.
6. **Pas pushen na het akkoord van de eigenaar.** Zet daarna de tag `v<VERSION>` op de release.

Nieuw in het draaien van deze opdrachten? [Voordat je begint](before-you-start.md) behandelt Python en de terminal.

## Vertalingen: de opdrachten {#translations-the-commands}

De site is vertaald in de 40 talen van de 3DHeat-viewer: Engels in `docs/`, elke andere taal in `docs/<lang>/` met dezelfde bestandsnamen. `tools/docs_i18n.py` houdt de administratie bij:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Vertaal alleen wat `todo` vermeldt: laat Markdown, links, code, bestands- en kolomnamen zoals ze zijn, vertaal titels en beschrijvingen van afbeeldingen, en gebruik de eigen woorden van de 3DHeat-viewer voor zijn knoppen en panelen (de map `src/i18n/locales/<lang>/`). Gegenereerde referentiepagina's en terminalafbeeldingen blijven Engels. Op de site zegt een verouderde vertaling dat en linkt naar de Engelse pagina; ontbreekt een vertaling, dan valt de site terug op Engels. Het taalmenu in de koptekst en de doorverwijzing op basis van de browsertaal van de startpagina komen uit `docs/_includes/`.
