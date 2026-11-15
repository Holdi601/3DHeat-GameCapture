---
title: Trackmania (2020)
nav_order: 5
lang: "hr"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kod: dodatak Openplanet
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Dodatak još nije pokrenut u igri**; čitač njegovog CSV-a u pregledniku je
testiran.

## Zašto dodatak koji piše datoteke {#why-a-plugin-that-writes-files}

Trackmania nema vlastiti izlaz za telemetriju. Openplanet, platforma za dodatke igre, izlaže dodacima
stanje vozila koji se gleda, ali Openplanet dodaci ne mogu slati UDP. Zato dodatak piše jednu CSV
datoteku po vožnji u vlastitu mapu za pohranu, a preglednik čita te datoteke kakve jesu. Nema procesa
snimanja: `telemetry --game trackmania` samo instalira dodatak (uz `--install`) i ispiše gdje će se
datoteke pojaviti.

## Instalacija i učitavanje {#installing-and-loading}

- `--install` kopira `mods/trackmania/Heat3dRecorder` u
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`, zamjenjujući stariju kopiju. Bez `--install`
  ništa se ne kopira.
- U igri: **Openplanet > Developer > Load plugin**, i odaberite `3DHeat recorder`.
- Dodatak ovisi o Openplanetovu dodatku **VehicleState** (`dependencies = ["VehicleState"]` u
  `info.toml`).
- Nepotpisani dodaci učitavaju se samo u **razvojnom načinu Openplaneta**, koji ograničava igru na
  mreži. Dodatak se može potpisati na openplanet.dev; ovdje nije potpisan.

Vožnje se zapisuju u `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Te CSV datoteke
učitajte na kartici Analiza utrke preglednika. `-o` i `--port` se za Trackmaniju zanemaruju.

## Što dodatak snima {#what-the-plugin-records}

Čita samo ono što Openplanet izlaže - stanje vozila koje se gleda
(`VehicleState::ViewingPlayerState()`) i vrijeme utrke igrača te broj ponovnih pojavljivanja
(`CSmScriptPlayer`) - nigdje ništa ne šalje i ništa ne mijenja u igri. Redak se piše na svakom kadru
(`Update`), pa je brzina uzorkovanja brzina kadrova igre.

| Stupac | Izvor |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunde |
| `x`, `y`, `z` | `Position` (svijet, Y gore) |
| `speed` | duljina `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ili 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` svakog kotača (mjera klizanja 0..1) |
| `loose` | 1 kad neki kotač stoji na materijalu Grass, Ice, Sand, Dirt, Green ili RoadIce |
| `airborne` | 1 kad automobil nema dodira s tlom |
| `respawns` | ponovna pojavljivanja od početka vožnje |

## Vožnje {#runs}

- Vožnja **počinje** na prvom kadru gdje vrijeme utrke nije negativno (odbrojavanje se ne snima).
- **Završava** kad je UI slijed igrališta slijed završetka (vrijednost 11): datoteka se zapisuje kao
  cijela, a zadnje vrijeme utrke je njezin `seconds`.
- **Napušta se** - zapisuje se s `_partial` u nazivu i `"complete": false` - kad sat utrke skoči unatrag
  za više od pola sekunde (ponovno pokretanje), ili kad igrač napusti igralište.
- Vožnja s manje od 20 redaka se ne zapisuje.

## Datoteka {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Naziv je `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Iz naziva karte uklonjeni su kodovi za oblikovanje, a
dvostruki navodnici su zamijenjeni jednostrukima. Vrijednosti se pišu s četiri decimale. Format je
opisan u [Format datoteke heat3d-lap](lap-format.md#the-csv-form).

`meta` u zaglavlju nosi `"slip": "index"` - kanali `slipIndex.*` su Trackmanijina vlastita mjera
klizanja 0..1, a ne fizički proklizaj - i `"discipline": "arcade"`.
