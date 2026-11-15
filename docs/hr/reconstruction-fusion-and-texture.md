---
title: "Spajanje, pokrivenost i boja"
nav_order: 5
lang: "hr"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Spajanje, pokrivenost i boja {#fusion-coverage-and-colour}

Kod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Svaki smješteni ključni kadar ažurira dvije rijetke mreže odjednom: **volumen površine**, iz
kojeg nastaje mreža, i **mrežu pokrivenosti**, koja kaže koliko joj vjerovati i kamo se
vratiti. Obje se ažuriraju po ključnom kadru, a ne na kraju, jer je karta pokrivenosti ono
po čemu igrač usmjerava.

## Od dubine do točaka {#from-depth-to-points}

Za svaki ključni kadar čiji je položaj poznat **i** čija dubina ima mjerilo:

1. Koristi se svaki drugi piksel u svakom smjeru (`PIXEL_STRIDE = 2`; susjedni pikseli jedne
   površine nisu neovisna mjerenja).
2. Dubina se pretvara u metre afinom prilagodbom kadra.
3. Zadržava se samo između **0,35 m** (bliže je oružje, HUD, haube) i **60 m** (monokularna
   pogreška raste otprilike s kvadratom udaljenosti, pa su daleke točke šum oblikovan kao
   geometrija) i samo na pikselima svijeta iz maske.
4. Podiže se kroz model kamere i prenosi u svijet pomoću položaja.
5. Svaka točka nosi boju piksela.

Kadar koji je smješten, ali nema mjerilo dubine, broji se kao *smješten*, ali ne i *spojen*.

## Volumen površine {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voksel je „Surface detail” prozora.

### Ponderirana zauzetost, a ne TSDF {#weighted-occupancy-not-a-tsdf}

Predznačeno polje udaljenosti (TSDF) reže duž svakog zraka piksela i dobro određuje tanke
strukture i čist slobodan prostor, jer zna da je zraka prošla *kroz* prazan prostor. To znači
prolaziti zrakom za svaku od stotina milijuna piksela. Ovaj volumen umjesto toga zbraja
**ponderiranu zauzetost** po vokselu i pokreće marching cubes na izglađenom rezultatu: dovoljno
brzo da radi tijekom skeniranja, na računalu bez upotrebljive GPU-a, a izlaz je zatvorena
površina, a ne oblak točaka. Cijena: tanke strukture i slobodan prostor su lošiji nego što bi
dao TSDF.

### Ugrađivanje kadra {#integrating-a-frame}

- Točke se binarno smještaju u voksele (`floor(point / voxel)`).
- Svaki dotaknuti voksel dobiva `weight x sqrt(count / max_count)`, gdje je `count` koliko je
  točaka kadra palo u njega, a `weight = max(0.1, pouzdanost položaja)`. Drugi korijen: nakon
  nekog broja, više piksela iste površine iz istog mjesta prestaje biti dokaz; važenje
  pouzdanošću položaja sprječava da sumnjiv položaj pomakne površinu.
- Boja je tekući ponderirani prosjek po vokselu.

Mreža je **rijetka**: prolazak rutom dotakne mali dio svog okvira. Koordinate voksela pakiraju
se u jedan 64-bitni ključ (21 bit po osi, do ±1.048.575 voksela - pri 0,25 m otprilike ±262 km)
i traže se sortiranim nizom i binarnom pretragom, potpuno vektorizirano.

### Izvlačenje mreže {#extracting-the-mesh}

1. Vokseli s težinom ispod **0,35** se odbacuju (pojedinačne točke na rubovima siluete postale
   bi šiljci).
2. Težine se skaliraju **75. percentilom** kroz skeniranje i ograničavaju na 1.
3. Zauzeti prostor reže se na blokove od **64 voksela** po strani, svaki s **halo-om od 3
   voksela** podataka susjeda (bez njega bi se svaka granica bloka zatvorila u zid, a cesta bi
   izašla kao red kutija).
4. Polje svakog bloka izglađuje se Gaussovim filtrom (sigma 0,8 voksela) da se ukloni nabor
   koji ostavlja šum dubine.
5. **Prvi prolaz**: 99. percentil izglađenog polja, uzorkovan kroz sve blokove (najviše 2
   milijuna vrijednosti), postavlja jedno globalno mjerilo razine. Normiranje po bloku bi
   usamljeni izvanredni podatak promoviralo u punu površinu u njegovom praznom bloku.
6. **Drugi prolaz**: polje svakog bloka podijeljeno tim mjerilom, marching cubes na **0,5**.
   Trokut pripada bloku u kojem je njegovo **težište**, pa se trokuti koji prelaze šav emitiraju
   točno jednom.
7. Vrhovi se pomiču u svjetske jedinice na središtima voksela; svaki vrh dobiva boju svog
   voksela (srednje siva tamo gdje pada izvan zauzetog voksela).

Izvlačenje po blokovima omogućuje skeniranje veličine staze: jedno gusto polje preko kvadrata
od kilometar po strani pri 0,25 m bilo bi milijarde ćelija. `tests/test_track_scale.py`
osigurava da to radi na toj veličini uz memoriju razmjernu onome što je skenirano.

### Tlo i struktura {#ground-and-structure}

`classify` označava svaki trokut prema njegovoj normali (orijentiranoj prema normalama vrhova):
unutar **35 stupnjeva od ravno gore** je `ground`, sve ostalo `structure`. Preglednik crta tlo
punim, a strukture gotovo prozirnima. **Voda se nikad ne označava** - ne može se razlikovati od
ravnog tla po obliku, a pogrešna oznaka bi dvorište prikazala kao jezero. Svaka oznaka postaje
jedan dio `.glb` datoteke ([Izlaz .glb](glb-output.md)).

## Pokrivenost {#coverage}

`CoverageGrid(voxel=0.5)` bilježi, za svaku ćeliju od pola metra, četiri stvari koje nisu iste:

| Pojam | Pohranjeno | Ocjena (svaka ograničena na 0..1) | Zašto se broji zasebno |
|---|---|---|---|
| Koliko puta viđeno | broj ključnih kadrova koji su vidjeli ćeliju | `count / 3` | jednom je samo nagađanje, nema s čime usporediti |
| Iz koliko smjerova | zbroj jediničnih smjerova gledanja | `(1 - spread) / (1 - 0,93)`, gdje je spread = duljina zbroja / broj | dvadeset kadrova koji idu ravno prema zidu nemaju paralaksu među sobom; dva pogleda pod trideset stupnjeva vrijede više |
| Iz koje daljine | najbliža udaljenost gledanja | `1 - nearest / 40 m` | pogreška dubine raste otprilike s kvadratom udaljenosti |
| Koliko je dobro kamera smještena | najbolja pouzdanost položaja | sama pouzdanost | geometrija spojena s upitnim položajem završi na krivom mjestu |

Točke kadra prvo se grupiraju po ćeliji, pa deset tisuća piksela jednog zida broji kao jedno
opažanje iz jednog smjera.

**Kvaliteta = umnožak četiri pojma**, a ne prosjek: to su uvjeti koji moraju vrijediti
istodobno. Mjesto viđeno dvjesto puta iz jednog smjera na šezdeset metara loše je promatrano, a
prosjek bi to sakrio iza jednog odličnog pojma.

Glavne brojke (`summary`): zauzete ćelije, udio s kvalitetom najmanje 0,5 (postotak „well
seen” u prozoru), prosječna kvaliteta i volumen.

### Slabe točke {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. ćelije s kvalitetom ispod 0,35 su slabe;
2. slabe ćelije grupiraju se po **povezanosti** (26-susjedstvo, union-find samo nad zauzetim
   ćelijama - ne rasterom preko okvira, koji je na dugoj vožnji milijune praznih ćelija);
3. grupe s manje od 8 ćelija se zanemaruju;
4. razlog svake grupe je najčešći *najslabiji pojam* njezinih ćelija, a njezin položaj
   srednja vrijednost njezinih ćelija;
5. poredano od najveće prema najmanjoj (zatim po najgoroj kvaliteti), najviše 8.

| Razlog | Prikazani savjet |
|---|---|
| few views | Viđeno samo jednom ili dvaput - prođite ponovno pokraj toga. |
| one direction | Viđeno samo iz jednog kuta. Odmaknite se u stranu i pogledajte ponovno. |
| distant | Viđeno samo izdaleka. Približite se tome. |
| poor tracking | Kamera ovdje nije dobro smještena. Približavajte se sporije. |

Povezanost je važna: grupiranje po fiksnoj mreži blokova prijavi jednu zanemarenu sporednu
sobu kao mnogo odvojenih prstenova, a nitko ne može razlikovati osam mjesta od jednog mjesta
koje je brojeno osam puta.

### Plan {#the-plan-view}

`top_down(resolution)` projicira ćelije na x/z i zadržava **najbolju** kvalitetu po stupcu
(netko stojeći u sobi ima lošu pokrivenost stropa i odličnu pokrivenost poda; prosjek bi
sobu obojio jantarno). Nikad viđeni stupci se označavaju posebno. Prozor crta to na 200 x 200,
prekrivanje na 120 x 120 ([Prozor skeniranja](reconstruction-scan-ui.md#the-coverage-map)).

### Je li ovo rekonstruktibilno? {#is-this-reconstructable}

Svakih 25 spojenih kadrova, kad ima najmanje 500 ćelija:

| Nalaz | Presuda | Poruka (skraćeno) |
|---|---|---|
| manje od 2 % ćelija ima raspon gledanja ispod 0,93 | nije rekonstruktibilno | Gotovo nema paralakse. Ili kamera nikad ne gleda postrance, ili praćenje odlazi, pa se ista površina nikad ne pojavljuje dvaput na istom mjestu. Provjerite broj smještenih kadrova: ako je visok, riječ je o driftu. |
| medijan najbliže udaljenosti veći od 25 m | nije rekonstruktibilno | Sve je viđeno s N m ili dalje ... Približite se onome što želite. |
| manje od 6 % s dobrim rasponom | rekonstruktibilno, s upozorenjem | Tanka paralaksa - geometrija će biti gruba. Najviše pomaže kretanje postrance u odnosu na ono što gledate. |

Niska paralaksa ima dva uzroka koje ovo ne može razlikovati, zato poruka navodi oba.

## Boja {#colour}

Boja po vokselu u spajanju je jeftina i uživo, i mutna: svaki piksel u ćeliji od četvrtine
metra se prosječi, uključujući one viđene postrance s trideset metara. Zato se pri izvozu mreža
ponovno boji, jednom, iz samih kadrova:

- **Zadržani kadrovi**: do **160** ključnih kadrova (slika i položaj), odabranih
  rezervoarskim uzorkovanjem tako da su raspršeni po cijelom skeniranju, a ne samo po njegovu
  kraju.
- **Po vrhu** (`project_colours`), svaki zadržani kadar doprinosi ako je vrh ispred kamere i
  unutar slike, površina je okrenuta najviše oko 70 stupnjeva od izravnog gledanja u kameru
  (`|normal . view| > 0.34`), bliži je od **35 m**, i ništa bliže nije stajalo ispred njega
  (niže).
- Svaki takav pogled ocjenjuje se kao `facing x (1 - distance / 35)`, pa blizak pogled izravno
  nadjačava daleki kosi. **4 najbolje ocijenjena** pogleda svakog vrha zadržavaju se - bez
  obzira na redoslijed kadrova, bolji pogled zamjenjuje najslabiji od četiri - i miješaju se,
  ponderirano istom ocjenom.
- **Zaklanjanje**: u svakom kadru vrhovi same mreže koji su u pogledu crtaju se u međuspremnik
  dubine s ćelijama od 2 piksela, zadržavajući najbliži po ćeliji. Vrh koji je više od `0,3 m +
  5 %` svoje udaljenosti iza najbližeg u svojoj ćeliji bio je skriven u tom kadru - zid između
  kamere i ceste iza njega - pa taj pogled ne vrijedi ništa. Test zna samo za mrežu: zaklanjač
  koji nikad nije spojen (automobil u prolazu, stup kabine izvan maske HUD-a) se ne hvata.
- Vrh koji nijedan kadar nije vidio zadržava boju svog voksela; vrh bez oboje je srednje siv
  (crno bi se čitalo kao rupa).

Boja se zapisuje kao `COLOR_0` po vrhu, a ne kao atlas tekstura. Zadani izgled preglednika je
siva karta pod zasićenom toplinom; boja služi da se pronađe cesta na skeniranoj stazi, gdje
sama geometrija ne razdvaja cestu od ruba, a prikazuje se iza prekidača *Captured colour*
preglednika u njegovu panelu Pozadina / razina. Atlas bi umnožio veličinu datoteke i trebao bi
raspakiravač, za prikaz koji namjerno nije zadani. Blender i drugi glTF alati čitaju `COLOR_0`.
