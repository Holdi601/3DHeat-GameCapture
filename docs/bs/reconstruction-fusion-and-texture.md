---
title: "Fuzija, pokrivenost i boja"
nav_order: 5
lang: "bs"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fuzija, pokrivenost i boja {#fusion-coverage-and-colour}

Kod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Svaki postavljeni ključni kadar istovremeno ažurira dvije rijetke mreže: **volumen površine**, koji postaje
mreža trokuta, i **mrežu pokrivenosti**, koja kaže koliko joj vjerovati i kamo se vratiti.
Obje se ažuriraju po ključnom kadru, a ne na kraju, jer igrač upravlja prema mapi pokrivenosti.

## Od dubine do tačaka {#from-depth-to-points}

Za svaki ključni kadar čija je poza poznata **i** čija dubina ima skalu:

1. Koristi se svaki drugi piksel u svakom smjeru (`PIXEL_STRIDE = 2`; susjedni pikseli
   jedne površine nisu nezavisna mjerenja).
2. Dubina se pretvara u metre afinim podešavanjem kadra.
3. Zadržava se samo između **0,35 m** (bliže je oružje, HUD, hauba) i **60 m**
   (monokularna greška raste otprilike s kvadratom udaljenosti, pa su daleke tačke šum oblikovan
   kao geometrija) i samo na pikselima svijeta iz maske.
4. Podiže se kroz model kamere i premješta u svijet pozom.
5. Svaka tačka nosi boju piksela.

Kadar koji je pozicioniran, ali nema skalu dubine, računa se kao *postavljen*, ali ne *spojen*.

## Volumen površine {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voksel je "Surface detail" u prozoru.

### Ponderisana zauzetost, ne TSDF {#weighted-occupancy-not-a-tsdf}

Odsječeno polje označene udaljenosti reže duž zraka svakog piksela i ispravno obrađuje tanke strukture i
čist slobodan prostor, jer zna da je zraka prošla *kroz* prazan prostor. To znači obilazak
zrake za svaki od stotina miliona piksela. Ovaj volumen umjesto toga akumulira
**ponderisanu zauzetost** po vokselu i pokreće marching cubes na zaglađenom rezultatu: dovoljno brzo da
radi tokom skeniranja, na mašini bez upotrebljivog GPU-a, a izlaz je zatvorena površina, a ne
oblak tačaka. Cijena: tanke strukture i slobodan prostor su lošiji nego što bi dao TSDF.

### Integracija kadra {#integrating-a-frame}

- Tačke se razvrstavaju u voksele (`floor(point / voxel)`).
- Svaki dodirnuti voksel dobija `weight x sqrt(count / max_count)`, gdje je `count` koliko je
  tačaka kadra palo u njega, a `weight = max(0.1, pose confidence)`. Kvadratni korijen: preko neke tačke,
  više piksela iste površine s istog mjesta prestaje biti dokaz; ponderisanje pouzdanošću
  poze sprječava da sumnjiva poza pomjera površinu.
- Boja je tekuća ponderisana srednja vrijednost po vokselu.

Mreža je **rijetka**: pređena ruta dodiruje sićušan dio svog graničnog okvira. Koordinate voksela
pakuju se u jedan 64-bitni ključ (21 bit po osi, do +-1.048.575 voksela - pri
0,25 m oko +-262 km) i traže sortiranim nizom i binarnom pretragom, potpuno vektorizirano.

### Izdvajanje mreže trokuta {#extracting-the-mesh}

1. Voksele s težinom ispod **0,35** se odbacuje (zalutale pojedinačne tačke na rubovima siluete
   postale bi šiljci).
2. Težine se skaliraju **75. percentilom** preko skeniranja i ograničavaju na 1.
3. Zauzeti prostor se reže na **blokove od 64 voksela** po stranici, svaki ostvaren s
   **haloom od 3 voksela** podataka susjeda (bez njega se svaka granica bloka zatvara u
   zid i put ispadne kao niz kutija).
4. Polje svakog bloka se zaglađuje Gaussom (sigma 0,8 voksela) da se ukloni nabor koji šum
   dubine ostavlja.
5. **Prvi prolaz**: 99. percentil zaglađenog polja, uzorkovan preko svih blokova (najviše 2
   miliona vrijednosti), postavlja jednu globalnu skalu nivoa. Normalizacija po bloku podigla bi usamljeni
   izuzetak u punu površinu u njegovom praznom bloku.
6. **Drugi prolaz**: polje svakog bloka podijeljeno tom skalom, marching cubes na **0,5**. Trokut
   pripada bloku u koji pada njegov **centroid**, pa se trokuti koji prelaze šav
   emituju tačno jednom.
7. Vrhovi se pomjeraju u svjetske jedinice u centrima voksela; svaki vrh uzima boju svog voksela
   (srednje siva tamo gdje pada izvan zauzetog voksela).

Izdvajanje po blokovima omogućava skeniranje veličine staze: jedan gusti niz preko kutije
kilometar puta kilometar pri 0,25 m imao bi milijarde ćelija. `tests/test_track_scale.py` učvršćuje
da to radi u toj razmjeri s memorijom proporcionalnom onome što je skenirano.

### Tlo i struktura {#ground-and-structure}

`classify` označava svaki trokut prema njegovoj normali (orijentisanoj normalama izdvojenih vrhova): unutar
**35 stepeni od ravno gore** je `ground`, sve ostalo `structure`. Preglednik crta tlo
puno, a strukture gotovo prozirno. **Voda se nikad ne tvrdi** - ne razlikuje se od ravnog
tla po obliku, a pogrešna oznaka bi dvorište prikazala kao jezero. Svaka oznaka postaje jedan
dio `.glb`-a ([Izlaz .glb](glb-output.md)).

## Pokrivenost {#coverage}

`CoverageGrid(voxel=0.5)` bilježi, po ćeliji od pola metra, četiri stvari koje nisu ista stvar:

| Pojam | Pohranjeno | Ocjena (svaka ograničena na 0..1) | Zašto se računa posebno |
|---|---|---|---|
| Koliko puta viđeno | broj ključnih kadrova koji su vidjeli ćeliju | `count / 3` | jednom je nagađanje bez čega uprosječiti |
| Iz koliko smjerova | zbir jediničnih smjerova pogleda | `(1 - spread) / (1 - 0.93)`, gdje je spread = dužina zbira / count | dvadeset kadrova koji idu ravno na zid nemaju paralaksu među sobom; dva pogleda pod trideset stepeni vrijede više |
| S koje udaljenosti | najbliža udaljenost gledanja | `1 - nearest / 40 m` | greška dubine raste otprilike s kvadratom udaljenosti |
| Koliko je dobro postavljena kamera | najbolja pouzdanost poze | pouzdanost | geometrija spojena sa sumnjivom pozom završi na pogrešnom mjestu |

Tačke kadra se prvo grupišu po ćeliji, pa deset hiljada piksela jednog zida računa kao jedno
opažanje iz jednog smjera.

**Kvalitet = proizvod ova četiri pojma**, a ne prosjek: to su uvjeti koji svi
moraju vrijediti. Mjesto viđeno dvjesto puta iz jednog smjera sa šezdeset metara loše je promatrano, a
prosjek bi to sakrio iza jednog odličnog pojma.

Glavne brojke (`summary`): zauzete ćelije, udio s kvalitetom najmanje 0,5 ("% well
seen" u prozoru), srednji kvalitet i volumen.

### Slabe tačke {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. ćelije s kvalitetom ispod 0,35 su slabe;
2. slabe ćelije grupišu se po **povezanosti** (26 susjeda, union-find samo preko zauzetih
   ćelija - ne raster preko graničnog okvira, što su na dugoj vožnji milioni praznih
   ćelija);
3. grupe od manje od 8 ćelija se ignorišu;
4. razlog svake grupe je najčešći *najslabiji pojam* njenih ćelija, a položaj srednja vrijednost
   njenih ćelija;
5. sortirano najveća prva (zatim najgori kvalitet), najviše 8.

| Razlog | Prikazani savjet |
|---|---|
| few views | Seen only once or twice — walk past it again. |
| one direction | Only seen from one angle. Step sideways and look at it again. |
| distant | Only seen from far away. Get closer to it. |
| poor tracking | The camera was not well located here. Approach it more slowly. |

Povezanost je bitna: grupisanje fiksnom mrežom blokova prijavljuje jednu zanemarenu sporednu sobu kao mnogo
odvojenih prstenova, i niko ne može razlikovati osam mjesta od jednog mjesta izbrojanog osam puta.

### Pogled iz ptičje perspektive {#the-plan-view}

`top_down(resolution)` projicira ćelije na x/z i zadržava **najbolji** kvalitet po koloni
(neko ko stoji u sobi ima slabu pokrivenost plafona i odličnu pokrivenost
poda; uprosječivanje bi sobu obojilo žuto). Nikad neopažene kolone označene su zasebno.
Prozor ga crta na 200 x 200, overlay na 120 x 120 ([Prozor za skeniranje](reconstruction-scan-ui.md#the-coverage-map)).

### Je li ovo moguće rekonstruisati? {#is-this-reconstructable}

Svakih 25 spojenih kadrova, kad ima najmanje 500 ćelija:

| Nalaz | Presuda | Poruka (skraćeno) |
|---|---|---|
| manje od 2% ćelija ima raspršenost pogleda ispod 0,93 | nije moguće rekonstruisati | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| medijan najbliže udaljenosti preko 25 m | nije moguće rekonstruisati | Everything was seen from N m away or further ... Get closer to what you want. |
| manje od 6% s dobrom raspršenošću | moguće rekonstruisati, s upozorenjem | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Niska paralaksa ima dva uzroka koja se ovdje ne mogu razlikovati, zbog čega poruka imenuje oba.

## Boja {#colour}

Boja po vokselu iz fuzije je jeftina i uživo, i mutna: svaki piksel u ćeliji od četvrt metra se
uprosječuje, uključujući one viđene bočno sa trideset metara. Zato se pri izvozu mreža boji
ponovo, jednom, iz samih kadrova:

- **Zadržani kadrovi**: do **160** ključnih kadrova (slika i poza), odabranih uzorkovanjem rezervoara tako da se
  rasprostru po cijelom skeniranju, a ne po njegovom kraju.
- **Po vrhu** (`project_colours`), svaki zadržani kadar doprinosi ako je vrh ispred
  kamere i unutar slike, površina nije okrenuta više od otprilike 70 stepeni od
  direktnog lica kamere (`|normal . view| > 0.34`), bliži je od **35 m**, i ništa bliže nije
  stajalo ispred njega (ispod).
- Svaki takav pogled ocjenjuje se `facing x (1 - distance / 35)`, pa blizak frontalni pogled pobjeđuje
  daleki koso. **4 najbolje ocijenjena** pogleda svakog vrha se zadržavaju - bez obzira na redoslijed
  kadrova, bolji pogled zamjenjuje najslabiji od četiri - i miješaju, ponderisano tom
  istom ocjenom.
- **Okluzija**: u svakom kadru se vlastiti vrhovi mreže u pogledu crtaju u međuspremnik dubine od
  ćelija od 2 piksela, zadržavajući najbliži po ćeliji. Vrh koji je za više od `0.3 m + 5%` svoje udaljenosti
  iza najbližeg u svojoj ćeliji bio je u tom kadru skriven - zid između kamere i
  puta iza - i taj pogled se ne računa. Test poznaje samo mrežu: okluder koji
  nikad nije spojen (automobil u prolazu, stup kokpita izvan HUD maske) ne hvata se.
- Vrh koji nijedan kadar nije vidio zadržava boju svog voksela; vrh bez oba je srednje siv (crna bi
  se čitala kao rupa).

Boja se zapisuje kao `COLOR_0` po vrhu, a ne kao atlas teksture. Zadani izgled preglednika je
siva mapa pod zasićenom toplinom; boja služi da se pronađe put na skeniranoj stazi, gdje
sama geometrija ne odvaja put od ivice, i prikazuje se iza prekidača preglednika *Snimljena
boja* u njegovom panelu Pozadina / nivo. Atlas bi pomnožio veličinu datoteke i trebao bi odmotavanje,
za pogled koji namjerno nije zadan. Blender i drugi glTF alati čitaju `COLOR_0`.
