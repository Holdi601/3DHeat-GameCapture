---
title: Kommandoreference
nav_order: 5
lang: "da"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Kommandoreference {#command-reference}

Alle kommandoer køres fra mappen med lageret, med projektets miljø:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Kommando | Gør |
|---|---|
| [`route`](#route) | Optager kun et Forza-omgangs positioner, til at finde banen i spillets filer |
| [`telemetry`](#telemetry) | Optager alle kanaler, en omgangsfil pr. omgang, til fanen Race-analyse |
| [`laps`](#laps) | Læser et FH Companion-omgangsbibliotek og skriver én banes rute og samples |
| [`reconstruct`](#reconstruct) | Løser en optagelse offline og skriver en `.glb` |
| [`hud`](#hud) | Læser spillerens egne handlinger, dødsfald og minimapspor samt dræbersiden ud af en optagelse |
| [`locate`](#locate) | Hvor hver billedramme i en optagelse blev taget, i forhold til gengivelser af banen |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Scanvinduet |
| [`python -m heat3d_update`](#updates) | Søger efter og installerer en opdatering |
| [`python tools/export_onnx.py`](#the-model-converter) | Konverterer dybdemodellen til ONNX |

Når den startes som `python -m heat3d_capture`, søger værktøjet først efter en nyere udgivelse (se
[Opdateringer](updates.md); `HEAT3D_NO_UPDATE=1` slår det fra). `--help` efter et hvilket som helst
kommandoord viser dets valgmuligheder:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kode: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Lytter efter Forza Data Out og gemmer kun bilens positioner, intet andet: ingen dybdemodel, ingen
GPU, ingen optagelse. Kode: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `-o`, `--out` | påkrævet | Outputsti; endelsen erstattes, så `-o lap` skriver `lap.npz` og `lap.json`. |
| `--port` | `5300` | Porten spillet sender til (bundet til 127.0.0.1). |
| `--seconds` | `0` | Stop efter så mange sekunder; `0` kører til Ctrl+C. |

En position gemmes kun, mens spillet melder et løb (`isRaceOn`), bilen kører hurtigere end
0,5 m/s, og den er mindst 0,5 m fra sidst gemte position - ellers ville en bil, der står i en menu
og sender 60 pakker i sekundet, fylde filen med startlinjen. Hvert samples tid er spillets
løbstid, eller klokkens tid når den er 0. Layoutet findes på samme måde som for `telemetry` (bilen
skal køre først; se [Forza](telemetry-forza.md)).

Hvert sekund udskriver den antal modtagne pakker, antal gemte positioner og den aktuelle position,
eller `nothing on port 5300 yet - is Data Out on?`. Ruten **gemmes, mens der køres**: hver 2.
sekund, når en ny position er kommet ind (intervallet vokser til tyve gange den sidste gemning
tog, så en meget lang session aldrig bruger mere end en tyvendedel af sin tid på at skrive), og en
gang til, når optageren stopper af en hvilken som helst grund - Ctrl+C, `--seconds` eller en fejl.
Hver gemning skriver `lap.npz.partial` / `lap.json.partial` og flytter derefter filen over den rigtige
fil, så filerne på disken altid er hele; et nedbrud eller en dræbt proces mister højst de sidste
få sekunder. Hvis intet blev gemt, udskriver den, hvordan man slår Data Out til, og afslutter med
kode 1.

Output:

- `lap.npz` - NumPy-arrays `positions` (n x 3, meter), `times`, `speeds` (m/s);
- `lap.json` - kan læses uden dette projekt:

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

Positionerne er spillets egne verdenskoordinater, og det er det, der gør dem til et håndtag til at
finde den samme jord i spillets filer: [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)-kommandoen
`course` tager denne JSON og eksporterer den bane, omgangen kørte på.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Alle valgmuligheder og spil beskrives på [Telemetrioptagere](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Læser det omgangsbibliotek FH Companion gemmer, og skriver to filer for én bane: en rute, der
siger, hvilket stykke kort der skal skæres ud af spillets arkiv, og en tabel med hvert sample i
hver omgang. De skrives samtidig, så de ikke kan komme ud af takt. Kode:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `course` | ingen | Banenavn, søgt løst. Udelad for at liste biblioteket. |
| `-o`, `--out` | banenavnet med småt, mellemrum som `_` | Outputsti; `.json` og `.csv` skrives ved siden af hinanden. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Hvor banemapperne ligger. |
| `--margin` | `80` | Meter lagt til omkring banens udstrækning i x og z i rutens `bounds`. |

### Liste {#listing}

Uden en bane udskriver den antal banemapper og for hver af dem antal omgangsfiler
(`*.json` hvor som helst under den undtagen `course.json`) og banenavnet, derefter
`Name one to write it out:  -o <file> <course>`.

### Find en bane {#finding-a-course}

Banemapper hedder `<name> (course_<x>_<z>_to_<x>_<z>)` - start og mål, afrundet. En bane findes
i denne rækkefølge: det præcise mappenavn; navnedelen af mappenavnet, uden hensyn til store og små
bogstaver; en entydig mappe, hvis navn indeholder teksten. Flere træf er en fejl, der lister dem.

### Læsning {#reading-it}

- `course.json` i mappen, når den kan læses, giver navnet og de uafrundede start- og målpunkter
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); ellers hentes de fra mappenavnet. En bane
  regnes som rundbane, når start og mål ligger mindre end 10 m fra hinanden.
- Hver anden `*.json` under mappen er en omgang (omgange ligger flere mapper ned - efter klasse,
  bil, tuning, mærke - og søgningen er simpelthen rekursiv). Filer læses som UTF-8 med en
  byte order mark. En omgang, der ikke kan læses, springes over. Omgange sorteres efter deres
  optagelsestid.
- Pr. omgang: `Lap.samples` (hver med `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`) samt bilens
  klasse, ordinal, ydelsesindeks, omgangstid, længde, optagelsestid og stående start.

Den udskriver et resumé (omgange, samples, bedste omgang og dens klasse, udstrækningen i x/y/z).

### Output {#output}

**`<out>.json`** - samme rutestruktur som `route` skriver, så kortudtrækkeren tager begge:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (udvidet med `--margin` i x og
z) og `positions` for den **hurtigste** omgang (én linje i stedet for en udtværing af alle omgange).

**`<out>.csv`** - hvert sample i hver omgang, én række hver:

| Kolonne | Betydning |
|---|---|
| `course` | banenavn |
| `lap` | en etiket pr. omgang: optagelsesdato og -tid til minuttet, og omgangstiden |
| `car` | bilens ordinal |
| `car_class` | ydelsesklassens bogstav |
| `pi` | ydelsesindeks |
| `lap_seconds` | omgangens tid |
| `speed_kmh` | hastighed i km/t |
| `x`, `y`, `z` | verdensposition, meter, 3 decimaler |
| `speed_ms` | hastighed, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | som FH Companion optager dem |
| `metres` | afstand langs omgangen, 3 decimaler |
| `elapsed` | sekunder siden omgangens egen start, 3 decimaler |

Værdier, der ikke er positioner, skrives med 4 betydende cifre; positioner får faste decimaler,
fordi 4 betydende cifre ville få en bane til at snappe til et gitter med én meters trin. Kolonnenavnene
er valgt, så viewer'en kan kortlægge filen uden at få at vide hvordan: `lap` bliver til sessionen
(to omgange af samme bil bliver aldrig sat sammen), `car` til det, der bevæger sig, `car_class` til
gruppen der farves efter, `elapsed` til tidsaksen (alle omgange flugter ved deres egen start).

Til sidst udskriver den et hint om, hvordan kortet skæres ud af spillet med GameFiles, med rutefilen
eller en eksplicit boks.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruerer en optagelse offline, med kameraets bane løst på én gang af VGGT. Langsomt: minutter
pr. vindue på et desktop-GPU. Kræver PyTorch, Hugging Face `transformers` og pakken `vggt`, som
scanneren ikke har brug for: de står i `requirements-offline.txt`, og kommandoen tjekker for dem efter
at have udskrevet licenslinjen, og tilbyder at installere det, der mangler (afslutter med kode 1, hvis
det afvises). Fuld beskrivelse: [Offline rekonstruktion](reconstruction-offline.md).

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `video` | påkrævet | Optagelsen. Afslutter med kode 2, hvis den ikke findes. |
| `-o`, `--out` | påkrævet | Den `.glb`, der skrives. |
| `--solve-budget` | `260` | Flest billedrammer givet til løseren. De er fordelt efter, hvor meget billedet bevæger sig, ikke efter uret. Flere er mere præcist og langt langsommere. Mere end 400 planlagte rammer afvises. |
| `--fuse-interval` | `0.4` | Sekunder mellem billedrammer, der smeltes sammen til geometri. |
| `--model` | `vggt-1b` | Hvilke VGGT-vægte der løses med: `vggt-1b` (`facebook/VGGT-1B`, ikke-kommerciel) eller `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, låst; kræver adgang givet af Meta). Licenslinjen, der udskrives først, er den pågældende models. |

Den udskriver modellens licenslinje først, derefter hvert trin (`masking`, `planning`, `solving`,
`fusing`, `exporting`) med forløbne sekunder og fremskridt, og til sidst et resumé: løste kameraer,
lukkefejl, værste søm, noter og den skrevne fil. Afslutningskoden er kun 0, hvis en fil blev skrevet.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Læser spillets HUD ud af spillerens egen optagelse, efter kampen: spillerens egne handlinger fra
point-popuppen, dødsfald og genoplivninger fra nedslags- og udsætningsskærmene, minimapsporet og
dræbersiden. Skriver `<out>.parquet` (spor og hændelser, en 3DHeat-tabel), `<out>.events.jsonl`,
`<out>.summary.json` og `<out>.map.png` + `.map.json` (minimapens mosaik og dens ankre til viewer'ens
**Kortbillede**). Battlefield 6 (`bf6`) er indtil videre den eneste profil.

Kræver **ffmpeg og ffprobe** på PATH (`winget install Gyan.FFmpeg`, derefter en ny terminal).

| Valgmulighed | Standard | Betydning |
|---|---|---|
| `video` | påkrævet | Optagelsen. |
| `-o`, `--out` | videoens navn | Outputsti uden endelse. |
| `--game` | `bf6` | Hvis HUD der læses. |
| `--player` | gættet | Spillerens navn, som dræberlisten viser det, søgt løst. |
| `--fps` | `5` | Minimapsamples pr. sekund. |
| `--start`, `--seconds` | hele videoen | Den del af optagelsen der læses. |
| `--metres-per-pixel` | ingen | Minimapens skala, når den er kendt; uden den er positioner i minimapens pixels. |
| `--cpu` | fra | Dekod på CPU, også når et NVIDIA-kort er til stede. |

Fuld beskrivelse: [Læsning af HUD fra en optagelse](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` gengiver en bane fra alle steder en spiller kan stå og indekserer gengivelserne; `frames`
placerer hver udtaget billedramme af en optagelse mod den ud fra billedet, med minimapsporet fra
`hud`-kommandoen som reserve; `eval` sammenligner et resultat med kendte kameraposer; `train` træner
en stedsmodel pr. kort på gengivelser af banen (og på rammer en kørsel allerede har placeret) til
`build --head`; `refmap` placerer spillets eget kort (dets udsætningsskærm) på banen, og `minimap`
læser en optagelses minimap mod det, billede for billede - det forudgående `frames --minimap` kan
tage. Kræver PyTorch og `requirements-locate.txt`. **Eksperimentelt:** på rigtige optagelser placerer
det indtil videre kun en lille andel af rammerne. Alle valgmuligheder, output og metoden:
[Find billedrammer i en bane](locate.md); hele listen over valgmuligheder: [Kommandoreference](../cli-reference.md).

## Scanvinduet {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

eller dobbeltklik på `scan.bat`. Ingen valgmuligheder. Se [Scanvinduet](reconstruction-scan-ui.md).

## Opdateringer {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Se [Opdateringer](updates.md).

## Modelkonverteren {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Konverterer en Depth Anything V2-checkpoint til den ONNX-fil, scanneren kører. Kræver PyTorch,
`transformers` og `onnxscript`. Se [Dybde](reconstruction-depth.md#building-the-model).
