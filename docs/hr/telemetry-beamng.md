---
title: BeamNG.drive
nav_order: 4
lang: "hr"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # kopiraj mod, zatim snimaj
python -m heat3d_capture telemetry --game beamng -o laps      # snimaj
```

Zatim u igri: **Options > Other > Protocols**, uključite **"others"**.

Kod: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
i mod [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testovi: `tests/test_beamng.py`, na paketima izgrađenima iz strukture moda. **Mod još nije pokrenut u
igri.**

## Zašto mod {#why-a-mod}

BeamNG šalje telemetriju kroz "protokole": Lua module u vozilu koje vlastiti
`lua/vehicle/protocols.lua` igre pakira i šalje preko UDP-a iz automobila koji igrač vozi. Ugrađeni
ne nose ono što treba analiza upravljanja automobilom - OutGauge nema položaj, MotionSim nema kotače, a
OutSim je u aktualnim verzijama samo zamjena. Zato ovaj projekt isporučuje vlastiti protokol, `heat3d`. Ne
dira ništa izvan Lua koda samog vozila.

## Instalacija {#installing}

`--install` kopira `mods/beamng/heat3d` u
`%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (BeamNG 0.30 i noviji tamo čuvaju
korisničke modove), brišući prije toga stariju kopiju, i ispiše kamo je otišao. Bez `LOCALAPPDATA`
koristi se početna mapa. Mapu možete kopirati i ručno.

Nakon `--install` odmah se nastavlja sa snimanjem.

## Mod {#the-mod}

| Postavka (u `heat3d.lua`) | Vrijednost |
|---|---|
| Adresa | `127.0.0.1` |
| Port | `4460` - promijenite ovdje i predajte isti `--port` snimaču |
| Najveća brzina osvježavanja | 100 Hz |
| Korak fizike | koristi se (`isPhysicsStepUsed` vraća true) |

Svaki paket je 4-bajtna oznaka `H3D1`, a za njom 39 float vrijednosti u little-endian zapisu (ukupno
160 bajta):

| Polje | Broj | Izvor u Lua kodu vozila |
|---|---|---|
| `time` | 1 | vlastiti sat moda: zbroj koraka fizike, resetira se kad se vozilo resetira |
| položaj | 3 | `obj:getPositionXYZ()` |
| brzina | 3 | `obj:getVelocityXYZ()` (svijet) |
| naprijed | 3 | `obj:getDirectionVector()` |
| gore | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, te 1/0 iz `absActive` i `tcsActive` |
| `wheelSpeed` | 4 | brzina površine svakog kotača (m/s) |
| `wheelAngular` | 4 | kutna brzina pomnožena smjerom kotača (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1 kad nije na tlu |

Četiri kotača biraju se prema tome **gdje stoje na automobilu**, a ne po nazivu (nazivi se razlikuju
među vozilima): naprijed ili straga po položaju čvora duž automobila, lijevo ili desno preko njega
(lokalni smjer vozila +X lijevo, -Y naprijed), uzimajući za svaki kut kotač koji je najdalje od
središta. Kut koji nedostaje šalje se kao nule s materijalom -1.

## Što s tim radi snimač {#what-the-recorder-does-with-it}

Svijet BeamNG-a ima Z gore; svijet preglednika ima Y gore. Položaji i vektori se okreću oko X-a,
`(x, y, z) -> (x, z, -y)`, što čuva orijentaciju svijeta. Zatim:

| Kanal | Izvedeno kao |
|---|---|
| `x`, `y`, `z` | okrenuti položaj |
| `speed` | duljina okrenute brzine |
| `longVel`, `latVel`, `vertVel` | brzina projicirana na naprijed, na desno = naprijed x gore, na gore |
| `longAcc`, `latAcc`, `vertAcc` | promjena brzine svijeta kroz ±2 uzorka, projicirana na iste osi (okvir vlastitih senzora automobila nije dokumentiran, pa se ne koristi) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | kako su poslani |
| `absActive`, `tcActive` | lampice ABS-a i TC-a, gdje ih automobil ima |
| `wheelSurfaceSpeed.*` | apsolutna vrijednost brzine površine kotača |
| `wheelSpeed.*` | vrtnja |
| `wheelLoad.*` | opterećenje |
| `groundContact.*` | 0 kad je materijal negativan, inače 1 |

Paketi bez oznake ili kraći od 160 bajta se ignoriraju.

## Krugovi {#laps}

`LineSplitter`, kao za AC EVO: točka na kojoj je snimanje počelo je linija; krug se zatvara gdje se
automobil sljedeći put najbliže prođe, u istom smjeru, najmanje 300 m kasnije; vožnja se zatvara kad
automobil stoji 8 sekundi. Krug se računa kao cijeli samo ako je počeo brzinom većom od 5 m/s, pa je
prvi krug iz mirovanja djelomičan. Kad sat moda skoči unatrag za više od pola sekunde (automobil je
resetiran), vožnja otvorena u tom trenutku se prvo zatvara - zapisuje se kao djelomična ako je pokrila
najmanje 300 m, kao na kraju snimke - i tada se splitter kreće ispočetka. Vidi
[Kako se krugovi i etape dijele](lap-splitting.md).

## Datoteka kruga {#the-lap-file}

`game` je `beamng`, `meta` je `{"discipline": "circuit"}`, datoteke se zovu
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Klizanje se ne zapisuje; preglednik ga
izvodi iz brzina površine kotača (vidi [Klizanje, drift i izvedeni kanali](slip-and-drift.md).
Položaji su u istom okviru koji piše izvoz staze BeamNG-a u GameFiles, pa snimljeni krug sjedi na
izvezenoj stazi.
