---
title: Trackmania (2020)
nav_order: 5
lang: "hu"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kód: az Openplanet-bővítmény,
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **A bővítményt a játékban még nem futtatták**; a megjelenítő CSV-olvasója tesztelt.

## Miért egy fájlokat író bővítmény {#why-a-plugin-that-writes-files}

A Trackmaniának nincs saját telemetriai kimenete. Az Openplanet, a játék bővítményplatformja, a nézett autó
jármű-állapotát közli a bővítményekkel, de az Openplanet-bővítmények nem tudnak UDP-n küldeni. Ezért a bővítmény
futásonként egy CSV-fájlt ír a saját tárolómappájába, a megjelenítő pedig a fájlokat olyanul olvassa, amilyenek.
Nincs rögzítő folyamat: a `telemetry --game trackmania` csak telepíti a bővítményt (`--install` kapcsolóval), és
kiírja, hová kerülnek a fájlok.

## Telepítés és betöltés {#installing-and-loading}

- Az `--install` átmásolja a `mods/trackmania/Heat3dRecorder` mappát a
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` helyre, egy régebbi másolatot felülírva. `--install` nélkül
  semmi nem másolódik.
- A játékban: **Openplanet > Developer > Load plugin** (Fejlesztő > Bővítmény betöltése), és válassza a
  `3DHeat recorder` bővítményt.
- A bővítmény az Openplanet **VehicleState** bővítményétől függ (`dependencies = ["VehicleState"]` az
  `info.toml`-ban).
- A nem aláírt bővítmények csak az **Openplanet fejlesztői módjában** töltődnek be, ami korlátozza az online
  játékot. A bővítményt az openplanet.dev oldalon alá lehet írni; itt nincs aláírva.

A futások ide íródnak: `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Ezeket a CSV-fájlokat a
megjelenítő Versenyelemzés fülére töltse. A `-o` és a `--port` Trackmaniánál figyelmen kívül marad.

## Amit a bővítmény rögzít {#what-the-plugin-records}

Csak azt olvassa, amit az Openplanet megmutat - a nézett autó jármű-állapotát
(`VehicleState::ViewingPlayerState()`) és a játékos versenyidejét és újraindulásainak számát (`CSmScriptPlayer`) -,
sehová nem küld, és a játékon nem változtat. Minden képkockánál (`Update`) íródik egy sor, így a mintavételezés a
játék képkockasebessége.

| Oszlop | Forrás |
|---|---|
| `time` | `CurrentRaceTime` / 1000, másodpercben |
| `x`, `y`, `z` | `Position` (világ, Y felfelé) |
| `speed` | a `WorldVel` hossza |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 vagy 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | minden kerék `SlipCoef` értéke (0..1 csúszásmérő) |
| `loose` | 1, ha bármelyik kerék talajanyaga Grass, Ice, Sand, Dirt, Green vagy RoadIce |
| `airborne` | 1, ha az autónak nincs talajérintkezése |
| `respawns` | a futás kezdete óta történt újraindulások száma |

## Futások {#runs}

- Egy futás akkor **kezdődik**, amikor a versenyidő először nem negatív (a visszaszámlálás nincs rögzítve).
- Akkor **végződik be**, amikor a pálya UI-szekvenciája a célszekvencia (11-es érték): a fájl teljesként íródik,
  `seconds` értéke az utolsó versenyidő.
- **Félbehagyottként** íródik - a névben `_partial` jelöléssel és `"complete": false` értékkel -, ha a versenyóra
  több mint fél másodperccel visszaugrik (újrakezdés), vagy ha a játékos elhagyja a pályát.
- A 20 sornál rövidebb futás nem íródik ki.

## A fájl {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

A neve `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. A pályanév formázási kódjai törlésre kerülnek, a dupla idézőjelek
egyszeresekre cserélődnek. Az értékek négy tizedesjeggyel íródnak. A formátumot a
[heat3d-körfájl](lap-format.md#the-csv-form) oldal írja le.

A fejléc `meta` része a `"slip": "index"` értéket hordozza - a `slipIndex.*` csatornák a Trackmania saját 0..1
csúszásmérője, nem fizikai csúszás -, és a `"discipline": "arcade"` értéket.
