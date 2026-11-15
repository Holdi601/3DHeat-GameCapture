---
title: "Položaj kamere in merilo"
nav_order: 4
lang: "sl"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Položaj kamere in merilo {#camera-pose-and-scale}

Globinska karta pove, kako daleč so stvari od *neke* točke gledanja. Da iz mnogih naredimo en nivo, moramo vedeti, kje je bila vsaka točka gledanja in v katerih enotah. Ta stran pokriva žive poti; offline rešitev feed-forward je na [Rekonstrukcija brez povezave](reconstruction-offline.md).

Koda: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py), [`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py), [`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py), [`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py), [`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py), [`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## Model kamere {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` zgradi luknjično kamero iz **vodoravnega vidnega polja**, ki ga nastaviš v oknu: `fx = (width / 2) / tan(fov / 2)`, kvadratni piksli (`fy = fx`), glavna točka v središču okvira. Igra ne objavi svoje projekcije, zato je to edino predpostavljeno število: premajhno, in prizor se zdi globlji, kot je. Offline pot uporablja 65 stopinj.

`Pose` je shranjena kot **svet-iz-kamere**: `rotation` (3 x 3) in `translation` = središče kamere v svetu, kar želijo trajektorija, pokritost in prekrivni sloj.

## Vizualna odometrija (privzeta) {#visual-odometry-the-default}

`VisualOdometry` sledi vsakemu ključnemu okviru glede na prejšnjega:

1. **Značilnosti**: ORB, do 1500 na okvir, zaznane samo na masi sveta (glejte [Zajem](reconstruction-capture.md#what-is-not-the-world)).
2. **Ujemanja** z prejšnjim ključnim okvirom: grobo iskanje, Hammingova razdalja, navzkrižno preverjanje (samo medsebojno najboljši pari).
3. **Dvig v 3D**: globina prejšnjega okvira je že v svetovnih enotah, zato njegovi ujeti pikslji postanejo svetovne točke.
4. **Postavitev kamere**: `solvePnPRansac` med tem točkami (napaka projekcije 3 px, zaupanje 0,999, 200 iteracij). Premik pride v istih enotah, zato **merilo prečka vrzel**.
5. **Zasidranje globine tega okvira**: njena lastna napovedana inverzna globina se prilagodi (`fit_scale`) glede na globine notranjih točk PnP, in cikel se ponovi.

**Prvi okvir** je izhodišče: identična poza, njegov afin globine pa je bodisi kalibracija tal spodaj bodisi, brez nje, identiteta (rekonstrukcija je potem sama s seboj skladna, a brez enot).

Poza potrebuje vsaj **18 notranjih točk RANSAC** – jasno več kot minimum PnP-ja, to je šest, ker je rešitev iz komaj dovolj točk ravno tista, ki je samozavestno napačna.

### Zaupanje {#confidence}

Vsak umeščen okvir dobi zaupanje med 0 in 1, ki uteži njegovo zlivanje in pokritost:

| Poza iz | Zaupanje |
|---|---|
| telemetrije | 1,0 |
| rešitve feed-forward | 0,85 |
| vizualnega sledenja | `inliers / matches x min(1, inliers / 60)` |

### Ko sledenje odpove {#when-tracking-breaks}

Okvir, ki ga ni mogoče umestiti, se prijavi, nikoli ne ugiba: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Poza se ne zabeleži in ničesar se ne zlije. Nadaljevanje od zadnje poze ali začetek novega izhodišča bi premaknilo naslednji kos nivoja na poljuben odmik – šiv, ki izgleda kot prava geometrija.

Po prekinitvi se vsak nov okvir **relokalizira** glede na bazo preteklih ključnih okvirjev (vsak četrti sledeni okvir se doda, največ 120, najstarejši se izpusti), najnovejši najprej, z istim korakom ujemanja in PnP. Dokler eden ne uspe, se okvirji izpuščajo. Relokalizirani okvir se nadaljuje v istem koordinatnem sistemu. Relokalizacije se štejejo in prikažejo v oknu (`N recovered`).

### Zapiranje zanke: izklopljeno {#loop-closure-off}

Ista baza podpira tudi zapiranje zanke: ujemanje s ključnimi okvirji iz veliko prej, da se zazna ponovni obisk in trajektorija se pripne nazaj nanj. **Privzeto je izklopljeno, skener ga nikoli ne vklopi** (`Reconstructor(loop_closure=False)`). Na ponavljajočem se okolju – relijska etapa, koridor, vrsta dreves – je vsak del videti kot vsak drug, ujemanje značilnosti pa potrjuje lažne ponovne obiske, kar drži kamero blizu začetka, medtem ko vozi naprej. Da bi to delalo prav, je potrebno prepoznavanje krajev (vokabular vreč besed ali naučen deskriptor) in geometrijsko preverjanje proti zemljevidu, kar ni zgrajeno.

Kadar je vklopljeno iz kode, zapiranje potrebuje: ključni okvir, ki je star vsaj 60 ključnih okvirjev, znotraj 6 m od trenutne poze, ujemanje z vsaj 90 notranjimi točkami, premik poze za več kot 0,02 m in manj kot 6 m. Tudi takrat samo nadomesti trenutno pozo; ni graf poz in ne premakne prejšnjih okvirjev ali zlite geometrije.

## Telemetrijske poze {#telemetry-poses}

Z vklopljeno možnostjo **Racing telemetry (Forza) -> Listen for position data** pride pot kamere iz Forzinega Data Out, ne iz slik (`ForzaPoseSource`):

- Nit posluša na `127.0.0.1:<port>` (privzeto 5300) z enakim zaznavanjem postavitve kot snemalniki ([Forza](telemetry-forza.md)); paketi se uporabijo, medtem ko je `isRaceOn` nastavljen. Zaseden port se prijavi, ne sproži izjeme: telemetrija je nadgradnja, skeniranje pa gre naprej vizualno.
- Vsak paket se žigosa z **monotonim časom prihoda** – isto uro, s katero zajem žigosa okvirje. Igrin lasten časovni žig šteje od nečesa nepovezanega, zato se ne uporablja za poravnavo. Jitter zanke za ena do dve milisekundi je pri 200 km/h približno 6 cm.
- Ohranja se drseči medpomnilnik 30 sekund. Poza okvira se **interpolira** iz vzorcev na obeh straneh njegovega časa zajema: položaj linearno, rotacija sferično (mešana matrika ni rotacija in bi popačila vsako točko). Preko vrzeli, daljše od **0,35 s**, ali zunaj medpomnilnika, poze ni.
- `pose_from_forza`: kamera je postavljena na avto (odmik kamere za zasledovanje ni objavljen). **Položaji se ohranijo točno, kot jih pošilja igra**: svet Forze je že y navzgor (x in z po zemljevidu, y višina), kar je isto, kako datoteke krogov in poti zapisujejo, zato površina pristane na istih koordinatah kot krogi, posneti nad njo. (Prejšnja različica je zamenjala y in z za svet "z navzgor" in položila progo na bok.)
- Rotacija je yaw, nato pitch, nato roll, s smermi, prebranimi iz posnetih krogov: smer vožnje `atan2(dx, dz)` je enaka yawu, naklon navzgor je enak minus pitchu (pozitivno je nos navzdol), roll je pozitiven, kadar je vzmet na desni strani stisnjena (pozitivno spusti desno stran). Osi avta (x desno, y navzgor, z naprej) se nato spremenijo v osi kamere (x desno, y navzdol, z naprej) z obračanjem y.
- Svet Forze je **levosučen** in koordinatni sistem kamere ni, zato je rezultirajoča matrika svet-iz-kamere zrcaljenje (determinanta -1), skener pa je levosučen kot datoteke krogov. Interpolacija ni prizadeta (zavoj med dvema takima pozama je pravilna rotacija).
- Kadar okvir nima telemetrijske poze (vrzel), rekonstruktor za ta okvir pade nazaj na **vizualno sledenje**, pri čemer nadaljuje od zadnje telemetrijske poze, in se vrne k pozam vira takoj, ko ta spet odgovori. PnP vrne samo rotacije, zato se v zrcaljenem svetu rešuje tako, da se svet zrcali čez z, zrcaljenje pa se na koncu vrne nazaj; okvir pristane v igrinih koordinatah. Šele če tudi vizualno sledenje odpove, je okvir neizsledovan.

### Merilo globine iz telemetrije {#depth-scale-from-telemetry}

Igra pove, kje je kamera, ne pa kako daleč je kaj, zato je treba še vedno zasidrati globino vsakega okvira – vendar ne z verižnim povezovanjem od okvira nič, čigar enota je poljubna, medtem ko so poze v metrih. Namesto tega se značilnosti, ujete med prejšnjim in trenutnim okvirom (vsaj 8), **triangulirajo neposredno iz obeh znanih poz**, v metrih, globinska karta pa se prilagodi točkam pred kamero. Vsak okvir se zato zasidra glede na telemetrijo, zato ni verige, ki bi odnašala.

Če sta obe pozi bliže kot **0,05 m**, so žarki skoraj vzporedni in triangulacija je šum, zato okvir ostane nezasidran: popolnoma postavljen, a ne zlit ("positioned, but its depth has no scale yet"). Zato okno šteje *umeščene* in *zlite* okvirje ločeno.

## Merilo {#scale}

Vizualna odometrija pravilno veriži relativno merilo, a celoten nivo še vedno pluta na eni neznani faktorju. Relativni izhod Depth Anything je v poljubnih enotah, zato pustitev prvega okvira kot identiteta postavi svet v nekaj metrov od kamere v poljubni velikosti.

`GroundCalibrator` pripne ta faktor glede na **to, kako visoko je kamera nad tlemi**, izmerjeno na **prvem ključnem okviru** in, kadar tam ni uporabnih tal, na naslednjih:

- Višina kamere: **1,15 m** (višina oči voznika) – okno jo vedno uporabi; skripte lahko dajo 1,70 m (`WALKING_HEIGHT`, stoječ igralec) ali `None` (brez kalibracije).
- Vzorec tal: vrstice 62–92 % od vrha okvira (pod obzorjem, nad pokrovom motorja ali orožjem) in stolpci 30–70 % čez širino (stran od berme).
- Vsak piksel tam z uporabno napovedjo se dvigne z globino `1 / predicted` v enotah mreže; točke pod optično osjo dajo višino pod kamero. Njihova mediana je višina kamere v enotah mreže, zato je `metri na enoto = 1,15 / mediana`, afin okvira pa `scale = 1 / metri_na_enoto`, odmik 0.
- Zaupa se samo, če je vsaj 200 vzorcev tal in **razpršenost** (mediana absolutnega odklona nad mediano) pod **0,60**.
- Na prvem ključnem okviru postane kalibracija enota izhodišča, zato je skener v metrih od začetka. Kadar prvi ključni okvir nima uporabnih tal, skener začne brez enot, in vsak naslednji sledeni ključni okvir se preizkusi, največ **30 okvirjev** v vsem. Prva, ki se kalibrira, da *metre na enoto*: mediana čez pas tal globine, ki jo tla nakazujejo, deljena z globino, ki jo je veriga dala temu okviru. Vse, kar je že zlito, je v enoti prvega okvira, zato se faktor ne vrača v verigo; uporabi se na celoten nivo (in na označene točke), ko se zapiše, in na razdaljo, prikazano medtem. Velikost voksla je potem v enotah prvega okvira, zato se njena velikost v metrih razlikuje od nastavitve za ta faktor.
- Po 30 okvirjih brez tal skener ostane brez enot in to pove.
- S telemetrijo se kasnejši ključni okvirji ne preizkušajo: globina je zasidrana na metre telemetrije.

Biti znotraj deset odstotkov prave velikosti je boljše kot biti iztirjen za faktor tisoč; telemetrija, kjer je na voljo, to naredi nepotrebno. Opomba je prikazana v oknu pod vrstico sledenja, kot `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (z `found on frame N, so the level is scaled by F when it is written`, kadar je prišlo kasneje), `no usable ground in the first N frames - sizes are relative, not metres` ali `in metres, from the telemetry's positions`.

## Prilagajanje snopov in dolge poti (ni povezano) {#bundle-adjustment-and-long-tracks-not-wired-in}

Dva kosa obstajata za prihodnji reševalec oken in **ju skener ne uporablja**:

- **`FeatureTracks`** ohranja identiteto značilnosti čez stotine okvirjev s sledenjem Lucas-Kanade (600 značilnosti, ponovno zasejane pod 60 %, naprej-nazaj toleranca 1 px, nove značilnosti 10 px od obstoječih), kar prilagajanje snopov potrebuje – ujemanje deskriptorjev med zaporednimi okvirji da samo pare.
- **`bundle_adjust`** izboljša okno poz in točk skupaj z `scipy.optimize.least_squares` (regija zaupanja, mehka-L1 izguba z merilom 2 px, eksplicitni vzorec redkosti Jacobijana, fiksne kamere se vrnejo natančno). Preizkušeno proti znanim resnicam v `tests/test_bundle.py`.

`WindowedOdometry` ju združi (okna po 12 ključnih okvirjev, reševanje na vsake 3 ključne okvirje, prvi dve kameri fiksni, točke z napako nad 6 px se izpustijo, skoki nad 6-kratnikom nedavnega koraka se zavrnejo). Njegov docstring beleži, da je na posnetem videu **stisnil pot in bil bistveno počasnejši** od sledenja okvir za okvirom, z lestvico (merilo) in bootstrapom na globini kot znanima vzrokoma in tretjim vzrokom, ki ni bil identificiran. Zato ostaja odometrija okvir za okvirom privzeta; možna popravka, zapisana v kodi, je bootstrap z esencialno matriko dveh pogledov, z bazno linijo, fiksirano iz kalibracije tal.
