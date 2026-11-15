---
title: "Trackmania"
nav_order: 5
lang: "bs"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kod: Openplanet dodatak
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Dodatak još nije pokrenut u igri**; čitač preglednika
za njegov CSV je testiran.

## Zašto dodatak koji piše datoteke {#why-a-plugin-that-writes-files}

Trackmania nema vlastiti telemetrijski izlaz. Openplanet, platforma za dodatke igre,
izlaže dodacima stanje vozila koje se gleda, ali Openplanet dodaci ne mogu slati UDP. Zato
dodatak piše po jedan CSV datoteka za svaku vožnju u svoj folder za pohranu, a preglednik čita te
datoteke takve kakve jesu. Nema procesa snimača: `telemetry --game trackmania` samo instalira
dodatak (uz `--install`) i ispisuje gdje će se datoteke pojaviti.

## Instaliranje i učitavanje {#installing-and-loading}

- `--install` kopira `mods/trackmania/Heat3dRecorder` u
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, zamjenjujući stariju kopiju. Bez
  `--install` ništa se ne kopira.
- U igri: **Openplanet > Developer > Load plugin**, i odaberite `3DHeat recorder`.
- Dodatak zavisi od Openplanetovog dodatka **VehicleState** (`dependencies = ["VehicleState"]`
  u `info.toml`).
- Nepotpisani dodaci se učitavaju samo u **Openplanetovom razvojnom načinu**, koji ograničava igranje online.
  Dodatak se može potpisati na openplanet.dev; ovdje nije potpisan.

Vožnje se pišu u `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Učitajte te
CSV datoteke na kartici Analiza utrke preglednika. `-o` i `--port` se za Trackmania ignoriraju.

## Šta dodatak bilježi {#what-the-plugin-records}

Čita samo ono što Openplanet izlaže - stanje vozila koje se gleda
(`VehicleState::ViewingPlayerState()`) te igračevo vrijeme trke i broj respawnova
(`CSmScriptPlayer`) - ne šalje ništa nikamo i ne mijenja ništa u igri. Red se
piše u svakom kadru (`Update`), pa je brzina uzorkovanja brzina kadrova igre.

| Kolona | Izvor |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunde |
| `x`, `y`, `z` | `Position` (svijet, Y gore) |
| `speed` | dužina `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ili 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` svakog točka (mjera klizanja 0..1) |
| `loose` | 1 kad je materijal podloge bilo kojeg točka Grass, Ice, Sand, Dirt, Green ili RoadIce |
| `airborne` | 1 kad auto nema kontakt s tlom |
| `respawns` | respawnovi od početka vožnje |

## Vožnje {#runs}

- Vožnja **počinje** u prvom kadru u kojem vrijeme trke nije negativno (odbrojavanje se
  ne bilježi).
- **Završava** kad je UI sekvenca igrališta završna sekvenca (vrijednost 11): datoteka
  se piše kao potpuna, a posljednje vrijeme trke je njen `seconds`.
- **Napušta se** - piše se sa `_partial` u imenu i `"complete": false` - kad
  sat trke ode unazad za više od pola sekunde (restart), ili kad igrač napusti
  igralište.
- Vožnja s manje od 20 redova se ne piše.

## Datoteka {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Zove se `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Iz imena mape se uklanjaju kodovi
za formatiranje, a dvostruki navodnici zamjenjuju jednostrukim. Vrijednosti se pišu s četiri decimale. Format
je opisan u [Datoteci heat3d-lap](lap-format.md#the-csv-form).

`meta` u zaglavlju nosi `"slip": "index"` - kanali `slipIndex.*` su Trackmanijina vlastita
mjera klizanja 0..1, a ne fizički slip - i `"discipline": "arcade"`.
