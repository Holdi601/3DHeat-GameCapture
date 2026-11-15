---
title: "Fusion, täckning och färg"
nav_order: 5
lang: "sv"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusion, täckning och färg {#fusion-coverage-and-colour}

Kod: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Varje placerad nyckelbildruta uppdaterar två glesa rutnät samtidigt: **ytvolymen**, som blir nätet, och **täckningsrutnätet**, som säger hur mycket man ska tro på det och var man ska gå tillbaka. Båda uppdateras per nyckelbildruta, inte i slutet, eftersom täckningskartan är det spelaren styr efter.

## Från djup till punkter {#from-depth-to-points}

För varje nyckelbildruta vars pose är känd **och** vars djup har en skala:

1. Varje andra pixel i varje riktning används (`PIXEL_STRIDE = 2`; grannpixlar av samma yta är inte oberoende mätningar).
2. Djupet omvandlas till meter med bildrutans affina anpassning.
3. Behålls bara mellan **0,35 m** (närmare är vapnet, HUD:en, motorhuven) och **60 m** (monokulärt fel växer ungefär med avståndet i kvadrat, så fjärran punkter är brus med formen av geometri), och bara på världspixlar i masken.
4. Lyfts genom kameramodellen och flyttas in i världen av posen.
5. Varje punkt bär pixelns färg.

En bildruta som är placerad men saknar djupskala räknas som *placerad* men inte *fusionerad*.

## Ytvolymen {#the-surface-volume}

`SurfaceVolume(voxel=0.25)`. Voxeln är fönstrets "Surface detail".

### Viktad ockupation, inte en TSDF {#weighted-occupancy-not-a-tsdf}

En trunkerad signerad avståndsfält skär längs varje pixels stråle och klarar tunna strukturer och rena fria ytor rätt, eftersom den vet att en stråle passerade *genom* tomt utrymme. Det kräver att gå längs strålen för var och en av hundratals miljoner pixlar. Den här volymen ackumulerar i stället **viktad ockupation** per voxel och kör marching cubes på det utjämnade resultatet. Det är tillräckligt snabbt för att köra medan man skannar, på en maskin utan användbart GPU, och utdata är en sluten yta snarare än ett punktmoln. Kostnaden: tunna strukturer och fritt utrymme blir sämre än en TSDF skulle ge.

### Integrera en bildruta {#integrating-a-frame}

- Punkter binns i voxlar (`floor(point / voxel)`).
- Varje berörd voxel får `weight x sqrt(count / max_count)`, där `count` är hur många av bildrutans punkter som föll i den, och `weight = max(0.1, pose confidence)`. Kvadratroten: efter en punkt slutar fler pixlar från samma yta, från samma plats, att vara belägg. Viktning med posens säkerhet hindrar en tveksam pose från att knuffa ytan.
- Färg är ett löpande viktat medelvärde per voxel.

Rutnätet är **glest**: en gången rutt berör en liten bråkdel av sin omslutande låda. Voxelkoordinater packas i en 64-bitars nyckel (21 bitar per axel, upp till +-1 048 575 voxlar - vid 0,25 m ungefär +-262 km) och slås upp med en sorterad array och binärsökning, helt vektoriserat.

### Extrahera nätet {#extracting-the-mesh}

1. Voxlar med vikt under **0,35** släpps (enstaka punkter vid silhuettkanter skulle bli spikar).
2. Vikterna skalas med **75:e percentilen** över skanningen och klipps till 1.
3. Det ockuperade utrymmet delas i **block om 64 voxlar** per sida, vart och ett realiserat med en **3-voxlars halo** av grannarnas data (utan den stängs varje blockgräns till en vägg, och en väg kommer ut som en rad lådor).
4. Varje blocks fält jämnas med en Gauss (sigma 0,8 voxel) för att ta bort skrynkligheten som djupbrus lämnar.
5. **Pass ett**: 99:e percentilen av det jämnade fältet, samplad över alla block (högst 2 miljoner värden), sätter en global nivåskala. Normalisering per block skulle höja ett ensamt extremvärde till en full yta i sitt eget tomma block.
6. **Pass två**: varje blocks fält delas med den skalan, marching cubes vid **0,5**. En triangel hör till blocket dess **tyngdpunkt** faller i, så att trianglar över en söm bara emitteras en gång.
7. Vertiser flyttas till världsenheter vid voxelcentrum; varje vertex tar sin voxels färg (mellangrått där den faller utanför en ockuperad voxel).

Blockvis extraktion är det som gör en skanning i banstorlek möjlig: en tät array över en kilometerstor kvadrat vid 0,25 m skulle vara miljarder celler. `tests/test_track_scale.py` låser att det fungerar i den skalan, med minne proportionellt mot det som skannats.

### Mark och struktur {#ground-and-structure}

`classify` märker varje triangel efter dess normal (orienterad efter de utdragna vertexnormalerna): inom **35 grader från rakt upp** är det `ground` (mark), allt annat `structure` (struktur). Visaren ritar mark solid och strukturer nästan genomskinliga. **Vatten märks aldrig**: det går inte att skilja från platt mark på form, och en fel etikett skulle återge en borggård som en sjö. Varje etikett blir en del av `.glb`-filen ([.glb-utdata](glb-output.md)).

## Täckning {#coverage}

`CoverageGrid(voxel=0.5)` registrerar, per halvmeterscell, fyra saker som inte är samma sak:

| Term | Lagrat | Poäng (var och en klippt till 0..1) | Varför den räknas separat |
|---|---|---|---|
| Hur många gånger sedd | antal nyckelbildrutor som såg cellen | `count / 3` | en gång är en gissning utan något att jämföra med |
| Från hur många riktningar | summan av enhetsvy-riktningar | `(1 - spread) / (1 - 0,93)`, där spread = summans längd / antal | tjugo bildrutor som går rakt mot en vägg har ingen parallax mellan sig; två vyer trettio grader isär är mer värda |
| Från hur långt | närmaste visningsavstånd | `1 - nearest / 40 m` | djupfel växer ungefär med avståndet i kvadrat |
| Hur väl kameran placerades | bästa posesäkerhet | säkerheten | geometri fusionerad med en tveksam pose hamnar på fel plats |

En bildrutas punkter grupperas först per cell, så att tiotusentals pixlar på en vägg räknas som en observation från en riktning.

**Kvalitet = produkten av de fyra termerna**, inte medelvärdet. De är villkor som var och en måste uppfyllas. En plats sedd tvåhundra gånger från en riktning på sextio meter är dåligt observerad, och ett medelvärde skulle dölja det bakom en utmärkt term.

Huvudsiffror (`summary`): ockuperade celler, andelen med kvalitet minst 0,5 ("% well seen" i fönstret), medelkvalitet och volym.

### Svaga platser {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. celler med kvalitet under 0,35 är svaga;
2. svaga celler grupperas efter **sammanhang** (26-grannskap, union-find bara över de ockuperade cellerna, inte en rasterkörning över det omslutande området, som på en lång körning är miljontals tomma celler);
3. grupper med färre än 8 celler ignoreras;
4. varje grupps orsak är den vanligaste *svagaste termen* bland dess celler, och dess position medelvärdet av dess celler;
5. sorteras störst först (sedan sämst kvalitet), högst 8.

| Orsak | Visat råd |
|---|---|
| få vyer | Sedd bara en eller två gånger - gå förbi den igen. |
| en riktning | Bara sedd från en vinkel. Gå åt sidan och titta på den igen. |
| långt borta | Bara sedd från långt håll. Kom närmare den. |
| dålig spårning | Kameran var inte väl lokaliserad här. Närma dig den långsammare. |

Sammanhang spelar roll: gruppering efter ett fast blockrutnät rapporterar ett försummat sidorum som många separata ringar, och ingen kan säga åtta platser från en plats räknad åtta gånger.

### Planvyn {#the-plan-view}

`top_down(resolution)` projicerar cellerna på x/z och behåller den **bästa** kvaliteten per kolumn. Någon som står i ett rum har dålig täckning av taket och utmärkt täckning av golvet; ett medelvärde skulle måla rummet gult. Ej observerade kolumner markeras separat. Fönstret ritar den i 200 x 200, overlayn i 120 x 120 ([Skanningsfönstret](reconstruction-scan-ui.md#the-coverage-map)).

### Är detta rekonstruerbart? {#is-this-reconstructable}

Var 25:e fusionerade bildruta, när det finns minst 500 celler:

| Fynd | Bedömning | Meddelande (förkortat) |
|---|---|---|
| färre än 2 % av cellerna har vyspridning under 0,93 | inte rekonstruerbart | Nästan ingen parallax. Antingen tittar kameran aldrig åt sidan, eller så driver spårningen så att samma yta aldrig hamnar två gånger på samma ställe. Kontrollera antalet placerade bildrutor: är det högt, är det drift. |
| medianens närmaste avstånd över 25 m | inte rekonstruerbart | Allt sågs från N m eller längre bort ... Kom närmare det du vill ha. |
| färre än 6 % med god spridning | rekonstruerbart, med varning | Tunn parallax - geometrin blir grov. Att röra sig åt sidan i förhållande till det du tittar på hjälper mest. |

Låg parallax har två orsaker som detta inte kan skilja åt, vilket är varför meddelandet nämner båda.

## Färg {#colour}

Fusionens färg per voxel är billig och live, och suddig: varje pixel i en kvarts meters cell medelvärdesbildas, även de som sågs på kanten från trettio meter. Så vid export färgläggs nätet igen, en gång, från bildrutorna själva:

- **Behållna bildrutor**: upp till **160** nyckelbildrutor (bild och pose), valda med reservoarsampling så att de sprids över hela skanningen i stället för dess svans.
- **Per vertex** (`project_colours`) bidrar varje behållen bildruta om vertexen ligger framför kameran och inom bilden, ytan är vänd högst ungefär 70 grader bort från att möta kameran rakt (`|normal . view| > 0.34`), den är närmare än **35 m**, och inget närmare stod framför den (nedan).
- Varje sådan vy poängsätts `facing x (1 - distance / 35)`, så att en nära vy rakt framifrån slår en avlägsen sned. De **4 högst poängsatta** vyerna för varje vertex behålls - oavsett i vilken ordning bildrutorna kommer, ersätter en bättre vy den svagaste av de fyra - och blandas, viktade med samma poäng.
- **Skymning**: i varje bildruta ritas nätets egna vertiser i sikte in i en djupbuffert med 2-pixlars celler, och den närmaste behålls per cell. En vertex mer än `0,3 m + 5 %` av sitt avstånd bakom den närmaste i sin cell var dold i bildrutan (en vägg mellan kameran och vägen bortom), och den vyn räknas för ingenting. Testet känner bara till nätet: en skymmare som aldrig fusionerades (en passerande bil, en förarhyttsstolpe utanför HUD-masken) fångas inte.
- En vertex som ingen bildruta såg behåller sin voxelfärg. En vertex med ingetdera är mellangrått, eftersom svart skulle läsas som ett hål.

Färg skrivs som per-vertex `COLOR_0`, inte som en texturatlas. Visarens standardutseende är en grå karta under mättad värme. Färgen finns där för att hitta vägen på en skannad bana, där geometrin ensam inte skiljer den från kanten, och visas bakom visarens *Fångad färg*-omkopplare i panelen *Bakgrund / nivå*. En atlas skulle multiplicera filstorleken och behöva en unwrapper, för en vy som medvetet inte är standard. Blender och andra glTF-verktyg läser `COLOR_0`.
