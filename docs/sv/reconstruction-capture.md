---
title: "Bildtagning, masker och bildkvalitet"
nav_order: 2
lang: "sv"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Bildtagning, masker och bildkvalitet {#capture-masks-and-frame-quality}

Kod: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Var bildrutorna kommer från {#where-frames-come-from}

Ett källmål är ett av:

| Mål | Källa | Anmärkningar |
|---|---|---|
| `monitor:<n>` | en hel bildskärm, live | fönstrets "Whole screen" med numret i "Which" |
| `window:<title>` | ett fönster, live | fönstrets "A window" med dess titel |
| en sökväg till en fil | en videofil | fönstrets "A video file"; alla format som OpenCV kan läsa |

### Livetagning: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` använder paketet `windows-capture`, som omsluter **Windows Graphics Capture** - det publika API som skärminspelare använder. Ingenting injiceras i spelet. Markören fångas inte och ingen gul fångstram ritas.

Biblioteket levererar bildrutor till en callback på kompositörens tråd och förväntar sig att den returnerar direkt. Callbacken kopierar därför bara bildrutan (bufferten återanvänds), konverterar BGRA till RGB, skalar om den, stämplar den och lägger den i en kö med **4 bildrutor**. När kön är full **släpps den äldsta bildrutan** och en räknare ökar: att halka efter ska kosta bildrutor, inte minne eller korrekthet, och liveförhandsvisningen ska visa var spelaren är nu. Släppta bildrutor visas i fönstrets statistikrad, och om mer än hälften släpps ges ett tips.

Varje bildruta bär `t` (sekunder sedan fångsten började) och `monotonic` (den råa `time.monotonic()` vid fångsten), samma klocka som telemetripaketen stämplas med. Det är vad som gör att Forza-poser kan linjeras med bildrutor.

`windows-capture` är valfri i beroendekontrollen: utan det går det ändå att skanna en videofil.

### Videofiler {#video-files}

`VideoSource` läser med OpenCV, konverterar till RGB och skalar om. En container utan bildfrekvens behandlas som 30 bilder per sekund. Tidsstämplar är bildindex delat med bildfrekvensen; en fil har ingen väggklocka, så telemetri kan inte linjeras mot en video.

### Upplösning {#resolution}

Bildrutor skalas om vid källan så att längsta sidan är förinställningens fångstsida (Draft 640, Balanced 960, Detailed 1280 px), med areainterpolation. En 4K-bildruta är trettio gånger så många pixlar som djupmodellen använder.

## Nyckelbildrutor {#keyframes}

Nästan varje bildruta i en fångst är överflödig: att stå still ger hundratals vyer av samma sak. Rekonstruktion vill ha *parallax*. Så en bildruta behålls efter **hur mycket bilden har ändrats sedan den senast behållna bildrutan**, inte efter en timer.

`picture_change(a, b)`:

1. båda bildrutorna görs gråa och ner till ett 16 x 16-rutnät av blockmedelvärden (blockmedelvärden reagerar på att bilden rör sig, inte på korn, lövverk, flimmer eller HUD:en);
2. medelabsolutskillnaden, som bråkdel av 255;
3. när en världsmask är känd viktas varje block med andelen av det som är värld snarare än förarhytt, så att ett block som är till hälften instrumentbräda räknas till hälften (används när masken täcker mer än 5 % av rutnätets vikt).

Tröskeln **anpassar sig till fångsten**: de första 30 bildrutorna använder förinställningens startvärde (0,020 / 0,010 / 0,004), sedan förinställningens kvantil (0,85 / 0,65 / 0,40) av de senaste 240 uppmätta ändringarna, aldrig under 0,0001. En bildruta behålls när dess ändring når tröskeln; den första bildrutan behålls alltid. En fast tröskel fungerar inte över scener - bildrutornas förändring i ett mörkt förarhyttsvarv är en liten bråkdel av den i ett ljust, texturerat rum - medan "behåll den mest händelserika tredjedelen" betyder detsamma i båda. Tröskeln som används skickas med varje förloppsuppdatering (`ScanProgress.threshold`), och hastighetsstaplarna för gång i fönstret och overlayn mäter den senaste ändringen mot den (`ScanProgress.toward_next_view`).

Bara behållna bildrutor går genom djupmodellen och rekonstruktionen. Bildrutor sparas inte om inte en anropare begär det (`keep_frames`); 160 av dem behålls för att färglägga nätet (se [färg](reconstruction-fusion-and-texture.md#colour)).

En skanning slutar när den stoppas, när en video tar slut, eller vid tids- eller nyckelbildrutegränsen.

## Vad som inte är världen {#what-is-not-the-world}

Två saker i en spelbildruta är inte nivågeometri, och båda förstör en rekonstruktion:

- **HUD:en.** Ett hårkors är den mest upprepbara detaljen i någon bildruta. En särdragsmatchare älskar den: den matchar perfekt mellan varje par av bildrutor, och varje matchning är bevis på att kameran inte rörde sig - vilket komprimerar hela rekonstruktionen.
- **Saker fästa vid kameran.** Ett vapen, en motorhuv, en förarhyttsram, en instrumentbräda. Det är verklig geometri i fel koordinatsystem: fusionerad smetar den ut sig längs hela den gångna vägen.

Två detektorer hittar dem. Båda producerar en mask (255 = värld, 0 = inte värld) eller `None` medan det inte finns tillräckligt med belägg. `None` betyder alltid "använd allt", aldrig "använd inget".

Masken tillämpas:

- vid **särdragsdetektering** i visuell odometri (att maskera bort ett hårkors från utdata men låta det rösta om posen skulle åtgärda det synliga symptomet och behålla det skadliga);
- på de **fusionerade pixlarna**, så att ingen förarhyttsgeometri fusioneras;
- på **skärpe- och ljusstyrkemåttet**, eftersom en förarhytt alltid är perfekt skarp;
- på **bildändringen** som avgör nyckelbildrutorna.

Den tillämpas **inte** på bildrutorna som ges till den offline-lösaren VGGT (se [Offline-rekonstruktion](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: vad som inte ändras {#screenmask-what-does-not-change}

Används från första nyckelbildrutan tills FlowMask är klar.

- Varje bildruta görs grå, halveras och suddas (3 x 3 Gauss) så att en ettpixlars darrning i ett statiskt HUD-element inte läses som rörelse.
- Den absoluta pixelskillnaden mot föregående bildruta viks in i ett exponentiellt medelvärde (avtagning 0,9), så att masken följer ett HUD som dyker upp eller försvinner mitt i en skanning.
- Den lär sig bara av bildrutor där kameran är känd för att röra sig (i skanningen: efter att minst en bildruta spårats) - en parkerad kamera gör allt statiskt.
- Efter **12** inlärningsbildrutor är en pixel statisk när dess medelförändring ligger under **0,22** av bildrutans medianförändring - relativt, så att tröskeln följer hur snabbt spelaren rör sig.
- Om mer än **45 %** av bildrutan läses som statisk har premissen fallit (en meny, en filmsekvens) och ingenting maskeras.
- Masken krymps med en pixel (antialiserade HUD-kanter hör inte till någondera sidan) och skalas tillbaka till full storlek.

Dess notis i fönstret: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected`, eller `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: vad som aldrig rör sig {#flowmask-what-never-travels}

En förarhytt är inte statisk: nålar sveper, varvräknaren ryckar, kartan roterar, så en förändringsdetektor kallar de pixlarna värld - och de är de sämsta särdragen att ge en posellösare. FlowMask ställer den bättre frågan: **vilka särdrag består utan att förflytta sig?**

- I live-skanningen lär den sig en gång, från de första **40 nyckelbildrutorna** (gråskala); sedan ersätter den ScreenMask för resten av skanningen.
- Bildrutorna delas i fönster om **30** bildrutor, överlappande med hälften. I varje fönster sås upp till 800 hörn (`goodFeaturesToTrack`, kvalitet 0,01, 8 px isär) och följs med pyramidal Lucas-Kanade (21 x 21, 4 nivåer) med en **framåt-bakåtkontroll**: ett spår vars bakåtflöde inte landar inom 1 px från där det började släpps. En spårare som driver över på ett grannmönster skulle annars skapa exakt den signatur "består men är stillastående" som letas efter. Fönster kortare än 20 bildrutor hoppas över. Korta fönster spelar roll: över en lång körning lämnar nästan varje världsdetalj bildrutan, och belägget tunnas ut till ingenting.
- Varje överlevande särdrags nettoförflyttning jämförs med **2 % av bildrutans bredd**: under det är det "fast", över är det "rörligt". Antalen samlas på ett **24 x 24**-rutnät av skärmceller efter var särdraget började.
- En cell blockeras när den innehåller minst 2 fasta särdrag och fler fasta än rörliga, **och** minst 3 av dess 8 grannar också är blockerade. En ensam cell är brus; mörkt material ger gott om sådana.
- Bara blockerade områden **som är sammanhängande med bildrutans kant** behålls. Allt som sitter fast vid kameran når en kant av skärmen. Det som sitter mitt i bilden och inte rör sig är försvinningspunkten: när man kör framåt har vägen rakt framför inget flöde, och den är geometrin som mest önskas.
- Det överlevande området växs med en cell (en instrumentpanels kant är en gradient).
- Om mer än **60 %** av bildrutan skulle maskeras maskeras ingenting: på nattmaterial saknar de flesta celler ett spårbart särdrag, vilket ser likadant ut som en mätare.

Dess notis: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, eller, över 60 %, ett meddelande som förklarar att den inte maskerar något.

Den offline-vägen lär sig samma FlowMask från 4 körningar om 90 på varandra följande bildrutor, utspridda över videon, vid 960 x 540 ([Offline](reconstruction-offline.md)).

## Bildkvalitet och råd {#frame-quality-and-advice}

`QualityWatcher` bedömer varje nyckelbildruta och väljer **en** instruktion, så att overlayn kan säga "kör långsammare" medan det fortfarande finns tid.

Per bildruta mäts, bara på världspixlarna (alla pixlar om masken lämnar mindre än 5 %):

- **skärpa**: variansen av Laplacian - det vanliga måttet som görs i ett pass, och det reagerar på just det rörelseoskärpa förstör;
- **ljusstyrka**: medelgrånivå, 0-255.

Skärpan har ingen absolut skala (en nattetapp och en ljus gata skiljer sig med en storleksordning, båda i fokus), så den bedöms mot **denna fångsts löpande median**: de senaste 90 bildrutorna, och 20 behövs innan någon bedömning görs. Varje bildruta jämförs med historiken *före* den läggs till, så att en lång oskarp sträcka inte kan dra medianen ner till sig själv.

| Villkor | Test |
|---|---|
| platt | skärpa högst 1,0 (en laddningsskärm, en vägg, himmel) |
| mörk | ljusstyrka under 26 |
| oskarp | skärpa under 0,55 av medianen, och inte platt |

Rådet, första träff gäller (ordnat efter vad som hindrar skanningen mest):

| Läge | Råd | Nivå |
|---|---|---|
| färre än 20 bildrutor | Får en känsla för bilden… | ok |
| platt | Inget att mäta - rikta kameran mot nivån, inte mot himlen. | stopp |
| mörk | För mörkt för att rekonstruera. Tänd strålkastarna, eller kör sträckan i dagsljus. | stopp |
| oskarp | Oskarpt - kör långsammare. | varning |
| färre än hälften av bildrutorna spårade | Tappar spåret - kör långsammare och håll mer av nivån i sikte. | varning |
| färre än 40 % av de spårade bildrutorna fusionerade | Positionerna är bra men djupet fastnar inte. Kör närmare landskapet. | varning |
| svaga platser finns | N svaga platser - kartan markerar dem. | ok |
| annars | Bra - fortsätt. | ok |

Nivån färgar overlayns råd (grönt / gult / rött). Overlayns **skärpe**-stapel är bildrutans skärpa i förhållande till medianen. (Koden har också "Blurred, and the camera is not moving. Check the capture." för en stillastående kamera. Skanningen rapporterar alltid kameran som rörlig, så den visas inte.)
