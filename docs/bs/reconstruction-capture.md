---
title: "Snimanje, maske i kvalitet kadrova"
nav_order: 2
lang: "bs"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Snimanje, maske i kvalitet kadrova {#capture-masks-and-frame-quality}

Kod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Odakle dolaze kadrovi {#where-frames-come-from}

Ciljni izvor je jedno od:

| Cilj | Izvor | Napomene |
|---|---|---|
| `monitor:<n>` | cijeli monitor, uživo | "Whole screen" u prozoru, s brojem u "Which" |
| `window:<title>` | jedan prozor, uživo | "A window" u prozoru, s njegovim naslovom |
| putanja datoteke | video datoteka | "A video file" u prozoru; bilo koji format koji OpenCV može čitati |

### Snimanje uživo: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` koristi paket `windows-capture`, koji omotava **Windows Graphics Capture** -
javni API koji koriste snimači ekrana. Ništa se ne ubacuje u igru. Kursor se ne
snima i ne crta se žuti okvir snimanja.

Biblioteka za snimanje isporučuje kadrove povratnom funkciji na niti kompozitora i očekuje da se ona
odmah vrati, pa povratna funkcija samo kopira kadar (međuspremnik se ponovo koristi), pretvara BGRA u
RGB, mijenja mu veličinu, označava ga vremenom i stavlja u red od **4 kadra**. Kada je red pun,
**najstariji kadar se odbacuje** i brojač raste: zaostajanje treba koštati kadrove, ne
memoriju ni ispravnost, a prikaz uživo treba pokazivati gdje je igrač sada. Odbačeni kadrovi
prikazuju se u statistici prozora, a ako je odbačeno više od polovine, javlja se savjet.

Svaki kadar nosi `t` (sekunde od početka snimanja) i `monotonic` (sirovo
`time.monotonic()` pri snimanju), isti sat kojim se označavaju i telemetrijski paketi - što
omogućava da se Forza poze poravnaju s kadrovima.

`windows-capture` je opcionalan u provjeri zavisnosti: bez njega se video datoteka i dalje
može skenirati.

### Video datoteke {#video-files}

`VideoSource` čita preko OpenCV-a, pretvara u RGB i mijenja veličinu. Kontejner bez brzine kadrova
tretira se kao 30 fps. Vremenske oznake su indeks kadra podijeljen brzinom kadrova; datoteka nema
stvarno vrijeme, pa se telemetrija ne može poravnati s videom.

### Rezolucija {#resolution}

Kadrovima se veličina mijenja na izvoru tako da je najduža stranica snimajuća stranica postavke (Draft 640,
Balanced 960, Detailed 1280 px), s interpolacijom po površini. 4K kadar ima trideset puta više piksela
nego što model dubine koristi.

## Ključni kadrovi {#keyframes}

Gotovo svaki kadar snimka je suvišan: stajanje u mjestu daje stotine pogleda na jednu
stvar. Rekonstrukcija želi *paralaksu*. Zato se kadar zadržava prema **tome koliko se slika
promijenila od posljednjeg zadržanog kadra**, a ne prema satu.

`picture_change(a, b)`:

1. oba kadra u sivo i smanjena na mrežu 16 x 16 srednjih vrijednosti blokova (srednje vrijednosti blokova reaguju na
   pomicanje slike, ne na zrno, lišće, treperenje ili HUD);
2. srednja apsolutna razlika, kao dio od 255;
3. kada je poznata maska svijeta, svaki blok se ponderiše udjelom koji je svijet, a ne
   kokpit, pa blok s pola instrument-table računa pola (koristi se kada maska pokriva više od 5%
   težine mreže).

Prag se **prilagođava snimanju**: prvih 30 kadrova je početna vrijednost postavke
(0,020 / 0,010 / 0,004), a zatim je kvantil postavke (0,85 / 0,65 / 0,40) posljednjih
240 izmjerenih promjena, nikad ispod 0,0001. Kadar se zadržava kada njegova promjena dostigne
prag; prvi kadar se uvijek zadržava. Fiksni prag ne može raditi kroz različite scene -
promjena od kadra do kadra tamnog kruga iz kokpita mali je dio one u svijetloj teksturiranoj sobi -
dok "zadrži najživlju trećinu" znači isto u obje. Prag u upotrebi šalje se uz
svako ažuriranje napretka (`ScanProgress.threshold`), a trake brzine hoda u prozoru i na
overlayu mjere posljednju promjenu prema njemu (`ScanProgress.toward_next_view`).

Samo zadržani kadrovi prolaze kroz model dubine i rekonstrukciju. Kadrovi se ne pohranjuju
osim ako pozivalac to ne zatraži (`keep_frames`); 160 njih se zadržava za bojenje mreže (pogledajte
[boja](reconstruction-fusion-and-texture.md#colour)).

Skeniranje se završava kada se zaustavi, kada video ponestane, ili na granici vremena ili ključnih kadrova.

## Šta nije svijet {#what-is-not-the-world}

Dvije stvari u kadru igre nisu geometrija nivoa, a obje uništavaju rekonstrukciju:

- **HUD.** Nišan je najponovljivija karakteristika u svakom kadru. Uparivač karakteristika
  ga voli, savršeno se poklapa između svakog para kadrova, a svako poklapanje je dokaz
  da se kamera nije pomakla - što sabija cijelu rekonstrukciju.
- **Stvari pričvršćene za kameru.** Oružje, hauba, okvir kokpita, instrument-tabla. Prava
  geometrija u pogrešnom koordinatnom sistemu: spojena, razmaže se duž cijele pređene putanje.

Dva detektora ih pronalaze. Oba daju masku (255 = svijet, 0 = nije svijet) ili `None` dok
nema dovoljno dokaza, a `None` uvijek znači "koristi sve", nikad "ne koristi ništa".

Maska se primjenjuje:

- pri **detekciji karakteristika** u vizualnoj odometriji (maskiranje nišana iz izlaza
  dok mu se dozvoljava da glasa o pozi ispravilo bi vidljiv simptom, a zadržalo štetni);
- na **spojene piksele**, da se ne spaja geometrija kokpita;
- na mjeru **oštrine i svjetline**, jer je kokpit uvijek savršeno oštar;
- na **promjenu slike** koja odlučuje o ključnim kadrovima.

**Ne** primjenjuje se na kadrove predate offline VGGT rješavaču (pogledajte
[Offline rekonstrukcija](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: ono što se ne mijenja {#screenmask-what-does-not-change}

Koristi se od prvog ključnog kadra dok FlowMask ne bude spreman.

- Svaki kadar se pretvara u sivo, prepolovljuje i zamućuje (Gaussov 3 x 3) tako da jednopikselno podrhtavanje
  statičnog HUD elementa ne izgleda kao kretanje.
- Apsolutna razlika po pikselu u odnosu na prethodni kadar ugrađuje se u eksponencijalni
  prosjek (opadanje 0,9), pa maska prati HUD koji se pojavi ili nestane usred skeniranja.
- Uči samo iz kadrova u kojima se zna da se kamera kreće (u skeniranju: čim je najmanje jedan
  kadar praćen) - parkirana kamera čini sve statičnim.
- Nakon **12** kadrova učenja piksel je statičan kada je njegova prosječna promjena ispod **0,22**
  medijane promjene kadra - relativno, pa prag prati koliko brzo igrač
  ide.
- Ako se više od **45%** kadra čita kao statično, pretpostavka je pala (meni, scena
  bez igre) i ništa se ne maskira.
- Maska se erodira za jedan piksel (zaglađene ivice HUD-a ne pripadaju nijednoj strani) i vraća na
  punu veličinu.

Njena napomena u prozoru: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, ili `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: ono što nikad ne putuje {#flowmask-what-never-travels}

Kokpit nije statičan: kazaljke se pomiču, brojač obrtaja podrhtava, mini-mapa se okreće, pa
detektor promjene te piksele proglašava svijetom - a oni su najgore karakteristike za davanje rješavaču poze.
FlowMask postavlja bolje pitanje: **koje karakteristike ostaju a ne putuju?**

- U skeniranju uživo uči jednom, iz prvih **40 ključnih kadrova** (sivi tonovi); zatim zamjenjuje
  ScreenMask do kraja skeniranja.
- Kadrovi se režu na prozore od **30** kadrova, s preklapanjem od pola. U svakom prozoru se postavlja do
  800 uglova (`goodFeaturesToTrack`, kvalitet 0,01, razmak 8 px) i prate se
  piramidalnim Lucas-Kanadeom (21 x 21, 4 nivoa) s **provjerom naprijed-nazad**: trag čiji
  povratni tok ne sleti unutar 1 px od mjesta početka se odbacuje, jer bi pratilac koji
  odluta na susjedni uzorak proizveo upravo onaj potpis "postojan ali nepomičan"
  koji se traži. Prozori kraći od 20 kadrova se preskaču. Kratki prozori su bitni:
  tokom duge vožnje skoro svaka karakteristika svijeta napusti kadar i dokazi se razrijede do ničega.
- Neto put svake preživjele karakteristike poredi se s **2% širine kadra**: ispod toga je
  "zaglavljena"; iznad, "pokretna". Brojevi se skupljaju na mreži **24 x 24** ćelija ekrana prema tome
  gdje je svaka karakteristika počela.
- Ćelija je blokirana kada drži najmanje 2 zaglavljene karakteristike i više zaglavljenih nego pokretnih,
  **i** najmanje 3 od njenih 8 susjeda su također blokirana (usamljena ćelija je šum; tamni snimak
  daje ih mnogo).
- Zadržavaju se samo blokirane oblasti **povezane s rubom kadra**. Sve što je pričvršćeno za
  kameru dosegne rub ekrana; ono što je u sredini i ne putuje je
  tačka nestajanja - vozeći naprijed, put ravno ispred nema tok i to je
  geometrija koja je najpotrebnija.
- Preživjela oblast se proširuje za jednu ćeliju (rub instrument-table je gradijent).
- Ako bi se maskiralo više od **60%** kadra, ništa se ne maskira: na noćnom snimku većina
  ćelija ne drži praćenu karakteristiku, što se čita isto kao brojčanik.

Njena napomena: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame —
it never travels`, ili, preko 60%, poruka koja objašnjava da ne maskira ništa.

Offline putanja uči isti FlowMask iz 4 niza od po 90 uzastopnih kadrova raspoređenih kroz
video, na 960 x 540 ([Offline](reconstruction-offline.md)).

## Kvalitet kadrova i savjeti {#frame-quality-and-advice}

`QualityWatcher` ocjenjuje svaki ključni kadar i bira **jednu** uputu, tako da overlay može reći
"uspori" dok još ima vremena.

Po kadru mjeri, samo na pikselima svijeta (svi pikseli ako maska ostavlja manje od 5%):

- **oštrinu**: varijansa Laplasijana - standardna jednoprolazna mjera, koja reaguje na
  upravo ono što zamućenje pokreta uništava;
- **osvijetljenost**: srednji nivo sive, 0-255.

Oštrina nema apsolutnu skalu (noćna dionica i svijetla ulica razlikuju se za red
veličine, a obje su u fokusu), pa se ocjenjuje prema **tekućem medijanu ovog snimanja**:
posljednjih 90 kadrova, a potrebno ih je 20 prije bilo kakve ocjene. Svaki kadar se poredi s istorijom
*prije* nego što se doda, pa dugo zamućeno razdoblje ne može povući medijan dolje da mu se izjednači.

| Stanje | Test |
|---|---|
| ravno | oštrina najviše 1,0 (ekran učitavanja, zid, nebo) |
| tamno | osvijetljenost ispod 26 |
| zamućeno | oštrina ispod 0,55 medijana, i nije ravno |

Savjet, prvo poklapanje pobjeđuje (poredano prema tome šta skeniranje najviše blokira):

| Situacija | Savjet | Nivo |
|---|---|---|
| manje od 20 kadrova | Getting a feel for the picture… | ok |
| ravno | Nothing to measure — point the camera at the level, not at the sky. | stop |
| tamno | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| zamućeno | Blurred — slow down. | warn |
| praćeno manje od pola kadrova | Losing track — slow down and keep more of the level in view. | warn |
| spojeno manje od 40% praćenih kadrova | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| postoje slabe tačke | N thin spots — the map marks them. | ok |
| inače | Good — keep going. | ok |

Nivo boji savjet na overlayu (zeleno / žuto / crveno). Traka **sharpness** na overlayu
je oštrina kadra u odnosu na medijan. (Kod ima i "Blurred, and the camera is
not moving. Check the capture." za nepomičnu kameru; skeniranje uvijek javlja da se kamera
kreće, pa se ne prikazuje.)
