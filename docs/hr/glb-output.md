---
title: Izlaz .glb
nav_order: 6
lang: "hr"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Izlaz .glb {#the-glb-output}

Rekonstrukcija se zapisuje kao binarna datoteka glTF 2.0 (`.glb`) koju 3DHeat preglednik učitava
kroz panel Pozadina / razina bez ikakve posebne obrade - isti ugovor koji piše Unreal izvoznik.
Kod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Piše se ručno, a ne kroz biblioteku za glTF: izlaz je uski podskup (jedan spremnik, zbijeno
posloženo, bez animacije i skinninga), a ovisnost koja zna pisati sav glTF donijela bi svoje
neslaganje verzija zbog nekoliko stotina redaka.

## Što je u datoteci skeniranja {#what-is-in-a-scans-file}

| Dio (naziv čvora i mreže) | Sadržaj |
|---|---|
| `ground:<name>` | trokuti unutar 35 stupnjeva od okretanja prema gore |
| `structure:<name>` | sve ostalo |

`<name>` je naziv datoteke bez nastavka pri spremanju iz prozora, ili naziv videa za `reconstruct`.
Dio bez trokuta se izostavlja. Skeniranje nikad ne piše dio `water:`. `asset.generator` je
`heat3d-capture-scan`.

## Ugovor {#the-contract}

- **Jedan čvor po dijelu**, nazvan oznakom dijela; mreža ponavlja naziv. Preglednik čita prvo
  naziv *čvora*, pa bi samo imenovanje mreža izgubilo klasifikaciju.
- Oznaka je `<class>:<name>`, s klasom `ground`, `structure` ili `water` - prefiks koji preglednik
  prepoznaje (`^(ground|structure|water)\s*[:|]`) pa klasu uzima zdravo za gotovo umjesto da je
  pogađa iz geometrije. Tlo se prikazuje punim, a konstrukcije gotovo prozirne.
- **Koordinate su u prostoru pregledniku**: Y gore, desnoruki sustav, i **skalirane na centimetre**
  (metri x 100) da odgovaraju Unreal izvozniku, pa se snimka i izvoz motora istog mjesta učitavaju
  u istoj veličini sa istim zadanim kutom kamere. Najviša razina datoteke `extras.unit_metres` je
  `0.01` (jedna jedinica je centimetar), pa je čitač koji radi u metrima, primjerice
  [`locate`](locate.md), uzima u stvarnoj veličini. Skeniranje postavljeno telemetrijom Forze je
  iznimka u orijentaciji: ostaje u vlastitom svijetu igre, Y gore i lijevoruki, baš kao datoteke
  krugova, pa krugovi snimljeni preko njega padaju na pravo mjesto. Kad je mjerilo skeniranja
  pronađeno na kasnijem ključnom kadru ([Mjerilo](reconstruction-pose.md#scale)), taj faktor se
  ugrađuje u zapisano mjerilo.
- `COLOR_0` čita preglednik; njime oboji tlo kad je prekidač *Snimljena boja* na panelu Pozadina /
  razina uključen (isključen je zadano).
- Skeniranje s mjestima označenim ručno dobiva uz sebe datoteku `<name>.marks.json`; vidi
  [Spremanje](reconstruction-scan-ui.md#saving).
- Po primitivu: `POSITION` (float VEC3, s `min` i `max`, iz kojih preglednik kadrira kameru),
  `NORMAL` (float VEC3), izborni `COLOR_0` (float VEC3, 0..1), izborni `TEXCOORD_0`; indeksi kao
  16-bitni ako je svaki indeks manji od 65,536, inače 32-bitni; način trokuta.
- Svaki pogled na spremnik počinje na 4-bajtnoj granici; JSON dio je popunjen razmacima, a BIN dio
  nulama do 4 bajta.

## Provjere prije pisanja {#checks-before-writing}

Svaki dio se provjerava i odbija uz poruku s njegovim imenom ako nema vrhova, ako broj indeksa nije
cijeli broj trokuta, ako je indeks izvan raspona ili negativan, ako pozicije nisu konačne, ili ako
normale ili boje ne odgovaraju broju vrhova. Normale se računaju kad nedostaju, **ponderirane
površinom** (marching cubes ostavlja sitne trokute uz velike ploh, a neponderirani prosjek bi pustio
da tih sitnih trokuta odlučuju nad plohom na kojoj leže); vrh bez smjera dobiva "gore". Ako se ne
zapiše nijedan dio, to je greška.

Izvoz ne vraća ništa - a prozor kaže "Nothing to save" (Nema što spremiti) - kad volumen ne daje
površinu, umjesto da zapiše praznu datoteku koja bi izgledala kao uspješno skeniranje.

## Teksture {#textures}

Pisac podržava PNG teksturu osnovne boje po dijelu (s UV koordinatama, dvostranim, nemetalnim
materijalom s potpunom hrapavošću). Skeniranja ne koriste je; nose boju po vrhu. Vidi
[boja](reconstruction-fusion-and-texture.md#colour).

## Referentna razina {#the-reference-level}

`geometry/reference.py` gradi sintetičku razinu točno poznate veličine kroz isti pisac: tlo od 400 m
s podjelom, tri zgrade 20 x 20 x 12 m i jezero od 50 m 1,5 m ispod tla, svaka klasa u drugoj
ravnoj boji. Testovi preglednika je generiraju i čitaju pravim čitačem preglednika, pa format
ostaje testiran s obiju strana bez igre i bez hardvera za snimanje.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
