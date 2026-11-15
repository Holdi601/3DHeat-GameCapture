---
title: "Optagelse, masker og billedkvalitet"
nav_order: 2
lang: "da"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Optagelse, masker og billedkvalitet {#capture-masks-and-frame-quality}

Kode: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Hvor billederne kommer fra {#where-frames-come-from}

Et kildemål er en af disse:

| Mål | Kilde | Noter |
|---|---|---|
| `monitor:<n>` | en hel skærm, live | vinduets "Whole screen" med nummeret i "Which" |
| `window:<title>` | ét vindue, live | vinduets "A window" med dets titel |
| en filsti | en videofil | vinduets "A video file"; ethvert format OpenCV kan læse |

### Live-optagelse: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` bruger pakken `windows-capture`, som pakker **Windows Graphics Capture** - det offentlige API, skærmoptagere bruger. Intet injiceres i spillet. Markøren fanges ikke, og der tegnes ingen gul optagelseskant.

Optageudvidelsen leverer billeder til en tilbagekaldsfunktion på compositorens tråd og forventer, at den returnerer med det samme. Derfor gør tilbagekaldsfunktionen kun tre ting: den kopierer billedet (bufferen genbruges), konverterer BGRA til RGB, ændrer størrelsen, stempler det og lægger det i en kø på **4 billeder**. Når køen er fuld, **smides det ældste billede væk**, og en tæller stiger: at halte bagefter skal koste billeder, ikke hukommelse eller korrekthed, og livevisningen skal vise, hvor spilleren er nu. Droppede billeder vises i vinduets statistiklinje, og når mere end halvdelen droppes, kommer et tip.

Hvert billede bærer `t` (sekunder siden optagelsen startede) og `monotonic` (den rå `time.monotonic()` ved optagelsen), det samme ur som telemetripakkerne stemples med - det er det, der gør det muligt at flugte Forza-positioner med billeder.

`windows-capture` er valgfri i afhængighedstjekket: uden den kan en videofil stadig skannes.

### Videofiler {#video-files}

`VideoSource` læser med OpenCV, konverterer til RGB og ændrer størrelsen. En beholder uden billedfrekvens behandles som 30 fps. Tidsstemplerne er billedindekset divideret med billedfrekvensen; en fil har ingen vægtidstid, så telemetri kan ikke flugtes med en video.

### Opløsning {#resolution}

Billederne ændres i størrelse ved kilden, så den lange side er forudindstillingens optageside (Draft 640, Balanced 960, Detailed 1280 px), med arealinterpolation. Et 4K-billede har tredive gange så mange pixels, som dybdemodellen bruger.

## Nøglebilleder {#keyframes}

Næsten hvert billede i en optagelse er overflødigt: at stå stille giver hundredvis af udsigter over én ting. Det, rekonstruktionen har brug for, er *parallakse*. Så et billede gemmes efter **hvor meget billedet har ændret sig siden det sidst gemte nøglebillede**, ikke efter et timerur.

`picture_change(a, b)`:

1. begge billeder gøres til gråtoner og nedskaleres til et 16 x 16-gitter af blokgennemsnit (blokgennemsnit reagerer på billedet, der bevæger sig, ikke på korn, løv, flimren eller HUD'en);
2. den gennemsnitlige absolutte forskel, som en brøk af 255;
3. når en verdensmaske er kendt, vægtes hver blok efter den andel af den, der er verden og ikke cockpit, så en halv instrumentbræt-blok tæller halvt (bruges, når masken dækker mere end 5 % af gitterets vægt).

Tærsklen **tilpasser sig optagelsen**: de første 30 billeder bruger forudindstillingens startværdi (0,020 / 0,010 / 0,004), derefter forudindstillingens kvantil (0,85 / 0,65 / 0,40) af de sidste 240 målte ændringer, aldrig under 0,0001. Et billede gemmes, når dets ændring når tærsklen; det første billede gemmes altid. En fast tærskel virker ikke på tværs af scener - billedændringen fra et mørkt cockpit på en lap er en lille brøk af den for et lyst, teksturrigt rum - mens "behold den travleste tredjedel" betyder det samme i begge. Den tærskel, der bruges, sendes med hver fremdriftsopdatering (`ScanProgress.threshold`), og gåhastighedsbarerne i vinduet og overlayet måler den sidste ændring mod den (`ScanProgress.toward_next_view`).

Kun nøglebilleder går gennem dybdemodellen og rekonstruktionen. Billeder gemmes ikke, medmindre en kalder beder om det (`keep_frames`); 160 af dem gemmes til farvning af mesh'en (se [farve](reconstruction-fusion-and-texture.md#colour)).

En scanning slutter, når den stoppes, når en video løber tør, eller ved tids- eller nøglebilledegrænsen.

## Hvad der ikke er verden {#what-is-not-the-world}

To ting i et spilbillede er ikke niveaugeometri, og begge ødelægger en rekonstruktion:

- **HUD'en.** Et sigtekorn er det mest gentagelige træk i ethvert billede. En feature-matcher elsker det: det passer perfekt mellem hvert par af billeder, og hvert match er bevis for, at kameraet ikke flyttede sig - det komprimerer hele rekonstruktionen.
- **Ting fastgjort til kameraet.** Et våben, en motorhjelm, en cockpitramme, et instrumentbræt. Virkelig geometri i det forkerte koordinatsystem: fusioneret smører det sig ud langs hele den gåede sti.

To detektorer finder dem. Begge producerer en maske (255 = verden, 0 = ikke verden) eller `None`, så længe der ikke er nok belæg; `None` betyder altid "brug alt", aldrig "brug intet".

Masken anvendes:

- ved **feature-detektion** i visuel odometri (at maskere et sigtekorn væk fra outputtet, mens det må stemme om positionen, ville rette det synlige symptom og beholde det skadelige);
- på de **fusionerede pixels**, så ingen cockpitgeometri fusioneres;
- på **skarphed- og lysstyrkemålet**, fordi et cockpit altid er perfekt skarpt;
- på **billedændringen**, der afgør nøglebilleder.

Den anvendes **ikke** på de billeder, der gives til den offline VGGT-løser (se [Offline-rekonstruktion](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: hvad der ikke ændrer sig {#screenmask-what-does-not-change}

Bruges fra det første nøglebillede, indtil FlowMask er klar.

- Hvert billede gøres til gråtoner, halveres og gøres sløret (3 x 3 Gauss), så et et-pixel-ryk i et statisk HUD-element ikke læses som bevægelse.
- Den absolutte forskel pr. pixel fra det forrige billede foldes ind i et eksponentielt gennemsnit (henfald 0,9), så masken følger et HUD, der dukker op eller forsvinder midt i en scanning.
- Den lærer kun fra billeder, hvor kameraet vides at bevæge sig (i scanningen: når mindst ét billede er sporet) - et parkeret kamera gør alt statisk.
- Efter **12** læringsbilleder er en pixel statisk, når dens gennemsnitlige ændring er under **0,22** af billedets medianændring - relativt, så tærsklen følger, hvor hurtigt spilleren bevæger sig.
- Hvis mere end **45 %** af billedet læses som statisk, er forudsætningen slået fejl (en menu, en mellemfilm), og intet maskeres.
- Masken eroderes med én pixel (antialiasede HUD-kanter hører hverken til den ene side eller den anden) og skaleres tilbage til fuld størrelse.

Dens besked i vinduet: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` eller `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: hvad der aldrig bevæger sig {#flowmask-what-never-travels}

Et cockpit er ikke statisk: nåle svinger, omdrejningstælleren ryster, minikortet drejer, så en ændringsdetektor kalder de pixels verden - og de er de dårligste træk at give en positionsløser. FlowMask stiller det bedre spørgsmål: **hvilke træk består uden at bevæge sig?**

- I live-scanningen lærer den én gang, ud fra de første **40 nøglebilleder** (gråtoner); derefter erstatter den ScreenMask for resten af scanningen.
- Billederne skæres i vinduer på **30** billeder, overlappende med det halve. I hvert vindue sås op til 800 hjørner (`goodFeaturesToTrack`, kvalitet 0,01, 8 px fra hinanden) og følges med pyramidal Lucas-Kanade (21 x 21, 4 niveauer) med et **fremad-bagud-tjek**: et spor, hvis baglæns flow ikke lander inden for 1 px af det, det startede fra, droppes, fordi en tracker, der driver over på et naboseende mønster, ville fremstille netop det "vedvarende men stationære" signatur, der søges. Vinduer kortere end 20 billeder springes over. Korte vinduer har betydning: over et langt forløb forlader næsten alle verdenstræk billedet, og beviset tyndes til intet.
- Hvert overlevende trækkets nettobevægelse sammenlignes med **2 % af billedbredden**: under er det "fastlåst", over er det "bevægelig". Tællinger akkumuleres på et **24 x 24**-gitter af skærmceller efter, hvor trækket startede.
- En celle blokeres, når den rummer mindst 2 fastlåste træk og flere fastlåste end bevægelige, **og** mindst 3 af dens 8 naboer også er blokerede (en enlig celle er støj; mørkt optagemateriale giver mange).
- Kun blokerede områder **forbundet til billedkanten** beholdes. Alt fastgjort til kameraet når en kant af skærmen; det, der sidder midt i billedet og ikke bevæger sig, er forsvindingspunktet - når man kører fremad, har vejen lige frem ingen flow, og det er den geometri, der helst ønskes.
- Det overlevende område vokser med én celle (et instrumentbrædts kant er en gradient).
- Hvis mere end **60 %** af billedet ville blive maskeret, maskeres intet: på nattemateriale rummer de fleste celler ingen sporbart træk, hvilket ser ud som et ur.

Dens besked: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, eller, over 60 %, en besked, der forklarer, at den ikke maskerer noget.

Offline-stien lærer den samme FlowMask ud fra 4 kørsler af 90 på hinanden følgende billeder fordelt over videoen, ved 960 x 540 ([Offline](reconstruction-offline.md)).

## Billedkvalitet og råd {#frame-quality-and-advice}

`QualityWatcher` bedømmer hvert nøglebillede og vælger **én** anvisning, så overlayet kan sige "kør langsommere", mens der stadig er tid til det.

Pr. billede måler den, kun på verdenspixels (alle pixels, hvis masken efterlader mindre end 5 %):

- **skarphed**: variansen af Laplace-operatoren - det standardmål i ét gennemløb, og det reagerer netop på det, bevægelsesslør ødelægger;
- **lysstyrke**: gennemsnitligt gråniveau, 0-255.

Skarphed har ingen absolut skala (en natlig etape og en lys gade adskiller sig med en størrelsesorden, begge i fokus), så den bedømmes mod **den løbende median for denne optagelse**: de sidste 90 billeder, og der kræves 20, før der dømmes. Hvert billede sammenlignes med historikken *før* det tilføjes, så en lang sløret strækning ikke kan trække medianen ned til sig selv.

| Tilstand | Test |
|---|---|
| flad | skarphed højst 1,0 (en indlæsningsskærm, en væg, himmel) |
| mørk | lysstyrke under 26 |
| sløret | skarphed under 0,55 af medianen, og ikke flad |

Rådet, første match vinder (ordnet efter hvad der blokerer scanningen hårdest):

| Situation | Råd | Niveau |
|---|---|---|
| færre end 20 billeder | Getting a feel for the picture… | ok |
| flad | Nothing to measure — point the camera at the level, not at the sky. | stop |
| mørk | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| sløret | Blurred — slow down. | warn |
| færre end halvdelen af billederne sporet | Losing track — slow down and keep more of the level in view. | warn |
| færre end 40 % af de sporede billeder fusioneret | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| svage pletter findes | N thin spots — the map marks them. | ok |
| ellers | Good — keep going. | ok |

Niveauet farver overlayets råd (grøn / gul / rød). Overlayets **skarphedsbar** er billedets skarphed i forhold til medianen. (Koden har også "Blurred, and the camera is not moving. Check the capture." for et stillestående kamera; scanningen melder altid kameraet som bevægeligt, så den vises ikke.)
