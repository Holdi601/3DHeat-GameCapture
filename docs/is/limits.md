---
title: "Takmarkanir og sannprófun"
nav_order: 9
lang: "is"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Takmarkanir og hvað er sannprófað {#limits-and-what-is-verified}

Heiðarlegur listi: hvað verkfærin gera ekki og hvað hefur ekki verið prófað gegn leik sem er í gangi.

## Mælingagögn {#telemetry}

| Upptökutæki | Staða |
|---|---|
| Forza | Byggt á opinberu Data Out skjölunum; uppsetningin er greind út frá pökkunum sjálfum. `.tele.gz` lesari FH Companion í skoðaranum hefur verið prófaður á raunverulegum hringjum. |
| AC, ACC, AC EVO, AC Rally | Prófað á gervisíðum sem eru smíðaðar eftir útgefnum uppsetningum. **Ekki enn keyrt gegn raunverulegum leikjum.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Prófað á pökkum sem eru smíðaðir eftir skjalfestum uppsetningum. **Ekki enn keyrt gegn raunverulegum leikjum.** Ásar, halli og hraðaeiningar í RBR eru óskjalfest og eru meðhöndluð út frá gögnunum. |
| BeamNG.drive | Upptökutækið er prófað á pökkum sem eru smíðaðir eftir struct viðbótarinnar. **Viðbótin hefur ekki verið keyrð í leiknum.** |
| Trackmania | Lesari skoðarans fyrir CSV er prófaður. **Viðbótin hefur ekki verið keyrð í leiknum.** Hún hleðst aðeins í þróunarham Openplanet. |
| iRacing | `.ibt` lesari skoðarans er prófaður á gerviskrá. |

Aðrar takmarkanir mælingagagna:

- Stöðlun Forza á rennsli er óskjalfest; rennsli Kunos er skalað með dæmigerðu hámarki á malbiki, sem er
  nálgun.
- Stefna sumra hliðarása í bílrammanum (Kunos, DiRT) er skjalfest á báða vegu; stærð
  rekhornsins er áreiðanleg, formerki þess ekki.
- Enginn rallýleikjanna sendir hjólbarðarennsli; það er reiknað í skoðaranum. RBR sendir engan hjólahraða.
- Yfirborð rallýleiðar er aðeins skrifað þegar `--surface` er gefið; annars nefnir skráin
  ekkert og skoðarinn ályktar það (heiti leiðar eða viðburðar, síðan akstursstíll, laust undirlag sjálfgefið).
- Hringgreining án hringateljara (AC EVO, AC Rally, BeamNG) notar staðinn þar sem upptakan
  hófst sem marklínu, svo byrjaðu upptökuna á ráslínunni.
- Endurstilling ökutækis í BeamNG lokar hringnum sem er opinn á þeirri stundu: hann er skrifaður sem hlutakeyrsla
  ef hann náði lágmarksvegalengd (300 m), annars er honum hent.
- `route` vistar á um það bil 2 sekúndna fresti meðan ekið er; hrun eða drepið ferli tapar í mesta lagi
  stöðunum frá síðustu vistun.
- Forza Horizon sendir ekkert brautarheiti, svo Forza hringskrár hafa `"track": null`; Forza Motorsport
  (2023) sendir aðeins tölu, sem er geymd sem `lap.trackOrdinal`.

## Endurgerð {#reconstruction}

- **Dýpt er áætluð, ekki lesin.** Þak allrar aðferðarinnar og verðið fyrir að snerta aldrei
  leikferlið.
- **Sjónsvið er gefið sér, ekki mælt.** Sé það of þröngt endurgerist borðið dýpra en það
  er.
- **Heildarkvarði** kemur frá gefinni myndavélarhæð (1,15 m í glugganum) eða frá
  mælingagögnum. Hann er mældur á fyrsta lykilramma; ef hann hefur ekkert nothæft undirlag eru næstu
  lykilrammar reyndir (allt að 30 rammar), og kvarði sem finnst síðar er notaður á allt borðið
  þegar það er skrifað. Línan „Size:“ í glugganum segir hvað gerðist; ef ekkert undirlag finnst
  er skönnunin áfram án eininga. Þá er teningastærðin í einingum fyrsta rammans, svo stærð hennar
  í metrum er önnur en stillingin. Endurgerðir án nettengingar eru í eigin einingum lausnarinnar.
- **Lokun lykkju er slökkt** og er ekki „pose graph“ þegar kveikt er á henni í kóða; rek er aðeins takmarkað
  af gæðum rakningar á milli ramma.
- **Gluggað búntjöfnun (bundle adjustment) er til en er ekki tengd inn**; hún hrundi á raunverulegu myndefni.
- **Yfirborðið er vegin umráð, ekki TSDF**: þunn mannvirki og laust rými koma verr út en
  með TSDF.
- **Enginn áferðaratlas.** Litur er á hvert hornpunkt (`COLOR_0`), blandaður úr 4 bestu sjónarhornunum af
  160 geymdum römmum. Skyggnipróf er gróft: það prófar gegn eigin hornpunktum netsins í
  dýptarbuffa upp á 2 punkta, svo hlutur sem skyggir og netið inniheldur ekki (bíll sem ekur fram hjá) er ekki gripinn.
- **Vatn er aldrei merkt**; allt er undirlag eða mannvirki.
- **Framvirk lausn (feed-forward) er ekki í beinni**: hún þarfnast upptökunnar fyrst. Aðlögunarhæf endurlausn
  erfiðra kafla er ekki smíðuð.
- **Stöður úr mælingagögnum** setja myndavélina við bílinn (frávik eltimyndavélar er óþekkt). Staðsetningar
  eru teknar eins og Forza sendir þær (Y upp, eins og í hringskránum); stefna snúnings (yaw), hallahorns (pitch) og veltu (roll)
  var lesin af upptekinum hringjum (akstursstefna, halli, hvorrar hliðar fjöðrun þjappast),
  ekki af myndavél leiksins í gangi.
- Yfirlagið getur ekki teiknað yfir **sérhæfðan heilskjá (exclusive fullscreen)**; notaðu gluggaham án ramma (borderless windowed).
- Altækir flýtilyklar, yfirlag sem smellur fara í gegnum og bein upptaka eru **aðeins fyrir Windows**.
- Þegar glugganum er lokað er ekki boðið að vista.

## Hvað er mælt {#what-is-measured}

- `tests/test_accuracy.py`: gerviherbergi með þekktum vegi og greinanlegri dýpt - rammar settir,
  skekkja vegarins, gengin vegalengd, stærð herbergis, yfirborð á veggjunum ([Endurgerð borðs](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: vegur með þekktri breidd, ekinn utan miðju, endurgerir breidd sína.
- `tests/test_track_scale.py`: yfirborðsvinnsla í kvarða kappakstursbrautar, minni í réttu hlutfalli við það sem
  var skannað, kubbar sem sameinast í eitt yfirborð.
- `tests/test_glb.py` ásamt prófum skoðarans sjálfs: `.glb` samningurinn frá báðum hliðum.
- Hvernig dýptarnetið stendur sig í raunverulegum leik getur gerviatriði ekki svarað, og
  það er ekki mælt af prófasafninu.
