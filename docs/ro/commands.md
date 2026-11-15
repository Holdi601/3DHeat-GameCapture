---
title: "Lista comenzilor"
nav_order: 5
lang: "ro"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Lista comenzilor {#command-reference}

Toate comenzile se rulează din folderul depozitului, cu mediul proiectului:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Comandă | Ce face |
|---|---|
| [`route`](#route) | Înregistrează doar pozițiile unui tur Forza, ca să găsească harta în fișierele jocului |
| [`telemetry`](#telemetry) | Înregistrează fiecare canal, câte un fișier pentru fiecare tur, pentru fila Analiza cursei |
| [`laps`](#laps) | Citește biblioteca de tururi FH Companion și scrie traseul și eșantioanele unui singur traseu |
| [`reconstruct`](#reconstruct) | Rezolvă o înregistrare offline și scrie un `.glb` |
| [`hud`](#hud) | Citește acțiunile, morțile și traseul de pe harta minimă ale jucătorului, precum și lista de eliminări, dintr-o înregistrare |
| [`locate`](#locate) | Unde a fost luat fiecare cadru al unei înregistrări, față de randările nivelului |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Fereastra de scanare |
| [`python -m heat3d_update`](#updates) | Verifică și aplică o actualizare |
| [`python tools/export_onnx.py`](#the-model-converter) | Convertește modelul de adâncime în ONNX |

Când este pornit ca `python -m heat3d_capture`, instrumentul verifică mai întâi dacă există o versiune
nouă (vezi [Actualizări](updates.md); `HEAT3D_NO_UPDATE=1` o dezactivează). `--help` după orice comandă
listează opțiunile ei:

![heat3d_capture --help](../assets/img/cli-help.svg)

Cod: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Ascultă Forza Data Out și păstrează doar pozițiile mașinii, nimic altceva: fără model de adâncime, fără
GPU, fără captură. Cod: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `-o`, `--out` | obligatorie | Calea de ieșire; sufixul ei este înlocuit, deci `-o lap` scrie `lap.npz` și `lap.json`. |
| `--port` | `5300` | Portul la care trimite jocul (legat de 127.0.0.1). |
| `--seconds` | `0` | Oprește după atâtea secunde; `0` rulează până la Ctrl+C. |

O poziție este păstrată doar cât timp jocul raportează o cursă (`isRaceOn`), mașina se mișcă mai repede de
0,5 m/s și este la cel puțin 0,5 m de ultima poziție păstrată. Altfel, stând într-un meniu la 60 de pachete
pe secundă, fișierul s-ar umple cu linia de start. Timpul fiecărui eșantion este timpul de cursă al jocului,
sau ceasul real când acesta este 0. Așezarea este detectată exact ca la `telemetry` (mașina trebuie să se
miște mai întâi; vezi [Forza](telemetry-forza.md)).

O dată pe secundă afișează pachetele primite, pozițiile păstrate și poziția curentă, sau
`nothing on port 5300 yet - is Data Out on?` (nimic pe portul 5300 încă - este Data Out pornit?). Traseul
este **salvat în timp ce este parcurs**: la fiecare 2 secunde, după ce a sosit o poziție nouă (intervalul
crește până la de douăzeci de ori cât a durat ultima salvare, astfel încât o sesiune foarte lungă să nu
petreacă niciodată mai mult de a douăzecea parte din timp scriind), și încă o dată când înregistratorul se
oprește din orice motiv - Ctrl+C, `--seconds` sau o excepție. Fiecare salvare scrie `lap.npz.partial` /
`lap.json.partial` și apoi le mută peste fișierele reale, astfel încât fișierele de pe disc să fie mereu
complete; o cădere sau un proces oprit pierde cel mult ultimele câteva secunde. Dacă nu s-a păstrat nimic,
afișează cum se pornește Data Out și iese cu codul 1.

Rezultat:

- `lap.npz` - matrice NumPy: `positions` (n x 3, metri), `times`, `speeds` (m/s);
- `lap.json` - citibil fără acest proiect:

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

Pozițiile sunt coordonatele lumii ale jocului, și tocmai asta le face un reper pentru a găsi același teren
în fișierele jocului: comanda `course` din [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
citește acest JSON și exportă traseul peste care a rulat tura.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Fiecare opțiune și fiecare joc sunt descrise în [Înregistratoare de telemetrie](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Citește biblioteca de tururi pe care o ține FH Companion și scrie două fișiere pentru un singur traseu: un
traseu care spune ce bucată de hartă să fie tăiată din arhiva jocului, și un tabel cu fiecare eșantion din
fiecare tur. Sunt scrise împreună, ca să nu ajungă niciodată nepotrivite. Cod:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `course` | niciunul | Numele traseului, potrivit aproximativ. Lipsește ca să fie listată biblioteca. |
| `-o`, `--out` | numele traseului, cu litere mici, spațiile ca `_` | Calea de ieșire; `.json` și `.csv` sunt scrise unul lângă altul. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Unde sunt folderele traseelor. |
| `--margin` | `80` | Metri adăugați în jurul întinderii traseului, pe x și z, în `bounds` din traseu. |

### Listarea {#listing}

Fără un traseu, afișează numărul de foldere de trasee și, pentru fiecare, numărul de fișiere de tur
(`*.json` oriunde sub el, în afară de `course.json`) și numele traseului, apoi
`Name one to write it out:  -o <file> <course>` (alege unul și scrie-l: `-o <fișier> <traseu>`).

### Găsirea unui traseu {#finding-a-course}

Folderele de trasee se numesc `<nume> (course_<x>_<z>_to_<x>_<z>)` - linia de start și de sosire,
rotunjite. Un traseu este găsit, în ordine, după: numele exact al folderului; partea de nume din numele
folderului, fără a ține cont de majuscule; un folder unic al cărui nume conține textul. Mai multe potriviri
înseamnă o eroare care le listează.

### Citirea {#reading-it}

- `course.json` din folder, când poate fi citit, dă numele și linia de start și de sosire nerotunjite
  (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); altfel, acestea vin din numele folderului. Un traseu
  este raportat ca circuit când start și sosire sunt la mai puțin de 10 m unul de altul.
- Fiecare alt `*.json` de sub folder este un tur (tururile stau la câteva foldere adâncime - după clasă,
  mașină, reglaj, etichetă - iar căutarea este pur și simplu recursivă). Fișierele sunt citite ca UTF-8 cu
  marcaj de ordine a octeților. Un tur care nu poate fi citit este sărit. Tururile sunt sortate după ora
  înregistrării.
- Pentru fiecare tur: `Lap.samples` (fiecare cu `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), plus clasa mașinii,
  ordinalul, indicele de performanță, secundele turului, lungimea, ora înregistrării și start din loc.

Afișează un rezumat (ture, eșantioane, cel mai bun tur și clasa lui, întinderea pe x/y/z).

### Rezultat {#output}

**`<out>.json`** - aceeași formă de traseu pe care o scrie `route`, astfel încât extractorul de hărți le
acceptă pe amândouă: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (mărit cu `--margin` pe
x și z) și `positions` ale turului **cel mai rapid** (o linie, nu o pată din fiecare tur).

**`<out>.csv`** - fiecare eșantion din fiecare tur, câte un rând:

| Coloană | Înseamnă |
|---|---|
| `course` | numele traseului |
| `lap` | o etichetă pentru fiecare tur: data și ora înregistrării, până la minut, și timpul turului |
| `car` | ordinalul mașinii |
| `car_class` | litera clasei de performanță |
| `pi` | indicele de performanță |
| `lap_seconds` | timpul turului |
| `speed_kmh` | viteza în km/h |
| `x`, `y`, `z` | poziția în lume, metri, 3 zecimale |
| `speed_ms` | viteza, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | așa cum le înregistrează FH Companion |
| `metres` | distanța de-a lungul turului, 3 zecimale |
| `elapsed` | secunde de la începutul propriu al turului, 3 zecimale |

Valorile care nu sunt poziții sunt scrise cu 4 cifre semnificative; pozițiile primesc zecimale fixe, pentru
că 4 cifre semnificative ar fixa un traseu pe o grilă de un metru. Numele coloanelor sunt alese astfel încât
vizualizatorul să mapeze fișierul fără să i se spună: `lap` devine sesiunea (două ture ale aceleiași mașini
nu se unesc niciodată), `car` lucrul care se mișcă, `car_class` grupul după care se colorează, `elapsed`
axa timpului (fiecare tur se aliniază la propriul start).

La final afișează un indiciu pentru tăierea hărții din joc cu GameFiles, cu fișierul de traseu sau o cutie
explicită.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Reconstruiește o înregistrare offline, cu traiectoria camerei rezolvată dintr-o dată de VGGT. Lent: minute
pentru fiecare fereastră pe un GPU de desktop. Are nevoie de PyTorch, Hugging Face `transformers` și pachetul
`vggt`, pe care scanerul nu le cere: sunt listate în `requirements-offline.txt`, iar comanda le verifică după
ce afișează linia de licență și propune instalarea celor care lipsesc (cod de ieșire 1 dacă este refuzată).
Descriere completă: [Reconstrucție offline](reconstruction-offline.md).

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `video` | obligatorie | Înregistrarea. Cod de ieșire 2 dacă nu există. |
| `-o`, `--out` | obligatorie | `.glb` de scris. |
| `--solve-budget` | `260` | Cele mai multe cadre date solverului. Sunt distanțate după cât se mișcă imaginea, nu după ceas. Mai multe înseamnă mai precis și mult mai lent. Peste 400 de cadre planificate este refuzat. |
| `--fuse-interval` | `0.4` | Secunde între cadrele îmbinate în geometrie. |
| `--model` | `vggt-1b` | Ce greutăți VGGT se folosesc la rezolvare: `vggt-1b` (`facebook/VGGT-1B`, necomercial) sau `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, cu acces restricționat; necesită acces acordat de Meta). Linia de licență afișată prima este a modelului respectiv. |

Afișează mai întâi linia de licență a modelului, apoi fiecare etapă (`masking`, `planning`, `solving`,
`fusing`, `exporting`) cu secundele scurse și progresul, și în final un rezumat: camere rezolvate, eroare de
închidere, cea mai slabă cusătură, note și fișierul scris. Codul de ieșire este 0 doar dacă a fost scris un
fișier.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Citește HUD-ul jocului din propria înregistrare a jucătorului, după meci: acțiunile jucătorului din fereastra
de puncte, morțile și reanimările din ecranele de cădere și de desfășurare, traseul de pe harta minimă și
lista de eliminări. Scrie `<out>.parquet` (traseu și evenimente, un tabel 3DHeat), `<out>.events.jsonl`,
`<out>.summary.json` și `<out>.map.png` + `.map.json` (mozaicul hărții minime și punctele lui de ancorare
pentru imaginea de hartă a vizualizatorului). Battlefield 6 (`bf6`) este singurul profil de până acum.

Are nevoie de **ffmpeg și ffprobe** în PATH (`winget install Gyan.FFmpeg`, apoi un terminal nou).

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `video` | obligatorie | Înregistrarea. |
| `-o`, `--out` | numele videoclipului | Calea de ieșire fără extensie. |
| `--game` | `bf6` | al cărui HUD se citește. |
| `--player` | ghicit | Numele jucătorului așa cum îl arată lista de eliminări, potrivit aproximativ. |
| `--fps` | `5` | Eșantioane de hartă minimă pe secundă. |
| `--start`, `--seconds` | tot videoclipul | Partea înregistrării care se citește. |
| `--metres-per-pixel` | niciunul | Scara hărții minime, când este cunoscută; fără ea pozițiile sunt în pixeli ai hărții minime. |
| `--cpu` | oprit | Decodează pe procesor chiar când există un card NVIDIA. |

Progresul se afișează la fiecare cinci secunde; la final, jucătorul, eliminările, morțile, viețile și fișierele
scrise.

Descriere completă: [Citirea HUD-ului dintr-o înregistrare](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` randează un nivel din fiecare loc unde poate sta un jucător și indexează randările; `frames` așază
fiecare cadru eșantionat al unei înregistrări față de ele, după imagine, cu traseul de pe harta minimă din
comanda `hud` ca rezervă; `eval` compară un rezultat cu pozele cunoscute ale camerei; `train` antrenează un
model de locuri pentru fiecare hartă, pe randările nivelului (și pe cadrele pe care o rulare deja le-a
localizat), pentru `build --head`; `refmap` așază harta jocului însăși (ecranul ei de desfășurare) pe nivel,
iar `minimap` citește harta minimă a unei înregistrări față de ea, cadru cu cadru - ce poate lua `frames
--minimap` înainte. Are nevoie de PyTorch și de `requirements-locate.txt`. **Experimental:** pe înregistrări
reale plasează, deocamdată, doar o mică parte din cadre. Fiecare opțiune, rezultatele și metoda:
[Localizarea cadrelor într-un nivel](locate.md); lista completă a opțiunilor: [Lista comenzilor](../cli-reference.md).

## Fereastra de scanare {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

sau dublu-clic pe `scan.bat`. Fără opțiuni. Vezi [Fereastra de scanare](reconstruction-scan-ui.md).

## Actualizări {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Vezi [Actualizări](updates.md).

## Convertorul de model {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Convertește un punct de control Depth Anything V2 în fișierul ONNX pe care îl rulează scanerul. Are nevoie de
PyTorch, `transformers` și `onnxscript`. Vezi [Adâncime](reconstruction-depth.md#building-the-model).
