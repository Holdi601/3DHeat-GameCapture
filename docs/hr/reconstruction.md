---
title: Rekonstrukcija razine iz igranja
nav_order: 6
lang: "hr"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Rekonstrukcija razine iz igranja {#level-reconstruction-from-gameplay}

Prođite razinu polako, ili vozite stazu, i skener pretvara ono što je prikazano na ekranu u `.glb`
koji 3DHeat preglednik učitava kao kontekst ispod telemetrije - isti ugovor datoteke koji piše Unreal
izvoznik. Namijenjeno je slučaju kad nitko nije izvezao kartu i kad se datoteke igre ne mogu čitati;
izvoz iz motora ili izvoz datoteka igre je točan, ovo je procjena.

## Tijek {#the-pipeline}

```text
 kadrovi             ključni kadrovi      dubina               položaj              spajanje            izlaz
 -------             ---------------      ------               -------              --------            -----
 Windows Graphics -> prag promjene    ->  Depth Anything V2 -> vizualna odometrija -> volumen zauzeća  -> marching cubes
 Capture, ili        slike (prilagodljiv) (ONNX Runtime,        (ORB + PnP), ili     + mreža pokrivenosti -> tlo/konstrukcija
 video datoteka                          s letterboxom)         telemetrija Forze,    (karta uživo,       -> boja vrhova
                                                                ili VGGT rješenje     slaba mjesta)       -> .glb

                     maske HUD-a i kokpita, savjeti o kvaliteti kadra, mjerilo iz ravnine tla
```

| Korak | Skeniranje uživo (`heat3d_capture.ui`) | Izvanmrežno (`reconstruct`) | Stranica |
|---|---|---|---|
| Kadrovi | monitor, prozor ili video, smanjeni na najdulju stranicu prethodnog podešenja | video, uzorkovan dvaput (plan rješavanja i interval spajanja) | [Snimanje](reconstruction-capture.md) |
| Ključni kadrovi | zadržavaju se prema tome koliko se slika promijenila, prag prilagođen snimanju | svakih `--fuse-interval` sekundi | [Snimanje](reconstruction-capture.md#keyframes) |
| Maske | promjena na temelju `ScreenMask`, zatim na temelju toka `FlowMask` nakon 40 ključnih kadrova | `FlowMask` naučen iz četiri prolaza videa; ne primjenjuje se na rješavač | [Snimanje](reconstruction-capture.md#what-is-not-the-world) |
| Dubina | ONNX model na najboljoj GPU pozadini | PyTorch Depth Anything V2 Small | [Dubina](reconstruction-depth.md) |
| Položaj | vizualna odometrija, ili točna telemetrija Forze | VGGT prozori spojeni u jedan put, interpolirano | [Položaj](reconstruction-pose.md), [Izvanmrežno](reconstruction-offline.md) |
| Mjerilo | visina kamere iznad tla (1,15 m) jednom, ili telemetrija | jedinice riješenog puta | [Položaj](reconstruction-pose.md#scale) |
| Spajanje | ponderirani volumen zauzeća, rijetki vokseli; mreža pokrivenosti | isto | [Spajanje](reconstruction-fusion-and-texture.md) |
| Izlaz | `.glb`, dijelovi tla/konstrukcije, boja vrhova, centimetri | isto | [Izlaz .glb](glb-output.md) |

Kod: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan)
(`session.py` - postavke i tempo skeniranja; `reconstruct.py` - ključni kadrovi u geometriju;
`offline.py` - izvanmrežni put), s koracima u `capture/`, `depth/`, `pose/`, `fusion/` i `geometry/`.

## Odakle dolazi točnost {#where-accuracy-comes-from}

Dubina iz jedne kamere točna je samo do nepoznatog mjerila - fotografija sobe i kućice za lutke su
ista slika. Zato mreži prepuštamo ono u čemu je dobra (relativni oblik, rubovi, tanke konstrukcije), a
mjerilo i put kamere dolaze odakle se znaju:

| Igra | Put kamere | Mjerilo |
|---|---|---|
| Forza Horizon / Motorsport s uključenom telemetrijom | točan, iz Data Outa, interpoliran na vrijeme snimanja svakog kadra | točno: dubina je vezana triangulacijom značajki između dva poznata položaja |
| Sve ostalo, uživo | vizualna odometrija, povezana od kadra do kadra | jednom fiksirano iz pretpostavljene visine kamere iznad tla |
| Snimka, izvanmrežno | VGGT, riješen preko preklapajućih prozora | jedinice samog rješenja (nisu metričke) |

Jedan broj koji skener dobiva od korisnika, a ne mjeri, je **horizontalni kut gledanja** igre (zadano
90 stupnjeva u prozoru; trkaće igre su bliže 65). Preuzak i razina se rekonstruira dublja nego što
jest; preširok i sve se spljošti.

## Javljanje korisniku na vrijeme {#telling-the-user-early}

Skeniranje je fizička radnja - netko hoda razinom nekoliko minuta - a skupi neuspjeh je kad se hod
završi pa se ustanovi da nije bio dobar. Zato prozor prije svega mjeri brzinu dubine na ovom računalu
i kaže kakvo će skeniranje biti ([Runtime](runtime.md#what-to-expect-from-this-machine)); tijekom
skeniranja prikazuje kartu pokrivenosti s numeriranim slabim mjestima, zdravlje praćenja, traku brzine
hodanja, traku oštrine i jednu upute u trenutku, u prozoru i u prozirnom sloju preko igre
([Prozor skeniranja](reconstruction-scan-ui.md)).

## Mjereno na sintetičkoj referentnoj istini {#measured-on-synthetic-ground-truth}

`tests/test_accuracy.py` iscrtava sobu 12 x 8 m (visoku 4 m) iz poznate putanje kamere, s
analitičkom (ne mrežnom) dubinom, i rekonstruira je s vokselima od 0,2 m. Provjerava da je više od 90%
kadrova postavljeno, da je srednja pogreška putanje manja od 0,35 m (najgora manja od 1 m), da je
prijeđena udaljenost unutar 10% istine, da soba ispadne ispravne širine unutar 1,5 m, da je više od
75% zidne površine unutar 0,45 m od pravog zida, da hod nalik pregledu daje jasno bolju pokrivenost od
ravnog hodanja naprijed, i da se scena bez značajki odbije umjesto da se izmisli. Analitička dubina
izolira položaj, mjerilo i spajanje od mreže; kako mreža radi na pravoj igri je zasebno pitanje na
koje nijedna sintetička scena ne odgovara. `tests/test_track_width.py` provjerava da vožnja van
središta ceste poznate širine rekonstruira širinu ceste, a ne samo vozeću liniju.

## Stranice {#pages}

- [Prozor skeniranja](reconstruction-scan-ui.md) - svaka kontrola, prečac i sloj preko ekrana
- [Snimanje, maske i kvaliteta kadra](reconstruction-capture.md)
- [Dubina](reconstruction-depth.md)
- [Položaj kamere i mjerilo](reconstruction-pose.md)
- [Spajanje, pokrivenost i boja](reconstruction-fusion-and-texture.md)
- [Izlaz .glb](glb-output.md)
- [Izvanmrežna rekonstrukcija](reconstruction-offline.md)
