---
title: Igre
nav_order: 4
lang: "bs"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Igre: snimanje i staze {#games-recording-and-courses}

Kako se snima svaka podržana igra, šta šalje i koje se njene staze mogu
izvesti iz vlastitih datoteka igre.

Pravila su ista za svaku igru: staza dolazi iz datoteka koje korisnik posjeduje
ili se rekonstruiše iz korisnikove vlastite igre. Arhive koje su šifrovane
otvaraju se samo ključem koji korisnik već ima - ovdje se ne isporučuju
ključevi niti se oni vraćaju, i ništa se ne ubacuje u proces igre. Telemetrija
dolazi samo preko sučelja koja igre objavljuju za tu svrhu (UDP izlazi,
dijeljena memorija, vlastita sučelja za modove i dodatke). Ono na šta korisnik
usmjeri alate i dalje podliježe licenci te igre.

## Telemetrija {#telemetry}

Svaka igra završi kao `heat3d-lap` datoteke ([`lap-format.md`](lap-format.md)),
s kanonskim imenima kanala i `meta` blokom koji kaže šta njeni brojevi znače -
kako je skaliran klizanje, je li krug, reli ili arkada, površina kada je poznata -
tako da ih čitač sve tretira jednako. Sve komande su `python -m heat3d_capture ...`
u ovom repozitoriju.

| Igra | Kako snimati | Pozicija | Gume i klizanje | Ugao zanošenja | Status |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out preko UDP-a: `heat3d_capture telemetry` (prosljeđuje do FH Companion) - ili vlastiti `.tele.gz` programa FH Companion pored svakog kruga, učitan s datotekom kruga | svjetski XYZ | omjer klizanja, ugao klizanja, kombinovano klizanje po točku, normalizirano; vibracija površine | brzina u okviru automobila | snimač testiran; čitač `.tele.gz` provjeren na stvarnim krugovima |
| Forza Motorsport (uklj. 2023) | isto; razlikuju se po dužini paketa | svjetski XYZ | isto | isto | snimač testiran |
| Assetto Corsa, ACC, AC EVO | dijeljena memorija: `telemetry --game ac / acc / acevo` | srednja vrijednost dodirnih tačaka guma | omjer i ugao klizanja (fizički, skalirani asfaltnim vrhom); ABS i TC u radu (ACC, EVO) | brzina u okviru automobila | snimač testiran na sintetičkim stranicama |
| Assetto Corsa Rally | `telemetry --game acrally` | isto | isto; opterećenja točkova; temperature pretvorene iz kelvina | brzina u okviru automobila | snimač testiran na sintetičkim stranicama |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documents>/My Games/WRC/telemetry/config.json"` uključuje zadani `wrc` paket (datoteka se prvo kopira kao rezerva) | svjetski XYZ | brzina kontaktne površine po točku; klizanje izvedeno | iz osa automobila i njegove brzine | snimač testiran na paketima izgrađenim prema dokumentiranom rasporedu |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: postavite `<udp enabled="true" extradata="3" port="20777" delay="1" />` u `hardware_settings_config.xml`, zatim `telemetry --game dirtrally2` (ili `dirtrally`, `dirt4`) | svjetski XYZ | brzina kontaktne površine po točku; klizanje izvedeno. Nema kanala ručne kočnice | iz osa automobila i njegove brzine | isto |
| Richard Burns Rally (RSF/NGP) | NGP-ova UDP telemetrija (`udpTelemetry=1`): `telemetry --game rbr` | svijet, osa gore pronađena iz dionice | ugib opruge i sila po točku; nema brzina točkova | vlastite brzine automobila | isto; ose i jedinice brzine nisu dokumentirane i obrađuju se iz podataka |
| BeamNG.drive | `heat3d` protokol mod: `telemetry --game beamng --install`, zatim Options > Other > Protocols > "others" | svijet, okrenut tako da je Y gore | brzina površine točka, rotacija, opterećenje, dodir s tlom; klizanje izvedeno | iz osa automobila i njegove brzine | snimač testiran na paketima izgrađenim iz strukture moda; mod nije testiran u igri |
| Trackmania (2020) | Openplanet dodatak `Heat3dRecorder`: `telemetry --game trackmania --install`, učitan u Openplanetovom razvojnom režimu; jedan CSV po vožnji u njegovom folderu za pohranu | svjetski XYZ | Trackmaniain koeficijent klizanja po točku; rastresito tlo iz materijala točkova; u zraku | prednja i bočna brzina | čitač testiran; dodatak nije testiran u igri |
| iRacing | vlastite `.ibt` datoteke; snimač nije potreban | geografska širina/dužina/visina, položene na tangentnu ravan | nema klizanja (ne bilježi se); brzina skretanja i bočno ubrzanje | iz brzine skretanja u odnosu na putanju | čitač testiran na sintetičkoj datoteci |

Ono što nijedna reli igra ne šalje - klizanje guma - čitač izračunava: iz
brzine kontaktne površine ili površine svakog točka u odnosu na brzinu
automobila tamo gdje je igra šalje (`(wheel - car) / car`), a iz rotacije i
radijusa kotrljanja izmjerenog na samom krugu tamo gdje šalje samo rotaciju.
Ugao zanošenja dolazi iz vlastite brzine automobila (Forza, AC igre,
Trackmania, RBR), iz svjetske brzine projicirane na ose automobila (EA WRC,
DiRT, BeamNG) ili iz smjera kretanja u odnosu na putanju. Je li automobil u
zraku, vidi se iz dodira, opterećenja ili ovjesa njegovih točkova.

Tamo gdje je svijet igre lijevoruk - Forzin jeste - staza izlazi zrcaljena u
desnorukom pregledniku; vlastito upravljanje i ovjes krugova to odaju. Igre
čija ruka nije dokumentirana (RBR, BeamNG, Trackmania) obrađuju se na isti
način: mjeri se, ne pretpostavlja.

Pored vozačkih kanala, snimači čuvaju ono što svaka igra dodaje: ABS i
kontrolu proklizavanja u radu, raspodjelu kočenja, DRS, ograničivač u boksu,
turbo pritisak te vijek kočionih pločica i diskova kod AC igara; postavke
pomoćnih sistema, raspodjelu kočenja, gorivo, temperature ulja i vode kod
iRacinga, i svaki drugi kanal koji bilježi pod vlastitim imenom.

### Izvori i šta još nije potvrđeno {#sources-and-what-is-not-yet-confirmed}

- **Forza:** zvanična Data Out dokumentacija (Forza Motorsport; Forza
  Horizon 6) za polja, njihove jedinice i okvir automobila (x desno, y gore,
  z naprijed - lijevoruk). Prema čemu Forza normalizira klizanje nije
  dokumentirano: mjerite gdje prianjanje svakog automobila zaista popušta
  umjesto da pretpostavljate da je 1 granica.
- **Kunos:** AC1 SDK, dokumentacija dijeljene memorije za ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, izmjereno; AC Rally koristi ACC-ov
  raspored, "confirmed via byte-by-byte probe"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Na koju stranu pokazuje x osa u okviru automobila dokumentirano je na oba
  načina: koristite veličinu ugla zanošenja, ne njegov predznak.
- **EA SPORTS WRC:** EA-ov UDP Telemetry Guide v1.3 i spisak kanala koji igra
  upisuje u `readme/channels.json`; pomaci zadanog `wrc` paketa kako ih je
  dekodirao nobonobo/obs-codemasters-telemetry. Zadani port nije
  dokumentiran; snimač uključuje paket na 20777.
- **DiRT:** Codemastersov UDP dokument za DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Smjer bočnog vektora i jedinica
  položaja ovjesa dokumentirani su na oba načina; ni jedno ne odlučuje o
  nalazu.
- **RBR:** NGP-ov `rbr.telemetry.data.TelemetryData.h` (preko
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Ose položaja, jedinice
  stava i jedinica brzine nisu dokumentirani: snimač uzima "gore" iz dionice, a
  brzinu iz položaja.
- **BeamNG:** documentation.beamng.com (protokoli; refNodes: vozilo +X lijevo,
  -Y naprijed, Z gore), te igrini vlastiti `lua/vehicle/protocols.lua` i
  `wheels.lua`. OutSim je u trenutnim verzijama samo prazan okvir; OutGauge nema
  položaj, a MotionSim nema točkove, otuda mod.
- **Trackmania:** Openplanetov `CSceneVehicleVisState` i VehicleState dodatak,
  vrijeme trke `CSmScriptPlayer`. Openplanet dodaci ne mogu slati UDP, pa
  dodatak upisuje datoteke. Nepotpisani dodaci se učitavaju samo u razvojnom
  režimu, što ograničava igru na mreži; dodatak se može potpisati na openplanet.dev.

Nijedan od snimača još nije pokrenut protiv živih igara ovdje; prva stvarna
sesija svakog od njih je test koji se računa, a `tests/test_kunos.py`,
`test_rally.py` i `test_beamng.py` učvršćuju rasporede prema kojima su
izgrađeni. Svaki snimač provjerava svoje pakete dok stižu - vektor brzine u
odnosu na iznos brzine, veličinu strukture - i javlja kada se raspored ne poklapa.

## Staze: šta se izvozi, po igri {#courses-what-is-exported-per-game}

Staza dodaje ivičnjake, zidove i zaštitne zone koje objašnjavaju liniju vožnje. Staze izvozi
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <lap>`), iz vlastitih datoteka igre, tamo gdje je
to izgrađeno i provjereno na instaliranoj kopiji. Detalji su u
[dokumentaciji GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Igra | Staza iz kruga |
|---|---|
| Forza Horizon | da |
| BeamNG.drive | da |
| Assetto Corsa Rally | da |
| Assetto Corsa EVO | ne: njen sadržaj nije čitljiv kao datoteke |
| iRacing | ne: modeli staza dolaze u zaštićenom formatu |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | još ne: svakoj treba instalirana kopija za izgradnju i provjeru |

Dotle radi put preko igranja, opisan ispod, za sve njih.

## Put koji radi za svaku igru {#the-route-that-works-for-every-game}

GameCapture rekonstruiše nivo iz video snimka igranja. Težak dio je
putanja kamere, a za Forzu je ona tačna jer telemetrija daje
pozu automobila u svakom kadru. Svaka gore navedena igra sada ima istu stvar:
položaj i stav, uživo, iz dokumentiranog sučelja. Ubacivanje toga u
`pose/telemetry_pose.py` umjesto Forzinog jedini je dio koji
čini put preko igranja tačnim za sve njih - ostatak tog cjevovoda (dubina,
spajanje, teksturisanje) ne mari koja je igra nacrtala kadrove.
