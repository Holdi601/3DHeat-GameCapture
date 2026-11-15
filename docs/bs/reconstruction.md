---
title: "Rekonstrukcija nivoa"
nav_order: 6
lang: "bs"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonstrukcija nivoa iz igranja {#level-reconstruction-from-gameplay}

Prođite polako kroz nivo ili vozite stazu, a skener pretvara ono što je ekran pokazao u
`.glb` koji preglednik 3DHeat učitava kao kontekst ispod telemetrije - isti ugovor datoteke
koji piše Unreal izvoznik. Namijenjen je slučaju kad niko nije izvezao mapu, a datoteke igre
se ne mogu čitati; izvoz iz engine-a ili izvoz datoteka igre je tačan, ovo je procjena.

## Cjevovod {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Faza | Skeniranje uživo (`heat3d_capture.ui`) | Offline (`reconstruct`) | Stranica |
|---|---|---|---|
| Kadrovi | monitor, prozor ili video, smanjeni na najdužu stranu zadane kvalitete | video, uzorkovan dvaput (plan rješavanja i interval fuzije) | [Snimanje](reconstruction-capture.md) |
| Ključni kadrovi | zadržavaju se prema tome koliko se slika promijenila, prag prilagođen snimanju | svakih `--fuse-interval` sekundi | [Snimanje](reconstruction-capture.md#keyframes) |
| Maske | `ScreenMask` zasnovana na promjeni, zatim `FlowMask` zasnovana na toku nakon 40 ključnih kadrova | `FlowMask` naučena iz četiri prolaza videa; ne primjenjuje se na rješavač | [Snimanje](reconstruction-capture.md#what-is-not-the-world) |
| Dubina | ONNX model na najboljem GPU backendu | PyTorch Depth Anything V2 Small | [Dubina](reconstruction-depth.md) |
| Poza | vizualna odometrija ili tačna Forza telemetrija | VGGT prozori spojeni u jednu putanju, interpolirani | [Poza](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Razmjer | visina kamere iznad tla (1,15 m) jednom, ili telemetrija | vlastite jedinice riješene putanje | [Poza](reconstruction-pose.md#scale) |
| Fuzija | ponderirana zauzetost, rijetki voksel; mreža pokrivenosti | ista | [Fuzija](reconstruction-fusion-and-texture.md) |
| Izlaz | `.glb`, dijelovi tlo/struktura, boja po vrhu, centimetri | isti | [Izlaz .glb](glb-output.md) |

Kod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - postavke i tempo jednog skeniranja; `reconstruct.py` - ključni kadrovi u geometriju;
`offline.py` - offline putanja), s fazama u `capture/`, `depth/`, `pose/`, `fusion/`
i `geometry/`.

## Odakle dolazi tačnost {#where-accuracy-comes-from}

Monokularna dubina je tačna samo do nepoznatog razmjera - fotografija sobe i kućice za lutke
je ista slika. Zato se mreži prepušta ono u čemu je dobra
(relativni oblik, ivice, tanke strukture), a razmjer i putanju kamere daje nešto što ih zna:

| Igra | Putanja kamere | Razmjer |
|---|---|---|
| Forza Horizon / Motorsport s uključenom telemetrijom | tačna, iz Data Out, interpolirana na vrijeme snimanja svakog kadra | tačan: dubina se usidri triangulacijom karakteristika između dvije poznate poze |
| Sve ostalo, uživo | vizualna odometrija, lančana od kadra do kadra | jednom fiksiran iz pretpostavljene visine kamere iznad tla |
| Snimak, offline | VGGT, riješen preko preklapajućih prozora | vlastite jedinice rješenja (nisu metričke) |

Jedini broj koji se skeneru kaže, a ne mjeri, je **horizontalno vidno polje** igre
(u prozoru zadano 90 stepeni; trkaće igre su bliže 65). Preusko, i nivo se rekonstruira
dublji nego što jest; preširoko, i spljošti se.

## Upozoravanje korisnika na vrijeme {#telling-the-user-early}

Skeniranje je fizički čin - neko nekoliko minuta hoda nivoom - a skup neuspjeh je
završiti šetnju i otkriti da nije valjala. Zato prozor prije početka mjeri propusnost dubine
ove mašine i kaže kakvo će skeniranje biti
([Runtime](runtime.md#what-to-expect-from-this-machine)); tokom skeniranja prikazuje mapu
pokrivenosti s numeriranim slabim tačkama, zdravlje praćenja, traku brzine hoda, traku oštrine i
jednu uputu u datom trenutku, u prozoru i u prekrivaču kroz koji se može kliknuti preko igre
([Prozor skeniranja](reconstruction-scan-ui.md)).

## Izmjereno na sintetičkoj referentnoj istini {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` renderira sobu 12 x 8 m (visoku 4 m) iz poznate putanje kamere, s
analitičkom (ne mrežnom) dubinom, i rekonstruira je s vokselima od 0,2 m. Tvrdi da je postavljeno više od
90% kadrova, srednja greška putanje je ispod 0,35 m (najgora ispod 1 m), pređena
udaljenost je u granicama 10% od istine, soba ispada prave širine do 1,5 m, preko
75% površine zida leži unutar 0,45 m od pravog zida, šetnja u stilu premjera daje jasno
bolju pokrivenost nego hodanje pravo naprijed, a scena bez karakteristika se odbija umjesto da se
izmisli. Analitička dubina izdvaja pozu, razmjer i
fuziju od mreže; kako mreža prolazi na pravom igranju je zasebno pitanje na koje nijedna
sintetička scena ne odgovara. `tests/test_track_width.py` provjerava da krug vožen van središta na
putu poznate širine rekonstruira širinu puta, a ne samo vožnu liniju.

## Stranice {#pages}

- [Prozor skeniranja](reconstruction-scan-ui.md) - svaka kontrola, prečica i element prekrivača
- [Snimanje, maske i kvalitet kadra](reconstruction-capture.md)
- [Dubina](reconstruction-depth.md)
- [Poza kamere i razmjer](reconstruction-pose.md)
- [Fuzija, pokrivenost i boja](reconstruction-fusion-and-texture.md)
- [Izlaz .glb](glb-output.md)
- [Offline rekonstrukcija](reconstruction-offline.md)
