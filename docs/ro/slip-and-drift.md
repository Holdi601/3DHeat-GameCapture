---
title: "Alunecare, derapaj și canale derivate"
nav_order: 8
lang: "ro"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Alunecare, derapaj și canale derivate {#slip-drift-and-derived-channels}

Analiza controlului mașinii din fila Race analysis a vizualizatorului (*Analiză de cursă*) cere aceleași câteva mărimi de la fiecare joc: cât alunecă fiecare anvelopă, cât de mult se îndreaptă mașina în altă parte decât unde merge (unghiul de derapaj), dacă este în aer, dacă este pe sol afânat. Jocurile le trimit în forme foarte diferite, sau deloc. Înregistratoarele de aici scriu ce trimite fiecare joc, sub nume canonice, plus o notă `meta.slip` care spune ce înseamnă numerele de alunecare; apoi vizualizatorul deduce ce lipsește, o singură dată, când încarcă o tură. **Valoarea proprie a unui joc învinge întotdeauna una derivată.**

## Ce scriu înregistratoarele {#what-the-recorders-write}

| Joc | Canale de alunecare | `meta.slip` | Intrări pentru unghiul de derapaj |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` pe fiecare roată, cum sunt trimise | `peak` (scris de înregistrator; cititorul `.tele.gz` al vizualizatorului pune la fel) | `latVel`, `longVel` din viteza în cadrul mașinii |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` din viteza în cadrul mașinii |
| EA SPORTS WRC, jocurile DiRT | niciunul; în schimb `wheelSurfaceSpeed` pe fiecare roată | `null` | `latVel`, `longVel` = viteza lumii proiectată pe axele mașinii |
| Richard Burns Rally | niciunul; nici viteze ale roților | niciunul | `latVel`, `longVel` = derapajul și înaintarea proprii ale mașinii |
| BeamNG.drive | niciunul; `wheelSurfaceSpeed` și `wheelSpeed` pe fiecare roată | niciunul | `latVel`, `longVel` = viteza lumii proiectată pe axele mașinii |
| Trackmania | `slipIndex` pe fiecare roată (o măsură de alunecare 0..1) | `index` | `latVel` (viteza laterală), `longVel` (viteza frontală) |
| iRacing | niciunul (nu este înregistrat) | niciunul | `yaw` și traseul, `yawRate` |

Valorile `meta.slip` sunt definite în [Fișierul heat3d-lap](lap-format.md): `peak` (normalizată, astfel încât peste 1 anvelopa își pierde aderența), `scaled` (o alunecare fizică împărțită la un vârf tipic de asfalt), `physical` (o fracție și radiani), `index` (o măsură de alunecare 0..1).

### De ce alunecarea Kunos este scalată {#why-kunos-slip-is-scaled}

Alunecarea Forza este normalizată astfel încât 1 este marginea aderenței; ce normalizează ea împotriva nu este documentat. Kunos trimite raportul fizic de alunecare (o fracție) și unghiul de alunecare (radiani). Împărțirea la un vârf tipic de asfalt - 0,12 pentru raport și 0,14 rad (aproximativ 8 grade) pentru unghi - face ca „peste 1 înseamnă alunecare" să fie aproximativ adevărat pentru ambele familii, ceea ce păstrează o singură citire pentru afișajele vizualizatorului. Este o aproximare: vârfurile reale variază după anvelopă și suprafață, de aceea valorile brute sunt păstrate lângă cele scalate și de ce vizualizatorul măsoară unde începe să scape aderența fiecărei mașini chiar din ture.

## Ce deduce vizualizatorul (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Acestea rulează în vizualizator (`src/race/derive.ts` din vizualizatorul 3DHeat), nu în acest depozit.

### Unghiul de derapaj, `bodySlip` {#drift-angle-bodyslip}

- **Din viteza în cadrul mașinii** când sunt prezente `latVel` și `longVel`: `atan2(latVel, |longVel|)`, iar 0 sub 3 m/s (o mașină oprită lateral nu derapează).
  Semnul său urmează viteza laterală a jocului, al cărei sens este documentat în ambele sensuri pentru unele jocuri - citiți mărimea.
- **Altfel din orientarea față de traseu**: direcția de mers este luată din poziții la aproximativ 2 m de o parte și de alta a fiecărui eșantion (`atan2(dx, dz)`); `yaw`-ul jocului este potrivit pe ea cu un semn și un decalaj (fiecare joc are propriul zero și propriul sens de rotație) folosind eșantioane peste 10 m/s, și este crezut doar dacă apoi se potrivește strâns (răspândire circulară de cel mult 0,05, cel puțin 20 de eșantioane). Unghiul de derapaj este diferența, 0 sub 3 m/s.

### Raportul de alunecare din roți {#slip-ratio-from-the-wheels}

Unde o tură nu are `slipRatio.*`, dar are viteze ale roților, raportul de alunecare este `(roată - mașină) / mașină` pe fiecare roată, din:

- `wheelSurfaceSpeed.*` (viteza punctului de contact, m/s) direct, când este trimisă (EA WRC, DiRT, BeamNG);
- altfel `wheelSpeed.*` (rotație, rad/s) înmulțit cu o **rază de rulare măsurată pe tură**: mediana `speed / |omega|` peste eșantioanele unde mașina merge liber în linie dreaptă (peste 10 m/s, nu în aer, accelerație cu pedala sub 0,3, frână sub 0,05, accelerație longitudinală sub 3 m/s²); cu mai puțin de 20 de asemenea eșantioane, toate eșantioanele peste 10 m/s. O rază în afara intervalului 0,1-1 m este respinsă.

Doar când toate cele patru roți pot fi derivate; `meta.slip` al turei devine atunci `physical`. Sub 3 m/s alunecarea este 0.

### În aer {#airborne}

`airborne` este 1 acolo unde fiecare roată este de la sol, judecat după primul dintre acestea pe care îl are tura pentru toate cele patru roți:

1. `groundContact.*` (BeamNG): nicio roată peste 0,5;
2. `wheelLoad.*` (jocurile AC, RBR, BeamNG): nicio roată peste 5% din sarcina ei mediană;
3. `suspension.*` (0..1 din cursă): nicio roată peste 0,02, adică toate complet extinse.

Un singur eșantion izolat în aer este șters. Trackmania scrie singur `airborne`.

### Sol afânat {#loose-ground}

Unde o tură are `surfaceRumble.*` (Forza), `loose` este 1 acolo unde cel puțin două roți raportează zgomot timp de cel puțin o treime de secundă, cu golurile mai scurte de o secundă unite (un petec neted pe un drum de pietriș este tot drumul de pietriș). Trackmania scrie singur `loose` din materialele de sol ale roților.

### Viteza de rotație în jurul verticalei {#yaw-rate}

Unde o tură are `yaw`, dar nu `yawRate`, aceasta este schimbarea yaw-ului peste eșantioanele vecine.

## Ce derivă singure înregistratoarele {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): fiecare înregistrator, cu excepția Forza (care o trimite), o scrie din `suspensionM.*` ca poziția în intervalul folosit de tura aceasta (minim până la maxim). Este pentru barele de suspensie ale mașinii și pentru a observa o roată care atârnă în aer; nu este o fracție absolută a cursei.
- **`steer`** pentru jocurile Kunos, scalat pe tură (vezi [Jocurile Assetto Corsa](telemetry-assetto-corsa.md)).
- **Accelerațiile** pentru BeamNG, din schimbarea vitezei lumii ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** și axa „sus" pentru Richard Burns Rally, din poziții ([Jocuri de raliu](telemetry-rally.md)).

## Lateralitate {#handedness}

Acolo unde lumea unui joc este levogiră - ca cea a Forza - un traseu iese oglindit într-un vizualizator dreptgiriu; direcția și suspensia proprie ale turelor o arată. Înregistratoarele nu schimbă lateralitatea: o lume cu Z în sus (BeamNG) este rotită la Y în sus printr-o rotație, care o păstrează, iar totul este scris cum a fost trimis.
