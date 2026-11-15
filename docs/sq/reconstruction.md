---
title: "Rindërtimi i nivelit"
nav_order: 6
lang: "sq"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rindërtimi i nivelit nga lojë e luajtur {#level-reconstruction-from-gameplay}

Ec ngadalë nëpër një nivel, ose vozit një pistë, dhe skaneri e kthen atë që tregoi ekrani në një
`.glb` që shikuesi 3DHeat e ngarkon si kontekst nën telemetri - e njëjta kontratë skedari
që shkruan eksportuesi i Unreal. Është për rastin kur askush nuk e eksportoi hartën dhe skedarët
e lojës nuk lexohen; një eksport i motorit ose i skedarëve të lojës është i saktë, ky është një vlerësim.

## Rrjedha e punës {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Faza | Skanim i drejtpërdrejtë (`heat3d_capture.ui`) | Offline (`reconstruct`) | Faqja |
|---|---|---|---|
| Kuadrot | monitor, dritare ose video, e zvogëluar në anën më të gjatë të paracaktimit | video, e marrë dy herë (plani i zgjidhjes dhe intervali i bashkimit) | [Kapja](reconstruction-capture.md) |
| Kuadrot kyç | mbahen sipas sa ndryshoi fotoja, pragu i përshtatur me kapjen | çdo `--fuse-interval` sekonda | [Kapja](reconstruction-capture.md#keyframes) |
| Maskat | `ScreenMask` sipas ndryshimit, pastaj `FlowMask` sipas rrjedhës pas 40 kuadrove kyç | `FlowMask` i mësuar nga katër kalime të videos; nuk zbatohet te zgjidhësi | [Kapja](reconstruction-capture.md#what-is-not-the-world) |
| Thellësia | model ONNX në prapavijën më të mirë të GPU-së | PyTorch Depth Anything V2 Small | [Thellësia](reconstruction-depth.md) |
| Poza | odometri vizuale, ose telemetri e saktë e Forzës | dritare VGGT të qepura në një shteg të vetëm, të interpoluara | [Poza](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Shkalla | lartësia e kamerës mbi tokë (1.15 m) një herë, ose telemetria | njësitë e vetë shtegut të zgjidhur | [Poza](reconstruction-pose.md#scale) |
| Bashkimi | zënie e peshuar, voksela të rrallë; rrjetë mbulimi | e njëjta | [Bashkimi](reconstruction-fusion-and-texture.md) |
| Dalja | `.glb`, pjesë ground/structure, ngjyrë për çdo kulm, centimetra | e njëjta | [Dalja .glb](glb-output.md) |

Kodi: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - cilësimet dhe ritmi i një skanimi; `reconstruct.py` - kuadrot kyç në gjeometri;
`offline.py` - rruga offline), me fazat në `capture/`, `depth/`, `pose/`, `fusion/`
dhe `geometry/`.

## Nga vjen saktësia {#where-accuracy-comes-from}

Thellësia monokulare është e saktë vetëm deri në një shkallë të panjohur - një foto e një dhome dhe një e një shtëpize kukullash
janë e njëjta foto. Ndaj rrjetit i lihet ajo që e bën mirë (forma relative, skajet,
struktura e hollë), kurse shkalla dhe shtegu i kamerës vijnë nga diku që i di:

| Loja | Shtegu i kamerës | Shkalla |
|---|---|---|
| Forza Horizon / Motorsport me telemetrinë ndezur | i saktë, nga Data Out, i interpoluar në kohën e kapjes së çdo kuadri | e saktë: thellësia ankorohet duke triangulizuar veçori mes dy pozash të njohura |
| Çdo gjë tjetër, drejtpërdrejt | odometri vizuale, e vargëzuar nga kuadri në kuadër | fiksohet një herë nga një lartësi e supozuar e kamerës mbi tokë |
| Një regjistrim, offline | VGGT, i zgjidhur mbi dritare që mbivendosen | njësitë e vetë zgjidhjes (jo metrike) |

Numri i vetëm që skanerit i thuhet në vend që ta masë është **këndi horizontal i shikimit**
i lojës (90 gradë si parazgjedhje në dritare; lojërat e garave janë më afër 65). Shumë i ngushtë dhe
niveli rindërtohet më i thellë nga sa është; shumë i gjerë dhe sheshohet.

## Njoftimi i përdoruesit herët {#telling-the-user-early}

Një skanim është një veprim fizik - dikush ecën nëpër një nivel për disa minuta - dhe dështimi i kushtueshëm
është ta mbarosh ecjen dhe të zbulosh se nuk ishte e mirë. Ndaj dritarja mat
përmasën e thellësisë së kësaj makine para se të nisë ndonjë gjë dhe thotë si do të jetë skanimi
([Runtime](runtime.md#what-to-expect-from-this-machine)); gjatë skanimit tregon një hartë
mbulimi me pika të dobëta të numëruara, shëndetin e gjurmimit, një shirit shpejtësie ecjeje, një shirit mprehtësie dhe një
udhëzim njëherësh, në dritare dhe në një mbulesë mbi lojë ku mund të klikosh përmes saj
([Dritarja e skanimit](reconstruction-scan-ui.md)).

## Matur mbi të vërtetën sintetike {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` vizaton një dhomë 12 x 8 m (4 m e lartë) nga një shteg i njohur kamere, me thellësi
analitike (jo nga rrjeti), dhe e rindërton me voksela 0.2 m. Ai pohon se më shumë se
90% e kuadrove vendosen, gabimi mesatar i shtegut është nën 0.35 m (më i keqi nën 1 m), distanca
e ecur është brenda 10% të së vërtetës, dhoma del e gjerë sa duhet brenda 1.5 m, mbi
75% e sipërfaqes së mureve shtrihet brenda 0.45 m nga një mur i vërtetë, një ecje në stilin e studimit merr
mbulim dukshëm më të mirë se ecja drejt përpara, dhe një skenë pa veçori refuzohet në vend se të shpiket. Thellësia analitike ndan pozën, shkallën dhe
bashkimin nga rrjeti; se si ia del rrjeti në lojë të vërtetë është një pyetje tjetër që asnjë
skenë sintetike nuk e përgjigjet. `tests/test_track_width.py` kontrollon që një xhiro e vozitur jashtë qendrës në një
rrugë me gjerësi të njohur rindërton gjerësinë e rrugës, jo vetëm vijën e vozitur.

## Faqet {#pages}

- [Dritarja e skanimit](reconstruction-scan-ui.md) - çdo kontroll, hotkey dhe element i mbulesës
- [Kapja, maskat dhe cilësia e kuadrove](reconstruction-capture.md)
- [Thellësia](reconstruction-depth.md)
- [Poza e kamerës dhe shkalla](reconstruction-pose.md)
- [Bashkimi, mbulimi dhe ngjyra](reconstruction-fusion-and-texture.md)
- [Dalja .glb](glb-output.md)
- [Rindërtimi offline](reconstruction-offline.md)
