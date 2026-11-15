---
title: "Opdrachtenoverzicht"
nav_order: 5
lang: "nl"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Opdrachtenoverzicht {#command-reference}

Alle opdrachten draaien vanuit de map van de repository, met de omgeving van het project:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Opdracht | Doet |
|---|---|
| [`route`](#route) | Legt alleen de posities van een Forza-ronde vast, om de kaart in de bestanden van het spel te vinden |
| [`telemetry`](#telemetry) | Legt elk kanaal vast, een rondebestand per ronde, voor het tabblad Race-analyse |
| [`laps`](#laps) | Leest een bibliotheek met FH Companion-ronden in en schrijft de route en de samples van één baan |
| [`reconstruct`](#reconstruct) | Lost een opname offline op en schrijft een `.glb` |
| [`hud`](#hud) | Leest de eigen acties, doden en het minimapspoor van de speler uit een opname, plus de killfeed |
| [`locate`](#locate) | Waar elk beeld van een opname is genomen, ten opzichte van renders van het level |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Het scanvenster |
| [`python -m heat3d_update`](#updates) | Zoekt naar een update en past die toe |
| [`python tools/export_onnx.py`](#the-model-converter) | Zet het dieptemodel om naar ONNX |

Gestart als `python -m heat3d_capture`, kijkt het eerst of er een nieuwere release is (zie
[Updates](updates.md); `HEAT3D_NO_UPDATE=1` zet dit uit). `--help` na elke opdracht toont de opties:

![heat3d_capture --help](../assets/img/cli-help.svg)

Code: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Luistert naar Forza Data Out en houdt alleen de posities van de auto bij, niets anders: geen
dieptemodel, geen GPU, geen opname. Code: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Optie | Standaard | Betekenis |
|---|---|---|
| `-o`, `--out` | verplicht | Uitvoerpad; het achtervoegsel wordt vervangen, dus `-o lap` schrijft `lap.npz` en `lap.json`. |
| `--port` | `5300` | Poort waar het spel naartoe stuurt (gebonden aan 127.0.0.1). |
| `--seconds` | `0` | Stop na zoveel seconden; `0` loopt door tot Ctrl+C. |

Een positie wordt alleen bewaard zolang het spel een race meldt (`isRaceOn`), de auto sneller
rijdt dan 0,5 m/s, en de positie minstens 0,5 m van de laatst bewaarde positie af ligt. Anders
zou stilstaan in een menu, 60 pakketjes per seconde, het bestand vol zetten met de startlijn. De
tijd van elk sample is de racetijd van het spel, of de kloktijd als die 0 is. De indeling wordt
herkend zoals bij `telemetry` (de auto moet eerst bewegen; zie [Forza](telemetry-forza.md)).

Elke seconde print het aantal ontvangen pakketten, de bewaarde posities en de huidige positie, of
`nothing on port 5300 yet - is Data Out on?`. De route wordt **opgeslagen terwijl je rijdt**: elke 2
seconden zodra er een nieuwe positie is binnengekomen (de tussenpauze groeit tot twintig keer de
duur van de laatste keer opslaan, zodat een heel lange sessie nooit meer dan een twintigste van
haar tijd met schrijven kwijt is), en nog één keer wanneer de recorder om welke reden dan ook
stopt - Ctrl+C, `--seconds`, of een uitzondering. Elke keer schrijft hij eerst `lap.npz.partial` /
`lap.json.partial` en verplaatst die daarna over het echte bestand, zodat de bestanden op schijf
altijd compleet zijn; bij een crash of een afgebroken proces gaan hooguit de laatste paar seconden
verloren. Is er niets bewaard, dan print hij hoe je Data Out aanzet en stopt met code 1.

Uitvoer:

- `lap.npz` - NumPy-arrays `positions` (n x 3, meter), `times`, `speeds` (m/s);
- `lap.json` - leesbaar zonder dit project:

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

De posities zijn de wereldcoördinaten van het spel zelf. Daarmee kun je dezelfde grond terugvinden
in de bestanden van het spel: de opdracht `course` van
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) leest deze JSON en exporteert de
baan waarover de ronde ging.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Elke optie en elk spel staat beschreven op [Telemetrierecorders](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Leest de ronde-bibliotheek die FH Companion bijhoudt en schrijft twee bestanden voor één baan: een
route die aangeeft welk stuk kaart uit het spelarchief moet worden gehaald, en een tabel met elk
sample van elke ronde. Ze worden samen geschreven, zodat ze nooit uit de pas kunnen lopen. Code:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Optie | Standaard | Betekenis |
|---|---|---|
| `course` | geen | Naam van de baan, losjes vergeleken. Laat weg om de bibliotheek te tonen. |
| `-o`, `--out` | de naam van de baan, in kleine letters, spaties als `_` | Uitvoerpad; `.json` en `.csv` worden naast elkaar geschreven. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Waar de banenmappen staan. |
| `--margin` | `80` | Meter die in x en z aan de omvang van de baan wordt toegevoegd in de `bounds` van de route. |

### Lijst {#listing}

Zonder baan print hij het aantal banenmappen en voor elke map het aantal rondebestanden (`*.json`
overal eronder, behalve `course.json`) en de naam van de baan, gevolgd door
`Name one to write it out:  -o <file> <course>`.

### Een baan vinden {#finding-a-course}

Banenmappen heten `<naam> (course_<x>_<z>_to_<x>_<z>)` - start en finish, afgerond. Een baan wordt
gevonden in deze volgorde: de exacte mapnaam; het naamdeel van de mapnaam, zonder hoofdlettergevoel;
een unieke map waarvan de naam de tekst bevat. Meerdere treffers is een fout, en die fout somt ze op.

### Uitlezen {#reading-it}

- `course.json` in de map, als die leesbaar is, geeft de naam en de niet-afgeronde start en finish
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); anders komen ze uit de mapnaam. Een baan wordt
  als circuit gemeld wanneer start en finish minder dan 10 m uit elkaar liggen.
- Elk ander `*.json` onder de map is een ronde (ronden liggen enkele mappen diep - per klasse, auto,
  afstelling, label - en het zoeken is gewoon recursief). Bestanden worden gelezen als UTF-8 met een
  byte-order-mark. Een onleesbare ronde wordt overgeslagen. Ronden worden gesorteerd op hun
  opnametijd.
- Per ronde: `Lap.samples` (elk met `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), en de autoklasse,
  de ordinal, de performance-index, de rondetijd in seconden, de lengte, de opnametijd en de
  stilstaande start.

Hij print een samenvatting (ronden, samples, beste ronde en haar klasse, de omvang in x/y/z).

### Uitvoer {#output}

**`<out>.json`** - dezelfde routevorm als `route` schrijft, zodat de kaartextractor beide aankan:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (uitgebreid met `--margin` in x en
z), en `positions` van de **snelste** ronde (één lijn in plaats van een wolk van alle ronden).

**`<out>.csv`** - elk sample van elke ronde, één rij per stuk:

| Kolom | Betekenis |
|---|---|
| `course` | naam van de baan |
| `lap` | een label per ronde: opnamedatum en -tijd tot de minuut, en de rondetijd |
| `car` | ordinal van de auto |
| `car_class` | letter van de prestatieklasse |
| `pi` | performance-index |
| `lap_seconds` | de tijd van de ronde |
| `speed_kmh` | snelheid in km/u |
| `x`, `y`, `z` | wereldpositie, meter, 3 decimalen |
| `speed_ms` | snelheid, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | zoals FH Companion ze vastlegt |
| `metres` | afstand langs de ronde, 3 decimalen |
| `elapsed` | seconden sinds de eigen start van de ronde, 3 decimalen |

Waarden die geen positie zijn, worden op 4 significante cijfers geschreven; posities krijgen een vast
aantal decimalen, want 4 significante cijfers zou een baan op een raster van één meter vastzetten. De
kolomnamen zijn zo gekozen dat de viewer het bestand zonder aanwijzingen indeelt: `lap` wordt de
sessie (twee ronden van één auto worden nooit samengevoegd), `car` het ding dat beweegt, `car_class`
de groep om op te kleuren, `elapsed` de tijdas (elke ronde loopt gelijk vanaf haar eigen start).

Tot slot print hij een tip om de kaart met GameFiles uit het spel te knippen, met het routebestand of
een expliciet kader.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Lost een opname offline op, waarbij het cameraspoor in één keer wordt opgelost door VGGT. Traag:
minuten per venster op een desktop-GPU. Heeft PyTorch, Hugging Face `transformers` en het pakket
`vggt` nodig, die de scanner niet nodig heeft: ze staan in `requirements-offline.txt`, en de opdracht
controleert of ze er zijn nadat de licentieregel is afgedrukt, en biedt aan wat ontbreekt te
installeren (exitcode 1 als je dat weigert). Volledige beschrijving:
[Offline reconstructie](reconstruction-offline.md).

| Optie | Standaard | Betekenis |
|---|---|---|
| `video` | verplicht | De opname. Exitcode 2 als hij niet bestaat. |
| `-o`, `--out` | verplicht | De `.glb` die wordt geschreven. |
| `--solve-budget` | `260` | Het grootste aantal beelden dat aan de oplosser wordt gegeven. Ze worden gekozen naar hoeveel het beeld verschuift, niet naar de klok. Meer is nauwkeuriger en veel trager. Meer dan 400 geplande beelden wordt geweigerd. |
| `--fuse-interval` | `0.4` | Seconden tussen de beelden die tot geometrie worden samengevoegd. |
| `--model` | `vggt-1b` | Welke VGGT-gewichten worden gebruikt: `vggt-1b` (`facebook/VGGT-1B`, niet-commercieel) of `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, afgeschermd; toegang moet door Meta worden verleend). De licentieregel die eerst wordt afgedrukt is die van het model. |

Hij print eerst de licentieregel van het model, daarna elke fase (`masking`, `planning`, `solving`,
`fusing`, `exporting`) met verstreken seconden en voortgang, en tot slot een samenvatting: opgeloste
camera's, sluitfout, ergste naad, opmerkingen en het geschreven bestand. De exitcode is alleen 0 als
er een bestand is geschreven.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Leest de HUD van het spel uit de eigen opname van de speler, na de wedstrijd: de eigen acties van de
speler uit het puntenpopupje, doden en opstandingen uit de down- en deploy-schermen, het
minimapspoor en de killfeed. Schrijft `<out>.parquet` (spoor en gebeurtenissen, een 3DHeat-tabel),
`<out>.events.jsonl`, `<out>.summary.json`, en `<out>.map.png` + `.map.json` (het minimapmozaïek en
de ankers ervan voor de afbeelding van de kaart in de viewer). Battlefield 6 (`bf6`) is tot nu toe
het enige profiel.

Heeft **ffmpeg en ffprobe** op PATH nodig (`winget install Gyan.FFmpeg`, daarna een nieuwe terminal).

| Optie | Standaard | Betekenis |
|---|---|---|
| `video` | verplicht | De opname. |
| `-o`, `--out` | de naam van de video | Uitvoerpad zonder extensie. |
| `--game` | `bf6` | Wiens HUD er gelezen wordt. |
| `--player` | geraden | De naam van de speler zoals de killfeed die toont, losjes vergeleken. |
| `--fps` | `5` | Minimap-samples per seconde. |
| `--start`, `--seconds` | hele video | Het deel van de opname dat wordt gelezen. |
| `--metres-per-pixel` | geen | De schaal van de minimap, als die bekend is; zonder deze optie staan posities in minimappixels. |
| `--cpu` | uit | Decodeer op de CPU, ook als er een NVIDIA-kaart is. |

Volledige beschrijving: [De HUD uit een opname lezen](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` rendert een level vanaf elke plek waar een speler kan staan en indexeert de renders;
`frames` plaatst elk bemonsterd beeld van een opname erop, aan de hand van het beeld, met het
minimapspoor van de `hud`-opdracht als terugvaloptie; `eval` vergelijkt een resultaat met bekende
cameraposities; `train` traint een plaatsmodel per kaart op renders van het level (en op beelden die
een eerdere run al heeft gevonden), voor `build --head`; `refmap` plaatst de eigen kaart van het spel
(zijn deploy-scherm) op het level, en `minimap` leest de minimap van een opname tegen die kaart, beeld
voor beeld - de eerdere `frames --minimap` kan dat gebruiken. Heeft PyTorch en
`requirements-locate.txt` nodig. **Experimenteel:** op echte opnames plaatst hij tot nu toe maar een
klein deel van de beelden. Alle opties, de uitvoer en de methode:
[Locaties van beelden in een level](locate.md); de volledige optielijst: [Opdrachtenoverzicht](../cli-reference.md).

## Het scanvenster {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

of dubbelklik op `scan.bat`. Geen opties. Zie [Het scanvenster](reconstruction-scan-ui.md).

## Updates {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Zie [Updates](updates.md).

## De modelconverter {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Zet een Depth Anything V2-checkpoint om naar het ONNX-bestand dat de scanner gebruikt. Heeft PyTorch,
`transformers` en `onnxscript` nodig. Zie [Diepte](reconstruction-depth.md#building-the-model).
