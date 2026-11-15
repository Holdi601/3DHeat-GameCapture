---
title: "Rezultatul .glb"
nav_order: 6
lang: "ro"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# Rezultatul .glb {#the-glb-output}

O reconstrucție este scrisă ca un fișier glTF 2.0 binar (`.glb`) pe care vizualizatorul 3DHeat
îl încarcă prin panoul Fundal / nivel, fără tratament special - același contract pe care îl scrie
exportatorul Unreal. Cod: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

Este scris manual, nu printr-o bibliotecă glTF: rezultatul este un subset restrâns (un singur
buffer, strâns împachetat, fără animație, fără skinning), iar o dependență care poate scrie tot
glTF ar aduce cu ea propriile diferențe de versiune pentru câteva sute de linii.

## Ce este în fișierul unei scanări {#what-is-in-a-scans-file}

| Parte (numele nodului și al mesh-ului) | Conținut |
|---|---|
| `ground:<name>` | triunghiurile aflate la mai puțin de 35 de grade față de orientarea în sus |
| `structure:<name>` | tot restul |

`<name>` este numele fișierului fără extensie când se salvează din fereastră, sau numele video-ului
pentru `reconstruct`. O parte fără triunghiuri este lăsată afară. Nicio parte `water:` nu este scrisă
vreodată de o scanare. `asset.generator` este `heat3d-capture-scan`.

## Contractul {#the-contract}

- **Un nod pentru fiecare parte**, numit cu eticheta părții; mesh-ul repetă numele. Vizualizatorul
  citește mai întâi numele *nodului*, deci denumirea doar a mesh-urilor ar pierde clasificarea.
- Eticheta este `<class>:<name>`, cu clasa `ground`, `structure` sau `water` - prefixul pe care
  vizualizatorul îl potrivește (`^(ground|structure|water)\s*[:|]`) ca să ia clasa așa cum este scrisă,
  în loc să o ghicească din geometrie. Terenul se randează plin, structurile aproape transparent.
- **Coordonatele sunt în spațiul vizualizatorului**: Y în sus, sistem dreptaci, și **scalate în
  centimetri** (metri x 100), ca să se potrivească cu exportatorul Unreal, astfel încât o captură și
  un export din motor ale aceluiași loc se încarcă la aceeași mărime, cu aceleași valori implicite
  ale camerei. Câmpul de nivel superior `extras.unit_metres` al fișierului este `0.01` (o unitate
  este un centimetru), astfel încât un cititor care lucrează în metri, precum [`locate`](locate.md),
  îl preia la mărimea lui reală. O scanare plasată de telemetria Forza face excepție la sistemul de
  coordonate: rămâne în lumea jocului, cu Y în sus și sistem stângaci, exact cum sunt fișierele de
  tur, ca turele înregistrate peste ea să aterizeze pe ea. Când scara unei scanări a fost găsită pe
  un cadru-cheie ulterior ([Scara](reconstruction-pose.md#scale)), acel factor este inclus în scara
  scrisă.
- `COLOR_0` este citit de vizualizator, care umbrește terenul cu el când comutatorul *Culoare
  capturată* din panoul Fundal / nivel este pornit (oprit implicit).
- O scanare cu puncte marcate manual primește lângă ea un fișier `<name>.marks.json`; vezi
  [Salvarea](reconstruction-scan-ui.md#saving).
- Pentru fiecare primitivă: `POSITION` (VEC3 float, cu `min` și `max`, din care vizualizatorul își
  încadrează camera), `NORMAL` (VEC3 float), `COLOR_0` opțional (VEC3 float, 0..1), `TEXCOORD_0`
  opțional; indicii ca 16 biți când fiecare index este sub 65.536, altfel 32 de biți; mod triunghiuri.
- Fiecare buffer view începe aliniat la 4 octeți; porțiunea JSON este completată cu spații, iar cea
  BIN cu zerouri, până la 4 octeți.

## Verificări înainte de scriere {#checks-before-writing}

Fiecare parte este validată și refuzată cu un mesaj care o numește dacă nu are vârfuri, dacă numărul
de indici nu formează triunghiuri întregi, dacă un index este în afara intervalului sau negativ, dacă
pozițiile nu sunt finite sau dacă normalele ori culorile nu se potrivesc cu numărul de vârfuri.
Normalele se calculează când lipsesc, **ponderate cu aria** (marching cubes lasă așchii lângă fețele
mari, iar o medie neponderată lasă triunghiurile mici să învingă fața pe care stau); un vârf degenerat
primește „în sus”. Scrierea fără nicio parte este o eroare.

Exportul nu returnează nimic - iar fereastra afișează „Nothing to save” - când volumul nu produce
nicio suprafață, în loc să scrie un fișier gol care ar părea o scanare reușită.

## Texturi {#textures}

Scriitorul acceptă o textură PNG de culoare de bază pentru fiecare parte (cu UV, cu două fețe, cu
material nemetalic, complet rugos). Scanările nu o folosesc; ele au culoare pe vârf. Vezi
[culoarea](reconstruction-fusion-and-texture.md#colour).

## Nivelul de referință {#the-reference-level}

`geometry/reference.py` construiește un nivel sintetic de mărime exact cunoscută, prin același
scriitor: un teren subdivizat de 400 m, trei clădiri de 20 x 20 x 12 m și un iaz de 50 m, cu 1,5 m
sub nivelul solului, fiecare clasă într-o culoare plată distinctă. Testele vizualizatorului îl
generează și îl citesc cu analizorul real al vizualizatorului, astfel încât formatul fișierului
rămâne testat în ambele părți, fără joc și fără hardware de captură.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
