---
title: "Prehľad príkazov"
nav_order: 5
lang: "sk"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Prehľad príkazov {#command-reference}

Všetky príkazy sa spúšťajú z priečinka repozitára, s prostredím projektu:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Príkaz | Robí |
|---|---|
| [`route`](#route) | Zaznamená len pozície auta z kola Forzy, aby sa mapa dala nájsť v herných súboroch |
| [`telemetry`](#telemetry) | Zaznamená každý kanál, jeden súbor kola na každé kolo, pre kartu Analýza pretekov |
| [`laps`](#laps) | Prečíta knižnicu kôl FH Companion a zapíše trasu a vzorky jednej trate |
| [`reconstruct`](#reconstruct) | Vyrieši nahrávku offline a zapíše `.glb` |
| [`hud`](#hud) | Z nahrávky prečíta vlastné akcie hráča, smrti, stopu na minimape a prúd zabití |
| [`locate`](#locate) | Zistí, kde bol každý snímok nahrávky, podľa vykreslení úrovne |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Okno skenovania |
| [`python -m heat3d_update`](#updates) | Skontroluje a nainštaluje aktualizáciu |
| [`python tools/export_onnx.py`](#the-model-converter) | Prevedie model hĺbky do ONNX |

Keď spustíte `python -m heat3d_capture`, nástroj najprv skontroluje, či nie je novšie vydanie (pozrite [Aktualizácie](updates.md); `HEAT3D_NO_UPDATE=1` ju vypne). `--help` za ľubovoľným príkazom vypíše jeho možnosti:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Počúva Forza Data Out a uchováva len pozície auta, nič iné: žiadny model hĺbky, žiadne GPU, žiadne snímanie. Kód: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Možnosť | Predvolené | Význam |
|---|---|---|
| `-o`, `--out` | povinné | Cesta výstupu; jej prípona sa nahradí, takže `-o lap` zapíše `lap.npz` a `lap.json`. |
| `--port` | `5300` | Port, na ktorý hra posiela dáta (viaže sa na 127.0.0.1). |
| `--seconds` | `0` | Zastaví sa po tomto počte sekúnd; `0` beží, kým nestlačíte Ctrl+C. |

Pozícia sa uloží, len keď hra hlási pretek (`isRaceOn`), auto sa hýbe rýchlejšie ako 0,5 m/s a je aspoň 0,5 m od poslednej uloženej pozície. Inak by pri 60 paketoch za sekundu v ponuke súbor zaplnil štartovou čiarou. Čas každej vzorky je herný čas pretekov, alebo hodinový čas, keď je herný čas nula. Rozloženie sa zisťuje rovnako ako pri `telemetry` (auto sa musí najprv pohnúť; pozrite [Forza](telemetry-forza.md)).

Raz za sekundu vypíše počet prijatých paketov, počet uložených pozícií a aktuálnu pozíciu, alebo `nothing on port 5300 yet - is Data Out on?`. Trasa sa **ukladá počas jazdy**: každé 2 sekundy, keď prišla nová pozícia (odstup narastá na dvadsaťnásobok času posledného uloženia, takže veľmi dlhá relácia nikdy nestrávi viac ako dvadsatinu času zápisom), a ešte raz, keď sa rekordér zastaví z akéhokoľvek dôvodu: Ctrl+C, `--seconds` alebo výnimka. Každé uloženie zapíše `lap.npz.partial` / `lap.json.partial` a potom ich presunie na skutočné súbory, takže súbory na disku sú vždy celé. Pád alebo zabitý proces stratí najviac posledných pár sekúnd. Ak sa nič neuložilo, vypíše, ako zapnúť Data Out, a skončí s kódom 1.

Výstup:

- `lap.npz` - polia NumPy `positions` (n x 3, metre), `times`, `speeds` (m/s);
- `lap.json` - čitateľné bez tohto projektu:

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

Pozície sú svetové súradnice hry, a práve preto sú vodítkom na nájdenie tej istej zeme v herných súboroch: príkaz `course` z [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) berie tento JSON a exportuje trať, po ktorej kolo išlo.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Každá voľba a každá hra sú opísané na [Telemetrické rekordéry](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Číta knižnicu kôl, ktorú si vedie FH Companion, a pre jednu trať zapíše dva súbory: trasu, ktorá hovorí, ktorý kus mapy vyrezať z herného archívu, a tabuľku každej vzorky každého kola. Zapisujú sa spoločne, aby sa nemohli rozísť. Kód: [`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Možnosť | Predvolené | Význam |
|---|---|---|
| `course` | žiadne | Názov trate, hľadaný približne. Keď ho vynecháte, vypíše knižnicu. |
| `-o`, `--out` | názov trate malými písmenami, medzery ako `_` | Cesta výstupu; `.json` a `.csv` sa zapíšu vedľa seba. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Kde sú priečinky tratí. |
| `--margin` | `80` | Metre pridané okolo rozsahu trate v x a z v `bounds` trasy. |

### Výpis {#listing}

Bez trate vypíše počet priečinkov tratí a pre každú trať počet súborov kôl (`*.json` kdekoľvek pod ním okrem `course.json`) a jej názov. Potom riadok `Name one to write it out:  -o <file> <course>`.

### Hľadanie trate {#finding-a-course}

Priečinky tratí sa volajú `<name> (course_<x>_<z>_to_<x>_<z>)`: štart a cieľ, zaokrúhlené. Trať sa nájde v tomto poradí: presný názov priečinka; časť názvu bez ohľadu na veľkosť písmen; jedinečný priečinok, ktorého názov obsahuje zadaný text. Viacero zhôd je chyba a vypíše ich všetky.

### Čítanie {#reading-it}

- `course.json` v priečinku, ak sa dá prečítať, dá názov a nezaokrúhlený štart a cieľ (`Name`, `StartX`, `StartZ`, `FinishX`, `FinishZ`); inak sa berú z názvu priečinka. Trať sa označí ako okruh, keď sú štart a cieľ menej ako 10 m od seba.
- Každý ďalší `*.json` pod priečinkom je kolo. Kolá sú niekoľko priečinkov hlbšie (podľa triedy, auta, ladenia, značky) a hľadanie je jednoducho rekurzívne. Súbory sa čítajú ako UTF-8 s BOM. Nečitateľné kolo sa preskočí. Kolá sa zoradia podľa času nahrávania.
- Pre každé kolo: `Lap.samples` (každá vzorka s `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`, `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`), a trieda auta, poradie, výkonnostný index, čas kola, dĺžka, čas nahrávania a štart zo stoja.

Vypíše súhrn: počet kôl, vzoriek, najlepšie kolo a jeho triedu a rozsah x/y/z.

### Výstup {#output}

**`<out>.json`**: rovnaký tvar trasy, aký zapisuje `route`, takže extraktor mapy prijme oba: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (rozšírené o `--margin` v x a z) a `positions` z **najrýchlejšieho** kola. Je to jedna čiara namiesto machu všetkých kôl.

**`<out>.csv`**: každá vzorka každého kola, jeden riadok na vzorku:

| Stĺpec | Význam |
|---|---|
| `course` | názov trate |
| `lap` | označenie každého kola: dátum a čas nahrávania na minútu a čas kola |
| `car` | poradové číslo auta |
| `car_class` | písmeno výkonnostnej triedy |
| `pi` | výkonnostný index |
| `lap_seconds` | čas kola |
| `speed_kmh` | rýchlosť v km/h |
| `x`, `y`, `z` | pozícia vo svete, metre, 3 desatinné miesta |
| `speed_ms` | rýchlosť v m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | tak, ako ich zaznamenáva FH Companion |
| `metres` | vzdialenosť pozdĺž kola, 3 desatinné miesta |
| `elapsed` | sekundy od vlastného štartu kola, 3 desatinné miesta |

Nepozičné hodnoty sa zapisujú na 4 platné číslice. Pozície majú pevné desatinné miesta, lebo 4 platné číslice by trať prichytili na mriežku s krokom jeden meter. Názvy stĺpcov sú zvolené tak, aby prehliadač súbor namapoval bez ďalšieho nastavenia: `lap` sa stane reláciou (dve kolá tým istým autom sa nikdy nespoja), `car` vecou, ktorá sa hýbe, `car_class` skupinou na farbenie a `elapsed` časovou osou (každé kolo sa zarovná na svoj štart).

Nakoniec vypíše tip, ako vyrezať mapu z hry pomocou GameFiles, so súborom trasy alebo s výslovne zadaným obdĺžnikom.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonštruuje nahrávku offline, s dráhou kamery vyriešenou naraz pomocou VGGT. Je to pomalé: minúty na okno na desktopovom GPU. Potrebuje PyTorch, Hugging Face `transformers` a balík `vggt`, ktoré skener nepotrebuje. Sú vypísané v `requirements-offline.txt` a príkaz ich skontroluje po výpise licenčného riadka. Ak chýbajú, ponúkne ich nainštalovať (kód 1, ak ponuku odmietnete). Úplný opis: [Offline rekonštrukcia](reconstruction-offline.md).

| Možnosť | Predvolené | Význam |
|---|---|---|
| `video` | povinné | Nahrávka. Kód 2, ak neexistuje. |
| `-o`, `--out` | povinné | `.glb`, ktoré sa zapíše. |
| `--solve-budget` | `260` | Najviac snímok odovzdaných riešiteľovi. Rozložia sa podľa toho, o koľko sa obraz pohol, nie podľa hodín. Viac znamená presnejšie a oveľa pomalšie. Viac ako 400 plánovaných snímok sa odmietne. |
| `--fuse-interval` | `0.4` | Sekundy medzi snímkami zlúčenými do geometrie. |
| `--model` | `vggt-1b` | Ktoré váhy VGGT použiť na riešenie: `vggt-1b` (`facebook/VGGT-1B`, nekomerčné) alebo `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, s prístupom; prístup musí udeliť Meta). Licenčný riadok, ktorý sa vypíše ako prvý, patrí tomuto modelu. |

Najprv vypíše licenčný riadok modelu. Potom každú fázu (`masking`, `planning`, `solving`, `fusing`, `exporting`) s uplynutými sekundami a priebehom. Nakoniec súhrn: riešené kamery, chyba uzavretia slučky, najhorší spoj, poznámky a zapísaný súbor. Kód výstupu je 0, len ak sa súbor zapísal.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Prečíta HUD hry z vlastnej nahrávky hráča, až po zápase: vlastné akcie hráča z vyskakovacieho okna bodov, smrti a oživenia z obrazoviek pádu a nasadenia, stopu hráča na minimape a prúd zabití. Zapíše `<out>.parquet` (stopa a udalosti, tabuľka 3DHeat), `<out>.events.jsonl`, `<out>.summary.json` a `<out>.map.png` + `.map.json` (mozaika minimapy a jej kotvy pre zobrazenie **Obrázok mapy** v prehliadači). Battlefield 6 (`bf6`) je zatiaľ jediný profil.

Potrebuje **ffmpeg a ffprobe** v `PATH` (`winget install Gyan.FFmpeg`, potom nový terminál).

| Možnosť | Predvolené | Význam |
|---|---|---|
| `video` | povinné | Nahrávka. |
| `-o`, `--out` | názov videa | Cesta výstupu bez prípony. |
| `--game` | `bf6` | Čie HUD sa číta. |
| `--player` | odhadnuté | Meno hráča tak, ako ho ukazuje prúd zabití, porovnané približne. |
| `--fps` | `5` | Vzorky minimapy za sekundu. |
| `--start`, `--seconds` | celé video | Časť nahrávky, ktorá sa číta. |
| `--metres-per-pixel` | žiadne | Mierka minimapy, keď je známa. Bez nej sú pozície v pixloch minimapy. |
| `--cpu` | vypnuté | Dekódovať na CPU, aj keď je karta NVIDIA. |

Úplný opis: [Čítanie HUD z nahrávky](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` vykreslí úroveň zo všetkých miest, na ktorých môže hráč stáť, a zaindexuje vykreslenia. `frames` umiestni každý vzorkovaný snímok nahrávky podľa obrázku, a ak to nejde, podľa stopy minimapy z príkazu `hud`. `eval` porovná výsledok so známymi pózami kamery. `train` natrénuje model miest pre jednu mapu na vykresleniach úrovne (a na snímkach, ktoré už beh našiel), pre `build --head`. `refmap` umiestni vlastnú mapu hry (jej obrazovku nasadenia) na úroveň a `minimap` prečíta minimapu nahrávky voči nej, snímok po snímku. Ten môže `locate frames --minimap` použiť ako predchádzajúci odhad. Potrebuje PyTorch a `requirements-locate.txt`. **Experimentálne:** na skutočných nahrávkach zatiaľ umiestni len malú časť snímok. Všetky voľby, výstupy a metóda: [Lokalizácia snímok v úrovni](locate.md). Úplný zoznam volieb: [Prehľad príkazov](../cli-reference.md).

## Okno skenovania {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

alebo dvojklik na `scan.bat`. Žiadne voľby. Pozrite [Okno skenovania](reconstruction-scan-ui.md).

## Aktualizácie {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Pozrite [Aktualizácie](updates.md).

## Prevodník modelu {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Prevedie kontrolný bod Depth Anything V2 na súbor ONNX, ktorý skener spúšťa. Potrebuje PyTorch, `transformers` a `onnxscript`. Pozrite [Hĺbka](reconstruction-depth.md#building-the-model).
