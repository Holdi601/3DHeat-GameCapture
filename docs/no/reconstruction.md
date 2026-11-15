---
title: Nivårekonstruksjon
nav_order: 6
lang: "no"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Nivårekonstruksjon fra spilling {#level-reconstruction-from-gameplay}

Gå sakte gjennom et nivå, eller kjør en bane, så gjør skanneren om det skjermen viste til en
`.glb`-fil. Visningsprogrammet 3DHeat laster den som bakgrunn under telemetrien. Det er samme
filkontrakt som Unreal-eksportøren skriver. Verktøyet er til for når ingen eksporterte kartet, og
spillets filer ikke kan leses. En eksport fra motoren eller en eksport av spillfiler er eksakt. Dette
er et anslag.

## Løypen {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Trinn | Direkte skanning (`heat3d_capture.ui`) | Frakoblet (`reconstruct`) | Side |
|---|---|---|---|
| Bilder | skjerm, vindu eller video, skalert til forhåndsinnstillingens lengste side | video, samplet to ganger (løsningsplan og fusjonsintervall) | [Opptak](reconstruction-capture.md) |
| Nøkkelbilder | beholdes etter hvor mye bildet endret seg, terskelen tilpasses opptaket | hver `--fuse-interval` sekund | [Opptak](reconstruction-capture.md#keyframes) |
| Masker | endringsbasert `ScreenMask`, deretter flytbasert `FlowMask` etter 40 nøkkelbilder | `FlowMask` lært fra fire kjøringer av videoen; ikke brukt på løseren | [Opptak](reconstruction-capture.md#what-is-not-the-world) |
| Dybde | ONNX-modell på den beste GPU-backend | PyTorch Depth Anything V2 Small | [Dybde](reconstruction-depth.md) |
| Posisjon | visuell odometri, eller eksakt Forza-telemetri | VGGT-vinduer sydd sammen til én bane, interpolert | [Posisjon](reconstruction-pose.md), [Frakoblet](reconstruction-offline.md) |
| Skala | kameraets høyde over bakken (1,15 m) én gang, eller telemetri | den løste banens egne enheter | [Posisjon](reconstruction-pose.md#scale) |
| Fusjon | vektet belegg, sparsomme voksler; dekningsnett | det samme | [Fusjon](reconstruction-fusion-and-texture.md) |
| Utdata | `.glb`, bakke- og konstruksjonsdeler, fargen fra hjørnepunktene, centimeter | det samme | [`.glb`-utdata](glb-output.md) |

Kode: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - en skannings innstillinger og tempo; `reconstruct.py` - nøkkelbilder til geometri;
`offline.py` - den frakoblede banen), med trinnene i `capture/`, `depth/`, `pose/`, `fusion/` og
`geometry/`.

## Hvor nøyaktigheten kommer fra {#where-accuracy-comes-from}

Monokulær dybde stemmer bare opp til en ukjent skala. Et bilde av et rom og av et dukkehus er det
samme bildet. Nettverket får derfor gjøre det det er godt til (relativ form, kanter, tynne
strukturer). Skala og kamerabane kommer fra et sted som kjenner dem:

| Spill | Kamerabane | Skala |
|---|---|---|
| Forza Horizon / Motorsport med telemetri på | eksakt, fra Data Out, interpolert til hver rammes opptakstid | eksakt: dybden forankres ved å triangulere kjennetegn mellom to kjente posisjoner |
| Alt annet, direkte | visuell odometri, kjedet fra ramme til ramme | låst én gang ut fra en antatt kamerahøyde over bakken |
| Et opptak, frakoblet | VGGT, løst over overlappende vinduer | løsningens egne enheter (ikke metriske) |

Det ene tallet skanneren får fortalt i stedet for å måle, er spillets **horisontale synsfelt** (90 grader
som standard i vinduet; racingspill ligger nærmere 65). For smalt, og nivået rekonstrueres for dypt.
For bredt, og det flater ut.

## Si fra tidlig {#telling-the-user-early}

En skanning er en fysisk handling: noen går gjennom et nivå i flere minutter. Den dyre feilen er å
fullføre gangen og så oppdage at den ikke var god. Derfor måler vinduet hvor raskt denne maskinen kan
beregne dybde før noe kan starte, og sier hvordan skanningen blir ([Kjøretid](runtime.md#what-to-expect-from-this-machine)).
Under skanningen viser det et dekningskart med nummererte svake punkter, sporingsstatus, en fartslinje
for gangtempo, en skarphetslinje og én instruksjon om gangen. Det gjelder både i vinduet og i et
klikkbart overlegg over spillet ([Skannevinduet](reconstruction-scan-ui.md)).

## Målt mot syntetisk fasit {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` tegner et rom på 12 x 8 m (4 m høyt) fra en kjent kamerabane, med analytisk
dybde (ikke fra nettverket). Det rekonstruerer rommet med 0,2 m voksler. Testen sjekker at mer enn 90
% av rammene plasseres, at gjennomsnittlig feil i banen er under 0,35 m (verst under 1 m), at tilbakelagt
avstand er innen 10 % av sannheten, at rommet får riktig bredde innen 1,5 m, at over 75 % av veggflaten
ligger innen 0,45 m fra en ekte vegg, at en gange i stil med oppmåling gir klart bedre dekning enn å gå
rett frem, og at en scene uten kjennetegn avvises i stedet for å bli funnet opp. Analytisk dybde
isolerer posisjon, skala og fusjon fra nettverket. Hvordan nettverket klarer seg på ekte spilling, er et
eget spørsmål som ingen syntetisk scene kan svare på. `tests/test_track_width.py` sjekker at en bane
kjørt utenfor midten på en vei med kjent bredde rekonstruerer veiens bredde, ikke bare linjen som ble
kjørt.

## Sider {#pages}

- [Skannevinduet](reconstruction-scan-ui.md) - alle knapper, hurtigtaster og elementer i overlegget
- [Opptak, masker og bildekvalitet](reconstruction-capture.md)
- [Dybde](reconstruction-depth.md)
- [Kameraposisjon og skala](reconstruction-pose.md)
- [Sammensmelting, dekning og farge](reconstruction-fusion-and-texture.md)
- [`.glb`-utdata](glb-output.md)
- [Offline rekonstruksjon](reconstruction-offline.md)
