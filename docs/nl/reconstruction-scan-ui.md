---
title: "Het scanvenster"
nav_order: 1
lang: "nl"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# Het scanvenster {#the-scan-window}

```bash
python -m heat3d_capture.ui        # or double-click scan.bat
```

Code: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
Het venster is een dunne weergave van `scan/session.py` en `scan/reconstruct.py`; het bevat geen
scan- of geometrielogica.

## Opstarten {#starting-up}

1. **Updatecontrole** - zie [Updates](updates.md).
2. **Afhankelijkheidscontrole** - elk pakket dat de scanner nodig heeft, wordt gecontroleerd voordat iets
   wordt geïmporteerd; ontbrekende pakketten worden vermeld met waarvoor ze dienen en de downloadgrootte, en
   pas geïnstalleerd na "Download and install". Annuleren sluit af zonder iets te veranderen. Zie
   [Runtime en afhankelijkheden](runtime.md#first-run-preflight).
3. **Venster** - "3DHeat — Level scanner", 1420 x 900, Qt's Fusion-stijl.
4. **Hardwarecontrole** - de beste inferentiebackend wordt gekozen, het dieptemodel wordt geladen en de
   doorvoer wordt gemeten op 6 beelden; het oordeelvak linksboven zegt hoe de scan zal zijn (zie
   [Runtime](runtime.md#what-to-expect-from-this-machine)).
5. **Globale sneltoetsen** worden als laatste geregistreerd.

### Wanneer er nog geen dieptemodel is {#when-there-is-no-depth-model-yet}

Als `models/` geen `depth-*.onnx` bevat, staat het oordeel op **"One more thing to set up."**, is Start
uitgeschakeld, en verschijnt een knop **Set up the depth model**. Die:

- controleert op PyTorch, `transformers` en `onnxscript` (samen ongeveer 945 MB), en vraagt of ze
  geïnstalleerd mogen worden;
- draait `tools/export_onnx.py --size small` als apart proces (zodat PyTorch nooit in het geheugen van de
  scanner blijft), met een limiet van 30 minuten. Het venster reageert niet terwijl het draait;
- herhaalt bij succes de hardwarecontrole; bij mislukking toont het de laatste 600 tekens van de uitvoer
  van de converter.

Wanneer er meerdere modellen aanwezig zijn, wordt de keuze **op licentie gemaakt, niet op bestandsnaam**:
`depth-small-*` (Apache-2.0, commercieel gebruik toegestaan) wanneer die er is, dan Base, dan Large (beide
niet-commercieel). Het oordeelvak en de grijze regel onder de knoppen noemen het gebruikte bestand, zijn
licentie, en alle andere aanwezige modelbestanden die niet gebruikt worden - bijvoorbeeld `Depth model:
depth-small-518.onnx (Apache-2.0, commercial use permitted); also present, not used:
depth-base-518.onnx`. Om met Base te scannen, verplaats je het Small-bestand uit `models/`.

## Linkerkolom: instellingen {#left-column-settings}

| Groep | Bediening | Standaard | Bereik / waarden | Wat het doet |
|---|---|---|---|---|
| (boven) | Oordeelvak | "Checking your graphics card…" | groen, oranje of rood naar niveau gekleurd | Kop, `<device> via <API> — N views per second`, één opmerking en `Depth model: <file> (<licence>)` |
| Wat scannen | Bron | Hele scherm | Hele scherm, Een venster, Een videobestand | Waar de beelden vandaan komen |
| | Welke | `1` | schermnummer / vensternaam / pad naar een video | `monitor:<n>`, `window:<title>`, of een bestandspad |
| | Choose file… | zichtbaar bij video | `*.mp4 *.mkv *.avi *.mov` | Vult het pad in |
| Hoe zorgvuldig | Voorinstelling | Balanced | Draft, Balanced, Detailed | Resolutie van de opname en hoe selectief de keyframes zijn (hieronder); een samenvatting van één regel staat eronder |
| | Game field of view | 90° | 30-140° | Het **horizontale** gezichtsveld van het spel. Te smal en het level wordt dieper gereconstrueerd dan het is; te breed en het wordt platgedrukt. Racespellen liggen dichter bij 65° |
| | Surface detail | 0,25 m | 0,05-2,0 m, stap 0,05 | Voxelgrootte van het oppervlak. Kleiner is fijner en zwaarder |
| Stop na | Tijd | geen limiet | 0-120 min | Beëindigt de scan na zoveel tijd (0 = geen limiet) |
| | Views kept | 3000 | 0-100.000 | Beëindigt de scan na zoveel keyframes, als geheugenbewaking (0 = geen limiet) |
| Wat negeren | Ignore HUD and anything on the camera | aan | | Leert en maskeert de HUD, het vizier, het wapen, de motorkap, de cockpit ([Opname](reconstruction-capture.md#what-is-not-the-world)). De regel eronder zegt wat de detector nu beslist |
| Tijdens het spelen | Show feedback over the game | aan | | Opent de klik-doorlatende overlay tijdens het scannen. De hint eronder: draai het spel in **randloos venster**; exclusief volledig scherm kan door niets worden overtekend |
| Racetelemetrie (Forza) | Listen for position data | uit | | Neemt het cameraspoor van Forza's Data Out in plaats van het te schatten ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (poort) | 5300 | 1-65535 | De Data Out-poort |
| | (statusregel) | | | `N packets — poses come from the game, not from the picture`, of `no packets yet — check Data Out is on and pointed at 127.0.0.1` |
| | **Start scanning** / **Stop scanning** | | | Start of stopt; toont de sneltoets als die geregistreerd werd |
| | **Set up the depth model** | verborgen | | Zie hierboven |
| | **Save level…** | uitgeschakeld | | Ingeschakeld na een scan die oppervlaktevoxels opleverde; vraagt om een bestandsnaam (standaard `scan.glb`) |
| | (grijze regel) | | | `Model: <file> (<licence>) · Available: <backends>`, plus installatienotities zoals het installeren van `onnxruntime-gpu` |

### De voorinstellingen {#the-presets}

| Voorinstelling | Lange zijde van de opname | Behoud-quantiel | Startdrempel | Getoonde samenvatting |
|---|---|---|---|---|
| Draft | 640 px | 0,85 | 0,020 | Snel en ruw. Goed om een route te controleren voor een echte scan. |
| Balanced | 960 px | 0,65 | 0,010 | De gebruikelijke keuze. Loop in een normaal tempo. |
| Detailed | 1280 px | 0,40 | 0,004 | Traag en grondig. Loop bewust en draai rustig. |

Het behoud-quantiel betekent "houd een beeld wanneer het meer veranderde dan dit quantiel van de veranderingen
van de laatste 240 beelden" - Draft houdt ruwweg de drukste 15%, Detailed de drukste 60%. Zie
[Keyframes](reconstruction-capture.md#keyframes).

### Instellingen die vast in het venster zitten {#settings-that-are-fixed-in-the-window}

Het venster reconstrueert altijd tijdens het scannen, gebruikt een camerahoogte van **1,15 m** voor de schaal
van het grondvlak (de loophoogte van 1,70 m is niet te kiezen), en laat de backendladder de GPU kiezen. Dit
zijn `ScanSettings`-velden (`camera_height`, `prefer_backend`) die alleen een script kan veranderen.

## Rechterkolom: wat de scan doet {#right-column-what-the-scan-is-doing}

| Element | Toont |
|---|---|
| **What the camera sees** | het laatste keyframe |
| **Shape it is reading** | zijn voorspelde diepte, gekleurd met de Turbo-kleurenkaart, genormaliseerd tussen het 2e en 98e percentiel van dat beeld (zodat één lucht-pixel het bereik niet platdrukt) |
| **Coverage — where you have been, and how well** | een bovenaanzicht (zie hieronder) |
| **Worth another look** | de zwakke plekken, genummerd naar de ringen op de kaart, elk met een instructie; de slechtste (grootste) eerst, hoogstens 8; daarna de plekken die je hebt gemarkeerd (`M1.  Marked by you, at x …, z … m — drive past again.`) |
| Loopsnelheidsbalk | `walk speed — N% of the way to the next view`: de beeldverandering van het laatste frame gedeeld door de **gebruikte drempel** - de startwaarde van de voorinstelling voor de eerste 30 beelden, daarna de aangepaste ([Keyframes](reconstruction-capture.md#keyframes)) |
| Gezondheidsregel | trackinggezondheid, of een opnamewaarschuwing (hieronder) |
| Groottregel | `Size: ...`, hoe de schaal van het level werd vastgelegd of waarom niet ([Schaal](reconstruction-pose.md#scale)) |
| Statistiekregel | `views  frames  dropped  depth-per-second  seconds`, en tijdens het reconstrueren `placed  cells  % well seen  metres`, plus `recovered` en `loops closed` wanneer een van beide niet nul is |
| Sneltoetsregel | de geregistreerde toetsen, of waarom ze niet geregistreerd konden worden |
| Hintregel (oranje) | advies tijdens het scannen (hieronder), het eindbericht van de scan, en markeringen |

### De dekkingskaart {#the-coverage-map}

Elke 900 ms opnieuw getekend op een achtergronddraad (nooit op de interfacedraad), op 200 x 200 cellen geschaald
naar 420 px:

- elke kolom van het dekkingsraster neemt de **beste** observatiekwaliteit erin (zodat een goed gezien vloer niet
  oranje wordt gekleurd door een slecht gezien plafond erboven);
- de schaal loopt van rood (slecht) - oranje (dun) - geel (acceptabel) - groen (goed);
- nooit geobserveerde cellen zijn een apart donkergrijs, zodat een onontgonnen hoek niet als slecht gescand leest;
- het gelopen pad is een dunne lichte lijn, de huidige positie een witte stip;
- zwakke plekken zijn witte ringen met hun nummer;
- gemarkeerde plekken zijn oranje vierkanten met `M1`, `M2`, ….

Hoe kwaliteit en zwakke plekken berekend worden: [Fusie, dekking en kleur](reconstruction-fusion-and-texture.md#coverage).

### De gezondheidsregel {#the-health-line}

| Trackinggezondheid (geplaatste frames / frames) | Tekst | Kleur |
|---|---|---|
| nog geen frames | Waiting for the first frame. | grijs |
| 90% of meer | Tracking well — N of M frames placed. | groen |
| 60% of meer | Tracking is patchy — N of M frames could not be placed. Turn more slowly. | oranje |
| minder dan 60% | Losing track — only N of M frames placed. Move slowly, and avoid blank walls and sky. | rood |

Een opnamewaarschuwing van het dekkingsraster vervangt die (rood wanneer de scan als niet te reconstrueren
wordt beoordeeld, anders oranje): bijna geen parallax, alles van meer dan 25 m gezien, of dunne parallax. Zie
[Dekking](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### De hintregel {#the-hint-line}

| Voorwaarde | Hint |
|---|---|
| meer dan de helft van de frames weggelaten, na 6 s | Falling behind — N frames dropped ... Try Draft quality, or a coarser surface detail. |
| minder dan 0,3 views kept per seconde, na 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. |
| meer dan 8 views kept per seconde, na 8 s | Keeping a lot. Slow down a little for cleaner geometry. |
| scan beëindigd | het bericht van de sessie: `stopped`, `finished`, `reached the Ns limit`, `reached N keyframes`, of `failed: <error>` |

## Sneltoetsen {#hotkeys}

Geregistreerd bij Windows (`RegisterHotKey`), dus ze werken terwijl het spel de focus heeft. Alt-tabben uit een
volledig scherm spel is precies wat een opname verpest.

| Toetsen | Actie |
|---|---|
| **Ctrl+Alt+F9** | Start / stop scannen |
| **Ctrl+Alt+F10** | Deze plek markeren om terug te komen (tijdens het scannen) |
| **Ctrl+Alt+F11** | Overlay tonen / verbergen (wisselt het vakje "Show feedback over the game") |

- Ze worden één keer geregistreerd, wanneer het venster opent, en vrijgegeven wanneer het sluit; zolang ze
  geregistreerd zijn, zijn deze toetscombinaties afgenomen van elk ander programma, inclusief het spel. F-toetsen
  met twee modifiers zijn gekozen omdat spellen die zelden gebruiken.
- Automatisch herhalen wordt onderdrukt (`MOD_NOREPEAT`), zodat een ingedrukte toets de scan niet tientallen keren
  laat wisselen.
- Een toets die een ander programma al vasthoudt wordt gemeld (`... unavailable: another program already has this
  key`) en de andere werken nog steeds. Een knop adverteert alleen een toets die echt geregistreerd is.
- De toetsen zijn in de code vastgelegd (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); de parser accepteert
  F1-F12 met `ctrl`, `alt` en `shift`. Buiten Windows zijn er geen globale sneltoetsen en het venster zegt dat.
- **Mark** legt de huidige cameraplek vast (die van het laatst geplaatste frame) en toont "Marked MN. Marked spots
  are on the map and saved with the level." Voordat een frame geplaatst is, zegt het dat er niets te markeren valt.
  Gemarkeerde plekken staan op de kaart van het venster en op die van de overlay als oranje vierkanten met `M1`,
  `M2`, …, staan in de lijst onder de zwakke plekken, tellen mee in de statistiekregel van de overlay, en worden
  bewaard bij het level (hieronder).

## De overlay {#the-overlay}

Een klein paneel dat over het spel is vastgezet, zodat de feedback is waar de ogen al zijn.

- Zonder rand, altijd bovenaan, een gereedschapsvenster (niet in de taakbalk of alt-tab), in Qt doorzichtig voor
  invoer en in Windows klik-doorlatend (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), zodat een klik die voor het spel
  bedoeld is nooit wordt opgevangen. Wordt getoond zonder de focus te nemen.
- Rechtsboven op het primaire scherm, 18 px van de randen; 214 x 358 px.
- Opent wanneer een scan start (als "Show feedback over the game" aan staat), sluit wanneer hij stopt.
- **Vereist randloze-vensterstand**: niets kan over exclusief volledig scherm tekenen - niet dit, niet de Steam-overlay,
  niet die van Discord.

Van boven naar beneden toont het:

| Element | Inhoud |
|---|---|
| Dekkingskaart | 190 px, dezelfde kaart als het venster maar op een grover 120 x 120, met het pad, de ringen van zwakke plekken en gemarkeerde plekken |
| Gezondheid | dezelfde tekst en kleur als de gezondheidsregel van het venster |
| Statistieken | `N placed · M to revisit · X m`, met `· K marked` wanneer er zijn |
| **beweging**-balk | hetzelfde als de loopsnelheidsbalk van het venster: de beeldverandering van het laatste frame over de gebruikte drempel, vol wanneer het volgende frame behouden wordt |
| **scherpte**-balk | scherpte ten opzichte van de eigen mediaan van deze opname: groen vanaf 0,75, oranje vanaf 0,45, rood eronder |
| Advies | één instructie, groen / oranje / rood (vet wanneer niet "ok") - zie [beeldkwaliteit en advies](reconstruction-capture.md#frame-quality-and-advice) |
| Sneltoetsen | de geregistreerde toetsen |

Als het bijwerken van de overlay ooit een fout gooit, schakelt hij over naar een rood paneel **"Feedback stopped"**
dat zegt dat alles wat eerder getoond werd verouderd is, dat de scan nog loopt en het hoofdvenster nog klopt, met de
fout en een teller. Een paneel dat groen bevroren is, zou anders blijven gelden als bevestiging.

## Opslaan {#saving}

**Save level…** schrijft de reconstructie als `.glb` (zie [De .glb-uitvoer](glb-output.md)). Als het volume geen
oppervlak oplevert, verklaart "Nothing to save" dat het volgen waarschijnlijk voor het grootste deel van de scan
verloren ging. Bij succes: "Written to <path> ... Load it in 3DHeat through the Level panel.", en noemt het ook het
markeringenbestand wanneer er gemarkeerde plekken zijn.

Gemarkeerde plekken worden naast het level geschreven als **`<name>.marks.json`**:

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

`position` staat in de eigen coördinaten van het level (de schaal van de GLB toegepast, zodat een markering op het
mesh zit waarop ze gemaakt werd), `metres` in meters; `number` komt overeen met `M1`, `M2`, … in het venster. Wanneer
de schaal op een later keyframe is gevonden ([Schaal](reconstruction-pose.md#scale)), bevatten beide die factor.

Een scan stoppen houdt wat verzameld is; een nieuwe **Start** gooit de vorige scan weg. **Het sluiten van het venster
vraagt niet om op te slaan**: het stopt de scan, geeft de sneltoetsen vrij en sluit de overlay.
