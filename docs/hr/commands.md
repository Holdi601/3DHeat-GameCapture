---
title: "Referenca naredbi"
nav_order: 5
lang: "hr"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Referenca naredbi {#command-reference}

Sve naredbe pokrećete iz mape repozitorija, s okruženjem projekta:

```bash
.venv\Scripts\python -m heat3d_capture <naredba> [opcije]
```

| Naredba | Što radi |
|---|---|
| [`route`](#route) | Bilježi samo pozicije Forza kruga, za pronalazak karte u datotekama igre |
| [`telemetry`](#telemetry) | Bilježi sve kanale, jednu datoteku kruga po krugu, za karticu Analiza utrke |
| [`laps`](#laps) | Čita biblioteku krugova FH Companion i zapisuje rutu i uzorke jedne staze |
| [`reconstruct`](#reconstruct) | Rješava snimku izvan mreže i zapisuje `.glb` |
| [`hud`](#hud) | Iz snimke čita vlastite radnje igrača, smrti i trag na mini karti te popis ubojstava |
| [`locate`](#locate) | Gdje je uzet svaki kadar snimke, u odnosu na prikaze razine |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Prozor skeniranja |
| [`python -m heat3d_update`](#updates) | Provjerava i primjenjuje ažuriranje |
| [`python tools/export_onnx.py`](#the-model-converter) | Pretvara model dubine u ONNX |

Kad se pokrene kao `python -m heat3d_capture`, alat najprije provjerava noviju verziju (vidi
[Ažuriranja](updates.md); `HEAT3D_NO_UPDATE=1` ga isključuje). `--help` iza bilo koje naredbe
navodi njezine opcije:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

<a id="route"></a>
## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Sluša Forza Data Out i zadržava samo pozicije automobila, ništa više: bez modela dubine, bez
GPU-a, bez snimanja. Kod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opcija | Zadano | Značenje |
|---|---|---|
| `-o`, `--out` | obavezno | Putanja izlaza; nastavak se zamjenjuje, pa `-o lap` zapisuje `lap.npz` i `lap.json`. |
| `--port` | `5300` | Port na koji igra šalje podatke (veže se na 127.0.0.1). |
| `--seconds` | `0` | Zaustavi nakon toliko sekundi; `0` radi dok ne pritisnete Ctrl+C. |

Pozicija se zadržava samo dok igra javlja da traje utrka (`isRaceOn`), automobil se kreće brže od
0,5 m/s i udaljen je najmanje 0,5 m od posljednje zadržane pozicije. Inače bi sjedenje u izborniku
uz 60 paketa u sekundi ispunilo datoteku početnom linijom. Vrijeme svakog uzorka je vrijeme
utrke u igri, ili stvarno vrijeme ako je ono 0. Raspored se prepoznaje isto kao kod `telemetry`
(automobil se prvo mora pomaknuti; vidi [Forza](telemetry-forza.md)).

Jednom u sekundi ispisuje primljene pakete, zadržane pozicije i trenutačnu poziciju, ili
`nothing on port 5300 yet - is Data Out on?`. Ruta se **sprema dok se vozi**: svake 2 sekunde nakon
što stigne nova pozicija (razmak raste na dvadeset puta duže od prethodnog spremanja, pa vrlo
duga sesija nikad ne troši više od dvadesetine vremena na pisanje), i još jednom kad se snimanje
zaustavi iz bilo kojeg razloga: Ctrl+C, `--seconds` ili iznimka. Svako spremanje piše
`lap.npz.partial` / `lap.json.partial`, pa ih preimenuje u stvarnu datoteku, tako da su datoteke
na disku uvijek cjelovite; pad ili ubijeni proces gubi najviše zadnjih nekoliko sekundi. Ako nije
zadržana nijedna pozicija, ispisuje kako uključiti Data Out i završava s kodom 1.

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

Pozicije su vlastite svjetske koordinate igre, što ih čini polazištem za pronalazak istog tla u
datotekama igre: [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) naredba `course`
uzima ovaj JSON i izvozi stazu po kojoj je krug vožen.

<a id="telemetry"></a>
## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Svaka opcija i svaka igra opisane su na [Snimači telemetrije](telemetry.md).

<a id="laps"></a>
## laps {#laps}

```bash
python -m heat3d_capture laps                                   # popis staza
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Čita biblioteku krugova koju vodi FH Companion i zapisuje dvije datoteke za jednu stazu: rutu koja
kaže koji dio karte treba izrezati iz arhive igre te tablicu svakog uzorka svakog kruga. Zapisuju
se zajedno da ne mogu ispasti iz koraka. Kod:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opcija | Zadano | Značenje |
|---|---|---|
| `course` | nema | Naziv staze, traži se ohlapno. Izostavite za popis biblioteke. |
| `-o`, `--out` | naziv staze, malim slovima, razmaci kao `_` | Putanja izlaza; `.json` i `.csv` zapisuju se jedna uz drugu. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Gdje su mape staza. |
| `--margin` | `80` | Metri dodani oko opsega staze u x i z u `bounds` rute. |

### Popis {#listing}

Bez staze ispisuje broj mapa staza i, za svaku, broj datoteka krugova (`*.json` bilo gdje ispod nje
osim `course.json`) i naziv staze, zatim `Name one to write it out:  -o <file> <course>`.

### Pronalazak staze {#finding-a-course}

Mape staza nose naziv `<name> (course_<x>_<z>_to_<x>_<z>)` - start i cilj, zaokruženi. Staza se
traži redom: točan naziv mape; dio naziva prije zagrade, bez obzira na velika i mala slova;
jedinstvena mapa čiji naziv sadrži tekst. Više pogodaka je greška koja ih ispisuje.

### Čitanje {#reading-it}

- `course.json` u mapi, kad se može pročitati, daje naziv i nezaokružene start i cilj
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); inače se oni uzimaju iz naziva mape. Staza
  se prijavljuje kao kružna kad su start i cilj manje od 10 m udaljeni.
- Svaki drugi `*.json` ispod mape je krug (krugovi su nekoliko mapa duboko - po razredu, automobilu,
  postavkama, oznaci - a pretraga je jednostavno rekurzivna). Datoteke se čitaju kao UTF-8 s
  oznakom redoslijeda bajtova. Nečitljiv krug se preskače. Krugovi se slažu po vremenu snimanja.
- Po krugu: `Lap.samples` (svaki s `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), te razred
  automobila, redni broj, indeks performansi, vrijeme kruga, duljina, vrijeme snimanja i je li
  bio iz mirovanja.

Ispisuje sažetak (krugovi, uzorci, najbolji krug i njegov razred, raspon x/y/z).

### Izlaz {#output}

**`<out>.json`** - isti oblik rute kao što zapisuje `route`, pa karta izvlači bilo koju od
dviju: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (proširen za `--margin` u
x i z), te `positions` **najbržeg** kruga (jedna crta, a ne mrlja svih krugova).

**`<out>.csv`** - svaki uzorak svakog kruga, po jedan redak:

| Stupac | Značenje |
|---|---|
| `course` | naziv staze |
| `lap` | oznaka po krugu: datum i vrijeme snimanja do minute, i vrijeme kruga |
| `car` | redni broj automobila |
| `car_class` | slovo razreda performansi |
| `pi` | indeks performansi |
| `lap_seconds` | vrijeme kruga |
| `speed_kmh` | brzina u km/h |
| `x`, `y`, `z` | svjetska pozicija, metri, 3 decimale |
| `speed_ms` | brzina, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | kako ih bilježi FH Companion |
| `metres` | udaljenost duž kruga, 3 decimale |
| `elapsed` | sekunde od vlastitog starta kruga, 3 decimale |

Vrijednosti koje nisu pozicije zapisuju se s 4 značajne znamenke; pozicije imaju fiksne decimale,
jer bi 4 značajne znamenke stazu slijepile na mrežu od jednog metra. Nazivi stupaca odabrani su
tako da preglednik karte datoteku prepozna bez uputa: `lap` postaje sesija (dva kruga istog
automobila se nikad ne spajaju), `car` stvar koja se kreće, `car_class` skupina za bojenje,
`elapsed` vremenska os (svi krugovi se poravnavaju na svoj start).

Na kraju ispisuje savjet kako izrezati kartu iz igre pomoću GameFiles, s datotekom rute ili
eksplicitnim okvirom.

<a id="reconstruct"></a>
## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruira snimku izvan mreže, a putanja kamere riješi se odjednom pomoću VGGT-a. Sporo:
minute po prozoru na radnoj stanici s GPU-om. Treba PyTorch, Hugging Face `transformers` i paket
`vggt`, koje skener ne treba: navedeni su u `requirements-offline.txt`, a naredba ih provjerava
nakon što ispiše redak licence, pa nudi instalaciju onoga što nedostaje (izlazni kod 1 ako
odbijete). Potpuni opis: [Rekonstrukcija izvan mreže](reconstruction-offline.md).

| Opcija | Zadano | Značenje |
|---|---|---|
| `video` | obavezno | Snimka. Izlazni kod 2 ako ne postoji. |
| `-o`, `--out` | obavezno | `.glb` koji se zapisuje. |
| `--solve-budget` | `260` | Najviše kadrova predanih rješavaču. Razmaknuti su prema tome koliko se slika pomakla, a ne prema satu. Više je preciznije i puno sporije. Više od 400 planiranih kadrova se odbija. |
| `--fuse-interval` | `0.4` | Sekunde između kadrova spojenih u geometriju. |
| `--model` | `vggt-1b` | Koje VGGT težine koristiti za rješavanje: `vggt-1b` (`facebook/VGGT-1B`, nekomercijalno) ili `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, zaključano; pristup mora odobriti Meta). Redak licence ispisan prvi pripada tom modelu. |

Prvo ispisuje licencu modela, zatim svaku fazu (`masking`, `planning`, `solving`,
`fusing`, `exporting`) s proteklim sekundama i napretkom, a na kraju sažetak: riješene kamere,
pogreška zatvaranja, najgori šav, bilješke i zapisana datoteka. Izlazni kod je 0 samo ako je
datoteka zapisana.

<a id="hud"></a>
## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Iz vlastite snimke igrača, nakon utakmice, čita HUD igre: vlastite radnje igrača iz skočnog
prozora s bodovima, smrti i ponovna oživljavanja sa zaslona za oborene i zaslona za raspoređivanje,
trag na mini karti i popis ubojstava. Zapisuje `<out>.parquet` (trag i događaji, tablica za
3DHeat), `<out>.events.jsonl`, `<out>.summary.json` te `<out>.map.png` + `.map.json` (mozaik mini
karte i njezina sidra za prikaz **Slika karte** u pregledniku). Battlefield 6 (`bf6`) je zasad
jedini profil.

Treba **ffmpeg i ffprobe** na PATH-u (`winget install Gyan.FFmpeg`, pa novi terminal).

| Opcija | Zadano | Značenje |
|---|---|---|
| `video` | obavezno | Snimka. |
| `-o`, `--out` | naziv videa | Putanja izlaza bez nastavka. |
| `--game` | `bf6` | Čiji HUD se čita. |
| `--player` | pogađa se | Ime igrača kako ga prikazuje popis ubojstava, traži se ohlapno. |
| `--fps` | `5` | Uzoraka mini karte u sekundi. |
| `--start`, `--seconds` | cijeli video | Dio snimke koji se čita. |
| `--metres-per-pixel` | nema | Mjerilo mini karte, kad je poznato; bez njega su pozicije u pikselima mini karte. |
| `--cpu` | isključeno | Dekodiraj na procesoru čak i kad postoji NVIDIA kartica. |

Puni opis: [Čitanje HUD-a iz snimke](hud-video.md).

<a id="locate"></a>
## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` prikazuje razinu sa svakog mjesta na kojem igrač može stajati i indeksira prikaze;
`frames` smješta svaki uzorkovani kadar snimke prema njoj, iz slike, a trag mini karte naredbe
`hud` služi kao rezerva; `eval` uspoređuje rezultat s poznatim položajima kamere; `train` trenira
model mjesta za pojedinu kartu na prikazima razine (i na kadrovima koje je pokretanje već
smjestilo), za `build --head`; `refmap` smješta vlastitu kartu igre (njezin zaslon za
raspoređivanje) na razinu, a `minimap` čita mini kartu snimke prema njoj, kadar po kadar - to
može uzeti prethodni `frames --minimap`. Treba PyTorch i `requirements-locate.txt`.
**Eksperimentalno:** na pravim snimkama zasad smješta samo mali dio kadrova. Svaka opcija, izlazi
i metoda: [Traženje kadrova u razini](locate.md); potpuni popis opcija:
[Referenca naredbi](../cli-reference.md).

<a id="the-scan-window"></a>
## Prozor skeniranja {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ili dvostruki klik na `scan.bat`. Nema opcija. Vidi [Prozor skeniranja](reconstruction-scan-ui.md).

<a id="updates"></a>
## Ažuriranja {#updates}

```bash
python -m heat3d_update            # provjeri, i ažuriraj ako je izašla novija verzija
python -m heat3d_update --check    # samo reci je li izašla
```

Vidi [Ažuriranja](updates.md).

<a id="the-model-converter"></a>
## Pretvarač modela {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Pretvara kontrolnu točku Depth Anything V2 u ONNX datoteku koju skener pokreće. Treba PyTorch,
`transformers` i `onnxscript`. Vidi [Dubina](reconstruction-depth.md#building-the-model).
