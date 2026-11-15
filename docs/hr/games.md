---
title: "Igre: snimanje i staze"
nav_order: 4
lang: "hr"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Igre: snimanje i staze {#games-recording-and-courses}

Kako se snima svaka podržana igra, što šalje i koje njezine staze se mogu izvesti iz
vlastitih datoteka igre.

Pravila su ista za svaku igru: staza dolazi iz datoteka koje korisnik posjeduje ili se
rekonstruira iz vlastite vožnje korisnika. Šifrirani arhivi otvaraju se samo ključem koji
korisnik već ima - ovdje se nijedan ključ ne isporučuje niti se ne oporavlja, i ništa se ne
ubacuje u proces igre. Telemetrija dolazi samo iz sučelja koja igre objavljuju za to (UDP
izlazi, dijeljena memorija, njihova vlastita sučelja modova i dodataka). Na što korisnik
usmjeri alate i dalje podliježe licenci te igre.

## Telemetrija {#telemetry}

Svaka igra na kraju završi kao datoteke `heat3d-lap` ([`lap-format.md`](lap-format.md)),
s kanonskim nazivima kanala i blokom `meta` koji kaže što znače njezini brojevi - kako se
njezino klizanje skalira, je li krug, vozačka etapa ili arkadna igra, podloga kad je
poznata - pa ih čitač tretira jednako. Sve naredbe su `python -m heat3d_capture ...` u
ovom repozitoriju.

| Igra | Kako snimiti | Položaj | Gume i klizanje | Kut drifta | Stanje |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out preko UDP-a: `heat3d_capture telemetry` (prosljeđuje FH Companionu) - ili `.tele.gz` od FH Companion-a uz svaku vožnju, učitan uz datoteku kruga | svjetski XYZ | omjer klizanja, kut klizanja, kombinirano klizanje po kotaču, normalizirano; vibriranje podloge | brzina vozila u okviru automobila | snimač isproban; čitač `.tele.gz` provjeren na pravim krugovima |
| Forza Motorsport (uklj. 2023.) | isto; razlikuje se po duljini paketa | svjetski XYZ | isto | isto | snimač isproban |
| Assetto Corsa, ACC, AC EVO | dijeljena memorija: `telemetry --game ac / acc / acevo` | srednja vrijednost točaka dodira guma s podlogom | omjer i kut klizanja (fizički, skalirano vrhom na asfaltu); ABS i TC aktivni (ACC, EVO) | brzina vozila u okviru automobila | snimač isproban na sintetičkim stranicama |
| Assetto Corsa Rally | `telemetry --game acrally` | isto | isto; opterećenja kotača; temperature pretvorene iz kelvina | brzina vozila u okviru automobila | snimač isproban na sintetičkim stranicama |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` uključuje zadani paket `wrc` (datoteka se prvo sigurnosno kopira) | svjetski XYZ | brzina dodirne površine po kotaču; klizanje izvedeno | iz osi automobila i njegove brzine | snimač isproban na paketima izrađenima prema dokumentiranom rasporedu |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: postavite `<udp enabled="true" extradata="3" port="20777" delay="1" />` u `hardware_settings_config.xml`, zatim `telemetry --game dirtrally2` (ili `dirtrally`, `dirt4`) | svjetski XYZ | brzina dodirne površine po kotaču; klizanje izvedeno. Nema kanala ručne kočnice | iz osi automobila i njegove brzine | isto |
| Richard Burns Rally (RSF/NGP) | UDP telemetrija NGP-a (`udpTelemetry=1`): `telemetry --game rbr` | svijet, os gore pronađena iz etape | progib opruge i sila po kotaču; nema brzina kotača | vlastite brzine automobila | isto; osi i jedinice brzine nisu dokumentirane i obrađuju se iz podataka |
| BeamNG.drive | mod protokola `heat3d`: `telemetry --game beamng --install`, zatim Options > Other > Protocols > "others" | svijet, okrenut tako da je Y gore | brzina površine kotača, okretanje, opterećenje, dodir s tlom; klizanje izvedeno | iz osi automobila i njegove brzine | snimač isproban na paketima izrađenima prema strukturi moda; mod nije isproban u igri |
| Trackmania (2020.) | Openplanet dodatak `Heat3dRecorder`: `telemetry --game trackmania --install`, učitan u razvojnom načinu Openplanet-a; jedan CSV po vožnji u njegovoj mapi za pohranu | svjetski XYZ | koeficijent klizanja Trackmanie po kotaču; rastresito tlo iz materijala kotača; u zraku | brzina naprijed i u stranu | čitač isproban; dodatak nije isproban u igri |
| iRacing | vlastite `.ibt` datoteke; snimač nije potreban | geografska širina/dužina/visina, položene na tangencijalnu ravninu | nema klizanja (nije zabilježeno); brzina skretanja i bočno ubrzanje | iz brzine skretanja naspram putanje | čitač isproban na sintetičkoj datoteci |

Što ne šalje nijedna vozačka igra - klizanje guma - čitač izračunava: iz brzine dodirne
površine ili brzine površine svakog kotača naspram brzine automobila tamo gdje je igra
šalje (`(wheel - car) / car`), iz njegova okretanja i polumjera kotrljanja izmjerenog na
samom krugu tamo gdje se šalje samo okretanje. Kut drifta dolazi iz vlastite brzine
automobila (Forza, igre AC, Trackmania, RBR), iz brzine svijeta projicirane na osi
automobila (EA WRC, DiRT, BeamNG) ili iz smjera naspram putanje. Je li automobil u zraku
zaključuje se iz dodira kotača, opterećenja ili ovjesa.

Tamo gdje je svijet igre lijevo orijentiran - Forzin jest - krug se u desno orijentiranom
pregledniku ispisuje zrcaljeno; vlastito upravljanje i ovjes krugova to odaju. Igre čija
orijentacija nije dokumentirana (RBR, BeamNG, Trackmania) obrađuju se na isti način:
izmjerena, ne pretpostavljena.

Osim kanala vožnje, snimači čuvaju što koja igra dodaje: ABS i traction control kad
djeluju u igrama AC, raspodjelu kočnica, DRS, ograničivač u boksu, pojačanje i vijek
kočnih pločica i diska; iRacingove postavke pomoći, raspodjelu kočnica, gorivo, temperature
ulja i vode te svaki drugi kanal koji zapisuje pod svojim imenom.

### Izvori i što nije potvrđeno {#sources-and-what-is-not-yet-confirmed}

- **Forza:** službena dokumentacija Data Out (Forza Motorsport; Forza Horizon 6) za polja,
  njihove jedinice i okvir automobila (x desno, y gore, z naprijed - lijevo orijentirano).
  Nije dokumentirano prema čemu Forza normalizira klizanje: izmjerite gdje se prianjanje
  svakog automobila stvarno gubi, umjesto da pretpostavite da je 1 granica.
- **Kunos:** SDK za AC1, dokumentacija dijeljene memorije ACC-a v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, izmjereno; AC Rally koristi raspored ACC-a,
  „potvrđeno bajt-po-bajt sondiranjem”), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Na koju stranu pokazuje x os automobila dokumentirano je u oba smjera: koristite veličinu
  kuta drifta, a ne njegov predznak.
- **EA SPORTS WRC:** EA-in UDP Telemetry Guide v1.3 i popis kanala koji igra zapisuje u
  `readme/channels.json`; pomaci zadanog paketa `wrc` kako ih dekodira
  nobonobo/obs-codemasters-telemetry. Zadani port igre nije dokumentiran; snimač uključuje
  paket na 20777.
- **DiRT:** Codemasters-ov UDP dokument za DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Smjer bočnog vektora i jedinica položaja
  ovjesa dokumentirani su u oba smjera; nijedan ne odlučuje ni o jednom nalazu.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` od NGP-a (preko
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Osi položaja, jedinice stava i
  jedinica brzine nisu dokumentirane: snimač os gore uzima iz etape, a brzinu iz položaja.
- **BeamNG:** documentation.beamng.com (protocols; refNodes: vozilo +X lijevo, -Y naprijed,
  Z gore), te vlastite datoteke igre `lua/vehicle/protocols.lua` i `wheels.lua`. OutSim je
  u trenutnim verzijama samo zamjena; OutGauge nema položaj, a MotionSim nema kotače, pa je
  potreban mod.
- **Trackmania:** `CSceneVehicleVisState` i VehicleState dodatak Openplanet-a, vrijeme
  utrke `CSmScriptPlayer`. Openplanet dodaci ne mogu slati UDP, pa dodatak piše datoteke.
  Nepotpisani dodaci učitavaju se samo u razvojnom načinu, što ograničava igru na mreži;
  dodatak se može potpisati na openplanet.dev.

Nijedan snimač još nije pokrenut uz žive igre ovdje; prva prava sesija svakog od njih je
pravi test, a `tests/test_kunos.py`, `test_rally.py` i `test_beamng.py` fiksiraju rasporede
za koje su napravljeni. Svaki snimač provjerava pakete dok stižu - brzinu vozila naspram
brzine, veličinu strukture - i kaže kad se raspored ne podudara.

## Staze: što se izvozi, po igri {#courses-what-is-exported-per-game}

Staza dodaje rubnike, zidove i izlazne zone koji objašnjavaju liniju vožnje. Staze izvozi
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`),
iz vlastitih datoteka igre, tamo gdje je to izrađeno i provjereno na instaliranoj kopiji
igre. Detalji su u [dokumentaciji GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Igra | Staza iz kruga |
|---|---|
| Forza Horizon | da |
| BeamNG.drive | da |
| Assetto Corsa Rally | da |
| Assetto Corsa EVO | ne: njezin sadržaj nije čitljiv kao datoteke |
| iRacing | ne: modeli staza dolaze u zaštićenom formatu |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | još ne: svakoj treba instalirana kopija da se izradi i provjeri |

Put kroz igru opisan u nastavku za sada radi za sve njih.

## Put koji radi za svaku igru {#the-route-that-works-for-every-game}

GameCapture rekonstruira razinu iz videa igranja. Njegov težak dio je put kamere, a za
Forzu je točan jer telemetrija daje položaj automobila u svakom kadru. Svaka igra iznad sada
ima isto: položaj i stav, uživo, iz dokumentiranog sučelja. Ako se to unese u
`pose/telemetry_pose.py` umjesto Forzinog, to je jedini dio koji put kroz igru čini točnim
za sve njih - ostatak cjevovoda (dubina, spajanje, teksture) ne zanima koja je igra crtala kadrove.
