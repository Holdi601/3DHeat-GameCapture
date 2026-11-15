---
title: Přehled příkazů
nav_order: 5
lang: "cs"
source: commands.md
source_hash: "2d4420053a98"
nav_exclude: true
search_exclude: true
---
# Přehled příkazů {#command-reference}

Všechny příkazy se spouštějí ze složky repozitáře, s prostředím projektu:

```bash
.venv\Scripts\python -m heat3d_capture <verb> [options]
```

| Příkaz | Co dělá |
|---|---|
| [`route`](#route) | Zaznamená jen pozice jednoho kola Forzy, aby se našla mapa v herních souborech |
| [`telemetry`](#telemetry) | Zaznamená každý kanál, jeden soubor kola na kolo, pro kartu Analýza závodu |
| [`laps`](#laps) | Přečte knihovnu kol FH Companion a zapíše trasu a vzorky jedné trati |
| [`reconstruct`](#reconstruct) | Offline vyřeší záznam a zapíše `.glb` |
| [`hud`](#hud) | Z záznamu přečte vlastní akce hráče, smrti a stopu na minimapě a zprávy o zabitích |
| [`locate`](#locate) | Kde byl pořízen každý snímek záznamu, podle vykreslení levelu |
| [`python -m heat3d_capture.ui`](#the-scan-window) | Okno skenování |
| [`python -m heat3d_update`](#updates) | Zkontroluje a nainstaluje aktualizaci |
| [`python tools/export_onnx.py`](#the-model-converter) | Převede model hloubky do ONNX |

Když se spustí jako `python -m heat3d_capture`, nejdřív zkontroluje, jestli není novější verze
(viz [Aktualizace](updates.md); `HEAT3D_NO_UPDATE=1` ji vypne). `--help` za libovolným příkazem
vypíše jeho volby:

![heat3d_capture --help](../assets/img/cli-help.svg)

Kód: [`heat3d_capture/__main__.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/__main__.py).

## route {#route}

```bash
python -m heat3d_capture route -o lap [--port 5300] [--seconds 0]
```

Naslouchá Forza Data Out a ukládá jen pozice auta, nic jiného: žádný model hloubky, žádná GPU,
žádné zachytávání. Kód: [`telemetry/record.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/record.py).

| Volba | Výchozí | Význam |
|---|---|---|
| `-o`, `--out` | povinné | Cesta k výstupu; její přípona se nahradí, takže `-o lap` zapíše `lap.npz` a `lap.json`. |
| `--port` | `5300` | Port, na který hra posílá data (naslouchá na 127.0.0.1). |
| `--seconds` | `0` | Zastaví se po tolika sekundách; `0` běží, dokud se nestiskne Ctrl+C. |

Pozice se uloží jen tehdy, když hra hlásí závod (`isRaceOn`), auto jede rychleji než
0,5 m/s a je nejméně 0,5 m od poslední uložené pozice. Jinak by se při 60 paketech za sekundu
v menu do souboru zapsal startovní rošt. Čas každého vzorku je závodní čas hry, nebo čas
hodin, když je tento čas 0. Rozložení se zjistí stejně jako u `telemetry` (auto musí nejdřív
popojet; viz [Forza](telemetry-forza.md)).

Jednou za sekundu vypíše počet přijatých paketů, počet uložených pozic a aktuální pozici, nebo
`nothing on port 5300 yet - is Data Out on?`. Trasa se **ukládá během jízdy**: každé dva
sekundy, jakmile přišla nová pozice (interval naroste až na dvacetinásobek doby posledního
uložení, takže velmi dlouhé sezení nikdy netráví zápisem víc než jednu dvacetinu času), a ještě
jednou, když se záznam zastaví z jakéhokoli důvodu - Ctrl+C, `--seconds`, nebo výjimka. Každé
uložení zapíše `lap.npz.partial` / `lap.json.partial` a pak je přesune na skutečné místo, takže
soubory na disku jsou vždy celé; pád nebo ukončený proces ztratí nejvýš posledních několik
sekund. Když se neuložila žádná pozice, vypíše, jak zapnout Data Out, a skončí s kódem 1.

Výstup:

- `lap.npz` - pole NumPy `positions` (n x 3, metry), `times`, `speeds` (m/s);
- `lap.json` - čitelný i bez tohoto projektu:

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

Pozice jsou světové souřadnice hry, a právě proto slouží jako odkaz na stejný terén v herních
souborech: příkaz `course` z [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
přečte tento JSON a vyexportuje trať, po které kolo vedlo.

## telemetry {#telemetry}

```bash
python -m heat3d_capture telemetry [--game GAME] [-o laps] [--port 5300] [--forward HOST:PORT]
                                   [--install] [--configure CONFIG_JSON] [--surface SURFACE]
```

Každou volbu a každou hru popisuje [Záznamníky telemetrie](telemetry.md).

## laps {#laps}

```bash
python -m heat3d_capture laps                                   # list the courses
python -m heat3d_capture laps "a racing circuit" -o races/circuit [--library DIR] [--margin 80]
```

Přečte knihovnu kol, kterou vede FH Companion, a zapíše dva soubory pro jednu trať: trasu, která
říká, který kus mapy vyříznout z herního archivu, a tabulku každého vzorku každého kola. Zapisují
se společně, aby nemohly přestat sedět. Kód:
[`telemetry/fhcompanion.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/fhcompanion.py).

| Volba | Výchozí | Význam |
|---|---|---|
| `course` | žádná | Název trati, hledá se volně. Když se vynechá, vypíše knihovnu. |
| `-o`, `--out` | název trati malými písmeny, mezery jako `_` | Cesta k výstupu; `.json` a `.csv` se zapíšou vedle sebe. |
| `--library` | `%LOCALAPPDATA%\FHCompanion\laps` | Kde jsou složky tratí. |
| `--margin` | `80` | Metry přidané kolem rozsahu trati v x a z do `bounds` trasy. |

### Výpis {#listing}

Bez trati vypíše počet složek tratí a pro každou počet souborů kol (`*.json` kdekoli pod ní kromě
`course.json`) a název trati, pak `Name one to write it out:  -o <file> <course>`.

### Hledání trati {#finding-a-course}

Složky tratí se jmenují `<name> (course_<x>_<z>_to_<x>_<z>)` - start a cíl, zaokrouhlené. Trať se
najde v tomto pořadí: přesný název složky; část názvu složky bez ohledu na velikost písmen;
jediná složka, jejíž název obsahuje zadaný text. Několik shod je chyba, která je vypíše.

### Čtení {#reading-it}

- `course.json` ve složce, pokud jde přečíst, dá název a nezaokrouhlený start a cíl (`Name`,
  `StartX`, `StartZ`, `FinishX`, `FinishZ`); jinak se berou z názvu složky. Trať se hlásí jako
  okruh, když jsou start a cíl blíž než 10 m.
- Každý další `*.json` pod složkou je kolo (kola leží několik složek hluboko - podle třídy, auta,
  ladění, štítku - a hledání je prostě rekurzivní). Soubory se čtou jako UTF-8 se značkou pořadí
  bajtů. Nečitelné kolo se přeskočí. Kola se řadí podle času záznamu.
- Pro každé kolo `Lap.samples` (každý s `X`, `Y`, `Z`, `Speed`, `Throttle`, `Brake`, `Steer`,
  `LatG`, `LongG`, `Gear`, `Clutch`, `HandBrake`, `Puddle`, `Metres`, `Seconds`) a třída auta,
  pořadí, výkonnostní index, časy kola, délka, čas záznamu a rozjezd ze stoje.

Vypíše souhrn (kola, vzorky, nejlepší kolo a jeho třída, rozsah x/y/z).

### Výstup {#output}

**`<out>.json`** - stejný tvar trasy, jaký zapisuje `route`, takže jej extraktor map přijme
kterýkoli z nich: `layout: "fhcompanion"`, `course`, `laps`, `samples`, `bounds` (rozšířené o
`--margin` v x a z) a `positions` **nejrychlejšího** kola (jedna čára, ne rozmazaná mračna všech
kol).

**`<out>.csv`** - každý vzorek každého kola, jeden řádek na vzorek:

| Sloupec | Význam |
|---|---|
| `course` | název trati |
| `lap` | popisek každého kola: datum a čas záznamu na minutu a čas kola |
| `car` | pořadové číslo auta |
| `car_class` | písmeno výkonnostní třídy |
| `pi` | výkonnostní index |
| `lap_seconds` | čas kola |
| `speed_kmh` | rychlost v km/h |
| `x`, `y`, `z` | světová pozice, metry, 3 desetinná místa |
| `speed_ms` | rychlost, m/s |
| `throttle`, `brake`, `steer`, `lat_g`, `long_g`, `gear`, `clutch`, `handbrake`, `puddle` | tak, jak je zaznamenává FH Companion |
| `metres` | vzdálenost podél kola, 3 desetinná místa |
| `elapsed` | sekundy od vlastního startu kola, 3 desetinná místa |

Hodnoty, které nejsou pozicemi, se zapisují na 4 významné číslice; pozice mají pevný počet
desetinných míst, protože 4 významné číslice by trať přichytily na mřížku po metru. Názvy
sloupců jsou zvolené tak, aby prohlížeč soubor namapoval bez nápovědy: `lap` se stane relací
(dvě kola jednoho auta se nikdy nespojí), `car` věcí, která se pohybuje, `car_class` skupinou pro
barvu, `elapsed` časovou osou (každé kolo se zarovná na vlastní start).

Nakonec vypíše nápovědu, jak vyříznout mapu z hry pomocí GameFiles, se souborem trasy nebo
s explicitním obdélníkem.

## reconstruct {#reconstruct}

```bash
python -m heat3d_capture reconstruct lap.mp4 -o lap.glb [--solve-budget 260] [--fuse-interval 0.4] [--model vggt-1b]
```

Rekonstruuje záznam offline, s dráhou kamery vyřešenou najednou pomocí VGGT. Pomalé: minuty na
okno na stolním GPU. Potřebuje PyTorch, Hugging Face `transformers` a balíček `vggt`, které
skener nepotřebuje: jsou uvedené v `requirements-offline.txt` a příkaz je zkontroluje poté, co
vypíše řádek licence, a nabídne instalaci toho, co chybí (když se odmítne, konec s kódem 1).
Úplný popis: [Rekonstrukce offline](reconstruction-offline.md).

| Volba | Výchozí | Význam |
|---|---|---|
| `video` | povinné | Záznam. Když neexistuje, konec s kódem 2. |
| `-o`, `--out` | povinné | Soubor `.glb`, který se zapíše. |
| `--solve-budget` | `260` | Nejvíc snímků předaných řešiteli. Rozestupy určuje, jak moc se obraz hýbe, ne čas. Více je přesnější a mnohem pomalejší. Více než 400 plánovaných snímků se odmítne. |
| `--fuse-interval` | `0.4` | Sekundy mezi snímky sloučenými do geometrie. |
| `--model` | `vggt-1b` | Které váhy VGGT se použijí: `vggt-1b` (`facebook/VGGT-1B`, nekomerční) nebo `vggt-1b-commercial` (`facebook/VGGT-1B-Commercial`, s omezeným přístupem; přístup uděluje Meta). Řádek licence vypsaný jako první je licence tohoto modelu. |

Nejdřív vypíše řádek licence modelu, pak každou fázi (`masking`, `planning`, `solving`,
`fusing`, `exporting`) s uplynulými sekundami a postupem, a nakonec souhrn: vyřešené kamery,
chyba uzavření, nejhorší šev, poznámky a zapsaný soubor. Kód konce je 0, jen když se soubor
zapsal.

## hud {#hud}

```bash
python -m heat3d_capture hud "<recording>.mp4" --game bf6 --player <name> -o out/match [--fps 5] [--start S] [--seconds S] [--metres-per-pixel M] [--cpu]
```

Čte HUD hry z vlastního záznamu hráče, po zápase: vlastní akce hráče z vyskakovacího okna bodů,
smrti a oživení z obrazovek sestřelení a nasazení, stopu na minimapě a zprávy o zabitích. Zapíše
`<out>.parquet` (stopa a události, tabulka 3DHeat), `<out>.events.jsonl`, `<out>.summary.json`
a `<out>.map.png` + `.map.json` (mozaika minimapy a její kotvy pro položku **Obrázek mapy**
v prohlížeči). Battlefield 6 (`bf6`) je zatím jediný profil.

Potřebuje **ffmpeg a ffprobe** v PATH (`winget install Gyan.FFmpeg`, pak nový terminál).

| Volba | Výchozí | Význam |
|---|---|---|
| `video` | povinné | Záznam. |
| `-o`, `--out` | název videa | Cesta k výstupu bez přípony. |
| `--game` | `bf6` | Čí HUD se čte. |
| `--player` | odhadnutý | Jméno hráče, jak ho ukazuje zpráva o zabití, hledá se volně. |
| `--fps` | `5` | Vzorky minimapy za sekundu. |
| `--start`, `--seconds` | celé video | Část záznamu, která se čte. |
| `--metres-per-pixel` | žádná | Měřítko minimapy, když je známé; bez něj jsou pozice v pixelech minimapy. |
| `--cpu` | vypnuto | Dekódovat na procesoru, i když je NVIDIA karta. |

Podle [Čtení HUD ze záznamu](hud-video.md).

## locate {#locate}

```bash
python -m heat3d_capture locate build level.glb -o level.db [--game bf6] [--spacing 2.5] [--shadows]
python -m heat3d_capture locate frames recording.mp4 --db level.db -o out/match [--fps 2] [--minimap match.parquet]
python -m heat3d_capture locate eval out/match.parquet --truth poses.parquet [--offset S] [--unit-metres 1]
python -m heat3d_capture locate train level.glb -o level.head.pt [--places auto] [--real out/match.parquet recording.mp4]
python -m heat3d_capture locate refmap level.glb deploy.png -o out/refmap [--mpp 0.5]
python -m heat3d_capture locate minimap recording.mp4 --refmap out/refmap -o out/minimap.parquet [--hud out/match.parquet]
```

`build` vykreslí level ze všech míst, kde může hráč stát, a zaindexuje vykreslení; `frames`
umístí každý vzorkovaný snímek záznamu proti němu, podle obrazu, s dráhou na minimapě z příkazu
`hud` jako záložním řešením; `eval` porovná výsledek se známými pozicemi kamery; `train` natrénuje
model místa pro jednu mapu na vykresleních levelu (a na snímcích, které už běh našel), pro
`build --head`; `refmap` umístí vlastní mapu hry (její obrazovku nasazení) na level, a `minimap`
přečte minimapu záznamu proti ní, snímek po snímku - to může vzít předchozí `frames --minimap`.
Potřebuje PyTorch a `requirements-locate.txt`. **Experimentální:** na skutečných záznamech zatím
umístí jen malý podíl snímků. Každá volba, výstupy a metoda:
[Umísťování snímků v úrovni](locate.md); úplný seznam voleb: [Přehled příkazů](../cli-reference.md).

## Okno skenování {#the-scan-window}

```bash
python -m heat3d_capture.ui
```

nebo dvojklik na `scan.bat`. Žádné volby. Viz [Okno skenování](reconstruction-scan-ui.md).

## Aktualizace {#updates}

```bash
python -m heat3d_update            # check, and update if a newer release is out
python -m heat3d_update --check    # only say whether one is out
```

Viz [Aktualizace](updates.md).

## Převodník modelu {#the-model-converter}

```bash
python tools/export_onnx.py [--size small|base|large] [--out PATH] [--side 518] [--opset 17]
```

Převede kontrolní bod Depth Anything V2 na soubor ONNX, který skener spouští. Potřebuje PyTorch,
`transformers` a `onnxscript`. Viz [Hloubka](reconstruction-depth.md#building-the-model).
