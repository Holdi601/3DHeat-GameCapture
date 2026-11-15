---
title: Scanvinduet
nav_order: 1
lang: "da"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Scanvinduet {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kode: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Vinduet er en tynd visning over `scan/session.py` og `scan/reconstruct.py`; det ejer ingen
scanne- eller geometrilogik.

## Opstart {#starting-up}

1. **Opdateringstjek** - se [Opdateringer](updates.md).
2. **Afhængighedstjek** - hver pakke scanneren har brug for, tjekkes, før noget importeres; manglende
   pakker listes med hvad de bruges til og downloadstørrelsen, og installeres først efter "Download and install". Annuller
   afslutter uden at ændre noget. Se [Kørsel og afhængigheder](runtime.md#first-run-preflight).
3. **Vindue** - "3DHeat — Level scanner", 1420 x 900, Qt's Fusion-stil.
4. **Hardwaretjek** - den bedste inferensbackend vælges, dybdemodellen indlæses, og dens gennemstrømning måles på 6
   billeder; vurderingsboksen øverst til venstre siger, hvordan scanningen bliver (se [Kørsel](runtime.md#what-to-expect-from-this-machine)).
5. **Globale genveje** registreres til sidst.

### Når der ingen dybdemodel er endnu {#when-there-is-no-depth-model-yet}

Hvis `models/` ikke indeholder nogen `depth-*.onnx`, står vurderingen til **"One more thing to set up."**, Start er
deaktiveret, og en knap **Set up the depth model** dukker op. Den:

- tjekker for PyTorch, `transformers` og `onnxscript` (omkring 945 MB tilsammen), og spørger, før de installeres;
- kører `tools/export_onnx.py --size small` som en separat proces (så PyTorch aldrig bliver i scannerens hukommelse), med en
  grænse på 30 minutter. Vinduet reagerer ikke, mens den kører;
- ved succes kører hardwaretjekket igen; ved fejl vises de sidste 600 tegn af konverterens output.

Når flere modeller er til stede, vælges der **efter licens, ikke efter filnavn**: `depth-small-*`
(Apache-2.0, kommerciel brug tilladt), når der er en, derefter Base, og så Large (begge ikke-kommercielle). Vurderingsboksen og
den grå linje under knapperne navngiver filen i brug, dens licens og eventuelle andre modelfiler, der findes og ikke bruges - for
eksempel `Depth model: depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used: depth-base-518.onnx`.
For at scanne med Base, flyt Small-filen ud af `models/`.

## Venstre kolonne: indstillinger {#left-column-settings}

| Gruppe | Kontrol | Standard | Interval / værdier | Hvad den gør |
|---|---|---|---|---|
| (top) | Vurderingsboks | "Checking your graphics card…" | farvet grøn, gul eller rød efter niveau | Overskrift, `<device> via <API> — N views per second`, én note og `Depth model: <file> (<licence>)` |
| Hvad der scannes | Kilde | Hele skærmen | Hele skærmen, Et vindue, En videofil | Hvor billederammerne kommer fra |
| | Hvilken | `1` | skærmnummer / vinduestitel / sti til en video | `monitor:<n>`, `window:<title>`, eller en filsti |
| | Vælg fil… | vist for video | `*.mp4 *.mkv *.avi *.mov` | Udfylder stien |
| Hvor omhyggeligt | Forudindstilling | Balanced | Draft, Balanced, Detailed | Optageopløsning og hvor selektiv nøgleramme-valget er (nedenfor); et enlinjes resumé vises under den |
| | Spillets synsfelt | 90° | 30-140° | Spillets **vandrette** synsfelt. For smalt, og banen rekonstrueres dybere, end den er; for bredt, og den bliver flad. Racerspil ligger nærmere 65° |
| | Overfladedetalje | 0,25 m | 0,05-2,0 m, trin 0,05 | Voxelstørrelsen på overfladen. Mindre er finere og tungere |
| Stop efter | Tid | ingen grænse | 0-120 min | Afslutter scanningen efter så længe (0 = ingen grænse) |
| | Gemte views | 3000 | 0-100.000 | Afslutter scanningen efter så mange nøglerammer, som en hukommelsesvagt (0 = ingen grænse) |
| Hvad der ignoreres | Ignorer HUD og alt på kameraet | til | | Lærer og maskerer HUD'en, sigtekornet, våbnet, motorhjelmen, førerhuset ([Optagelse](reconstruction-capture.md#what-is-not-the-world)). Linjen under den siger, hvad detektoren lige nu afgør |
| Mens du spiller | Vis feedback over spillet | til | | Åbner den klikgennemsigtige overlejring under scanningen. Hintet under den: kør spillet i **kantløs fuldskærm**; eksklusiv fuldskærm kan ikke tegnes over af noget |
| Køretelemetri (Forza) | Lyt efter positionsdata | fra | | Tager kamerastien fra Forzas Data Out i stedet for at estimere den ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Data Out-porten |
| | (statuslinje) | | | `N packets — poses come from the game, not from the picture`, eller `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Starter eller stopper; viser genvejstasten, når den blev registreret |
| | **Set up the depth model** | skjult | | Se ovenfor |
| | **Save level…** | deaktiveret | | Aktiveres efter en scanning, der gav overfladevoxels; spørger efter et filnavn (standard `scan.glb`) |
| | (grå linje) | | | `Model: <file> (<licence>) · Available: <backends>`, plus opsætningsnoter, såsom installation af `onnxruntime-gpu` |

### Forudindstillingerne {#the-presets}

| Forudindstilling | Optagelsens længste side | Keep quantile | Startgrænse | Vist resumé |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Hurtig og grov. God til at tjekke en rute før en rigtig scanning. |
| Balanced | 960 px | 0,65 | 0,010 | Det sædvanlige valg. Gå i et normalt tempo. |
| Detailed | 1280 px | 0,40 | 0,004 | Langsom og grundig. Gå bevidst, og drej blidt. |

Keep quantile betyder "behold en ramme, når den ændrede sig mere end denne kvantil af de sidste 240 rammers ændringer" - Draft
beholder cirka de travleste 15%, Detailed de travleste 60%. Se [Nøglerammer](reconstruction-capture.md#keyframes).

### Indstillinger der er låst i vinduet {#settings-that-are-fixed-in-the-window}

Vinduet rekonstruerer altid under scanning, bruger en kamerahøjde på **1,15 m** til gulvplanens skala (gåværdien 1,70 m kan ikke
vælges), og lader backend-stigen vælge GPU'en. Det er `ScanSettings`-felterne `camera_height` og `prefer_backend`, som kun et script kan ændre.

## Højre kolonne: hvad scanningen laver {#right-column-what-the-scan-is-doing}

| Element | Viser |
|---|---|
| **What the camera sees** | den sidste nøgleramme |
| **Shape it is reading** | dens forudsagte dybde, farvet med Turbo-farvekortet, normaliseret mellem den 2. og 98. percentil af den ramme (så én himmelpixel ikke udjævner området) |
| **Coverage — where you have been, and how well** | et planbillede (se nedenfor) |
| **Worth another look** | de svage pletter, nummereret så de passer til ringene på kortet, hver med en instruks; værst (størst) først, højst 8; derefter de pletter du har markeret (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Gangfartsbar | `walk speed — N% of the way to the next view`: sidste rammes billedændring divideret med **den grænse, der bruges** - præsetets startværdi for de første 30 rammer, den tilpassede værdi efter det ([Nøglerammer](reconstruction-capture.md#keyframes)) |
| Sundhedslinje | sporingens sundhed, eller en optageadvarsel (nedenfor) |
| Størrelseslinje | `Size: ...`, hvordan banens skala blev fastlagt, eller hvorfor den ikke blev ([Skala](reconstruction-pose.md#scale)) |
| Statistiklinje | `views  frames  dropped  depth-per-second  seconds`, og mens der rekonstrueres `placed  cells  % well seen  metres`, plus `recovered` og `loops closed`, når en af dem ikke er nul |
| Genvejslinje | de registrerede taster, eller hvorfor de ikke kunne registreres |
| Hintlinje (gul) | live-råd (nedenfor), scanningens sidste besked og mærkninger |

### Dækningskortet {#the-coverage-map}

Tegnes igen hvert 900 ms på en baggrundstråd (aldrig på grænsefladetråden), i 200 x 200 celler skaleret til 420 px:

- hver kolonne i dækningsgitteret tager den **bedste** observationskvalitet i den (så et godt set gulv ikke males gult af et dårligt set loft ovenover);
- skalaen går rød (dårlig) - gul (tynd) - gul-grøn (acceptabel) - grøn (god);
- aldrig observerede celler er en tydelig mørkegrå, så et uudforsket hjørne ikke ser ud som et dårligt scannet;
- den gåede sti tegnes som en tynd lys linje, den aktuelle position som en hvid prik;
- svage pletter er hvide ringe med deres nummer;
- pletter du har markeret er gule firkanter mærket `M1`, `M2`, …

Hvordan kvalitet og svage pletter beregnes: [Fusion, dækning og farve](reconstruction-fusion-and-texture.md#coverage).

### Sundhedslinjen {#the-health-line}

| Sporingssundhed (placerede rammer / rammer) | Tekst | Farve |
|---|---|---|
| ingen rammer endnu | Waiting for the first frame. | grå |
| 90% eller mere | Tracking well — N of M frames placed. | grøn |
| 60% eller mere | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | gul |
| under 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rød |

En optageadvarsel fra dækningsgitteret erstatter den (rød, når scanningen vurderes som ikke rekonstruerbar, ellers gul): næsten ingen
parallakse, alt set fra mere end 25 m, eller tynd parallakse. Se [Dækning](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Hintlinjen {#the-hint-line}

| Betingelse | Hint |
|---|---|
| mere end halvdelen af rammerne droppet, efter 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| færre end 0,3 views gemt i sekundet, efter 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| mere end 8 views gemt i sekundet, efter 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| scanningen sluttede | sessionens besked: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, eller `failed: <error>` |

## Genvejstaster {#hotkeys}

Registreret hos Windows (`RegisterHotKey`), så de virker, mens spillet har fokus. At alt-tabbe ud af et fuldskærmsspil er netop det, der ødelægger en optagelse.

| Taster | Handling |
|---|---|
| **Ctrl+Alt+F9** | Start / stop scanning |
| **Ctrl+Alt+F10** | Marker dette sted, så du kan besøge det igen (under scanning) |
| **Ctrl+Alt+F11** | Vis / skjul overlejringen (skifter afkrydsningen "Show feedback over the game") |

- De registreres én gang, når vinduet åbnes, og frigives, når det lukkes; mens de er registreret, er disse tastkombinationer taget fra alle andre programmer, inklusive spillet. F-taster med to modifikatorer blev valgt, fordi spil sjældent bruger dem.
- Automatisk gentagelse undertrykkes (`MOD_NOREPEAT`), så et holdt tastetryk ikke skifter scanningen snesevis af gange.
- En tast, et andet program allerede har, meldes (`... unavailable: another program already has this key`), og de andre virker stadig. En knap annoncerer kun en tast, der faktisk blev registreret.
- Tasterne er fastlagt i koden (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); parseren accepterer F1-F12 med `ctrl`, `alt` og `shift`. Uden for Windows findes der ingen globale genveje, og vinduet siger det.
- **Mark** gemmer den aktuelle kameraposition (den sidst placerede rammes) og viser "Marked MN. Marked spots are on the map and saved with the level." Før nogen ramme er placeret, siger den, at der ikke er noget at markere. Markerede pletter tegnes på vinduets kort og overlejringens som gule firkanter mærket `M1`, `M2`, …, listes under de svage pletter, tælles i overlejringens statistiklinje og gemmes med banen (nedenfor).

## Overlejringen {#the-overlay}

En lille panel fastgjort over spillet, så feedbacken er der, hvor øjnene allerede er.

- Rammeløs, altid øverst, et værktøjsvindue (ikke på proceslinjen eller i alt-tab), gennemsigtig for input i Qt og klikgennemsigtig i Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), så et klik beregnet til spillet aldrig opsluges. Vises uden at tage fokus.
- Øverste højre hjørne af den primære skærm, 18 px fra kanterne; 214 x 358 px.
- Åbner, når en scanning starter (hvis "Show feedback over the game" er til), og lukker, når den stopper.
- **Kræver kantløs fuldskærm**: intet kan tegnes over eksklusiv fuldskærm - hverken dette, Steams overlejring eller Discords.

Fra top til bund viser den:

| Element | Indhold |
|---|---|
| Dækningskort | 190 px, samme kort som vinduet i et grovere 120 x 120, med stien, ringene for svage pletter og markerede pletter |
| Sundhed | samme tekst og farve som vinduets sundhedslinje |
| Statistik | `N placed · M to revisit · X m`, med `· K marked`, når der er nogen |
| **bevægelses**-bar | samme som vinduets gangfartsbar: sidste rammes billedændring over den grænse, der bruges, fuld når næste ramme vil blive beholdt |
| **skarphedsbar** | skarphed i forhold til denne optagelses egen median: grøn fra 0,75, gul fra 0,45, rød under |
| Råd | én instruks, grøn / gul / rød (fed, når den ikke er "ok") - se [billedkvalitet](reconstruction-capture.md#frame-quality-and-advice) |
| Genveje | de registrerede taster |

Hvis en opdatering af overlejringen nogensinde fejler, skifter den til et rødt **"Feedback stopped"**-panel, der siger, at alt vist før er forældet, at scanningen stadig kører og hovedvinduet stadig er korrekt, med fejlen og en tæller. Et panel, der frøs mens det var grønt, ville ellers blive ved med at læses som bekræftelse.

## Gem {#saving}

**Save level…** skriver rekonstruktionen som en `.glb` (se [.glb-outputtet](glb-output.md)).
Hvis volumenet ikke giver nogen overflade, forklarer "Nothing to save", at sporingen sandsynligvis gik tabt for det meste af scanningen. Ved succes: "Written to <path> ... Load it in 3DHeat through the Level
panel." (Baggrund / bane), og nævner markeringsfilen også, når der er markerede pletter.

Markerede pletter skrives ved siden af banen som **`<name>.marks.json`**:

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

`position` er i banens egne koordinater (GLB'ens skala anvendt, så en markering ligger på det mesh, den blev lavet over), `metres` i meter; `number` svarer til `M1`, `M2`, … i vinduet. Når skalaen blev fundet på en senere nøgleramme ([Skala](reconstruction-pose.md#scale)), inkluderer begge den faktor.

At stoppe en scanning beholder det, der blev samlet; en ny **Start** kasserer den forrige scanning.
**Lukning af vinduet spørger ikke om at gemme**: det stopper scanningen, frigiver genvejstasterne og lukker overlejringen.
