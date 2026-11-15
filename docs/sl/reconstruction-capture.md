---
title: "Zajem, maske in kakovost okvirjev"
nav_order: 2
lang: "sl"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Zajem, maske in kakovost okvirjev {#capture-masks-and-frame-quality}

Koda: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py), [`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py), [`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py), [`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py), [`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## Od kod prihajajo okvirji {#where-frames-come-from}

Cilj vira je eden od naslednjih:

| Cilj | Vir | Opombe |
|---|---|---|
| `monitor:<n>` | ves monitor, živo | "Whole screen" v oknu s številko v "Which" |
| `window:<title>` | eno okno, živo | "A window" v oknu z naslovom v "Which" |
| pot do datoteke | video datoteka | "A video file" v oknu; katerikoli format, ki ga OpenCV zna brati |

### Živi zajem: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` uporablja paket `windows-capture`, ki ovije **Windows Graphics Capture** – javni API, ki ga uporabljajo snemalniki zaslona. V igro se ne vstavlja nič. Kazalec se ne zajame in ne riše se rumen okvir zajema.

Knjižnica za zajem dostavlja okvirje v povratnem klicu na niti kompozitorja in pričakuje, da se takoj vrne. Zato povratni klic samo kopira okvir (medpomnilnik se ponovno uporablja), pretvori BGRA v RGB, spremeni velikost, mu pritisne časovni žig in ga da v čakalno vrsto s **4 okvirji**. Ko je vrsta polna, se **najstarejši okvir izpusti** in števec se poveča: zaostajanje naj stane okvirje, ne pomnilnika ali pravilnosti, živi prikaz pa naj pokaže, kje je igralec zdaj. Izpuščeni okvirji se prikažejo v statistični vrstici okna, več kot polovica izpuščenih pa sproži namig.

Vsak okvir nosi `t` (sekunde od začetka zajema) in `monotonic` (surovi `time.monotonic()` ob zajemu), isto uro, s katero se žigosajo paketi telemetrije – zato se lahko pozi Forze poravnajo z okvirji.

`windows-capture` je pri preverjanju odvisnosti neobvezen: brez njega se video datoteka vseeno lahko skenira.

### Video datoteke {#video-files}

`VideoSource` bere z OpenCV, pretvori v RGB in spremeni velikost. Vsebnik brez hitrosti okvirov se obravnava kot 30 fps. Časovni žigi so indeks okvirja, deljen s hitrostjo okvirov; datoteka nima stenske ure, zato telemetrije ni mogoče poravnati z videom.

### Ločljivost {#resolution}

Okvirji se pri viru spremenijo tako, da je daljša stranica velikost zajema iz predloge (Draft 640, Balanced 960, Detailed 1280 px), z interpolacijo po površini. Okvir 4K ima trideset-krat več pikslov, kot jih uporablja model globine.

## Ključni okvirji {#keyframes}

Skoraj vsak okvir zajema je odvečen: stoja na mestu ustvari sto pogledov na eno stvar. Rekonstrukcija pa želi *paralakso*. Zato se okvir ohrani glede na **to, koliko se je slika spremenila od zadnjega ohranjenega okvira**, ne glede na uro.

`picture_change(a, b)`:

1. oba okvirja se pretvorita v sivino in zmanjšata na mrežo 16 x 16 povprečij blokov (povprečja blokov se odzivajo na premikanje slike, ne na zrnavost, listje, utripanje ali HUD);
2. povprečna absolutna razlika, kot delež 255;
3. kadar je znana maska sveta, se vsak blok utež z deležem, ki je svet, ne kokpit, zato blok, ki je pol armaturne plošče, šteje za polovico (uporabljeno, ko maska pokrije več kot 5 % uteži mreže).

Prag se **prilagaja zajemu**: prvih 30 okvirjev uporablja začetno vrednost predloge (0,020 / 0,010 / 0,004), nato pa kvantil predloge (0,85 / 0,65 / 0,40) zadnjih 240 izmerjenih sprememb, nikoli pod 0,0001. Okvir se ohrani, kadar njegova sprememba doseže prag; prvi okvir je vedno ohranjen. Fiksni prag ne more delovati med prizori – sprememba iz okvirja do okvirja v temni kabini je majhen delež tiste v svetli, teksturirani sobi – medtem ko "ohrani najbolj razgibano tretjino" pomeni isto v obeh. Prag v uporabi se pošlje z vsako posodobitvijo napredka (`ScanProgress.threshold`), vrstice hitrosti hoje v oknu in prekrivnem sloju pa merijo zadnjo spremembo glede nanj (`ScanProgress.toward_next_view`).

Samo ohranjeni okvirji gredo skozi model globine in rekonstrukcijo. Okvirji se ne shranjujejo, razen če jih kdo zahteva (`keep_frames`); 160 jih ostane za barvanje mreže (glejte [barva](reconstruction-fusion-and-texture.md#colour)).

Skeniranje se konča, ko ga ustavite, ko zmanjka videa, ali ob časovni ali številski meji ključnih okvirjev.

## Kaj ni svet {#what-is-not-the-world}

Dve stvari v igralnem okvirju nista geometrija nivoja, obe pa uničita rekonstrukcijo:

- **HUD.** Nišan je najbolj ponovljiva značilnost v katerem koli okvirju. Iskalnik značilnosti ga ima zelo rad, med vsakima dvema okvirjema se popolnoma ujema, vsako ujemanje pa je dokaz, da se kamera ni premaknila – kar stisne celotno rekonstrukcijo.
- **Stvari, pritrjene na kamero.** Orožje, pokrov motorja, okvir kabine, armaturna plošča. Prava geometrija v napačnem koordinatnem sistemu: zlita se razmaže vzdolž celotne poti.

Dva detektorja ju najdeta. Oba ustvarita masko (255 = svet, 0 = ni svet) ali `None`, dokler ni dovolj dokazov; `None` vedno pomeni "uporabi vse", nikoli "ne uporabi ničesar".

Maska se uporabi:

- pri **zaznavanju značilnosti** v vizualni odometriji (maskiranje nišana iz izhoda, medtem ko mu dovolimo glasovanje za pozo, bi odpravilo vidni simptom in ohranilo škodljivega);
- na **zlite piksle**, da se ne zlije geometrija kokpita;
- na merilo **ostrine in svetlosti**, ker je kokpit vedno popolnoma ostr;
- na **spremembo slike**, ki odloča o ključnih okvirjih.

**Ne** uporabi se na okvirje, ki gredo offline rešivcu VGGT (glejte [Rekonstrukcija brez povezave](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: kar se ne spreminja {#screenmask-what-does-not-change}

Uporablja se od prvega ključnega okvirja, dokler FlowMask ni pripravljen.

- Vsak okvir se pretvori v sivino, prepolovi in zamegli (Gaussov filter 3 x 3), da se ne bere kot gibanje en piksel jitterja v statičnem elementu HUD-a.
- Absolutna razlika vsakega piksla od prejšnjega okvirja se sešteje v eksponentno povprečje (zatiranje 0,9), zato maska sledi HUD-u, ki se pojavi ali izgine sredi skeniranja.
- Uči se samo iz okvirjev, kjer je znano, da se kamera premika (v skeniranju: ko je vsaj en okvir sledilo) – nepremična kamera naredi vse statično.
- Po **12** učnih okvirjih je piksel statičen, kadar je njegova povprečna sprememba pod **0,22** mediane spremembe okvirja – relativno, zato prag sledi, kako hitro se igralec premika.
- Če je več kot **45 %** okvirja prebranega kot statičnega, premisa ne drži (meni, posnetek), zato se ne maskira ničesar.
- Maska se zoži za en piksel (robovi HUD-a z glajenjem ne pripadajo nobeni strani) in se spet povečajo na polno velikost.

Opomba v oknu: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected` ali `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: kar nikoli ne potuje {#flowmask-what-never-travels}

Kokpit ni statičen: igle se premikajo, števec vrtljajev trepeta, mini zemljevid se vrti, zato detektor sprememb te piksle šteje za svet – in so najslabše značilnosti, ki jih lahko dobi rešivec poze. FlowMask zastavi boljše vprašanje: **katere značilnosti vztrajajo, ne da bi potovale?**

- Pri živem skeniranju se uči enkrat, iz prvih **40 ključnih okvirjev** (v sivini); nato za preostanek skeniranja nadomesti ScreenMask.
- Okvirji se razrežejo na okna po **30** okvirov, prekrivajoča se za polovico. V vsakem oknu se seje do **800** kotov (`goodFeaturesToTrack`, kakovost 0,01, razmak 8 px) in sledi piramidalnemu Lucas-Kanadeju (21 x 21, 4 nivoji) z **naprej-nazaj preverjanjem**: sled, katere povratni tok ne pristane v 1 px od začetka, se izpusti, ker bi sledilnik, ki se zanese na sosednji vzorec, ustvaril prav podpis "vztraja, a ne potuje", ki ga iščemo. Okna, krajša od 20 okvirjev, se preskočijo. Kratka okna so pomembna: v dolgem teku skoraj vsaka značilnost sveta zapusti okvir in dokazi se stanjšajo na nič.
- Neto pot vsake preživele značilnosti se primerja z **2 % širine okvirja**: pod to je "zataknjena", nad to "premikajoča se". Števci se nabirajo na mreži **24 x 24** celic glede na to, kje se je značilnost začela.
- Celica je blokirana, kadar vsebuje vsaj 2 zataknjeni značilnosti in več zataknjenih kot premikajočih se, **in** je vsaj 3 od njenih 8 sosedov prav tako blokiranih (sama celica je šum; temni posnetki jih proizvedejo veliko).
- Ohranijo se samo blokirane regije, **povezane z robom okvirja**. Vse, kar je pritrjeno na kamero, doseže rob zaslona; kar sedi na sredini in ne potuje, je izginjajoča točka – pri vožnji naprej cesta naravnost pred nami nima toka in je najbolj zaželena geometrija.
- Preostala regija se poveča za eno celico (rob armaturne plošče je gradient).
- Če bi bilo maskirano več kot **60 %** okvirja, se ne maskira ničesar: na nočnih posnetkih večina celic ne vsebuje sledljive značilnosti, kar izgleda enako kot brezina.

Opomba: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels` ali, nad 60 %, sporočilo, ki pojasni, da ne maskira ničesar.

Offline pot se uči enak FlowMask iz 4 posnetkov po 90 zaporednih okvirjev, razporejenih po videu, pri 960 x 540 ([Rekonstrukcija brez povezave](reconstruction-offline.md)).

## Kakovost okvirjev in nasveti {#frame-quality-and-advice}

`QualityWatcher` oceni vsak ključni okvir in izbere **eno** navodilo, da lahko prekrivni sloj reče "zavij počasneje", medtem ko je še čas.

Na okvir meri, samo na pikslih sveta (vsi pikseli, če maska pusti manj kot 5 %):

- **ostrina**: varianca Laplaceovega operatorja – standardna enoprehodna mera, ki se odziva prav na to, kar motni zamegli;
- **svetlost**: povprečna sivinska vrednost, 0–255.

Ostrina nima absolutne skale (nočni prizor in svetla ulica se razlikujeta za velikostni red, oba sta ostra), zato se presoja glede na **tekočo mediano tega zajema**: zadnjih 90 okvirjev, s potrebnima 20, preden se sploh presoja. Vsak okvir se primerja z zgodovino *pred* njegovim dodajanjem, da dolg zamegljen odsek ne more potegniti mediane navzdol, da bi se sama s seboj ujela.

| Pogoj | Preizkus |
|---|---|
| ravno | ostrina največ 1,0 (nalagalni zaslon, zid, nebo) |
| temno | svetlost pod 26 |
| zamegljeno | ostrina pod 0,55 mediane in ni ravno |

Nasvet, prvo ujemanje zmaga (razvrščeno po tem, kaj najbolj ovira skeniranje):

| Položaj | Nasvet | Stopnja |
|---|---|---|
| manj kot 20 okvirjev | Getting a feel for the picture… | ok |
| ravno | Nothing to measure — point the camera at the level, not at the sky. | stop |
| temno | Too dark to reconstruct. Headlights on, or drive this stretch in daylight. | stop |
| zamegljeno | Blurred — slow down. | warn |
| manj kot polovica okvirjev sledena | Losing track — slow down and keep more of the level in view. | warn |
| manj kot 40 % sledenih okvirjev zlitih | Positions are good but depth is not sticking. Drive nearer the scenery. | warn |
| obstajajo šibke točke | N thin spots — the map marks them. | ok |
| sicer | Good — keep going. | ok |

Prekrivni sloj obarva nasvet (zeleno / oranžno / rdeče). Vrstica **ostrine** v prekrivnem sloju je ostrina okvirja glede na mediano. (V kodi je tudi "Blurred, and the camera is not moving. Check the capture." za nepremično kamero; skeniranje vedno javi, da se kamera premika, zato se ne prikaže.)
