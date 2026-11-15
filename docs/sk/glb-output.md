---
title: "Výstup .glb"
nav_order: 6
lang: "sk"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Výstup .glb {#the-glb-output}

Rekonštrukcia sa zapisuje ako binárny glTF 2.0 súbor (`.glb`), ktorý prehliadač 3DHeat načíta cez
panel Pozadie / level bez akejkoľvek špeciálnej úpravy - rovnaká zmluva, akú zapisuje
exportér Unreal. Kód: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Je napísaný ručne, nie cez knižnicu glTF: výstup je úzka podmnožina (jeden buffer, tesne
zbalený, bez animácie, bez skinningu) a závislosť, ktorá vie zapisovať celé glTF, by priniesla
svoje problémy s verziami kvôli pár stovkám riadkov.

## Čo je v súbore skenovania {#what-is-in-a-scans-file}

| Časť (názov uzla a siete) | Obsah |
|---|---|
| `ground:<name>` | trojuholníky do 35 stupňov od smeru nahor |
| `structure:<name>` | všetko ostatné |

`<name>` je názov súboru bez prípony, keď sa ukladá z okna, alebo názov videa pri `reconstruct`.
Časť bez trojuholníkov sa vynechá. Skenovanie nikdy nezapíše časť `water:`. `asset.generator` je
`heat3d-capture-scan`.

## Zmluva {#the-contract}

- **Jeden uzol pre každú časť**, pomenovaný podľa štítku časti; sieť nesie rovnaký názov.
  Prehliadač číta najprv názov *uzla*, takže pomenovať len siete by stratilo klasifikáciu.
- Štítok je `<trieda>:<name>`, kde trieda je `ground`, `structure` alebo `water` - predpona, ktorú
  prehliadač porovnáva (`^(ground|structure|water)\s*[:|]`), aby triedu vzal z tohto zápisu a
  nehádal ju z geometrie. Terén sa zobrazuje plný, stavby takmer priehľadné.
- **Súradnice sú v priestore prehliadača**: Y smeruje nahor, pravotočivá sústava a **prepočítané
  na centimetre** (metre x 100), aby sedeli s exportérom Unreal - snímka a export z motora toho
  istého miesta sa načítajú v rovnakej veľkosti s rovnakým predvoleným pohľadom kamery. Hodnota
  `extras.unit_metres` na najvyššej úrovni súboru je `0.01` (jedna jednotka je centimeter), takže
  čitateľ, ktorý pracuje v metroch, ako [`locate`](locate.md), ju prevezme v jej skutočnej veľkosti.
  Skenovanie umiestnené telemetriou Forza je výnimkou v orientácii: zostáva vo svete hry, Y
  nahor a ľavotočivé, presne ako súbory kôl, takže kolá nahrané nad ním na ňom pristanú. Keď sa
  mierka skenu zistila na neskoršej kľúčovej snímke ([Mierka](reconstruction-pose.md#scale)),
  tento koeficient sa započíta do zapísanej mierky.
- Sken s bodmi označenými ručne dostane vedľa seba súbor `<name>.marks.json`; pozrite
  [Ukladanie](reconstruction-scan-ui.md#saving).
- Pre každý primitív: `POSITION` (float VEC3, s `min` a `max`, podľa ktorých prehliadač zarámuje
  kameru), `NORMAL` (float VEC3), voliteľne `COLOR_0` (float VEC3, 0..1), voliteľne `TEXCOORD_0`;
  indexy ako 16-bitové, keď je každý index menší ako 65 536, inak 32-bitové; režim trojuholníky.
- Každý buffer view začína na 4-bajtovom zarovnaní; JSON blok sa dopĺňa medzerami a BIN blok
  nulami na 4 bajty.

## Kontroly pred zápisom {#checks-before-writing}

Každá časť sa overí a zamietne so správou, ktorá ju pomenuje, ak nemá vrcholy, ak počet indexov
nie sú celé trojuholníky, ak je index mimo rozsahu alebo záporný, ak pozície nie sú konečné, alebo
ak normály či farby nesedia s počtom vrcholov. Chýbajúce normály sa dopočítajú, **vážené plochou**
(marching cubes zanechá úzke pásy vedľa veľkých plôch a nevážený priemer nechá drobné
trojuholníky prehlasovať plochu, na ktorej ležia); degenerovaný vrchol dostane smer "nahor".
Zápis bez akejkoľvek časti je chyba.

Export nič nevráti - a okno hlási "Nothing to save" - keď objem nedá žiadny povrch, namiesto
toho, aby zapísal prázdny súbor, ktorý by vyzeral ako úspešné skenovanie.

## Textúry {#textures}

Zapisovač podporuje PNG textúru základnej farby pre každú časť (s UV súradnicami, obojstranný,
nekovový materiál, úplne drsný). Skeny ju nepoužívajú; nesú farbu po vrcholoch. Pozrite
[farba](reconstruction-fusion-and-texture.md#colour).

## Referenčný level {#the-reference-level}

`geometry/reference.py` vytvorí syntetický level presne známej veľkosti tým istým zapisovačom:
400 m rozdelený terén, tri budovy 20 x 20 x 12 m a jazierko 50 m pod zemou o hĺbke 1,5 m, každá
trieda v osobitnej plnej farbe. Testy prehliadača ho vygenerujú a načítajú jeho vlastným
parserom, takže formát je overený na oboch stranách bez hry a bez snímacieho hardvéru.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
