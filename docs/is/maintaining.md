---
title: "Viðhald þessara skjala"
nav_order: 96
lang: "is"
source: maintaining.md
source_hash: "ab9167bccf3a"
nav_exclude: true
search_exclude: true
---
# Viðhald þessara skjala {#maintaining-these-docs}

Gátlistinn fyrir hverja útgáfu, svo að kóðinn, ensku síðurnar og þýðingar þeirra haldist í takt. Gerðu skrefin í réttri röð.

1. **Búðu til sjálfvirku síðurnar upp á nýtt.**
   - `python tools/gen_docs_reference.py` endurskrifar [Skipanayfirlit](../cli-reference.md) úr
     `--help` og dálkalistunum í kóðanum. `--check` hættir með kóða 1 þegar síðan er úrelt: keyrðu hana
     fyrir hverja útgáfu.
   - `python tools/docs_diagrams.py` teiknar skýringarmyndirnar í `docs/assets/img/` upp á nýtt;
     `--strings` uppfærir líka `docs/assets/i18n/en.json`, textana sem á að þýða.
   - `python tools/sync_wiki.py` býr afrit GitHub wiki-sins í `docs/wiki/` til upp á nýtt.
2. **Taktu saman hvað breyttist frá síðustu útgáfu.** `git log --oneline v$(cat VERSION)..` (síðasta
   merkið er `v` + útgáfan í `VERSION`). Fyrir hverja nýja eða breytta skipun, valkost, úttaksdálk
   eða hegðun: uppfærðu síðuna hennar og bættu línu við *Docs* töfluna í `CHANGELOG.md`.
3. **Óháð yfirferð.** Einhver sem skrifaði ekki breytinguna les breyttu síðurnar og skýringarmyndirnar
   sem þrír lesendur: **byrjandi** (hefur aldrei notað skipanalínu: getur hann sett upp og keyrt
   það?), **8 ára barn** (segir síðan með einföldum orðum hvað þetta er og hvers vegna?) og **fagmaður**
   (passa valkostir, sjálfgildi og dálkar við kóðann?). Athugaðu að engin síða nefni raunveruleg borð,
   kort, spilara eða upptökur: dæmi eru tilbúin, og fullyrðingar um sannprófun gefa aðeins aðferðina og
   vikmörkin.
4. **Lagaðu niðurstöðurnar.**
5. **Þýddu.** Hver þýdd síða geymir kjötkássu (hash) ensku síðunnar sem hún var gerð úr.
   Þýddu aftur síðurnar þar sem kjötkássa enska frumtextans breyttist, og textana í skýringarmyndunum sem breyttust;
   yfirfarðu síðan hvert tungumál: skýrt fyrir lesendurna þrjá, textar á skýringarmyndum réttir, orð í samræmi við
   staðfært viðmót skoðarans.
6. **Ýttu aðeins eftir að eigandinn hefur gefið grænt ljós.** Merktu svo útgáfuna `v<VERSION>`.

Ertu nýr í að keyra þessar skipanir? [Áður en þú byrjar](before-you-start.md) fjallar um Python og
skipanalínuna.

## Þýðingar: skipanirnar {#translations-the-commands}

Vefurinn er þýddur á 40 tungumál 3DHeat-skoðarans: enska í `docs/`, hvert annað
tungumál í `docs/<lang>/` með sömu skráarheitum. `tools/docs_i18n.py` sér um bókhaldið:

```bash
python tools/docs_i18n.py hashes             # after any English change: record each page's hash
python tools/docs_i18n.py svg-strings        # after any picture change: the labels to translate
python tools/docs_i18n.py status             # per language: current, outdated, missing pages
python tools/docs_i18n.py todo --lang de     # the German pages to (re)translate
python tools/docs_i18n.py svg-build --lang de    # German pictures from docs/assets/i18n/svg/de.json
python tools/docs_i18n.py finish --lang de   # stamp the German pages with their English hash
python tools/docs_i18n.py check              # exit 1 when hashes or labels are stale
```

Þýddu aðeins það sem `todo` listar: haltu Markdown, tenglum, kóða, skráar- og dálkaheitum eins og þau eru,
þýddu titla og myndlýsingar, og notaðu orð 3DHeat-skoðarans sjálfs fyrir hnappa hans
og spjöld (`src/i18n/locales/<lang>/` hans). Sjálfvirkar tilvísunarsíður og skjámyndir úr skipanalínu haldast á
ensku. Á vefnum segir úrelt þýðing til um það og tengir á ensku síðuna; vantandi þýðing
fellur aftur á ensku. Tungumálavalmynd haussins og tilvísun heimasíðunnar eftir tungumáli vafrans
koma úr `docs/_includes/`.
