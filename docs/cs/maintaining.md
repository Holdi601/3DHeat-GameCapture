---
title: Údržba těchto dokumentů
nav_order: 96
lang: "cs"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Údržba těchto dokumentů {#maintaining-these-docs}

Kontrolní seznam pro každé vydání, aby kód, anglické stránky a jejich překlady zůstaly v souladu. Kroky dělejte v pořadí.

1. **Znovu vygenerujte generované stránky.**
   - `python tools/gen_docs_reference.py` přepíše [Referenci příkazů](../cli-reference.md) z `--help` a ze seznamů sloupců v kódu. `--check` skončí s kódem 1, když je stránka zastaralá: spusťte ho před každým vydáním.
   - `python tools/docs_diagrams.py` překreslí diagramy v `docs/assets/img/`; `--strings` také obnoví `docs/assets/i18n/en.json`, popisky k překladu.
   - `python tools/sync_wiki.py` znovu vytvoří kopii wiki na GitHubu v `docs/wiki/`.
2. **Vypište, co se změnilo od posledního vydání.** `git log --oneline v$(cat VERSION)..` (poslední značka je `v` + verze v `VERSION`). Pro každý nový nebo změněný příkaz, volbu, sloupec výstupu nebo chování: aktualizujte jeho stránku a přidejte řádek do tabulky *Docs* v `CHANGELOG.md`.
3. **Nezávislá kontrola.** Někdo, kdo změnu nenapsal, přečte změněné stránky a diagramy třemi čtenáři: **začátečník** (nikdy nepoužil příkazový řádek: dokáže nainstalovat a spustit?), **osmiletý čtenář** (říká stránka prostými slovy, co to je a proč?) a **profesionál** (sedí volby, výchozí hodnoty a sloupce s kódem?). Zkontrolujte, že žádná stránka nejmenuje skutečné úrovně, mapy, hráče ani záznamy. Příklady jsou syntetické a tvrzení o ověření uvádějí jen metodu a toleranci.
4. **Opravte nálezy.**
5. **Přeložte.** Každá přeložená stránka si zapamatuje hash anglické stránky, ze které vznikla. Znovu přeložte stránky, jejichž anglický zdroj se změnil, a popisky diagramů, které se změnily. Pak zkontrolujte každý jazyk: jasné pro všechny tři čtenáře, správné popisky diagramů, slova odpovídající lokalizovanému rozhraní prohlížeče.
6. **Odevzdávejte jen se souhlasem vlastníka.** Pak označte vydání `v<VERSION>`.

Ještě jste nepracovali s těmito příkazy? [Než začnete](before-you-start.md) vysvětluje Python a terminál.

## Překlady: příkazy {#translations-the-commands}

Web se překládá do 40 jazyků prohlížeče 3DHeat: angličtina je v `docs/`, každý další jazyk v `docs/<lang>/` se stejnými názvy souborů. `tools/docs_i18n.py` vede evidenci:

```bash
python tools/docs_i18n.py hashes             # po každé změně angličtiny: zapíše hash každé stránky
python tools/docs_i18n.py svg-strings        # po každé změně obrázku: popisky k překladu
python tools/docs_i18n.py status             # pro každý jazyk: aktuální, zastaralé a chybějící stránky
python tools/docs_i18n.py todo --lang de     # německé stránky k (novému) překladu
python tools/docs_i18n.py svg-build --lang de    # německé obrázky z docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # označí německé stránky hashem anglické verze
python tools/docs_i18n.py check              # skončí s kódem 1, když jsou hashe nebo popisky zastaralé
```

Překládejte jen to, co vypíše `todo`. Markdown, odkazy, kód, názvy souborů a sloupců ponechte beze změny, překládejte nadpisy a popisy obrázků a pro tlačítka a panely používejte vlastní slova prohlížeče 3DHeat (jeho `src/i18n/locales/<lang>/`). Generované referenční stránky a obrázky terminálu zůstávají anglicky. Na webu zastaralý překlad to řekne a odkáže na anglickou stránku; chybějící se vrátí k angličtině. Nabídka jazyků v záhlaví a přesměrování na úvodní stránku podle jazyka prohlížeče pocházejí z `docs/_includes/`.
