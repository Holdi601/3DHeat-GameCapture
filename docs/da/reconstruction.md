---
title: Banerekonstruktion
nav_order: 6
lang: "da"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Banerekonstruktion fra spil {#level-reconstruction-from-gameplay}

Gå langsomt igennem en bane, eller kør et løb, og scanneren gør det, skærmen viste, til en `.glb`,
som 3DHeat-vieweren indlæser som kontekst under telemetrien - den samme filkontrakt, som
Unreal-eksportøren skriver. Den er til tilfældet, hvor ingen har eksporteret kortet, og spillets filer
ikke kan læses; en motoreksport eller en spilfilseksport er nøjagtig, dette er et estimat.

## Pipelinen {#the-pipeline}

```text
 billeder            keyframes            dybde                positur              fusion              output
 --------            ---------            -----                -------              ------              ------
 Windows Graphics -> billedændrings   ->  Depth Anything V2 -> visuel odometri   -> volumen med       -> marching cubes
 Capture, eller en   tærskel             (ONNX Runtime,        (ORB + PnP), eller   besatte celler      -> jord/konstruktion
 videofil            (adaptiv)           letterboxed)          Forza-telemetri,     + dækningsgitter   -> vertex-farve
                                                               eller en VGGT-løsning (live kort,        -> .glb
                                                                                    svage steder)
                     HUD-/cockpitmasker, råd om billedkvalitet, skala fra jordplanet
```

| Trin | Live-scanning (`heat3d_capture.ui`) | Offline (`reconstruct`) | Side |
|---|---|---|---|
| Billeder | skærm, vindue eller video, skaleret til forvalgets længste side | video, samplet to gange (løsningsplan og fusionsinterval) | [Optagelse](reconstruction-capture.md) |
| Keyframes | beholdes efter hvor meget billedet ændrede sig, tærskel tilpasset optagelsen | hver `--fuse-interval`. sekund | [Optagelse](reconstruction-capture.md#keyframes) |
| Masker | ændringsbaseret `ScreenMask`, derefter flowbaseret `FlowMask` efter 40 keyframes | `FlowMask` lært af fire kørsler af videoen; ikke anvendt på løseren | [Optagelse](reconstruction-capture.md#what-is-not-the-world) |
| Dybde | ONNX-model på den bedste GPU-backend | PyTorch Depth Anything V2 Small | [Dybde](reconstruction-depth.md) |
| Positur | visuel odometri, eller nøjagtig Forza-telemetri | VGGT-vinduer syet sammen til én sti, interpoleret | [Positur](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Skala | kamerahøjde over jorden (1,15 m) én gang, eller telemetri | den løste stis egne enheder | [Positur](reconstruction-pose.md#scale) |
| Fusion | vægtede besatte celler, sparsomme voxels; dækningsgitter | det samme | [Fusion](reconstruction-fusion-and-texture.md) |
| Output | `.glb`, jord-/konstruktionsdele, vertex-farve, centimeter | det samme | [.glb-output](glb-output.md) |

Kode: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - en scannings indstillinger og tempo; `reconstruct.py` - keyframes om til geometri;
`offline.py` - den offline-sti), med trinene i `capture/`, `depth/`, `pose/`, `fusion/`
og `geometry/`.

## Hvor nøjagtigheden kommer fra {#where-accuracy-comes-from}

Dybde ud fra et enkelt kamera er kun rigtig op til en ukendt skala - et billede af et rum og af et
dukkehus er det samme billede. Så netværket får lov til at gøre det, det er godt til (relativ form,
kanter, tynde strukturer), og skala og kamerasti kommer fra et sted, der kender dem:

| Spil | Kamerasti | Skala |
|---|---|---|
| Forza Horizon / Motorsport med telemetri slået til | nøjagtig, fra Data Out, interpoleret til hvert billedes optagetidspunkt | nøjagtig: dybden forankres ved at triangulere features mellem to kendte positurer |
| Alt andet, live | visuel odometri, kædet billede til billede | fastlagt én gang ud fra en antaget kamerahøjde over jorden |
| En optagelse, offline | VGGT, løst over overlappende vinduer | løsningens egne enheder (ikke metriske) |

Det ene tal, scanneren får at vide i stedet for at måle, er spillets **vandrette synsfelt** (90 grader
som standard i vinduet; racingspil ligger nærmere 65). For smalt, og banen rekonstrueres for dyb; for
bredt, og den bliver flad.

## Fortæl brugeren tidligt {#telling-the-user-early}

En scanning er en fysisk handling - nogen går igennem en bane i flere minutter - og den dyre fejl er at
gennemføre gåturen og så opdage, at den ikke var god. Så vinduet måler denne maskines dybdegennemstrømning,
før noget kan starte, og siger, hvordan scanningen bliver ([Kørsel](runtime.md#what-to-expect-from-this-machine));
under scanningen viser det et dækningskort med nummererede svage steder, sporingens tilstand, en
gangfartsbjælke, en skarphedsbjælke og én instruktion ad gangen, både i vinduet og i et klik-igennem-overlay
over spillet ([Scanningsvinduet](reconstruction-scan-ui.md)).

## Målt på syntetisk grundsandhed {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` tegner et 12 x 8 m rum (4 m højt) fra en kendt kamerasti, med analytisk
(ikke netværks-) dybde, og rekonstruerer det med 0,2 m voxels. Den hævder, at mere end 90 % af billederne
placeres, at den gennemsnitlige stifejl er under 0,35 m (værst under 1 m), at den tilbagelagte afstand
ligger inden for 10 % af sandheden, at rummet kommer ud med den rigtige bredde inden for 1,5 m, at over
75 % af vægfladen ligger inden for 0,45 m af en rigtig væg, at en overblik-gang med opmåling scorer klart
bedre dækning end at gå lige frem, og at en scene uden features afvises i stedet for at blive opdigtet.
Analytisk dybde isolerer positur, skala og fusion fra netværket; hvordan netværket klarer sig på rigtigt
spil, er et særskilt spørgsmål, som ingen syntetisk scene besvarer. `tests/test_track_width.py` kontrollerer,
at en lap kørt uden for midten på en vej med kendt bredde rekonstrueres til vejens bredde, ikke kun til
den kørte linje.

## Sider {#pages}

- [Scanningsvinduet](reconstruction-scan-ui.md) - hver kontrol, genvej og overlay-element
- [Optagelse, masker og billedkvalitet](reconstruction-capture.md)
- [Dybde](reconstruction-depth.md)
- [Kamerapositur og skala](reconstruction-pose.md)
- [Fusion, dækning og farve](reconstruction-fusion-and-texture.md)
- [.glb-output](glb-output.md)
- [Offline-rekonstruktion](reconstruction-offline.md)
