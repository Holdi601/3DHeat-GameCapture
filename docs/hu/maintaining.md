---
title: A dokumentáció karbantartása
nav_order: 96
lang: "hu"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# A dokumentáció karbantartása {#maintaining-these-docs}

Minden kiadás ellenőrzőlistája, hogy a kód, az angol oldalak és a fordítások összhangban maradjanak.
A lépéseket sorrendben végezze.

1. **Generálja újra a generált oldalakat.**
   - `python tools/gen_docs_reference.py` újraírja a [Parancsreferenciát](../cli-reference.md) a `--help`
     és a kódban lévő oszlopok alapján. A `--check` 1-es kóddal lép ki, ha az oldal elavult: minden kiadás
     előtt futtassa.
   - `python tools/docs_diagrams.py` újrarajzolja a diagramokat a `docs/assets/img/` mappában;
     a `--strings` a `docs/assets/i18n/en.json` fájlt is frissíti, azaz a lefordítandó címkéket.
   - `python tools/sync_wiki.py` újragenerálja a GitHub-wiki másolatát a `docs/wiki/` mappában.
2. **Sorolja fel, mi változott az utolsó kiadás óta.** `git log --oneline v$(cat VERSION)..` (az utolsó
   címke `v` + a `VERSION`-ben lévő verzió). Minden új vagy megváltozott parancsnál, kapcsolónál, kimeneti
   oszlopnál vagy viselkedésnél frissítse az oldalát, és vegyen fel egy sort a `CHANGELOG.md` *Docs* táblázatába.
3. **Független átnézés.** Valaki, aki nem írta a változtatást, végigolvassa a megváltozott oldalakat és
   diagramokat három olvasóként: egy **kezdő** (soha nem használt parancssort: telepíteni és futtatni tudja?),
   egy **8 éves** (az oldal egyszerű szavakkal elmondja, mi ez és miért?), és egy **profi** (az opciók,
   alapértékek és oszlopok egyeznek a kóddal?). Ellenőrizze, hogy egy oldal sem nevez meg valódi pályákat,
   térképeket, játékosokat vagy felvételeket: a példák szintetikusak, az ellenőrzési állítások csak a módszert
   és a tűrést adják meg.
4. **Javítsa a megállapításokat.**
5. **Fordítsa le.** Minden lefordított oldal rögzíti annak az angol oldalnak a hash-ét, amelyből készült.
   Fordítsa újra azokat az oldalakat, amelyek angol forrásának hash-e megváltozott, valamint a megváltozott
   diagramcímkéket; majd nyelvenként nézze át: érthető-e a három olvasónak, jók-e a diagramcímkék, és a szavak
   egyeznek-e a megjelenítő lokalizált felületével.
6. **Csak a tulajdonos jóváhagyása után töltsön fel.** Utána jelölje meg a kiadást `v<VERSION>` címkével.

Ha most ismerkedik ezekkel a parancsokkal, a [Mielőtt elkezdi](before-you-start.md) oldal a Pythont és a
parancssort magyarázza el.

## Fordítások: a parancsok {#translations-the-commands}

Az oldal a 3DHeat megjelenítő 40 nyelvére fordított: az angol a `docs/` mappában van, minden más nyelv a
`docs/<lang>/` mappában, ugyanazokkal a fájlnevekkel. A `tools/docs_i18n.py` végzi a nyilvántartást:

```bash
python tools/docs_i18n.py hashes             # angol változtatás után: minden oldal hash-ének rögzítése
python tools/docs_i18n.py svg-strings        # képváltozás után: a lefordítandó címkék
python tools/docs_i18n.py status             # nyelvenként: naprakész, elavult, hiányzó oldalak
python tools/docs_i18n.py todo --lang de     # a német oldalak, amelyeket (újra) le kell fordítani
python tools/docs_i18n.py svg-build --lang de    # német képek a docs/assets/i18n/svg/de.json alapján
python tools/docs_i18n.py finish --lang de   # a német oldalak megjelölése az angol hash-sel
python tools/docs_i18n.py check              # 1-es kóddal lép ki, ha a hash-ek vagy címkék elavultak
```

Csak azt fordítsa, amit a `todo` felsorol: a Markdownt, a linkeket, a kódot, a fájl- és oszlopneveket
hagyja, ahogy vannak; a címeket és a képleírásokat fordítsa; a megjelenítő gombjaihoz és paneljeihez a
megjelenítő saját szavait használja (`src/i18n/locales/<lang>/`). A generált referenciaoldalak és a
terminálképek angolok maradnak. A honlapon az elavult fordítás ezt jelzi, és az angol oldalra mutat; a
hiányzó fordítás angolra esik vissza. A fejléc nyelvi menüjét és a főoldal böngészőnyelv-átirányítását a
`docs/_includes/` adja.
