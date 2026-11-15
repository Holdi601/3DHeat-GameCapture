---
title: "Trackmania (2020)"
nav_order: 5
lang: "sk"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kód: zásuvný modul Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Zásuvný modul ešte nebol spustený v hre**; čítačka jeho CSV v prehliadači
je otestovaná.

## Prečo zásuvný modul, ktorý zapisuje súbory {#why-a-plugin-that-writes-files}

Trackmania nemá vlastný výstup telemetrie. Openplanet, platforma zásuvných modulov hry, sprístupní
zásuvným modulom stav vozidla sledovaného auta, ale zásuvné moduly Openplanet nemôžu posielať UDP.
Zásuvný modul preto zapisuje jeden CSV súbor na beh do svojho úložného priečinka a prehliadač
číta tieto súbory tak, ako sú. Nie je tu žiadny nahrávací proces: `telemetry --game trackmania` len
inštaluje zásuvný modul (s `--install`) a vypíše, kde sa súbory objavia.

## Inštalácia a načítanie {#installing-and-loading}

- `--install` skopíruje `mods/trackmania/Heat3dRecorder` do
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, pričom nahradí staršiu kópiu. Bez
  `--install` sa nič nekopíruje.
- V hre: **Openplanet > Developer > Load plugin** a vyberte `3DHeat recorder`.
- Zásuvný modul závisí od zásuvného modulu Openplanet **VehicleState** (`dependencies = ["VehicleState"]`
  v `info.toml`).
- Nepodpísané zásuvné moduly sa načítajú len v **režime vývojára Openplanet**, ktorý obmedzuje hru
  online. Zásuvný modul sa dá podpísať na openplanet.dev; tu nie je podpísaný.

Behy sa zapisujú do `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Tieto CSV súbory
načítajte na karte Analýza pretekov v prehliadači. `-o` a `--port` sa pre Trackmania ignorujú.

## Čo zásuvný modul zaznamenáva {#what-the-plugin-records}

Číta len to, čo Openplanet sprístupní - stav vozidla sledovaného auta
(`VehicleState::ViewingPlayerState()`) a čas pretekov hráča a počet respawnov (`CSmScriptPlayer`) -
nikam nič neposiela a v hre nič nemení. Riadok sa zapisuje pri každom snímku (`Update`), takže
frekvencia vzoriek je snímková frekvencia hry.

| Stĺpec | Zdroj |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekundy |
| `x`, `y`, `z` | `Position` (svet, Y nahor) |
| `speed` | dĺžka `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 alebo 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` každého kolesa (miera šmyku 0..1) |
| `loose` | 1, keď má niektoré koleso materiál povrchu Grass, Ice, Sand, Dirt, Green alebo RoadIce |
| `airborne` | 1, keď auto nemá kontakt so zemou |
| `respawns` | počet respawnov od začiatku behu |

## Behy {#runs}

- Beh **začína** na prvom snímku, kde čas pretekov nie je záporný (odpočítavanie sa nezaznamenáva).
- **Končí**, keď je UI sekvencia ihriska sekvencia cieľa (hodnota 11): súbor sa zapíše ako úplný,
  s posledným časom pretekov ako `seconds`.
- Je **opustený** - zapíše sa s `_partial` v názve a `"complete": false` - keď hodiny pretekov
  klesnú o viac ako pol sekundy (reštart), alebo keď hráč opustí ihrisko.
- Beh s menej ako 20 riadkami sa nezapíše.

## Súbor {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Pomenovaný `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Názov mapy má odstránené formátovacie kódy
a dvojité úvodzovky nahradené jednoduchými. Hodnoty sa zapisujú so štyrmi desatinnými miestami.
Formát je opísaný v [Formát heat3d kola](lap-format.md#the-csv-form).

Hodnota `meta` v hlavičke nesie `"slip": "index"` - kanály `slipIndex.*` sú vlastná miera šmyku
Trackmania v rozsahu 0..1, nie fyzikálny šmyk - a `"discipline": "arcade"`.
