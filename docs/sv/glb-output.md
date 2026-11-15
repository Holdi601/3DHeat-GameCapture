---
title: Utdatan .glb
nav_order: 6
lang: "sv"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Utdatan .glb {#the-glb-output}

En rekonstruktion skrivs som en binär glTF 2.0-fil (`.glb`) som 3DHeat-visaren läser in via
panelen Bakgrund / nivå utan någon särskild hantering - samma kontrakt som Unreal-exportören
skriver. Kod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Den skrivs för hand i stället för via ett glTF-bibliotek: utdatan är en smal delmängd (en buffert,
tätt packad, ingen animation, ingen skinning), och ett beroende som kan skriva all glTF skulle ge
sin versionsglidning för några hundra rader.

## Vad som finns i en skannings fil {#what-is-in-a-scans-file}

| Del (nod- och meshnamn) | Innehåll |
|---|---|
| `ground:<name>` | trianglar inom 35 grader från att vara vända uppåt |
| `structure:<name>` | allt annat |

`<name>` är filnamnet utan ändelse när man sparar från fönstret, eller videons namn för
`reconstruct`. En del utan trianglar utelämnas. Ingen `water:`-del skrivs någonsin av en skanning.
`asset.generator` är `heat3d-capture-scan`.

## Kontraktet {#the-contract}

- **En nod per del**, namngiven med delens etikett; meshen upprepar namnet. Visaren läser
  *nodens* namn först, så om man bara namngav meshar skulle klassificeringen gå förlorad.
- Etiketten är `<class>:<name>` med klassen `ground`, `structure` eller `water` - prefixet som
  visaren matchar (`^(ground|structure|water)\s*[:|]`) för att ta klassen för vad den säger i
  stället för att gissa utifrån geometrin. Mark renderas solid, strukturer nästan genomskinliga.
- **Koordinaterna är i visarens rum**: Y uppåt, högerhänt, och **skalade till centimeter** (meter
  x 100) för att matcha Unreal-exportören, så att en inspelning och en motorexport av samma plats
  laddas i samma storlek med samma kameraståndard. Filens översta `extras.unit_metres` är `0.01`
  (en enhet är en centimeter), så att en läsare som arbetar i meter, till exempel
  [`locate`](locate.md), tar den i sin rätta storlek. En skanning placerad med Forza-telemetri är
  undantaget i högerhänthet: den ligger kvar i spelets egen värld, Y uppåt och vänsterhänt, precis
  som varvfilerna är, så att varven som spelas in över den hamnar på den. När en skannings skala
  hittades på en senare nyckelbild ([Skala](reconstruction-pose.md#scale)), läggs den faktorn in i
  den skala som skrivs.
- `COLOR_0` läses av visaren, som skuggar marken med den när panelen Bakgrund / nivå har
  omkopplaren *Fångad färg* på (av som standard).
- En skanning med platser markerade för hand får `<name>.marks.json` bredvid sig; se
  [Spara](reconstruction-scan-ui.md#saving).
- Per primitiv: `POSITION` (float VEC3, med `min` och `max`, som visaren ramar in kameran från),
  `NORMAL` (float VEC3), valfri `COLOR_0` (float VEC3, 0..1), valfri `TEXCOORD_0`; index som 16-bitars
  när varje index är under 65 536, annars 32-bitars; läge triangles.
- Varje buffervy börjar 4-bytesjusterad; JSON-delen fylls ut med blanksteg och BIN-delen med nollor
  till 4 byte.

## Kontroller före skrivning {#checks-before-writing}

Varje del valideras och avvisas med ett meddelande som namnger den när den saknar hörn, ett
indexantal som inte är hela trianglar, ett index utanför intervallet eller negativt, icke-ändliga
positioner, eller normaler eller färger som inte stämmer med antalet hörn. Normaler beräknas när de
saknas, **areaviktade** (marching cubes lämnar smala trianglar intill stora ytor, och ett
oviktat medelvärde låter små trianglar överrösta ytan de ligger på); ett degenererat hörn får
"upp". Om inga delar alls skrivs är det ett fel.

Export returnerar ingenting - och fönstret säger "Inget att spara" - när volymen inte ger någon yta,
i stället för att skriva en tom fil som skulle se ut som en lyckad skanning.

## Texturer {#textures}

Skrivaren stöder en PNG-basfärgstextur per del (med UV, dubbelsidigt, icke-metalliskt och helt
grovt material). Skanningar använder den inte; de bär färg per hörn. Se
[färg](reconstruction-fusion-and-texture.md#colour).

## Referensnivån {#the-reference-level}

`geometry/reference.py` bygger en syntetisk nivå av exakt känd storlek genom samma skrivare: en
400 m indelad mark, tre byggnader på 20 x 20 x 12 m och en damm på 50 m 1,5 m under marken, där varje
klass har en egen platt färg. Visarens egna tester skapar den och läser den med visarens riktiga
läsare, så filformatet hålls testat på båda sidor utan något spel och utan inspelningsutrustning.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
