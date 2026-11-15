---
title: "BeamNG.drive"
nav_order: 4
lang: "bs"
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

Zatim u igri: **Options > Other > Protocols**, uključite **"others"**.

Kod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
i mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testovi: `tests/test_beamng.py`, na paketima izgrađenim iz modove strukture. **Mod još nije
pokrenut u igri.**

## Zašto mod {#why-a-mod}

BeamNG šalje telemetriju kroz "protokole": Lua module u vozilu koje igrin vlastiti
`lua/vehicle/protocols.lua` pakuje i šalje preko UDP-a iz auta kojim igrač vozi. Standardni
ne nose ono što analiza upravljanja autom treba - OutGauge nema poziciju,
MotionSim nema točkove, a OutSim je u trenutnim verzijama prazan okvir. Zato ovaj projekat isporučuje vlastiti
protokol, `heat3d`. Ne dira ništa izvan vlastitog Lua koda vozila.

## Instaliranje {#installing}

`--install` kopira `mods/beamng/heat3d` u
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 i noviji tu drže
korisničke modove), prethodno briše stariju kopiju, i ispisuje kamo je otišao. Bez
`LOCALAPPDATA` vraća se na korisnički folder. Folder možete i kopirati ručno.

`--install` zatim ide ravno dalje u snimanje.

## Mod {#the-mod}

| Postavka (u `heat3d.lua`) | Vrijednost |
|---|---|
| Adresa | `127.0.0.1` |
| Port | `4460` - promijenite ga ovdje i proslijedite isti `--port` snimaču |
| Maksimalna brzina osvježavanja | 100 Hz |
| Fizički korak | koristi se (`isPhysicsStepUsed` vraća true) |

Svaki paket je 4-bajtni magični broj `H3D1` iza kojeg slijedi 39 little-endian float vrijednosti (ukupno 160 bajta):

| Polje | Broj | Izvor u Lua kodu vozila |
|---|---|---|
| `time` | 1 | modov vlastiti sat: zbir fizičkih koraka, resetira se kad se vozilo resetira |
| position | 3 | `obj:getPositionXYZ()` |
| velocity | 3 | `obj:getVelocityXYZ()` (svijet) |
| forward | 3 | `obj:getDirectionVector()` |
| up | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, te 1/0 iz `absActive` i `tcsActive` |
| `wheelSpeed` | 4 | brzina površine svakog točka (m/s) |
| `wheelAngular` | 4 | ugaona brzina puta smjer točka (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 kad je točak u zraku |

Četiri točka biraju se prema **tome gdje stoje na autu**, a ne po imenu (imena se razlikuju među
vozilima): prednji ili zadnji prema položaju čvora duž auta, lijevi ili desni preko njega
(u okviru vozila +X je lijevo, -Y naprijed), pri čemu se za svaki ugao uzima točak najdalji od
središta. Ugao koji nedostaje šalje se kao nule s materijalom -1.

## Šta snimač radi s tim {#what-the-recorder-does-with-it}

BeamNG svijet ima Z gore; preglednikov ima Y gore. Pozicije i vektori se okreću oko X,
`(x, y, z) -> (x, z, -y)`, što čuva orijentaciju sistema svijeta. Zatim:

| Kanal | Izvodi se kao |
|---|---|
| `x`, `y`, `z` | okrenuta pozicija |
| `speed` | dužina okrenute brzine |
| `longVel`, `latVel`, `vertVel` | brzina projicirana na naprijed, na desno = naprijed x gore, na gore |
| `longAcc`, `latAcc`, `vertAcc` | promjena brzine u svijetu preko +-2 uzorka, projicirana na iste ose (okvir senzora samog auta nije dokumentiran, pa se ne koriste) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | kako su poslani |
| `absActive`, `tcActive` | ABS i TC lampice, gdje ih auto ima |
| `wheelSurfaceSpeed.*` | apsolutna vrijednost brzine površine točka |
| `wheelSpeed.*` | rotacija |
| `wheelLoad.*` | opterećenje |
| `groundContact.*` | 0 kad je materijal negativan, inače 1 |

Paketi bez magičnog broja ili kraći od 160 bajta se ignoriraju.

## Krugovi {#laps}

`LineSplitter`, kao za AC EVO: tačka gdje je snimanje počelo je linija; krug se zatvara
kad auto sljedeći put prođe najbliže njoj krećući se istim smjerom, najmanje 300 m kasnije; vožnja
se zatvara kad auto stoji mirno 8 sekundi. Krug se računa kao potpun samo ako je počeo pri
brzini većoj od 5 m/s, pa je prvi krug iz mjesta djelimičan. Kad modov
sat ode unazad za više od pola sekunde (auto je resetiran), vožnja otvorena u tom trenutku
se prvo zatvara - upisuje se kao djelimična vožnja ako je prešla najmanje 300 m, kao na kraju
snimanja - a zatim razdjelnik počinje iznova. Pogledajte [Razdvajanje krugova i etapa](lap-splitting.md).

## Datoteka kruga {#the-lap-file}

`game` je `beamng`, `meta` je `{"discipline": "circuit"}`, datoteke se zovu
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Slip se ne upisuje; preglednik ga izvodi
iz brzina površine točkova (pogledajte [Slip, drift i izvedeni kanali](slip-and-drift.md)).
Pozicije su u istom okviru koji piše izvoz BeamNG staze iz GameFiles, pa snimljeni
krug leži na izvezenoj stazi.
