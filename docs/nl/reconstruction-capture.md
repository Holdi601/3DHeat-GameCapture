---
title: "Opname, maskers en beeldkwaliteit"
nav_order: 2
lang: "nl"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Opname, maskers en beeldkwaliteit {#capture-masks-and-frame-quality}

Code: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py), [`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py), [`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py), [`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py), [`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Waar de frames vandaan komen {#where-frames-come-from}

Een bronnendoel is een van:

| Doel | Bron | Opmerkingen |
|---|---|---|
| `monitor:<n>` | een heel scherm, live | het venster "Whole screen" met het nummer bij "Which" |
| `window:<title>` | één venster, live | het venster "A window" met zijn titel |
| een bestandspad | een videobestand | het venster "A video file"; elk formaat dat OpenCV kan lezen |

### Live opnemen: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` gebruikt het pakket `windows-capture`, dat **Windows Graphics Capture** inpakt - de openbare API die schermopnameprogramma's gebruiken. Er wordt niets in het spel geïnjecteerd. De cursor wordt niet opgenomen en er wordt geen gele opnamerand getekend.

De opnamebibliotheek levert frames aan een callback op de thread van de compositor en verwacht dat die meteen terugkeert, dus de callback kopieert alleen het frame (de buffer wordt hergebruikt), zet BGRA om naar RGB, schaalt het, voorziet het van een tijdstempel en zet het in een wachtrij van **4 frames**. Als de wachtrij vol is, wordt het **oudste frame weggegooid** en gaat een teller omhoog: achterlopen moet frames kosten, niet geheugen of juistheid, en de live weergave moet laten zien waar de speler nu is. Weggegooide frames worden getoond in de statistiekregel van het venster, en meer dan de helft weggegooid geeft een tip.

Elk frame heeft `t` (seconden sinds de opname begon) en `monotonic` (de ruwe `time.monotonic()` bij de opname), de klok waarmee ook telemetriepakketten worden gestempeld - daarmee kunnen Forza-posities op de frames worden uitgelijnd.

`windows-capture` is optioneel in de afhankelijkheidscontrole: zonder kan een videobestand nog steeds worden gescand.

### Videobestanden {#video-files}

`VideoSource` leest met OpenCV, zet om naar RGB en schaalt. Een container zonder framesnelheid wordt als 30 fps behandeld. Tijdstempels zijn de frameindex gedeeld door de framesnelheid; een bestand heeft geen kloktijd, dus telemetrie kan niet met een video worden uitgelijnd.

### Resolutie {#resolution}

Frames worden aan de bron geschaald zodat de langste zijde de opnamezijde van de preset is (Draft 640, Balanced 960, Detailed 1280 px), met gebiedsinterpolatie. Een frame van 4K heeft dertig keer zoveel pixels als het dieptemodel gebruikt.

## Keyframes {#keyframes}

Bijna elk frame van een opname is overbodig: stilstaan levert honderden beelden van hetzelfde op. Reconstructie wil *parallax*. Dus wordt een frame bewaard op basis van **hoeveel het beeld is veranderd sinds het laatste bewaarde frame**, niet op een timer.

`picture_change(a, b)`:

1. beide frames naar grijs en omlaag naar een raster van 16 x 16 blokgemiddelden (blokgemiddelden reageren op het bewegen van het beeld, niet op korrel, gebladerte, flikkering of de HUD);
2. het gemiddelde absolute verschil, als fractie van 255;
3. als een wereldmasker bekend is, wordt elk blok gewogen naar het aandeel ervan dat wereld is in plaats van cockpit, zodat een half-dashboardblok half telt (gebruikt zodra het masker meer dan 5% van het gewicht van het raster bedekt).

De drempel **past zich aan de opname aan**: de eerste 30 frames is het de startwaarde van de preset (0,020 / 0,010 / 0,004), daarna het kwantiel van de preset (0,85 / 0,65 / 0,40) van de laatste 240 gemeten veranderingen, nooit lager dan 0,0001. Een frame wordt bewaard als de verandering de drempel bereikt; het eerste frame wordt altijd bewaard. Een vaste drempel werkt niet over verschillende scènes heen - de verandering van frame tot frame in een donkere cockpitronde is een klein deel van die in een heldere, rijk getextureerde kamer - terwijl "bewaar het drukste derde" overal hetzelfde betekent. De drempel die in gebruik is, gaat mee met elke voortgangsupdate (`ScanProgress.threshold`), en de loopsnelheidbalken in het venster en de overlay meten de laatste verandering daartegen (`ScanProgress.toward_next_view`).

Alleen bewaarde frames gaan door het dieptemodel en de reconstructie. Frames worden niet bewaard tenzij een aanroeper erom vraagt (`keep_frames`); 160 ervan worden bewaard voor het inkleuren van het mesh (zie [kleur](reconstruction-fusion-and-texture.md#colour)).

Een scan eindigt wanneer hij wordt gestopt, wanneer een video op is, of bij de tijd- of keyframelimiet.

## Wat niet de wereld is {#what-is-not-the-world}

Twee dingen in een gameframe zijn geen levelgeometrie, en allebei verpesten een reconstructie:

- **De HUD.** Een richtkruis is het meest herhaalbare kenmerk in elk frame. Een featurematcher houdt ervan, het past perfect tussen elk paar frames, en elke match is bewijs dat de camera niet bewoog - wat de hele reconstructie samendrukt.
- **Dingen die aan de camera vastzitten.** Een wapen, een motorkap, een cockpitframe, een dashboard. Echte geometrie in het verkeerde coördinatenstelsel: samengevoegd smeert het uit langs het hele afgelegde pad.

Twee detectoren vinden ze. Beide leveren een masker (255 = wereld, 0 = geen wereld) of `None` zolang er niet genoeg bewijs is, en `None` betekent altijd "gebruik alles", nooit "gebruik niets".

Het masker wordt toegepast:

- bij **het vinden van features** in visuele odometrie (een richtkruis uit de uitvoer maskeren terwijl het wel meestemt over de positie, zou het zichtbare symptoom oplossen en het schadelijke laten zitten);
- op de **samengevoegde pixels**, zodat geen cockpitgeometrie wordt samengevoegd;
- op de **meting van scherpte en helderheid**, omdat een cockpit altijd perfect scherp is;
- op de **beeldverandering** die bepaalt wat een keyframe is.

Het wordt **niet** toegepast op de frames die naar de offline VGGT-oplosser gaan (zie [Offline reconstructie](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: wat niet verandert {#screenmask-what-does-not-change}

Gebruikt vanaf het eerste keyframe tot FlowMask klaar is.

- Elk frame wordt naar grijs omgezet, gehalveerd en vervaagd (3 x 3 Gauss), zodat een pixel van trillen in een statisch HUD-element niet als beweging telt.
- Het absolute verschil per pixel met het vorige frame wordt in een exponentieel gemiddelde gevouwen (verval 0,9), zodat het masker een HUD volgt die midden in een scan verschijnt of verdwijnt.
- Het leert alleen van frames waarin bekend is dat de camera beweegt (in de scan: zodra minstens één frame is gevolgd) - een stilstaande camera maakt alles statisch.
- Na **12** leerframes is een pixel statisch wanneer zijn gemiddelde verandering onder **0,22** ligt van de mediane verandering van het frame - relatief, dus de drempel volgt hoe snel de speler beweegt.
- Als meer dan **45%** van het frame statisch leest, is de premisse mislukt (een menu, een tussenfilm), en wordt niets gemaskeerd.
- Het masker wordt met één pixel geërodeerd (antialias-randen van de HUD horen bij geen van beide kanten) en teruggeschaald naar volle grootte.

De melding in het venster: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected`, of `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: wat nooit meebeweegt {#flowmask-what-never-travels}

Een cockpit is niet statisch: naalden bewegen, de toerenteller trilt, de minimap draait, dus telt een veranderingsdetector die pixels als wereld. FlowMask stelt de betere vraag: **welke features blijven bestaan zonder mee te bewegen?**

- In de live scan leert het één keer, uit de eerste **40 keyframes** (grijswaarden); daarna vervangt het ScreenMask voor de rest van de scan.
- De frames worden gesneden in vensters van **30** frames, die voor de helft overlappen. In elk venster worden tot **800** hoeken gezaaid (`goodFeaturesToTrack`, kwaliteit 0,01, 8 px uit elkaar) en gevolgd met piramidale Lucas-Kanade (21 x 21, 4 niveaus) met een **voorwaarts-achterwaartse controle**: een spoor waarvan de achterwaartse flow niet binnen 1 px landt van waar het begon, wordt weggegooid, omdat een tracker die op een naburig patroon wegdrijft precies de handtekening "blijvend maar stilstaand" zou fabriceren die wordt gezocht. Vensters korter dan 20 frames worden overgeslagen. Korte vensters doen ertoe: over een lange run verlaten bijna alle wereldfeatures het frame, en wordt het bewijs tot niets verdund.
- De netto verplaatsing van elke overgebleven feature wordt vergeleken met **2% van de breedte van het frame**: eronder is het "vast", erboven "bewegend". Tellingen worden opgeteld op een raster van **24 x 24** schermcellen naar waar elke feature begon.
- Een cel wordt geblokkeerd wanneer ze minstens 2 vaste features bevat en meer vaste dan bewegende, **en** minstens 3 van haar 8 buren ook geblokkeerd zijn (een losse cel is ruis; donker beeldmateriaal levert er veel op).
- Alleen geblokkeerde gebieden die **aan de rand van het frame vastzitten** worden bewaard. Alles wat aan de camera vastzit, raakt een rand van het scherm; wat in het midden zit en niet beweegt, is het verdwijnpunt - vooruit rijdend heeft de weg recht vooruit geen stroming en is het de geometrie die het meest gewenst is.
- Het overgebleven gebied wordt met één cel uitgebreid (de rand van een instrumentenpaneel is een helling).
- Als meer dan **60%** van het frame zou worden gemaskeerd, wordt niets gemaskeerd: bij nachtbeelden heeft de meeste cellen geen volgbare feature, wat er net zo uitziet als een wijzerplaat.

De melding: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, of, boven 60%, een melding die uitlegt dat er niets wordt gemaskeerd.

Het offline pad leert dezelfde FlowMask uit 4 runs van 90 opeenvolgende frames, verspreid over de video, op 960 x 540 ([Offline](reconstruction-offline.md)).

## Beeldkwaliteit en advies {#frame-quality-and-advice}

`QualityWatcher` beoordeelt elk keyframe en kiest **één** instructie, zodat de overlay "langzamer" kan zeggen terwijl er nog tijd is.

Per frame meet hij, alleen op de wereldpixels (alle pixels als het masker minder dan 5% overlaat):

- **scherpte**: variantie van de Laplace - de standaardmaat in één keer, en ze reageert op precies wat bewegingsonscherpte vernietigt;
- **helderheid**: gemiddeld grijsniveau, 0-255.

Scherpte heeft geen absolute schaal (een nachtetappe en een heldere straat verschillen een orde van grootte, beide scherp), dus wordt ze beoordeeld tegen de **lopende mediaan van deze opname**: de laatste 90 frames, waarvan er 20 nodig zijn voordat er een oordeel komt. Elk frame wordt vergeleken met de geschiedenis *vóór* het zelf wordt toegevoegd, zodat een lange wazige stretch de mediaan niet naar zichzelf toe kan trekken.

| Conditie | Test |
|---|---|
| vlak | scherpte hoogstens 1,0 (een laadscherm, een muur, lucht) |
| donker | helderheid onder 26 |
| wazig | scherpte onder 0,55 van de mediaan, en niet vlak |

Het advies, de eerste die past wint (geordend op hoe hard het de scan blokkeert):

| Situatie | Advies | Niveau |
|---|---|---|
| minder dan 20 frames | `Getting a feel for the picture…` | ok |
| vlak | `Nothing to measure — point the camera at the level, not at the sky.` | stop |
| donker | `Too dark to reconstruct. Headlights on, or drive this stretch in daylight.` | stop |
| wazig | `Blurred — slow down.` | warn |
| minder dan de helft van de frames gevolgd | `Losing track — slow down and keep more of the level in view.` | warn |
| minder dan 40% van de gevolgde frames samengevoegd | `Positions are good but depth is not sticking. Drive nearer the scenery.` | warn |
| zwakke plekken aanwezig | `N thin spots — the map marks them.` | ok |
| anders | `Good — keep going.` | ok |

De niveaus kleuren het advies van de overlay (groen / oranje / rood). De **scherpte**-balk van de overlay is de scherpte van het frame ten opzichte van de mediaan. (De code heeft ook "Blurred, and the camera is not moving. Check the capture." voor een stilstaande camera; de scan meldt de camera altijd als bewegend, dus die wordt niet getoond.)

Het advies-**tekst** en de meldingen van het venster staan hier in het Engels, zoals de app ze toont: de scanner heeft nog geen Nederlandse teksten.
