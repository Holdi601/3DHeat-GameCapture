---
title: "Samenvoegen, dekking en kleur"
nav_order: 5
lang: "nl"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Samenvoegen, dekking en kleur {#fusion-coverage-and-colour}

Code: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py), [`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py), [`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py), [`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py), [`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Elk geplaatst keyframe werkt twee schaarse roosters tegelijk bij: het **oppervlaktevolume**, dat het mesh wordt, en het **dekkingsrooster**, dat zegt hoeveel je erin moet geloven en waar je naar terug moet. Beide worden per keyframe bijgewerkt, niet aan het eind, omdat de dekkingskaart is wat de speler stuurt.

## Van diepte naar punten {#from-depth-to-points}

Voor elk keyframe waarvan de pose bekend is **én** waarvan de diepte een schaal heeft:

1. Elke tweede pixel in elke richting wordt gebruikt (`PIXEL_STRIDE = 2`; naburige pixels van één oppervlak zijn geen onafhankelijke metingen).
2. De diepte wordt door de affiene fit van het frame omgezet naar meters.
3. Alleen behouden tussen **0,35 m** (dichterbij is het wapen, de HUD, de motorkap) en **60 m** (monoculaire fout groeit ruwweg met het kwadraat van de afstand, dus verre punten zijn ruis in de vorm van geometrie), en alleen op wereldpixels van het masker.
4. Opgetild door het cameramodel en door de pose de wereld in verplaatst.
5. Elk punt draagt de kleur van de pixel.

Een frame dat is geplaatst maar geen diepteschaal heeft, telt als *geplaatst* maar niet als *samengevoegd*.

## Het oppervlaktevolume {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - de voxel is de "Surface detail" van het venster.

### Gewogen bezetting, geen TSDF {#weighted-occupancy-not-a-tsdf}

Een afgeknot signed distance field snijdt langs elke pixelstraal en krijgt dunne structuren en schone vrije ruimte goed, omdat het weet dat een straal *door* lege ruimte ging. Dat betekent de straal lopen voor elk van honderden miljoenen pixels. Dit volume telt daarentegen **gewogen bezetting** per voxel op en draait marching cubes op het gladgestreken resultaat: snel genoeg om tijdens het scannen te draaien, op een machine zonder bruikbare GPU, en de uitvoer is een gesloten oppervlak in plaats van een puntenwolk. Het nadeel: dunne structuren en vrije ruimte zijn slechter dan een TSDF die zou halen.

### Een frame integreren {#integrating-a-frame}

- Punten worden in voxels gebonden (`floor(point / voxel)`).
- Elke geraakte voxel krijgt `gewicht x sqrt(aantal / max_aantal)`, waarbij `aantal` is hoeveel van de punten van het frame in die voxel vielen, en `gewicht = max(0,1; poseconfidentie)`. Wortel: voorbij een punt tellen meer pixels van hetzelfde oppervlak vanaf dezelfde plek niet meer als bewijs; het wegen op poseconfidentie houdt een twijfelachtige pose ervan af het oppervlak te verschuiven.
- Kleur is een lopend gewogen gemiddelde per voxel.

Het rooster is **schaars**: een afgelegde route raakt een klein deel van zijn begrenzingsvak. Voxelcoördinaten worden in één 64-bits sleutel gepakt (21 bits per as, tot ±1.048.575 voxels - bij 0,25 m ongeveer ±262 km) en opgezocht met een gesorteerde array en binair zoeken, volledig vectorgewijs.

### Het mesh extraheren {#extracting-the-mesh}

1. Voxels met een gewicht onder **0,35** worden weggegooid (losse punten aan de randen van silhouetten zouden piekjes worden).
2. Gewichten worden geschaald naar het **75e percentiel** over de scan en afgekapt op 1.
3. De bezette ruimte wordt gesneden in **blokken van 64 voxels** per zijde, elk met een **halo van 3 voxels** van de data van de buren (zonder die sluit elke blokgrens zich tot een muur, en komt een weg eruit als een rij dozen).
4. Het veld van elk blok wordt gladgestreken met een Gauss (sigma 0,8 voxel) om het rimpelen van de dieptereis weg te halen.
5. **Eerste pas**: het 99e percentiel van het gladgestreken veld, over alle blokken bemonsterd (hoogstens 2 miljoen waarden), zet één globale niveauschaal. Per blok normaliseren zou een losse uitschieter tot een compleet oppervlak in zijn eigen lege blok promoveren.
6. **Tweede pas**: het veld van elk blok gedeeld door die schaal, marching cubes op **0,5**. Een driehoek hoort bij het blok waarin zijn **zwaartepunt** valt, zodat driehoeken die over een naad lopen precies één keer worden uitgezonden.
7. Hoekpunten gaan naar wereldeenheden in de middelpunten van de voxels; elk hoekpunt neemt de kleur van zijn voxel (middelgrijs waar het buiten een bezette voxel valt).

Blokgewijze extractie maakt een scan op baanschaal mogelijk: één dicht array over een vierkant van een kilometer op 0,25 m zou miljarden cellen zijn. `tests/test_track_scale.py` legt vast dat het op die schaal werkt, met geheugen evenredig aan wat er gescand is.

### Grond en structuur {#ground-and-structure}

`classify` labelt elke driehoek naar zijn normaal (georiënteerd met de geëxtraheerde normalen van de hoekpunten): binnen **35 graden van recht omhoog** is het `ground`, al het andere `structure`. De viewer tekent grond massief en structuren bijna transparant. **Water krijgt nooit een label** - het is op vorm niet van vlakke grond te onderscheiden, en een verkeerd label zou een binnenplaats als meer laten zien. Elk label wordt één deel van de `.glb` ([De .glb-uitvoer](glb-output.md)).

## Dekking {#coverage}

`CoverageGrid(voxel=0.5)` registreert per cel van een halve meter vier dingen die niet hetzelfde zijn:

| Term | Opgeslagen | Score (elk beperkt tot 0..1) | Waarom het apart telt |
|---|---|---|---|
| Hoe vaak gezien | aantal keyframes dat de cel zag | `count / 3` | één keer is een gok met niets om tegen te middelen |
| Vanuit hoeveel richtingen | som van de eenheidsvectoren van de kijkrichting | `(1 - spreiding) / (1 - 0,93)`, waarbij spreiding = lengte van de som / aantal | twintig frames die recht op een muur afrijden hebben geen parallax tussen zich; twee zichten dertig graden uit elkaar zijn meer waard |
| Vanaf hoe ver | dichtstbijzijnde kijkafstand | `1 - dichtstbij / 40 m` | diepte-fout groeit ruwweg met het kwadraat van de afstand |
| Hoe goed de camera was geplaatst | beste poseconfidentie | de confidentie | geometrie die met een twijfelachtige pose is samengevoegd, komt op de verkeerde plek |

De punten van een frame worden eerst per cel gegroepeerd, zodat tienduizend pixels van één muur tellen als één waarneming vanuit één richting.

**Kwaliteit = het product van de vier termen**, niet het gemiddelde: het zijn voorwaarden die elk moeten gelden. Een plek die tweehonderd keer uit één richting op zestig meter is gezien, is slecht waargenomen, en een gemiddelde zou dat verbergen achter één uitstekende term.

Kerncijfers (`summary`): bezette cellen, het aandeel met kwaliteit van minstens 0,5 ("% well seen" in het venster), gemiddelde kwaliteit, en volume.

### Zwakke plekken {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. cellen met kwaliteit onder 0,35 zijn zwak;
2. zwakke cellen worden gegroepeerd op **samenhang** (26-buurt, union-find over alleen de bezette cellen - niet een raster over het begrenzingsvak, wat op een lange rit miljoenen lege cellen zou zijn);
3. groepen van minder dan 8 cellen worden genegeerd;
4. de reden van elke groep is de meest voorkomende *zwakste term* van haar cellen, en haar positie het gemiddelde van haar cellen;
5. gesorteerd van groot naar klein (dan op slechtste kwaliteit), hoogstens 8.

| Reden | Getoond advies |
|---|---|
| weinig waarnemingen | Seen only once or twice — walk past it again. |
| één richting | Only seen from one angle. Step sideways and look at it again. |
| veraf | Only seen from far away. Get closer to it. |
| slechte tracking | The camera was not well located here. Approach it more slowly. |

Samenhang doet ertoe: groeperen op een vast blokraster meldt één verwaarloosde zijkamer als vele aparte ringen, en niemand kan dan onderscheiden of het acht plekken zijn of één plek die acht keer telt.

### De plattegrondweergave {#the-plan-view}

`top_down(resolution)` projecteert de cellen op x/z en houdt de **beste** kwaliteit per kolom aan (iemand die in een kamer staat, heeft slechte dekking van het plafond en uitstekende dekking van de vloer; middelen zou de kamer oranje schilderen). Kolommen die nooit zijn gezien, worden apart gemarkeerd. Het venster tekent het op 200 x 200, de overlay op 120 x 120 ([Het scanvenster](reconstruction-scan-ui.md#the-coverage-map)).

### Is dit te reconstrueren? {#is-this-reconstructable}

Elke 25 samengevoegde frames, zodra er minstens 500 cellen zijn:

| Bevinding | Oordeel | Melding (ingekort) |
|---|---|---|
| minder dan 2% van de cellen heeft een kijkspreiding onder 0,93 | not reconstructable | Almost no parallax. Either the camera never looks aside, or the tracking is drifting so the same surface never lands twice in the same place. Check the placed-frame count: if that is high, it is drift. |
| mediane dichtstbijzijnde afstand boven 25 m | not reconstructable | Everything was seen from N m away or further ... Get closer to what you want. |
| minder dan 6% met goede spreiding | reconstructable, warned | Thin parallax — the geometry will be rough. Moving sideways relative to what you are looking at helps most. |

Lage parallax heeft twee oorzaken die dit niet uit elkaar kan houden, en daarom noemt de melding beide.

De oordelen en meldingen staan in het Engels, zoals de app ze toont.

## Kleur {#colour}

De kleur per voxel van het samenvoegen is goedkoop en live, en wazig: elke pixel in een cel van een kwart meter wordt gemiddeld, ook die die vanaf dertig meter schuin zijn gezien. Dus wordt het mesh bij het exporteren één keer opnieuw ingekleurd, uit de frames zelf:

- **Bewaarde frames**: tot **160** keyframes (beeld en pose), gekozen met reservoirbemonstering zodat ze over de hele scan verspreid zijn en niet alleen over het einde.
- **Per hoekpunt** (`project_colours`) draagt elk bewaard frame bij als het hoekpunt voor de camera ligt en binnen het beeld valt, het oppervlak niet meer dan ongeveer 70 graden van recht op de camera gericht is (`|normaal . zicht| > 0,34`), het dichterbij is dan **35 m**, en er niets dichterbij voor stond (hieronder).
- Elk zo'n zicht krijgt een score `gerichtheid x (1 - afstand / 35)`, zodat een dicht recht zicht beter is dan een verre schuine blik. De **4 hoogst scorende** zichten van elk hoekpunt worden bewaard - in welke volgorde de frames ook staan, een beter zicht vervangt het zwakste van de vier - en worden gemengd, gewogen met diezelfde score.
- **Afscherming**: in elk frame worden de eigen hoekpunten van het mesh die in beeld zijn in een dieptebuffer van cellen van 2 pixels getekend, met per cel de dichtstbijzijnde. Een hoekpunt dat meer dan `0,3 m + 5%` van zijn afstand achter het dichtstbijzijnde in zijn cel ligt, was in dat frame verborgen - een muur tussen de camera en de weg daarachter - en dat zicht telt niet mee. De test kent alleen het mesh: een afscherming die nooit is samengevoegd (een passerende auto, een cockpitstijl buiten het HUD-masker) wordt niet gevangen.
- Een hoekpunt dat geen frame zag, houdt zijn voxelkleur; een hoekpunt met geen van beide is middelgrijs (zwart zou als gat lezen).

Kleur wordt geschreven als `COLOR_0` per hoekpunt, niet als tekstuuratlas. De standaardlook van de viewer is een grijze kaart met verzadigde hitte; kleur is er om de weg te vinden op een gescand circuit, waar geometrie alleen die niet van de berm onderscheidt, en wordt getoond achter de schakelaar *Vastgelegde kleur* van de viewer in het paneel Achtergrond / level. Een atlas zou de bestandsgrootte vermenigvuldigen en een unwrapper vereisen, voor een weergave die bewust niet de standaard is. Blender en andere glTF-tools lezen `COLOR_0`.
