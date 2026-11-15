---
title: "Igre: snemanje in proge"
nav_order: 4
lang: "sl"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Igre: snemanje in proge {#games-recording-and-courses}

Kako se snema vsaka podprta igra, kaj pošlje in katere njene proge lahko izvozimo iz igrinih lastnih datotek.

Pravilo je za vse igre enako: proga pride iz datotek, ki jih uporabnik ima, ali pa je rekonstruirana iz uporabnikove lastne vožnje. Šifrirani arhivi se odprejo samo s ključem, ki ga uporabnik že ima. Tukaj ne dobite nobenih ključev in ničesar se ne vdira. Nič ne vstavlja kode v proces igre. Telemetrija prihaja samo iz vmesnikov, ki jih igre objavljajo zanjo (UDP izhodi, deljeni pomnilnik, lastni vtičniki in vmesniki modov). Za to, kamor uporabnik usmeri orodja, še vedno velja licenca te igre.

## Telemetrija {#telemetry}

Vsaka igra na koncu da datoteke `heat3d-lap` ([`lap-format.md`](lap-format.md)) s kanonskimi imeni kanalov in blokom `meta`, ki pove, kaj njihove številke pomenijo: kako je zdrs merjen, ali gre za krožno, relijsko ali arkadno vožnjo ter podlago, kadar jo igra pove. Tako jih bralnik obravnava enako. Vsi ukazi so `python -m heat3d_capture ...` v tem repozitoriju.

| Igra | Kako snemati | Pozicija | Gume in zdrs | Kot drifta | Stanje |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out prek UDP: `heat3d_capture telemetry` (posreduje FH Companionu) – ali FH Companionova lastna `.tele.gz` ob vsakem krogu, naložena skupaj z datoteko kroga | svetovni XYZ | zdrs razmerja, zdrs kota, skupni zdrs na kolo, normiran; hrapavost površine | hitrost v koordinatnem sistemu avta | snemalnik preizkušen; bralnik `.tele.gz` preverjen na pravih krogih |
| Forza Motorsport (vključno z 2023) | enako; ločeno po dolžini paketa | svetovni XYZ | enako | enako | snemalnik preizkušen |
| Assetto Corsa, ACC, AC EVO | deljeni pomnilnik: `telemetry --game ac / acc / acevo` | povprečje točk stika gum | zdrs razmerja in kota (fizikalen, deljen z vrhom na asfaltu); ABS in TC delujeta (ACC, EVO) | hitrost v koordinatnem sistemu avta | snemalnik preizkušen na sintetičnih straneh |
| Assetto Corsa Rally | `telemetry --game acrally` | enako | enako; obremenitve koles; temperature pretvorjene iz kelvinov | hitrost v koordinatnem sistemu avta | snemalnik preizkušen na sintetičnih straneh |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` vklopi privzeti paket `wrc` (datoteka se prej varnostno kopira) | svetovni XYZ | hitrost stika pnevmatike na kolo; zdrs izpeljan | iz osi avta in njegove hitrosti | snemalnik preizkušen na paketih, sestavljenih po dokumentirani postavitvi |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: v `hardware_settings_config.xml` nastavi `<udp enabled="true" extradata="3" port="20777" delay="1" />`, nato `telemetry --game dirtrally2` (ali `dirtrally`, `dirt4`) | svetovni XYZ | hitrost stika na kolo; zdrs izpeljan. Ni kanala za ročno zavoro | iz osi avta in njegove hitrosti | enako |
| Richard Burns Rally (RSF/NGP) | NGP-jeva UDP telemetrija (`udpTelemetry=1`): `telemetry --game rbr` | svet, navzgor os najdena iz etape | pomik vzmeti in sila na kolo; ni hitrosti koles | lastne hitrosti avta | enako; osi in enote hitrosti niso dokumentirane, obdelane so iz podatkov |
| BeamNG.drive | mod protokola `heat3d`: `telemetry --game beamng --install`, nato Options > Other > Protocols > "others" | svet, obrnjen na Y navzgor | hitrost površine kolesa, vrtenje, obremenitev, stik s tlemi; zdrs izpeljan | iz osi avta in njegove hitrosti | snemalnik preizkušen na paketih, sestavljenih iz strukture modula; mod v igri ni preizkušen |
| Trackmania (2020) | vtičnik Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, naložen v razvijalskem načinu Openplanet; ena CSV datoteka na vožnjo v njegovi shrambi | svetovni XYZ | koeficient zdrsa Trackmanie za vsako kolo; ohlapna tla iz materialov koles; v zraku | sprednja in stranska hitrost | bralnik preizkušen; vtičnik v igri ni preizkušen |
| iRacing | lastne datoteke `.ibt`; snemalnik ni potreben | zemljepisna širina, dolžina in višina, položene na tangentno ravnino | zdrs ni shranjen; hitrost zasuka in bočni pospešek | iz hitrosti zasuka glede na pot | bralnik preizkušen na sintetični datoteki |

Kar tudi nobena relijska igra ne pošlje – zdrs gume – bralnik izračuna sam: iz hitrosti točke stika vsakega kolesa glede na hitrost avta, kjer igra eno pošlje (`(kolo - avto) / avto`), oziroma iz vrtenja in polmera kotaljenja, izmerjenega na samem krogu, kjer igra pošlje samo vrtenje. Kot drifta pride iz lastne hitrosti avta (Forza, igre AC, Trackmania, RBR), iz svetovne hitrosti, projicirane na osi avta (EA WRC, DiRT, BeamNG), ali iz smeri avta glede na pot. Ali je avto v zraku, se vidi iz stika koles, obremenitev ali vzmetenja.

Kjer je svet igre levosučen – Forzin je tak – se proga v desnosučnem pregledovalniku zrcalno obrne. To se vidi po krmiljenju in vzmetenju samih krogov. Igre, pri katerih levosučnost ni dokumentirana (RBR, BeamNG, Trackmania), obravnavamo enako: izmerimo jo, ne predpostavimo.

Poleg vožnjih kanalov snemalniki shranijo tudi tisto, kar vsaka igra dodaja: ABS in kontrolo zdrsa v igrah AC, zavorno razmerje, DRS, omejevalnik za bokse, polnjenje (boost) ter življenjsko dobo zavornih oblog in diskov; pri iRacingu nastavitve pomoči, zavorno razmerje, gorivo, temperature olja in vode ter vsak drug kanal, ki ga zapisuje pod svojim imenom.

### Viri in kar še ni potrjeno {#sources-and-what-is-not-yet-confirmed}

- **Forza:** uradna dokumentacija Data Out (Forza Motorsport; Forza Horizon 6) za polja, njihove enote in osi avta (x desno, y navzgor, z naprej – levosučno). Proti čemu Forza normira svoj zdrs, ni dokumentirano: izmerite, kje se pri vsakem avtu oprijem res začne izgubljati, namesto da predpostavite, da je 1 meja.
- **Kunos:** SDK za AC1, dokumentacija deljenega pomnilnika ACC v1.8.12, `albertowd/live-telemetry-evo` (EVO, izmerjeno; AC Rally uporablja ACC-jevo postavitev, "potrjeno z bajt-za-bajtom preiskavo"), `LuizZak/AssettoCorsaRallyTelemetryReader`. Stran, v katero kaže x os avta, je dokumentirana na obe strani: uporabi velikost kota drifta, ne njegovega predznaka.
- **EA SPORTS WRC:** EA-jev UDP Telemetry Guide v1.3 in seznam kanalov, ki ga igra zapiše v `readme/channels.json`; odmiki privzetega paketa `wrc`, kot jih dekodira nobonobo/obs-codemasters-telemetry. Privzeta vrata igre niso dokumentirana; snemalnik vklopi paket na vratih 20777.
- **DiRT:** Codemastersov UDP dokument za DiRT 4, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. Smer stranskega vektorja in enota položaja vzmeti sta dokumentirani na obe strani; nobena ne odloča o ugotovitvi.
- **RBR:** NGP-jeva datoteka `rbr.telemetry.data.TelemetryData.h` (prek mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Osi položaja, enote drže in enota hitrosti niso dokumentirane: snemalnik vzame navzgor z etape, hitrost pa iz položajev.
- **BeamNG:** documentation.beamng.com (protokoli; refNodes: vozilo +X levo, -Y naprej, Z navzgor) ter igrini datoteki `lua/vehicle/protocols.lua` in `wheels.lua`. OutSim je v novejših različicah prazen (stub); OutGauge nima položaja, MotionSim pa nima koles, zato je potreben mod.
- **Trackmania:** Openplanetov `CSceneVehicleVisState` in vtičnik VehicleState, čas dirke `CSmScriptPlayer`. Openplanetovi vtičniki ne morejo pošiljati UDP, zato vtičnik piše datoteke. Nepodpisani vtičniki se naložijo samo v razvijalskem načinu, kar omejuje igro na spletu; vtičnik se lahko podpiše na openplanet.dev.

Nobeden od snemalnikov še ni bil zagnan proti živim igram, na katerih delam; prva prava seja vsakega je preizkus, ki šteje. Datoteke `tests/test_kunos.py`, `test_rally.py` in `test_beamng.py` zapirajo postavitve, za katere so bile zgrajene. Vsak snemalnik preverja pakete, ko prihajajo – hitrost glede na hitrost avta, velikost strukture – in pove, kadar se postavitev ne ujema.

## Proge: kaj se izvozi, po igrah {#courses-what-is-exported-per-game}

Proga doda robnike, zidove in površine za iztek, ki pojasnijo linijo. Proge izvozi [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), iz igrinih lastnih datotek, kjer je to zgrajeno in preverjeno na nameščeni kopiji igre. Podrobnosti so v [dokumentaciji GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Igra | Proga iz kroga |
|---|---|
| Forza Horizon | da |
| BeamNG.drive | da |
| Assetto Corsa Rally | da |
| Assetto Corsa EVO | ne: njena vsebina ni berljiva kot datoteke |
| iRacing | ne: modeli prog so v zaščitenem formatu |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | še ne: vsaka potrebuje nameščeno kopijo igre, da se zgradi in preveri |

Za vse do takrat deluje spodnja pot iz igranja.

## Pot, ki deluje za vsako igro {#the-route-that-works-for-every-game}

GameCapture rekonstruira nivo iz videoposnetka igranja. Njegov težki del je pot kamere. Pri Forzi je ta natančna, ker telemetrija da položaj avta vsak okvir. Zdaj ima to isto vsaka zgoraj navedena igra: položaj in držo, v živo, iz dokumentiranega vmesnika. Če se to vnese v `pose/telemetry_pose.py` namesto Forzinega, je to ena stvar, ki naredi pot iz igranja natančno za vse – preostanek cevovoda (globina, zlivanje, teksture) ne mara, katera igra je narisala okvirje.
