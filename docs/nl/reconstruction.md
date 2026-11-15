---
title: Level-reconstructie
nav_order: 6
lang: "nl"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Level-reconstructie uit gameplay {#level-reconstruction-from-gameplay}

Loop langzaam door een level, of rijd een baan, en de scanner maakt van wat het scherm toonde een `.glb` die de 3DHeat-viewer als context onder de telemetrie laadt - hetzelfde bestandscontract als de Unreal-exporter schrijft. Het is bedoeld voor het geval dat niemand de map heeft geëxporteerd en de bestanden van het spel niet gelezen kunnen worden; een engine-export of een game-bestandsexport is exact, dit is een schatting.

## De pijplijn {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Fase | Live-scan (`heat3d_capture.ui`) | Offline (`reconstruct`) | Pagina |
|---|---|---|---|
| Frames | monitor, venster of video, geschaald naar de langste zijde van de preset | video, twee keer bemonsterd (oplossingsplan en fuse-interval) | [Opname](reconstruction-capture.md) |
| Keyframes | bewaard naar hoeveel het beeld veranderde, drempel aangepast aan de opname | elke `--fuse-interval` seconden | [Opname](reconstruction-capture.md#keyframes) |
| Maskers | op verandering gebaseerde `ScreenMask`, daarna op stroming gebaseerde `FlowMask` na 40 keyframes | `FlowMask` geleerd uit vier runs van de video; niet toegepast op de solver | [Opname](reconstruction-capture.md#what-is-not-the-world) |
| Diepte | ONNX-model op de beste GPU-backend | PyTorch Depth Anything V2 Small | [Diepte](reconstruction-depth.md) |
| Pose | visuele odometrie, of exacte Forza-telemetrie | VGGT-vensters samengevoegd tot één pad, geïnterpoleerd | [Pose](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Schaal | camerahoogte boven de grond (1,15 m) eenmalig, of telemetrie | de eigen eenheden van het opgeloste pad | [Pose](reconstruction-pose.md#scale) |
| Fusie | gewogen bezetting, schaarse voxels; dekkingsraster | hetzelfde | [Fusie](reconstruction-fusion-and-texture.md) |
| Uitvoer | `.glb`, grond-/constructiedelen, kleur per hoekpunt, centimeters | hetzelfde | [De .glb-uitvoer](glb-output.md) |

Code: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan) (`session.py` - de instellingen en het tempo van een scan; `reconstruct.py` - keyframes naar geometrie; `offline.py` - het offline-pad), met de fases in `capture/`, `depth/`, `pose/`, `fusion/` en `geometry/`.

## Waar de nauwkeurigheid vandaan komt {#where-accuracy-comes-from}

Diepte uit één camera klopt alleen tot op een onbekende schaal - een foto van een kamer en van een poppenhuis zijn hetzelfde beeld. Daarom laat het netwerk doen waar het goed in is (relatieve vorm, randen, dunne structuren), en komen schaal en cameratraject van ergens die ze wél kent:

| Spel | Cameratraject | Schaal |
|---|---|---|
| Forza Horizon / Motorsport met telemetrie aan | exact, uit Data Out, geïnterpoleerd naar de opnametijd van elk frame | exact: de diepte wordt verankerd door kenmerken tussen twee bekende posities te trianguleren |
| Al het andere, live | visuele odometrie, frame na frame aaneengeschakeld | één keer vastgelegd vanuit een aangenomen camerahoogte boven de grond |
| Een opname, offline | VGGT, opgelost over overlappende vensters | de eigen eenheden van de oplossing (niet metrisch) |

Het ene getal dat de scanner krijgt in plaats van dat het meet, is het **horizontale gezichtsveld** van het spel (standaard 90 graden in het venster; racespellen liggen dichter bij 65). Te smal, en het level wordt dieper gereconstrueerd dan het is; te breed, en het wordt platgedrukt.

## De gebruiker op tijd waarschuwen {#telling-the-user-early}

Een scan is een fysieke handeling - iemand loopt een level enkele minuten af - en de dure fout is de wandeling afmaken en ontdekken dat hij niets waard was. Daarom meet het venster voordat er iets kan beginnen de dieptedoorvoer van deze computer en zegt het hoe de scan zal worden ([Runtime](runtime.md#what-to-expect-from-this-machine)); tijdens de scan toont het een dekkingskaart met genummerde zwakke plekken, de trackinggezondheid, een balk voor de loopsnelheid, een scherpte-balk en één instructie tegelijk, in het venster en in een klikbare overlay over het spel ([Het scanvenster](reconstruction-scan-ui.md)).

## Gemeten op synthetische grondwaarheid {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` rendert een kamer van 12 x 8 m (4 m hoog) vanaf een bekend cameratraject, met analytische (niet-netwerk) diepte, en reconstrueert die op voxels van 0,2 m. Hij controleert dat meer dan 90% van de frames is geplaatst, de gemiddelde padfout onder 0,35 m ligt (ergste onder 1 m), de afgelegde afstand binnen 10% van de waarheid valt, de kamer de juiste breedte krijgt binnen 1,5 m, meer dan 75% van het wandoppervlak binnen 0,45 m van een echte wand ligt, een inspectiewandeling duidelijk meer dekking haalt dan rechtdoor lopen, en een scène zonder kenmerken wordt geweigerd in plaats van verzonnen. Analytische diepte isoleert pose, schaal en fusie van het netwerk; hoe het netwerk presteert op echte gameplay is een aparte vraag die geen synthetische scène beantwoordt. `tests/test_track_width.py` controleert dat een ronde die uit het midden is gereden op een weg met bekende breedte, de breedte van de weg reconstrueert, niet alleen de gereden lijn.

## Pagina's {#pages}

- [Het scanvenster](reconstruction-scan-ui.md) - elke bediening, sneltoets en overlay-element
- [Opname, maskers en beeldkwaliteit](reconstruction-capture.md)
- [Diepte](reconstruction-depth.md)
- [Camerapose en schaal](reconstruction-pose.md)
- [Fusie, dekking en kleur](reconstruction-fusion-and-texture.md)
- [De .glb-uitvoer](glb-output.md)
- [Offline reconstructie](reconstruction-offline.md)
