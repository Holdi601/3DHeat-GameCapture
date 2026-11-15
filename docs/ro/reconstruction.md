---
title: "Reconstrucția nivelului"
nav_order: 6
lang: "ro"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Reconstrucția nivelului din joc {#level-reconstruction-from-gameplay}

Parcurgeți un nivel încet, sau conduceți o pistă, iar scanerul transformă ce a arătat ecranul într-un
`.glb` pe care vizualizatorul 3DHeat îl încarcă drept context sub telemetrie - același contract de
fișier pe care îl scrie exportatorul Unreal. Este pentru cazul în care nimeni nu a exportat harta și
fișierele jocului nu pot fi citite; un export din motor sau din fișierele jocului este exact, acesta
este o estimare.

## Pipeline-ul {#the-pipeline}

```text
 cadre               cadre-cheie          adâncime             poziție              fuziune             rezultat
 ------              -----------          --------             -------              -------             --------
 Windows Graphics -> prag al schimbării -> Depth Anything V2 -> odometrie vizuală -> volum de ocupare -> marching cubes
 Capture, sau un    a imaginii           (ONNX Runtime,        (ORB + PnP), sau     + grila de          -> teren/structură
 fișier video       (adaptiv)            letterboxed)          telemetria Forza,    acoperire (harta    -> culoare pe vârf
                                                                sau o soluție VGGT   live, punctele         -> .glb
                                                                                     slabe)
                    mști HUD / cabină, sfaturi de calitate a cadrului, scara din planul solului
```

| Etapă | Scanare live (`heat3d_capture.ui`) | Offline (`reconstruct`) | Pagina |
|---|---|---|---|
| Cadre | monitor, fereastră sau video, redimensionate la latura cea mai lungă a presetului | video, eșantionat de două ori (planul de rezolvare și intervalul de fuziune) | [Captura](reconstruction-capture.md) |
| Cadre-cheie | păstrate după cât s-a schimbat imaginea, cu pragul adaptat la captură | la fiecare `--fuse-interval` secunde | [Captura](reconstruction-capture.md#keyframes) |
| Măști | `ScreenMask` bazat pe schimbare, apoi `FlowMask` bazat pe flux după 40 de cadre-cheie | `FlowMask` învățat din patru rulări ale videoclipului; nu se aplică solverului | [Captura](reconstruction-capture.md#what-is-not-the-world) |
| Adâncime | model ONNX pe cel mai bun backend GPU | PyTorch Depth Anything V2 Small | [Adâncimea](reconstruction-depth.md) |
| Poziție | odometrie vizuală, sau telemetria Forza exactă | ferestre VGGT lipite într-o singură traiectorie, interpolată | [Poziția](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Scară | înălțimea camerei deasupra solului (1,15 m) o singură dată, sau telemetria | unitățile proprii ale traiectoriei rezolvate | [Poziția](reconstruction-pose.md#scale) |
| Fuziune | ocupare ponderată, voxeli rari; grila de acoperire | la fel | [Fuziunea](reconstruction-fusion-and-texture.md) |
| Rezultat | `.glb`, părți teren/structură, culoare pe vârf, centimetri | la fel | [Rezultatul .glb](glb-output.md) |

Cod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - setările și ritmul unei scanări; `reconstruct.py` - cadre-cheie transformate în
geometrie; `offline.py` - calea offline), cu etapele în `capture/`, `depth/`, `pose/`, `fusion/`
și `geometry/`.

## De unde vine precizia {#where-accuracy-comes-from}

Adâncimea monoculară este corectă doar până la o scară necunoscută - o fotografie a unei camere și a
unei case de păpuși sunt aceeași imagine. Așa că rețelei i se lasă ce face bine (forma relativă,
muchiile, structurile subțiri), iar scara și traseul camerei vin de la ceva care le cunoaște:

| Joc | Traseul camerei | Scara |
|---|---|---|
| Forza Horizon / Motorsport cu telemetria pornită | exact, din Data Out, interpolat la momentul captării fiecărui cadru | exactă: adâncimea este ancorată prin triangularea trăsăturilor între două poziții cunoscute |
| Orice altceva, live | odometrie vizuală, înlănțuită cadru cu cadru | fixată o dată, dintr-o înălțime presupusă a camerei deasupra solului |
| O înregistrare, offline | VGGT, rezolvat pe ferestre care se suprapun | unitățile rezolvării (nu sunt metrice) |

Singurul număr pe care scanerul îl primește ca informație, în loc să îl măsoare, este **câmpul vizual
orizontal** al jocului (90 de grade implicit în fereastră; jocurile de curse sunt mai aproape de 65).
Prea îngust, și nivelul se reconstruiește mai adânc decât este; prea larg, și se turtește.

## Spunerea utilizatorului din timp {#telling-the-user-early}

O scanare este un act fizic - cineva parcurge un nivel timp de câteva minute - iar eșecul costisitor
este să termini plimbarea și să descoperi că nu a folosit la nimic. Așa că fereastra măsoară debitul
adâncimii pe acest calculator înainte ca ceva să poată porni și spune cum va fi scanarea
([Rularea](runtime.md#what-to-expect-from-this-machine)); în timpul scanării arată o hartă a
acoperirii cu punctele slabe numerotate, starea urmăririi, o bară a vitezei de mers, o bară a
clarității și câte o instrucțiune pe rând, atât în fereastră, cât și într-o suprapunere transparentă
peste joc ([Fereastra de scanare](reconstruction-scan-ui.md)).

## Măsurat pe adevăr de referință sintetic {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` randează o cameră de 12 x 8 m (4 m înălțime) dintr-o traiectorie cunoscută a
camerei, cu adâncime analitică (nu de la rețea), și o reconstruiește la voxeli de 0,2 m. Verifică faptul
că peste 90% din cadre sunt plasate, că eroarea medie a traseului este sub 0,35 m (cea mai mare sub 1 m),
că distanța parcursă este în 10% față de adevăr, că lățimea camerei iese corect cu o abatere de 1,5 m,
că peste 75% din suprafața pereților se află la mai puțin de 0,45 m de un perete real, că o plimbare în
stil de recunoaștere obține o acoperire clar mai bună decât mersul drept înainte, și că o scenă fără
trăsături este refuzată în loc să fie inventată. Adâncimea analitică izolează poziția, scara și
fuziunea de rețea; cum se descurcă rețeaua pe joc real este o întrebare separată, pe care nicio scenă
sintetică nu o poate răspunde. `tests/test_track_width.py` verifică faptul că un tur condus decentrat
pe un drum de lățime cunoscută reconstruiește lățimea drumului, nu doar linia condusă.

## Pagini {#pages}

- [Fereastra de scanare](reconstruction-scan-ui.md) - fiecare comandă, tastă rapidă și element de suprapunere
- [Captura, măștile și calitatea cadrului](reconstruction-capture.md)
- [Adâncimea](reconstruction-depth.md)
- [Poziția camerei și scara](reconstruction-pose.md)
- [Fuziunea, acoperirea și culoarea](reconstruction-fusion-and-texture.md)
- [Rezultatul .glb](glb-output.md)
- [Reconstrucția offline](reconstruction-offline.md)
