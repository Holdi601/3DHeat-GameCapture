---
title: Begrænsninger og verifikation
nav_order: 9
lang: "da"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Begrænsninger og hvad der er verificeret {#limits-and-what-is-verified}

En ærlig liste: hvad værktøjerne ikke gør, og hvad der ikke er kontrolleret mod et kørende spil.

## Telemetri {#telemetry}

| Optager | Status |
|---|---|
| Forza | Bygget på den officielle Data Out-dokumentation; layoutet findes ud fra selve pakkerne. Viewer'ens FH Companion `.tele.gz`-læser er kontrolleret på rigtige omgange. |
| AC, ACC, AC EVO, AC Rally | Testet på syntetiske sider bygget ud fra de offentliggjorte layouts. **Endnu ikke kørt mod de levende spil.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testet på pakker bygget ud fra de dokumenterede layouts. **Endnu ikke kørt mod de levende spil.** RBR's akser, holdning og hastighedsenheder er udokumenterede og håndteres ud fra dataene. |
| BeamNG.drive | Optageren er testet på pakker bygget ud fra modpakkens struct. **Modpakken er ikke kørt i spillet.** |
| Trackmania | Viewer'ens læser af CSV'en er testet. **Pluginet er ikke kørt i spillet.** Det indlæses kun i Openplanets udviklertilstand. |
| iRacing | Viewer'ens `.ibt`-læser er testet på en syntetisk fil. |

Andre telemetribegrænsninger:

- Forzas normalisering af slip er udokumenteret; Kunos slip skaleres med en typisk asfalttop, en tilnærmelse.
- Retningen på nogle af bilens sideakser (Kunos, DiRT) er dokumenteret begge veje; drifthældningens størrelse er
  pålidelig, dens fortegn er det ikke.
- Ingen af rally-spillene sender hjulslip; det udledes i viewer'en. RBR sender ingen hjulhastigheder.
- En rallyprøves overflade skrives kun, når `--surface` angives; ellers nævner filen ingen, og viewer'en udleder den
  (prøvens eller begivenhedens navn, derefter køremåden, løst som standard).
- Omgangsregistrering uden omgangstæller (AC EVO, AC Rally, BeamNG) bruger det punkt, hvor optagelsen startede, som
  linje, så start optagelsen ved startlinjen.
- Et nulstilling af et BeamNG-køretøj lukker den åbne omgang på det øjeblik: den skrives som en delvis kørsel, når den
  dækkede den mindste afstand (300 m), og droppes ellers.
- `route` gemmer hver 2. sekund eller deromkring, mens der køres; et nedbrud eller en dræbt proces mister højst positionerne
  siden den sidste gemning.
- Forza Horizon sender intet banenavn, så Forza-omgangsfiler har `"track": null`; Forza Motorsport (2023) sender kun et tal,
  som gemmes som `lap.trackOrdinal`.

## Rekonstruktion {#reconstruction}

- **Dybden er estimeret, ikke læst.** Loftet for hele fremgangsmåden, og prisen for aldrig at røre spilprocessen.
- **Synsfeltet er antaget, ikke målt.** For smalt, og banen rekonstrueres dybere, end den er.
- **Den globale skala** kommer fra en antaget kamerahøjde (1,15 m i vinduet) eller fra telemetri. Den måles på den første
  nøgleramme; når den ikke har brugbar jord, prøves de næste nøglerammer (op til 30 billeder), og en skala fundet senere
  anvendes på hele banen, når den skrives. Vinduets linje "Size:" siger, hvad der skete; uden jord overhovedet forbliver
  scanningen uden enhed. Voxelstørrelsen er i den første rammes enheder i det tilfælde, så dens størrelse i meter afviger
  fra indstillingen. Offline-rekonstruktioner er i løsningens egne enheder.
- **Løkkelukning er slået fra** og er ikke en posegraf, når den slås til i koden; driften begrænses kun af kvaliteten af
  sporing fra ramme til ramme.
- **Vindues-bundle-justering findes, men er ikke koblet på**; den kollapsede på rigtige optagelser.
- **Overfladen er vægtet belægning, ikke en TSDF**: tynde strukturer og frit rum er dårligere, end en TSDF ville give.
- **Ingen teksturatlas.** Farve er pr. vertex (`COLOR_0`), blandet fra de 4 bedste visninger blandt 160 gemte rammer.
  Okklusionstesten er grov: den tester mod meshets egne vertices i en 2-pixels dybdebuffer, så en forhindring, meshet ikke
  indeholder (en passerende bil), fanges ikke.
- **Vand mærkes aldrig**; alt er jord eller struktur.
- **Løsning med feed-forward er ikke live**: den kræver først optagelsen. Den adaptive genløsning af svære afsnit er ikke bygget.
- **Telemetriposer** placerer kameraet ved bilen (et tredjepersonskameras forskydning er ukendt). Positionerne tages, som Forza
  sender dem (Y op, som i omgangsfilerne); retningerne for gir, hældning og rulning blev aflæst af optagede omgange (kørselsretning,
  hældning, hvilken side affjedringen trykker sammen), ikke af det kørende spils kamera.
- Overlejringen kan ikke tegne over **eksklusiv fuldskærm**; brug kantløs fuldskærm.
- Globale genveje, den klikgennemsigtige overlejring og live-optagelse er **kun Windows**.
- Lukning af vinduet tilbyder ikke at gemme.

## Hvad der måles {#what-is-measured}

- `tests/test_accuracy.py`: et syntetisk rum med en kendt sti og analytisk dybde - placerede rammer, stifejl, tilbagelagt
  afstand, rummets størrelse, overfladen på væggene ([Banerekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: en vej med kendt bredde, kørt ud af midten, rekonstrueres med sin bredde.
- `tests/test_track_scale.py`: overfladeudtræk i racerbanens skala, hukommelse proportional med det, der blev scannet, blokke
  der forenes til én overflade.
- `tests/test_glb.py` plus viewer'ens egne tests: `.glb`-kontrakten fra begge sider.
- Hvordan dybdenetværket klarer sig på rigtigt spil er ikke noget et syntetisk billede kan besvare, og måles ikke af testpakken.
