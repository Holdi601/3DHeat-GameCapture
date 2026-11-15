---
title: Skanningsfönstret
nav_order: 1
lang: "sv"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Skanningsfönstret {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Kod: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Fönstret är en tunn vy över `scan/session.py` och `scan/reconstruct.py`; det äger ingen skannings- eller
geometrilogik.

Knapparna, rutorna och raderna i fönstret visas på engelska, så de anges här med samma namn som på skärmen.

## Starta {#starting-up}

1. **Uppdateringskontroll** - se [Uppdateringar](updates.md).
2. **Beroendekontroll** - varje paket skannern behöver kontrolleras innan något importeras; saknade listas med
   vad de är till för och nedladdningens storlek, och installeras först efter "Download and install". Cancel avslutar
   utan att ändra något. Se [Körning och beroenden](runtime.md#first-run-preflight).
3. **Fönster** - "3DHeat — Level scanner", 1420 x 900, Qt:s stil Fusion.
4. **Hårdvarukontroll** - den bästa inferensbackenden väljs, djupmodellen laddas och dess genomströmning mäts på
   6 bildrutor; rutan med domen längst upp till vänster säger hur skanningen kommer att bli (se
   [Körning](runtime.md#what-to-expect-from-this-machine)).
5. **Globala snabbtangenter** registreras sist.

### När det inte finns någon djupmodell än {#when-there-is-no-depth-model-yet}

Om `models/` inte har någon `depth-*.onnx` står domen på **"One more thing to set up."**, Start är avstängd, och en
knapp **Set up the depth model** visas. Den:

- kontrollerar PyTorch, `transformers` och `onnxscript` (ungefär 945 MB tillsammans), och frågar innan den installerar dem;
- kör `tools/export_onnx.py --size small` som en egen process (så PyTorch aldrig ligger kvar i skannerns minne), med en
  gräns på 30 minuter. Fönstret svarar inte medan den körs;
- vid lyckat resultat kör hårdvarukontrollen om; vid misslyckande visas de sista 600 tecknen av konverterarens utdata.

När flera modeller finns väljs de **efter licens, inte efter filnamn**: `depth-small-*` (Apache-2.0, kommersiell användning
tillåten) när en sådan finns, sedan Base, sedan Large (båda ickekommersiella). Domrutan och den grå raden under knapparna
anger filen som används, dess licens, och eventuella andra modellfiler som finns men inte används - till exempel `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. För att skanna med Base, flytta Small-filen ur `models/`.

## Vänsterkolumnen: inställningar {#left-column-settings}

| Grupp | Kontroll | Standard | Intervall / värden | Vad den gör |
|---|---|---|---|---|
| (överst) | Domruta | "Checking your graphics card…" | färgad grön, gul eller röd efter nivå | Rubriken, `<device> via <API> — N views per second`, en anmärkning och `Depth model: <file> (<licence>)` |
| What to scan | Source | Whole screen | Whole screen, A window, A video file | Varifrån bildrutorna kommer |
| | Which | `1` | bildskärmsnummer / fönstertitel / sökväg till en video | `monitor:<n>`, `window:<title>`, eller en filsökväg |
| | Choose file… | visas för video | `*.mp4 *.mkv *.avi *.mov` | Fyller i sökvägen |
| How carefully | Preset | Balanced | Draft, Balanced, Detailed | Upplösning på inspelningen och hur selektiv nyckelbildsvalet är (nedan); en sammanfattning på en rad visas under |
| | Game field of view | 90° | 30-140° | Spelets **horisontella** synfält. För smalt, och banan rekonstrueras djupare än den är; för brett, och den blir platt. Racingspel ligger nära 65° |
| | Surface detail | 0.25 m | 0.05-2.0 m, steg 0.05 | Voxelstorleken på ytan. Mindre är finare och tyngre |
| Stop after | Time | ingen gräns | 0-120 min | Avslutar skanningen efter så lång tid (0 = ingen gräns) |
| | Views kept | 3000 | 0-100 000 | Avslutar skanningen efter så många nyckelbilder, som minnesspärr (0 = ingen gräns) |
| What to ignore | Ignore HUD and anything on the camera | på | | Lär sig och maskerar HUD:en, korshåret, vapnet, motorhuven, hytten ([Inspelning](reconstruction-capture.md#what-is-not-the-world)). Raden under visar vad detektorn just nu bestämmer |
| While you play | Show feedback over the game | på | | Öppnar det klickgenomsläppliga överlägget under skanningen. Tipset under: kör spelet i **borderless windowed** (rutat fönsterläge utan kant); exklusiv helskärm kan inte ritas över av något |
| Racing telemetry (Forza) | Listen for position data | av | | Tar kamerabanan från Forzas Data Out i stället för att uppskatta den ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (port) | 5300 | 1-65535 | Data Out-porten |
| | (status line) | | | `N packets — poses come from the game, not from the picture`, eller `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Startar eller stoppar; visar snabbtangenten när den registrerades |
| | **Set up the depth model** | dold | | Se ovan |
| | **Save level…** | avstängd | | Aktiveras efter en skanning som gav ytvoxlar; frågar efter ett filnamn (standard `scan.glb`) |
| | (grey line) | | | `Model: <file> (<licence>) · Available: <backends>`, plus installationsnoter, till exempel att installera `onnxruntime-gpu` |

### Förinställningarna {#the-presets}

| Förinställning | Inspelningens längsta sida | Behållningskvantil | Startgräns | Sammanfattning som visas |
|---|---|---|---|---|
| Draft | 640 px | 0.85 | 0.020 | Snabb och grov. Bra för att kontrollera en väg innan en riktig skanning. |
| Balanced | 960 px | 0.65 | 0.010 | Det vanliga valet. Gå i normal takt. |
| Detailed | 1280 px | 0.40 | 0.004 | Långsam och noggrann. Gå medvetet och sväng försiktigt. |

Behållningskvantilen betyder "behåll en bildruta när den ändrats mer än denna kvantil av ändringarna i de senaste 240
bildrutorna" - Draft behåller ungefär de mest aktiva 15 %, Detailed de mest aktiva 60 %. Se
[Nyckelbilder](reconstruction-capture.md#keyframes).

### Inställningar som är fasta i fönstret {#settings-that-are-fixed-in-the-window}

Fönstret rekonstruerar alltid medan en skanning pågår, använder en kamerahöjd på **1.15 m** för skalan i markplanet
(gånghöjden 1.70 m kan inte väljas), och låter backendstegen välja GPU. Dessa är `ScanSettings`-fält (`camera_height`,
`prefer_backend`) som bara ett skript kan ändra.

## Högerkolumnen: vad skanningen gör {#right-column-what-the-scan-is-doing}

| Element | Visar |
|---|---|
| **What the camera sees** | den senaste nyckelbilden |
| **Shape it is reading** | dess förutsagda djup, färgat med Turbo-färgkartan, normaliserat mellan den 2:a och 98:e percentilen för bildrutan (så att en enda himmelspixel inte plattar ut omfånget) |
| **Coverage — where you have been, and how well** | en planvy (se nedan) |
| **Worth another look** | de svaga punkterna, numrerade så att de stämmer med ringarna på kartan, var och en med en instruktion; värst (störst) först, högst 8; sedan de punkter du markerat (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Walk-speed bar | `walk speed — N% of the way to the next view`: den senaste bildrutans bildförändring delat med **gränsen i bruk** - förinställningens startvärde för de första 30 bildrutorna, sedan den anpassade gränsen ([Nyckelbilder](reconstruction-capture.md#keyframes)) |
| Health line | spårningens hälsa, eller en varning om inspelningen (nedan) |
| Size line | `Size: ...`, hur banans skala fastställdes, eller varför den inte gjordes ([Skala](reconstruction-pose.md#scale)) |
| Statistics line | `views  frames  dropped  depth-per-second  seconds`, och under rekonstruktionen `placed  cells  % well seen  metres`, plus `recovered` och `loops closed` när något av dem är skilt från noll |
| Hotkey line | de registrerade tangenterna, eller varför de inte kunde registreras |
| Hint line (amber) | direkta råd (nedan), skanningens slutmeddelande och markeringar |

### Täckningskartan {#the-coverage-map}

Ritas om var 900 ms i en bakgrundstråd (aldrig i gränssnittstråden), på 200 x 200 celler skalade till 420 px:

- varje kolumn i täckningsrutnätet tar den **bästa** observationskvaliteten i den (så att ett väl sett golv inte
  målas gult av ett dåligt sett tak ovanför);
- skalan går från rött (dåligt) - gult (tunt) - gulgrönt (godtagbart) - grönt (bra);
- aldrig observerade celler är en tydlig mörkgrå, så att ett outforskat hörn inte ser ut som ett dåligt skannat;
- den gångna vägen ritas som en tunn ljus linje, den aktuella positionen som en vit prick;
- svaga punkter är vita ringar med sitt nummer;
- markerade punkter är gula rutor märkta `M1`, `M2`, ….

Hur kvalitet och svaga punkter beräknas: [Sammanfogning, täckning och färg](reconstruction-fusion-and-texture.md#coverage).

### Hälsoraden {#the-health-line}

| Spårningens hälsa (placerade bildrutor / bildrutor) | Text | Färg |
|---|---|---|
| inga bildrutor än | Waiting for the first frame. | grå |
| 90 % eller mer | Tracking well — N of M frames placed. | grön |
| 60 % eller mer | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | gul |
| under 60 % | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | röd |

En varning om inspelningen från täckningsrutnätet ersätter den (röd när skanningen bedöms inte kunna rekonstrueras,
gul annars): nästan ingen parallax, allt sett från mer än 25 m, eller tunn parallax. Se
[Täckning](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### Råd-raden {#the-hint-line}

| Villkor | Råd |
|---|---|
| mer än hälften av bildrutorna släppta, efter 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| färre än 0,3 vyer behållna per sekund, efter 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| fler än 8 vyer behållna per sekund, efter 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| scan ended | sessionens meddelande: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, eller `failed: <error>` |

## Snabbtangenter {#hotkeys}

Registrerade i Windows (`RegisterHotKey`), så de fungerar medan spelet har fokus. Att alt-tabba ur ett
helskärmsspel är precis det som förstör en inspelning.

| Tangenter | Åtgärd |
|---|---|
| **Ctrl+Alt+F9** | Starta / stoppa skanningen |
| **Ctrl+Alt+F10** | Markera den här platsen att återbesöka (under skanningen) |
| **Ctrl+Alt+F11** | Visa / dölj överlägget (växlar rutan "Show feedback over the game") |

- De registreras en gång, när fönstret öppnas, och släpps när det stängs; medan de är registrerade tas dessa
  tangentkombinationer bort från alla andra program, inklusive spelet. F-tangenter med två modifierare valdes för
  att spel sällan binder dem.
- Automatisk upprepning undertrycks (`MOD_NOREPEAT`), så att en nedhållen tangent inte växlar skanningen tiotals gånger.
- En tangent som ett annat program redan håller rapporteras (`... unavailable: another program already has this key`),
  och de övriga fungerar fortfarande. En knapp visar bara en tangent som faktiskt registrerades.
- Tangenterna är fasta i koden (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); tolkaren tar F1-F12 med `ctrl`, `alt`
  och `shift`. Utanför Windows finns inga globala snabbtangenter, och fönstret säger det.
- **Mark** sparar kamerans nuvarande position (den senast placerade bildrutans) och visar "Marked MN.
  Marked spots are on the map and saved with the level." Innan någon bildruta har placerats säger den att det inte
  finns något att markera. Markerade punkter ritas på fönstrets karta och överlägget som gula rutor märkta `M1`, `M2`,
  …, listas under de svaga punkterna, räknas på överläggets statistikrad, och sparas med nivån (nedan).

## Överlägget {#the-overlay}

En liten panel fäst över spelet, så att återkopplingen finns där ögonen redan är.

- Utan ram, alltid överst, ett verktygsfönster (inte i aktivitetsfältet eller alt-tab), genomskinligt för indata i Qt och
  gjort klickgenomsläppligt i Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), så att ett klick avsett för spelet aldrig
  sväljs. Visas utan att ta fokus.
- Övre högra hörnet på den primära skärmen, 18 px från kanterna; 214 x 358 px.
- Öppnas när en skanning startar (om "Show feedback over the game" är på), stängs när den stoppas.
- **Kräver borderless windowed-läge**: ingenting kan ritas över exklusiv helskärm - varken detta, Steams överlägg eller
  Discords.

Uppifrån och ned visas:

| Element | Innehåll |
|---|---|
| Coverage map | 190 px, samma karta som fönstret i grövre 120 x 120, med vägen, de svaga punkternas ringar och de markerade punkterna |
| Health | samma text och färg som fönstrets hälsorad |
| Stats | `N placed · M to revisit · X m`, med `· K marked` när någon finns |
| **movement**-stapel | samma som fönstrets gånghastighetsstapel: den senaste bildrutans bildförändring över gränsen i bruk, full när nästa bildruta kommer att behållas |
| **sharpness**-stapel | skärpan i förhållande till denna inspelnings egen median: grön från 0.75, gul från 0.45, röd under |
| Advice | en instruktion, grön / gul / röd (fetstil när den inte är "ok") - se [bildrutekvalitet och råd](reconstruction-capture.md#frame-quality-and-advice) |
| Hotkeys | de registrerade tangenterna |

Om uppdateringen av överlägget någon gång kastar ett fel byter det till en röd panel **"Feedback stopped"** som säger
att allt som visats tidigare är inaktuellt, att skanningen fortfarande pågår och att huvudfönstret fortfarande är rätt,
med felet och en räknare. En panel som frös medan den var grön skulle annars fortsätta att läsas som en bekräftelse.

## Spara {#saving}

**Save level…** skriver rekonstruktionen som en `.glb` (se [`.glb`-utdata](glb-output.md)).
Om volymen inte ger någon yta står "Nothing to save" och förklarar att spårningen troligen tappades under större delen av
skanningen. Vid lyckat resultat: "Written to <path> ... Load it in 3DHeat through the Level
panel.", och anger även markeringsfilen om det finns markerade punkter.

Markerade punkter skrivs bredvid nivån som **`<name>.marks.json`**:

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

`position` är i nivåns egna koordinater (GLB:ens skala tillämpad, så en markering ligger på den mesh den gjordes över),
`metres` i meter; `number` motsvarar `M1`, `M2`, … i fönstret. När skalan hittades på en senare nyckelbild
([Skala](reconstruction-pose.md#scale)) ingår den faktorn i båda.

Att stoppa en skanning behåller det som samlats in; en ny **Start** kasserar den föregående skanningen.
**Att stänga fönstret frågar inte om att spara**: det stoppar skanningen, släpper snabbtangenterna och stänger överlägget.
