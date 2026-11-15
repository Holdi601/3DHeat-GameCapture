---
title: "Referenca e komandave"
nav_order: 5
lang: "sq"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Referenca e komandave {#command-reference}

Të gjitha komandat ekzekutohen nga dosja e repozitorit, me mjedisin e projektit:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Komanda | Çfarë bën |
|---|---|
| [`route`](#route) | Regjistron vetëm pozicionet e një xhiroje Forza, për të gjetur hartën në skedarët e lojës |
| [`telemetry`](#telemetry) | Regjistron çdo kanal, një skedar xhiroje për xhiro, për skedën "Analiza e garës" |
| [`laps`](#laps) | Lexon një bibliotekë xhirosh të FH Companion dhe shkruan rrugën dhe mostrat e një kursi |
| [`reconstruct`](#reconstruct) | Zgjidh një regjistrim offline dhe shkruan një `.glb` |
| [`hud`](#hud) | Lexon nga një regjistrim veprimet e vetë lojtarit, vdekjet dhe gjurmën e minihartës, si dhe kill feed-in |
| [`locate`](#locate) | Ku u mor çdo kuadër i një regjistrimi, kundrejt rendereve të nivelit |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Dritarja e skanimit |
| [`python -m heat3d_update`](#updates) | Kontrollon dhe zbaton një përditësim |
| [`python tools/export_onnx.py`](#the-model-converter) | Kthen modelin e thellësisë në ONNX |

Kur nisni si `python -m heat3d_capture`, mjeti fillimisht kontrollon për një version më të ri (shihni
[Përditësimet](updates.md); `HEAT3D_NO_UPDATE=1` e fik). `--help` pas çdo verbi liston opsionet e tij:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kodi: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Dëgjon Forza Data Out dhe mban vetëm pozicionet e makinës, asgjë tjetër: pa model thellësie, pa
GPU, pa kapje. Kodi: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opsioni | Parazgjedhja | Kuptimi |
|---|---|---|
| `-o`, `--out` | i detyrueshëm | Rruga e daljes; prapashtesa e saj zëvendësohet, ndaj `-o lap` shkruan `lap.npz` dhe `lap.json`. |
| `--port` | `5300` | Porta ku dërgon loja (lidhur në 127.0.0.1). |
| `--seconds` | `0` | Ndalon pas kaq sekondash; `0` vazhdon deri te Ctrl+C. |

Një pozicion mbahet vetëm ndërsa loja raporton një garë (`isRaceOn`), makina lëviz më shpejt se
0.5 m/s dhe ndodhet të paktën 0.5 m larg pozicionit të fundit të mbajtur - përndryshe të qenit në një meny
me 60 paketa në sekondë do ta mbushte skedarin me vijën e nisjes. Koha e secilës mostër është
koha e garës e lojës, ose ora e murit kur ajo është 0. Struktura zbulohet saktësisht si për
`telemetry` (makina duhet të lëvizë fillimisht; shihni [Forza](telemetry-forza.md)).

Çdo sekondë printon paketat e marra, pozicionet e mbajtura dhe pozicionin e tanishëm, ose
`nothing on port 5300 yet - is Data Out on?`. Rruga **ruhet ndërsa drejtohet**: çdo
2 sekonda sapo ka mbërritur një pozicion i ri (hapësira rritet deri në njëzet herë kohën që mori
ruajtja e fundit, ndaj një seancë shumë e gjatë nuk shpenzon kurrë më shumë se një të njëzetën e kohës së saj duke shkruar), dhe edhe një herë
kur regjistruesi ndalon për çfarëdo arsye - Ctrl+C, `--seconds`, ose një përjashtim. Çdo ruajtje
shkruan `lap.npz.partial` / `lap.json.partial` dhe pastaj e zhvendos mbi skedarin e vërtetë, kështu që
skedarët në disk janë gjithmonë të plotë; një rrëzim ose një proces i vrarë humb më së shumti sekondat e fundit.
Nëse nuk u mbajt asgjë, printon si ta ndizni Data Out dhe del me kodin 1.

Dalja:

- `lap.npz` - vargje NumPy `positions` (n x 3, metra), `times`, `speeds` (m/s);
- `lap.json` - i lexueshëm pa këtë projekt:

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

Pozicionet janë koordinatat e vetë botës së lojës, e cila i bën një dorezë për
të gjetur të njëjtën tokë në skedarët e lojës: komanda `course` e
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) e merr këtë
JSON dhe eksporton kursin mbi të cilin u drejtua xhiroja.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Çdo opsion dhe çdo lojë përshkruhet te [Regjistruesit e telemetrisë](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Lexon bibliotekën e xhirosh që mban FH Companion dhe shkruan dy skedarë për një kurs: një rrugë që
tregon cilën pjesë të hartës ta presësh nga arkivi i lojës, dhe një tabelë me çdo mostër të çdo
xhiroje. Shkruhen së bashku që të mos dalin kurrë jashtë hapi. Kodi:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opsioni | Parazgjedhja | Kuptimi |
|---|---|---|
| `course` | asnjë | Emri i kursit, i përputhur lirshëm. Lëreni për të listuar bibliotekën. |
| `-o`, `--out` | emri i kursit, me shkronja të vogla, hapësirat si `_` | Rruga e daljes; `.json` dhe `.csv` shkruhen pranë njëri-tjetrit. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Ku ndodhen dosjet e kurseve. |
| `--margin` | `80` | Metra të shtuara rreth shtrirjes së kursit në x dhe z te `bounds` e rrugës. |

### Listimi {#listing}

Pa një kurs printon numrin e dosjeve të kurseve dhe, për secilën, numrin e skedarëve të xhiros
(`*.json` kudo poshtë saj, përveç `course.json`) dhe emrin e kursit, pastaj
`Name one to write it out:  -o <file> <course>`.

### Gjetja e një kursi {#finding-a-course}

Dosjet e kurseve emërtohen `<name> (course_<x>_<z>_to_<x>_<z>)` - nisja dhe mbarimi,
të rrumbullakuara. Një kurs gjendet sipas kësaj radhe: emri i saktë i dosjes; pjesa e emrit në emrin e
dosjes, pa marrë parasysh shkronjat e mëdha; një dosje unike emri i së cilës përmban tekstin. Disa përputhje
janë gabim që i liston ato.

### Leximi {#reading-it}

- `course.json` në dosje, kur lexohet, jep emrin dhe nisjen dhe mbarimin e parrumbullakuar
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); përndryshe vijnë nga emri i
  dosjes. Një kurs raportohet si qark kur nisja dhe mbarimi janë më pak se 10 m
  larg njëra-tjetrës.
- Çdo `*.json` tjetër poshtë dosjes është një xhiro (xhirot qëndrojnë disa dosje thellë - sipas klasës,
  makinës, rregullimit, etiketës - dhe kërkimi është thjesht rekursiv). Skedarët lexohen si UTF-8 me shenjën
  e rendit të bajteve. Një xhiro e palexueshme anashkalohet. Xhirot renditen sipas kohës së regjistrimit.
- Për xhiro: `Lap.samples` (secila me `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), dhe klasa e makinës,
  ordinali, indeksi i performancës, sekondat e xhiros, gjatësia, koha e regjistrimit dhe nisja nga qëndrimi.

Printon një përmbledhje (xhirot, mostrat, xhiroja më e mirë dhe klasa e saj, shtrirja x/y/z).

### Dalja {#output}

**`<out>.json`** - e njëjta formë rruge që shkruan `route`, kështu që nxjerrësi i hartës merr cilindo:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (zgjeruar me `--margin` në x dhe
z), dhe `positions` të xhiros **më të shpejtë** (një vijë në vend të një njolle me çdo xhiro).

**`<out>.csv`** - çdo mostër e çdo xhiroje, një rresht secila:

| Kolona | Kuptimi |
|---|---|
| `course` | emri i kursit |
| `lap` | një etiketë për xhiro: data dhe ora e regjistrimit deri te minuta, dhe koha e xhiros |
| `car` | ordinali i makinës |
| `car_class` | shkronja e klasës së performancës |
| `pi` | indeksi i performancës |
| `lap_seconds` | koha e xhiros |
| `speed_kmh` | shpejtësia në km/h |
| `x`, `y`, `z` | pozicioni në botë, metra, 3 shifra dhjetore |
| `speed_ms` | shpejtësia, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | siç i regjistron FH Companion |
| `metres` | distanca përgjatë xhiros, 3 shifra dhjetore |
| `elapsed` | sekonda që nga nisja e vetë xhiros, 3 shifra dhjetore |

Vlerat që nuk janë pozicione shkruhen me 4 shifra domethënëse; pozicionet marrin shifra dhjetore të fiksuara sepse
4 shifra domethënëse do ta ngjitnin një kurs te një rrjetë një metërshe. Emrat e kolonave janë zgjedhur
që shikuesi ta lidhë skedarin pa iu thënë: `lap` bëhet seanca (dy xhiro të një makine
nuk bashkohen kurrë), `car` gjëja që lëviz, `car_class` grupi sipas të cilit ngjyroset, `elapsed`
boshti i kohës (çdo xhiro rreshtohet në nisjen e vet).

Në fund printon një sugjerim për ta prerë hartën nga loja me GameFiles, me skedarin e
rrugës ose një kuti të qartë.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rindërton një regjistrim offline, me rrugën e kamerës të zgjidhur të gjitha menjëherë nga VGGT. Ngadalë:
minuta për dritare në një GPU desktop. Kërkon PyTorch, Hugging Face `transformers` dhe paketën
`vggt`, që skaneri nuk i kërkon: ato listohen te `requirements-offline.txt`, dhe
komanda i kontrollon pasi printon rreshtin e licencës dhe ofron të instalojë çfarëdo që mungon
(kodi i daljes 1 nëse refuzohet). Përshkrimi i plotë:
[Rindërtimi offline](reconstruction-offline.md).

| Opsioni | Parazgjedhja | Kuptimi |
|---|---|---|
| `video` | i detyrueshëm | Regjistrimi. Kodi i daljes 2 nëse nuk ekziston. |
| `-o`, `--out` | i detyrueshëm | `.glb` që do të shkruhet. |
| `--solve-budget` | `260` | Më së shumti kuadro që i jepen zgjidhësit. Ato hapësohen sipas sa lëviz pamja, jo sipas orës. Më shumë do të thotë më i saktë dhe shumë më i ngadaltë. Më shumë se 400 kuadro të planifikuara refuzohen. |
| `--fuse-interval` | `0.4` | Sekonda midis kuadrove që shkrihen në gjeometri. |
| `--model` | `vggt-1b` | Me cilat pesha VGGT të zgjidhet: `vggt-1b` (`facebook/VGGT-1B`, jo komerciale) ose `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, i kufizuar; kërkon akses të dhënë nga Meta). Rreshti i licencës që printohet i pari është i atij modeli. |

Printon fillimisht rreshtin e licencës së modelit, pastaj çdo fazë (`masking`, `planning`, `solving`,
`fusing`, `exporting`) me sekondat e kaluara dhe përparimin, dhe në fund një përmbledhje: kamerat
e zgjidhura, gabimi i mbylljes, tegeli më i keq, shënimet dhe skedari i shkruar. Kodi i daljes është 0 vetëm nëse u
shkrua një skedar.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Lexon HUD-in e lojës nga regjistrimi i vetë lojtarit, pas ndeshjes: veprimet e vetë lojtarit
nga dritarja e pikëve, vdekjet dhe ringjalljet nga ekranet e rrëzimit dhe të vendosjes, gjurmën e
minihartës dhe kill feed-in. Shkruan `<out>.parquet` (gjurma dhe ngjarjet, një tabelë 3DHeat),
`<out>.events.jsonl`, `<out>.summary.json`, dhe `<out>.map.png` + `.map.json` (mozaiku i minihartës
dhe spirancat e tij për "Imazh harte" të shikuesit). Battlefield 6 (`bf6`) është i vetmi profil deri tani.

Kërkon **ffmpeg dhe ffprobe** në PATH (`winget install Gyan.FFmpeg`, pastaj një terminal i ri).

| Opsioni | Parazgjedhja | Kuptimi |
|---|---|---|
| `video` | i detyrueshëm | Regjistrimi. |
| `-o`, `--out` | emri i videos | Rruga e daljes pa prapashtesë. |
| `--game` | `bf6` | HUD-in e kujt ta lexojë. |
| `--player` | merret me hamendje | Emri i lojtarit siç e shfaq kill feed-i, i përputhur lirshëm. |
| `--fps` | `5` | Mostra të minihartës në sekondë. |
| `--start`, `--seconds` | e gjithë videoja | Pjesa e regjistrimit që do të lexohet. |
| `--metres-per-pixel` | asnjë | Shkalla e minihartës, kur dihet; pa të pozicionet janë në piksele të minihartës. |
| `--cpu` | fikur | Dekodon në CPU edhe kur ka një kartë NVIDIA. |

Përshkrimi i plotë: [Leximi i HUD-it nga një regjistrim](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderon një nivel nga çdo vend ku mund të qëndrojë një lojtar dhe indekson rendert; `frames`
e vendos çdo kuadër të mostruar të një regjistrimi kundrejt tij, nga pamja, me gjurmën e minihartës së verbit `hud`
si zgjidhje rezervë; `eval` krahason një rezultat me pozicione të njohura të kamerës; `train` stërvit një
model vendesh për çdo hartë mbi rendera të nivelit (dhe mbi kuadro që një ekzekutim i ka lokalizuar tashmë), për `build --head`;
`refmap` e vendos hartën e vetë lojës (ekranin e vendosjes) mbi nivelin, dhe `minimap` lexon minihartën e një
regjistrimi kundrejt saj, kuadër pas kuadri - paraprakja që `frames --minimap` mund ta marrë. Kërkon PyTorch
dhe `requirements-locate.txt`. **Eksperimentale:** në regjistrime reale deri tani vendos vetëm një pjesë të vogël të
kuadrove. Çdo opsion, daljet dhe metoda:
[Gjetja e kuadrove në një nivel](locate.md); lista e plotë e opsioneve: [Referenca e komandave](../cli-reference.md).

## Dritarja e skanimit {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ose klikoni dy herë `scan.bat`. Pa opsione. Shihni [Dritarja e skanimit](reconstruction-scan-ui.md).

## Përditësimet {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Shihni [Përditësimet](updates.md).

## Konvertuesi i modelit {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Kthen një checkpoint të Depth Anything V2 në skedarin ONNX që xhiron skaneri. Kërkon PyTorch,
`transformers` dhe `onnxscript`. Shihni [Thellësia](reconstruction-depth.md#building-the-model).
