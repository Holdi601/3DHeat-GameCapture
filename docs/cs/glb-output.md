---
title: Výstup .glb
nav_order: 6
lang: "cs"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Výstup .glb {#the-glb-output}

Rekonstrukce se zapisuje jako binární soubor glTF 2.0 (`.glb`), který prohlížeč 3DHeat načte přes panel Pozadí / úroveň bez zvláštního zacházení. Je to stejná smlouva, jakou zapisuje exportér Unreal. Kód: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Zapisuje se ručně, ne přes knihovnu glTF. Výstup je úzká podmnožina (jeden buffer, pevně sbalený, bez animace a skinningu) a závislost, která umí celé glTF, by pro pár set řádků přinesla vlastní problémy s verzemi.

## Co je v souboru skenu {#what-is-in-a-scans-file}

| Část (název uzlu a sítě) | Obsah |
|---|---|
| `ground:<name>` | trojúhelníky do 35 stupňů od směru nahoru |
| `structure:<name>` | všechno ostatní |

`<name>` je název souboru bez přípony, když ukládáte z okna, nebo název videa u `reconstruct`. Část bez trojúhelníků se vynechá. Sken nikdy nezapisuje část `water:`. `asset.generator` je `heat3d-capture-scan`.

## Smlouva {#the-contract}

- **Jeden uzel na část**, pojmenovaný popiskem části; síť název opakuje. Prohlížeč čte nejdřív název *uzlu*, takže pojmenovat jen sítě by ztratilo zařazení.
- Popisek je `<class>:<name>`, kde třída je `ground`, `structure` nebo `water`. Je to předpona, kterou prohlížeč hledá (`^(ground|structure|water)\s*[:|]`), aby třídu vzal doslova a nehádal ji z geometrie. Terén se vykresluje plně, konstrukce téměř průhledně.
- **Souřadnice jsou v prostoru prohlížeče**: Y nahoru, pravotočivé, a **převedené na centimetry** (metry x 100), aby odpovídaly exportéru Unreal. Zachycená a exportovaná místa se tak načtou ve stejné velikosti se stejným výchozím pohledem kamery. Hlavní `extras.unit_metres` v souboru je `0.01` (jedna jednotka je centimetr), takže čtenář pracující v metrech, jako [`locate`](locate.md), ho vezme v jeho skutečné velikosti. Sken umístěný telemetrií Forzy je výjimkou v orientaci: zůstává ve světě hry, Y nahoru a levotočivé, přesně jako soubory kol, takže kola nahraná nad ním na něj dopadnou. Když se měřítko skenu našlo na pozdějším klíčovém snímku ([Měřítko](reconstruction-pose.md#scale)), je ten činitel zapsán do výsledného měřítka.
- `COLOR_0` čte prohlížeč, který podle něj stíní terén, když je přepínač *Zachycená barva* na panelu Pozadí / úroveň zapnutý (ve výchozím stavu vypnutý).
- Sken s body označenými ručně dostane vedle sebe `<name>.marks.json`; viz [Ukládání](reconstruction-scan-ui.md#saving).
- Pro každý primitiv: `POSITION` (float VEC3, s `min` a `max`, podle kterých prohlížeč nastaví kameru), `NORMAL` (float VEC3), volitelně `COLOR_0` (float VEC3, 0 až 1), volitelně `TEXCOORD_0`; indexy jako 16bitové, když je každý index menší než 65 536, jinak 32bitové; režim triangles.
- Každý buffer view začíná zarovnaný na 4 bajty; blok JSON se doplní mezerami a blok BIN nulami na 4 bajty.

## Kontroly před zápisem {#checks-before-writing}

Každá část se ověřuje a odmítne se se zprávou, která ji pojmenuje, když nemá vrcholy, když počet indexů nedává celé trojúhelníky, když je index mimo rozsah nebo záporný, když pozice nejsou konečné, nebo když normály či barvy nesedí s počtem vrcholů. Chybějící normály se počítají **vážené podle plochy** (pochodující kostky zanechávají u velkých ploch úzké trojúhelníčky a nevážený průměr nechá drobné trojúhelníky přehlasovat plochu, na které sedí). Zdegenerovaný vrchol dostane „nahoru“. Když nejsou zapsané žádné části, je to chyba.

Export nic nevrací a okno hlásí „Nic k uložení“, když objem nedává žádný povrch. Nezapíše prázdný soubor, který by vypadal jako úspěšný sken.

## Textury {#textures}

Zapisovatel podporuje PNG texturu základní barvy na část (s UV, oboustranný, nekovový, plně drsný materiál). Skeny ji nepoužívají; nesou barvu na vrchol. Viz [barva](reconstruction-fusion-and-texture.md#colour).

## Referenční úroveň {#the-reference-level}

`geometry/reference.py` sestaví syntetickou úroveň přesně známé velikosti stejným zapisovatelem: terén 400 m rozdělený na plochy, tři budovy 20 x 20 x 12 m a jezírko 50 m, 1,5 m pod zemí. Každá třída má jinou plochou barvu. Testy prohlížeče ji vygenerují a zpracují skutečným parserem prohlížeče, takže formát zůstává testovaný na obou stranách, bez hry a bez záznamového hardwaru.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
