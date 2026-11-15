---
title: "Lojërat"
nav_order: 4
lang: "sq"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Lojërat: regjistrimi dhe pistat {#games-recording-and-courses}

Si regjistrohet çdo lojë e mbështetur, çfarë dërgon dhe cilat nga pistat e tyre
mund të eksportohen nga skedarët e vetë lojës.

Rregullat janë të njëjta për çdo lojë: një pistë del nga skedarë që i përkasin
përdoruesit, ose rindërtohet nga lojra e vetë përdoruesit. Arkivat e enkriptuara
hapen vetëm me një çelës që përdoruesi e ka tashmë - këtu nuk jepet asnjë çelës
dhe nuk rikuperohet asnjë, dhe asgjë nuk injektohet në procesin e një loje.
Telemetria vjen vetëm nga ndërfaqet që lojërat publikojnë për të (daljet UDP,
memoria e përbashkët, ndërfaqet e tyre të modeve dhe të shtesave). Ajo që
përdoruesi u jep mjeteve mbetet nën licencën e asaj loje.

## Telemetria {#telemetry}

Çdo lojë përfundon në skedarë `heat3d-lap` ([`lap-format.md`](lap-format.md)),
me emra kanalesh standardë dhe një bllok `meta` që tregon çfarë nënkuptojnë
numrat e saj - si shkallëzohet rrëshqitja, qark apo ralim apo arkadë, sipërfaqja
kur dihet - që një lexues t'i trajtojë të gjitha njësoj. Të gjitha komandat janë
`python -m heat3d_capture ...` në këtë repo.

| Loja | Si regjistrohet | Pozicioni | Gomat dhe rrëshqitja | Këndi i drift-it | Gjendja |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out përmes UDP: `heat3d_capture telemetry` (e përcjell te FH Companion) - ose `.tele.gz` e vetë FH Companion pranë çdo xhiroje, e ngarkuar me skedarin e xhiros | XYZ botërore | raporti i rrëshqitjes, këndi i rrëshqitjes, rrëshqitja e kombinuar për çdo rrotë, e normalizuar; dridhja e sipërfaqes | shpejtësia në kornizën e makinës | regjistruesi i testuar; lexuesi i `.tele.gz` i kontrolluar në xhiro të vërteta |
| Forza Motorsport (përfshirë 2023) | njësoj; dallohen nga gjatësia e paketës | XYZ botërore | njësoj | njësoj | regjistruesi i testuar |
| Assetto Corsa, ACC, AC EVO | memoria e përbashkët: `telemetry --game ac / acc / acevo` | mesatarja e pikave të kontaktit të gomave | raporti dhe këndi i rrëshqitjes (fizik, i shkallëzuar sipas një maksimumi në asfalt); ABS dhe TC në veprim (ACC, EVO) | shpejtësia në kornizën e makinës | regjistruesi i testuar në faqe sintetike |
| Assetto Corsa Rally | `telemetry --game acrally` | njësoj | njësoj; ngarkesat e rrotave; temperaturat të konvertuara nga kelvini | shpejtësia në kornizën e makinës | regjistruesi i testuar në faqe sintetike |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` ndez paketën standarde `wrc` (skedari ruhet më parë si kopje rezervë) | XYZ botërore | shpejtësia e njollës së kontaktit për çdo rrotë; rrëshqitja e nxjerrë | nga akset e makinës dhe shpejtësia e saj | regjistruesi i testuar në paketa të ndërtuara sipas strukturës së dokumentuar |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: vendos `<udp enabled="true" extradata="3" port="20777" delay="1" />` te `hardware_settings_config.xml`, pastaj `telemetry --game dirtrally2` (ose `dirtrally`, `dirt4`) | XYZ botërore | shpejtësia e njollës së kontaktit për çdo rrotë; rrëshqitja e nxjerrë. Pa kanal frenimi me dorë | nga akset e makinës dhe shpejtësia e saj | njësoj |
| Richard Burns Rally (RSF/NGP) | telemetria UDP e NGP (`udpTelemetry=1`): `telemetry --game rbr` | botërore, aksi lart gjendet nga etapa | devijimi dhe forca e sustës për çdo rrotë; pa shpejtësi rrotash | shpejtësitë e vetë makinës | njësoj; akset dhe njësitë e shpejtësisë nuk janë të dokumentuara dhe merren nga të dhënat |
| BeamNG.drive | moda e protokollit `heat3d`: `telemetry --game beamng --install`, pastaj Options > Other > Protocols > "others" | botërore, e kthyer me Y lart | shpejtësia e sipërfaqes së rrotës, rrotullimi, ngarkesa, kontakti me tokën; rrëshqitja e nxjerrë | nga akset e makinës dhe shpejtësia e saj | regjistruesi i testuar në paketa të ndërtuara nga struktura e modës; moda nuk është testuar në lojë |
| Trackmania (2020) | shtesa Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, e ngarkuar në modalitetin e zhvilluesit të Openplanet; një CSV për çdo vozitje në dosjen e saj të ruajtjes | XYZ botërore | koeficienti i rrëshqitjes së Trackmania për çdo rrotë; toka e lirshme nga materialet e rrotave; në ajër | shpejtësia përpara dhe anësore | lexuesi i testuar; shtesa nuk është testuar në lojë |
| iRacing | skedarët e vet `.ibt`; nuk duhet regjistrues | gjerësi/gjatësi/lartësi gjeografike, të shtrira mbi një plan tangjent | pa rrëshqitje (nuk regjistrohet); shpejtësia e rrotullimit (yaw) dhe nxitimi anësor | nga shpejtësia e rrotullimit krahasuar me rrugën | lexuesi i testuar në një skedar sintetik |

Atë që asnjë nga lojërat e ralit nuk e dërgon - rrëshqitjen e gomave - e llogarit
një lexues: nga shpejtësia e njollës së kontaktit ose e sipërfaqes së çdo rrote
krahasuar me shpejtësinë e makinës aty ku loja e dërgon një të tillë
(`(wheel - car) / car`), ose nga rrotullimi i saj dhe një rreze rrotullimi e
matur në vetë xhironë aty ku dërgon vetëm rrotullimin. Këndi i drift-it vjen nga
shpejtësia e vetë makinës (Forza, lojërat AC, Trackmania, RBR), nga shpejtësia
botërore e projektuar mbi akset e makinës (EA WRC, DiRT, BeamNG), ose nga drejtimi
i makinës krahasuar me rrugën. Nëse makina është në ajër, kjo del nga kontakti,
ngarkesat ose pezullimi i rrotave të saj.

Aty ku bota e një loje është e majtë - ajo e Forza është - pista del e pasqyruar
në një shikues me sistem të djathtë; drejtimi dhe pezullimi i vetë xhirove e
zbulojnë këtë. Lojërat që nuk e dokumentojnë orientimin e botës
(RBR, BeamNG, Trackmania) trajtohen njësoj: e matur, jo e supozuar.

Përtej kanaleve të vozitjes, regjistruesit mbajnë atë që shton çdo lojë: ABS dhe
kontrollin e tërheqjes në veprim të lojërave AC, ndarjen e frenave, DRS,
kufizuesin e pit-it, boost-in dhe jetëgjatësinë e jastëkëve dhe disqeve të
frenave; cilësimet e ndihmave të iRacing, ndarjen e frenave, karburantin,
temperaturat e vajit dhe të ujit, dhe çdo kanal tjetër që ai regjistron me emrin
e vet.

### Burimet dhe ajo që ende nuk është konfirmuar {#sources-and-what-is-not-yet-confirmed}

- **Forza:** dokumentacioni zyrtar i Data Out (Forza Motorsport; Forza
  Horizon 6) për fushat, njësitë e tyre dhe kornizën e makinës (x djathtas, y
  lart, z përpara - e majtë). Ndaj çfarë e normalizon Forza rrëshqitjen nuk është
  e dokumentuar: mate ku e humbet realisht kapjen çdo makinë, në vend që të
  supozosh se 1 është kufiri.
- **Kunos:** SDK i AC1, dokumentacioni i memories së përbashkët të ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, e matur; AC Rally përdor strukturën e ACC,
  "confirmed via byte-by-byte probe"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Ana nga drejtohet aksi x i kornizës së makinës dokumentohet në të dyja mënyrat:
  përdor madhësinë e këndit të drift-it, jo shenjën e tij.
- **EA SPORTS WRC:** UDP Telemetry Guide v1.3 i EA dhe lista e kanaleve që loja
  shkruan te `readme/channels.json`; zhvendosjet e paketës standarde `wrc` siç
  janë dekoduar nga nobonobo/obs-codemasters-telemetry. Porta standarde e
  fabrikës nuk është e dokumentuar; regjistruesi e ndez paketën te 20777.
- **DiRT:** dokumenti UDP i DiRT 4 nga Codemasters, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Kuptimi i vektorit anësor dhe
  njësia e pozicionit të pezullimit dokumentohen në të dyja mënyrat; asnjëra
  nuk vendos një konstatim.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` i NGP (nëpërmjet
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Akset e pozicionit,
  njësitë e qëndrimit dhe njësia e shpejtësisë nuk janë të dokumentuara:
  regjistruesi e merr aksin lart nga etapa dhe shpejtësinë nga pozicionet.
- **BeamNG:** documentation.beamng.com (protokollet; refNodes: automjeti +X majtas,
  -Y përpara, Z lart), dhe vetë `lua/vehicle/protocols.lua` dhe
  `wheels.lua` të lojës. OutSim është një shabllon bosh në versionet e tanishme;
  OutGauge nuk ka pozicion dhe MotionSim nuk ka rrota, prandaj moda.
- **Trackmania:** `CSceneVehicleVisState` i Openplanet dhe shtesa VehicleState,
  koha e garës `CSmScriptPlayer`. Shtesat e Openplanet nuk mund të dërgojnë UDP,
  prandaj shtesa shkruan skedarë. Shtesat e pasinjuara ngarkohen vetëm në
  modalitetin e zhvilluesit, që kufizon lojën online; shtesa mund të nënshkruhet
  te openplanet.dev.

Asnjë nga regjistruesit nuk është ekzekutuar ende këtu kundër lojërave të vërteta;
seanca e parë e vërtetë e secilit është testi që ka rëndësi, dhe
`tests/test_kunos.py`, `test_rally.py` dhe `test_beamng.py` fiksojnë strukturat
sipas të cilave u ndërtuan. Çdo regjistrues kontrollon paketat ndërsa vijnë -
shpejtësinë krahasuar me shpejtësinë, madhësinë e strukturës - dhe e thotë kur
një strukturë nuk përputhet.

## Pistat: çfarë eksportohet, për çdo lojë {#courses-what-is-exported-per-game}

Një pistë shton kerbat, muret dhe zonat e daljes që shpjegojnë një vijë vozitjeje.
Pistat i eksporton [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <lap>`), nga skedarët e vetë lojës, aty ku kjo
është ndërtuar dhe kontrolluar në një kopje të instaluar. Detajet janë te
[dokumentacioni i GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Loja | Pista nga një xhiro |
|---|---|
| Forza Horizon | po |
| BeamNG.drive | po |
| Assetto Corsa Rally | po |
| Assetto Corsa EVO | jo: përmbajtja e saj nuk lexohet si skedarë |
| iRacing | jo: modelet e pistave vijnë në një format të mbrojtur |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ende jo: secila ka nevojë për një kopje të instaluar për ta ndërtuar dhe kontrolluar |

Rruga e lojës më poshtë funksionon për të gjitha ndërkohë.

## Rruga që funksionon për çdo lojë {#the-route-that-works-for-every-game}

GameCapture rindërton një nivel nga video e lojës. Pjesa e saj e vështirë është
rruga e kamerës, dhe për Forza ajo është e saktë sepse telemetria jep pozën e
makinës në çdo kuadër. Çdo lojë e mësipërme ka tani të njëjtën gjë: pozicion dhe
qëndrim, drejtpërdrejt, nga një ndërfaqe e dokumentuar. Futja e tyre te
`pose/telemetry_pose.py` në vend të atyre të Forza është pjesa e vetme që e bën
rrugën e lojës të saktë për të gjitha - pjesa tjetër e atij procesi (thellësia,
bashkimi, teksturimi) nuk ka rëndësi se cila lojë i vizatoi kuadrot.
