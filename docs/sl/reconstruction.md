---
title: Rekonstrukcija nivoja
nav_order: 6
lang: "sl"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonstrukcija nivoja iz igranja {#level-reconstruction-from-gameplay}

Počasi se sprehodite po nivoju ali vozite po progi, skener pa spremeni, kar je pokazal zaslon, v
`.glb`, ki ga pregledovalnik 3DHeat naloži kot kontekst pod telemetrijo – enaka pogodba datoteke, kot jo
zapisuje izvoznik za Unreal. Namenjen je primeru, ko nihče ni izvozil zemljevida in datotek igre ni
mogoče prebrati; izvoz iz pogona ali izvoz datotek igre je natančen, to je ocena.

## Potek {#the-pipeline}

```text
 okvirji              ključni okvirji      globina              poza                 zlivanje            izhod
 --------            ------------------   -----                ----                 --------            -----
 Windows Graphics ->prag spremembe   ->  Depth Anything V2 -> vizualna odometrija -> volumen zasedenosti -> marching cubes
 Capture, ali        slike (prilagodljiv) (ONNX Runtime,        (ORB + PnP), ali     + mreža pokritosti  -> tla/konstrukcije
 video datoteka                            z robovi)            telemetrija Forze,   (živi zemljevid,   -> barva oglišč
                                                                ali rešitev VGGT     šibka mesta)        -> .glb

                     maske HUD / kabine, nasveti o kakovosti okvirjev, merilo z ravnino tal
```

| Faza | Skeniranje v živo (`heat3d_capture.ui`) | Brez povezave (`reconstruct`) | Stran |
|---|---|---|---|
| Okvirji | monitor, okno ali video, zmanjšan na najdaljšo stranico predizbora | video, vzorčen dvakrat (načrt reševanja in interval zlivanja) | [Zajem](reconstruction-capture.md) |
| Ključni okvirji | ohranjeni glede na to, koliko se je slika spremenila; prag se prilagodi zajemu | vsakih `--fuse-interval` sekund | [Zajem](reconstruction-capture.md#keyframes) |
| Maske | `ScreenMask` na podlagi sprememb, nato `FlowMask` na podlagi toka po 40 ključnih okvirjih | `FlowMask`, naučen iz štirih prehodov videa; ni uporabljen v reševalniku | [Zajem](reconstruction-capture.md#what-is-not-the-world) |
| Globina | model ONNX na najboljšem zaledju GPU | PyTorch Depth Anything V2 Small | [Globina](reconstruction-depth.md) |
| Poza | vizualna odometrija ali natančna telemetrija Forze | okna VGGT, zlepljena v eno pot, interpolirana | [Poza](reconstruction-pose.md), [Brez povezave](reconstruction-offline.md) |
| Merilo | višina kamere nad tlemi (1,15 m) enkrat ali telemetrija | lastne enote rešene poti | [Poza](reconstruction-pose.md#scale) |
| Zlivanje | uteženo zasedanje, redki voksli; mreža pokritosti | enako | [Zlivanje](reconstruction-fusion-and-texture.md) |
| Izhod | `.glb`, deli tal/konstrukcij, barva oglišč, centimetri | enako | [Izhod .glb](glb-output.md) |

Koda: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` – nastavitve in tempo skeniranja; `reconstruct.py` – ključne okvirje v geometrijo;
`offline.py` – pot brez povezave), faze pa so v `capture/`, `depth/`, `pose/`, `fusion/` in
`geometry/`.

## Od kod prihaja natančnost {#where-accuracy-comes-from}

Enooka globina je pravilna le do neznanega merila – fotografija sobe in fotografija hišice za lutke
sta ista slika. Zato naj mreža dela tisto, kar ji najbolje gre (relativna oblika, robovi, tanke
strukture), merilo in pot kamere pa prihajata od nekod, kjer ju poznajo:

| Igra | Pot kamere | Merilo |
|---|---|---|
| Forza Horizon / Motorsport s telemetrijo | natančna, iz Data Out, interpolirana na čas zajema vsakega okvirja | natančno: globina je pritrjena s triangulacijo značilnosti med dvema znanima pozama |
| Vse drugo, v živo | vizualna odometrija, povezana od okvirja do okvirja | enkrat določeno iz predpostavljene višine kamere nad tlemi |
| Posnetek, brez povezave | VGGT, rešen po prekrivajočih se oknih | lastne enote rešitve (ne metrične) |

Edina številka, ki skenerju je povedana namesto da jo izmeri, je **vodoravni vidni kot** igre (v
oknu privzeto 90 stopinj; dirkalne igre so bliže 65). Preozek kot, in nivo se rekonstruira globlji,
kot je; preširok, in se splošči.

## Uporabnika opozoriti zgodaj {#telling-the-user-early}

Skeniranje je fizično dejanje – nekdo več minut hodi po nivoju – draga napaka pa je, da dokončate
sprehod in ugotovite, da ni bil dober. Zato okno izmeri pretočnost globine na tem računalniku, preden
se karkoli lahko začne, in pove, kakšno bo skeniranje
([Izvajanje](runtime.md#what-to-expect-from-this-machine)); med skeniranjem pokaže zemljevid pokritosti
z oštevilčenimi šibkimi mesti, zdravje sledenja, vrstico hitrosti hoje, vrstico ostrine in po eno
navodilo naenkrat, v oknu in v prosojnem prekrivnem sloju čez igro, ki prepušča klike
([Okno skeniranja](reconstruction-scan-ui.md)).

## Izmerjeno na sintetični referenčni resnici {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` upodobi sobo 12 x 8 m (visoko 4 m) z znane kamere poti, z analitično (ne
mrežno) globino, in jo rekonstruira z vokseli po 0,2 m. Preveri, da je postavljenih več kot 90 %
okvirjev, da je povprečna napaka poti manjša od 0,35 m (najslabša pod 1 m), da je prehojena razdalja v
10 % resnične, da soba dobi pravilno širino na 1,5 m natančno, da je več kot 75 % površine sten na
razdalji 0,45 m od resničnega zidu, da sprehod v slogu meritve dosega jasno boljšo pokritost kot hoja
naravnost naprej, in da je prizor brez značilnosti zavrnjen namesto izmišljen. Analitična globina
loči pozo, merilo in zlivanje od mreže; kako se mreža obnese na resničnem igranju, je ločeno
vprašanje, na katerega nobeden sintetični prizor ne odgovori. `tests/test_track_width.py` preveri, da
krog, odpeljan izven središča ceste znane širine, rekonstruira širino ceste, ne le odpeljane črte.

## Strani {#pages}

- [Okno za pregled](reconstruction-scan-ui.md) – vsak gumb, bližnjica in element prekrivanja
- [Zajem, maske in kakovost okvirjev](reconstruction-capture.md)
- [Globina](reconstruction-depth.md)
- [Položaj kamere in merilo](reconstruction-pose.md)
- [Zlivanje, pokritost in barva](reconstruction-fusion-and-texture.md)
- [Izhod .glb](glb-output.md)
- [Rekonstrukcija brez povezave](reconstruction-offline.md)
