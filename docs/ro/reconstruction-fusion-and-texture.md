---
title: "Fuziune, acoperire și culoare"
nav_order: 5
lang: "ro"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fuziune, acoperire și culoare {#fusion-coverage-and-colour}

Cod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Fiecare cadru-cheie plasat actualizează două grile rare deodată: **volumul de suprafață**, care devine mesh-ul, și **grila de acoperire**, care spune cât de mult să se creadă în el și unde să te întorci. Ambele sunt actualizate pe cadru-cheie, nu la final, pentru că harta acoperirii este ceea ce jucătorul folosește ca să se orienteze.

## De la adâncime la puncte {#from-depth-to-points}

Pentru fiecare cadru-cheie a cărui poziție este cunoscută **și** a cărui adâncime are o scară:

1. Se folosește fiecare al doilea pixel pe fiecare direcție (`PIXEL_STRIDE = 2`; pixelii vecini ai unei aceleiași suprafețe nu sunt măsurători independente).
2. Adâncimea este convertită în metri prin afinul cadrului.
3. Se păstrează doar între **0,35 m** (mai aproape este arma, HUD-ul, capotajul) și **60 m** (eroarea monoculară crește cam cu pătratul distanței, deci punctele îndepărtate sunt zgomot cu formă de geometrie), și numai pe pixelii lumii din mască.
4. Este ridicat prin modelul camerei și mutat în lume prin poziție.
5. Fiecare punct poartă culoarea pixelului.

Un cadru care este plasat, dar nu are o scară a adâncimii, este numărat ca *plasat*, dar nu *fuzionat*.

## Volumul de suprafață {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - voxelul este „Surface detail" din fereastră.

### Ocupare ponderată, nu TSDF {#weighted-occupancy-not-a-tsdf}

Un câmp de distanță semnat trunchiat sculptează de-a lungul fiecărei raze de pixel și prinde bine structurile subțiri și spațiul liber curat, pentru că știe că o rază a trecut *prin* spațiu gol. Asta înseamnă parcurgerea razei pentru fiecare dintre sute de milioane de pixeli. Acest volum acumulează în schimb **ocupare ponderată** per voxel și rulează marching cubes pe rezultatul netezit: suficient de rapid ca să ruleze în timpul scanării, pe o mașină fără GPU utilizabil, iar rezultatul este o suprafață închisă, nu un nor de puncte. Costul: structurile subțiri și spațiul liber sunt mai slabe decât le-ar da un TSDF.

### Integrarea unui cadru {#integrating-a-frame}

- Punctele sunt grupate în voxeli (`floor(point / voxel)`).
- Fiecare voxel atins primește `weight x sqrt(count / max_count)`, unde `count` este câte puncte ale cadrului au căzut în el și `weight = max(0.1, pose confidence)`. Rădăcina pătrată: după un punct, mai mulți pixeli ai aceleiași suprafețe din același loc încetează să mai fie dovadă; ponderarea după încrederea poziției împiedică o poziție îndoielnică să miște suprafața.
- Culoarea este o medie ponderată rulată per voxel.

Grila este **rară**: un traseu parcurs atinge o fracțiune mică din caseta sa de încadrare. Coordonatele voxelilor sunt împachetate într-o cheie de 64 de biți (21 de biți pe axă, până la ±1.048.575 voxeli - la 0,25 m, aproximativ ±262 km) și căutate cu un tablou sortat și căutare binară, complet vectorizat.

### Extragerea mesh-ului {#extracting-the-mesh}

1. Voxelii cu greutate sub **0,35** sunt eliminați (puncte izolate la marginile siluetei ar deveni vârfuri ascuțite).
2. Greutățile sunt scalate după **percentila 75** din toată scanarea și tăiate la 1.
3. Spațiul ocupat este tăiat în **blocuri de 64 de voxeli** pe latură, fiecare realizat cu un **halo de 3 voxeli** din datele vecinilor (fără el, fiecare limită de bloc s-ar închide într-un zid, iar un drum ar ieși ca un rând de cutii).
4. Câmpul fiecărui bloc este netezit cu o Gaussiană (sigma 0,8 voxeli) ca să se elimine ridurile pe care le lasă zgomotul de adâncime.
5. **Prima trecere**: percentila 99 a câmpului netezit, eșantionată din toate blocurile (cel mult 2 milioane de valori), fixează o scară globală a nivelului. Normalizarea pe bloc ar promova un singur element aberant la o suprafață completă în propriul bloc gol.
6. **A doua trecere**: câmpul fiecărui bloc împărțit la această scară, marching cubes la **0,5**. Un triunghi aparține blocului în care cade **centroidul** său, deci triunghiurile care traversează o joncțiune sunt emise exact o dată.
7. Vârfurile sunt mutate în unități ale lumii, la centrele voxelilor; fiecare vârf își ia culoarea voxelului (gri mediu acolo unde cade în afara unui voxel ocupat).

Extragerea pe blocuri este ceea ce face posibilă o scanare de mărimea unui traseu: un tablou dens peste o casetă de un kilometru pătrat la 0,25 m ar fi miliarde de celule. `tests/test_track_scale.py` fixează că funcționează la această scară, cu memorie proporțională cu ce s-a scanat.

### Sol și structură {#ground-and-structure}

`classify` etichetează fiecare triunghi după normala sa (orientată după normalele vârfurilor extrase): în **35 de grade față de verticala în sus** este `ground`, orice altceva este `structure`. Vizualizatorul desenează solul plin și structurile aproape transparente. **Apa nu este niciodată revendicată** - nu poate fi deosebită de solul plat după formă, iar o etichetă greșită ar face o curte să pară un lac. Fiecare etichetă devine o parte a fișierului `.glb` ([Ieșirea .glb](glb-output.md)).

## Acoperire {#coverage}

`CoverageGrid(voxel=0.5)` înregistrează, pentru fiecare celulă de jumătate de metru, patru lucruri care nu sunt același lucru:

| Termen | Stocat | Scor (fiecare tăiat la 0..1) | De ce se numără separat |
|---|---|---|---|
| De câte ori a fost văzut | numărul de cadre-cheie care au văzut celula | `count / 3` | o singură dată este o presupunere, fără nimic cu care să fie mediată |
| Din câte direcții | suma vectorilor unitari de vizualizare | `(1 - spread) / (1 - 0,93)`, unde spread = lungimea sumei / număr | douăzeci de cadre care merg drept spre un perete nu au paralaxă între ele; două vederi la treizeci de grade una de alta valorează mai mult |
| De la ce distanță | cea mai apropiată distanță de vizualizare | `1 - nearest / 40 m` | eroarea adâncimii crește cam cu pătratul distanței |
| Cât de bine a fost plasată camera | cea mai bună încredere a poziției | încrederea însăși | geometria fuzionată cu o poziție îndoielnică ajunge în locul greșit |

Punctele unui cadru sunt grupate mai întâi pe celulă, astfel încât zece mii de pixeli ai unui perete să conteze ca o observație dintr-o direcție.

**Calitatea = produsul celor patru termeni**, nu media lor: sunt condiții care trebuie toate să fie adevărate. Un loc văzut de două sute de ori dintr-o direcție, de la șaizeci de metri, este slab observat, iar o medie l-ar ascunde în spatele unui termen excelent.

Cifrele principale (`summary`): celulele ocupate, partea cu calitate cel puțin 0,5 („% well seen" din fereastră), calitatea medie și volumul.

### Zone slabe {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. celulele cu calitate sub 0,35 sunt slabe;
2. celulele slabe sunt grupate după **conectivitate** (vecinătatea de 26, union-find doar pe celulele ocupate - nu un raster peste caseta de încadrare, care pe un drum lung înseamnă milioane de celule goale);
3. grupurile cu mai puțin de 8 celule sunt ignorate;
4. motivul fiecărui grup este cel mai frecvent *termen cel mai slab* al celulelor sale, iar poziția sa este media celulelor;
5. sortate, cel mai mare primul (apoi cea mai proastă calitate), cel mult 8.

| Motiv | Sfat afișat |
|---|---|
| puține vederi | Văzut doar o dată sau de două ori - treci din nou pe lângă el. |
| o singură direcție | Văzut doar dintr-un unghi. Fă un pas lateral și uită-te din nou. |
| departe | Văzut doar de departe. Apropie-te de el. |
| urmărire slabă | Camera nu a fost bine localizată aici. Apropie-te mai încet. |

Conectivitatea contează: gruparea după o grilă fixă de blocuri ar raporta o cameră laterală neglijată ca pe multe inele separate, iar nimeni nu poate spune opt locuri de la un singur loc numărat de opt ori.

### Harta de sus {#the-plan-view}

`top_down(resolution)` proiectează celulele pe x/z și păstrează **cea mai bună** calitate pe coloană (cineva stând într-o cameră are acoperire slabă a tavanului și excelentă a podelei; media ar colora camera în chihlimbar). Coloanele nevăzute niciodată sunt marcate separat. Fereastra o desenează la 200 x 200, overlay-ul la 120 x 120 ([Fereastra de scanare](reconstruction-scan-ui.md#the-coverage-map)).

### Este reconstructibil? {#is-this-reconstructable}

La fiecare 25 de cadre fuzionate, odată ce există cel puțin 500 de celule:

| Constatare | Verdict | Mesaj (prescurtat) |
|---|---|---|
| sub 2% din celule au spread de vizualizare sub 0,93 | nereconstructibil | Aproape deloc paralaxă. Fie camera nu privește niciodată într-o parte, fie urmărirea derivă, astfel încât aceeași suprafață nu aterizează niciodată de două ori în același loc. Verifică numărul de cadre plasate: dacă e mare, este derivă. |
| distanța mediană până la cel mai apropiat punct peste 25 m | nereconstructibil | Totul a fost văzut de la N m sau mai departe ... Apropie-te de ce vrei. |
| sub 6% cu spread bun | reconstructibil, cu avertisment | Paralază subțire - geometria va fi aspră. Mișcarea lateral față de ce privești ajută cel mai mult. |

Paralaza joasă are două cauze pe care aceasta nu le poate deosebi, de aceea mesajul le numește pe amândouă.

## Culoare {#colour}

Culoarea de fuziune per voxel este ieftină și în direct, și estompată: fiecare pixel dintr-o celulă de un sfert de metru este mediat, inclusiv cei văzuți de la tăiș de la treizeci de metri. Deci la export mesh-ul este colorat încă o dată, o singură dată, din cadrele însele:

- **Cadre păstrate**: până la **160** de cadre-cheie (imagine și poziție), alese prin eșantionare cu rezervor, astfel încât să se întindă pe toată scanarea, nu pe coada ei.
- **Pe vârf** (`project_colours`), fiecare cadru păstrat contribuie dacă vârful este în fața camerei și în imagine, suprafața este întoarsă cel mult cam 70 de grade de la fața camerei (`|normal . view| > 0.34`), este mai aproape de **35 m**, și nimic mai aproape nu stătea în față (mai jos).
- Fiecare astfel de vedere este notată `facing x (1 - distance / 35)`, astfel încât o vedere apropiată, frontală, bate una îndepărtată, rasantă. Cele **4 vederi cu cel mai mare scor** ale fiecărui vârf sunt păstrate - indiferent de ordinea cadrelor, o vedere mai bună o înlocuiește pe cea mai slabă dintre cele patru - și sunt amestecate, ponderate cu același scor.
- **Ocluzie**: în fiecare cadru, vârfurile proprii ale mesh-ului aflate în vedere sunt desenate într-un buffer de adâncime de celule de 2 pixeli, păstrându-l pe cel mai apropiat pe celulă. Un vârf mai mult de `0,3 m + 5%` din distanța sa în spatele celui mai apropiat din celula lui era ascuns în acel cadru - un perete între cameră și drum, în spatele lui - iar acea vedere nu contează. Testul cunoaște doar mesh-ul: un ocluzor care nu a fost niciodată fuzionat (o mașină care trece, un stâlp de cabină în afara mascii HUD) nu este prins.
- Un vârf pe care niciun cadru nu l-a văzut își păstrează culoarea voxelului; un vârf fără niciuna este gri mediu (negrul ar arăta ca o gaură).

Culoarea se scrie ca `COLOR_0` per vârf, nu ca un atlas de texturi. Modul implicit al vizualizatorului este o hartă gri sub căldură saturată; culoarea există ca să găsească drumul pe un circuit scanat, unde geometria singură nu îl desparte de bancheta laterală, și se arată în spatele comutatorului *Captured colour* din panoul său Background / level (*Fundal / nivel*). Un atlas ar înmulți dimensiunea fișierului și ar cere un desfăcător de UV, pentru o vedere care în mod deliberat nu este cea implicită. Blender și alte unelte glTF citesc `COLOR_0`.
