---
title: "Localizarea cadrelor într-un nivel"
nav_order: 91
lang: "ro"
source: locate.md
source_hash: "a194419868e6"
nav_exclude: true
search_exclude: true
---
# Localizarea cadrelor într-un nivel {#locating-frames-in-a-level}

`locate` află unde a fost luat fiecare cadru al unei înregistrări de joc - poziția 3D a camerei și direcția privirii - potrivind
imaginea cu randările geometriei nivelului. Este pentru jocurile care nu păstrează nicio evidență a locului unde se afla jucătorul:
fără demo, fără fișier de reluare, fără telemetrie. Battlefield 6 este primul.

> **Experimental.** Pe înregistrări reale plasează, deocamdată, doar o mică parte din cadre; vezi
> [Cadre reale: experimental](#real-frames-experimental).

```bash
# Once per level: render it from every place a player can stand, and index the renders.
.venv\Scripts\python -m heat3d_capture locate build level.glb -o level.db

# Per recording: where was each frame taken?
.venv\Scripts\python -m heat3d_capture locate frames "<recording>.mp4" --db level.db -o out/match
```

Poziția vine **din imagine**, față de tot nivelul, fără nicio informație prealabilă. Traseul de pe harta minimă al
[cititorului HUD](hud-video.md) este doar o rezervă pentru cadrele pe care imaginea nu le poate plasa, iar fiecare rând spune
din care dintre cele două surse provine.

![locate: se construiește o dată pe nivel, apoi se localizează cadrele fiecărei înregistrări; cititorul hud sau locate minimap dă o
informație prealabilă și viețile](../assets/img/ro/locate-pipeline.svg)

![Subcomenzile locate, așa cum le arată --help](../assets/img/locate-help.svg)

## Ce atinge și ce nu atinge {#what-it-does-and-does-not-touch}

- Citește **propria înregistrare** a jucătorului și un fișier de nivel exportat de jucător din **propria copie** a jocului. Nu
  atinge niciodată jocul, memoria lui, fișierele lui cât timp rulează, sau rețeaua lui, și rulează după meci. Vezi
  [Regulile](rules.md).
- Plasează **doar camera proprie a jucătorului**: cadrul este vederea proprie a jucătorului.
- Nivelul, baza de date construită din el și tot ce este randat din el aparțin editorului jocului. Păstrează-le local.

## Cerințe {#requirements}

- Ce listează `requirements.txt`, PyTorch (de pe pytorch.org, pentru GPU), și `requirements-locate.txt`:

```bash
.venv\Scripts\python -m pip install -r requirements-locate.txt
```

- Un GPU cu OpenGL 3.3 (4.3 este mai rapid) pentru randări, și de preferat CUDA pentru modele. Pe un CPU merge, dar lent.
- Modelele sunt descărcate la prima utilizare (cam 450 MB): DINOv2 de pe Hugging Face, ALIKED și LightGlue prin kornia. Toate au
  licențe care permit uz comercial; vezi [Licențele](#licences).
- **Nivelul** ca `.glb` (sau `.gltf`) în sistemul de coordonate al vizualizatorului, Y în sus, **cu texturile lui de culoare de
  bază**, așa cum le scriu exportatorii 3DHeat (părțile `ground:` / `structure:`; numele părților nu sunt necesare). O unitate este un
  metru, cu excepția cazului în care `extras.unit_metres` din nivelul de sus al fișierului spune altceva. O scanare GameCapture
  (`reconstruct`, fereastra de scanare) este scrisă în **centimetri** și poartă `extras.unit_metres: 0.01`, deci este citită la
  mărimea ei reală. Un nivel fără texturi funcționează mult mai slab; vezi [Limite](#limits).

## Comenzi {#commands}

### `locate build <level> -o <db>` {#locate-build---o-}

Randează nivelul din fiecare loc de unde ar putea sta un jucător și stochează, pentru fiecare randare, poza ei și un descriptor global.

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `level` | | `.glb` / `.gltf` al nivelului. |
| `-o`, `--out` | | Folderul bazei de date de scris. |
| `--game` | `bf6` | Profilul jocului: înălțimile ochilor, câmpul vizual, casetele HUD, viteza (mai jos). `generic` pentru orice joc la persoana întâi. |
| `--eye` | al profilului | Înălțimile ochilor deasupra podelei, în metri, cea în picioare întâi. Câte o vedere în baza de date pentru fiecare înălțime. |
| `--fov` / `--vfov` | al profilului | Câmpul vizual orizontal al înregistrării, sau cel vertical (glisorul Battlefield) pentru o înregistrare 16:9. |
| `--spacing` | 2.5 | Metri între locurile de unde se iau vederile. |
| `--yaw-step` | 30 | Grade între direcțiile vederilor. |
| `--pitch` | 0 | Înclinările la care se randează, în grade în sus. |
| `--positions` | niciunul | Un tabel (Parquet sau CSV cu `x`, `y`, `z` la picioare, în sistemul nivelului) din care să se ia locurile în loc de fiecare podea: de exemplu, rezultatul unei rulări anterioare. |
| `--shadows` | oprit | Proiectează umbrele soarelui în randări (soarele nivelului, când fișierul lui îl numește în `extras.sun`). |
| `--untextured` | oprit | Randează doar forma și lumina. |
| `--box X0 Z0 X1 Z1` | tot fișierul | Doar locuri în interiorul acestei casete (unități ale nivelului): zona de joc. |
| `--places` | `auto` | De unde se iau vederile: `nav` - jucători la înălțimea ochilor deasupra plasei de navigație a nivelului (părțile `nav:`: exact unde are voie jocul să meargă), camere de vehicul la înălțimea lor deasupra părților `ground:` (teren și drumuri) în 50 m de el; `ground` - ambele deasupra `ground:`; `floors` - deasupra fiecărei fețe orientate în sus (și acoperișuri, și lăzi); `auto` - `nav` când nivelul are o plasă de navigație, altfel `floors`. |
| `--head` | niciunul | Un cap per hartă de la `locate train`, pentru descriptori. |

Scrie `<db>/db.json` (din ce a fost construit și cu ce) și `<db>/views.npz` (poze, descriptori).

### `locate frames <recording> --db <db>` {#locate-frames----db-}

| Opțiune | Implicit | Înseamnă |
|---|---|---|
| `source` | | Un video, o imagine sau un folder de imagini (luate în ordinea numelor, la `--fps` distanță). |
| `--db` | | Baza de date scrisă de `build`. Fișierul ei de nivel trebuie să fie încă unde a fost (sau `--level`). |
| `-o`, `--out` | `<source>.locate` | Calea de ieșire fără extensie. |
| `--fps` | 2 | Cadre localizate pe secundă de video. |
| `--start`, `--seconds` | tot | Partea din video care se citește. |
| `--width` | 1280 | Lățimea la care se potrivesc cadrele. |
| `--shortlist` | 8 | Vederi din baza de date încercate pe cadru, aproape de o informație prealabilă sau de o fixare. |
| `--search-shortlist` | 16 | Fără informație prealabilă: vederi din baza de date încercate pe cadru ([căutate împreună](#with-no-prior-frames-searched-together)). |
| `--no-search` | oprit | Fără informație prealabilă: caută fiecare cadru separat și crede fixarea lui fără vecinii lui. |
| `--accept-depth` | 0 (oprit) | Fără informație prealabilă: crede o fixare doar dacă distanța îndepărtată a potrivirilor ei este de atâtea ori distanța apropiată. |
| `--accept-support` | 2 | Fără informație prealabilă: vecini de acord de-a lungul vieții necesari ca o fixare să fie crezută. |
| `--checkpoint` | niciunul | Păstrează starea rulării aici și continuă de unde a rămas dacă există. |
| `--stop-file`, `--stop-process` | niciunul | Se oprește singur, starea salvată, cu codul de ieșire 75, când există acest fișier sau rulează un proces al cărui nume începe cu acesta (verificat înaintea fiecărui cadru; se poate repeta), ca o rulare lungă să elibereze mașina pentru un joc. Aceeași comandă continuă mai târziu. |
| `--normalise` | niciunul | Normalizare ușoară înainte de potrivire: `clahe`, `gray`. |
| `--minimap` | niciunul | Tabelul comenzii `hud`: **rezerva** pentru cadrele pe care imaginea nu le poate plasa. |
| `--prior-radius` | niciunul | **Accelerare opțională**, oprită implicit: caută doar vederile din baza de date aflate la atâția metri de poziția de pe harta minimă (cere `--minimap`). |
| `--minimap-anchor` | niciunul | Un fișier JSON care leagă harta minimă de nivel ([harta minimă ca informație prealabilă pentru căutare](#the-minimap-as-a-search-prior)): harta minimă taie căutarea încă din primul cadru; fixările găsite astfel sunt `visual+minimap-prior`. |
| `--no-level-search` | oprit | Cu o informație prealabilă: când nimic din apropierea ei nu se potrivește, nu caută și în tot nivelul (mai rapid). |
| `--lives` | tabelul `--minimap` | Tabelul comenzii `hud` ale cărui morți, desfășurări și reanimări spun când jucătorul era în joc: pozițiile sar doar peste o moarte ([vieți din filmare](#lives-from-the-footage)). |
| `--no-sequence` | oprit | Decide fiecare cadru separat, nu de-a lungul rulării (mai jos). |
| `--fit-fov` | oprit | După rulare, ajustează câmpul vizual după cele mai puternice fixări, pe fiecare vedere, și îl raportează. |
| `--check-every` | 0 | Și la fiecare N cadre, plasate sau nu, o imagine în `<out>.check`. |
| `--no-checks` | oprit | Nu scrie imaginile de verificare ale fixărilor vizuale (mai jos). |
| `--no-zoomed` | oprit | Nu rezolvă vederile mărite din fixările vecinilor (mai jos). |
| `--no-grow` | oprit | Nu caută din nou în jurul fiecărei fixări cadrele din jur care încă n-au una. |
| `--game`, `--eye`, `--fov`, `--vfov`, `--mask`, `--no-hud-mask`, `--max-speed` | al profilului | Ca mai sus; `--mask x,y,w,h` adaugă o casetă de ecran (pe un ecran 1920x1080) care nu este nivelul. |
| `--vehicle-vfov` | al profilului | Câmpul vizual vertical al camerelor din vehicule (glisorul vehiculului din Battlefield). |
| `--settings` | cel mai nou fișier de setări | `bf6`: fișierul de setări al jocului din care se citesc câmpurile vizuale (doar citire) când nu este dat `--fov`/`--vfov`; implicit, cel mai nou `PROFSAVE*_profile` din `Documents/Battlefield 6/settings`. Conține setările așa cum sunt acum, ceea ce poate să nu fie cum a fost făcută o înregistrare mai veche. |

### `locate refmap <level> <deploy screen> -o <refmap>` {#locate-refmap----o-}

Așază harta jocului pe nivel: referința față de care se citește harta minimă ([harta minimă, citită față de nivel](#the-minimap-read-against-the-level)).
`<deploy screen>` este o imagine a ecranului de desfășurare care arată toată harta, sau o înregistrare cu `--at <seconds>` la un asemenea
moment; caseta de hartă a profilului este decupată din ea (`--whole-picture` păstrează tot). Scrie `<refmap>.png` (harta reeșantionată în
sistemul de coordonate al nivelului, `--mpp` metri pe pixel, implicit 0,5), `<refmap>.valid.png` (unde este harta, nu un marcaj sau o
etichetă) și `<refmap>.json` (sistemul de coordonate și calibrarea, cu cât de departe erau plăcile hărții de el). `--topdown <prefix>`
păstrează nivelul randat de sus pentru rularea următoare (`--topdown-mpp`, implicit 0,656 m; `--box` îl limitează).

### `locate minimap <recording> --refmap <refmap> -o <table>.parquet` {#locate-minimap----refmap---o-parquet}

Citește harta minimă a înregistrării față de harta de referință, cadru cu cadru (`--fps`, implicit 2): poziția, direcția și zoomul fiecărei
hărți minime care se potrivește, în sistemul nivelului, scrise ca un tabel de hartă minimă cu o ancoră alături (`<table>.anchor.json`) pe
care o primește `locate frames` ca `--minimap <table>.parquet --minimap-anchor <table>.anchor.json`. Cu tabelul comenzii `hud` (`--hud`),
viețile lui sunt preluate; cu o ancoră și pentru acel tabel (`--hud-anchor`), prima căutare este în jurul locului unde o pune HUD-ul
jucătorului, iar unde nicio hartă minimă nu se potrivește, traseul HUD-ului propriu completează, mutat pe cele mai apropiate fixări de pe
harta de referință (`--hud-fill`, secunde, implicit 120; 0 îl oprește). `source` din tabel spune care (`refmap`, `hud`).

### `locate eval <out>.parquet --truth <poses>` {#locate-eval-parquet---truth-}

Compară un rezultat cu poze de cameră cunoscute: un tabel cu `time`, `x`, `y`, `z` (ochiul), `yaw`, `pitch` în sistemul nivelului.
`--offset` este decalajul de ceas (ora adevărată = ora video + decalaj); fără el, decalajul este căutat. `--unit-metres` transformă
erorile în metri.

## Profiluri de joc {#game-profiles}

| | `bf6` | `generic` |
|---|---|---|
| Înălțimile ochilor | 1,6 m în picioare, 1,05 m ghemuit (nemăsurate încă în joc) | 1,65, 1,1 m |
| Câmpul vizual | 55 de grade vertical, cam 86 orizontal la 16:9: **dă-l pe al jucătorului** cu `--vfov` | 90 orizontal |
| Casete HUD mascate | harta minimă și lista de echipă, lista de eliminări, busola, muniția, arma jucătorului, ferestrele, reticulul | reticulul |
| Cel mai rapid pe jos | 8 m/s | 8 m/s |
| Vederi deosebite | pe jos, în vehicul, mărit (mai jos) | fiecare cadru pe jos |
| Camere de vehicul | glisorul vehiculului (din fișierul de setări), vehiculul mascat, camera până la 8 m deasupra podelei, 30 m/s | - |

Câmpul vizual contează cel mai mult: un cadru rezolvat cu cel greșit este rezolvat cu o distanță focală greșită, iar poziția lui
alunecă de-a lungul vederii.

## Rezultate {#outputs}

### `<out>.parquet` {#parquet}

Un rând pentru fiecare cadru localizat, în **sistemul nivelului** (Y în sus, unitățile nivelului), cu instrucțiunile de citire ale
vizualizatorului în subsol (`kind: heat3d-locate`). Subsolul numește fiecare coloană care nu are un rol propriu drept extra, deci
vizualizatorul le păstrează pe toate (fișa lui de inspecție le arată).

| Coloană | Înseamnă |
|---|---|
| `time` | Secunde de la începutul videoclipului. |
| `event` | `start` pe primul rând al unei vieți, `position` pe celelalte. |
| `x`, `y`, `z` | Ochiul, netezit în interiorul vieții. Gol acolo unde nici o sursă nu a plasat cadrul. |
| `yaw`, `pitch` | Grade: yaw în jurul axei verticale (0 de-a lungul lui +X, crescând spre -Z, care este yaw-ul propriu al unui joc în sistemul vizualizatorului), pitch în sus de la orizontală. `pitch` este gol la rândurile de hartă minimă. |
| `dir_x`, `dir_y`, `dir_z` | Direcția privirii. |
| `player`, `team`, `session` | `me`, `own`, și `<video>#NN`, câte una pentru fiecare viață. |
| `life` | Viața în care filmarea arată cadrul (din morțile HUD-ului; 1 = prima). Gol când nu este în joc (mort, la pământ, în desfășurare) sau când viețile nu au fost citite. `session` este viața traseului, care se poate despica și la o săritură. |
| `source` | `visual` (din imagine), `visual+minimap-prior` (din imagine, căutarea tăiată de informația prealabilă de pe harta minimă), `minimap` (rezerva), `minimap+nav-floor` (în interior: harta minimă și podeaua din plasa de navigație) sau `none`. |
| `view` | `foot`, `vehicle`, `zoomed` sau `screen` (mai jos). |
| `cam_x`, `cam_y`, `cam_z` | Camera care a văzut cadrul. Pe jos și printr-o lunetă este ochiul, iar `x`, `y`, `z` sunt aceleași; în vederea a treia persoană dintr-un vehicul `x`, `y`, `z` sunt vehiculul (modelul de decalaj de mai jos), iar camera merge în spate și deasupra lui. |
| `hfov`, `zoom` | Câmpul vizual orizontal cu care a fost rezolvat cadrul, și pentru o vedere mărită zoomul ei față de vederea normală. |
| `confidence` | 0..1: cât de mult să ai încredere în rând (mai jos). |
| `uncertainty` | Eroarea tipică a rândului, în unitățile nivelului: pentru o fixare vizuală din inliere și vecini, pentru un rând de hartă minimă din potrivire (mai jos). |
| `inliers`, `rmse` | Inlierele PnP ale rezolvării vizuale și eroarea de reproiectare (pixeli la lățimea de lucru). |
| `x_raw` ... `pitch_raw` | Rezolvarea vizuală înainte de netezire (și pentru cele scoase prin votul valorilor aberante). |
| `kept` | Fixarea vizuală a supraviețuit votului valorilor aberante. |
| `note` | De ce un cadru nu a fost plasat sau a fost scos prin vot. |

### `<out>.summary.json` {#summaryjson}

Cadre, fixări vizuale, valori aberante, vieți, rânduri pe sursă, potrivirea hărții minime (perechi, inliere, reziduu), timpul pe cadru.

## Metoda {#method}

### Baza de date {#the-database}

Locurile sunt puncte pe fiecare triunghi orientat în sus al nivelului, împrăștiate uniform (câte unul la `--spacing`, pe o grilă 3D, astfel
încât etajele unei clădiri primesc fiecare al lor). Fiecare loc este verificat din ochi cu șase randări mici de adâncime: o cameră în
interiorul geometriei vede mai ales fețe din spate, un spațiu ascuns are ceva solid deasupra ochiului; ambele sunt eliminate. Din fiecare
loc nivelul este randat la fiecare înălțime a ochilor, la fiecare `--yaw-step` și la fiecare `--pitch`, iar fiecare randare este descrisă de
**DINOv2** (jetoanele ei de petic, adunate prin medie generalizată, unite cu jetonul de clasă).

Caracteristicile locale și punctele 3D față de care este în cele din urmă rezolvat un cadru **nu sunt stocate**: sunt refăcute când sunt
necesare, randând câteva vederi alese de recuperare, ceea ce ia milisecunde. Astfel o bază de date rămâne la câteva sute de megaocteți, nu
zeci de gigaocteți, iar asta permite rafinarea de mai jos. Costul este că `frames` are nevoie de fișierul nivelului și de un GPU, nu doar de
baza de date.

### Un cadru {#one-frame}

1. **Mască** tot ce nu este nivelul: casetele HUD ale profilului și reticulul, plus orice `--mask`.
2. **Recuperare** pe **tot nivelul**: descriptorul cadrului față de fiecare vedere din baza de date; cele mai asemănătoare câteva zeci, subțiate
   ca să cuprindă locuri și direcții diferite, formează lista scurtă.
3. **Potrivire**: fiecare vedere din lista scurtă este randată din nou la dimensiunea și câmpul vizual ale cadrului, cu adâncimea ei. Punctele-cheie
   ALIKED ale cadrului și ale randării sunt potrivite cu LightGlue. Un pixel randat potrivit plus adâncimea lui este un punct 3D al nivelului, deci
   fiecare potrivire este o corespondență 2D-3D; punctele-cheie de pe o margine de adâncime (a cărei adâncime poate aparține la ce e în spatele lor)
   sunt eliminate.
4. **Poziție**: PnP cu RANSAC (SQPnP), apoi o rafinare robustă care ține camera dreaptă - o vedere la persoana întâi nu se rotește pe ax - și
   minimizează eroarea de reproiectare a inlierelor.
5. **Este posibil?** O poziție trebuie să fie la înălțimea ochilor unui jucător, deasupra unei podele și în afara geometriei (o randare de adâncime
   direct în jos). O textură asemănătoare în altă parte - o podea în plăci potrivită cu un perete din același material - poate da sute de inliere
   într-o poziție pe care niciun jucător n-ar fi putut-o avea; acestea sunt puse deoparte, oricâte inliere ar avea.
6. **Randare și comparație**: nivelul este randat în poziția rezolvată și potrivit din nou, ceea ce înlocuiește o vedere din baza de date aflată
   până la câțiva metri și zeci de grade distanță cu una care aproape coincide cu cadrul. Se repetă cât timp câștigă inliere (cel mult de două ori).
7. **Alegerea**: cele mai puternice trei locuri (la mai mult de vreo 3 m unul de altul) sunt rafinate fiecare înainte să se aleagă unul. O asemănare
   poate conduce înainte de rafinare; locul corect câștigă mult mai mult din ea.
8. **Verdict**: `confidence` combină numărul de inliere, cel mai bun alt loc (`runner_up`) și eroarea de reproiectare. O fixare este `ok` cu cel puțin
   25 de inliere, fără alt loc în 80% din inlierele ei și o încredere de cel puțin 0,85 - pragul pe care măsurătorile de mai jos îl pun la 97,5-99% corecte.

### Vederi {#views}

Un cadru nu este mereu ochii jucătorului. Detectorul profilului citește din HUD ce vedere este și cadrul este rezolvat în consecință:

- **Pe jos**: câmpul vizual de infanterie și înălțimile ochilor.
- **Vehicul** (Battlefield 6: indicațiile tastelor din diagrama locului, `C CAMERA` și `E EXIT`, jos în centru): câmpul vizual al vehiculului,
  vehiculul însuși mascat (partea de jos din mijloc a ecranului, în vederea lui a treia persoană), și o cameră permisă până la 8 m deasupra podelei.
  Fixarea este a camerei.
- **Ecran** (margini întunecate în jurul unui mijloc întunecat: harta de desfășurare, un meniu, tabelul de scor): nu este o vedere a nivelului;
  sărit.
- **Mărit** (o lunetă, vizorul unui artilerist, vederea proprie la persoana întâi a unui vehicul: o margine a ecranului neagră, ambele întunecate,
  în jurul unei imagini luminoase): nu este căutat peste nivel - o felie de lunetă din nivel nu seamănă cu nicio vedere largă din baza de date -
  dar este rezolvat după rulare din cea mai apropiată fixare aflată la cel mult 6 s, mai jos. Oprit cu `--no-zoomed`.

### Vederi mărite {#zoomed-views}

O vedere îngustă fixează slab poziția: un pas înapoi cu puțin mai mult zoom arată aproape la fel. Deci un cadru mărit pornește de unde spune
vecinul că se află ținta - pe jos ochiul fixării aceleia, într-un vehicul 2,5 m deasupra terenului sub mijlocul vehiculului (ținta unei turele) - și
cât de mult se poate fi mutat de atunci: 2 m, plus 4 m pe secundă pe jos sau 8 în vehicul, cel mult 12 m (`reach`).

1. **Direcție și zoom, poziția ținută**. Pentru fiecare zoom de 1, 1,2 (vederea proprie a unui vehicul, mai îngustă decât pe jos), 1,5, 2, 3, 4, 6 și 8,
   nivelul este randat din ținută în direcții aflate la cel mult 30 de grade de cea a vecinului (și, de la 3x, câteva înclinări). Punctele-cheie ale
   cadrului potrivite cu o randare, cu punctele nivelului sub ele, sunt raze din ținută; o rotație este ajustată pe ele câte două (RANSAC) pentru distanțe
   focale de la 0,75 la 1,3 ori cele ale acelui zoom, un punct fiind de acord într-un unghi care lasă loc ca ținta să fie la `reach` depărtare la distanța
   lui. Zoomul, direcția și distanța focală cu care se află cele mai multe puncte de acord câștigă.
2. **Fixat**. Acele puncte ajustează apoi împreună poziția, direcția și distanța focală, după eroarea lor de reproiectare, poziția ținută de ținută printr-un
   cost de doi pixeli pe `reach` mutat; randat încă o dată la răspuns și ajustat din nou. Inlierele și eroarea se numără în pixeli, iar fixarea este `ok`
   după aceeași încredere ca oricare alta.

Zoomul scris (`zoom`) este față de câmpul vizual al rulării pe jos; `hfov` este cel rezolvat. Într-un vehicul, poziția scrisă este a vehiculului, cu 2,5 m sub
ținută, ca pentru vederea lui a treia persoană.

### Vehicule: camera și vehiculul {#vehicles-the-camera-and-the-vehicle}

În vederea a treia persoană dintr-un vehicul, poziția rezolvată este a camerei de urmărire, care merge în spate și deasupra vehiculului și se rotește în jurul
lui odată cu privirea jucătorului. Poziția scrisă (`x`, `y`, `z`) este a vehiculului - terenul de sub mijlocul lui: camera plus `vehicle_offset` al profilului,
cu atâția metri înainte de-a lungul direcției orizontale a camerei și cu atâția în jos. Camera rămâne în `cam_x`, `cam_y`, `cam_z`. Conversia se face înainte de
secvență și de traseu, astfel încât o cameră care se rotește în jurul unui vehicul staționar nu este luată drept mișcare. Subsolul tabelului poartă decalajul
folosit și dacă a fost măsurat (`vehicleOffset`). Pe jos și printr-o lunetă nu există decalaj.

Cum a fost măsurat decalajul Battlefield 6: la fixări corecte ale unor cadre reale la a treia persoană ale unui tanc, mijlocul tancului a fost marcat cu ochiul pe
cadru, iar nivelul randat în fixare a dat terenul de la acel pixel. Profilul ia mediana: cam 10 m înainte de cameră și cam 4 m mai jos. Marcajul este bun la un metru
sau cam așa, și este pentru un singur tip de vehicul: o mașină sau un elicopter își poartă camera altfel.

### Fără informație prealabilă: cadre căutate împreună {#with-no-prior-frames-searched-together}

Descriptorul global al unui cadru față de un nivel întreg este un semnal slab, iar inlierele unui singur cadru nu spun un loc adevărat de unul asemănător. Deci fără
informație prealabilă cadrele unei înregistrări sunt mai întâi descrise și căutate împreună (`search.py`), iar o fixare este crezută doar împreună cu cadrele din jur:

- **Lista scurtă.** Asemănările fiecărei vederi sunt măsurate față de propria medie și împrăștierea de pe înregistrare, ca o vedere care seamănă cu fiecare cadru să nu
  mai câștige peste tot. Fiecare cadru notează celulele unei grile de 24 m după rangul celei mai bune vederi a lor; cel mai bun drum prin celule de-a lungul fiecărei
  vieți, în ce poate acoperi jucătorul între cadre, dă o credință pentru fiecare celulă, iar cea mai bună vedere a fiecărei celule, cea mai crezută întâi, formează o
  singură listă. Recuperarea simplă este cealaltă, iar cele două se iau pe rând: măsurarea vederilor față de înregistrare penalizează un loc pe care jucătorul abia îl
  părăsește, iar acolo recuperarea simplă se descurcă bine.
- **Crezând.** Un candidat contează doar dacă inlierele lui acoperă cel puțin 12% dintr-o grilă de 8 x 8 peste cadru: o asemănare este un obiect repetat, o stivă de
  containere, cu sute de inliere pe câteva celule ale cadrului. O fixare este crezută când se află pe cel mai bun drum prin candidații care numără (mai jos), cu cel
  puțin doi vecini la 6 s care sunt de acord cu ea. Un cadru în afara jocului nu este căutat deloc.
- **Creșterea.** Doar ce este crezut este folosit ca punct de plecare, iar o fixare crescută trebuie să acopere cadrul în același fel.

### De-a lungul rulării {#along-the-run}

Fiecare cadru păstrează fiecare poziție fizic posibilă pe care a găsit-o, câte una pentru fiecare loc (`candidates`), nu doar cea mai puternică. Rularea alege apoi
câte una pentru fiecare cadru - sau niciuna - astfel încât pozițiile alese să formeze un traseu pe care l-ar fi putut merge sau conduce un jucător, iar cât mai multe
inliere să stea pe el: un model Markov ascuns, decodat dintr-o dată (Viterbi). O asemănare care câștigă un cadru singură pierde în fața locului pe care vecinii ei
sunt de acord; un candidat slab pe care traseul trece, cu cel puțin doi vecini de acord, devine o fixare (`note`: chosen along the sequence); o fixare sigură pe care
toți vecinii o contrazic încetează să mai fie una. Un vecin este de acord doar în 6 s: mai departe, distanța pe care ar fi putut-o acoperi un jucător - și mai ales un
vehicul - este atât de mare încât acordul nu spune nimic. Oprit cu `--no-sequence`.

### Orele cadrelor {#frame-times}

`time` unui rând este momentul propriu al cadrului în înregistrare, nu numărătoarea lui după rata nominală de cadre. Înregistrările se abat de la rata lor nominală (cu
câteva zecimi de secundă pe un clip, la cele măsurate), iar tot ce citește un cadru înapoi după ora lui - imaginile de verificare, trecerea în zonă, `locate train --real`,
harta minimă din comanda `hud` - caută după ora de pe cadru. Cadrele numărate ar pune cadrul imaginii de verificare departe, cu atât, de cel localizat.

### Câmpul vizual, din cadre {#the-field-of-view-from-the-frames}

`--fit-fov` păstrează cele mai puternice fixări ale unei rulări (pe fiecare vedere) și rafinează poziția, direcția și distanța focală ale fiecăreia împreună, pe inlierele ei;
mediana lor este câmpul vizual cu care a fost făcută înregistrarea, raportat în rezumat (`hfov_fitted`) pentru `--fov` al rulării următoare. Punctele apropiate și cele
îndepărtate se mișcă diferit la o schimbare a distanței focale decât la o schimbare de poziție, și asta îl fixează; are nevoie de fixări cu adâncime, nu de un perete plat.

### Un model per hartă {#a-per-map-model}

`locate train` antrenează un cap mic peste DINOv2 pentru un singur nivel, pe randările lui, ca descriptorul global să găsească vederile potrivite ale cadrelor reale, nu
doar ale randărilor:

- **Capul**: fiecare jeton de petic printr-o proiecție în două straturi, adunat prin medie generalizată peste peticele care arată nivelul, unit cu jetonul de clasă
  proiectat. DINOv2 rămâne înghețat. Tot ce este aici scris (MIT).
- **Perechi**: un loc pe terenul pe care se poate merge și o direcție, randate de două ori din poziții aflate la un metru sau două și cam zece grade distanță, la câmpuri
  vizuale aflate la până la 10 grade distanță, sub lumini diferite (soare, umbre, lumină ambientală), fiecare printr-un aspect de joc: gradare, ceață după adâncime,
  strălucire, vignetă, fum, oameni în cale, vehiculul propriu al jucătorului în vederile din vehicul, estompare de mișcare, zgomot, JPEG (`augment.py`). Mascate ca un cadru.
  Locurile aflate la câțiva metri unul de altul și care privesc în aceeași direcție nu sunt numărate drept negative.
- **Cadre reale**: cadre cu o poziție pe care conducta a găsit-o singură (pseudo-etichete: fixări alese de-a lungul unei secvențe) pot intra ca perechi - cadrul și o randare
  la poziția lui - într-o a doua rundă.
- **Pierderea**: contrastivă (InfoNCE) peste lot.

`locate build --head <head.pt>` construiește baza de date cu el; `frames` îl folosește apoi pentru cadre.

| Opțiune `locate train` | Implicit | Înseamnă |
|---|---|---|
| `-o`, `--out` | obligatorie | Fișierul capului de scris (`.pt`). |
| `--steps` | 600 | Pași de antrenare. |
| `--real TABLE VIDEO` | niciunul | Un tabel `locate frames` și înregistrarea lui: fixările lui sigure intră ca perechi reale. Se poate repeta. |
| `--real-confidence` | 0.85 | Încrederea de care are nevoie o fixare ca să intre ca pereche reală. |
| `--spacing`, `--box`, `--places`, și opțiunile profilului | ca la `build` | Unde sunt locurile de antrenare și profilul jocului. |

### Verificarea cu ochiul {#checking-by-eye}

Fiecare fixare vizuală primește o imagine în `<out>.check` - `<time>s_<view>_visual.jpg`: cadrul, și alături nivelul randat la camera fixării, cu marginile cadrului
desenate peste randare. Acolo unde se aliniază, fixarea este corectă. Scrisă după ce secvența și traseul au decis, deci imaginile sunt exact rândurile pe care tabelul le
numește vizuale. Oprit cu `--no-checks`.

### Harta minimă, citită față de nivel {#the-minimap-read-against-the-level}

O hartă minimă înfășurată într-un singur mozaic (cea a comenzii `hud`) nu este plată: scara ei se schimbă odată cu zoomul la care a fost înregistrat fiecare
minimap, un loc văzut de două ori poate fi desenat de două ori, iar mozaicul fiecărui clip este al lui. O similaritate ajustată pe câteva fixări ține atunci aproape de
ele, dar este la zeci de metri de ele, departe. Deci harta minimă este așezată de nivelul însuși, în doi pași, iar nimic nu este înfășurat:

- **Harta de referință** (`locate refmap`). Ecranul de desfășurare desenează toată harta cu nordul sus, plată, la o singură scară. Nivelul randat de sus arată aceleași
  lucruri ridicate deasupra terenului (tancuri, clădiri, ziduri): pe nivel, înălțimea lor deasupra terenului pe 15 m în jur; pe hartă, ce este desenat mai deschis decât
  terenul din jur. Harta este pusă pe nivel prin corelație încrucișată normalizată a celor două, peste scară și o mică rotire, rafinată potrivind plăcile hărții una câte una,
  și, la final, toată harta odată în jurul acelui răspuns (câteva zeci de plăci lasă scara liberă cu un procent, metri la capetele hărții). Rezultatul este o singură
  similaritate, de la pixelul hărții la nivel.
- **Harta minimă, cadru cu cadru** (`locate minimap`). Fiecare hartă minimă eșantionată - decupajul cititorului HUD și masca lui - este potrivită (SIFT) cu harta de referință
  în jurul locului unde a fost ultima oară jucătorul, sau oriunde când nu se știe nimic, și se ajustează o similaritate (rotire, zoom, deplasare). Punctul jucătorului dus
  prin ea este poziția, sus-ul hărții minime (conul de vizualizare) este direcția, iar scara ei este zoomul - măsurat, nu presupus.
- **Unde nu se potrivește.** Ecranul de desfășurare nu desenează nimic în afara zonei de joc; o hartă minimă care arată mai ales ce se află în afara ei - un jucător la marginea
  hărții - nu are ce să potrivească. Acolo traseul propriu al HUD-ului ține locul, mutat cu decalajul măsurat de cele mai apropiate fixări de pe harta de referință
  (`--hud-fill`); este la fel de bun cât mozaicul lângă acele fixări.

Pe nivelul de test, harta minimă citită astfel a fost la câțiva metri (mediană) de fixările vizuale sigure, la fel de bună în afara zonei în care a fost potrivită harta de
referință ca în interiorul ei.

### Harta minimă ca informație prealabilă pentru căutare {#the-minimap-as-a-search-prior}

Traseul hărții minime din comanda `hud` spune, pentru cele mai multe cadre din joc, cam unde se află jucătorul și încotro privește - în unitățile ei (pixeli ai hărții minime,
nordul sus). Odată legat de nivel, taie căutarea la o parte mică din el; poza în sine tot vine din imagine, după aceleași reguli.

- **Ancora** (`--minimap-anchor <anchor.json>`): o similaritate per hartă, de la harta minimă la nivel - scară, rotire (cu oglinda dintre pixelii cu nordul sus și axele
  nivelului), deplasare - ajustată pe fixările vizuale sigure (încredere 0,7 și mai mare) din mai multe clipuri. Harta minimă a fiecărui clip este un mozaic pe care cititorul HUD
  l-a înfășurat singur, deci fiecare stă în alt loc în unitățile hărții minime; două mozaicuri ale aceleiași hărți diferă doar printr-o deplasare, găsită potrivind punctele-cheie
  între ele (deplasarea pe care se potrivesc cel mai mult), iar fiecare mozaic este legat de o referință comună prin toate perechile care se potrivesc bine. Fișierul ancorei
  poartă similaritatea hărții, deplasarea clipului (`clip_shift`) și eroarea pe care a arătat-o ancora față de fixările clipurilor lăsate afară din ajustare (`median`, `p90`,
  metri).
- **Unde și în ce direcție.** Direcția hărții minime este yaw-ul camerei: pe clipurile măsurate a fost de acord cu yaw-ul rezolvat în 2-5 grade. Deci un cadru este mai întâi
  potrivit cu randări făcute acolo unde pune harta minimă camera - pe jos un ochi deasupra terenului de acolo, într-un vehicul camera de urmărire în spate și deasupra lui
  (decalajul vehiculului) - privind de-a lungul direcției: locul și încă 4 m de fiecare parte, la două înclinări (`seeds`). Doar când niciunul dintre acestea nu dă o fixare
  se încearcă vederile proprii ale bazei de date din disc (30 m plus eroarea de 90% a ancorei).
- **Corectată pe parcurs.** Fiecare fixare sigură din apropierea informației prealabile spune cât de departe e ancora acolo; mediana celor din 2 minute corectează informația
  prealabilă, iar împrăștierea lor (cel puțin 5 m) înlocuiește eroarea ancorei în raza discului - până la 10 m: fixările care nu se potrivesc mai mult spun că harta minimă este
  greșită ca loc, nu că orice aflat la 50 m ar fi bun. Fără nicio fixare în 2 minute, informația prealabilă nu este corectată deloc (eroarea din altă parte a clipului nu spune nimic
  despre aici).
- **Ancore cu grilă.** O ancoră poate purta și `grid`: sistemul nivelului x și z pe o grilă regulată peste unitățile hărții minime ale clipului, citită biliniar; înăuntrul ei grila
  așază punctul, în afara ei, similaritatea. Ancora unui tabel `locate minimap` este identitatea (tabelul lui este deja în sistemul nivelului).
- **Potriviri slabe.** Cu o informație prealabilă, o potrivire slabă (25 de inliere sau mai multe, dar nu suficient de sigură de una singură) care stă în disc este păstrată -
  cu încrederea ei mai mică - pentru ca secvența și traseul să o judece, nu aruncată: fumul, molozul și zidurile distruse lasă cadrelor reale mai puține potriviri.
- **Surse.** `visual` - imaginea a plasat-o, fără informație prealabilă; `visual+minimap-prior` - imaginea a plasat-o, căutarea tăiată la informația prealabilă;
  `minimap` - imaginea nu a reușit, harta minimă ține locul; `minimap+nav-floor` - în interior, mai jos.
- **În interior, harta minimă conduce.** Un cadru pe care imaginea nu l-a plasat, pe jos, unde un ochi la poziția hărții minime vede nivelul închis din toate părțile (distanța
  mediană sub 8 m în patru direcții) și niciun cer, este în interior: primește x și z ale hărții minime și înălțimea podelei din plasa de navigație de acolo - din mai multe etaje,
  cel mai apropiat de ultima fixare - cu `source = minimap+nav-floor`, ca să fie clar că imaginea nu l-a fixat.

### Vieți din filmare {#lives-from-the-footage}

O poziție poate sări doar acolo unde a murit jucătorul. Viețile nu sunt ghicite din poziții - o singură fixare greșită ar deschide una nouă - ci citite din filmare: tabelul
cititorului HUD înregistrează morțile arătate de ecranele de cădere și de desfășurare (`death`), căderile pe care le-a reanimat un coechip (`downed`, `revived`), desfășurările
(`spawn`) și unde au început și s-au oprit jocul (`start`, `end`); `lives.py` le transformă în vieți. O moarte închide o viață, primul cadru în joc după ecranul de desfășurare
deschide următoarea; o reanimare nu taie viața (jucătorul e unde a căzut), iar cadrele cât e la pământ nu sunt plasate; o porțiune de meniuri sau încărcare mai lungă de 10 s o taie
și ea. Cadrele în afara jocului (morți, în desfășurare, la pământ) nu sunt plasate niciodată.

În interiorul unei vieți continuitatea este o regulă strictă: fiecare pas cel mult viteza înmulțită cu timpul dintre, plus 1,5 m. Viteza este a cadrului: pe jos cea a profilului,
într-un vehicul viteza pe care a arătat-o indicatorul vehiculului în 3 s (o treime în plus, și 2 m/s, pentru accelerare) sau, unde nu arată nimic, limita clasei lui. De-a lungul
rulării (Viterbi) un pas peste o moarte este liber la orice distanță, fiecare alt pas este limitat; un cadru care ar avea nevoie de o săritură este lăsat afară - latura mai slabă a
unei contradicții pierde (mai puține inliere, mai puțin sprijin) - și viața nu este niciodată despicată din cauza lui. Când latura lăsată afară este ea însăși puternică (încredere
0,9 și mai mare, două sau mai multe fixări de acord între ele), rularea nu ghicește: ambele părți sunt păstrate și marcate `jump without detected death` (o moarte nedetectată, sau
o teleportare reală), și listate în rezumat. Rezerva pe harta minimă urmează aceleași vieți.

Battlefield 6: vederea la persoana întâi a tancurilor arată viteza (`<n> KPH`, în dreapta vizorului; citită cu OCR-ul cititorului HUD); vederea a treia persoană nu. Indicațiile
de pe clipurile de test au fost mici, deci vehiculele terestre sunt lăsate să meargă cu 15 m/s acolo unde nu se citește nimic. Bărcile, elicopterele și avioanele cu reacție primesc limite
generoase (20, 90 și 280 m/s) care nu sunt măsurate: niciun clip nu arată vreunul condus sau pilotat, iar clasificatorul de vedere nu deosebește aerul de sol - o porțiune mai rapidă
decât un vehicul terestru apare ca săritură, marcată, și nu este crezută.

### Distrugerea {#destruction}

Fișierele nivelului sunt nivelul intact; într-un meci pereții, casele și stâncile sunt împușcate, molozul și fumul stau pe-acolo, iar lucrurile se înrăutățesc pe măsură ce meciul avansează.

- **Potrivirea are încredere în nivelul static.** O parte pe care exportul o marchează ca distructibilă (numele ei începe cu `destructible:`, sau `extras.destructible` pe nodul,
  plasa sau primitiva ei) este desenată în masca `destructible` a randării. Potrivirile al căror punct de nivel stă pe ea sunt eliminate când mai rămân 40 sau mai multe potriviri pe
  părți statice - terenul, drumurile, structurile mari poartă rezolvarea.
- **Antrenamentul vede dispariția.** Randările de antrenament (`locate train`) înlocuiesc petice din părțile distructibile cu zgomot de culoarea molozului și adaugă praf jos,
  deasupra terenului, peste fum și restul aspectului jocului (`augment.py`), ca modelul pe hartă să nu se bazeze pe ele.
- **Geometria lipsă nu este un loc greșit**: cu o informație prealabilă, potrivirile slabe din disc sunt păstrate (mai sus).

Până când exporturile nu poartă etichetele, nimic nu este marcat distructibil, iar acestea nu fac nimic.

### Traseul {#the-track}

- **Valori aberante**: o fixare este comparată cu fixările din cele 3 s dinainte și, separat, cu cele 3 s de după; consistentă înseamnă să nu fie mai departe decât permite viteza
  profilului, plus 1,5 m. O fixare care nu este de acord cu majoritatea vecinilor pe **ambele** părți este scoasă prin vot (păstrată în coloanele `_raw`, `kept` fals). Cerința
  pentru ambele părți păstrează prima fixare după o reapariție.
- **Vieți**: cu viețile din filmare (mai sus), traseul le urmează, iar în interiorul unei vieți lasă afară latura mai slabă a unui pas care încalcă viteza. Fără ele, se taie unde două
  fixări păstrate consecutive sunt mai departe decât permite viteza, unde există un gol de mai mult de 8 s și unde tabelul hărții minime începe o viață nouă.
- **Netezire**: în interiorul unei vieți, fiecare fixare este fuzionată cu o linie dreaptă prin fixările din jur (o potrivire liniară locală ponderată, sigma 0,5 s), fiecare
  ponderată după incertitudinea ei: o fixare puternică - bună la centimetri - rămâne unde este, una slabă este trasă spre vecinii ei puternici. O linie și nu o medie, fiindcă o
  medie trage un jucător care aleargă în urmă: media a fost încercată prima și a transformat un traseu de 3 mm într-unul de 0,3 m la 2 cadre pe secundă. Unghiurile de privire nu
  sunt netezite; o întoarcere a privirii este reală și rapidă.

### Rezerva de pe harta minimă {#the-minimap-fallback}

Tabelul hărții minime este în cadrul propriului mozaic (pixeli, x est, y nord). Este legat de nivel printr-o singură similaritate - rotire, scară, deplasare, și o oglindă dacă
se potrivește mai bine - ajustată robust pe cadrele unde ambele au o poziție. Acolo unde imaginea n-a dat nimic, sau fixarea ei a fost scoasă prin vot, poziția de pe harta minimă ține
locul cu `source = minimap`, o încredere de cel mult 0,5 și o incertitudine de dublul reziduului ajustării plus 1,5 m. Harta minimă nu are înălțime: este preluată de la cea mai apropiată
fixare vizuală. O rulare doar cu harta minimă (fără fixări vizuale) nu poate fi legată de nivel și nu plasează nimic.

`--prior-radius` folosește aceeași ajustare invers: odată ce opt fixări vizuale au legat harta minimă de nivel, recuperarea caută doar vederile din baza de date aflate în raza aceea
de poziția hărții minime, și revine la tot nivelul când asta nu găsește nimic. Este mai rapidă; este însă doar la fel de corectă ca harta minimă, de aceea este oprită implicit.

## Exactitate {#accuracy}

Măsurată pe un **banc** unde adevărul este exact: un nivel de test exportat cu texturile lui, și cadre randate din poze de cameră cunoscute *ca să arate ca un joc, nu ca baza de
date* - soarele și umbrele nivelului, contrast mai dur, o gradare de culoare aleatoare, vignetă și strălucire, forme cu mărimea unui jucător și fum în cale, HUD-ul desenat în casetele
mascate, estompare, zgomot și JPEG. Fiecare cadru este localizat față de **tot nivelul, fără informație prealabilă**. Corect înseamnă în 1 m și 5 grade. Nimic din banc (nivele,
randări) nu face parte din acest depozit.

| Cadre fără informație prealabilă | Rezultat |
|---|---|
| plasate corect | cam 4 din 5 |
| din fixările `ok` (încredere 0,85 și mai mare), corecte | cam 97-99% |
| eroarea fixărilor corecte | milimetri până la un centimetru; câteva sutimi de grad |
| timpul pe cadru | cam 1 s pe un GPU de desktop |

Încrederea este o măsură utilă a încrederii: aproape fiecare fixare de 0,9 și mai mare a fost corectă, în timp ce fixările sub 0,85 erau adesea greșite - de aici pragul de 0,85 pentru
`ok`. Unde eșuează: nu se găsește nicio vedere potrivită, prea puține potriviri (un perete la un pas, mai ales cer, mai ales un obstacol), sau două locuri arată la fel.

**O cale.** O cale de cameră de test, randată ca mai sus într-un videoclip de 30 fps, cu un tabel de hartă minimă făcut din aceeași cale (cadrul ei întors, scalat, oglindit, cu zgomot),
rulată prin `locate frames` la 2 cadre pe secundă și notată cu `locate eval`, care trebuia să găsească și decalajul de ceas: fiecare cadru în joc a fost plasat, aproape toate din imagine;
decalajul de ceas a fost găsit în sutimi de secundă; rândurile din imagine au fost în câțiva centimetri, cele de pe harta minimă în cam un metru.

**Ce face diferența:**

- **Texturile** sunt ceea ce se bazează potrivirea. Fără ele se plasează doar o mică parte din cadre; o podea redusă la o singură culoare plată costă cam o treime din fixările sigure.
- **Câmpul vizual corect.** Cu 3 grade în plus, eroarea fixărilor corecte crește de la milimetri la zeci de centimetri, iar majoritatea fixărilor nu mai sunt `ok`. Dă câmpul real.
- **Umbrele** în randările bazei de date (`--shadows`): un câștig mic.
- **O listă scurtă mai lungă**: un câștig mic, de câteva ori mai lent. Una mai scurtă: mai puține fixări, precizie mai mare.
- Normalizarea luminii (CLAHE) n-a adus niciun câștig și nu este implicită.

Locurile asemănătoare sunt principala sursă de greșeli sigure: o poziție exact cu un modul de clădire în urmă, de-a lungul unui perete de module repetate, rezolvată la fel în mai multe
cadre ale unui jucător care stă pe loc. Rafinarea celor mai puternice trei locuri înainte de alegere și punerea deoparte a pozițiilor imposibile au înlăturat cele mai multe dintre celelalte.

### Cadre reale: experimental {#real-frames-experimental}

Pe înregistrări reale `locate` **nu funcționează încă bine**: plasează din imagine doar o mică parte din cadre, în majoritate cadre din vehicule (camera a treia persoană vede mai mult din
nivel de sus), și aproape niciun cadru pe jos (jucătorul se uită la pereți și la sol de aproape). Ce s-a învățat pe înregistrările de test:

- **Găsirea vederii corecte este ceea ce eșuează.** Lumina jocului, efectele și texturile de export grosiere mută un cadru real mai departe de randări decât imitația din banc, deci
  vederea corectă stă aproape de lista scurtă, dar în afara ei.
- **Un model per hartă ajută** (`locate train`): ridică mult mai sus vederea corectă, iar cadrele reale adăugate ca perechi de antrenament ajută și mai mult cadrele din jurul lor.
- **Cadrele apropiate se ajută între ele**: la 2 cadre pe secundă, o porțiune dintr-un vehicul avea cam o treime din cadre plasate; la un cadru la fiecare 5 s, aproape niciunul.
- **Cadrele reale arată o eroare de reproiectare de 2-3 pixeli** față de 1 la randări; profilul ia 3 drept normal (`pixel_noise`).
- **Câmpul vizual** ajustat din cadre (`--fit-fov`) poate fi diferit de setările salvate: setarea s-ar fi putut schimba de la înregistrare.
- **Fixările slabe făcute `ok` doar de vecini depărtați** au fost cele greșite; vecinii contează acum doar în 6 s, iar fiecare fixare de încredere 0,7 și mai mare a fost corectă.
- **Fișierul nivelului contează**: terenul fără textură și vegetația desenată ca niște cartonașe negre strică. Randatorul respectă decupajele (`alphaMode: MASK`): un texel sub `alphaCutoff`-ul
  materialului (0,5 când nu este dat) este aruncat, iar fundalul se vede prin el (`render.py`).

Ce trebuie făcut în continuare: multe mai multe pseudo-etichete reale din multe clipuri pentru antrenament și pentru calibrarea încrederii (`locate train --real <table> <video>`), nivele cu
teren cu textură și o cale de a trata vederile mărite.

## Randări față de cadre {#renders-against-frames}

Randările din care este făcută baza de date nu sunt cadrele jocului. Pe banc diferența a fost imitată (lumină, umbre, gradare, jucători, fum, HUD) și costă cam 10 puncte din fixările corecte
(91% la 80-89%); fixările corecte rămân la milimetri. Ce a ajutat: soarele și umbrele hărții în randările de față de care se potrivește (puțin), o listă scurtă mai lungă (puțin, lent). Ce nu:
normalizarea luminii CLAHE.

Ce nu poate imita banca este restul unui cadru real: lumina coaptă și reflectată, ocluzia ambientală, ceața, particulele, vegetația care se mișcă, post-procesarea jocului. Ca să se măsoare,
înregistrează redarea unui lucru ale cărui poze de cameră sunt exacte - un demo sau o reluare a unui joc - și compară cu `locate eval`; el găsește singur decalajul de ceas dintre înregistrare și poze,
sau îl ia din `--offset`.

## Limite {#limits}

- **Cadrele reale sunt abia plasate deocamdată.** Doar cu DINOv2, aproape niciun cadru real nu este plasat fără informație prealabilă; cu un model per hartă, câteva procente sunt, corecte când sunt
  privite (vezi [Cadre reale: experimental](#real-frames-experimental)). Fiecare cifră de exactitate de mai sus este pe randări ale nivelului, făcute să arate ca jocul (soarele lui, umbrele, gradarea,
  strălucirea, zgomotul, jucătorii, HUD-ul), față de randări ale aceluiași nivel. Un cadru real diferă în moduri pe care o randare nu le poate imita: lumina coaptă și reflectată, ocluzia ambientală,
  ceața, particulele, texturile care se schimbă, vegetația animată. Cât costă asta este întrebarea deschisă; vezi [Randări față de cadre](#renders-against-frames) pentru cum se măsoară.
- **Nivelul trebuie să fie cel jucat**, la aceeași versiune, cu texturile lui, inclusiv cele ale podelei: vezi [Ce trebuie să conțină fișierul nivelului](#accuracy).
- **Locuri asemănătoare.** Nivelele refolosesc clădiri, obiecte și materiale în plăci. Două locuri care arată la fel dau două rezolvări bune; a doua este raportată (`runner_up`), fixarea
  nu este `ok`, iar traseul sau harta minimă trebuie să decidă. O fixare care este corectă, dar marcată ambiguă, este pierdută, nu greșită.
- **Cadre cu puțin nivel în ele**: un perete la un pas, cerul, un fum de grenadă, înconjurătorul negru al unei lunete, un ecran de moarte sau de meniu. Nu dau nicio fixare și sunt spuse că nu dau.
- **Zoomul.** Ținta în sus și lunetele îngustează câmpul vizual. Cadrele mărite sunt rezolvate doar dintr-o fixare vecină (mai sus); o porțiune lungă printr-o lunetă fără fixare în jur nu este.
- **Vehicule și camere a treia persoană.** Camera nu este atunci la înălțimea ochilor și nici unde este vehiculul; decalajul dintre ele (mai sus) a fost măsurat pentru un singur tip de vehicul, un tanc principal
  de luptă. Alte vehicule își poartă camera altfel, iar pozițiile lor sunt greșite cu diferența - câțiva metri. Vehiculul însuși este mascat (`vehicle_hud` al profilului).
- **Ce nu conține nivelul**: distrugerile, vehiculele, jucătorii, ușile mișcate. Mascate unde este HUD-ul; în rest, RANSAC trebuie să vadă peste ele.
- **Viteza.** Un cadru costă cam 0,5-1,5 s pe un GPU de desktop (mai mult când alt lucru împarte GPU-ul): randările listei scurte, potrivirea și randarea-și-compararea. Două cadre pe secundă
  dintr-un meci de 20 de minute sunt 2 400 de cadre, 20 de minute până la o oră. Baza de date se construiește o dată pe nivel: cam 20-30 de minute pentru un nivel de mărimea unei hărți de
  shooter competitiv la 2,5 m distanță; o zonă de joc de mărimea Battlefield are nevoie de `--box` și de o distanță mai mare între locuri, sau de mai multe casete.
- **Nivele mari.** Un fișier de nivel poate conține kilometri de fundal: `--box` limitează locurile la zona de joc. Umbrele (`--shadows`) sunt proiectate dintr-o singură hartă de umbre peste tot fișierul,
  care devine grosieră la cele foarte mari.

## Licențe {#licences}

| Componentă | Licență |
|---|---|
| Greutățile DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 |
| ALIKED (`aliked-n16`) | BSD-3-Clause |
| LightGlue, varianta ALIKED | Apache-2.0 |
| kornia, kornia-rs | Apache-2.0 |
| moderngl, glcontext | MIT |
| transformers, huggingface_hub, safetensors | Apache-2.0 |

Toate permit uzul comercial. Două alternative obișnuite au fost lăsate deoparte, pentru că termenii lor s-ar transmite fiecărui rezultat: greutățile SuperPoint (necomerciale) și codul de regresie a coordonatelor de scenă
sub licențe necomerciale. Vezi [Modelele și licențele](models-and-licences.md).

## Rularea pe Battlefield 6 {#running-it-on-battlefield-6}

Ce trebuie, în ordine:

1. **Nivelul, cu texturi**, din copia instalată de jucător, ca `.glb` în metri, Y în sus, în sistemul de coordonate pe care îl folosesc tabelele cititorului HUD și ale vizualizatorului.
   `extras.unit_metres` (1 pentru metri; o scanare GameCapture scrie 0.01, pentru că este în centimetri) și, dacă este cunoscut, `extras.sun` (direcția spre soare) în `extras`-ul de nivel
   de sus al fișierului. Un nivel fără texturi se încarcă și se randează, dar vezi [Limite](#limits).
2. **Zona de joc** ca o casetă (`--box X0 Z0 X1 Z1`, metri): fișierele de nivel Battlefield poartă fundalul pe kilometri în jur, iar o bază de date a tuturor este în mare parte vederi pe care nu le vede nimeni.
3. **Câmpul vizual al jucătorului**: glisorul Battlefield este vertical; dă-l ca `--vfov` (cele 55 de grade ale profilului sunt un loc păstrat). Înregistrări la 16:9.
4. **Înălțimile ochilor** (`--eye`, în picioare apoi ghemuit) - cele 1,6 și 1,05 m ale profilului nu sunt măsurate. Măsoară-le la prima rulare bună: `y` al fixărilor unui jucător care stă pe loc pe
   teren plat, minus înălțimea podelei acolo.
5. **Casetele HUD** au fost verificate pe înregistrări 4K cu aspectul implicit (harta minimă, lista de echipă, lista de eliminări, busola și busola vizorului, bara de scor și steagurile
   obiectivelor, chatul, muniția, indicațiile, arma). Un HUD mutat sau scalat are nevoie de `--mask`.
6. Construiește, apoi localizează cu tabelul cititorului HUD ca rezervă, și uită-te la un eșantion de fixări:

```bash
.venv\Scripts\python -m heat3d_capture locate build level.glb -o level.db --game bf6 --box X0 Z0 X1 Z1 --shadows
.venv\Scripts\python -m heat3d_capture hud "<recording>.mp4" --game bf6 -o out/match
.venv\Scripts\python -m heat3d_capture locate frames "<recording>.mp4" --db level.db --game bf6 --vfov <yours> --minimap out/match.parquet -o out/match.locate --check-every 20
```

Fiecare fixare vizuală primește o imagine de verificare (`<out>.check`; `--check-every 20` adaugă fiecare al 20-lea cadru, plasat sau nu): cadrul alături de nivelul randat la fixarea lui, cu marginile
cadrului desenate peste randare. Acolo unde se aliniază, fixarea este corectă. Nu există adevăr cu care să compari în Battlefield, deci imaginea aceasta, partea de cadre plasate din imagine
(`summary.json`) și cât de bine se potrivește ajustarea hărții minime cu fixările vizuale (`residual` ei) sunt verificările.
