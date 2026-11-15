---
title: Kommandoreferens
nav_order: 5
lang: "sv"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Kommandoreferens {#command-reference}

Alla kommandon körs från förvaringsmappen, med projektets miljö:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Kommando | Gör |
|---|---|
| [`route`](#route) | Spelar in bara positionerna för ett Forza-varv, för att hitta kartan i spelets filer |
| [`telemetry`](#telemetry) | Spelar in alla kanaler, en varvfil per varv, för fliken Racinganalys |
| [`laps`](#laps) | Läser ett FH Companion-varvbibliotek och skriver ut en banas rutt och sampel |
| [`reconstruct`](#reconstruct) | Löser en inspelning offline och skriver en `.glb` |
| [`hud`](#hud) | Läser spelarens egna handlingar, dödsfall och minikartans spår, samt dödsnotisen, ur en inspelning |
| [`locate`](#locate) | Var varje bildruta i en inspelning togs, jämfört med renderingar av banan |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Skanningsfönstret |
| [`python -m heat3d_update`](#updates) | Letar efter och installerar en uppdatering |
| [`python tools/export_onnx.py`](#the-model-converter) | Konverterar djupmodellen till ONNX |

När du startar `python -m heat3d_capture` kontrollerar verktyget först om det finns en nyare
version (se [Uppdateringar](updates.md); `HEAT3D_NO_UPDATE=1` stänger av kontrollen). `--help` efter
ett kommando visar dess alternativ:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Lyssnar efter Forza Data Out och sparar bara bilens positioner, inget annat: ingen djupmodell, ingen
GPU, ingen bildinspelning. Kod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Alternativ | Standard | Betydelse |
|---|---|---|
| `-o`, `--out` | krävs | Utdatasökväg; ändelsen byts ut, så `-o lap` skriver `lap.npz` och `lap.json`. |
| `--port` | `5300` | Porten spelet skickar till (bunden till 127.0.0.1). |
| `--seconds` | `0` | Stoppa efter så många sekunder; `0` kör tills du trycker Ctrl+C. |

En position sparas bara när spelet rapporterar ett lopp (`isRaceOn`), bilen rör sig fortare än
0,5 m/s och den är minst 0,5 m från den senast sparade positionen. Annars skulle en bil som står
still i en meny, med 60 paket per sekund, fylla filen med startlinjen. Varje samples tid är spelets
lopptid, eller klockan när den är 0. Layouten identifieras exakt som för `telemetry` (bilen måste
röra sig först; se [Forza](telemetry-forza.md)).

En gång per sekund skrivs antal mottagna paket, antal sparade positioner och den aktuella
positionen ut, eller `nothing on port 5300 yet - is Data Out on?` (ingenting på port 5300 än - är
Data Out på?). Rutten **sparas medan du kör**: var 2:a sekund när en ny position har kommit (intervallet
växer till tjugo gånger den förra sparningens tid, så en mycket lång session aldrig lägger mer än en
tjugondel av tiden på att skriva), och en gång till när inspelningen stoppas av någon orsak: Ctrl+C,
`--seconds` eller ett undantag. Varje sparning skriver `lap.npz.partial` / `lap.json.partial` och
flyttar sedan filerna till de riktiga namnen, så filerna på disken är alltid hela; vid en krasch eller
en avslutad process förloras högst de sista sekunderna. Om ingenting sparades skrivs hur du slår på
Data Out ut, och programmet avslutas med kod 1.

Utdata:

- `lap.npz` - NumPy-matriser `positions` (n x 3, meter), `times`, `speeds` (m/s);
- `lap.json` - går att läsa utan det här projektet:

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

Positionerna är spelets egna världskoordinater, och det är det som gör dem till ett handtag för att
hitta samma mark i spelets filer: kommandot `course` i
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) tar den här JSON-filen och exporterar
banan som varvet gick över.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Varje alternativ och varje spel beskrivs på [Telemetriinspelare](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Läser det varvbibliotek som FH Companion sparar och skriver två filer för en bana: en rutt som anger
vilken del av kartan som ska klippas ut ur spelets arkiv, och en tabell med varje sampel av varje varv.
De skrivs ihop, så att de inte kan komma ur takt. Kod:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Alternativ | Standard | Betydelse |
|---|---|---|
| `course` | ingen | Banans namn, matchas löst. Utelämna det för att lista biblioteket. |
| `-o`, `--out` | banans namn med gemener, mellanslag som `_` | Utdatasökväg; `.json` och `.csv` skrivs bredvid varandra. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Var banmapparna finns. |
| `--margin` | `80` | Meter som läggs till runt bannans utsträckning i x och z, i rutten `bounds`. |

### Lista {#listing}

Utan bananamn skrivs antalet banmappar ut, och för varje mapp antalet varvfiler (`*.json` var som helst
under den, utom `course.json`) och banans namn. Sedan skrivs raden `Name one to write it out:  -o <file> <course>`.

### Hitta en bana {#finding-a-course}

Banmapparna heter `<name> (course_<x>_<z>_to_<x>_<z>)`, det vill säga start och mål, avrundade. En
bana hittas i den här ordningen: det exakta mappnamnet; namnets del utan hänsyn till versaler och
gemener; en unik mapp vars namn innehåller texten. Fler träffar än en är ett fel, och felet listar
dem.

### Läsa den {#reading-it}

- `course.json` i mappen, när den går att läsa, anger namnet och den oavrundade start- och
  målpunkten (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); annars hämtas de från mappnamnet. En
  bana rapporteras som bana (circuit) när start och mål ligger mindre än 10 m från varandra.
- Varje annan `*.json` under mappen är ett varv (varven ligger flera mappnivåer djupt - efter klass,
  bil, inställning, etikett - och sökningen är helt rekursiv). Filerna läses som UTF-8 med
  byte-ordningsmärke. Ett varv som inte går att läsa hoppas över. Varven sorteras efter sin
  inspelningstid.
- Per varv: `Lap.samples` (var och en med `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), och bilens klass,
  ordningsnummer, prestandaindex, varvtid, längd, inspelningstid och om det var en stillastående start.

Den skriver ut en sammanfattning (varv, sampel, snabbaste varv och dess klass, utsträckningen i x/y/z).

### Utdata {#output}

**`<out>.json`** - samma rutt som `route` skriver, så kartextraktorn tar emot båda:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (utvidgad med `--margin` i x och
z), och `positions` från det **snabbaste** varvet (en linje i stället för ett grått moln av alla varv).

**`<out>.csv`** - varje sampel av varje varv, en rad var:

| Kolumn | Betydelse |
|---|---|
| `course` | banans namn |
| `lap` | en etikett per varv: inspelningsdatum och klockslag till minuten, och varvtiden |
| `car` | bilens ordningsnummer |
| `car_class` | bokstaven för prestandaklassen |
| `pi` | prestandaindex |
| `lap_seconds` | varvets tid |
| `speed_kmh` | hastighet i km/h |
| `x`, `y`, `z` | världsposition, meter, 3 decimaler |
| `speed_ms` | hastighet, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | som FH Companion spelar in dem |
| `metres` | sträcka längs varvet, 3 decimaler |
| `elapsed` | sekunder sedan varvets egen start, 3 decimaler |

Värden som inte är positioner skrivs med 4 signifikanta siffror. Positioner får fasta decimaler,
eftersom 4 signifikanta siffror skulle låsa en bana till ett rutnät på en meter. Kolumnnamnen är valda
så att visaren kan läsa filen utan att få veta mer: `lap` blir sessionen (två varv av samma bil
blandas aldrig ihop), `car` blir det som rör sig, `car_class` gruppen att färga efter, och `elapsed`
tidsaxeln (alla varv radas upp vid sin egen start).

Till sist skrivs ett tips ut om hur kartan klipps ut ur spelet med GameFiles, med rutt-filen eller en
egen ruta.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruerar en inspelning offline, med kamerabanan löst på en gång av VGGT. Långsamt: minuter per
fönster på ett skrivbordsgrafikkort. Kräver PyTorch, Hugging Face `transformers` och paketet `vggt`,
som skannern inte behöver: de står i `requirements-offline.txt`, och kommandot kontrollerar dem efter
att licensraden skrivits ut och erbjuder sig att installera det som saknas (avslutningskod 1 om du
säger nej). Full beskrivning: [Offline-rekonstruktion](reconstruction-offline.md).

| Alternativ | Standard | Betydelse |
|---|---|---|
| `video` | krävs | Inspelningen. Avslutningskod 2 om den inte finns. |
| `-o`, `--out` | krävs | `.glb`-filen som ska skrivas. |
| `--solve-budget` | `260` | Största antal bildrutor som lämnas till lösaren. De väljs efter hur mycket bilden rör sig, inte efter klockan. Fler ger bättre träffsäkerhet men är mycket långsammare. Fler än 400 planerade bildrutor avvisas. |
| `--fuse-interval` | `0.4` | Sekunder mellan de bildrutor som smälts ihop till geometri. |
| `--model` | `vggt-1b` | Vilka VGGT-vikter som löser: `vggt-1b` (`facebook/VGGT-1B`, ickekommersiell) eller `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, spärrad; kräver åtkomst beviljad av Meta). Licensraden som skrivs ut först är den modellens. |

Den skriver först ut modellens licensrad, sedan varje steg (`masking`, `planning`, `solving`,
`fusing`, `exporting`) med förfluten tid och förlopp, och till sist en sammanfattning: lösta kameror,
slutfelet, värsta sömmen, anteckningar och filen som skrevs. Avslutningskoden är 0 bara om en fil
skrevs.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Läser spelets HUD ur spelarens egen inspelning, efter matchen: spelarens egna handlingar ur
poänguppkomsten, dödsfall och återkomster ur nedslags- och utplaceringsskärmarna, minikartans spår
och dödsnotisen. Skriver `<out>.parquet` (spår och händelser, en 3DHeat-tabell),
`<out>.events.jsonl`, `<out>.summary.json` och `<out>.map.png` + `.map.json` (minikartans mosaik och
dess ankare för visarens Kartbild). Battlefield 6 (`bf6`) är den enda profilen hittills.

Kräver **ffmpeg och ffprobe** i PATH (`winget install Gyan.FFmpeg`, och sedan en ny terminal).

| Alternativ | Standard | Betydelse |
|---|---|---|
| `video` | krävs | Inspelningen. |
| `-o`, `--out` | videons namn | Utdatasökväg utan ändelse. |
| `--game` | `bf6` | Vars HUD som ska läsas. |
| `--player` | gissas | Spelarens namn så som dödsnotisen visar det, matchat löst. |
| `--fps` | `5` | Minikartans sampel per sekund. |
| `--start`, `--seconds` | hela videon | Den del av inspelningen som ska läsas. |
| `--metres-per-pixel` | ingen | Minikartans skala, när den är känd; utan den anges positionerna i minikartans pixlar. |
| `--cpu` | av | Avkoda på processorn även när ett NVIDIA-kort finns. |

Förloppet skrivs ut var femte sekund; i slutet skrivs spelaren, kills, deaths, liv och filerna som
skrevs.

Fullständig beskrivning: [Läsa HUD från en inspelning](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderar en bana från varje plats en spelare kan stå på och indexerar renderingarna; `frames`
placerar varje samplad bildruta i en inspelning mot den, utifrån bilden, med hud-kommandots spår på
minikartan som reserv; `eval` jämför ett resultat med kända kameraposer; `train` tränar en
platsmodell per karta på renderingar av banan (och på bildrutor som en körning redan lokaliserat), för
`build --head`; `refmap` placerar spelets egen karta (dess utplaceringsskärm) på banan, och `minimap`
läser en inspelnings minikarta mot den, bildruta för bildruta - den föregående `frames --minimap` kan
ta. Kräver PyTorch och `requirements-locate.txt`. **Experimentellt:** på riktiga inspelningar placerar
det hittills bara en liten andel av bildrutorna. Alla alternativ, utdata och metoden:
[Lokalisera bildrutor i en bana](locate.md); hela alternativlistan: [Kommandoreferens](../cli-reference.md).

<a id="the-scan-window"></a>
## Skanningsfönstret {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

eller dubbelklicka på `scan.bat`. Inga alternativ. Se [Skanningsfönstret](reconstruction-scan-ui.md).

<a id="updates"></a>
## Uppdateringar {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Se [Uppdateringar](updates.md).

<a id="the-model-converter"></a>
## Modellkonverteraren {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Konverterar en Depth Anything V2-kontrollpunkt till den ONNX-fil som skannern kör. Kräver PyTorch,
`transformers` och `onnxscript`. Se [Djup](reconstruction-depth.md#building-the-model).
