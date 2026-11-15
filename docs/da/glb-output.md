---
title: .glb-output
nav_order: 6
lang: "da"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# .glb-output {#the-glb-output}

En rekonstruktion skrives som en binær glTF 2.0-fil (`.glb`), som 3DHeat-vieweren indlæser
gennem sit panel Baggrund / bane uden særlig håndtering - den samme kontrakt, som Unreal-eksportøren
skriver. Kode: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Den er skrevet i hånden i stedet for med et glTF-bibliotek: outputtet er en smal delmængde (én
buffer, tæt pakket, ingen animation, ingen skinning), og et afhængighedsbibliotek, der kan skrive
hele glTF, ville medbringe sin egen versionsglidning for nogle få hundrede linjer.

## Hvad der er i en scannings fil {#what-is-in-a-scans-file}

| Del (node- og mesh-navn) | Indhold |
|---|---|
| `ground:<name>` | trekanter inden for 35 grader af at vende opad |
| `structure:<name>` | alt andet |

`<name>` er filnavnet uden endelse, når der gemmes fra vinduet, eller videoens navn ved
`reconstruct`. En del uden trekanter udelades. Der skrives aldrig en `water:`-del af en scanning.
`asset.generator` er `heat3d-capture-scan`.

## Kontrakten {#the-contract}

- **Én node pr. del**, navngivet med delens etiket; mesh'en gentager navnet. Vieweren læser
  *node*-navnet først, så kun at navngive mesh'e ville miste klassificeringen.
- Etiketten er `<class>:<name>` med klassen `ground`, `structure` eller `water` - præfikset, som
  vieweren matcher (`^(ground|structure|water)\s*[:|]`), så den tager klassen for god fro i stedet
  for at gætte ud fra geometrien. Jord tegnes fast, konstruktioner næsten gennemsigtige.
- **Koordinaterne er i viewerens rum**: Y op, højrehåndet, og **skaleret til centimeter** (meter
  gange 100), så de matcher Unreal-eksportøren; en optagelse og en motoreksport af samme sted indlæses
  i samme størrelse med samme kamerastandarder. Filens øverste `extras.unit_metres` er `0.01`
  (en enhed er en centimeter), så en læser, der arbejder i meter, såsom [`locate`](locate.md), tager
  den i sin rigtige størrelse. En scanning placeret af Forza-telemetri er undtagelsen i
  håndedhed: den bliver i spillets egen verden, Y op og venstrehåndet, præcis som lap-filerne er, så
  de laps, der optages over den, havner på den. Når en scannings skala blev fundet på et senere
  keyframe ([Skala](reconstruction-pose.md#scale)), foldes den faktor ind i den skrevne skala.
- `COLOR_0` læses af vieweren, som skygger jorden med den, når kontakten *Optaget farve* i dets
  panel Baggrund / bane er tændt (slået fra som standard).
- En scanning med pletter markeret i hånden får `<name>.marks.json` ved siden af sig; se
  [Gem](reconstruction-scan-ui.md#saving).
- Pr. primitiv: `POSITION` (float VEC3, med `min` og `max`, som vieweren indrammer sit kamera ud fra),
  `NORMAL` (float VEC3), valgfri `COLOR_0` (float VEC3, 0..1), valgfri `TEXCOORD_0`; indekser som
  16 bit, når alle indekser er under 65.536, ellers 32 bit; tilstand triangles.
- Hver buffer view starter 4-byte-justeret; JSON-chunken fyldes med mellemrum og BIN-chunken med
  nuller til 4 byte.

## Kontroller før skrivning {#checks-before-writing}

Hver del valideres og afvises med en besked, der navner den, når den ikke har nogen vertices, et
antal indekser, der ikke er hele trekanter, et indeks uden for området eller negativt, ikke-endelige
positioner, eller normaler eller farver, der ikke passer til antallet af vertices. Normaler beregnes,
når de mangler, **areavægtet** (marching cubes efterlader slivere ved siden af store flader, og et
uvægtet gennemsnit lader små trekanter overstemme den flade, de ligger på); en degenereret vertex
får "op". At skrive slet ingen dele er en fejl.

Eksport returnerer intet - og vinduet siger "Intet at gemme" - når volumenet ikke giver nogen
overflade, i stedet for at skrive en tom fil, der ville se ud som en vellykket scanning.

## Teksturer {#textures}

Skriveren understøtter en PNG-grundfarvetekstur pr. del (med UV'er, dobbeltsidet, ikke-metallisk,
helt ru materiale). Scanninger bruger den ikke; de har farve pr. vertex. Se
[farve](reconstruction-fusion-and-texture.md#colour).

## Referencebanen {#the-reference-level}

`geometry/reference.py` bygger en syntetisk bane med nøjagtigt kendt størrelse gennem den samme skriver:
en 400 m underinddelt jord, tre bygninger på 20 x 20 x 12 m og en dam på 50 m 1,5 m under jorden, hver
klasse i en særskilt flad farve. Viewerens egne tests genererer den og læser den med viewerens rigtige
parser, så filformatet holdes under test på begge sider uden spil og uden optagehardware.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
