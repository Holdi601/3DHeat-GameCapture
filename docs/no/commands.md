---
title: Kommandoreferanse
nav_order: 5
lang: "no"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Kommandoreferanse {#command-reference}

Alle kommandoene kjøres fra mappen til repositoriet, med prosjektets miljø:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Kommando | Gjør |
|---|---|
| [`route`](#route) | Lagrer bare posisjonene til en Forza-runde, for å finne kartet i spillets filer |
| [`telemetry`](#telemetry) | Lagrer alle kanaler, én rundefil per runde, til Løpsanalyse-fanen |
| [`laps`](#laps) | Leser FH Companions rundebibliotek og skriver ruten og målepunktene for én bane |
| [`reconstruct`](#reconstruct) | Løser et opptak offline og skriver en `.glb` |
| [`hud`](#hud) | Leser spillerens egne handlinger, dødsfall og minikartsporet, samt drapsloggen, ut av et opptak |
| [`locate`](#locate) | Hvor hver ramme i et opptak ble tatt, mot gjengivelser av nivået |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Skannevinduet |
| [`python -m heat3d_update`](#updates) | Ser etter og installerer en oppdatering |
| [`python tools/export_onnx.py`](#the-model-converter) | Konverterer dybdemodellen til ONNX |

Når det startes som `python -m heat3d_capture`, ser verktøyet først etter en nyere utgivelse (se
[Oppdateringer](updates.md); `HEAT3D_NO_UPDATE=1` slår det av). `--help` etter et hvilket som helst
kommandonavn lister alternativene:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kode: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Lytter etter Forza Data Out og lagrer bare bilens posisjoner, ingenting annet: ingen dybdemodell,
ingen GPU, ingen opptak. Kode: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Alternativ | Standard | Betydning |
|---|---|---|
| `-o`, `--out` | påkrevd | Utdatasti; endelsen erstattes, så `-o lap` skriver `lap.npz` og `lap.json`. |
| `--port` | `5300` | Porten spillet sender til (bundet til 127.0.0.1). |
| `--seconds` | `0` | Stopp etter så mange sekunder; `0` kjører til Ctrl+C. |

En posisjon lagres bare mens spillet melder at det kjøres et løp (`isRaceOn`), bilen beveger seg
raskere enn 0,5 m/s, og den er minst 0,5 m fra forrige lagrede posisjon. Ellers ville en bil som
står i en meny, med 60 pakker i sekundet, fylle filen med startstreken. Hver prøves tid er spillets
løpstid, eller klokkeslettet når den er 0. Oppsettet oppdages på samme måte som for `telemetry`
(bilen må bevege seg først; se [Forza](telemetry-forza.md)).

Én gang i sekundet skriver den ut hvor mange pakker som er mottatt, hvor mange posisjoner som er
lagret, og gjeldende posisjon, eller `nothing on port 5300 yet - is Data Out on?`.
Ruten **lagres mens den kjøres**: hvert 2. sekund etter at en ny posisjon er kommet (intervallet
vokser til tjue ganger det siste lagringen tok, slik at en svært lang økt aldri bruker mer enn en
tjuendedel av tiden på å skrive), og én gang til når opptakeren stopper, uansett grunn – Ctrl+C,
`--seconds` eller et unntak. Hver lagring skriver `lap.npz.partial` / `lap.json.partial` og flytter
dem deretter over de ekte filene, slik at filene på disken alltid er hele. Et krasj eller en avsluttet
prosess mister høyst de siste sekundene. Hvis ingenting ble lagret, skriver den ut hvordan Data Out
slås på, og avslutter med exit-kode 1.

Utdata:

- `lap.npz` - NumPy-matriser `positions` (n x 3, meter), `times`, `speeds` (m/s);
- `lap.json` - kan leses uten dette prosjektet:

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

Posisjonene er spillets egne verdenskoordinater. Det er det som gjør dem til et håndtak for å finne
samme bakke i spillets filer: [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)-kommandoen
`course` tar denne JSON-filen og eksporterer banen som runden kjørte over.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Alle alternativene og alle spillene beskrives på [Telemetriopptakere](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Leser rundebiblioteket FH Companion holder, og skriver to filer for én bane: en rute som sier hvilket
stykke kart som skal klippes ut av spillets arkiv, og en tabell med hvert målepunkt i hver runde.
De skrives sammen, slik at de ikke kan komme ut av takt. Kode:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Alternativ | Standard | Betydning |
|---|---|---|
| `course` | ingen | Banenavn, med løs matching. Utelat det for å liste biblioteket. |
| `-o`, `--out` | banenavnet med små bokstaver, mellomrom som `_` | Utdatasti; `.json` og `.csv` skrives ved siden av hverandre. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Der banemappene ligger. |
| `--margin` | `80` | Meter lagt til rundt banens utstrekning i x og z, i rutens `bounds`. |

### Liste {#listing}

Uten bane skriver den ut antall banemapper og, for hver av dem, antall rundefiler (`*.json` hvor som
helst under den, unntatt `course.json`) og banenavnet. Så kommer linjen
`Name one to write it out:  -o <file> <course>`.

### Finne en bane {#finding-a-course}

Banemappene heter `<navn> (course_<x>_<z>_to_<x>_<z>)`: start og mål, avrundet. En bane finnes ved, i
denne rekkefølgen: det nøyaktige mappenavnet; navnedelen av mappenavnet, uten forskjell på store og
små bokstaver; en unik mappe der navnet inneholder teksten. Flere treff er en feil, og den lister dem.

### Lese den {#reading-it}

- `course.json` i mappen, når den kan leses, gir navnet og uavrundet start og mål (`Name`, `StartX`,
  `StartZ`, `FinishX`, `FinishZ`). Ellers hentes de fra mappenavnet. En bane regnes som rundebane når
  start og mål er mindre enn 10 m fra hverandre.
- Hver annen `*.json` under mappen er en runde. Runder ligger flere mapper ned, etter klasse, bil,
  innstilling og merkelapp, og søket er rett og slett rekursivt. Filer leses som UTF-8 med byte order
  mark. En runde som ikke kan leses, hoppes over. Rundene sorteres etter opptakstid.
- Per runde: `Lap.samples` (hver med `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`,
  `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), og bilens klasse,
  plassering, rundetid, lengde, opptakstid og stående start.

Den skriver ut et sammendrag: runder, målepunkter, beste runde og dens klasse, og utstrekningen i x/y/z.

### Utdata {#output}

**`<out>.json`** - samme rutestruktur som `route` skriver, så kartuttrekkeren tar begge:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (utvidet med `--margin` i x og z), og
`positions` for den **raskeste** runden (én linje i stedet for en søle av alle rundene).

**`<out>.csv`** - hvert målepunkt i hver runde, én rad hver:

| Kolonne | Betydning |
|---|---|
| `course` | banenavn |
| `lap` | en etikett per runde: opptaksdato og -tid til minuttet, og rundetiden |
| `car` | bilens ordinal |
| `car_class` | bokstaven for ytelsesklassen |
| `pi` | ytelsesindeks |
| `lap_seconds` | rundens tid |
| `speed_kmh` | fart i km/t |
| `x`, `y`, `z` | verdensposisjon, meter, 3 desimaler |
| `speed_ms` | fart, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | slik FH Companion registrerer dem |
| `metres` | avstand langs runden, meter, 3 desimaler |
| `elapsed` | sekunder siden rundens egen start, 3 desimaler |

Verdier som ikke er posisjoner, skrives med 4 signifikante siffer. Posisjoner får faste desimaler,
fordi 4 signifikante siffer ville festet en bane til et rutenett på én meter. Kolonnenavnene er valgt
slik at visningsprogrammet kan lese filen uten at det må fortelles hvordan: `lap` blir økten (to runder
av samme bil blir aldri slått sammen), `car` det som beveger seg, `car_class` gruppen å fargelegge etter,
og `elapsed` tidsaksen (alle runder stiller seg opp etter sin egen start).

Til slutt skriver den ut et hint om hvordan kartet klippes ut av spillet med GameFiles, med rutefilen
eller en eksplisitt boks.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruerer et opptak offline, der kamerabanen løses i én operasjon av VGGT. Det er tregt: minutter
per vindu på et stasjonært GPU. Trenger PyTorch, Hugging Face `transformers` og pakken `vggt`, som
skanneren ikke trenger. De står i `requirements-offline.txt`, og kommandoen sjekker etter dem etter
å ha skrevet ut lisenslinjen. Den tilbyr så å installere det som mangler (exit-kode 1 hvis det avslås).
Full beskrivelse: [Offline-rekonstruksjon](reconstruction-offline.md).

| Alternativ | Standard | Betydning |
|---|---|---|
| `video` | påkrevd | Opptaket. Exit-kode 2 hvis det ikke finnes. |
| `-o`, `--out` | påkrevd | `.glb`-filen som skal skrives. |
| `--solve-budget` | `260` | Flest rammer som gis til løseren. De fordeles etter hvor mye bildet beveger seg, ikke etter klokken. Flere gir bedre nøyaktighet og er mye tregere. Mer enn 400 planlagte rammer avvises. |
| `--fuse-interval` | `0.4` | Sekunder mellom rammene som smeltes inn i geometrien. |
| `--model` | `vggt-1b` | Hvilke VGGT-vekter som skal løse med: `vggt-1b` (`facebook/VGGT-1B`, ikke-kommersiell) eller `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, låst; krever tilgang gitt av Meta). Lisenslinjen som skrives først, er for den modellen. |

Den skriver først modellens lisenslinje, deretter hvert trinn (`masking`, `planning`, `solving`,
`fusing`, `exporting`) med medgåtte sekunder og fremdrift. Til slutt kommer et sammendrag: løste
kameraer, lukkefeil, verste søm, notater og filen som ble skrevet. Exit-koden er bare 0 hvis en fil
ble skrevet.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Leser spillets HUD ut av spillerens eget opptak, etter kampen: spillerens egne handlinger fra
poengpopupen, dødsfall og gjenoppstandelser fra skjermene for nedslått og utplassering, sporet på
minikartet og drapsloggen. Skriver `<out>.parquet` (spor og hendelser, en 3DHeat-tabell),
`<out>.events.jsonl`, `<out>.summary.json`, og `<out>.map.png` + `.map.json` (mosaikken av minikartet
og ankrene for visningsprogrammets **Kartbilde**). Battlefield 6 (`bf6`) er den eneste profilen så langt.

Trenger **ffmpeg og ffprobe** på `PATH` (`winget install Gyan.FFmpeg`, deretter et nytt terminalvindu).

| Alternativ | Standard | Betydning |
|---|---|---|
| `video` | påkrevd | Opptaket. |
| `-o`, `--out` | videoens navn | Utdatasti uten filendelse. |
| `--game` | `bf6` | Hvilket HUD som leses. |
| `--player` | gjettet | Spillerens navn slik drapsloggen viser det, med løs matching. |
| `--fps` | `5` | Minikart-prøver per sekund. |
| `--start`, `--seconds` | hele videoen | Delen av opptaket som skal leses. |
| `--metres-per-pixel` | ingen | Minikartets skala, når den er kjent. Uten den er posisjonene i minikart-piksler. |
| `--cpu` | av | Dekod på CPU, selv om det finnes et NVIDIA-kort. |

Full beskrivelse: [Å lese HUD fra et opptak](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` gjengir et nivå fra hvert sted en spiller kan stå, og indekserer gjengivelsene. `frames`
plasserer hver samplet ramme i et opptak mot dem, ut fra bildet, med sporet fra `hud`-kommandoens
minikart som reserve. `eval` sammenligner et resultat med kjente kameraposisjoner. `train` trener en
stedsmodell per kart på gjengivelser av nivået (og på rammer som en kjøring allerede har lokalisert),
for `build --head`. `refmap` plasserer spillets eget kart (deploy-skjermen) på nivået, og `minimap`
leser et opptaks minikart mot det, bilde for bilde. Det er det forrige `frames --minimap` kan ta.
Trenger PyTorch og `requirements-locate.txt`. **Eksperimentelt:** på virkelige opptak plasserer det
så langt bare en liten andel av rammene. Alle alternativene, utdataene og metoden:
[Lokalisere rammer i et nivå](locate.md). Hele alternativlisten: [Kommandoreferansen](../cli-reference.md).

<a id="the-scan-window"></a>

## Skannevinduet {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

eller dobbeltklikk på `scan.bat`. Ingen alternativer. Se [Skannevinduet](reconstruction-scan-ui.md).

<a id="updates"></a>

## Oppdateringer {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Se [Oppdateringer](updates.md).

<a id="the-model-converter"></a>

## Modellkonverteren {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Konverterer en Depth Anything V2-sjekkpunktfil til ONNX-filen skanneren kjører. Trenger PyTorch,
`transformers` og `onnxscript`. Se [Dybde](reconstruction-depth.md#building-the-model).
