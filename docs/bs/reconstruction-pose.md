---
title: "Poza kamere i skala"
nav_order: 4
lang: "bs"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poza kamere i skala {#camera-pose-and-scale}

Mapa dubine kaže koliko su stvari daleko od *jedne* tačke gledišta. Da bi se mnoge od njih pretvorile u jedan nivo,
treba znati gdje je bila svaka tačka gledišta i u kojim jedinicama. Ova stranica pokriva putanje uživo;
offline feed-forward rješavanje je na [Offline rekonstrukcija](reconstruction-offline.md).

Kod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamere {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` gradi pinhole kameru iz **horizontalnog vidnog
polja** koje postavite u prozoru: `fx = (width / 2) / tan(fov / 2)`, kvadratni pikseli (`fy = fx`),
glavna tačka u centru kadra. Igra ne objavljuje svoju projekciju, pa je ovo
jedan pretpostavljeni broj: preusko i scena izgleda dublja nego što jeste. Offline putanja koristi
65 stepeni.

`Pose` se pohranjuje kao **svijet-iz-kamere**: `rotation` (3 x 3) i `translation` = centar kamere
u svijetu, što traže putanja, mapa pokrivenosti i overlay.

## Vizualna odometrija (zadano) {#visual-odometry-the-default}

`VisualOdometry` prati svaki ključni kadar u odnosu na prethodni:

1. **Karakteristike**: ORB, do 1500 po kadru, otkrivene samo na masci svijeta (pogledajte
   [Snimanje](reconstruction-capture.md#what-is-not-the-world)).
2. **Poklapanja** s prethodnim ključnim kadrom: grubom silom, Hammingova udaljenost, unakrsno provjerena (samo
   uzajamno najbolji parovi).
3. **Podizanje u 3D**: dubina prethodnog kadra je već u svjetskim jedinicama, pa njegovi poklopljeni pikseli
   postaju svjetske tačke.
4. **Postavljanje kamere**: `solvePnPRansac` među tim tačkama (greška reprojekcije 3 px,
   pouzdanost 0,999, 200 iteracija). Translacija izlazi u istim jedinicama, pa
   **skala prelazi jaz**.
5. **Sidrenje dubine ovog kadra**: njegova vlastita predviđena inverzna dubina se podešava (`fit_scale`)
   prema dubinama PnP unutrašnjih tačaka, i ciklus se ponavlja.

**Prvi kadar** je ishodište: jedinična poza, a afina transformacija njegove dubine je ili kalibracija
tla ispod ili, bez nje, identitet (rekonstrukcija je tada sama sa sobom usklađena,
ali bez jedinica).

Poza treba najmanje **18 RANSAC unutrašnjih tačaka** - jasno više od PnP-ovog minimuma od šest, jer je
rješenje iz jedva dovoljno tačaka upravo ono koje je sigurno pogrešno.

### Pouzdanost {#confidence}

Svaki postavljeni kadar dobija pouzdanost u rasponu 0..1 koja ponderiše njegovu fuziju i pokrivenost:

| Poza iz | Pouzdanost |
|---|---|
| telemetrije | 1,0 |
| feed-forward rješenja | 0,85 |
| vizualnog praćenja | `inliers / matches x min(1, inliers / 60)` |

### Kada praćenje pukne {#when-tracking-breaks}

Kadar koji se ne može postaviti prijavljuje se, nikad ne pogađa: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Nikakva poza se ne bilježi,
i ništa se ne spaja. Nastavak od posljednje poze, ili početak novog ishodišta, postavio bi
sljedeći dio nivoa na proizvoljan pomak - šav koji izgleda kao prava geometrija.

Nakon prekida, svaki novi kadar se **relokalizira** prema bazi prošlih ključnih kadrova (svaki
4. praćeni kadar se dodaje, do 120, najstariji se izbacuje), najnoviji prvi, istim korakom
poklapanja i PnP-a. Dok jedan ne uspije, kadrovi se odbacuju. Oporavljeni kadar nastavlja u istom
koordinatnom okviru. Oporavci se broje i prikazuju u prozoru (`N recovered`).

### Zatvaranje petlje: isključeno {#loop-closure-off}

Ista baza podržava zatvaranje petlje: poklapanje s mnogo ranijim ključnim kadrovima da bi se
otkrio ponovni posjet i putanja vratila na njega. **Isključeno je zadano, a skener ga nikad
ne uključuje** (`Reconstructor(loop_closure=False)`). Na ponavljajućem okruženju - reli dionica,
hodnik, red drveća - svaki dio izgleda kao svaki drugi i poklapanje karakteristika potvrđuje
lažne ponovne posjete, što prikuje kameru blizu mjesta gdje je počela dok vozi dalje. Pravilno
izvođenje traži prepoznavanje mjesta (rječnik vreće riječi ili naučeni deskriptor) i
geometrijsku provjeru prema mapi, što nije izgrađeno.

Kada se uključi iz koda, zatvaranje traži: ključni kadar star najmanje 60 ključnih kadrova, unutar 6 m od
trenutne poze, poklopljen s najmanje 90 unutrašnjih tačaka, koji pomjera pozu za više od 0,02 m i
manje od 6 m. Čak i tada samo zamjenjuje trenutnu pozu; nije graf poza i ne pomjera
ranije kadrove niti spojenu geometriju.

## Telemetrijske poze {#telemetry-poses}

Kada je uključeno **Racing telemetry (Forza) -> Listen for position data**, putanja kamere dolazi iz
Forzinog Data Out umjesto iz slika (`ForzaPoseSource`):

- Nit sluša na `127.0.0.1:<port>` (zadano 5300) s istom detekcijom rasporeda kao
  snimači ([Forza](telemetry-forza.md)); paketi se koriste dok je `isRaceOn` postavljen. Zauzeti port
  se prijavljuje, ne baca grešku: telemetrija je nadogradnja i skeniranje nastavlja vizualno.
- Svaki paket se označava **monotonim vremenom kada je stigao** - istim satom kojim snimanje
  označava kadrove. Igrina vlastita vremenska oznaka broji od nečeg nepovezanog, pa se
  ne koristi za poravnanje. Loopback jitter od milisekunde ili dvije je oko 6 cm pri 200 km/h.
- Čuva se klizni međuspremnik od 30 sekundi. Poza kadra se **interpolira** iz uzoraka s obje
  strane trenutka snimanja: pozicija linearno, rotacija sfernom interpolacijom (pomiješana
  matrica nije rotacija i iskrivila bi svaku tačku). Preko praznine duže od **0,35 s**, ili
  izvan međuspremnika, nema poze.
- `pose_from_forza`: kamera se postavlja na automobil (pomak kamere za praćenje se ne objavljuje).
  **Pozicije se čuvaju tačno kako ih igra šalje**: Forzin svijet je već Y-gore (x i z
  preko mape, y visina), kako ga pišu datoteke krugova i datoteke ruta, pa
  površina sleti na iste koordinate kao krugovi snimljeni nad njom. (Ranija verzija je zamijenila
  y i z za "Z-gore" svijet i položila stazu na bok.)
- Rotacija je skretanje, pa nagib, pa valjanje, sa smislovima pročitanim iz snimljenih krugova:
  smjer kretanja `atan2(dx, dz)` jednak je skretanju, savladani uspon jednak je minus nagibu
  (pozitivno je nos dolje), a valjanje je pozitivno kada je desni ovjes stisnut
  (pozitivno spušta desnu stranu). Ose automobila (x desno, y gore, z naprijed) zatim se okreću u
  ose kamere (x desno, y dolje, z naprijed) obrtanjem y.
- Forzin svijet je **lijevoruk**, a okvir kamere nije, pa je rezultirajuća
  matrica svijet-iz-kamere refleksija (determinanta -1), i skeniranje izlazi lijevoruko
  kao datoteke krugova. Interpolacija nije pogođena (okret između dvije takve poze je prava
  rotacija).
- Kada kadar nema telemetrijsku pozu (praznina), rekonstruktor se vraća na **vizualno praćenje**
  za taj kadar, nastavljajući od posljednje telemetrijske poze, i vraća se na poze iz feeda čim
  odgovori. PnP vraća samo rotacije, pa se u zrcaljenom svijetu rješava sa
  svijetom zrcaljenim kroz z, a zrcalo se vraća nazad; kadar sleti u koordinate igre.
  Tek ako i vizualno praćenje zakaže, kadar je neprćen.

### Skala dubine iz telemetrije {#depth-scale-from-telemetry}

Igra kaže gdje je kamera, a ne koliko je šta daleko, pa dubina svakog kadra i dalje
traži sidrenje - ali ne lančanjem od nultog kadra, čija je jedinica proizvoljna dok su poze
u metrima. Umjesto toga, karakteristike poklopljene između prethodnog i trenutnog kadra (najmanje
8) **triangulišu se direktno iz dvije poznate poze**, u metrima, a mapa dubine se
podešava prema tačkama ispred kamere. Svaki kadar je usidren prema telemetriji, pa
nema lanca koji bi odlutao.

Ako su dvije poze udaljene manje od **0,05 m**, zrake su skoro paralelne i triangulacija je
šum, pa se kadar ostavlja neusidren: tačno pozicioniran, ali nespojen ("positioned, but its
depth has no scale yet"). Zato prozor odvojeno broji *postavljene* i *spojene* kadrove.

## Skala {#scale}

Vizualna odometrija ispravno lančano prenosi relativnu skalu, ali cijeli nivo i dalje lebdi na jednom nepoznatom
faktoru. Relativni izlaz Depth Anythinga izlazi u proizvoljnim jedinicama, pa ostavljanje prvog
kadra na identitetu postavlja svijet unutar metara od kamere u proizvoljnoj veličini.

`GroundCalibrator` fiksira taj faktor iz **visine kamere iznad tla**, izmjerene na
**prvom ključnom kadru** i, kada on nema upotrebljivo tlo, na sljedećim:

- Visina kamere: **1,15 m** (visina očiju vozača) - prozor uvijek koristi ovu; skripte mogu
  predati 1,70 m (`WALKING_HEIGHT`, igrač koji stoji) ili `None` (bez kalibracije).
- Uzorak tla: redovi 62-92% niz kadar (ispod horizonta, iznad haube ili oružja) i
  kolone 30-70% preko (dalje od bankina).
- Svaki piksel tu s upotrebljivim predviđanjem podiže se s dubinom `1 / predicted` u jedinicama
  mreže; tačke ispod optičke ose daju visinu ispod kamere. Njihov medijan je
  visina kamere u jedinicama mreže, pa je `metres per unit = 1.15 / median`, a afina transformacija kadra je
  `scale = 1 / metres_per_unit`, shift 0.
- Vjeruje se samo uz najmanje 200 uzoraka tla i **rasipanje** (medijan apsolutnog odstupanja
  podijeljen medijanom) ispod **0,60**.
- Na prvom ključnom kadru podešavanje postaje jedinica ishodišta, pa je skeniranje u metrima od
  početka. Kada prvi ključni kadar nema upotrebljivo tlo, skeniranje počinje bez jedinica, a svaki kasniji
  praćeni ključni kadar se pokušava, ukupno do **30 kadrova**. Prvi koji se kalibrira daje
  *metre po jedinici*: medijan, preko pojasa tla, dubine koju njegovo tlo implicira nad
  dubinom koju je lanac dao tom kadru. Sve već spojeno je u jedinici prvog kadra, pa se
  faktor ne vraća u lanac; primjenjuje se na cijeli nivo (i na označena
  mjesta) kad se zapisuje, i na udaljenost prikazanu u međuvremenu. Veličina voksela je tada u
  jedinicama prvog kadra, pa se njegova veličina u metrima razlikuje od postavke za taj faktor.
- Nakon 30 kadrova bez tla skeniranje ostaje bez jedinica, i to kaže.
- S telemetrijom se kasniji ključni kadrovi ne pokušavaju: dubina je usidrena na telemetrijske metre.

Biti unutar deset posto prave veličine bolje je nego biti pogrešan za faktor hiljadu; telemetrija,
gdje je dostupna, to čini nepotrebnim. Napomena se prikazuje u prozoru ispod linije praćenja,
kao `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (s `found on frame N, so the level is scaled
by F when it is written` kad je došlo kasnije), `no usable ground in the first N frames - sizes are
relative, not metres`, ili `in metres, from the telemetry's positions`.

## Podešavanje snopa i dugi tragovi (nije povezano) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dva dijela postoje za budući prozorski rješavač i **skener ih ne koristi**:

- **`FeatureTracks`** čuva identitet karakteristika kroz stotine kadrova Lucas-Kanade
  praćenjem (600 karakteristika, ponovo se sije ispod 60%, tolerancija naprijed-nazad 1 px, nove karakteristike 10 px
  od postojećih), što je ono što podešavanje snopa treba - poklapanje deskriptora između
  uzastopnih kadrova daje samo parove.
- **`bundle_adjust`** usavršava prozor poza i tačaka zajedno pomoću
  `scipy.optimize.least_squares` (trust region, soft-L1 gubitak sa skalom 2 px, eksplicitni
  obrazac rijetkosti Jakobijana, fiksne kamere tačno vraćene). Testirano prema poznatoj istini u
  `tests/test_bundle.py`.

`WindowedOdometry` ih kombinuje (prozori od 12 ključnih kadrova, rješavanje svaka 3 ključna kadra, prve dvije
kamere fiksne, tačke s greškom preko 6 px odbačene, skokovi preko 6 puta većeg od nedavnog koraka odbijeni). Njegov
docstring bilježi da je na stvarnom snimku **srušio putanju i bio mnogo sporiji** od
praćenja kadar po kadar, s kalibarskom slobodom (skala) i bootstrapom zasnovanim na dubini kao poznatim uzrocima i
trećim neidentifikovanim uzrokom. Zato kadar-po-kadar odometrija ostaje zadana; vjerovatni popravak zabilježen
u kodu je bootstrap esencijalne matrice iz dva pogleda s baznom linijom fiksiranom iz
kalibracije ravni tla.
