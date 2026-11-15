---
title: Nivårekonstruktion
nav_order: 6
lang: "sv"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Nivårekonstruktion från spelande {#level-reconstruction-from-gameplay}

Gå sakta genom en nivå, eller kör ett lopp, så gör skannern om det skärmen visade till en `.glb`
som 3DHeat-visaren laddar som sammanhang under telemetrin - samma filkontrakt som
Unreal-exportören skriver. Den är till för fallet där ingen exporterade kartan och spelets filer
inte går att läsa; en motorexport eller en spelfilsexport är exakt, den här är en uppskattning.

## Flödet {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Steg | Live-skanning (`heat3d_capture.ui`) | Offline (`reconstruct`) | Sida |
|---|---|---|---|
| Bildrutor | bildskärm, fönster eller video, skalade till förinställningens längsta sida | video, samplad två gånger (lösningsplan och fusionsintervall) | [Inspelning](reconstruction-capture.md) |
| Nyckelbilder | behålls efter hur mycket bilden ändrats, tröskeln anpassas till inspelningen | var `--fuse-interval`:e sekund | [Inspelning](reconstruction-capture.md#keyframes) |
| Masker | ändringsbaserad `ScreenMask`, sedan flödesbaserad `FlowMask` efter 40 nyckelbilder | `FlowMask` inlärd från fyra körningar av videon; inte tillämpad på lösaren | [Inspelning](reconstruction-capture.md#what-is-not-the-world) |
| Djup | ONNX-modell på den bästa GPU-backend | PyTorch Depth Anything V2 Small | [Djup](reconstruction-depth.md) |
| Pose | visuell odometri, eller exakt Forza-telemetri | VGGT-fönster sydda till en väg, interpolerad | [Pose](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Skala | kamerans höjd över marken (1,15 m) en gång, eller telemetri | den lösta vägens egna enheter | [Pose](reconstruction-pose.md#scale) |
| Fusion | viktad ockupation, glesa voxlar; täckningsnät | samma | [Fusion](reconstruction-fusion-and-texture.md) |
| Utdata | `.glb`, mark-/strukturdelar, hörnfärg, centimeter | samma | [Utdatan .glb](glb-output.md) |

Kod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - en skannings inställningar och takt; `reconstruct.py` - nyckelbilder till geometri;
`offline.py` - offline-vägen), med stegen i `capture/`, `depth/`, `pose/`, `fusion/` och `geometry/`.

## Var noggrannheten kommer ifrån {#where-accuracy-comes-from}

Monokulärt djup är rätt bara upp till en okänd skala - en bild av ett rum och av ett dockskåp är
samma bild. Så nätverket får göra det det är bra på (relativ form, kanter, tunna strukturer), och
skala och kamerans väg kommer från någonstans som känner dem:

| Spel | Kamerans väg | Skala |
|---|---|---|
| Forza Horizon / Motorsport med telemetri på | exakt, från Data Out, interpolerad till varje bildrutas inspelningstid | exakt: djupet förankras genom att triangulera särdrag mellan två kända poser |
| Allt annat, live | visuell odometri, kedjad bildruta för bildruta | fixerad en gång från en antagen kamerahöjd över marken |
| En inspelning, offline | VGGT, löst över överlappande fönster | lösningens egna enheter (inte metriska) |

Det enda talet skannern får veta i stället för att mäta är spelets **horisontella synfält** (90
grader som standard i fönstret; racingspel ligger närmare 65). För smalt, och nivån rekonstrueras
djupare än den är; för brett, och den plattas ut.

## Berätta tidigt för användaren {#telling-the-user-early}

En skanning är en fysisk handling - någon går genom en nivå i flera minuter - och det dyra felet
är att gå klart och upptäcka att den var värdelös. Så fönstret mäter den här datorns djuptakt
innan något kan starta och säger hur skanningen kommer att bli
([Körtid](runtime.md#what-to-expect-from-this-machine)); under skanningen visar det en täckningskarta
med numrerade svaga punkter, spårningens hälsa, en hastighetsmätare för gången, en skarphetsmätare
och en instruktion i taget, i fönstret och i ett klicka-igenom-överlägg över spelet
([Skanningsfönstret](reconstruction-scan-ui.md)).

## Mätt mot syntetiskt facit {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` renderar ett 12 x 8 m rum (4 m högt) från en känd kamerabana, med analytiskt
(inte nätverksbaserat) djup, och rekonstruerar det med 0,2 m voxlar. Den kontrollerar att över 90 %
av bildrutorna placeras, att det genomsnittliga banfelet är under 0,35 m (värsta under 1 m), att den
gångna sträckan ligger inom 10 % av sanningen, att rummet får rätt bredd inom 1,5 m, att över 75 % av
väggytan ligger inom 0,45 m från en verklig vägg, att en undersökningsliknande gång ger tydligt bättre
täckning än att gå rakt fram, och att en scen utan särdrag avvisas i stället för att hittas på. Analytiskt
djup isolerar pose, skala och fusion från nätverket; hur nätverket klarar riktigt spelande är en annan
fråga som ingen syntetisk scen besvarar. `tests/test_track_width.py` kontrollerar att ett varv körs
utanför mitten på en väg med känd bredd rekonstrueras till vägens bredd, inte bara den körda linjen.

## Sidor {#pages}

- [Skanningsfönstret](reconstruction-scan-ui.md) - varje kontroll, snabbtangent och överlägg
- [Inspelning, masker och bildrutekvalitet](reconstruction-capture.md)
- [Djup](reconstruction-depth.md)
- [Kamerans pose och skala](reconstruction-pose.md)
- [Fusion, täckning och färg](reconstruction-fusion-and-texture.md)
- [Utdatan .glb](glb-output.md)
- [Offline-rekonstruktion](reconstruction-offline.md)
