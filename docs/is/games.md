---
title: "Leikir"
nav_order: 4
lang: "is"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Leikir: upptaka og brautir {#games-recording-and-courses}

Hvernig hver leikur sem stuðningur er við er tekinn upp, hvað hann sendir og hvaða
brautir hans er hægt að flytja út úr skrám leiksins sjálfs.

Reglurnar eru þær sömu fyrir alla leiki: braut kemur úr skrám sem notandinn
á, eða er endurgerð úr leik notandans sjálfs. Dulkóðuð skjalasöfn opnast aðeins með lykli sem
notandinn á þegar - hér fylgja engir lyklar og engin leið til að endurheimta þá, og ekkert er sprautað inn í
ferli leiks. Mælingagögn koma eingöngu um þau viðmót sem leikirnir gefa út fyrir þau
(UDP-úttak, sameiginlegt minni, eigin viðbóta- og módviðmót leikjanna). Það sem
notandi beinir verkfærunum að heyrir áfram undir leyfi viðkomandi leiks.

## Mælingagögn {#telemetry}

Hver leikur endar sem `heat3d-lap` skrár ([`lap-format.md`](lap-format.md)),
með föstum rásaheitum og `meta` blokk sem segir hvað tölurnar þýða -
hvernig skrið er skalað, hvort það er hringakstur, ralllí eða spilakassaleikur, og undirlagið þegar það er vitað - svo
lesari meðhöndli þau öll eins. Allar skipanir eru `python -m heat3d_capture ...`
í þessari geymslu.

| Leikur | Hvernig á að taka upp | Staðsetning | Dekk og skrið | Rekhorn | Staða |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out yfir UDP: `heat3d_capture telemetry` (áframsendir til FH Companion) - eða eigin `.tele.gz` skrá FH Companion við hlið hvers hrings, hlaðin með hringskránni | heimsins XYZ | skriðhlutfall, skriðhorn, samanlagt skrið á hvert hjól, stöðlað; undirlagsskrölt | hraði í ramma bílsins | upptökutæki prófað; `.tele.gz` lesari prófaður á raunverulegum hringjum |
| Forza Motorsport (líka 2023) | það sama; greint að á lengd pakka | heimsins XYZ | það sama | það sama | upptökutæki prófað |
| Assetto Corsa, ACC, AC EVO | sameiginlegt minni: `telemetry --game ac / acc / acevo` | meðaltal snertipunkta dekkja | skriðhlutfall og horn (eðlisfræðilegt, skalað með hámarki á malbiki); ABS og TC virk (ACC, EVO) | hraði í ramma bílsins | upptökutæki prófað á gerviblöðum |
| Assetto Corsa Rally | `telemetry --game acrally` | það sama | það sama; hjólaálag; hitastig umreiknað úr kelvin | hraði í ramma bílsins | upptökutæki prófað á gerviblöðum |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` kveikir á sjálfgefnum `wrc` pakka (skráin er afrituð fyrst) | heimsins XYZ | hraði snertiflatar á hvert hjól; skrið reiknað út | út frá ásum bílsins og hraða hans | upptökutæki prófað á pökkum smíðuðum eftir skjalfestu sniði |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: settu `<udp enabled="true" extradata="3" port="20777" delay="1" />` í `hardware_settings_config.xml`, keyrðu svo `telemetry --game dirtrally2` (eða `dirtrally`, `dirt4`) | heimsins XYZ | hraði snertiflatar á hvert hjól; skrið reiknað út. Engin handbremsurás | út frá ásum bílsins og hraða hans | það sama |
| Richard Burns Rally (RSF/NGP) | UDP-mælingagögn NGP (`udpTelemetry=1`): `telemetry --game rbr` | heimurinn, upp-ásinn fundinn út frá leiðinni | fjöðrun og kraftur á hvert hjól; engir hjólahraðar | eigin hraðar bílsins | það sama; ásar og hraðaeiningar eru óskjalfestar og unnið úr gögnunum |
| BeamNG.drive | `heat3d` samskiptareglu-módið: `telemetry --game beamng --install`, síðan Options > Other > Protocols > "others" | heimurinn, snúið þannig að Y sé upp | yfirborðshraði hjóls, snúningur, álag, snerting við jörð; skrið reiknað út | út frá ásum bílsins og hraða hans | upptökutæki prófað á pökkum smíðuðum eftir struct módsins; módið er óprófað í leiknum |
| Trackmania (2020) | Openplanet viðbótin `Heat3dRecorder`: `telemetry --game trackmania --install`, hlaðin í þróunarham Openplanet; ein CSV skrá á hverja ferð í geymslumöppu hennar | heimsins XYZ | skriðstuðull Trackmania á hvert hjól; laust undirlag út frá efni hjólanna; í lofti | fram- og hliðarhraði | lesari prófaður; viðbótin er óprófuð í leiknum |
| iRacing | eigin `.ibt` skrár; ekkert upptökutæki þarf | breiddargráða/lengdargráða/hæð, lagt á snertiflöt | ekkert skrið (ekki skráð); snúningshraði um lóðás og hliðarhröðun | út frá snúningshraða um lóðás miðað við ferilinn | lesari prófaður á gervi-skrá |

Það sem engin ralllíleikjanna sendir - dekkjaskrið - reiknar lesari út: út frá
hraða snertiflatar eða yfirborðshraða hvers hjóls miðað við hraða bílsins þar sem leikur sendir
slíkan (`(wheel - car) / car`), út frá snúningi þess og veltiradíus
mældum á hringnum sjálfum þar sem aðeins snúningur er sendur. Rekhornið kemur
úr eigin hraða bílsins (Forza, AC-leikirnir, Trackmania, RBR), úr
heimshraðanum varpað á ása bílsins (EA WRC, DiRT, BeamNG), eða út frá
stefnunni miðað við ferilinn. Hvort bíllinn er í lofti kemur úr
snertingu hjólanna, álagi eða fjöðrun.

Þar sem heimur leiks er örvhentur - heimur Forza er það - kemur brautin út
spegluð í rétthentum áhorfanda; stýring og fjöðrun hringjanna sjálfra
koma upp um það. Leikir þar sem handstefna er óskjalfest
(RBR, BeamNG, Trackmania) eru meðhöndlaðir eins: mælt, ekki gert ráð fyrir.

Fyrir utan akstursrásirnar geyma upptökutækin það sem hver leikur bætir við: ABS og
spólvörn virk í AC-leikjunum, bremsujöfnun, DRS, hraðatakmarkara í viðgerðarhléi, forþjöppu og
endingu bremsuklossa og diska; í iRacing stillingar hjálpartækja, bremsujöfnun, eldsneyti, olíu- og
vatnshita, og allar aðrar rásir sem það skráir undir eigin heiti.

### Heimildir og hvað er ekki enn staðfest {#sources-and-what-is-not-yet-confirmed}

- **Forza:** opinber Data Out skjölun (Forza Motorsport; Forza
  Horizon 6) fyrir reitina, einingar þeirra og ramma bílsins (x til hægri, y upp,
  z áfram - örvhentur). Við hvað Forza stillir skrið sitt er ekki
  skjalfest: mældu hvar grip hvers bíls fer í raun að minnka frekar en
  að gera ráð fyrir að 1 sé mörkin.
- **Kunos:** AC1 SDK, ACC skjölun sameiginlegs minnis v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, mælt; AC Rally notar uppsetningu ACC,
  "confirmed via byte-by-byte probe"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Í hvora átt x-ás í ramma bílsins vísar er skjalfest á báða vegu: notaðu
  stærð rekhornsins, ekki formerki þess.
- **EA SPORTS WRC:** UDP Telemetry Guide v1.3 frá EA og rásalistinn sem
  leikurinn skrifar í `readme/channels.json`; offset sjálfgefna `wrc` pakkans eins og
  nobonobo/obs-codemasters-telemetry afkóðar þau. Sjálfgefin gátt er ekki
  skjalfest; upptökutækið kveikir á pakkanum á 20777.
- **DiRT:** UDP skjal Codemasters fyrir DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Stefna hliðarvigursins og
  eining fjöðrunarstöðunnar eru skjalfestar á báða vegu; hvorugt ræður
  niðurstöðu.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` frá NGP (um
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Staðsetningarásar, einingar
  afstöðu og hraðaeining eru óskjalfest: upptökutækið tekur upp-ásinn úr
  leiðinni og hraðann úr staðsetningunum.
- **BeamNG:** documentation.beamng.com (samskiptareglur; refNodes: ökutæki +X vinstri,
  -Y áfram, Z upp), og eigin `lua/vehicle/protocols.lua` og
  `wheels.lua` leiksins. OutSim er stubbur í núverandi útgáfum; OutGauge hefur enga staðsetningu
  og MotionSim engin hjól, þess vegna módið.
- **Trackmania:** `CSceneVehicleVisState` og VehicleState viðbótin frá Openplanet,
  kappaksturstími `CSmScriptPlayer`. Openplanet viðbætur geta ekki sent UDP, svo
  viðbótin skrifar skrár. Óundirritaðar viðbætur hlaðast aðeins í þróunarham, sem
  takmarkar netspilun; hægt er að undirrita viðbótina á openplanet.dev.

Ekkert upptökutækjanna hefur enn verið keyrt gegn raunverulegu leikjunum hér; fyrsta
raunverulega lotan hjá hverju er prófið sem skiptir máli, og `tests/test_kunos.py`,
`test_rally.py` og `test_beamng.py` festa þær uppsetningar sem þau voru smíðuð
eftir. Hvert upptökutæki athugar pakka sína jafnóðum og þeir koma - hraðann miðað við
hraðamælinn, stærð struct - og segir frá því þegar uppsetning stemmir ekki.

## Brautir: hvað er flutt út, eftir leik {#courses-what-is-exported-per-game}

Braut bætir við kantsteinum, veggjum og útafakstursvæði sem skýra línu. Brautir eru fluttar út með
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), úr skrám leiksins sjálfs, þar sem það
hefur verið smíðað og athugað á uppsettu eintaki. Nánar í
[GameFiles skjölunum](https://holdi601.github.io/3DHeat-GameFiles/).

| Leikur | Braut úr hring |
|---|---|
| Forza Horizon | já |
| BeamNG.drive | já |
| Assetto Corsa Rally | já |
| Assetto Corsa EVO | nei: efni þess er ekki læsilegt sem skrár |
| iRacing | nei: brautarlíkön koma á varðveittu sniði |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ekki enn: hvert þarf uppsett eintak til að smíða og athuga gegn |

Leikjaleiðin hér á eftir virkar fyrir þá alla á meðan.

## Leiðin sem virkar fyrir alla leiki {#the-route-that-works-for-every-game}

GameCapture endurgerir borð úr myndskeiði af leik. Erfiðasti hlutinn
er ferill myndavélarinnar, og fyrir Forza er hann nákvæmur því mælingagögnin gefa
stöðu bílsins í hverjum ramma. Allir leikirnir hér að ofan hafa nú það sama: staðsetningu og
afstöðu, í beinni, úr skjalfestu viðmóti. Að setja þetta í
`pose/telemetry_pose.py` í stað Forza er sá eini hlutur sem gerir
leikjaleiðina nákvæma fyrir þá alla - restin af ferlinu (dýpt,
samruni, áferð) er sama hvaða leikur teiknaði rammana.
