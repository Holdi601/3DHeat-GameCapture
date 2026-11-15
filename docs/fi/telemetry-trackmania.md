---
title: Trackmania
nav_order: 5
lang: "fi"
source: telemetry-trackmania.md
source_hash: "26be8aff772b"
nav_exclude: true
search_exclude: true
---
# Trackmania (2020) {#trackmania-2020}

```bash
python -m heat3d_capture telemetry --game trackmania --install
```

Koodi: Openplanet-liitännäinen [`mods/trackmania/Heat3dRecorder`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/mods/trackmania/Heat3dRecorder) (`info.toml`, `main.as`). **Liitännäistä ei ole vielä ajettu pelissä.** Katselimen CSV-lukija on testattu.

## Miksi liitännäinen, joka kirjoittaa tiedostoja {#why-a-plugin-that-writes-files}

Trackmanialla ei ole omaa telemetriaulostuloa. Openplanet on pelin liitännäisalusta. Se näyttää liitännäisille katsotun auton ajoneuvon tilan, mutta Openplanet-liitännäiset eivät voi lähettää UDP:tä. Siksi liitännäinen kirjoittaa yhden CSV-tiedoston per ajo omaan tallennuskansioonsa, ja katselin lukee tiedostot sellaisinaan. Erillistä tallennusprosessia ei ole. `telemetry --game trackmania` vain asentaa liitännäisen (`--install`-valinnalla) ja tulostaa, mihin tiedostot ilmestyvät.

## Asentaminen ja lataaminen {#installing-and-loading}

- `--install` kopioi `mods/trackmania/Heat3dRecorder`-kansion kohteeseen `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` ja korvaa vanhemman kopion. Ilman `--install`-valintaa mitään ei kopioida.
- Pelissä: **Openplanet > Developer > Load plugin**, ja valitse `3DHeat recorder`.
- Liitännäinen tarvitsee Openplanetin **VehicleState**-liitännäisen (`dependencies = ["VehicleState"]` tiedostossa `info.toml`).
- Allekirjoittamattomat liitännäiset latautuvat vain **Openplanetin kehittäjätilassa**, mikä rajoittaa verkkopeliä. Liitännäisen voi allekirjoittaa openplanet.dev-sivustolla. Tässä sitä ei ole allekirjoitettu.

Ajot kirjoitetaan kansioon `%USERPROFILE%\OpenplanetNext\PluginStorage\Heat3dRecorder`. Lataa nuo CSV-tiedostot katselimen **Kisa-analyysi**-välilehdelle. `-o` ja `--port` jätetään Trackmanialla huomiotta.

## Mitä liitännäinen tallentaa {#what-the-plugin-records}

Se lukee vain sen, minkä Openplanet paljastaa. Nämä ovat katsotun auton ajoneuvon tila (`VehicleState::ViewingPlayerState()`) sekä pelaajan kisa-aika ja uudelleensyntymien määrä (`CSmScriptPlayer`). Se ei lähetä mitään minnekään eikä muuta mitään pelissä. Rivi kirjoitetaan jokaisessa kuvassa (`Update`), joten näytteenottotaajuus on pelin kuvataajuus.

| Sarake | Lähde |
|---|---|
| `time` | `CurrentRaceTime` / 1000, sekuntia |
| `x`, `y`, `z` | `Position` (maailma, Y ylös) |
| `speed` | `WorldVel`-vektorin pituus |
| `longVel` | `FrontSpeed` |
| `latVel` | `VehicleState::GetSideSpeed` |
| `yaw` | `atan2(Dir.x, Dir.z)` |
| `throttle` | `InputGasPedal` |
| `brake` | `InputIsBraking`, 1 tai 0 |
| `steer` | `InputSteer` |
| `gear` | `CurGear` |
| `rpm` | `VehicleState::GetRPM` |
| `slipIndex.FL/FR/RL/RR` | kunkin pyörän `SlipCoef` (0..1 liukumismitta) |
| `loose` | 1, kun minkä tahansa pyörän maamateriaali on Grass, Ice, Sand, Dirt, Green tai RoadIce |
| `airborne` | 1, kun autolla ei ole maakosketusta |
| `respawns` | uudelleensyntymiä ajon alusta |

## Ajot {#runs}

- Ajo **alkaa** ensimmäisessä kuvassa, jossa kisa-aika ei ole negatiivinen. Lähtölaskentaa ei tallenneta.
- Ajo **päättyy**, kun pelialueen käyttöliittymäjakso on maaliin tulon jakso (arvo 11). Tiedosto kirjoitetaan täydellisenä, ja viimeinen kisa-aika on sen `seconds`-arvo.
- Ajo **hylätään**. Se kirjoitetaan nimessä `_partial` ja `"complete": false`. Näin käy, kun kisakello menee taaksepäin yli puoli sekuntia (uudelleenkäynnistys), tai kun pelaaja poistuu pelialueelta.
- Ajoa, jossa on alle 20 riviä, ei kirjoiteta.

## Tiedosto {#the-file}

```text
# {"format":"heat3d-lap-csv","version":1,"game":"trackmania","track":"<map name>","complete":true,"seconds":42.1234,"meta":{"slip":"index","discipline":"arcade"}}
time,x,y,z,speed,longVel,latVel,yaw,throttle,brake,steer,gear,rpm,slipIndex.FL,slipIndex.FR,slipIndex.RL,slipIndex.RR,loose,airborne,respawns
0.0000,512.0000,9.0000,480.0000,0.0000,...
```

Nimi on `run_<YYYY-MM-DD_HH-MM-SS>[_partial].csv`. Kartan nimestä poistetaan muotoilukoodit, ja kaksoislainausmerkit korvataan yksinkertaisilla. Arvot kirjoitetaan neljällä desimaalilla. Muoto on kuvattu sivulla [heat3d-kierrostiedosto](lap-format.md#the-csv-form).

Otsikon `meta` kantaa arvot `"slip": "index"` ja `"discipline": "arcade"`. Kanavat `slipIndex.*` ovat Trackmanian oma 0..1 liukumismitta, eivät fyysinen luisto.
