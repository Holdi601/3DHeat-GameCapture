---
title: "Limite și verificare"
nav_order: 9
lang: "ro"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Limite și ce este verificat {#limits-and-what-is-verified}

O listă sinceră: ce nu fac instrumentele și ce nu a fost verificat pe un joc care rulează.

## Telemetrie {#telemetry}

| Înregistrator | Stare |
|---|---|
| Forza | Construit pe documentația oficială Data Out; așezarea este detectată din pachetele însele. Cititorul `.tele.gz` FH Companion al vizualizatorului a fost verificat pe tururi reale. |
| AC, ACC, AC EVO, AC Rally | Testat pe pagini sintetice construite din așezările publicate. **Nerulat încă pe jocurile reale.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testat pe pachete construite din așezările documentate. **Nerulat încă pe jocurile reale.** Axele, atitudinea și unitățile de viteză ale RBR nu sunt documentate și sunt tratate din date. |
| BeamNG.drive | Înregistratorul este testat pe pachete construite din structura modului. **Modul nu a fost rulat în joc.** |
| Trackmania | Cititorul CSV al vizualizatorului este testat. **Pluginul nu a fost rulat în joc.** Se încarcă doar în modul dezvoltator al Openplanet. |
| iRacing | Cititorul `.ibt` al vizualizatorului este testat pe un fișier sintetic. |

Alte limite ale telemetriei:

- Normalizarea alunecării Forza nu este documentată; alunecarea Kunos este scalată după un vârf tipic de asfalt, o
  aproximare.
- Sensul unor axe laterale ale cadrului mașinii (Kunos, DiRT) este documentat în ambele sensuri; mărimea unghiului de
  derapaj este sigură, semnul ei nu.
- Niciunul dintre jocurile de raliu nu trimite alunecarea pneurilor; ea este derivată în vizualizator. RBR nu trimite vitezele
  roților.
- Suprafața unei probe de raliu este scrisă doar când este dat `--surface`; altfel fișierul nu numește niciuna, iar
  vizualizatorul o deduce (numele probei sau al evenimentului, apoi stilul de condus, lejer în mod implicit).
- Detecția tururilor fără contor de ture (AC EVO, AC Rally, BeamNG) folosește punctul de unde a început înregistrarea drept
  linie, deci pornește înregistrarea la linia de start.
- Un reset de vehicul în BeamNG închide turul deschis în acel moment: este scris ca un parcurs parțial când a acoperit distanța
  minimă (300 m), și aruncat altfel.
- `route` salvează aproximativ la fiecare 2 secunde în timp ce conduci; o cădere sau un proces oprit pierde cel mult pozițiile
  de după ultima salvare.
- Forza Horizon nu trimite numele pistei, deci fișierele de tur Forza au `"track": null`; Forza Motorsport (2023) trimite doar
  un număr, păstrat ca `lap.trackOrdinal`.

## Reconstrucție {#reconstruction}

- **Adâncimea este estimată, nu citită.** Plafonul întregii abordări și prețul de a nu atinge niciodată procesul jocului.
- **Câmpul vizual este presupus, nu măsurat.** Prea îngust, iar nivelul se reconstruiește mai adânc decât este.
- **Scara globală** vine dintr-o înălțime presupusă a camerei (1,15 m în fereastră) sau din telemetrie. Este măsurată pe primul
  cadru-cheie; când acesta nu are sol utilizabil, sunt încercate următoarele cadre-cheie (până la 30 de cadre), iar o scară găsită
  mai târziu este aplicată întregului nivel la scriere. Linia „Size:” a ferestrei spune ce s-a întâmplat; când nu se găsește deloc sol,
  scanarea rămâne fără unitate. Dimensiunea voxelului este în unitățile primului cadru în acest caz, deci dimensiunea lui în metri
  diferă de setare. Reconstrucțiile offline sunt în unitățile soluției.
- **Închiderea buclelor este dezactivată** și nu este un graf de poziții când este pornită în cod; deriva este limitată doar de
  calitatea urmăririi de la cadru la cadru.
- **Ajustarea de pachete pe ferestre există, dar nu este conectată**; s-a prăbușit pe filmări reale.
- **Suprafața este o ocupare ponderată, nu un TSDF**: structurile subțiri și spațiul liber sunt mai slabe decât le-ar da un TSDF.
- **Nicio hartă de texturi.** Culoarea este pe vârf (`COLOR_0`), amestecată din cele 4 cele mai bune vederi dintre 160 de cadre
  păstrate. Testul de ocluzie este grosier: verifică față de vârfurile proprii ale plasei, într-un tampon de adâncime de 2 pixeli,
  deci un obstacol pe care plasa nu îl conține (o mașină care trece) nu este prins.
- **Apa nu este etichetată niciodată**; totul este sol sau structură.
- **Rezolvarea feed-forward nu este live**: are nevoie mai întâi de înregistrare. Re-rezolvarea adaptivă a secțiunilor dificile nu este
  construită.
- **Pozele din telemetrie** plasează camera la mașină (decalajul unei camere din spate nu este cunoscut). Pozițiile sunt luate așa
  cum le trimite Forza (Y în sus, ca în fișierele de tur); sensurile yaw-ului, pitch-ului și roll-ului au fost citite din tururi
  înregistrate (sensul de deplasare, panta, care parte a suspensiei se comprimă), nu din camera jocului în rulare.
- Suprapunerea nu poate desena peste **ecranul complet** exclusiv; folosește fereastră fără chenar, pe tot ecranul.
- Tastele globale, suprapunerea prin care se poate da clic și captura live sunt doar **pe Windows**.
- Închiderea ferestrei nu propune salvarea.

## Ce este măsurat {#what-is-measured}

- `tests/test_accuracy.py`: o cameră sintetică cu o cale cunoscută și adâncime analitică - cadre plasate, eroarea căii, distanța
  parcursă, dimensiunea camerei, suprafața pe pereți ([Reconstrucția nivelului](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: un drum de lățime cunoscută parcurs decentrat își reconstruiește lățimea.
- `tests/test_track_scale.py`: extragerea suprafeței la scara unui circuit de curse, memoria proporțională cu ce a fost scanat, blocuri
  care se unesc într-o singură suprafață.
- `tests/test_glb.py` plus testele proprii ale vizualizatorului: contractul `.glb` din ambele părți.
- Cât de bine se descurcă rețeaua de adâncime pe jocul real nu este ceva ce poate răspunde o scenă sintetică și nu este măsurat de
  suita de teste.
