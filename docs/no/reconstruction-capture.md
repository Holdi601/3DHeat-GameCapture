---
title: "Opptak, masker og bildekvalitet"
nav_order: 2
lang: "no"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Opptak, masker og bildekvalitet {#capture-masks-and-frame-quality}

Kode: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Hvor bildene kommer fra {#where-frames-come-from}

Et kildemål er ett av disse:

| Mål | Kilde | Merknad |
|---|---|---|
| `monitor:<n>` | en hel skjerm, live | vinduets "Hele skjermen" med nummeret i "Hvilken" |
| `window:<title>` | ett vindu, live | vinduets "Ett vindu" med tittelen |
| en filsti | en videofil | vinduets "En videofil"; ethvert format OpenCV kan lese |

### Live-opptak: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` bruker pakken `windows-capture`, som pakker **Windows Graphics Capture** -
det offentlige API-et skjermopptakere bruker. Ingenting injiseres i spillet. Markøren fanges ikke,
og ingen gul opptaksramme tegnes.

Opptaksbiblioteket leverer bilder til en callback på kompositorens tråd og forventer at den
returnerer med en gang, så callbacken bare kopierer bildet (bufferen gjenbrukes), gjør
BGRA om til RGB, skalerer det, stempler det og legger det i en kø med **4 bilder**. Når køen
er full, **droppes det eldste bildet** og en teller går opp: å henge etter skal koste bilder,
ikke minne eller korrekthet, og liveviewet skal vise hvor spilleren er nå. Droppede bilder vises
i vinduets statistikklinje, og når mer enn halvparten droppes, kommer et tips.

Hvert bilde bærer `t` (sekunder siden opptaket startet) og `monotonic` (den rå
`time.monotonic()` ved opptak), klokken telemetripakkene også stemples med - det er det som
gjør at Forza-posisjoner kan linjes opp med bilder.

`windows-capture` er valgfri i avhengighetssjekken: uten den kan en videofil likevel skannes.

### Videofiler {#video-files}

`VideoSource` leser med OpenCV, konverterer til RGB og skalerer. En beholder uten bildefrekvens
behandles som 30 bps. Tidsstempler er bildeindeksen delt på bildefrekvensen; en fil har ingen
veggklokketid, så telemetri kan ikke linjes opp med en video.

### Oppløsning {#resolution}

Bilder skaleres ved kilden slik at lengste side er forhåndsinnstillingens opptaksstørrelse (Utkast 640,
Balansert 960, Detaljert 1280 px), med arealinterpolasjon. Et 4K-bilde har tretti ganger så
mange piksler som dybdemodellen bruker.

## Nøkkelbilder {#keyframes}

Nesten hvert bilde i et opptak er overflødig: å stå stille gir hundrevis av utsikter over
ett og samme. Rekonstruksjonen vil ha *parallakse*. Så et bilde beholdes ut fra **hvor mye
bildet har endret seg siden forrige beholdte bilde**, ikke etter en timer.

`picture_change(a, b)`:

1. begge bildene gjøres grå og ned til et 16 x 16-rutenett av blokkgjennomsnitt (blokkgjennomsnitt
   reagerer på at bildet beveger seg, ikke på kornstøy, løvverk, flimmer eller HUD);
2. den gjennomsnittlige absolutte forskjellen, som brøkdel av 255;
3. når en verdenmaske er kjent, vektes hver blokk med andelen av den som er verden og ikke
   cockpit, så en blokk halvt dekket av instrumentbordet teller halvt (brukes når masken dekker
   mer enn 5 % av rutenettets vekt).

Terskelen **tilpasser seg opptaket**: de første 30 bildene bruker presetets startverdi (0,020 / 0,010 / 0,004),
deretter presetets kvantil (0,85 / 0,65 / 0,40) av de siste 240 målte endringene, aldri under
0,0001. Et bilde beholdes når endringen når terskelen; det første bildet beholdes alltid. En fast
terskel fungerer ikke på tvers av scener - bildeendringen fra et mørkt cockpit-opptak er en liten
brøkdel av et lyst, teksturrikt rom - mens "behold den travleste tredjedelen" betyr det samme i begge.
Terskelen i bruk sendes med hver fremdriftsoppdatering (`ScanProgress.threshold`), og
gangfartslinjene i vinduet og overlegget måler siste endring mot den (`ScanProgress.toward_next_view`).

Bare beholdte bilder går gjennom dybdemodellen og rekonstruksjonen. Bilder lagres ikke med mindre
en kaller ber om det (`keep_frames`); 160 av dem beholdes for å farge nettet (se
[farge](reconstruction-fusion-and-texture.md#colour)).

En skanning slutter når den stoppes, når en video er ferdig, eller ved tids- eller nøkkelbildegrensen.

## Det som ikke er verden {#what-is-not-the-world}

To ting i et spillbilde er ikke nivågeometri, og begge ødelegger en rekonstruksjon:

- **HUD-en.** Et sikte er det mest repeterbare kjennetegnet i et bilde. En trekkfunksjon
  elsker det, det treffer perfekt mellom alle bildepar, og hvert treff er bevis på at kameraet
  ikke flyttet seg - det komprimerer hele rekonstruksjonen.
- **Ting festet til kameraet.** Et våpen, en panser, en cockpitramme, et instrumentbord. Ekte
  geometri i feil koordinatsystem: sammensmeltet smører den seg langs hele stien som er gått.

To detektorer finner dem. Begge lager en maske (255 = verden, 0 = ikke verden) eller `None` så lenge
det ikke er nok bevis, og `None` betyr alltid "bruk alt", aldri "bruk ingenting".

Masken brukes:

- ved **trekkdeteksjon** i visuell odometri (å maskere et sikte bort fra utdataene, mens det får
  stemme i posisjonen, ville rette det synlige symptomet og beholde det skadelige);
- på de **sammensmeltede pikslene**, så ingen cockpitgeometri smeltes sammen;
- på **skarphets- og lysstyrkemålet**, fordi et cockpit alltid er perfekt skarpt;
- på **bildeendringen** som avgjør nøkkelbilder.

Den brukes **ikke** på bildene som gis til den offline VGGT-løseren (se
[Offline rekonstruksjon](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: det som ikke endrer seg {#screenmask-what-does-not-change}

Brukes fra første nøkkelbilde til FlowMask er klar.

- Hvert bilde gjøres til gråtoner, halveres og gjøres uskarpt (3 x 3 Gauss) slik at en pikseljitter i
  et statisk HUD-element ikke leses som bevegelse.
- Den absolutte forskjellen per piksel fra forrige bilde foldes inn i et eksponentielt
  gjennomsnitt (forfall 0,9), slik at masken følger et HUD som dukker opp eller forsvinner midt i skanningen.
- Den lærer bare fra bilder der kameraet kjent beveger seg (i skanningen: når minst ett bilde er
  sporet) - et parkert kamera gjør alt statisk.
- Etter **12** læringsbilder er en piksel statisk når gjennomsnittsendringen er under **0,22** av
  bildets medianendring - relativt, så terskelen følger hvor fort spilleren beveger seg.
- Hvis mer enn **45 %** av bildet leses som statisk, er forutsetningen brutt (en meny, en
  filmsekvens), og ingenting maskeres.
- Masken erodes med én piksel (antialiasede HUD-kanter hører til ingen av sidene) og skaleres
  tilbake til full størrelse.

Notatet i vinduet: `lærer hva som er HUD (n/12 bilder)`, `fant ingen HUD eller festet geometri`,
eller `ignorerer N % av bildet - HUD eller festet til kameraet`.

### FlowMask: det som aldri beveger seg {#flowmask-what-never-travels}

Et cockpit er ikke statisk: nåler feier, turtelleren rykker, kartet roterer, så en endringsdetektor
kaller disse pikslene verden - og de er de verste sporene å gi en posisjonsløser. FlowMask
stiller det bedre spørsmålet: **hvilke trekk består uten å bevege seg?**

- I live-skanningen lærer den én gang, fra de første **40 nøkkelbildene** (gråtoner); deretter
  erstatter den ScreenMask for resten av skanningen.
- Bildene deles i vinduer på **30** bilder, overlappende med en halv. I hvert vindu seedes opptil
  **800** hjørner (`goodFeaturesToTrack`, kvalitet 0,01, 8 px fra hverandre) og følges med pyramidal
  Lucas-Kanade (21 x 21, 4 nivåer) med en **forover-bakover-kontroll**: et spor hvis bakoverflyt
  ikke lander innenfor 1 px fra startpunktet, droppes - fordi en sporer som driver over på et nabomønster
  ville lage nøyaktig den "består men står stille"-signaturen som letes etter. Vinduer kortere enn
  20 bilder hoppes over. Korte vinduer betyr noe: over en lang kjøring forlater nesten alle verdenstrekk
  bildet, og beviset tynnes til ingenting.
- Hvert gjenværende trekks nettobevegelse sammenlignes med **2 % av bildebredden**: under er det
  "stående", over er det "i bevegelse". Tellinger samles på et **24 x 24**-rutenett av skjermceller
  etter hvor trekket startet.
- En celle blokkeres når den har minst 2 stående trekk og flere stående enn bevegelige, **og**
  minst 3 av dens 8 naboer er blokkert også (en enslig celle er støy; mørkt opptak gir mange av dem).
- Bare blokkerte områder **koblet til bildekanten** beholdes. Alt festet til kameraet når en
  kant av skjermen; det som ligger midt i bildet og ikke beveger seg, er forsvinningspunktet - ved kjøring
  forover har veien rett fremover ingen bevegelse, og det er geometrien som er mest ønsket.
- Det gjenværende området vokser med én celle (et instrumentpanels kant er en gradient).
- Hvis mer enn **60 %** av bildet ville blitt maskert, maskeres ingenting: på nattopptak har de fleste
  celler ingen sporbart trekk, og det leses likt som en urskive.

Notatet: `ser på hva som beveger seg`, `ingenting festet til kameraet`, `ignorerer N % av bildet -
det beveger seg aldri`, eller, over 60 %, en melding som forklarer at det ikke maskeres noe.

Den offline banen lærer samme FlowMask fra 4 kjøringer på 90 sammenhengende bilder spredt over
videoen, i 960 x 540 ([Offline](reconstruction-offline.md)).

## Bildekvalitet og råd {#frame-quality-and-advice}

`QualityWatcher` vurderer hvert nøkkelbilde og velger **én** instruksjon, slik at overlegget kan
si "kjør saktere" mens det fortsatt er tid til det.

Per bilde måles, bare på verdenspikslene (alle piksler hvis masken lar mindre enn 5 % stå igjen):

- **skarphet**: variansen til Laplace-filteret - det standard enpasmålet, og det reagerer på nøyaktig
  det bevegelsesuskarphet ødelegger;
- **lysstyrke**: gjennomsnittlig gråtonenivå, 0-255.

Skarphet har ingen absolutt skala (en nattscene og en lys gate skiller seg med en størrelsesorden,
begge i fokus), så den vurderes mot **løpende median for dette opptaket**: de siste 90 bildene,
og 20 må finnes før noen vurdering gjøres. Hvert bilde sammenlignes med historikken *før* det legges
til, så en lang uskarp strekning ikke kan trekke medianen ned til seg selv.

| Tilstand | Test |
|---|---|
| flat | skarphet på høyst 1,0 (en lasteskjerm, en vegg, himmel) |
| mørkt | lysstyrke under 26 |
| uskarpt | skarphet under 0,55 av medianen, og ikke flatt |

Rådet, første treff vinner (ordnet etter hva som hindrer skanningen mest):

| Situasjon | Råd | Nivå |
|---|---|---|
| færre enn 20 bilder | Blir kjent med bildet… | ok |
| flatt | Ingenting å måle - rett kameraet mot banen, ikke mot himmelen. | stopp |
| mørkt | For mørkt til å rekonstruere. Slå på lysene, eller kjør denne strekningen i dagslys. | stopp |
| uskarpt | Uskarpt - kjør saktere. | advarsel |
| færre enn halvparten av bildene sporet | Mister sporet - kjør saktere og hold mer av banen i synsfeltet. | advarsel |
| færre enn 40 % av de sporede bildene sammensmeltet | Posisjonene er gode, men dybden fester seg ikke. Kjør nærmere omgivelsene. | advarsel |
| svake punkter finnes | N tynne punkter - kartet viser dem. | ok |
| ellers | Bra - fortsett. | ok |

Nivået farger rådet i overlegget (grønn / gul / rød). Overlegget viser **skarphet**-linjen som
bildets skarphet i forhold til medianen. (Koden har også "Uskarpt, og kameraet beveger seg ikke. Sjekk
opptaket." for et stasjonært kamera; skanningen melder alltid at kameraet beveger seg, så det vises ikke.)
