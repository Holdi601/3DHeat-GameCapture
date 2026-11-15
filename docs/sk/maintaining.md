---
title: "Správa týchto dokumentov"
nav_order: 96
lang: "sk"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Správa týchto dokumentov {#maintaining-these-docs}

Kontrolný zoznam pre každé vydanie, aby kód, anglické stránky a ich preklady zostali v súlade.
Kroky robte v poradí.

1. **Znovu vygenerujte vygenerované stránky.**
   - `python tools/gen_docs_reference.py` prepíše [Referencia príkazov](../cli-reference.md) z
     `--help` a zo zoznamov stĺpcov v kóde. `--check` skončí s kódom 1, keď je stránka zastaraná:
     spustite ho pred každým vydaním.
   - `python tools/docs_diagrams.py` prekreslí diagramy v `docs/assets/img/`; `--strings` tiež
     obnoví `docs/assets/i18n/en.json`, teda štítky na preklad.
   - `python tools/sync_wiki.py` znovu vytvorí kópiu wiki na GitHube v `docs/wiki/`.
2. **Zapíšte, čo sa zmenilo od posledného vydania.** `git log --oneline v$(cat VERSION)..` (posledná
   značka je `v` + verzia v `VERSION`). Pri každom novom alebo zmenenom príkaze, prepínači,
   stĺpci výstupu alebo správaní: upravte jeho stránku a pridajte riadok do tabuľky *Docs* v
   `CHANGELOG.md`.
3. **Nezávislá kontrola.** Niekto, kto zmenu nenapísal, prečíta zmenené stránky a diagramy ako tri
   čitatelia: **začiatočník** (nikdy nepoužil príkazový riadok: dokáže nainštalovať a spustiť
   nástroj?), **osemročné dieťa** (hovorí stránka jednoduchými slovami, čo to je a prečo?) a
   **profesionál** (sedia prepínače, predvolené hodnoty a stĺpce s kódom?). Skontrolujte, že
   žiadna stránka nepomenúva skutočné levely, mapy, hráčov ani nahrávky: príklady sú syntetické,
   tvrdenia o overení uvádzajú iba metódu a toleranciu.
4. **Opravte zistenia.**
5. **Preložte.** Každá preložená stránka zaznamená hash anglickej stránky, z ktorej vznikla.
   Znovu preložte stránky, ktorých hash zdrojového anglického textu sa zmenil, a štítky diagramov,
   ktoré sa zmenili; potom skontrolujte každý jazyk: zrozumiteľnosť pre tri čitatelia, správne
   štítky diagramov, slová zodpovedajúce lokalizovanému rozhraniu prehliadača.
6. **Odošlite len so súhlasom vlastníka.** Potom označte vydanie `v<VERSION>`.

Ak ešte nepoznáte tieto príkazy? [Predtým ako začnete](before-you-start.md) vysvetľuje Python a
terminál.

## Preklady: príkazy {#translations-the-commands}

Stránky sú preložené do 40 jazykov prehliadača 3DHeat: angličtina je v `docs/`, každý ďalší jazyk
v `docs/<lang>/` s rovnakými názvami súborov. `tools/docs_i18n.py` vedie evidenciu:

```bash
python tools/docs_i18n.py hashes             # po každej zmene v angličtine: zapíše hash každej stránky
python tools/docs_i18n.py svg-strings        # po každej zmene obrázka: štítky na preklad
python tools/docs_i18n.py status             # pre každý jazyk: aktuálne, zastarané, chýbajúce stránky
python tools/docs_i18n.py todo --lang de     # nemecké stránky na (znovu)preloženie
python tools/docs_i18n.py svg-build --lang de    # nemecké obrázky z docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # označí nemecké stránky hashom anglickej verzie
python tools/docs_i18n.py check              # skončí s kódom 1, keď sú hashe alebo štítky zastarané
```

Prekladajte len to, čo vypíše `todo`: Markdown, odkazy, kód, názvy súborov a stĺpcov ponechajte
tak, ako sú; preložte nadpisy a popisy obrázkov a používajte vlastné slová prehliadača 3DHeat pre
jeho tlačidlá a panely (`src/i18n/locales/<lang>/`). Vygenerované referenčné stránky a obrázky
terminálu zostávajú v angličtine. Na stránke zastaraný preklad to povie a odkáže na anglickú
stránku; chýbajúci preklad sa zobrazí v angličtine. Ponuka jazykov v hlavičke a presmerovanie
domovskej stránky podľa jazyka prehliadača sú v `docs/_includes/`.
