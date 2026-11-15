---
title: "Kufizimet dhe verifikimi"
nav_order: 9
lang: "sq"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Kufizimet dhe çfarë është verifikuar {#limits-and-what-is-verified}

Një listë e ndershme: çfarë nuk bëjnë mjetet dhe çfarë nuk është kontrolluar me një lojë që po xhiron.

## Telemetria {#telemetry}

| Regjistruesi | Gjendja |
|---|---|
| Forza | Ndërtuar sipas dokumentacionit zyrtar të Data Out; struktura zbulohet nga vetë paketat. Lexuesi `.tele.gz` i FH Companion në shikues është kontrolluar me xhiro reale. |
| AC, ACC, AC EVO, AC Rally | Provuar me faqe sintetike të ndërtuara sipas strukturave të publikuara. **Ende nuk është provuar me lojërat reale.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Provuar me paketa të ndërtuara sipas strukturave të dokumentuara. **Ende nuk është provuar me lojërat reale.** Boshtet, qëndrimi dhe njësitë e shpejtësisë të RBR nuk janë të dokumentuara dhe trajtohen nga të dhënat. |
| BeamNG.drive | Regjistruesi është provuar me paketa të ndërtuara nga struct-i i modit. **Moda nuk është provuar në lojë.** |
| Trackmania | Lexuesi i CSV-së në shikues është provuar. **Shtesa nuk është provuar në lojë.** Ngarkohet vetëm në modalitetin e zhvilluesit të Openplanet. |
| iRacing | Lexuesi `.ibt` i shikuesit është provuar me një skedar sintetik. |

Kufizime të tjera të telemetrisë:

- Normalizimi i rrëshqitjes në Forza nuk është i dokumentuar; rrëshqitja e Kunos shkallëzohet me një
  kulm tipik të asfaltit, pra është një përafrim.
- Kahu i disa akseve anësore në kornizën e makinës (Kunos, DiRT) dokumentohet në të dyja mënyrat; madhësia e
  këndit të drifit është e besueshme, shenja e tij jo.
- Asnjëra nga lojërat e rally-t nuk dërgon rrëshqitjen e gomave; ajo llogaritet në shikues. RBR nuk dërgon shpejtësitë e rrotave.
- Sipërfaqja e një etape rally shkruhet vetëm kur jepet `--surface`; përndryshe skedari nuk
  tregon asnjë dhe shikuesi e nxjerr vetë (emri i etapës ose i eventit, pastaj stili i drejtimit, si parazgjedhje e lirshme).
- Zbulimi i xhiros pa numërues xhirosh (AC EVO, AC Rally, BeamNG) e merr si vijë pikën ku filloi
  regjistrimi, ndaj filloni regjistrimin te vija e nisjes.
- Një rivendosje e mjetit në BeamNG e mbyll xhiron e hapur në atë çast: ajo shkruhet si ecje e pjesshme kur
  ka mbuluar distancën minimale (300 m) dhe hidhet poshtë përndryshe.
- `route` ruan çdo 2 sekonda a më shumë gjatë drejtimit; një rrëzim ose një proces i vrarë humb më së shumti
  pozicionet që nga ruajtja e fundit.
- Forza Horizon nuk dërgon emrin e pistës, ndaj skedarët e xhiros së Forza kanë `"track": null`; Forza Motorsport
  (2023) dërgon vetëm një numër, që ruhet si `lap.trackOrdinal`.

## Rindërtimi {#reconstruction}

- **Thellësia vlerësohet, nuk lexohet.** Kufiri i të gjithë qasjes dhe çmimi i të mos prekurit
  kurrë procesin e lojës.
- **Këndi i shikimit supozohet, nuk matet.** Nëse është shumë i ngushtë, niveli rindërtohet më i thellë se
  sa është.
- **Shkalla globale** vjen nga një lartësi e supozuar e kamerës (1.15 m në dritare), ose nga
  telemetria. Matet te kuadri kyç i parë; kur ai nuk ka tokë të përdorshme, provohen kuadrot kyç
  pasues (deri në 30 kuadro), dhe një shkallë e gjetur më vonë zbatohet në të gjithë nivelin
  kur ai shkruhet. Rreshti "Size:" i dritares tregon çfarë ndodhi; nëse nuk gjendet fare tokë,
  skanimi mbetet pa njësi. Në atë rast madhësia e voxel-it është në njësitë e kuadrit të parë, ndaj
  madhësia e tij në metra ndryshon nga cilësimi. Rindërtimet offline janë në njësitë e vetë zgjidhjes.
- **Mbyllja e ciklit është e fikur** dhe nuk është graf pozicionesh kur ndizet në kod; zhvendosja kufizohet vetëm nga
  cilësia e ndjekjes nga kuadri në kuadër.
- **Rregullimi i bundle-it me dritare ekziston, por nuk është i lidhur**; u shemb në pamje reale.
- **Sipërfaqja është zënie e peshuar, jo TSDF**: strukturat e holla dhe hapësira e lirë dalin më keq se
  me një TSDF.
- **Nuk ka atlas teksture.** Ngjyra është për secilën kulm (`COLOR_0`), e përzier nga 4 pamjet më të mira midis
  160 kuadrove të mbajtur. Testi i errësimit është i përafërt: provon kundrejt kulmeve të vetë rrjetës në një
  buffer thellësie 2 pikselësh, ndaj një errësues që rrjeta nuk e përmban (një makinë që kalon) nuk kapet.
- **Uji nuk etiketohet kurrë**; gjithçka është tokë ose strukturë.
- **Zgjidhja feed-forward nuk është live**: i duhet më parë regjistrimi. Rizgjidhja adaptive e
  pjesëve të vështira nuk është ndërtuar.
- **Pozicionet nga telemetria** e vendosin kamerën te makina (zhvendosja e një kamere ndjekëse nuk dihet). Pozicionet
  merren siç i dërgon Forza (Y lart, si në skedarët e xhiros); kahet e yaw, pitch dhe roll
  u lexuan nga xhiro të regjistruara (drejtimi i ecjes, pjerrësia, anët e cilës ngjeshet pezullimi),
  jo nga kamera e lojës që xhiron.
- Mbivendosja nuk mund të vizatojë mbi **ekran të plotë ekskluziv**; përdorni dritare pa kornizë (borderless windowed).
- Tastet globale, mbivendosja që lë klikimet të kalojnë dhe kapja live janë **vetëm për Windows**.
- Mbyllja e dritares nuk ofron të ruajë.

## Çfarë matet {#what-is-measured}

- `tests/test_accuracy.py`: një dhomë sintetike me rrugë të njohur dhe thellësi analitike - kuadrot e vendosura,
  gabimi i rrugës, distanca e ecur, madhësia e dhomës, sipërfaqja te muret ([Rindërtimi i nivelit](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: një rrugë me gjerësi të njohur e drejtuar jashtë qendrës e rindërton gjerësinë e saj.
- `tests/test_track_scale.py`: nxjerrja e sipërfaqes në shkallë pistë garash, memorie proporcionale me atë që
  u skanua, blloqe që bashkohen në një sipërfaqe të vetme.
- `tests/test_glb.py` plus testet e vetë shikuesit: kontrata `.glb` nga të dyja anët.
- Se si ia del rrjeti i thellësisë në lojë reale nuk e përgjigjet dot një skenë sintetike, dhe
  nuk matet nga paketa e testeve.
