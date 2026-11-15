---
title: "Skipanayfirlit"
nav_order: 5
lang: "is"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Skipanayfirlit {#command-reference}

Allar skipanir keyra úr möppu geymslunnar (repository), með umhverfi verkefnisins:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Skipun | Gerir |
|---|---|
| [`route`](#route) | Tekur aðeins upp staðsetningar Forza hrings, til að finna kortið í skrám leiksins |
| [`telemetry`](#telemetry) | Tekur upp allar rásir, eina hringskrá fyrir hvern hring, fyrir Kappakstursgreining flipann |
| [`laps`](#laps) | Les hringasafn FH Companion og skrifar leið og sýni einnar brautar |
| [`reconstruct`](#reconstruct) | Leysir upptöku án nettengingar og skrifar `.glb` |
| [`hud`](#hud) | Les eigin aðgerðir leikmannsins, dauðsföll og smákortsslóð, og drápslistann, úr upptöku |
| [`locate`](#locate) | Hvar hver rammi upptöku var tekinn, borið saman við myndir af borðinu |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Skönnunarglugginn |
| [`python -m heat3d_update`](#updates) | Athugar með uppfærslu og setur hana upp |
| [`python tools/export_onnx.py`](#the-model-converter) | Breytir dýptarlíkaninu í ONNX |

Þegar verkfærið er ræst sem `python -m heat3d_capture` athugar það fyrst hvort nýrri útgáfa sé til (sjá
[Uppfærslur](updates.md); `HEAT3D_NO_UPDATE=1` slekkur á því). `--help` á eftir hvaða skipun sem er sýnir valkosti hennar:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kóði: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Hlustar á Forza Data Out og geymir aðeins staðsetningar bílsins, ekkert annað: ekkert dýptarlíkan, enginn
skjákort, engin upptaka af skjá. Kóði: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `-o`, `--out` | nauðsynlegt | Slóð úttaksins; endingu hennar er skipt út, svo `-o lap` skrifar `lap.npz` og `lap.json`. |
| `--port` | `5300` | Gáttin sem leikurinn sendir á (bundin á 127.0.0.1). |
| `--seconds` | `0` | Stöðva eftir svona margar sekúndur; `0` keyrir þar til Ctrl+C. |

Staða er aðeins geymd meðan leikurinn tilkynnir keppni (`isRaceOn`), bíllinn fer hraðar en
0,5 m/s og hann er í það minnsta 0,5 m frá síðustu geymdu stöðu - annars myndi seta í valmynd með
60 pökkum á sekúndu fylla skrána með ráslínunni. Tími hvers sýnis er keppnistími
leiksins, eða veggklukkan þegar hann er 0. Uppsetningin er greind alveg eins og fyrir
`telemetry` (bíllinn verður fyrst að hreyfast; sjá [Forza](telemetry-forza.md)).

Einu sinni á sekúndu prentar það fjölda mótteknra pakka, geymdra staða og núverandi stöðu, eða
`nothing on port 5300 yet - is Data Out on?`. Leiðin er **vistuð meðan hún er ekin**: á 2
sekúndna fresti þegar ný staða hefur borist (bilið vex í tuttugufalt það sem síðasta vistun
tók, svo mjög löng lota eyðir aldrei meira en tuttugasta hluta tíma síns í skrif), og einu sinni
til þegar upptökutækið stöðvast af hvaða ástæðu sem er - Ctrl+C, `--seconds` eða villa. Hver vistun
skrifar `lap.npz.partial` / `lap.json.partial` og flytur það svo yfir raunverulegu skrána, svo
skrárnar á disknum eru alltaf heilar; hrun eða drepið ferli tapar í mesta lagi síðustu
sekúndunum. Ef ekkert var geymt prentar það hvernig kveikja á Data Out og hættir með kóðann 1.

Úttak:

- `lap.npz` - NumPy fylki `positions` (n x 3, metrar), `times`, `speeds` (m/s);
- `lap.json` - læsilegt án þessa verkefnis:

```json
{
  "layout": "Horizon dash",
  "samples": 4210,
  "seconds": 182.4,
  "metres_driven": 5120.7,
  "bounds": {"min": [-1200.0, 110.2, 300.5], "max": [-400.3, 160.8, 1400.0]},
  "positions": [[-1180.2, 112.0, 310.4], ...]
}
```

Staðsetningarnar eru heimshnit leiksins sjálfs, og þess vegna eru þær handfang til að
finna sama landslag í skrám leiksins: `course` skipun
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) tekur þessa
JSON skrá og flytur út brautina sem hringurinn var ekinn á.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Hver valkostur og leikur er lýstur á [Upptökutæki mælingagagna](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Les hringasafnið sem FH Companion heldur og skrifar tvær skrár fyrir eina braut: leið sem
segir hvaða kortabút á að skera úr skjalasafni leiksins, og töflu með hverju sýni hvers
hrings. Þær eru skrifaðar saman svo þær geti ekki farið úr takti. Kóði:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `course` | enginn | Heiti brautar, parað laust. Slepptu til að sýna safnið. |
| `-o`, `--out` | heiti brautarinnar, lágstafir, bil sem `_` | Slóð úttaksins; `.json` og `.csv` eru skrifaðar hlið við hlið. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Hvar brautarmöppurnar eru. |
| `--margin` | `80` | Metrar sem bætast við umhverfis útbreiðslu brautarinnar í x og z í `bounds` leiðarinnar. |

### Listi {#listing}

Án brautar prentar það fjölda brautarmappa og, fyrir hverja, fjölda hringskráa
(`*.json` hvar sem er undir henni nema `course.json`) og heiti brautarinnar, síðan
`Name one to write it out:  -o <file> <course>`.

### Að finna braut {#finding-a-course}

Brautarmöppur heita `<name> (course_<x>_<z>_to_<x>_<z>)` - upphaf og endir,
námundað. Braut er fundin með, í röð: nákvæmu möppuheiti; nafnhluta möppuheitisins,
án tillits til há- og lágstafa; einstakri möppu sem heiti hennar inniheldur textann. Margar samsvaranir
eru villa sem telur þær upp.

### Hvernig það les {#reading-it}

- `course.json` í möppunni, þegar hún er læsileg, gefur heitið og óhringað upphaf og
  endi (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); annars koma þau úr
  möppuheitinu. Braut er tilkynnt sem hringbraut þegar upphaf og endir eru minna en 10 m
  hvort frá öðru.
- Hver önnur `*.json` undir möppunni er hringur (hringir liggja nokkrar möppur niður - eftir flokki,
  bíl, stillingu, merki - og leitin er einfaldlega endurkvæm). Skrár eru lesnar sem UTF-8 með byte
  order mark. Ólæsilegum hring er sleppt. Hringir eru raðaðir eftir upptökutíma.
- Fyrir hvern hring: `Lap.samples` (hvert með `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), og bílaflokkur,
  númer, frammistöðuvísitala, hringsekúndur, lengd, upptökutími og kyrrstæð ræsing.

Það prentar samantekt (hringi, sýni, besta hring og flokk hans, x/y/z útbreiðsluna).

### Úttak {#output}

**`<out>.json`** - sama leiðarform og `route` skrifar, svo kortaútdráttartækið tekur hvort sem er:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (víkkað um `--margin` í x og
z), og `positions` **hraðasta** hringsins (ein lína frekar en klessa af öllum hringjum).

**`<out>.csv`** - hvert sýni hvers hrings, ein röð hvert:

| Dálkur | Merking |
|---|---|
| `course` | heiti brautar |
| `lap` | merkimiði fyrir hvern hring: upptökudagur og tími upp á mínútu, og hringtíminn |
| `car` | númer bíls |
| `car_class` | bókstafur frammistöðuflokks |
| `pi` | frammistöðuvísitala |
| `lap_seconds` | tími hringsins |
| `speed_kmh` | hraði í km/klst |
| `x`, `y`, `z` | heimsstaða, metrar, 3 aukastafir |
| `speed_ms` | hraði, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | eins og FH Companion skráir þau |
| `metres` | vegalengd eftir hringnum, 3 aukastafir |
| `elapsed` | sekúndur frá eigin upphafi hringsins, 3 aukastafir |

Gildi sem eru ekki staða eru skrifuð með 4 marktækum stöfum; staða fær fasta aukastafi því
4 marktækir stafir myndu smella braut á eins metra rist. Dálkaheitin eru valin
svo skoðarinn varpi skránni án þess að vera sagt frá: `lap` verður lotan (tveir hringir sama bíls
eru aldrei sameinaðir), `car` það sem hreyfist, `car_class` hópurinn til að lita eftir, `elapsed`
tímaásinn (hver hringur raðast upp við eigin upphaf).

Að lokum prentar það ábendingu um að skera kortið úr leiknum með GameFiles, með leiðarskránni
eða skýrum kassa.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Endurgerir upptöku án nettengingar, með myndavélarferilinn leystan allan í einu af VGGT. Hægt:
mínútur á glugga á skjákorti í borðtölvu. Þarf PyTorch, Hugging Face `transformers` og `vggt`
pakkann, sem skannarinn þarf ekki: þau eru talin upp í `requirements-offline.txt`, og
skipunin athugar með þau eftir að hafa prentað leyfislínuna og býðst til að setja upp það sem
vantar (kóði 1 ef hafnað). Full lýsing:
[Endurgerð án nettengingar](reconstruction-offline.md).

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `video` | nauðsynlegt | Upptakan. Kóði 2 ef hún er ekki til. |
| `-o`, `--out` | nauðsynlegt | `.glb` skráin sem á að skrifa. |
| `--solve-budget` | `260` | Flestir rammar sem lausnaranum eru réttir. Þeim er raðað eftir því hve mikið myndin hreyfist, ekki eftir klukkunni. Fleiri er nákvæmara og miklu hægara. Fleiri en 400 áætlaðir rammar eru afþakkaðir. |
| `--fuse-interval` | `0.4` | Sekúndur á milli ramma sem eru felldir saman í rúmfræði. |
| `--model` | `vggt-1b` | Hvaða VGGT þyngdir á að leysa með: `vggt-1b` (`facebook/VGGT-1B`, óviðskiptalegt) eða `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, læst; þarf aðgang veittan af Meta). Leyfislínan sem er prentuð fyrst er þess líkans. |

Það prentar leyfislínu líkansins fyrst, síðan hvert stig (`masking`, `planning`, `solving`,
`fusing`, `exporting`) með liðnum sekúndum og framvindu, og loks samantekt: myndavélar
leystar, lokunarskekkja, versta samskeyti, athugasemdir og skráin sem var skrifuð. Skilakóðinn er 0 aðeins ef
skrá var skrifuð.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Les HUD leiksins úr eigin upptöku leikmannsins, eftir leikinn: eigin aðgerðir leikmannsins
úr stigaglugganum, dauðsföll og endurlífganir af niður- og endurkomuskjáunum, smákortsslóðina
og drápslistann. Skrifar `<out>.parquet` (slóð og atburði, 3DHeat tafla),
`<out>.events.jsonl`, `<out>.summary.json`, og `<out>.map.png` + `.map.json` (smákortsmósaíkina
og festipunkta hennar fyrir Map image skoðarans). Battlefield 6 (`bf6`) er eina sniðið enn sem komið er.

Þarf **ffmpeg og ffprobe** í PATH (`winget install Gyan.FFmpeg`, svo nýjan Terminal glugga).

| Valkostur | Sjálfgefið | Merking |
|---|---|---|
| `video` | nauðsynlegt | Upptakan. |
| `-o`, `--out` | heiti myndbandsins | Slóð úttaksins án endingar. |
| `--game` | `bf6` | Hvers HUD á að lesa. |
| `--player` | giskað | Nafn leikmannsins eins og drápslistinn sýnir það, parað laust. |
| `--fps` | `5` | Smákortssýni á sekúndu. |
| `--start`, `--seconds` | allt myndbandið | Sá hluti upptökunnar sem á að lesa. |
| `--metres-per-pixel` | enginn | Kvarði smákortsins, þegar hann er þekktur; án hans eru staðsetningar í smákortspunktum. |
| `--cpu` | slökkt | Afkóða á örgjörvanum jafnvel þegar NVIDIA kort er til staðar. |

Full lýsing: [Að lesa HUD úr upptöku](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` teiknar borð frá hverjum stað þar sem leikmaður getur staðið og skráir myndirnar í vísi; `frames`
staðsetur hvern sýnaðan ramma upptöku gagnvart því, út frá myndinni, með smákortsslóð `hud` skipunarinnar
sem varaleið; `eval` ber niðurstöðu saman við þekktar stöður myndavélar; `train` þjálfar
staðalíkan fyrir hvert kort á myndum af borðinu (og á römmum sem keyrsla hefur þegar staðsett), fyrir `build --head`;
`refmap` setur eigið kort leiksins (útsetningarskjáinn) á borðið, og `minimap` les
smákort upptöku gagnvart því, ramma fyrir ramma - fyrri vísbendinguna sem `frames --minimap` getur tekið. Þarf PyTorch
og `requirements-locate.txt`. **Tilraunakennt:** á raunverulegum upptökum staðsetur það enn aðeins lítinn hluta
ramma. Hver valkostur, úttökin og aðferðin:
[Að staðsetja ramma í borði](locate.md); allur valkostalistinn: [Skipanayfirlit](../cli-reference.md).

## Skönnunarglugginn {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

eða tvísmelltu á `scan.bat`. Engir valkostir. Sjá [Skönnunargluggann](reconstruction-scan-ui.md).

## Uppfærslur {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Sjá [Uppfærslur](updates.md).

## Líkanabreytirinn {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Breytir Depth Anything V2 checkpoint í ONNX skrána sem skannarinn keyrir. Þarf PyTorch,
`transformers` og `onnxscript`. Sjá [Dýpt](reconstruction-depth.md#building-the-model).
