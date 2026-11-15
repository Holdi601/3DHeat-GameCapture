---
title: "Snimanje, maske i kvaliteta kadrova"
nav_order: 2
lang: "hr"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Snimanje, maske i kvaliteta kadrova {#capture-masks-and-frame-quality}

Kod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Odakle dolaze kadrovi {#where-frames-come-from}

Cilj izvora je jedan od ovih:

| Cilj | Izvor | Napomene |
|---|---|---|
| `monitor:<n>` | cijeli monitor, uživo | „Whole screen” prozora s brojem u „Which” |
| `window:<title>` | jedan prozor, uživo | „A window” prozora s njegovim naslovom |
| putanja datoteke | video datoteka | „A video file” prozora; bilo koji format koji OpenCV može čitati |

### Snimanje uživo: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` koristi paket `windows-capture`, koji omata **Windows Graphics Capture** -
javni API koji koriste programi za snimanje zaslona. Ništa se ne ubacuje u igru. Kursor se
ne snima i ne crta se žuti okvir snimanja.

Knjižnica za snimanje isporučuje kadrove povratnom funkciji na niti kompozitora i očekuje
da se ona odmah vrati, pa povratna funkcija samo kopira kadar (međuspremnik se ponovno
koristi), pretvara BGRA u RGB, mijenja mu veličinu, označava ga vremenom i stavlja u red od
**4 kadra**. Kad je red pun, **najstariji kadar se odbacuje** i brojač se povećava: zaostajanje
treba koštati kadrove, a ne memoriju ili ispravnost, a uživo prikazivanje treba pokazivati
gdje je igrač sada. Odbačeni kadrovi prikazuju se u retku statistike prozora, a ako je više od
polovice odbačeno, javlja se savjet.

Svaki kadar nosi `t` (sekunde od početka snimanja) i `monotonic` (sirovo `time.monotonic()`
u trenutku snimanja) - isto vrijeme kojim se označavaju paketi telemetrije, a upravo to
omogućuje poredanje Forzinih položaja uz kadrove.

`windows-capture` je u provjeri ovisnosti neobavezan: bez njega se video datoteka i dalje može skenirati.

### Video datoteke {#video-files}

`VideoSource` čita pomoću OpenCV-a, pretvara u RGB i mijenja veličinu. Spremnik bez brzine
kadrova tretira se kao 30 fps. Vremenske oznake su redni broj kadra podijeljen s brzinom
kadrova; datoteka nema stvarno vrijeme, pa se telemetrija ne može poravnati s videom.

### Razlučivost {#resolution}

Kadrovi se mijenjaju na izvoru tako da je duža strana jednaka snimateljskoj veličini
zadane postavke (Draft 640, Balanced 960, Detailed 1280 px), uz interpolaciju po površini.
Kadar 4K ima trideset puta više piksela nego što model dubine koristi.

## Ključni kadrovi {#keyframes}

Gotovo svaki kadar snimke je suvišan: stajanje u mjestu daje stotine pogleda na istu stvar.
Rekonstrukciji treba *paralaksa*. Zato se kadar zadržava prema **tome koliko se slika
promijenila od zadnjeg zadržanog kadra**, a ne prema satu.

`picture_change(a, b)`:

1. oba kadra pretvaraju se u sivo i smanjuju na mrežu 16 x 16 prosjeka blokova (prosjeci
   blokova reagiraju na pomicanje slike, a ne na zrnatost, lišće, treperenje ili HUD);
2. srednja apsolutna razlika, kao udio od 255;
3. kad je poznata maska svijeta, svaki blok se važe udjelom u kojem je svijet, a ne kabina,
   pa blok na pola nadzorne ploče broji se pola (koristi se kad maska pokriva više od 5 %
   težine mreže).

Prag se **prilagođava snimci**: prvih 30 kadrova ima početnu vrijednost postavke (0,020 /
0,010 / 0,004), zatim je to kvantil postavke (0,85 / 0,65 / 0,40) zadnjih 240 izmjerenih
promjena, nikad ispod 0,0001. Kadar se zadržava kad njegova promjena doseže prag; prvi kadar
se uvijek zadržava. Fiksni prag ne može raditi za različite prizore - promjena između kadrova
u tamnoj kabini vožnje je mali udio one u svijetloj, teksturiranoj sobi - dok „zadrži
najzanimljiviju trećinu” znači isto u oba slučaja. Prag u upotrebi šalje se uz svako
izvješće o napretku (`ScanProgress.threshold`), a trake brzine hoda u prozoru i na
prekrivanju mjere zadnju promjenu prema njemu (`ScanProgress.toward_next_view`).

Samo zadržani kadrovi idu kroz model dubine i rekonstrukciju. Kadrovi se ne spremaju osim
ako to pozivatelj ne traži (`keep_frames`); 160 ih se čuva za bojanje mreže (vidi
[boja](reconstruction-fusion-and-texture.md#colour)).

Skeniranje završava kad se zaustavi, kad videu ponestane kadrova, ili na granici vremena ili
broja ključnih kadrova.

## Što nije svijet {#what-is-not-the-world}

Dvije stvari u kadru igre nisu geometrija razine, a obje kvare rekonstrukciju:

- **HUD.** Nišan je najponovljivija značajka u bilo kojem kadru. Pronalazač značajki ga
  voli, savršeno se podudara između svakog para kadrova, a svaki takav podudar je dokaz da
  kamera nije pomaknuta - što sabija cijelu rekonstrukciju.
- **Stvari pričvršćene uz kameru.** Oružje, haube, okvir kabine, nadzorna ploča. Prava
  geometrija u krivom koordinatnom sustavu: spojena, razvlači se duž cijelog prijeđenog puta.

Dva detektora ih pronalaze. Oba daju masku (255 = svijet, 0 = nije svijet) ili `None` dok
nema dovoljno dokaza, a `None` uvijek znači „koristi sve”, nikad „ne koristi ništa”.

Maska se primjenjuje:

- na **otkrivanje značajki** u vizualnoj odometriji (maskiranje nišana iz izlaza uz
  dopuštanje da glasuje o položaju ispravlja vidljivi simptom, a ostavlja onaj koji šteti);
- na **spojene piksele**, pa se ne spaja geometrija kabine;
- na mjeru **oštrine i svjetline**, jer je kabina uvijek savršeno oštra;
- na **promjenu slike** koja odlučuje o ključnim kadrovima.

**Ne** primjenjuje se na kadrove koji se daju offline VGGT rješavaču (vidi
[Izvanmrežna rekonstrukcija](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: što se ne mijenja {#screenmask-what-does-not-change}

Koristi se od prvog ključnog kadra dok FlowMask nije spreman.

- Svaki kadar pretvara se u sivo, prepolovi i zamućuje (Gaussov 3 x 3) da jedan piksel
  treperenja u statičnom elementu HUD-a ne izgleda kao pokret.
- Apsolutna razlika po pikselu od prethodnog kadra zbraja se u eksponencijalni prosjek
  (propadanje 0,9), pa maska prati HUD koji se pojavi ili nestane usred skeniranja.
- Uči samo iz kadrova u kojima je poznato da se kamera miče (u skeniranju: nakon što je
  barem jedan kadar praćen) - nepomična kamera sve čini statičnim.
- Nakon **12** kadrova učenja piksel je statičan kad mu je prosječna promjena manja od
  **0,22** medijana promjene kadra - relativno, pa prag prati koliko brzo igrač vozi.
- Ako je više od **45 %** kadra statično, premisa je propala (izbornik, filmski umetak) i ništa se ne maskira.
- Maska se sužava za jedan piksel (rubovi HUD-a s uglađivanjem ne pripadaju ni jednoj strani)
  i vraća na punu veličinu.

Njezina napomena u prozoru: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry
detected`, ili `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: što nikad ne putuje {#flowmask-what-never-travels}

Kabina nije statična: igle se pomiču, brojač okretaja trza, mini-karta se rotira, pa detektor
promjene te piksele proglašava svijetom - a to su najgore značajke koje se mogu dati
rješavaču položaja. FlowMask postavlja bolje pitanje: **koje značajke opstaju a da ne
putuju?**

- U uživo skeniranju uči jednom, iz prvih **40 ključnih kadrova** (u sivom); zatim
  zamjenjuje ScreenMask za ostatak skeniranja.
- Kadrovi se režu na prozore od **30** kadrova, preklopljene za polovicu. U svakom prozoru
  zasijava se do 800 kutova (`goodFeaturesToTrack`, kvaliteta 0,01, 8 px razmaka) i prati
  piramidalnim Lucas-Kanadeom (21 x 21, 4 razine) uz **provjeru unaprijed-unatrag**: trag
  čiji se tok unatrag ne spusti unutar 1 px od mjesta gdje je počeo odbacuje se, jer bi
  tragač koji skliza na susjedni uzorak proizveo upravo onaj potpis „trajno a nepomično” koji
  se traži. Prozori kraći od 20 kadrova preskaču se. Kratki prozori su važni: u dugom
  prolazu gotovo svaka značajka svijeta napusti kadar, pa dokaz nestane.
- Neto pomak svake preživjele značajke uspoređuje se s **2 % širine kadra**: ispod toga je
  „zaglavljena”, iznad „u pokretu”. Brojevi se zbrajaju na mreži **24 x 24** ćelija zaslona
  prema tome gdje je značajka počela.
- Ćelija je blokirana kad sadrži najmanje 2 zaglavljene značajke i više zaglavljenih nego
  pokretnih, **i** kad je najmanje 3 od njezinih 8 susjeda također blokirano (usamljena ćelija
  je šum; tamni snimci proizvode ih mnogo).
- Zadržavaju se samo blokirane regije **povezane s rubom kadra**. Sve pričvršćeno uz kameru
  doseže rub zaslona; ono što je u sredini i ne putuje je točka nestajanja - kad vozite
  naprijed, cesta ravno pred vama nema tok i najviše je tražena geometrija.
- Preživjela regija raste za jednu ćeliju (rub nadzorne ploče je gradijent).
- Ako bi se više od **60 %** kadra maskiralo, ništa se ne maskira: na noćnim snimkama većina
  ćelija nema značajku koju se može pratiti, što izgleda isto kao brojčanik.

Njezina napomena: `watching what moves`, `nothing attached to the camera`, `ignoring N% of
the frame — it never travels`, ili, iznad 60 %, poruka da ništa ne maskira.

Izvanmrežni put uči isti FlowMask iz 4 niza po 90 uzastopnih kadrova raspoređenih po videu,
na 960 x 540 u sivom ([Izvanmrežno](reconstruction-offline.md)).

## Kvaliteta kadra i savjeti {#frame-quality-and-advice}

`QualityWatcher` ocjenjuje svaki ključni kadar i bira **jednu** uputu, da prekrivanje može
reći „uspori” dok je još vremena.

Po kadru mjeri se, samo na pikselima svijeta (svi pikseli ako maska ostavi manje od 5 %):

- **oštrina**: varijanca Laplaceovog operatora - standardna mjera u jednom prolazu, reagira
  upravo na ono što zamućenje u pokretu uništava;
- **svjetlina**: srednja razina sivog, 0-255.

Oštrina nema apsolutnu skalu (noćna etapa i svijetla ulica razlikuju se za red veličine, obje
u fokusu), pa se procjenjuje prema **tekućem medijanu ove snimke**: zadnjih 90 kadrova, uz
potrebnih 20 prije ikakve procjene. Svaki kadar uspoređuje se s poviješću *prije* nego što
se doda, pa dugi zamućeni dio ne može spustiti medijan da se izjednači sam sa sobom.

| Uvjet | Test |
|---|---|
| ravno | oštrina najviše 1,0 (ekran učitavanja, zid, nebo) |
| tamno | svjetlina manja od 26 |
| zamućeno | oštrina manja od 0,55 medijana, i nije ravno |

Savjet, prvo podudaranje pobjeđuje (poredano prema tome što najteže blokira skeniranje):

| Situacija | Savjet | Razina |
|---|---|---|
| manje od 20 kadrova | Upoznajemo sliku… | ok |
| ravno | Nema što mjeriti - usmjerite kameru na razinu, ne na nebo. | stop |
| tamno | Premračno za rekonstrukciju. Upalite svjetla ili vozite ovaj dio po danu. | stop |
| zamućeno | Zamućeno - usporite. | upozorenje |
| manje od pola kadrova praćeno | Gubitak traga - usporite i zadržite više razine u pogledu. | upozorenje |
| manje od 40 % praćenih kadrova spojeno | Položaji su dobri, ali dubina ne drži. Vozite bliže krajoliku. | upozorenje |
| postoje slabe točke | N slabih mjesta - karta ih označava. | ok |
| inače | Dobro - nastavite. | ok |

Razina boji savjet na prekrivanju (zeleno / jantarno / crveno). Traka **oštrine** na
prekrivanju je oštrina kadra u odnosu na medijan. (Kod također ima „Blurred, and the camera
is not moving. Check the capture.” za nepomičnu kameru; skeniranje uvijek javlja kameru kao
pomičnu, pa se to ne prikazuje.)
