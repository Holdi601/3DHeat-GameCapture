---
title: "Referenca komandi"
nav_order: 5
lang: "bs"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Referenca komandi {#command-reference}

Sve komande se pokreću iz foldera repozitorija, s okruženjem projekta:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Komanda | Šta radi |
|---|---|
| [`route`](#route) | Snima samo pozicije Forza kruga, za traženje mape u datotekama igre |
| [`telemetry`](#telemetry) | Snima svaki kanal, jedna datoteka kruga po krugu, za karticu Analiza utrke |
| [`laps`](#laps) | Čita biblioteku krugova FH Companion i zapisuje rutu i uzorke jedne staze |
| [`reconstruct`](#reconstruct) | Rješava snimak offline i zapisuje `.glb` |
| [`hud`](#hud) | Iz snimka čita igračeve vlastite akcije, smrti i trag s mini-mape te kill feed |
| [`locate`](#locate) | Gdje je snimljen svaki kadar snimka, naspram rendera nivoa |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Prozor za skeniranje |
| [`python -m heat3d_update`](#updates) | Provjerava i primjenjuje ažuriranje |
| [`python tools/export_onnx.py`](#the-model-converter) | Pretvara model dubine u ONNX |

Kad se pokrene kao `python -m heat3d_capture`, alat prvo provjerava postoji li novije izdanje (pogledajte
[Ažuriranja](updates.md); `HEAT3D_NO_UPDATE=1` to isključuje). `--help` iza bilo koje komande ispisuje njene opcije:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Sluša Forza Data Out i čuva samo pozicije automobila, ništa drugo: bez modela dubine, bez
GPU-a, bez snimanja ekrana. Kod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opcija | Zadano | Značenje |
|---|---|---|
| `-o`, `--out` | obavezno | Putanja izlaza; njen nastavak se zamjenjuje, pa `-o lap` zapisuje `lap.npz` i `lap.json`. |
| `--port` | `5300` | Port na koji igra šalje (veže se na 127.0.0.1). |
| `--seconds` | `0` | Zaustavite nakon ovoliko sekundi; `0` radi do Ctrl+C. |

Pozicija se čuva samo dok igra javlja utrku (`isRaceOn`), automobil se kreće brže od
0,5 m/s i udaljen je najmanje 0,5 m od posljednje sačuvane pozicije - inače bi sjedenje u meniju
sa 60 paketa u sekundi napunilo datoteku startnom linijom. Vrijeme svakog uzorka je
vrijeme utrke iz igre, ili sat računara kad je ono 0. Raspored (layout) se otkriva tačno kao za
`telemetry` (automobil se prvo mora kretati; pogledajte [Forza](telemetry-forza.md)).

Jednom u sekundi ispisuje primljene pakete, sačuvane pozicije i trenutnu poziciju, ili
`nothing on port 5300 yet - is Data Out on?`. Ruta se **sprema dok se vozi**: svake
2 sekunde čim stigne nova pozicija (razmak raste na dvadeset puta koliko je trajalo posljednje spremanje, pa
veoma duga sesija nikad ne troši više od dvadesetine vremena na pisanje), i još
jednom kad se snimač zaustavi iz bilo kojeg razloga - Ctrl+C, `--seconds` ili izuzetak. Svako spremanje
zapisuje `lap.npz.partial` / `lap.json.partial` i zatim ga premješta preko prave datoteke, pa su
datoteke na disku uvijek cijele; pad ili ubijen proces gubi najviše posljednjih nekoliko
sekundi. Ako ništa nije sačuvano, ispisuje kako uključiti Data Out i izlazi s kodom 1.

Izlaz:

- `lap.npz` - NumPy nizovi `positions` (n x 3, metri), `times`, `speeds` (m/s);
- `lap.json` - čitljiv bez ovog projekta:

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

Pozicije su vlastite svjetske koordinate igre, zbog čega su oslonac za
pronalaženje istog terena u datotekama igre: komanda `course` iz
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) uzima ovaj
JSON i izvozi stazu preko koje je krug vožen.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Svaka opcija i igra opisani su na stranici [Snimači telemetrije](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Čita biblioteku krugova koju vodi FH Companion i zapisuje dvije datoteke za jednu stazu: rutu koja
kaže koji dio mape izrezati iz arhive igre i tabelu svakog uzorka svakog
kruga. Zapisuju se zajedno da se ne bi razišle. Kod:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opcija | Zadano | Značenje |
|---|---|---|
| `course` | nema | Naziv staze, upoređuje se slobodno. Izostavite da se ispiše biblioteka. |
| `-o`, `--out` | naziv staze, malim slovima, razmaci kao `_` | Putanja izlaza; `.json` i `.csv` zapisuju se jedan pored drugog. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Gdje su folderi staza. |
| `--margin` | `80` | Metri dodani oko opsega staze u x i z u `bounds` rute. |

### Ispis liste {#listing}

Bez staze ispisuje broj foldera staza i, za svaki, broj datoteka
krugova (`*.json` bilo gdje ispod njega osim `course.json`) i naziv staze,
zatim `Name one to write it out:  -o <file> <course>`.

### Pronalaženje staze {#finding-a-course}

Folderi staza se zovu `<name> (course_<x>_<z>_to_<x>_<z>)` - start i cilj,
zaokruženi. Staza se pronalazi ovim redom: tačan naziv foldera; dio naziva
foldera s imenom, bez obzira na veličinu slova; jedinstven folder čiji naziv sadrži tekst.
Više podudaranja je greška koja ih navodi.

### Čitanje {#reading-it}

- `course.json` u folderu, kad je čitljiv, daje naziv te nezaokružene start i
  cilj (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); inače se uzimaju iz
  naziva foldera. Staza se prijavljuje kao kružna kad su start i cilj udaljeni manje od 10 m.
- Svaki drugi `*.json` ispod foldera je krug (krugovi leže nekoliko foldera duboko - po klasi,
  automobilu, podešenju, oznaci - a pretraga je jednostavno rekurzivna). Datoteke se čitaju kao UTF-8 s oznakom
  redoslijeda bajtova (BOM). Nečitljiv krug se preskače. Krugovi su sortirani po vremenu snimanja.
- Po krugu: `Lap.samples` (svaki s `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), te klasa
  automobila, redni broj, indeks performansi, sekunde kruga, dužina, vrijeme snimanja i start iz mjesta.

Ispisuje sažetak (krugovi, uzorci, najbolji krug i njegova klasa, opseg x/y/z).

### Izlaz {#output}

**`<out>.json`** - isti oblik rute koji zapisuje `route`, pa ga ekstraktor mape prima oba:
`layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (prošireno za `--margin` u x i
z) i `positions` **najbržeg** kruga (jedna linija umjesto mrlje svih krugova).

**`<out>.csv`** - svaki uzorak svakog kruga, po jedan red:

| Kolona | Značenje |
|---|---|
| `course` | naziv staze |
| `lap` | oznaka po krugu: datum i vrijeme snimanja do minute te vrijeme kruga |
| `car` | redni broj automobila |
| `car_class` | slovo klase performansi |
| `pi` | indeks performansi |
| `lap_seconds` | vrijeme kruga |
| `speed_kmh` | brzina u km/h |
| `x`, `y`, `z` | svjetska pozicija, metri, 3 decimale |
| `speed_ms` | brzina, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | kako ih bilježi FH Companion |
| `metres` | udaljenost duž kruga, 3 decimale |
| `elapsed` | sekunde od vlastitog starta kruga, 3 decimale |

Vrijednosti koje nisu pozicije zapisuju se na 4 značajne cifre; pozicije dobijaju fiksne decimale jer
bi 4 značajne cifre prilijepile stazu na rešetku od jednog metra. Nazivi kolona su izabrani
tako da pregledač mapira datoteku bez uputa: `lap` postaje sesija (dva kruga istog automobila
se nikad ne spajaju), `car` ono što se kreće, `car_class` grupa za bojenje, `elapsed`
vremenska osa (svaki krug se poravnava na vlastitom startu).

Na kraju ispisuje savjet kako izrezati mapu iz igre pomoću GameFiles, s datotekom
rute ili izričitim okvirom.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruiše snimak offline, a putanju kamere rješava VGGT odjednom. Sporo:
minute po prozoru na desktop GPU-u. Treba PyTorch, Hugging Face `transformers` i paket
`vggt`, koje skener ne treba: navedeni su u `requirements-offline.txt`, a
komanda ih provjerava nakon ispisa linije o licenci i nudi instalaciju onoga što
nedostaje (izlazni kod 1 ako se odbije). Puni opis:
[Offline rekonstrukcija](reconstruction-offline.md).

| Opcija | Zadano | Značenje |
|---|---|---|
| `video` | obavezno | Snimak. Izlazni kod 2 ako ne postoji. |
| `-o`, `--out` | obavezno | `.glb` koji se zapisuje. |
| `--solve-budget` | `260` | Najviše kadrova predanih rješavaču. Razmaknuti su prema tome koliko se slika pomjera, ne prema satu. Više je tačnije i mnogo sporije. Više od 400 planiranih kadrova se odbija. |
| `--fuse-interval` | `0.4` | Sekunde između kadrova stopljenih u geometriju. |
| `--model` | `vggt-1b` | S kojim VGGT težinama rješavati: `vggt-1b` (`facebook/VGGT-1B`, nekomercijalno) ili `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, zaključano; treba pristup koji odobrava Meta). Linija o licenci koja se prva ispisuje je licenca tog modela. |

Prvo ispisuje liniju o licenci modela, zatim svaku fazu (`masking`, `planning`, `solving`,
`fusing`, `exporting`) s protekle sekunde i napretkom, te na kraju sažetak: riješene
kamere, greška zatvaranja, najgori šav, napomene i zapisana datoteka. Izlazni kod je 0 samo ako je
datoteka zapisana.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Čita HUD igre iz igračevog vlastitog snimka, nakon meča: igračeve vlastite
akcije iz iskočnog prozora s bodovima, smrti i oživljavanja iz ekrana pada i povratka u igru, trag
mini-mape i kill feed. Zapisuje `<out>.parquet` (trag i događaji, 3DHeat tabela),
`<out>.events.jsonl`, `<out>.summary.json` i `<out>.map.png` + `.map.json` (mozaik mini-mape
i njena sidra za sliku mape u pregledaču). Battlefield 6 (`bf6`) je za sada jedini profil.

Treba **ffmpeg i ffprobe** na PATH-u (`winget install Gyan.FFmpeg`, zatim novi terminal).

| Opcija | Zadano | Značenje |
|---|---|---|
| `video` | obavezno | Snimak. |
| `-o`, `--out` | naziv videa | Putanja izlaza bez nastavka. |
| `--game` | `bf6` | Čiji HUD čitati. |
| `--player` | pogađa se | Igračevo ime kako ga prikazuje kill feed, upoređuje se slobodno. |
| `--fps` | `5` | Uzoraka mini-mape u sekundi. |
| `--start`, `--seconds` | cijeli video | Dio snimka koji se čita. |
| `--metres-per-pixel` | nema | Razmjera mini-mape, kad je poznata; bez nje su pozicije u pikselima mini-mape. |
| `--cpu` | isključeno | Dekodirajte na CPU-u čak i kad postoji NVIDIA kartica. |

Puni opis: [Čitanje HUD-a iz snimka](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` renderuje nivo sa svakog mjesta na kojem igrač može stajati i indeksira rendere; `frames`
smješta svaki uzorkovani kadar snimka naspram njega, na osnovu slike, s tragom mini-mape iz komande
`hud` kao rezervom; `eval` upoređuje rezultat sa poznatim pozama kamere; `train` trenira
model mjesta po mapi na renderima nivoa (i na kadrovima koje je neko pokretanje već lociralo), za `build --head`;
`refmap` smješta vlastitu mapu igre (njen ekran za raspoređivanje) na nivo, a `minimap` čita
mini-mapu snimka naspram nje, kadar po kadar - prethodnik koji `frames --minimap` može uzeti. Treba PyTorch
i `requirements-locate.txt`. **Eksperimentalno:** na stvarnim snimcima za sada smješta samo mali dio
kadrova. Svaka opcija, izlazi i metoda:
[Lociranje kadrova u nivou](locate.md); puna lista opcija: [Referenca komandi](../cli-reference.md).

## The scan window {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ili dvostruki klik na `scan.bat`. Bez opcija. Pogledajte [Prozor za skeniranje](reconstruction-scan-ui.md).

## Updates {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Pogledajte [Ažuriranja](updates.md).

## The model converter {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Pretvara checkpoint modela Depth Anything V2 u ONNX datoteku koju skener pokreće. Treba PyTorch,
`transformers` i `onnxscript`. Pogledajte [Dubina](reconstruction-depth.md#building-the-model).
