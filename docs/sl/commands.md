---
title: "Pregled ukazov"
nav_order: 5
lang: "sl"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Pregled ukazov {#command-reference}

Vsi ukazi se zaženejo iz mape repozitorija, z okoljem projekta:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Ukaz | Naredi |
|---|---|
| [`route`](#route) | Zapiše samo položaje avta med Forza krogom, da na datotekah igre najdete zemljevid |
| [`telemetry`](#telemetry) | Zapiše vse kanale, za vsak krog svojo datoteko kroga, za zavihek Analiza dirke |
| [`laps`](#laps) | Prebere knjižnico krogov FH Companion in zapiše pot in vzorce ene proge |
| [`reconstruct`](#reconstruct) | Posnetek reši brez povezave in zapiše `.glb` |
| [`hud`](#hud) | Iz posnetka prebere igralčeva lastna dejanja, smrti in pot na zemljevidu ter seznam ubojev |
| [`locate`](#locate) | Kje je bil vzet vsak okvir posnetka, glede na upodobitve nivoja |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Okno za pregled |
| [`python -m heat3d_update`](#updates) | Preveri in namesti posodobitve |
| [`python tools/export_onnx.py`](#the-model-converter) | Pretvori globinski model v ONNX |

Ko zaženete `python -m heat3d_capture`, orodje najprej preveri, ali je na voljo novejša izdaja (glejte
[Posodobitve](updates.md); `HEAT3D_NO_UPDATE=1` to izklopi). `--help` za katerimkoli ukazom pokaže
njegove možnosti:

![Pomoč heat3d_capture --help](../assets/img/cli-help.svg)

Koda: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Posluša Forza Data Out in hrani samo položaje avta, nič drugega: brez globinskega modela, brez
GPU-ja, brez zajemanja. Koda: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Možnost | Privzeto | Pomen |
|---|---|---|
| `-o`, `--out` | obvezno | Pot izhoda; njena pripona se zamenja, tako `-o lap` zapiše `lap.npz` in `lap.json`. |
| `--port` | `5300` | Vrata, na katera igra pošilja (vezana na 127.0.0.1). |
| `--seconds` | `0` | Ustavi se po tolikšnem številu sekund; `0` teče, dokler ne pritisnete Ctrl+C. |

Položaj se shrani samo, če igra poroča, da teče dirka (`isRaceOn`), avto se premika hitreje od
0,5 m/s in je vsaj 0,5 m oddaljen od zadnjega shranjenega položaja. Sicer bi pri 60 paketih na
sekundo v meniju datoteka napolnjena s startno črto. Čas vzorca je dirkalni čas igre ali zidna ura,
če je ta 0. Postavitev se zazna enako kot pri `telemetry` (avto se mora najprej premakniti; glejte
[Forza](telemetry-forza.md)).

Enkrat na sekundo izpiše, koliko paketov je prejel, koliko položajev je shranil in trenutni položaj,
ali pa `nothing on port 5300 yet - is Data Out on?`. Pot se **shranjuje med vožnjo**: vsaki 2 sekundi,
ko pride nov položaj (razmak se poveča na dvajsetkratnik časa zadnjega shranjevanja, tako da zelo
dolga seja ne porabi več kot dvajsetino časa za pisanje), in še enkrat, ko se snemalnik ustavi iz
katerega koli razloga - Ctrl+C, `--seconds` ali napaka. Vsako shranjevanje najprej zapiše
`lap.npz.partial` / `lap.json.partial`, nato pa ju prestavi čez pravi datoteki, tako da so datoteke
na disku vedno cele; zrušitev ali ubita aplikacija izgubi največ zadnjih nekaj sekund. Če ni bilo
shranjenega ničesar, izpiše, kako vklopiti Data Out, in se konča s kodo 1.

Izhod:

- `lap.npz` - NumPy polja `positions` (n x 3, metri), `times`, `speeds` (m/s);
- `lap.json` - je berljiv brez tega projekta:

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

Položaji so svetovne koordinate igre, zaradi česar so ročaj za iskanje istega tal v datotekah igre:
ukaz `course` iz [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) vzame ta JSON in
izvozi progo, po kateri je krog tekel.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Vsaka možnost in vsaka igra sta opisani na [Snemalniki telemetrije](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Prebere knjižnico krogov, ki jo hrani FH Companion, in za eno progo zapiše dve datoteki: pot, ki
pove, kateri kos zemljevida izrezati iz igrinega arhiva, in tabelo vseh vzorcev vsakega kroga. Zapišeta
se hkrati, da se ne moreta razhajati. Koda:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Možnost | Privzeto | Pomen |
|---|---|---|
| `course` | nič | Ime proge, ujema se ohlapno. Če ga izpustite, izpiše knjižnico. |
| `-o`, `--out` | ime proge z malimi črkami, presledki kot `_` | Pot izhoda; `.json` in `.csv` se zapišeta drug ob drugem. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Kje so mape prog. |
| `--margin` | `80` | Metri, dodani okoli razsežnosti proge v x in z v `bounds` poti. |

### Izpis {#listing}

Brez proge izpiše število map prog in za vsako število datotek krogov (`*.json` kjerkoli pod njo, razen
`course.json`) ter ime proge, nato `Name one to write it out:  -o <file> <course>`.

### Iskanje proge {#finding-a-course}

Mape prog se imenujejo `<name> (course_<x>_<z>_to_<x>_<z>)` - začetek in cilj, zaokrožena. Proga se
najde po tem vrstnem redu: točno ime mape; del imena mape brez upoštevanja velikih in malih črk;
edinstvena mapa, katere ime vsebuje besedilo. Več zadetkov je napaka, ki jih našteje.

### Branje {#reading-it}

- `course.json` v mapi, če ga je mogoče prebrati, da ime ter nezaokrožen začetek in cilj (`Name`, `StartX`,
  `StartZ`, `FinishX`, `FinishZ`); sicer se vzamejo iz imena mape. Proga je označena kot krožna, če sta
  začetek in cilj manj kot 10 m narazen.
- Vsak drug `*.json` pod mapo je krog (krogi so globoko v podmapah - po razredu, avtu, nastavitvi,
  oznaki - iskanje pa je preprosto rekurzivno). Datoteke se berejo kot UTF-8 z oznako zaporedja bajtov
  (BOM). Krog, ki se ne da prebrati, se preskoči. Krogi so razvrščeni po času snemanja.
- Za vsak krog `Lap.samples` (vsak s `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`,
  `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), ter razred avta, zaporedno
  številko, indeks zmogljivosti, sekunde kroga, dolžino, čas snemanja in začetek iz mirovanja.

Izpiše povzetek (krogi, vzorci, najboljši krog in njegov razred, razsežnosti x/y/z).

### Izhod {#output}

**`<out>.json`** - enaka oblika poti kot jo zapiše `route`, zato jo izvleček zemljevida sprejme
kakršno koli že: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (razširjene za
`--margin` v x in z) ter `positions` **najhitrejšega** kroga (ena črta, ne razmaz vseh krogov).

**`<out>.csv`** - vsak vzorec vsakega kroga, po ena vrstica:

| Stolpec | Pomen |
|---|---|
| `course` | ime proge |
| `lap` | oznaka za vsak krog: datum in čas snemanja na minuto ter čas kroga |
| `car` | zaporedna številka avta |
| `car_class` | črka razreda zmogljivosti |
| `pi` | indeks zmogljivosti |
| `lap_seconds` | čas kroga |
| `speed_kmh` | hitrost v km/h |
| `x`, `y`, `z` | svetovni položaj, metri, 3 decimalke |
| `speed_ms` | hitrost, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | kakor jih beleži FH Companion |
| `metres` | pot vzdolž kroga, 3 decimalke |
| `elapsed` | sekunde od lastnega začetka kroga, 3 decimalke |

Vrednosti, ki niso položaji, so zapisane na 4 pomembne števke; položaji imajo fiksne decimalke, ker bi
4 pomembne števke proge privezale na mrežo po enem metru. Imena stolpcev so izbrana tako, da si
pregledovalnik datoteko razloži sam: `lap` postane seja (dva kroga istega avta se nikoli ne združita),
`car` stvar, ki se premika, `car_class` skupina za barvanje, `elapsed` časovna os (vsi krogi se poravnajo
ob svojem začetku).

Na koncu izpiše namig, kako iz igre z GameFiles izrezati zemljevid, z datoteko poti ali z izrecno škatlo.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Posnetek reši brez povezave, pot kamere pa VGGT reši naenkrat. Počasi: minute na okno na namiznem GPU-ju.
Potrebuje PyTorch, Hugging Face `transformers` in paket `vggt`, ki jih skener ne potrebuje: našteti so
v `requirements-offline.txt`, ukaz pa jih preveri, potem ko izpiše licenčno vrstico, in ponudi namestitev
manjkajočih (če zavrnete, izhodna koda 1). Celoten opis:
[Rekonstrukcija brez povezave](reconstruction-offline.md).

| Možnost | Privzeto | Pomen |
|---|---|---|
| `video` | obvezno | Posnetek. Izhodna koda 2, če ne obstaja. |
| `-o`, `--out` | obvezno | Datoteka `.glb`, ki jo zapišemo. |
| `--solve-budget` | `260` | Največ okvirjev, predanih reševalniku. Razmaknjeni so glede na to, koliko se slika premakne, ne glede na uro. Več pomeni natančneje in veliko počasneje. Več kot 400 načrtovanih okvirjev je zavrnjenih. |
| `--fuse-interval` | `0.4` | Sekunde med okvirji, zlitimi v geometrijo. |
| `--model` | `vggt-1b` | S katerimi VGGT utežmi reševati: `vggt-1b` (`facebook/VGGT-1B`, nekomercialno) ali `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, zaprt; dostop mora odobriti Meta). Licenčna vrstica, izpisana najprej, je tega modela. |

Najprej izpiše licenčno vrstico modela, nato vsako fazo (`masking`, `planning`, `solving`, `fusing`,
`exporting`) s pretečenimi sekundami in napredkom, na koncu pa povzetek: rešene kamere, napaka
sklenitve, najslabši šiv, opombe in zapisana datoteka. Izhodna koda je 0 samo, če je bila datoteka
zapisana.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Iz igralčevega lastnega posnetka po tekmi prebere HUD igre: igralčeva lastna dejanja iz pojavnega okna
točk, smrti in oživitve iz zaslonov padca in namestitve, pot na zemljevidu minimape ter seznam ubojev.
Zapiše `<out>.parquet` (pot in dogodki, tabela 3DHeat), `<out>.events.jsonl`, `<out>.summary.json` ter
`<out>.map.png` + `.map.json` (mozaik minimape in njeni sidri za možnost Slika zemljevida v
pregledovalniku). Battlefield 6 (`bf6`) je zaenkrat edini profil.

Potrebuje **ffmpeg in ffprobe** na PATH (`winget install Gyan.FFmpeg`, nato nov terminal).

| Možnost | Privzeto | Pomen |
|---|---|---|
| `video` | obvezno | Posnetek. |
| `-o`, `--out` | ime videa | Pot izhoda brez pripone. |
| `--game` | `bf6` | Čigav HUD se bere. |
| `--player` | ugotovljeno | Igralčevo ime, kakor ga prikazuje seznam ubojev, ujema se ohlapno. |
| `--fps` | `5` | Vzorci minimape na sekundo. |
| `--start`, `--seconds` | ves video | Del posnetka, ki se bere. |
| `--metres-per-pixel` | nič | Merilo minimape, če je znano; brez njega so položaji v slikovnih pikah minimape. |
| `--cpu` | izključeno | Dekodiraj na CPE-ju, tudi če je na voljo kartica NVIDIA. |

Celoten opis: [Branje HUD-a iz posnetka](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` upodobi nivo iz vsakega mesta, kjer lahko igralec stoji, in indeksira upodobitve; `frames`
postavi vsak vzorčen okvir posnetka na nivo po sliki, z potjo minimape iz ukaza `hud` kot rezervo;
`eval` primerja rezultat z znanimi položaji kamere; `train` nauči model mest za vsak zemljevid
na upodobitvah nivoja (in na okvirjih, ki jih je prejšnji zagon že našel), za `build --head`; `refmap` postavi igrino
lastno karto (njen zaslon namestitve) na nivo, `minimap` pa po okvirjih prebere minimapo posnetka glede
nanjo - to lahko vzame prejšnji `frames --minimap`. Potrebuje PyTorch in `requirements-locate.txt`.
**Eksperimentalno:** na pravih posnetkih zaenkrat postavi samo majhen delež okvirjev. Vse možnosti,
izhodi in metoda: [Iskanje okvirjev v nivoju](locate.md); celoten seznam možnosti:
[Pregled ukazov](../cli-reference.md).

## Okno za pregled {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

ali dvokliknite `scan.bat`. Brez možnosti. Glejte [Okno za pregled](reconstruction-scan-ui.md).

## Posodobitve {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Glejte [Posodobitve](updates.md).

## Pretvornik modela {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Pretvori kontrolno točko Depth Anything V2 v datoteko ONNX, ki jo zažene skener. Potrebuje PyTorch,
`transformers` in `onnxscript`. Glejte [Globina](reconstruction-depth.md#building-the-model).
