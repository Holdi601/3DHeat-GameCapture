---
title: Parancsreferencia
nav_order: 5
lang: "hu"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Parancsreferencia {#command-reference}

Minden parancs a tároló mappájából fut, a projekt környezetével:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Parancs | Mit csinál |
|---|---|
| [`route`](#route) | Egy Forza-kör pozícióit rögzíti, csak azokat, hogy megtalálja a térképet a játék fájljaiban |
| [`telemetry`](#telemetry) | Minden csatornát rögzít, körönként egy körfájlt, a **Versenyelemzés** fülhöz |
| [`laps`](#laps) | Beolvassa egy FH Companion körtárat, és egy pálya útvonalát és minden mintáját kiírja |
| [`reconstruct`](#reconstruct) | Offline megoldja a felvételt, és egy `.glb` fájlt ír |
| [`hud`](#hud) | Kiolvassa a felvételből a játékos saját akcióit, halálait és minitérkép-útvonalát, valamint az ölési naplót |
| [`locate`](#locate) | Megmutatja, hol készült a felvétel minden képkockája, a pálya renderjeihez képest |
| [`python -m heat3d_capture.ui`](#the-scan-window) | A szkennelő ablak |
| [`python -m heat3d_update`](#updates) | Frissítést keres és alkalmaz |
| [`python tools/export_onnx.py`](#the-model-converter) | A mélységmodellt ONNX-formátumra alakítja |

Ha `python -m heat3d_capture` néven indítod, az eszköz először megnézi, van-e újabb kiadás (lásd [Frissítések](updates.md); a `HEAT3D_NO_UPDATE=1` kikapcsolja ezt). Bármelyik alparancs után a `--help` kiírja a kapcsolóit:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

A Forza Data Out-ot figyeli, és csak az autó pozícióit tartja meg, mást nem: nincs mélységmodell, nincs GPU, nincs rögzítés. Kód: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Kapcsoló | Alapérték | Jelentés |
|---|---|---|
| `-o`, `--out` | kötelező | A kimeneti útvonal; a végződése lecserélődik, így a `-o lap` a `lap.npz` és a `lap.json` fájlt írja. |
| `--port` | `5300` | A port, amelyre a játék küld (a 127.0.0.1-re kötve). |
| `--seconds` | `0` | Ennyi másodperc után áll meg; a `0` Ctrl+C-ig fut. |

Egy pozíció csak akkor marad meg, ha a játék versenyt jelez (`isRaceOn`), az autó 0,5 m/s-nál gyorsabban megy, és legalább 0,5 m-re van az utoljára megtartott pozíciótól. Enélkül a menüben állva, másodpercenként 60 csomaggal a fájl tele lenne a rajtvonallal. Minden minta ideje a játék versenyideje, vagy a falióra, ha az nulla. Az elrendezést ugyanúgy érzékeli, mint a `telemetry` (az autónak először el kell mozdulnia; lásd [Forza](telemetry-forza.md)).

Másodpercenként kiírja a kapott csomagok számát, a megtartott pozíciókat és az aktuális pozíciót, vagy a `nothing on port 5300 yet - is Data Out on?` üzenetet. Az útvonal **vezetés közben mentődik**: 2 másodpercenként, ha azóta új pozíció érkezett (a szünet az utolsó mentés idejének húszszorosáig nő, így egy nagyon hosszú munkamenet az idejének legfeljebb huszadát tölti írással), és egyszer még, amikor a rögzítő bármilyen okból leáll: Ctrl+C, `--seconds`, vagy kivétel. Minden mentés először a `lap.npz.partial` / `lap.json.partial` fájlba ír, és csak utána írja át a valódi fájlt, így a lemezen lévő fájlok mindig épek. Összeomlás vagy megölt folyamat legfeljebb az utolsó néhány másodpercet veszíti el. Ha semmi nem került megtartásra, kiírja, hogyan kapcsold be a Data Outot, és 1-es kilépési kóddal lép ki.

Kimenet:

- `lap.npz` - NumPy-tömbök: `positions` (n x 3, méter), `times`, `speeds` (m/s);
- `lap.json` - a projekt nélkül is olvasható:

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

A pozíciók a játék saját világkoordinátái. Ettől lesznek fogóként, amellyel megtalálható ugyanaz a talaj a játék fájljaiban: a [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) `course` parancsa ezt a JSON-t fogadja, és kiexportálja a pályát, amelyen a kör ment.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Minden kapcsolót és játékot a [Telemetria-rögzítők](telemetry.md) oldal ír le.

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Beolvassa az FH Companion által tartott körtárat, és egy pályához két fájlt ír: egy útvonalat, amely megmondja, melyik térképdarabot kell kivágni a játék archívumából, és egy táblázatot minden kör minden mintájáról. Egyszerre íródnak, hogy ne kerülhessenek ki szinkronból. Kód: [`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Kapcsoló | Alapérték | Jelentés |
|---|---|---|
| `course` | nincs | A pálya neve, lazán egyezve. Ha kihagyod, a tár listázódik. |
| `-o`, `--out` | a pálya neve kisbetűvel, a szóközök `_` jelekkel | A kimeneti útvonal; a `.json` és a `.csv` egymás mellé íródik. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Hol vannak a pályamappák. |
| `--margin` | `80` | Méter, amelyet az útvonal `bounds`-jában a pálya kiterjedéséhez x és z irányban hozzáadnak. |

### Listázás {#listing}

Pálya nélkül kiírja a pályamappák számát, és mindegyikhez a körfájlok számát (a `*.json` fájlok bárhol a mappa alatt, a `course.json` kivételével), valamint a pálya nevét, majd a `Name one to write it out:  -o <file> <course>` sort.

### Pálya keresése {#finding-a-course}

A pályamappák neve `<name> (course_<x>_<z>_to_<x>_<z>)`: a rajt és a cél, kerekítve. A pályát ebben a sorrendben keresi: a pontos mappanév; a mappanév neves része, kis- és nagybetű figyelmen kívül hagyva; egy egyedi mappa, amelynek a neve tartalmazza a szöveget. Több találat hibát ad, amely fel is sorolja őket.

### Olvasás {#reading-it}

- A mappában lévő `course.json`, ha olvasható, megadja a nevet és a kerekítetlen rajtot és célt (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); különben ezek a mappanévből jönnek. A pályát körként jelöli, ha a rajt és a cél 10 m-nél közelebb van egymáshoz.
- A mappa alatt minden más `*.json` egy kör. A körök több mappamélységben vannak (osztály, autó, hangolás, címke szerint), a keresés ezért egyszerűen rekurzív. A fájlokat UTF-8-ként olvassa, bájtsorrend-jellel (BOM). Az olvashatatlan kört kihagyja. A köröket a rögzítési idejük szerint rendezi.
- Körönként: `Lap.samples` (mindegyik `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds` mezővel), valamint az autó osztálya, sorszáma, teljesítményindexe, körideje, hossza, rögzítési ideje és állórajtja.

Kiír egy összefoglalót: körök, minták, a legjobb kör és az osztálya, az x/y/z kiterjedés.

### Kimenet {#output}

**`<out>.json`** - ugyanaz az útvonal-alak, mint amit a `route` ír, így a térképkinyerő mindkettőt elfogadja: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (x és z irányban a `--margin` értékével kiterjesztve), és a **leggyorsabb** kör `positions` mezője (egy vonal, nem az összes kör elmosódása).

**`<out>.csv`** - minden kör minden mintája, soronként egy:

| Oszlop | Jelentés |
|---|---|
| `course` | a pálya neve |
| `lap` | körönként egy címke: a rögzítés dátuma és ideje percre pontosan, és a körido |
| `car` | az autó sorszáma |
| `car_class` | a teljesítményosztály betűje |
| `pi` | a teljesítményindex |
| `lap_seconds` | a kör ideje |
| `speed_kmh` | sebesség km/h-ban |
| `x`, `y`, `z` | világpozíció, méter, 3 tizedesjeggyel |
| `speed_ms` | sebesség, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | ahogy az FH Companion rögzíti |
| `metres` | távolság a kör mentén, 3 tizedesjeggyel |
| `elapsed` | másodpercek a kör saját kezdete óta, 3 tizedesjeggyel |

A nem pozíció-értékek 4 értékes jegyre íródnak. A pozíciók fix tizedesjegyet kapnak, mert a 4 értékes jegy egy méteres rácsra húzná rá a pályát. Az oszlopnevek úgy vannak megválasztva, hogy a nézegető utasítás nélkül is leképezze a fájlt: a `lap` lesz a munkamenet (két kör egy autóval soha nem kapcsolódik össze), a `car` a mozgó dolog, a `car_class` a színezés csoportja, az `elapsed` az időtengely (minden kör a saját kezdeténél sorakozik fel).

Végül tippet ír arra, hogyan vágd ki a térképet a játékból a GameFiles-szal: az útvonalfájllal vagy egy megadott dobozzal.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Offline rekonstruálja a felvételt, a kameraútvonalat egyszerre oldja meg a VGGT. Lassú: percekbe telik ablakonként egy asztali GPU-n. PyTorch, Hugging Face `transformers` és a `vggt` csomag kell, amire a szkenner nem: ezek a `requirements-offline.txt`-ben vannak. A parancs a licencsor kiírása után ellenőrzi őket, és felajánlja a hiányzók telepítését (1-es kilépési kód, ha elutasítod). Teljes leírás: [Offline rekonstrukció](reconstruction-offline.md).

| Kapcsoló | Alapérték | Jelentés |
|---|---|---|
| `video` | kötelező | A felvétel. 2-es kilépési kód, ha nem létezik. |
| `-o`, `--out` | kötelező | A kiírandó `.glb`. |
| `--solve-budget` | `260` | A megoldónak átadott legtöbb képkocka. Nem az óra szerint, hanem aszerint vannak elosztva, mennyire mozog a kép. Több pontosabb, és sokkal lassabb. 400 tervezett képkocka fölött elutasítja. |
| `--fuse-interval` | `0.4` | Másodpercek a geometriába olvasztott képkockák között. |
| `--model` | `vggt-1b` | Melyik VGGT-súlyokkal oldjon meg: `vggt-1b` (`facebook/VGGT-1B`, nem kereskedelmi) vagy `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, kapuzott; a Metától kapott hozzáférés kell). Az először kiírt licencsor az adott modellé. |

Először kiírja a modell licencsorát, majd minden szakaszt (`masking`, `planning`, `solving`, `fusing`, `exporting`) az eltelt másodpercekkel és az előrehaladással, végül összefoglalót: megoldott kamerák, zárási hiba, legrosszabb varrat, megjegyzések és a kiírt fájl. A kilépési kód csak akkor 0, ha íródott fájl.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

A játék HUD-ját olvassa ki a játékos saját felvételéből, a meccs után: a játékos saját akcióit a pontpopupból, a halálait és újraélesztéseit a leesési és bevetési képernyőkről, a minitérkép útvonalát és az ölési naplót. Ezeket írja: `<out>.parquet` (útvonal és események, egy 3DHeat-tábla), `<out>.events.jsonl`, `<out>.summary.json`, és `<out>.map.png` + `.map.json` (a minitérkép-mozaik és a horgonyai a nézegető **Térképkép** részéhez). A Battlefield 6 (`bf6`) az egyetlen eddigi profil.

Az **ffmpeg és az ffprobe** kell a PATH-on (`winget install Gyan.FFmpeg`, majd új terminál).

| Kapcsoló | Alapérték | Jelentés |
|---|---|---|
| `video` | kötelező | A felvétel. |
| `-o`, `--out` | a videó neve | Kimeneti útvonal kiterjesztés nélkül. |
| `--game` | `bf6` | Melyik HUD-ot olvassa. |
| `--player` | kitalálva | A játékos neve úgy, ahogy az ölési napló mutatja; lazán egyezve. |
| `--fps` | `5` | Minitérkép-minták másodpercenként. |
| `--start`, `--seconds` | a teljes videó | A felvétel része, amelyet olvasni kell. |
| `--metres-per-pixel` | nincs | A minitérkép léptéke, ha ismert; nélküle a pozíciók minitérkép-pixelekben vannak. |
| `--cpu` | ki | CPU-n dekódoljon akkor is, ha van NVIDIA-kártya. |

Teljes leírás: [A HUD olvasása felvételből](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

A `build` minden olyan helyről renderel egy pályát, ahol játékos állhat, és indexeli a renderelt képeket. A `frames` a felvétel minden mintavett képkockáját a kép alapján helyezi el a pályán, a `hud` parancs minitérkép-útvonalát tartalékként használva. Az `eval` összehasonlít egy eredményt ismert kamera-pózokkal. A `train` pályánként tanít egy helymodellt a pálya renderjein (és azokon a képkockákon, amelyeket egy futás már elhelyezett), a `build --head`-hez. A `refmap` a játék saját térképét (a bevetési képernyőjét) illeszti a pályára, a `minimap` pedig egy felvétel minitérképét képkockánként ehhez méri; ezt használhatja a `frames --minimap` előzetesnek. PyTorch és a `requirements-locate.txt` kell. **Kísérleti:** valódi felvételeken eddig csak a képkockák kis részét helyezi el. Minden kapcsoló, a kimenetek és a módszer: [Képkockák elhelyezése pályán](locate.md); a teljes kapcsolólista: [Parancsreferencia](../cli-reference.md).

<a id="the-scan-window"></a>
## A szkennelő ablak {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

vagy dupla kattintás a `scan.bat`-on. Nincs kapcsoló. Lásd [A szkennelő ablak](reconstruction-scan-ui.md).

<a id="updates"></a>
## Frissítések {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Lásd [Frissítések](updates.md).

<a id="the-model-converter"></a>
## A modellkonvertáló {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Egy Depth Anything V2 ellenőrzőpontot alakít át arra az ONNX-fájlra, amelyet a szkenner futtat. PyTorch, `transformers` és `onnxscript` kell. Lásd [Mélység](reconstruction-depth.md#building-the-model).
