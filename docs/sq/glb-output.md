---
title: "Dalja .glb"
nav_order: 6
lang: "sq"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Dalja .glb {#the-glb-output}

Një rindërtim shkruhet si skedar binar glTF 2.0 (`.glb`) që shikuesi 3DHeat e ngarkon
përmes panelit të tij Sfondi / niveli pa asnjë trajtim të veçantë - e njëjta kontratë që shkruan
eksportuesi i Unreal. Kodi: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Shkruhet me dorë dhe jo përmes një biblioteke glTF: dalja është një nënbashkësi e ngushtë (një
bufer, i paketuar fort, pa animacion, pa skinning) dhe një varësi që di të shkruajë gjithë glTF
do të sillte mospërputhjen e versioneve për disa qindra rreshta.

## Çfarë ka në skedarin e një skanimi {#what-is-in-a-scans-file}

| Pjesa (emri i nyjës dhe i rrjetës) | Përmbajtja |
|---|---|
| `ground:<name>` | trekëndëshat që shikojnë lart brenda 35 gradëve |
| `structure:<name>` | gjithçka tjetër |

`<name>` është emri i skedarit pa shtesë kur ruhet nga dritarja, ose emri i videos
për `reconstruct`. Një pjesë pa trekëndësha lihet jashtë. Asnjë pjesë `water:` nuk shkruhet
kurrë nga një skanim. `asset.generator` është `heat3d-capture-scan`.

## Kontrata {#the-contract}

- **Një nyjë për çdo pjesë**, e emërtuar me etiketën e pjesës; rrjeta e përsërit emrin. Shikuesi
  e lexon fillimisht emrin e *nyjës*, ndaj emërtimi vetëm i rrjetave do ta humbiste klasifikimin.
- Etiketa është `<class>:<name>` me klasë `ground`, `structure` ose `water` - parashtesa që
  shikuesi e kërkon (`^(ground|structure|water)\s*[:|]`) për ta marrë klasën sipas fjalës në vend që
  ta hamendësojë nga gjeometria. Toka vizatohet e plotë, strukturat pothuajse të tejdukshme.
- **Koordinatat janë në hapësirën e shikuesit**: Y lart, dore e djathtë, dhe **në shkallë centimetrash** (metra x
  100) për t'u përputhur me eksportuesin e Unreal, ndaj një kapje dhe një eksport i motorit i të njëjtit vend ngarkohen
  me të njëjtën madhësi dhe me të njëjtat parazgjedhje të kamerës. `extras.unit_metres` në nivelin e lartë të skedarit është `0.01`
  (një njësi është një centimetër), ndaj një lexues që punon në metra, si [`locate`](locate.md), e merr
  në madhësinë e vet të vërtetë. Një skanim i vendosur nga telemetria e Forzës është përjashtimi
  në orientim: mbetet në botën e vetë lojës, Y lart dhe dore e majtë, saktësisht si skedarët e xhirave,
  që xhirat e regjistruara mbi të të bien mbi të. Kur shkalla e një skanimi u gjet në një kuadër kyç të mëvonshëm
  ([Shkalla](reconstruction-pose.md#scale)), ai faktor futet në shkallën e shkruar.
- `COLOR_0` lexohet nga shikuesi, i cili e ngjyros tokën me të kur ndërruesi
  *Ngjyra e kapur* i panelit të tij Sfondi / niveli është ndezur (si parazgjedhje është i fikur).
- Një skanim me pika të shënuara me dorë merr `<name>.marks.json` pranë tij; shih
  [Ruajtja](reconstruction-scan-ui.md#saving).
- Për çdo primitiv: `POSITION` (float VEC3, me `min` dhe `max`, nga të cilat shikuesi e kornizon
  kamerën), `NORMAL` (float VEC3), `COLOR_0` opsional (float VEC3, 0..1), `TEXCOORD_0` opsional;
  indekset si 16-bit kur çdo indeks është nën 65,536, përndryshe 32-bit; modaliteti trekëndësha.
- Çdo pamje bufere fillon e rreshtuar në 4 bajte; pjesa JSON plotësohet me hapësira dhe pjesa BIN
  me zero deri në 4 bajte.

## Kontrollet para shkrimit {#checks-before-writing}

Çdo pjesë verifikohet dhe refuzohet me një mesazh që e emërton kur nuk ka kulme, kur numri i
indekseve nuk është trekëndësha të plotë, kur një indeks është jashtë kufijve ose negativ, kur pozicionet
nuk janë të fundme, ose kur normalet apo ngjyrat nuk përputhen me numrin e kulmeve. Normalet llogariten kur mungojnë,
**të peshuara sipas sipërfaqes** (marching cubes lë pjesë të holla pranë faqeve të mëdha, dhe një mesatare
e papeshuar i lë trekëndëshat e vegjël të mbivotojnë faqen mbi të cilën rrinë); një kulm i degjeneruar merr "lart".
Të mos shkruash asnjë pjesë është gabim.

Eksporti nuk kthen asgjë - dhe dritarja thotë "Nothing to save" - kur vëllimi nuk jep asnjë
sipërfaqe, në vend që të shkruajë një skedar bosh që do të dukej si skanim i suksesshëm.

## Teksturat {#textures}

Shkruesi mbështet një teksturë PNG të ngjyrës bazë për çdo pjesë (me UV, një material me dy faqe,
jometalik, plotësisht i ashpër). Skanimet nuk e përdorin; ato mbajnë ngjyrë për çdo kulm. Shih
[ngjyra](reconstruction-fusion-and-texture.md#colour).

## Niveli i referencës {#the-reference-level}

`geometry/reference.py` ndërton një nivel sintetik me madhësi saktësisht të njohur përmes të njëjtit shkrues:
një tokë 400 m e nënndarë, tri ndërtesa 20 x 20 x 12 m dhe një pellg 50 m 1.5 m nën tokë, secila
klasë në një ngjyrë të sheshtë të veçantë. Testet e vetë shikuesit e gjenerojnë dhe e lexojnë me
analizuesin e vërtetë të shikuesit, ndaj formati i skedarit mbetet nën test nga të dyja anët pa lojë dhe pa
pajisje kapjeje.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
