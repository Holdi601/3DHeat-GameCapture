---
title: "Poziția camerei și scara"
nav_order: 4
lang: "ro"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Poziția camerei și scara {#camera-pose-and-scale}

O hartă de adâncime spune cât de departe sunt lucrurile de *un* punct de vedere. Transformarea multor astfel de hărți într-un singur nivel are nevoie să știe unde era fiecare punct de vedere și în ce unități. Această pagină acoperă căile în direct; odometria feed-forward offline este la [Reconstrucție offline](reconstruction-offline.md).

Cod: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Modelul camerei {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` construiește o cameră stenopeică din **câmpul vizual orizontal** pe care îl setați în fereastră: `fx = (width / 2) / tan(fov / 2)`, pixeli pătrați (`fy = fx`), punctul principal în centrul cadrului. Un joc nu își publică proiecția, deci acesta este singurul număr presupus: prea îngust și scena pare mai adâncă decât este. Calea offline folosește 65 de grade.

Un `Pose` este stocat **lume-din-cameră**: `rotation` (3 x 3) și `translation` = centrul camerei în lume, ceea ce vor traiectoria, harta acoperirii și overlay-ul.

## Odometrie vizuală (implicit) {#visual-odometry-the-default}

`VisualOdometry` urmărește fiecare cadru-cheie față de cel anterior:

1. **Trăsături**: ORB, până la 1500 pe cadru, detectate doar pe masca lumii (vezi [Captură](reconstruction-capture.md#what-is-not-the-world)).
2. **Potriviri** cu cadrul-cheie anterior: forță brută, distanță Hamming, verificare încrucișată (doar perechile reciproc cele mai bune).
3. **Ridicare în 3D**: adâncimea cadrului anterior este deja în unități ale lumii, deci pixelii săi potriviți devin puncte ale lumii.
4. **Plasarea camerei**: `solvePnPRansac` între aceste puncte (eroare de reproiectare 3 px, încredere 0,999, 200 de iterații). Translația iese în aceleași unități, deci **scara trece peste gol**.
5. **Ancorarea adâncimii acestui cadru**: adâncimea sa prezisă inversă este potrivită (`fit_scale`) față de adâncimile inlierelor PnP, iar ciclul se repetă.

**Primul cadru** este originea: poziție identitate, iar afinul adâncimii sale este fie calibrarea la sol de mai jos, fie, fără ea, identitatea (reconstrucția este atunci consecventă cu ea însăși, dar fără unități).

O poziție are nevoie de cel puțin **18 inliere RANSAC** - clar peste minimul PnP de șase, pentru că o soluție din puncte abia suficiente este exact cea care este încrezătoare și greșită.

### Încredere {#confidence}

Fiecare cadru plasat primește o încredere în 0..1 care îi ponderează fuziunea și acoperirea:

| Poziție din | Încredere |
|---|---|
| telemetrie | 1,0 |
| o rezolvare feed-forward | 0,85 |
| urmărire vizuală | `inliers / matches x min(1, inliers / 60)` |

### Când urmărirea se rupe {#when-tracking-breaks}

Un cadru care nu poate fi plasat este raportat, niciodată ghicit: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Nu se înregistrează nicio poziție și nu se fuzionează nimic. A continua de la ultima poziție sau a porni o origine nouă ar pune următoarea porțiune de nivel la un decalaj arbitrar - o cusătură care arată ca geometrie reală.

După o rupere, fiecare cadru nou este **relocalizat** față de o bază de date cu cadre-cheie trecute (la fiecare al 4-lea cadru urmărit se adaugă unul, până la 120, cel mai vechi se aruncă), începând cu cel mai recent, cu același pas de potrivire și PnP. Până reușește unul, cadrele sunt aruncate. Un cadru recuperat continuă în același sistem de coordonate. Recuperările sunt numărate și afișate în fereastră (`N recovered`).

### Închiderea buclei: dezactivată {#loop-closure-off}

Aceeași bază de date susține închiderea buclei: potrivirea cu cadre-cheie mult mai vechi pentru a detecta o revenire și a agăța traseul înapoi pe ea. **Este dezactivată implicit, iar scanerul nu o pornește niciodată** (`Reconstructor(loop_closure=False)`). Pe peisaje repetitive - o etapă de raliu, un coridor, un șir de copaci - fiecare porțiune arată ca fiecare alta, iar potrivirea trăsăturilor confirmă revenirile false, ceea ce ține camera aproape de locul de start în timp ce ea continuă să conducă. A o face corect cere recunoașterea locului (un vocabular bag-of-words sau un descriptor învățat) și verificare geometrică față de o hartă, ceea ce nu este construit.

Când este pornită din cod, o închidere are nevoie de: un cadru-cheie cu cel puțin 60 de cadre-cheie vechime, aflat la 6 m de poziția curentă, potrivit cu cel puțin 90 de inliere, care mută poziția cu mai mult de 0,02 m și mai puțin de 6 m. Chiar și atunci înlocuiește doar poziția curentă; nu este un graf de poziții și nu mută cadrele anterioare sau geometria fuzionată.

## Poziții din telemetrie {#telemetry-poses}

Cu **Racing telemetry (Forza) -> Listen for position data** pornit, calea camerei vine din Data Out al Forza în loc să vină din imagini (`ForzaPoseSource`):

- Un fir ascultă pe `127.0.0.1:<port>` (5300 implicit) cu aceeași detectare de structură ca înregistratoarele ([Forza](telemetry-forza.md)); pachetele sunt folosite cât timp `isRaceOn` este setat. Un port ocupat este raportat, nu ridicat ca excepție: telemetria este un bonus, iar scanarea continuă vizual.
- Fiecare pachet primește marca **momentului monotonic în care a sosit** - același ceas cu care captura își marchează cadrele. Timpul propriu al jocului numără de la ceva fără legătură, deci nu este folosit la aliniere. Un jitter de loopback de un milisecund sau două înseamnă aproximativ 6 cm la 200 km/h.
- Se păstrează un buffer rulant de 30 de secunde. Poziția unui cadru este **interpolată** din eșantioanele de o parte și de alta a momentului capturii: poziția liniar, rotația prin interpolare sferică (o matrice amestecată nu este o rotație și ar strâmba fiecare punct). Pe un gol mai lung de **0,35 s**, sau în afara buffer-ului, nu există poziție.
- `pose_from_forza`: camera este plasată la mașină (decalajul unei camere de urmărire nu este publicat). **Pozițiile sunt păstrate exact cum le trimite jocul**: lumea Forza este deja cu Y în sus (x și z pe hartă, y înălțimea), cum o scriu fișierele de ture și de traseu, deci suprafața aterizează pe aceleași coordonate ca turele înregistrate peste ea. (O versiune anterioară schimba y cu z pentru o lume „Z în sus" și culca traseul pe o parte.)
- Rotația este yaw, apoi pitch, apoi roll, cu sensurile citite din ture înregistrate: direcția de mers `atan2(dx, dz)` este egală cu yaw-ul, panta urcată este egală cu minus pitch-ul (pozitiv înseamnă nasul în jos), iar roll-ul este pozitiv când suspensia din dreapta este comprimată (pozitiv coboară partea dreaptă). Axele mașinii (x dreapta, y sus, z înainte) sunt apoi transformate în cele ale camerei (x dreapta, y jos, z înainte) prin inversarea lui y.
- Lumea Forza este **levogiră**, iar cadrul camerei nu este, deci matricea lume-din-cameră rezultată este o reflexie (determinant -1), iar scanarea iese levogiră ca fișierele de ture. Interpolarea nu este afectată (rotația dintre două asemenea poziții este o rotație adevărată).
- Când un cadru nu are poziție din telemetrie (un gol), reconstructorul revine la **urmărirea vizuală** pentru acel cadru, continuând de la ultima poziție din telemetrie, și revine la pozițiile feed-ului de îndată ce acesta răspunde din nou. PnP întoarce doar rotații, deci într-o lume oglindită se rezolvă cu lumea oglindită prin z, iar oglinda este pusă înapoi; cadrul ajunge în coordonatele jocului. Doar dacă urmărirea vizuală eșuează și ea, cadrul rămâne neurmărit.

### Scara adâncimii din telemetrie {#depth-scale-from-telemetry}

Jocul spune unde este camera, nu cât de departe este ceva, deci adâncimea fiecărui cadru tot trebuie ancorată - dar nu prin înlănțuire din cadrul zero, a cărui unitate este arbitrară, în timp ce pozițiile sunt în metri. În schimb, trăsăturile potrivite între cadrul anterior și cel curent (cel puțin 8) sunt **triangulate direct din cele două poziții cunoscute**, în metri, iar harta de adâncime este potrivită pe punctele din fața camerei. Fiecare cadru este ancorat față de telemetrie, deci nu există un lanț care să derive.

Dacă cele două poziții sunt la mai puțin de **0,05 m** una de alta, razele sunt aproape paralele, iar triangularea este zgomot, deci cadrul rămâne neancorat: plasat exact, dar nefuzionat („positioned, but its depth has no scale yet"). De aceea fereastra numără separat cadrele *plasate* și cele *fuzionate*.

## Scara {#scale}

Odometria vizuală înlănțuie corect scara relativă, dar întregul nivel plutește pe un factor necunoscut. Ieșirea relativă a Depth Anything vine în unități arbitrare, deci lăsarea primului cadru ca identitate pune lumea la câțiva metri de cameră la o dimensiune arbitrară.

`GroundCalibrator` fixează acel factor din **cât de sus este camera deasupra solului**, măsurat pe **primul cadru-cheie** și, când acesta nu are sol utilizabil, pe cele următoare:

- Înălțimea camerei: **1,15 m** (linia ochilor unui șofer) - fereastra folosește mereu aceasta; scripturile pot da 1,70 m (`WALKING_HEIGHT`, un jucător în picioare) sau `None` (fără calibrare).
- Eșantionul de sol: rândurile 62-92% de jos în cadru (sub orizont, deasupra capotajului sau armei) și coloanele 30-70% pe lățime (departe de bancheta laterală).
- Fiecare pixel de acolo cu o predicție utilizabilă este ridicat cu adâncimea `1 / predicted` în unitățile rețelei; punctele sub axa optică dau o înălțime sub cameră. Mediana lor este înălțimea camerei în unități ale rețelei, deci `metri per unitate = 1,15 / mediană`, iar afinul cadrului este `scale = 1 / metri_per_unitate`, shift 0.
- Este de încredere doar cu cel puțin 200 de eșantioane de sol și o **împrăștiere** (abaterea absolută mediană față de mediană) sub **0,60**.
- La primul cadru-cheie, potrivirea devine unitatea originii, deci scanarea este în metri de la început. Când primul cadru-cheie nu are sol utilizabil, scanarea pornește fără unități, iar fiecare cadru-cheie urmărit ulterior este încercat, până la **30 de cadre** în total. Prima potrivire care reușește dă *metri per unitate*: mediana, peste banda solului, a adâncimii pe care o implică solul peste adâncimea pe care a dat-o lanțul pentru acel cadru. Tot ce este deja fuzionat este în unitatea primului cadru, deci factorul nu este returnat în lanț; este aplicat întregului nivel (și punctelor marcate) când este scris și distanței afișate între timp. Dimensiunea voxelului este atunci în unitățile primului cadru, deci dimensiunea lui în metri diferă de setare cu acel factor.
- După 30 de cadre fără sol, scanarea rămâne fără unități și o spune.
- Cu telemetrie, cadrele ulterioare nu mai sunt încercate: adâncimea este ancorată la metrii telemetriei.

A fi în zece la sută de dimensiunea reală bate a fi greșit cu un factor de o mie; telemetria, acolo unde există, face asta inutil. Nota este afișată în fereastră sub linia de urmărire, ca `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (cu `found on frame N, so the level is scaled by F when it is written` când a venit mai târziu), `no usable ground in the first N frames - sizes are relative, not metres` sau `in metres, from the telemetry's positions`.

## Ajustare de pachet și urme lungi (neconectate) {#bundle-adjustment-and-long-tracks-not-wired-in}

Două piese există pentru un solver viitor pe ferestre și **nu sunt folosite de scaner**:

- **`FeatureTracks`** păstrează identitatea trăsăturilor pe sute de cadre cu urmărire Lucas-Kanade (600 de trăsături, reînsămânțate sub 60%, toleranță înainte-înapoi de 1 px, trăsături noi la 10 px de cele existente), ceea ce are nevoie ajustarea de pachet - potrivirea descriptorilor între cadre consecutive dă doar perechi.
- **`bundle_adjust`** rafinează o fereastră de poziții și puncte împreună cu `scipy.optimize.least_squares` (regiune de încredere, pierdere soft-L1 cu scală de 2 px, un tipar explicit de rarefiere al Jacobianului, camerele fixe restaurate exact). Testat față de adevărul cunoscut în `tests/test_bundle.py`.

`WindowedOdometry` le combină (ferestre de 12 cadre-cheie, o rezolvare la fiecare 3 cadre-cheie, primele două camere fixe, puncte cu eroare peste 6 px aruncate, salturi peste de 6 ori pasul recent refuzate). Docstring-ul său notează că pe materialul real **a prăbușit traseul și a fost mult mai lent** decât urmărirea cadru-cu-cadru, cu libertatea de gabarit (scara) și o bootstrap bazat pe adâncime ca cauze cunoscute, iar o a treia cauză neidentificată. Deci odometria cadru-cu-cadru rămâne implicită; remedierea probabilă notată în cod este un bootstrap cu matrice esențială pe două vederi, cu linia de bază fixată din calibrarea planului solului.
