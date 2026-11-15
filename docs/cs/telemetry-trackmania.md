---
title: Trackmania
nav_order: 5
lang: "cs"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kód: plugin pro Openplanet [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Plugin zatím nebyl spuštěn ve hře.** Čtečka jeho CSV v prohlížeči je testovaná.

## Proč plugin, který zapisuje soubory {#why-a-plugin-that-writes-files}

Trackmania nemá vlastní výstup telemetrie. Openplanet, platforma pluginů hry, zpřístupňuje pluginům stav vozidla, které hráč sleduje. Pluginy Openplanetu ale nemohou posílat UDP. Plugin proto zapisuje jeden soubor CSV na běh do vlastní úložné složky a prohlížeč tyto soubory čte tak, jak jsou. Žádný záznamový proces neexistuje: `telemetry --game trackmania` jen nainstaluje plugin (s `--install`) a vypíše, kde se soubory objeví.

## Instalace a načtení {#installing-and-loading}

- `--install` zkopíruje `mods/trackmania/Heat3dRecorder` do `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` a nahradí starší kopii. Bez `--install` se nic nekopíruje.
- Ve hře: **Openplanet > Developer > Load plugin** a vyberte `3DHeat recorder`.
- Plugin závisí na pluginu Openplanetu **VehicleState** (`dependencies = ["VehicleState"]` v `info.toml`).
- Nepodepsané pluginy se načtou jen v **vývojářském režimu Openplanetu**, který omezuje hraní online. Plugin lze podepsat na openplanet.dev; tady podepsaný není.

Běhy se zapisují do `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Tyto soubory CSV načtěte na záložce prohlížeče **Analýza závodu**. `-o` a `--port` se pro Trackmanii ignorují.

## Co plugin zaznamenává {#what-the-plugin-records}

Čte jen to, co Openplanet vystavuje: stav vozidla sledovaného hráče (`VehicleState::ViewingPlayerState()`) a čas závodu hráče a počet respawnů (`CSmScriptPlayer`). Nic nikam neposílá a nic ve hře nemění. Řádek se zapisuje při každém snímku (`Update`), takže vzorkovací frekvence je snímková frekvence hry.

| Sloupec | Zdroj |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekundy |
| `x`, `y`, `z` | `Position` (světová, Y nahoru) |
| `speed` | délka `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 nebo 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` každého kola (míra smyku 0..1) |
| `loose` | 1, když materiál pod některým kolem je Grass, Ice, Sand, Dirt, Green nebo RoadIce |
| `airborne` | 1, když auto nemá kontakt se zemí |
| `respawns` | počet respawnů od začátku běhu |

## Běhy {#runs}

- Běh **začíná** na prvním snímku, kde čas závodu není záporný. Odpočet se nezaznamenává.
- **Končí**, když je UI sekvence hřiště sekvencí cíle (hodnota 11). Soubor se zapíše jako úplný, s posledním časem závodu jako `seconds`.
- Je **opuštěn**, zapíše se se `_partial` v názvu a `"complete": false`. Stane se to, když čas závodu přeskočí zpět o víc než půl sekundy (restart), nebo když hráč opustí hřiště.
- Běh s méně než 20 řádků se nezapíše.

## Soubor {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Název je `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Název mapy má odstraněné formátovací kódy a dvojité uvozovky nahrazené jednoduchými. Hodnoty se zapisují na čtyři desetinná místa. Formát je popsán v [Soubor heat3d-lap](lap-format.md#the-csv-form).

Hlavička `meta` nese `"slip": "index"`. Sloupce `slipIndex.*` jsou vlastní míra smyku Trackmanie v rozsahu 0..1, ne fyzický skluz. Dále nese `"discipline": "arcade"`.
