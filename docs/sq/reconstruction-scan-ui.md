---
title: "Dritarja e skanimit"
nav_order: 1
lang: "sq"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Dritarja e skanimit {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kodi: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Dritarja është një pamje e hollë mbi `scan/session.py` dhe `scan/reconstruct.py`; ajo nuk ka asnjë
logjikë skanimi ose gjeometrie.

## Nisja {#starting-up}

1. **Kontrolli i përditësimit** - shihni [Përditësimet](updates.md).
2. **Kontrolli i varësive** - çdo paketë që i duhet skanerit kontrollohet para se të importohet
   ndonjë gjë; ato që mungojnë listohen me qëllimin e tyre dhe madhësinë e shkarkimit, dhe
   instalohen vetëm pas "Download and install". Cancel del pa ndryshuar asgjë. Shihni
   [Runtime dhe varësitë](runtime.md#first-run-preflight).
3. **Dritarja** - "3DHeat — Level scanner", 1420 x 900, stili Fusion i Qt.
4. **Kontrolli i harduerit** - zgjidhet backend-i më i mirë i inferencës, ngarkohet modeli i thellësisë dhe
   matet kapaciteti i tij në 6 kuadro; kutia e verdiktit lart majtas tregon si do të jetë skanimi
   (shihni [Runtime](runtime.md#what-to-expect-from-this-machine)).
5. **Tastet globale** regjistrohen të fundit.

### Kur nuk ka ende model thellësie {#when-there-is-no-depth-model-yet}

Nëse `models/` nuk ka asnjë `depth-*.onnx`, verdikti thotë **"One more thing to set up."**, Start
çaktivizohet dhe del një buton **Set up the depth model**. Ai:

- kontrollon për PyTorch, `transformers` dhe `onnxscript` (rreth 945 MB së bashku), dhe pyet para se
  t'i instalojë;
- ekzekuton `tools/export_onnx.py --size small` si proces të veçantë (që PyTorch të mos mbetet kurrë në
  memorien e skanerit), me kufi 30 minuta. Dritarja nuk përgjigjet ndërsa ai xhiron;
- nëse ia del, e ekzekuton sërish kontrollin e harduerit; nëse dështon, shfaq 600 karakteret e fundit të
  daljes së konvertuesit.

Kur janë të pranishëm disa modele, zgjedhja bëhet **sipas licencës, jo sipas emrit të skedarit**: `depth-small-*`
(Apache-2.0, përdorimi komercial lejohet) sa herë që ka një, pastaj Base, pastaj Large (të dyja
jo komerciale). Kutia e verdiktit dhe rreshti gri nën butonat tregojnë skedarin në përdorim, licencën e tij dhe
çdo skedar tjetër modeli që është i pranishëm dhe nuk përdoret - për shembull `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Për të skanuar me Base, zhvendoseni skedarin Small jashtë `models/`.

## Kolona e majtë: cilësimet {#left-column-settings}

| Grupi | Kontrolli | Parazgjedhja | Fusha / vlerat | Çfarë bën |
|---|---|---|---|---|
| (lart) | Kutia e verdiktit | "Checking your graphics card…" | ngjyroset jeshile, qelibar ose e kuqe sipas nivelit | Titulli, `<device> via <API> — N views per second`, një shënim dhe `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Nga vijnë kuadrot |
| | Which | `1` | numri i monitorit / titulli i dritares / rruga e një videoje | `monitor:<n>`, `window:<title>`, ose rruga e një skedari |
| | Choose file… | shfaqet për video | `*.mp4 *.mkv *.avi *.mov` | Plotëson rrugën |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Rezolucioni i kapjes dhe sa selektiv është zgjedhja e kuadrove kyç (më poshtë); një përmbledhje me një rresht shfaqet nën të |
| | Game field of view | 90° | 30-140° | Këndi **horizontal** i shikimit i lojës. Nëse është shumë i ngushtë, niveli rindërtohet më i thellë se sa është; nëse shumë i gjerë, rrafshohet. Lojërat e garave janë më afër 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, hapi 0.05 | Madhësia e voxel-it të sipërfaqes. Më i vogël është më i imët dhe më i rëndë |
| Stop after | Time | pa kufi | 0-120 min | E mbyll skanimin pas kësaj kohe (0 = pa kufi) |
| | Views kept | 3000 | 0-100,000 | E mbyll skanimin pas kaq kuadrosh kyç, si mbrojtje e memories (0 = pa kufi) |
| What to ignore | Ignore HUD and anything on the camera | ndezur | | Mëson dhe maskon HUD-in, shënjestrën, armën, kapakun e motorit, kabinën ([Kapja](reconstruction-capture.md#what-is-not-the-world)). Rreshti nën të thotë çfarë vendos aktualisht detektori |
| While you play | Show feedback over the game | ndezur | | Hap mbivendosjen që lë klikimet të kalojnë gjatë skanimit. Sugjerimi poshtë saj: xhironi lojën në **borderless windowed**; mbi ekranin e plotë ekskluziv nuk mund të vizatojë asgjë |
| Racing telemetry (Forza) | Listen for position data | fikur | | E merr rrugën e kamerës nga Data Out i Forza në vend që ta vlerësojë ([Pozicioni](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Porta e Data Out |
| | (status line) | | | `N packets — poses come from the game, not from the picture`, ose `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Nis ose ndalon; shfaq tastin kur ai u regjistrua |
| | **Set up the depth model** | e fshehur | | Shihni më sipër |
| | **Save level…** | çaktivizuar | | Aktivizohet pas një skanimi që dha voxel sipërfaqeje; kërkon një emër skedari (parazgjedhja `scan.glb`) |
| | (grey line) | | | `Model: <file> (<licence>) · Available: <backends>`, plus shënime konfigurimi si instalimi i `onnxruntime-gpu` |

### Presetet {#the-presets}

| Preseti | Ana më e gjatë e kapjes | Kuantili i mbajtjes | Pragu fillestar | Përmbledhja e shfaqur |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Shpejt dhe përafërsisht. I mirë për të kontrolluar një rrugë para një skanimi të vërtetë. |
| Balanced | 960 px | 0.65 | 0.010 | Zgjedhja e zakonshme. Ec me ritëm normal. |
| Detailed | 1280 px | 0.40 | 0.004 | Ngadalë dhe i plotë. Ec me qëllim dhe kthehu butë. |

Kuantili i mbajtjes do të thotë "mbaj një kuadër kur ndryshoi më shumë se ky kuantil i ndryshimeve të 240
kuadrove të fundit" - Draft mban afërsisht 15% më të zhurmshmet, Detailed 60% më të zhurmshmet. Shihni
[Kuadrot kyç](reconstruction-capture.md#keyframes).

### Cilësimet që janë fikse në dritare {#settings-that-are-fixed-in-the-window}

Dritarja gjithmonë rindërton gjatë skanimit, përdor lartësi kamere **1.15 m** për shkallën e
rrafshit të tokës (vlera e ecjes 1.70 m nuk zgjidhet) dhe e lë shkallën e backend-eve
të zgjedhë GPU-në. Këto janë fusha të `ScanSettings` (`camera_height`, `prefer_backend`) që mund t'i ndryshojë vetëm
një skript.

## Kolona e djathtë: çfarë po bën skanimi {#right-column-what-the-scan-is-doing}

| Elementi | Çfarë tregon |
|---|---|
| **What the camera sees** | kuadri kyç i fundit |
| **Shape it is reading** | thellësia e tij e parashikuar, e ngjyrosur me hartën e ngjyrave Turbo, e normalizuar midis përqindjes së 2-të dhe të 98-të të atij kuadri (që një piksel qielli të mos e rrafshojë gamën) |
| **Coverage — where you have been, and how well** | një pamje plani (shihni më poshtë) |
| **Worth another look** | pikat e dobëta, të numëruara si unazat në hartë, secila me një udhëzim; më e keqja (më e madhja) e para, më së shumti 8; pastaj pikat që shënuat (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Shiriti i shpejtësisë së ecjes | `walk speed — N% of the way to the next view`: ndryshimi i pamjes i kuadrit të fundit pjesëtuar me **pragun në përdorim** - vlera fillestare e presetit për 30 kuadrot e para, ajo e përshtatur pas kësaj ([Kuadrot kyç](reconstruction-capture.md#keyframes)) |
| Rreshti i shëndetit | shëndeti i ndjekjes, ose një paralajmërim i kapjes (më poshtë) |
| Rreshti i madhësisë | `Size: ...`, si u fiksua shkalla e nivelit ose pse nuk u fiksua ([Shkalla](reconstruction-pose.md#scale)) |
| Rreshti i statistikave | `views  frames  dropped  depth-per-second  seconds`, dhe gjatë rindërtimit `placed  cells  % well seen  metres`, plus `recovered` dhe `loops closed` kur njëri prej tyre nuk është zero |
| Rreshti i tasteve | tastet e regjistruara, ose pse nuk mund të regjistroheshin |
| Rreshti i sugjerimeve (qelibar) | këshilla live (më poshtë), mesazhi i fundit i skanimit dhe shenjat |

### Harta e mbulimit {#the-coverage-map}

Rivizatohet çdo 900 ms në një thread në sfond (kurrë në thread-in e ndërfaqes), me 200 x 200
qeliza të shkallëzuara në 420 px:

- çdo kolonë e rrjetës së mbulimit merr cilësinë **më të mirë** të vëzhgimit në të (që një
  dysheme e parë mirë të mos ngjyroset qelibar nga një tavan i parë dobët sipër saj);
- shkalla shkon e kuqe (keq) - qelibar (e hollë) - e verdhë (e pranueshme) - jeshile (mirë);
- qelizat e pavëzhguara kurrë janë gri e errët e dallueshme, që një cep i pashkelur të mos lexohet si një
  i skanuar keq;
- rruga e ecur vizatohet si vijë e hollë e çelët, pozicioni i tanishëm si pikë e bardhë;
- pikat e dobëta janë unaza të bardha me numrin e tyre;
- pikat që shënuat janë katrorë qelibar me etiketën `M1`, `M2`, …

Si llogariten cilësia dhe pikat e dobëta: [Shkrirja, mbulimi dhe ngjyra](reconstruction-fusion-and-texture.md#coverage).

### Rreshti i shëndetit {#the-health-line}

| Shëndeti i ndjekjes (kuadro të vendosura / kuadro) | Teksti | Ngjyra |
|---|---|---|
| ende pa kuadro | Waiting for the first frame. | gri |
| 90% ose më shumë | Tracking well — N of M frames placed. | jeshile |
| 60% ose më shumë | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | qelibar |
| nën 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | e kuqe |

Një paralajmërim kapjeje nga rrjeta e mbulimit e zëvendëson (e kuqe kur skanimi gjykohet i
parindërtueshëm, qelibar përndryshe): pothuajse pa paralaks, gjithçka e parë nga më shumë se 25 m,
ose paralaks i hollë. Shihni [Mbulimi](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Rreshti i sugjerimeve {#the-hint-line}

| Kushti | Sugjerimi |
|---|---|
| më shumë se gjysma e kuadrove të hedhura, pas 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| më pak se 0.3 kuadro të mbajtur në sekondë, pas 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| më shumë se 8 kuadro të mbajtur në sekondë, pas 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| skanimi përfundoi | mesazhi i seancës: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, ose `failed: <error>` |

## Tastet e shpejta {#hotkeys}

Regjistrohen në Windows (`RegisterHotKey`), ndaj funksionojnë ndërsa loja ka fokusin. Të dalësh me Alt+Tab
nga një lojë në ekran të plotë është pikërisht ajo që prish një kapje.

| Tastet | Veprimi |
|---|---|
| **Ctrl+Alt+F9** | Nis / ndalon skanimin |
| **Ctrl+Alt+F10** | Shënon këtë pikë për ta rishikuar (gjatë skanimit) |
| **Ctrl+Alt+F11** | Shfaq / fsheh mbivendosjen (ndërron kutinë "Show feedback over the game") |

- Regjistrohen një herë, kur hapet dritarja, dhe lirohen kur ajo mbyllet; sa kohë janë
  të regjistruara, këto kombinime tastesh u merren të gjitha programeve të tjera, përfshirë
  lojën. U zgjodhën tastet F me dy modifikues sepse lojërat rrallë i lidhin.
- Përsëritja automatike shtypet (`MOD_NOREPEAT`), ndaj mbajtja e një tasti nuk e ndërron skanimin
  dhjetëra herë.
- Një tast që e mban tashmë një program tjetër raportohet (`... unavailable: another program already
  has this key`) dhe të tjerët vazhdojnë të funksionojnë. Një buton reklamon vetëm një tast që u
  regjistrua vërtet.
- Tastet janë të fiksuara në kod (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); analizuesi
  pranon F1-F12 me `ctrl`, `alt` dhe `shift`. Jashtë Windows nuk ka taste globale
  dhe dritarja e thotë këtë.
- **Mark** regjistron pozicionin e tanishëm të kamerës (atë të kuadrit të fundit të vendosur) dhe shfaq "Marked MN.
  Marked spots are on the map and saved with the level." Para se të jetë vendosur ndonjë kuadër
  thotë se nuk ka ku të shënohet. Pikat e shënuara vizatohen në hartën e dritares dhe në atë të mbivendosjes si
  katrorë qelibar me etiketën `M1`, `M2`, …, listohen nën pikat e dobëta, numërohen në rreshtin e
  statistikave të mbivendosjes dhe ruhen me nivelin (më poshtë).

## Mbivendosja {#the-overlay}

Një panel i vogël i ngjitur mbi lojë që këshilla të jetë aty ku sytë janë tashmë.

- Pa kornizë, gjithmonë sipër, dritare mjeti (jo në taskbar ose Alt+Tab), transparente ndaj
  hyrjes në Qt dhe e bërë që lë klikimet të kalojnë në Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), ndaj një
  klikim i menduar për lojën nuk gëlltitet kurrë. Shfaqet pa marrë fokusin.
- Në këndin lart djathtas të ekranit kryesor, 18 px nga skajet; 214 x 358 px.
- Hapet kur nis një skanim (nëse "Show feedback over the game" është ndezur), mbyllet kur ai ndalon.
- **Kërkon modalitetin borderless windowed**: asgjë nuk mund të vizatojë mbi ekranin e plotë ekskluziv - jo kjo,
  jo mbivendosja e Steam, jo ajo e Discord.

Nga lart poshtë shfaq:

| Elementi | Përmbajtja |
|---|---|
| Harta e mbulimit | 190 px, e njëjta hartë si në dritare por më e trashë, 120 x 120, me rrugën, unazat e pikave të dobëta dhe pikat e shënuara |
| Shëndeti | i njëjti tekst dhe ngjyrë si rreshti i shëndetit të dritares |
| Statistikat | `N placed · M to revisit · X m`, me `· K marked` kur ka të tilla |
| Shiriti **movement** | si shiriti i shpejtësisë së ecjes i dritares: ndryshimi i pamjes i kuadrit të fundit mbi pragun në përdorim, plot kur kuadri tjetër do të mbahet |
| Shiriti **sharpness** | mprehtësia relative ndaj medianës së kësaj kapjeje: jeshile nga 0.75, qelibar nga 0.45, e kuqe poshtë |
| Këshilla | një udhëzim, jeshile / qelibar / e kuqe (me të trasha kur nuk është "ok") - shihni [cilësinë e kuadrit](reconstruction-capture.md#frame-quality-and-advice) |
| Tastet | tastet e regjistruara |

Nëse përditësimi i mbivendosjes ndonjëherë hedh gabim, kalon në një panel të kuq **"Feedback stopped"** që thotë
se çdo gjë e shfaqur më parë është e vjetruar, se skanimi vazhdon dhe dritarja kryesore është
ende e saktë, me gabimin dhe një numërues. Një panel që ngriu duke qenë jeshil përndryshe do të vazhdonte të
lexohej si konfirmim.

## Ruajtja {#saving}

**Save level…** e shkruan rindërtimin si `.glb` (shihni [Dalja .glb](glb-output.md)).
Nëse vëllimi nuk jep sipërfaqe, "Nothing to save" shpjegon se ndjekja ndoshta humbi
për pjesën më të madhe të skanimit. Në sukses: "Written to <path> ... Load it in 3DHeat through the Level
panel.", duke emëruar edhe skedarin e shenjave kur ka pika të shënuara.

Pikat e shënuara shkruhen pranë nivelit si **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` është në koordinatat e vetë nivelit (shkalla e GLB-së e zbatuar, ndaj një shenjë qëndron mbi rrjetën
mbi të cilën u bë), `metres` në metra; `number` përputhet me `M1`, `M2`, … në dritare. Kur
shkalla u gjet në një kuadër kyç të mëvonshëm ([Shkalla](reconstruction-pose.md#scale)), të dyja e përfshijnë atë
faktor.

Ndalimi i një skanimi mban atë që u mblodh; një **Start** i ri e hedh skanimin e mëparshëm.
**Mbyllja e dritares nuk pyet për ruajtje**: ndalon skanimin, liron tastet dhe
mbyll mbivendosjen.
