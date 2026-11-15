---
title: Trackmania (2020)
nav_order: 5
lang: "sl"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Koda: vtičnik Openplanet [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Vtičnik še ni bil zagnan v igri**; bralnik njegove datoteke CSV v pregledovalniku
je preizkušen.

## Zakaj vtičnik, ki piše datoteke {#why-a-plugin-that-writes-files}

Trackmania nima lastnega izhoda telemetrije. Openplanet, platforma vtičnikov igre, vtičnikom izpostavi
stanje gledanega vozila, vtičniki Openplanet pa ne znajo pošiljati UDP. Zato vtičnik za vsak tek zapiše
eno datoteko CSV v svojo mapo za shranjevanje, pregledovalnik pa te datoteke bere takšne, kakršne so. Ni
procesa snemalnika: `telemetry --game trackmania` samo namesti vtičnik (z `--install`) in izpiše, kje
se bodo pojavile datoteke.

## Namestitev in nalaganje {#installing-and-loading}

- `--install` skopira `mods/trackmania/Heat3dRecorder` v `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder`
  in nadomesti starejšo kopijo. Brez `--install` se nič ne kopira.
- V igri: **Openplanet > Developer > Load plugin** in izberite `3DHeat recorder`.
- Vtičnik je odvisen od vtičnika Openplanet **VehicleState** (`dependencies = ["VehicleState"]` v
  `info.toml`).
- Nepodpisani vtičniki se naložijo samo v **razvijalskem načinu Openplanet**, ki omejuje igranje na
  spletu. Vtičnik je mogoče podpisati na openplanet.dev; tu ni podpisan.

Teki se zapisujejo v `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Te datoteke CSV
naložite na zavihku „Analiza dirke“ v pregledovalniku. `-o` in `--port` se za Trackmania prezreta.

## Kaj vtičnik beleži {#what-the-plugin-records}

Bere samo to, kar Openplanet izpostavi – stanje gledanega vozila (`VehicleState::ViewingPlayerState()`)
ter čas dirke igralca in število ponovnih pojavitev (`CSmScriptPlayer`) – nikamor ničesar ne pošilja in
v igri ničesar ne spremeni. Vrstica se zapiše ob vsakem okvirju (`Update`), zato je hitrost vzorčenja
enaka hitrosti okvirov igre.

| Stolpec | Vir |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekunde |
| `x`, `y`, `z` | `Position` (svet, Y navzgor) |
| `speed` | dolžina `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 ali 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` vsakega kolesa (merilo drsenja 0..1) |
| `loose` | 1, kadar je material tal katerega koli kolesa Grass, Ice, Sand, Dirt, Green ali RoadIce |
| `airborne` | 1, kadar vozilo nima stika s tlemi |
| `respawns` | ponovne pojavitve od začetka teka |

## Teki {#runs}

- Tek se **začne** na prvem okvirju, kjer čas dirke ni negativen (odštevanje se ne beleži).
- **Konča** se, kadar je zaporedje vmesnika igrišča zaporedje cilja (vrednost 11): datoteka se zapiše
  kot popolna, z zadnjim časom dirke kot `seconds`.
- Tek je **opuščen** – zapiše se z `_partial` v imenu in `"complete": false` – kadar čas dirke gre nazaj
  za več kot pol sekunde (ponovni zagon) ali kadar igralec zapusti igrišče.
- Tek z manj kot 20 vrsticami se ne zapiše.

## Datoteka {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Ime je `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Ime zemljevida ima odstranjene oblikovalne kode,
dvojni narekovaji pa so zamenjani z enojnimi. Vrednosti se zapišejo s štirimi decimalkami. Format je
opisan v [Datoteka heat3d-lap](lap-format.md#the-csv-form).

Glava `meta` nosi `"slip": "index"` – kanali `slipIndex.*` so Trackmanijino lastno merilo drsenja
0..1, ne fizični zdrs – in `"discipline": "arcade"`.
