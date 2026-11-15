---
title: "Trackmania"
nav_order: 5
lang: "sq"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kodi: shtojca Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Shtojca ende nuk është ekzekutuar në lojë**; lexuesi i shikuesit
për CSV-në e saj është i testuar.

## Pse një shtojcë që shkruan skedarë {#why-a-plugin-that-writes-files}

Trackmania nuk ka dalje telemetrie të vetën. Openplanet, platforma e shtojcave të lojës,
u ekspozon shtojcave gjendjen e automjetit të parë, por shtojcat Openplanet nuk mund të dërgojnë UDP. Ndaj
shtojca shkruan një skedar CSV për çdo ecje në dosjen e vet të ruajtjes, dhe shikuesi i lexon ato
skedarë siç janë. Nuk ka proces regjistrues: `telemetry --game trackmania` vetëm e instalon
shtojcën (me `--install`) dhe printon ku do të shfaqen skedarët.

## Instalimi dhe ngarkimi {#installing-and-loading}

- `--install` kopjon `mods/trackmania/Heat3dRecorder` te
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, duke zëvendësuar një kopje më të vjetër. Pa
  `--install` nuk kopjohet asgjë.
- Te loja: **Openplanet > Developer > Load plugin**, dhe zgjidh `3DHeat recorder`.
- Shtojca varet nga shtojca **VehicleState** e Openplanet (`dependencies = ["VehicleState"]`
  te `info.toml`).
- Shtojcat e pasinjuara ngarkohen vetëm në **modalitetin e zhvilluesit të Openplanet**, që kufizon lojën online.
  Shtojca mund të nënshkruhet te openplanet.dev; këtu nuk është e nënshkruar.

Ecjet shkruhen te `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Ngarko ato
skedarë CSV te skeda Analiza e garës e shikuesit. `-o` dhe `--port` shpërfillen për Trackmania.

## Çfarë regjistron shtojca {#what-the-plugin-records}

Lexon vetëm ç'ekspozon Openplanet - gjendjen e automjetit të parë
(`VehicleState::ViewingPlayerState()`) dhe kohën e garës së lojtarit dhe numrin e rilindjeve
(`CSmScriptPlayer`) - nuk dërgon asgjë askund dhe nuk ndryshon asgjë në lojë. Një rresht shkruhet
në çdo kuadër (`Update`), ndaj shpejtësia e mostrimit është shpejtësia e kuadrove e lojës.

| Kolona | Burimi |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekonda |
| `x`, `y`, `z` | `Position` (bota, Y lart) |
| `speed` | gjatësia e `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ose 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` i çdo rrote (një masë rrëshqitjeje 0..1) |
| `loose` | 1 kur materiali i tokës i ndonjë rrote është Grass, Ice, Sand, Dirt, Green ose RoadIce |
| `airborne` | 1 kur makina nuk ka kontakt me tokën |
| `respawns` | rilindjet që nga fillimi i ecjes |

## Ecjet {#runs}

- Një ecje **fillon** në kuadrin e parë ku koha e garës nuk është negative (numërimi mbrapsht
  nuk regjistrohet).
- **Mbaron** kur sekuenca e UI të playground-it është sekuenca e finishit (vlera 11): skedari
  shkruhet si i plotë, me kohën e fundit të garës si `seconds`.
- **Braktiset** - shkruhet me `_partial` në emër dhe `"complete": false` - kur ora e
  garës kthehet pas me më shumë se gjysmë sekonde (një rinisje), ose kur lojtari del nga
  playground-i.
- Një ecje me më pak se 20 rreshta nuk shkruhet.

## Skedari {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Emërtohet `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Nga emri i hartës hiqen kodet e formatimit
dhe thonjëzat e dyfishta zëvendësohen me të njëfishta. Vlerat shkruhen me katër dhjetore. Formati
përshkruhet te [Skedari heat3d-lap](lap-format.md#the-csv-form).

`meta` i header-it mban `"slip": "index"` - kanalet `slipIndex.*` janë masa e vetë Trackmania
e rrëshqitjes 0..1, jo një slip fizik - dhe `"discipline": "arcade"`.
