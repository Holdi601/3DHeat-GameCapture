---
title: ".glb úttakið"
nav_order: 6
lang: "is"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# .glb úttakið {#the-glb-output}

Endurbygging er skrifuð sem tvíundar glTF 2.0 skrá (`.glb`) sem 3DHeat-skoðarinn hleður
í gegnum spjaldið Bakgrunnur / borð án sérstakrar meðhöndlunar - sami samningur og Unreal-útflytjandinn
skrifar. Kóði: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Hún er skrifuð í höndunum en ekki með glTF-safni: úttakið er þröng undirmenga (einn
biðminni, þétt pakkaður, engin hreyfimynd, engin beinagrind) og ósjálfstæði sem getur skrifað allt glTF
myndi draga með sér útgáfuósamræmi fyrir nokkur hundruð línur af kóða.

## Hvað er í skrá skönnunar {#what-is-in-a-scans-file}

| Hluti (heiti hnúts og nets) | Innihald |
|---|---|
| `ground:<name>` | þríhyrningar innan við 35 gráður frá því að snúa upp |
| `structure:<name>` | allt annað |

`<name>` er skráarheitið án endingar þegar vistað er úr glugganum, eða heiti myndbandsins
fyrir `reconstruct`. Hluti án þríhyrninga er felldur niður. Enginn `water:` hluti er nokkurn tíma skrifaður af
skönnun. `asset.generator` er `heat3d-capture-scan`.

## Samningurinn {#the-contract}

- **Einn hnútur fyrir hvern hluta**, nefndur með merki hlutans; netið endurtekur heitið. Skoðarinn
  les *hnútsheitið* fyrst, svo ef aðeins net væru nefnd færi flokkunin forgörðum.
- Merkið er `<class>:<name>` með flokknum `ground`, `structure` eða `water` - forskeytið sem
  skoðarinn leitar að (`^(ground|structure|water)\s*[:|]`) til að taka flokkinn trúanlegan í stað þess að
  giska út frá rúmfræðinni. Jörð er teiknuð heil, mannvirki næstum gegnsæ.
- **Hnit eru í rúmi skoðarans**: Y upp, hægrihandar, og **kvarðað í sentímetra** (metrar x
  100) til að samsvara Unreal-útflytjandanum, svo upptaka og vélarútflutningur af sama stað hlaðast
  í sömu stærð með sömu sjálfgefnu myndavélarstillingum. `extras.unit_metres` á efsta stigi skrárinnar er `0.01`
  (ein eining er sentímetri), svo lesandi sem vinnur í metrum, eins og [`locate`](locate.md), tekur
  hana í sinni réttu stærð. Skönnun sem er staðsett með Forza mælingagögnum er undantekningin
  hvað handhverfu varðar: hún helst í heimi leiksins sjálfs, Y upp og vinstrihandar, nákvæmlega eins og hringskrárnar
  eru, svo að hringirnir sem skráðir eru yfir henni lenda á henni. Þegar kvarði skönnunar fannst á síðari lykilramma
  ([Kvarði](reconstruction-pose.md#scale)), er sá stuðull felldur inn í kvarðann sem er skrifaður.
- `COLOR_0` er lesinn af skoðaranum, sem skyggir jörðina með honum þegar rofinn *Skráður litur* á spjaldinu Bakgrunnur / borð
  er á (slökktur sjálfgefið).
- Skönnun með blettum merktum í höndunum fær `<name>.marks.json` við hlið sér; sjá
  [Vistun](reconstruction-scan-ui.md#saving).
- Fyrir hverja frumeind (primitive): `POSITION` (float VEC3, með `min` og `max`, sem skoðarinn rammar myndavélina
  inn eftir), `NORMAL` (float VEC3), valfrjálst `COLOR_0` (float VEC3, 0..1), valfrjálst `TEXCOORD_0`;
  vísar sem 16 bita þegar hver vísir er undir 65.536, annars 32 bita; hamur þríhyrningar.
- Sérhver biðminnissýn byrjar 4 bæta samstillt; JSON-hlutinn er fylltur með bilum og BIN-hlutinn
  með núllum upp í 4 bæti.

## Athuganir áður en skrifað er {#checks-before-writing}

Sérhver hluti er sannprófaður og hafnað með skilaboðum sem nefna hann þegar hann hefur enga hnúta, vísafjöldi
sem er ekki heilir þríhyrningar, vísir utan marka eða neikvæður, óendanlegar stöður, eða
normölum eða litum sem passa ekki við fjölda hnúta. Normalar eru reiknaðir þegar þá vantar,
**vegnir eftir flatarmáli** (marching cubes skilur eftir flísar við hlið stórra flata, og óvegið meðaltal
lætur örsmáa þríhyrninga yfirgnæfa flötinn sem þeir sitja á); úrkynjaður hnútur fær „upp“. Að skrifa enga
hluta er villa.

Útflutningur skilar engu - og glugginn segir „Nothing to save“ - þegar rúmmálið gefur ekkert
yfirborð, frekar en að skrifa tóma skrá sem liti út eins og vel heppnuð skönnun.

## Áferðir {#textures}

Skrifarinn styður PNG grunnlitaáferð fyrir hvern hluta (með UV, tvíhliða, ómálmkennt,
alveg hrjúft efni). Skannanir nota hana ekki; þær bera lit á hvern hnút. Sjá
[lit](reconstruction-fusion-and-texture.md#colour).

## Viðmiðunarborðið {#the-reference-level}

`geometry/reference.py` smíðar tilbúið borð af nákvæmlega þekktri stærð í gegnum sama skrifara:
400 m undirskipta jörð, þrjár 20 x 20 x 12 m byggingar og 50 m tjörn 1,5 m undir jörðu, hver
flokkur í sérstökum sléttum lit. Eigin prófanir skoðarans búa það til og lesa það með
raunverulegum lesara skoðarans, svo skráarsniðið er áfram prófað báðum megin án leiks og án upptökubúnaðar.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
