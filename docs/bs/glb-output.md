---
title: "Izlaz .glb"
nav_order: 6
lang: "bs"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Izlaz .glb {#the-glb-output}

Rekonstrukcija se piše kao binarna glTF 2.0 datoteka (`.glb`) koju preglednik 3DHeat učitava
kroz svoj panel Pozadina / nivo bez posebne obrade - isti ugovor koji piše Unreal izvoznik.
Kod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Piše se ručno, a ne kroz glTF biblioteku: izlaz je uzak podskup (jedan
bafer, gusto pakovan, bez animacije, bez skeleta), a zavisnost koja zna pisati cijeli glTF
donijela bi nesklad verzija zbog nekoliko stotina linija koda.

## Šta je u datoteci skeniranja {#what-is-in-a-scan-s-file}

| Dio (ime čvora i mreže) | Sadržaj |
|---|---|
| `ground:<name>` | trouglovi unutar 35 stepeni od okrenutosti prema gore |
| `structure:<name>` | sve ostalo |

`<name>` je ime datoteke bez ekstenzije pri spremanju iz prozora, ili ime videa
za `reconstruct`. Dio bez trouglova se izostavlja. Skeniranje nikad ne piše dio `water:`.
`asset.generator` je `heat3d-capture-scan`.

## Ugovor {#the-contract}

- **Jedan čvor po dijelu**, imenovan oznakom dijela; mreža ponavlja ime. Preglednik
  prvo čita ime *čvora*, pa bi imenovanje samo mreža izgubilo klasifikaciju.
- Oznaka je `<class>:<name>` s klasom `ground`, `structure` ili `water` - prefiks koji
  preglednik prepoznaje (`^(ground|structure|water)\s*[:|]`) da klasu uzme zdravo za gotovo umjesto
  da je pogađa iz geometrije. Tlo se renderira puno, strukture skoro prozirno.
- **Koordinate su u prostoru preglednika**: Y gore, desnoruki sistem, **razmjera u centimetrima** (metri x
  100) da odgovara Unreal izvozniku, pa se snimak i izvoz iz engine-a istog mjesta učitaju
  iste veličine sa istim zadanim postavkama kamere. Gornji `extras.unit_metres` datoteke je `0.01`
  (jedinica je centimetar), pa čitač koji radi u metrima, kao što je [`locate`](locate.md), uzima
  pravu veličinu. Skeniranje postavljeno Forza telemetrijom je izuzetak
  u pogledu orijentacije koordinatnog sistema: ostaje u svijetu same igre, Y gore i ljevoruki sistem, tačno kao datoteke krugova,
  tako da krugovi snimljeni preko njega legnu na njega. Kad je razmjer skeniranja pronađen na kasnijem ključnom kadru
  ([Razmjer](reconstruction-pose.md#scale)), taj faktor se ugrađuje u upisani razmjer.
- `COLOR_0` čita preglednik, koji njime sjenči tlo kad je prekidač *Snimljena boja* njegovog panela
  Pozadina / nivo uključen (zadano je isključen).
- Skeniranje s ručno označenim tačkama dobija `<name>.marks.json` pored sebe; pogledajte
  [Spremanje](reconstruction-scan-ui.md#saving).
- Po primitivu: `POSITION` (float VEC3, sa `min` i `max`, iz kojih preglednik kadrira svoju kameru),
  `NORMAL` (float VEC3), opcionalno `COLOR_0` (float VEC3, 0..1), opcionalno `TEXCOORD_0`;
  indeksi su 16-bitni kad je svaki indeks ispod 65.536, inače 32-bitni; način trouglovi.
- Svaki pogled bafera počinje poravnat na 4 bajta; JSON dio se dopunjava razmacima, a BIN dio
  nulama do 4 bajta.

## Provjere prije pisanja {#checks-before-writing}

Svaki dio se provjerava i odbija porukom koja ga imenuje kad nema vrhova, kad broj
indeksa nije cijeli broj trouglova, kad je indeks van opsega ili negativan, kad pozicije
nisu konačni brojevi, ili kad se normale ili boje ne poklapaju s brojem vrhova. Normale se računaju kad nedostaju,
**ponderirane površinom** (marching cubes ostavlja tanke trouglove pored velikih ploha, a neponderirani prosjek
dopušta sitnim trouglovima da nadglasaju plohu na kojoj leže); degenerirani vrh dobija "gore". Pisanje
bez ijednog dijela je greška.

Izvoz ne vraća ništa - a prozor kaže "Nothing to save" - kad volumen ne daje
površinu, umjesto da napiše praznu datoteku koja bi izgledala kao uspješno skeniranje.

## Teksture {#textures}

Pisač podržava PNG teksturu osnovne boje po dijelu (s UV-ovima, dvostrani, nemetalni,
potpuno hrapav materijal). Skeniranja je ne koriste; nose boju po vrhu. Pogledajte
[boja](reconstruction-fusion-and-texture.md#colour).

## Referentni nivo {#the-reference-level}

`geometry/reference.py` gradi sintetički nivo tačno poznate veličine kroz isti pisač:
400 m podijeljeno tlo, tri zgrade 20 x 20 x 12 m i bara od 50 m 1,5 m ispod tla, svaka
klasa u zasebnoj jednolikoj boji. Vlastiti testovi preglednika ga generiraju i parsiraju pravim
parserom preglednika, pa je format pod testom s obje strane bez igre i bez opreme
za snimanje.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
