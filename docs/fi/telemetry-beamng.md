---
title: BeamNG.drive
nav_order: 4
lang: "fi"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamng-drive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copy the mod, then record
python -m heat3d_capture telemetry --game beamng -o laps      # record
```

Sitten pelissä: **Options > Other > Protocols**, ja kytke **"others"** päälle.

Koodi: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py) ja mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua). Testit: `tests/test_beamng.py`, modin rakenteesta rakennetuilla paketeilla. **Modia ei ole vielä ajettu pelissä.**

## Miksi mod {#why-a-mod}

BeamNG lähettää telemetriaa "protokollien" kautta. Ne ovat ajoneuvon Lua-moduuleita, jotka pelin oma `lua/vehicle/protocols.lua` pakkaa ja lähettää UDP:llä pelaajan ajamasta autosta. Valmiit protokollat eivät kanna sitä, mitä auton ohjauksen analyysi tarvitsee. OutGaugessa ei ole sijaintia, MotionSimissä ei ole pyöriä, ja OutSim on tyhjä runko nykyversioissa. Siksi tämä projekti tuo oman protokollansa, `heat3d`:n. Se ei koske mihinkään ajoneuvon oman Lua-koodin ulkopuolella.

## Asentaminen {#installing}

`--install` kopioi `mods/beamng/heat3d`-kansion kohteeseen `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d`. BeamNG 0.30 ja uudemmat pitävät käyttäjän modit siellä. Komento poistaa ensin vanhemman kopion ja tulostaa, minne kopio meni. Ilman `LOCALAPPDATA`-muuttujaa se käyttää kotikansiota. Kansion voi kopioida myös käsin.

`--install` jatkaa sen jälkeen suoraan tallennukseen.

## Modi {#the-mod}

| Asetus (tiedostossa `heat3d.lua`) | Arvo |
|---|---|
| Osoite | `127.0.0.1` |
| Portti | `4460` - vaihda se tässä ja anna tallentimelle sama `--port` |
| Päivitysnopeuden yläraja | 100 Hz |
| Fysiikka-askel | käytössä (`isPhysicsStepUsed` palauttaa todeksi) |

Jokainen paketti alkaa 4 tavun tunnisteella `H3D1`, jota seuraa 39 little-endian-liukulukua (160 tavua yhteensä):

| Kenttä | Määrä | Lähde ajoneuvon Lua:ssa |
|---|---|---|
| `time` | 1 | modin oma kello: fysiikka-askelten summa, nollataan ajoneuvon nollauksessa |
| sijainti | 3 | `obj:getPositionXYZ()` |
| nopeus | 3 | `obj:getVelocityXYZ()` (maailma) |
| eteenpäin | 3 | `obj:getDirectionVector()` |
| ylös | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, ja 1/0 kohteista `absActive` ja `tcsActive` |
| `wheelSpeed` | 4 | kunkin pyörän pintanopeus (m/s) |
| `wheelAngular` | 4 | kulmanopeus kerrottuna pyörän suunnalla (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 kun pyörä ei ole maassa |

Neljä pyörää valitaan sen mukaan, **missä ne ovat autossa**, ei nimen mukaan. Nimet vaihtelevat ajoneuvoittain. Pyörä on edessä tai takana solmun paikan mukaan auton pituussuunnassa. Se on vasemmalla tai oikealla poikkisuunnassa (ajoneuvon koordinaatisto: +X vasemmalle, -Y eteenpäin). Kunkin kulman osalta otetaan pyörä, joka on kauimpana keskustasta. Puuttuva kulma lähetetään nollina, materiaali -1.

## Mitä tallennin tekee datalle {#what-the-recorder-does-with-it}

BeamNG:n maailmassa Z on ylös. Katselimen maailmassa Y on ylös. Sijainnit ja vektorit käännetään X-akselin ympäri, `(x, y, z) -> (x, z, -y)`, mikä säilyttää maailman kätisyyden. Sitten:

| Kanava | Lasketaan näin |
|---|---|
| `x`, `y`, `z` | käännetty sijainti |
| `speed` | käännetyn nopeuden pituus |
| `longVel`, `latVel`, `vertVel` | nopeus projisoituna eteenpäin, oikealle (= eteenpäin x ylös) ja ylös |
| `longAcc`, `latAcc`, `vertAcc` | maailman nopeuden muutos ±2 näytteen yli, projisoituna samoille akseleille (auton omien antureiden koordinaatistoa ei ole dokumentoitu, joten niitä ei käytetä) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | sellaisenaan lähetettynä |
| `absActive`, `tcActive` | ABS- ja TC-valot, jos autossa on ne |
| `wheelSurfaceSpeed.*` | pyörän pintanopeuden itseisarvo |
| `wheelSpeed.*` | pyörimisnopeus |
| `wheelLoad.*` | kuorma |
| `groundContact.*` | 0, kun materiaali on negatiivinen, muuten 1 |

Paketit, joissa ei ole tunnistetta tai jotka ovat lyhyempiä kuin 160 tavua, ohitetaan.

## Kierrokset {#laps}

`LineSplitter` toimii kuten AC EVO:lla. Linja on kohta, josta tallennus alkoi. Kierros sulkeutuu siinä, missä auto seuraavan kerran kulkee lähimpänä sitä samaan suuntaan, vähintään 300 m myöhemmin. Ajo sulkeutuu, kun auto seisoo paikallaan 8 sekuntia. Kierros lasketaan täydeksi vain, jos se alkoi yli 5 m/s nopeudesta. Siksi ensimmäinen kierros paikaltaan lähdöstä on osittainen. Kun modin kello menee taaksepäin yli puoli sekuntia (auto nollattiin), sillä hetkellä auki oleva ajo suljetaan ensin. Se kirjoitetaan osittaisena ajona, jos se kattoi vähintään 300 m, kuten tallennuksen lopussa. Sitten jakaja aloittaa alusta. Katso [Kierros- ja osuusjako](lap-splitting.md).

## Kierrostiedosto {#the-lap-file}

`game` on `beamng`, `meta` on `{"discipline": "circuit"}`, ja tiedostot nimetään muotoon `beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Luistoa ei kirjoiteta. Katselin johtaa sen pyörien pintanopeuksista (katso [Luisto, ajautuminen ja johdetut kanavat](slip-and-drift.md)). Sijainnit ovat samassa koordinaatistossa kuin GameFiles-BeamNG-radan vienti, joten tallennettu kierros asettuu viedylle radalle.
