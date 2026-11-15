---
title: BeamNG.drive
nav_order: 4
lang: "sl"
source: telemetry-beamng.md
source_hash: "825665685a83"
nav_exclude: true
search_exclude: true
---
# BeamNG.drive {#beamngdrive}

```bash
python -m heat3d_capture telemetry --game beamng --install    # copy the mod, then record
python -m heat3d_capture telemetry --game beamng -o laps      # record
```

Nato v igri odprite **Options > Other > Protocols** in vklopite **„others“**.

Koda: [`telemetry/beamng.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/telemetry/beamng.py)
in modifikacija [`mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/mods/beamng/heat3d/lua/vehicle/protocols/heat3d.lua).
Testi: `tests/test_beamng.py`, na paketih, zgrajenih iz strukture modifikacije. **Modifikacija še ni
bila zagnana v igri.**

## Zakaj modifikacija {#why-a-mod}

BeamNG pošilja telemetrijo prek »protokolov«: modulov Lua v vozilu, ki jih lastna datoteka igre
`lua/vehicle/protocols.lua` zapakira in pošlje prek UDP iz vozila, ki ga vozi igralec. Standardni ne
vsebujejo tega, kar potrebuje analiza vožnje – OutGauge nima položaja, MotionSim nima koles, OutSim
pa je v trenutnih različicah samo prazna lupina. Zato ta projekt prinaša svoj protokol, `heat3d`. Ne
dotika se ničesar zunaj Lua lastnega vozila.

## Namestitev {#installing}

`--install` skopira `mods/beamng/heat3d` v `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d`
(BeamNG 0.30 in novejše hranijo uporabniške modifikacije tam), pred tem izbriše starejšo kopijo in
izpiše, kam je šla. Brez `LOCALAPPDATA` se vrne na domačo mapo. Mapo lahko kopirate tudi ročno.

Po `--install` se snemanje nadaljuje takoj.

## Modifikacija {#the-mod}

| Nastavitev (v `heat3d.lua`) | Vrednost |
|---|---|
| Naslov | `127.0.0.1` |
| Vrata | `4460` – spremenite jo tukaj in snemalniku podajte isti `--port` |
| Največja hitrost posodabljanja | 100 Hz |
| Korak fizike | uporabljen (`isPhysicsStepUsed` vrne true) |

Vsak paket je 4-bajtna oznaka `H3D1`, ki ji sledi 39 floatov little-endian (skupaj 160 bajtov):

| Polje | Število | Vir v Lua vozila |
|---|---|---|
| `time` | 1 | lastna ura modifikacije: vsota korakov fizike, ponastavi se ob ponastavitvi vozila |
| položaj | 3 | `obj:getPositionXYZ()` |
| hitrost | 3 | `obj:getVelocityXYZ()` (svet) |
| naprej | 3 | `obj:getDirectionVector()` |
| navzgor | 3 | `obj:getDirectionVectorUp()` |
| `yawRate` | 1 | `obj:getRollPitchYawAngularVelocity()` |
| `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear`, `abs`, `tcs` | 9 | `electrics.values`: `throttle`, `brake`, `clutch`, `parkingbrake`, `steering_input`, `rpm`, `gearIndex`, ter 1/0 iz `absActive` in `tcsActive` |
| `wheelSpeed` | 4 | hitrost površine vsakega kolesa (m/s) |
| `wheelAngular` | 4 | kotna hitrost, pomnožena s smerjo kolesa (rad/s) |
| `wheelLoad` | 4 | `downForce` (N) |
| `wheelMaterial` | 4 | `contactMaterialID1`, -1, kadar je kolo v zraku |

Štiri kolesa se izberejo glede na **to, kje so na vozilu**, ne po imenu (imena se med vozili
razlikujejo): spredaj ali zadaj po položaju vozla vzdolž vozila, levo ali desno čez vozilo (okvir
vozila +X levo, -Y naprej), za vsak vogal pa se vzame kolo, ki je najbolj oddaljeno od središča.
Manjkajoči vogal se pošlje kot ničle z materialom -1.

## Kaj z njim naredi snemalnik {#what-the-recorder-does-with-it}

Svet BeamNG ima Z navzgor; svet pregledovalnika ima Y navzgor. Položaji in vektorji se zasučejo okoli X,
`(x, y, z) -> (x, z, -y)`, kar ohrani sučnost sveta. Nato:

| Kanal | Izpeljano kot |
|---|---|
| `x`, `y`, `z` | zasukan položaj |
| `speed` | dolžina zasukane hitrosti |
| `longVel`, `latVel`, `vertVel` | hitrost, projicirana na naprej, na desno = naprej x navzgor, na navzgor |
| `longAcc`, `latAcc`, `vertAcc` | sprememba hitrosti sveta v ±2 vzorcih, projicirana na iste osi (okvir lastnih senzorjev vozila ni dokumentiran, zato se ne uporabljajo) |
| `yaw` | `atan2(forward.x, forward.z)` |
| `yawRate`, `throttle`, `brake`, `clutch`, `handbrake`, `steer`, `rpm`, `gear` | kot poslano |
| `absActive`, `tcActive` | lučki ABS in TC, kjer jih vozilo ima |
| `wheelSurfaceSpeed.*` | absolutna vrednost hitrosti površine kolesa |
| `wheelSpeed.*` | vrtenje |
| `wheelLoad.*` | obremenitev |
| `groundContact.*` | 0, kadar je material negativen, sicer 1 |

Paketi brez oznake ali krajši od 160 bajtov se prezrejo.

## Krogi {#laps}

`LineSplitter`, kot pri AC EVO: črta je točka, kjer se je začelo snemanje; krog se zaključi, ko se
vozilo naslednjič najbolj približa tej točki in pelje v isti smeri, vsaj 300 m pozneje; tek se
zaključi, ko vozilo 8 sekund miruje. Krog šteje za popolnega, samo če se je začel pri več kot 5 m/s,
zato je prvi krog z mesta delni. Kadar uro modifikacije za več kot pol sekunde vrne nazaj (vozilo je
bilo ponastavljeno), se najprej zaključi tek, ki je bil takrat odprt – zapiše se kot delni tek, če je
pokril vsaj 300 m, tako kot ob koncu posnetka – nato se delilnik začne znova. Glejte
[Razdelitev krogov in odsekov](lap-splitting.md).

## Datoteka kroga {#the-lap-file}

`game` je `beamng`, `meta` je `{"discipline": "circuit"}`, datoteke se imenujejo
`beamng_<stamp>_lap<n>_<seconds>s[_partial].json`. Zdrs se ne zapiše; pregledovalnik ga izpelje iz hitrosti
površin koles (glejte [Zdrs, drift in izpeljani kanali](slip-and-drift.md)). Položaji so v istem
okvirju, ki ga zapiše izvoz proge BeamNG iz GameFiles, zato posneti krog leži na izvoženi progi.
