---
title: "Trackmania"
nav_order: 5
lang: "is"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Kóði: Openplanet viðbótin
[`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder)
(`info.toml`, `main.as`). **Viðbótin hefur ekki enn verið keyrð í leiknum**; lesari skoðarans
á CSV skránni hennar er prófaður.

## Hvers vegna viðbót sem skrifar skrár {#why-a-plugin-that-writes-files}

Trackmania hefur ekkert eigið mælingaúttak. Openplanet, viðbótavettvangur leiksins,
birtir viðbótum ástand bílsins sem horft er á, en Openplanet viðbætur geta ekki sent UDP. Því
skrifar viðbótin eina CSV skrá fyrir hvert hlaup í eigin geymslumöppu, og skoðarinn les þessar
skrár eins og þær eru. Enginn upptökuferill er til: `telemetry --game trackmania` setur aðeins upp
viðbótina (með `--install`) og prentar hvar skrárnar munu birtast.

## Uppsetning og hleðsla {#installing-and-loading}

- `--install` afritar `mods/trackmania/Heat3dRecorder` í
  `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` og kemur í stað eldra afrits. Án
  `--install` er ekkert afritað.
- Í leiknum: **Openplanet > Developer > Load plugin**, og veldu `3DHeat recorder`.
- Viðbótin þarf **VehicleState** viðbót Openplanet (`dependencies = ["VehicleState"]`
  í `info.toml`).
- Óundirritaðar viðbætur hlaðast aðeins í **þróunarham Openplanet**, sem takmarkar netspilun.
  Hægt er að undirrita viðbótina á openplanet.dev; hún er ekki undirrituð hér.

Hlaup eru skrifuð í `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Hladdu þessum
CSV skrám á flipann Kappakstursgreining í skoðaranum. `-o` og `--port` eru hunsuð fyrir Trackmania.

## Hvað viðbótin skráir {#what-the-plugin-records}

Hún les aðeins það sem Openplanet birtir - ástand bílsins sem horft er á
(`VehicleState::ViewingPlayerState()`) og keppnistíma spilarans og fjölda endurræsinga
(`CSmScriptPlayer`) - sendir ekkert neitt og breytir engu í leiknum. Röð er
skrifuð í hverjum ramma (`Update`), svo sýnatökutíðnin er rammatíðni leiksins.

| Dálkur | Uppruni |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekúndur |
| `x`, `y`, `z` | `Position` (heimur, Y upp) |
| `speed` | lengd `WorldVel` |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 eða 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | `SlipCoef` hvers hjóls (0..1 mælikvarði á skrið) |
| `loose` | 1 þegar efni undir einhverju hjóli er Grass, Ice, Sand, Dirt, Green eða RoadIce |
| `airborne` | 1 þegar bíllinn snertir ekki jörðu |
| `respawns` | endurræsingar frá upphafi hlaupsins |

## Hlaup {#runs}

- Hlaup **byrjar** í fyrsta ramma þar sem keppnistíminn er ekki neikvæður (niðurtalningin er
  ekki skráð).
- Því **lýkur** þegar UI-röð leikvallarins er markröðin (gildi 11): skráin
  er skrifuð sem fullkomin, með síðasta keppnistímann sem `seconds`.
- Það er **yfirgefið** - skrifað með `_partial` í heitinu og `"complete": false` - þegar
  keppnisklukkan fer aftur um meira en hálfa sekúndu (endurræsing), eða þegar spilarinn yfirgefur
  leikvöllinn.
- Hlaup með færri en 20 raðir er ekki skrifað.

## Skráin {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Heitir `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Sniðkóðar eru fjarlægðir úr heiti kortsins
og tvöföldum gæsalöppum skipt út fyrir einfaldar. Gildi eru skrifuð með fjórum aukastöfum. Sniðið
er lýst í [heat3d-lap skráin](lap-format.md#the-csv-form).

`meta` í haus skrárinnar ber `"slip": "index"` - `slipIndex.*` rásirnar eru eigin
0..1 skriðmælikvarði Trackmania, ekki eðlisfræðilegt slip - og `"discipline": "arcade"`.
