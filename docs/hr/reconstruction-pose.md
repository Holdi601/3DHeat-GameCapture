---
title: "Položaj kamere i mjerilo"
nav_order: 4
lang: "hr"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Položaj kamere i mjerilo {#camera-pose-and-scale}

Karta dubine kaže koliko su stvari udaljene od *jednog* gledišta. Pretvaranje mnogih takvih
u jednu razinu traži da se zna gdje je bilo svako gledište i u kojim jedinicama. Ova stranica
pokriva žive putove; izvanmrežno rješavanje iz cijele snimke je na [Izvanmrežna rekonstrukcija](reconstruction-offline.md).

Kod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamere {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` gradi rupnu kameru iz **vodoravnog vidnog polja**
koje postavite u prozoru: `fx = (width / 2) / tan(fov / 2)`, kvadratni pikseli (`fy = fx`),
glavna točka u središtu kadra. Igra ne objavljuje svoju projekciju, pa je ovo jedini
pretpostavljeni broj: preuzak i scena izgleda dublja nego što jest. Izvanmrežni put koristi
65 stupnjeva.

`Pose` se pohranjuje kao **svijet-iz-kamere**: `rotation` (3 x 3) i `translation` = središte
kamere u svijetu, što žele putanja, karta pokrivenosti i prekrivanje.

## Vizualna odometrija (zadano) {#visual-odometry-the-default}

`VisualOdometry` prati svaki ključni kadar u odnosu na prethodni:

1. **Značajke**: ORB, do 1500 po kadru, otkrivaju se samo na masci svijeta (vidi
   [Snimanje](reconstruction-capture.md#what-is-not-the-world)).
2. **Podudaranja** s prethodnim ključnim kadrom: sila, Hammingova udaljenost, unakrsno
   provjerena (samo uzajamno najbolji parovi).
3. **Podizanje u 3D**: dubina prethodnog kadra već je u svjetskim jedinicama, pa njegovi
   podudarni pikseli postaju svjetske točke.
4. **Smještanje kamere**: `solvePnPRansac` među tim točkama (pogreška reprojekcije 3 px,
   pouzdanost 0,999, 200 iteracija). Translacija dolazi u istim jedinicama, pa **mjerilo
   prelazi preko razmaka**.
5. **Usidravanje dubine ovog kadra**: njegova vlastita predviđena inverzna dubina prilagođava
   se (`fit_scale`) na dubine unutarnjih točaka PnP-a, i ciklus se ponavlja.

**Prvi kadar** je ishodište: identitetski položaj, a njegov afin dubine je ili kalibracija
tla niže, ili bez nje identitet (rekonstrukcija je tada dosljedna sama sebi, ali bez jedinica).

Položaj treba najmanje **18 RANSAC unutarnjih točaka** - jasno više od minimuma PnP-a od šest,
jer je rješenje iz jedva dovoljno točaka upravo ono koje je samouvjereno pogrešno.

### Pouzdanost {#confidence}

Svaki smješteni kadar dobiva pouzdanost od 0 do 1 koja važi njegovo spajanje i pokrivenost:

| Položaj iz | Pouzdanost |
|---|---|
| telemetrije | 1,0 |
| izravnog rješavanja | 0,85 |
| vizualnog praćenja | `inliers / matches x min(1, inliers / 60)` |

### Kad praćenje pukne {#when-tracking-breaks}

Kadar koji se ne može smjestiti prijavljuje se, nikad se ne pogađa: `no features in the frame (N
found)`, `too few matches to place the camera`, `could not relocalise`. Položaj se ne bilježi i
ništa se ne spaja. Nastaviti od zadnjeg položaja ili započeti novo ishodište stavilo bi sljedeću
dionicu razine na proizvoljni pomak - šav koji izgleda kao prava geometrija.

Nakon prekida, svaki novi kadar se **ponovno lokalizira** prema bazi prošlih ključnih kadrova
(svaki četvrti praćeni kadar se dodaje, do 120, najstariji se odbacuje), od najnovijeg prema
starijem, istim korakom podudaranja i PnP-a. Dok jedan ne uspije, kadrovi se odbacuju. Ponovno
lokalizirani kadar nastavlja u istom koordinatnom sustavu. Oporavci se broje i prikazuju u
prozoru (`N recovered`).

### Zatvaranje petlje: isključeno {#loop-closure-off}

Ista baza podržava zatvaranje petlje: usporedba s ključnim kadrovima iz daleke prošlosti kako
bi se prepoznao povratak i vratila staza na njega. **Isključeno je po zadanom, a skener je
nikad ne uključuje** (`Reconstructor(loop_closure=False)`). Na ponavljajućem prizoru - etapa
rallyja, hodnik, red drveća - svaka dionica izgleda kao svaka druga, a podudaranje značajki
potvrđuje lažne povratke, što prikuje kameru blizu mjesta gdje je počela dok ona vozi dalje.
Ispravno to traži prepoznavanje mjesta (vokabular vreće riječi ili naučeni deskriptor) i
geometrijsku provjeru prema karti, a to nije izgrađeno.

Kad se uključi iz koda, zatvaranje treba: ključni kadar najmanje 60 ključnih kadrova star,
unutar 6 m od trenutnog položaja, podudaran s najmanje 90 unutarnjih točaka, koji pomiče
položaj za više od 0,02 m i manje od 6 m. Čak i tada samo zamjenjuje trenutni položaj; nije
graf položaja i ne pomiče ranije kadrove ni spojenu geometriju.

## Položaji iz telemetrije {#telemetry-poses}

Uz **Racing telemetry (Forza) -> Listen for position data** uključeno, putanja kamere dolazi
iz Forzina Data Out umjesto iz slika (`ForzaPoseSource`):

- Nit sluša na `127.0.0.1:<port>` (zadano 5300) s istim otkrivanjem rasporeda kao snimači
  ([Forza](telemetry-forza.md)); paketi se koriste dok je postavljeno `isRaceOn`. Zauzeti port
  se prijavljuje, ne podiže kao iznimka: telemetrija je nadogradnja, a skeniranje nastavlja
  vizualno.
- Svaki paket dobiva oznaku **monotonog vremena u kojem je stigao** - isti sat kojim kamera
  označava kadrove. Vlastita vremenska oznaka igre broji od nečeg nepovezanog, pa se ne koristi
  za poravnanje. Drhtanje petlje od jedne ili dvije milisekunde je oko 6 cm pri 200 km/h.
- Čuva se klizni međuspremnik od 30 sekundi. Položaj kadra **interpolira** se iz uzoraka s
  obje strane njegova vremena snimanja: položaj linearno, rotacija sfernom interpolacijom
  (zamućena matrica nije rotacija i iskrivila bi svaku točku). Preko praznine dulje od **0,35 s**,
  ili izvan međuspremnika, nema položaja.
- `pose_from_forza`: kamera se postavlja na automobil (pomak chase kamere nije objavljen).
  **Položaji se zadržavaju točno kako ih igra šalje**: Forzin svijet je već y-gore (x i z preko
  karte, y visina), što je isto kako datoteke krugova i datoteke rute zapisuju, pa površina
  sjeda na iste koordinate kao krugovi snimljeni preko nje. (Ranija verzija je zamijenila y i z
  za svijet „Z gore” i položila stazu na bok.)
- Rotacija je yaw, pa pitch, pa roll, sa smjerovima očitanim iz snimljenih krugova: smjer
  vožnje `atan2(dx, dz)` jednak je yawu, nagib uspona jednak je minus pitchu (pozitivno je nos
  prema dolje), a roll je pozitivan kad je desni ovjes sabijen (pozitivno spušta desnu stranu).
  Osi automobila (x desno, y gore, z naprijed) zatim se pretvaraju u osi kamere (x desno, y
  dolje, z naprijed) okretanjem y.
- Forzin svijet je **lijevo orijentiran**, a okvir kamere nije, pa je dobivena matrica
  svijet-iz-kamere zrcaljenje (determinanta -1), i skeniranje ispada lijevo orijentirano kao
  datoteke krugova. Interpolacija nije pogođena (zaokret između dvaju takvih položaja je prava
  rotacija).
- Kad kadar nema položaj iz telemetrije (praznina), rekonstruktor se za taj kadar vraća na
  **vizualno praćenje**, nastavljajući od zadnjeg položaja iz telemetrije, a čim feed opet
  odgovara vraća se na njegove položaje. PnP vraća samo rotacije, pa se u zrcaljenom svijetu
  rješava sa svijetom zrcaljenim kroz z, a zrcaljenje se vraća natrag; kadar tako sjeda u
  koordinate igre. Tek ako ni vizualno praćenje ne uspije, kadar je nepraćen.

### Mjerilo dubine iz telemetrije {#depth-scale-from-telemetry}

Igra kaže gdje je kamera, ne koliko je išta daleko, pa se dubina svakog kadra i dalje mora
usidriti - ali ne lancem od nultog kadra, čija je jedinica proizvoljna, dok su položaji u
metrima. Umjesto toga, značajke podudarene između prethodnog i tekućeg kadra (najmanje 8) se
**trianguliraju izravno iz dvaju poznatih položaja**, u metrima, a karta dubine se prilagođava
točkama ispred kamere. Svaki kadar se usidrava prema telemetriji, pa nema lanca koji bi
odlutao.

Ako su dva položaja bliža od **0,05 m**, zrake su gotovo paralelne i triangulacija je šum, pa
se kadar ne usidri: položaj je točan, ali se ne spaja ("positioned, but its depth has no scale
yet"). Zato prozor broji *smještene* i *spojene* kadrove posebno.

## Mjerilo {#scale}

Vizualna odometrija ispravno lančano prenosi relativno mjerilo, ali cijela razina lebdi na
jednom nepoznatom faktoru. Relativni izlaz Depth Anything-a dolazi u proizvoljnim jedinicama,
pa ostavljanje prvog kadra kao identiteta stavlja svijet na nekoliko metara od kamere u
proizvoljnoj veličini.

`GroundCalibrator` učvršćuje taj faktor prema **tome koliko je kamera visoko iznad tla**, mjereno
na **prvom ključnom kadru**, a kad on nema upotrebljivo tlo, na sljedećima:

- Visina kamere: **1,15 m** (linija očiju vozača) - prozor to uvijek koristi; skripte mogu
  zadati 1,70 m (`WALKING_HEIGHT`, stojeći igrač) ili `None` (bez kalibracije).
- Uzorak tla: redovi 62-92 % od vrha kadra (ispod horizonta, iznad haube ili oružja) i stupci
  30-70 % preko kadra (dalje od rubova).
- Svaki piksel tamo s upotrebljivom predikcijom podiže se s dubinom `1 / predicted` u jedinicama
  mreže; točke ispod optičke osi daju visinu ispod kamere. Njihov medijan je visina kamere u
  jedinicama mreže, pa je `metara po jedinici = 1,15 / medijan`, a afin kadra je
  `scale = 1 / metres_per_unit`, pomak 0.
- Vjeruje se samo s najmanje 200 uzoraka tla i **raspršenjem** (medijanska apsolutna
  devijacija podijeljena medijanom) ispod **0,60**.
- Na prvom ključnom kadru prilagodba postaje jedinica ishodišta, pa je skeniranje u metrima od
  početka. Kad prvi ključni kadar nema upotrebljivog tla, skeniranje počinje bez jedinica, a
  svaki sljedeći praćeni ključni kadar se pokušava, do **30 kadrova** ukupno. Prva koja se
  kalibrira daje *metara po jedinici*: medijan, preko pojasa tla, dubine koju tlo implicira
  podijeljene s dubinom koju je lanac dao tom kadru. Sve već spojeno je u jedinici prvog kadra,
  pa se faktor ne vraća u lanac; primjenjuje se na cijelu razinu (i na označena mjesta) kad se
  zapisuje, i na prikazanu udaljenost u međuvremenu. Veličina voksela je tada u jedinicama
  prvog kadra, pa se njezina veličina u metrima razlikuje od postavke za taj faktor.
- Nakon 30 kadrova bez tla skeniranje ostaje bez jedinica, i to kaže.
- S telemetrijom se kasniji ključni kadrovi ne pokušavaju: dubina je usidrena na metre
  telemetrije.

Biti unutar deset posto prave veličine bolje je nego biti krivi za faktor tisuću; telemetrija,
gdje je dostupna, to čini nepotrebnim. Napomena se prikazuje u prozoru ispod retka praćenja,
kao `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames
tried)`, `scaled from a 1.15 m camera height, ...` (uz `found on frame N, so the level is scaled
by F when it is written` kad je došlo kasnije), `no usable ground in the first N frames - sizes
are relative, not metres`, ili `in metres, from the telemetry's positions`.

## Prilagodba snopa i dugi tragovi (nisu povezani) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dva dijela postoje za budući prozorski rješavač i **skener ih ne koristi**:

- **`FeatureTracks`** čuva identitet značajki kroz stotine kadrova praćenjem Lucas-Kanade
  (600 značajki, ponovno zasijavanje ispod 60 %, tolerancija unaprijed-unatrag 1 px, nove
  značajke 10 px od postojećih), što prilagodba snopa treba - podudaranje deskriptora između
  uzastopnih kadrova daje samo parove.
- **`bundle_adjust`** prilagođava prozor položaja i točaka zajedno pomoću
  `scipy.optimize.least_squares` (područje povjerenja, soft-L1 gubitak s mjerilom 2 px,
  eksplicitni uzorak rijetkosti Jacobijana, fiksne kamere vraćene točno). Isprobano protiv
  poznate istine u `tests/test_bundle.py`.

`WindowedOdometry` ih spaja (prozori od 12 ključnih kadrova, rješavanje svaka 3 ključna kadra,
prve dvije kamere fiksne, točke s pogreškom većom od 6 px odbačene, skokovi veći od 6 puta od
nedavnog koraka odbijeni). Njegov docstring bilježi da je na pravoj snimci **sažeo putanju i
bio mnogo sporiji** od praćenja od kadra do kadra, uz slobodu mjerila kao poznati uzrok i
treći uzrok koji nije utvrđen. Zato praćenje od kadra do kadra ostaje zadano; vjerojatno
rješenje koje kod navodi je pokretanje esencijalnom matricom iz dva pogleda uz bazu fiksiranu iz
kalibracije ravnine tla.
