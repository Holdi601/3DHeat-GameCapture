---
title: "Klizanje, zanošenje i izvedeni kanali"
nav_order: 8
lang: "bs"
source: slip-and-drift.md
source_hash: "6b4721abae3c"
nav_exclude: true
search_exclude: true
---
# Klizanje, zanošenje i izvedeni kanali {#slip-drift-and-derived-channels}

Analiza kontrole automobila u kartici Analiza utrke u pregledniku traži iste nekoliko veličina iz svake
igre: koliko svaka guma klizi, koliko automobil gleda dalje od smjera kretanja (ugao
zanošenja), je li u zraku, je li na rastresitom tlu. Igre ovo šalju u vrlo
različitim oblicima, ili uopće ne. Snimači ovdje zapisuju ono što svaka igra šalje, pod
kanonskim imenima, uz napomenu `meta.slip` koja kaže šta brojevi klizanja znače; preglednik zatim
izvodi ono što nedostaje, jednom, kada učita krug. **Igrina vlastita vrijednost uvijek pobjeđuje
izvedenu.**

## Šta snimači zapisuju {#what-the-recorders-write}

| Igra | Kanali klizanja | `meta.slip` | Ulazi za ugao zanošenja |
|---|---|---|---|
| Forza | `slipRatio`, `slipAngle`, `combinedSlip` po točku, kako su poslani | `peak` (zapisuje snimač; čitač `.tele.gz` u pregledniku postavlja isto) | `latVel`, `longVel` iz brzine u lokalnom okviru automobila |
| AC, ACC, AC EVO, AC Rally | `slipRatio` / 0,12, `slipAngle` / 0,14 rad, plus `slipRatioRaw`, `slipAngleRaw` | `scaled` | `latVel`, `longVel` iz brzine u okviru automobila |
| EA SPORTS WRC, DiRT igre | nema; umjesto toga `wheelSurfaceSpeed` po točku | `null` | `latVel`, `longVel` = svjetska brzina projicirana na ose automobila |
| Richard Burns Rally | nema; ni brzina točkova | nema | `latVel`, `longVel` = vlastito bočno i uzdužno kretanje automobila |
| BeamNG.drive | nema; `wheelSurfaceSpeed` i `wheelSpeed` po točku | nema | `latVel`, `longVel` = svjetska brzina projicirana na ose automobila |
| Trackmania | `slipIndex` po točku (mjera klizanja od 0 do 1) | `index` | `latVel` (bočna brzina), `longVel` (prednja brzina) |
| iRacing | nema (ne bilježi se) | nema | `yaw` i putanja, `yawRate` |

Vrijednosti `meta.slip` definirane su u [Datoteka heat3d-lap](lap-format.md): `peak`
(normalizirano tako da preko 1 guma popušta), `scaled` (fizičko klizanje podijeljeno tipičnim asfaltnim
vrhom), `physical` (razlomak i radijani), `index` (mjera klizanja od 0 do 1).

### Zašto je Kunos klizanje skalirano {#why-kunos-slip-is-scaled}

Forzino klizanje je normalizirano tako da je 1 rub prianjanja; prema čemu se normalizira nije
dokumentirano. Kunos šalje fizički omjer klizanja (razlomak) i ugao klizanja (radijani). Dijeljenje
tipičnim asfaltnim vrhom - 0,12 za omjer, 0,14 rad (oko 8 stepeni) za ugao -
čini da "preko 1 znači klizanje" bude približno tačno za obje porodice, što zadržava jedno
čitanje za prikaze u pregledniku. To je aproksimacija: stvarni vrhovi variraju prema gumi i površini, zbog
čega se sirove vrijednosti čuvaju pored skaliranih i zbog čega preglednik iz samih krugova mjeri gdje
prianjanje svakog automobila zaista popušta.

## Šta preglednik izvodi (`deriveChannels`) {#what-the-viewer-derives-derivechannels}

Ovo radi u pregledniku (`src/race/derive.ts` u 3DHeat pregledniku), a ne u ovom repozitoriju.

### Ugao zanošenja, `bodySlip` {#drift-angle-bodyslip}

- **Iz brzine u okviru automobila** kada su `latVel` i `longVel` prisutni:
  `atan2(latVel, |longVel|)`, i 0 ispod 3 m/s (automobil zaustavljen bočno ne zanosi).
  Njegov predznak slijedi igrinu bočnu brzinu, čiji je smisao za neke igre dokumentiran na oba
  načina - čitajte veličinu.
- **Inače iz smjera u odnosu na putanju**: smjer kretanja uzima se iz
  pozicija oko 2 m s obje strane svakog uzorka (`atan2(dx, dz)`); igrin `yaw` se
  prilagođava tome s predznakom i pomakom (svaka igra ima svoju nulu i smisao rotacije) koristeći
  uzorke iznad 10 m/s, i vjeruje mu se samo ako se tada blisko slaže (kružno rasipanje najviše
  0,05, najmanje 20 uzoraka). Ugao zanošenja je razlika, 0 ispod 3 m/s.

### Omjer klizanja iz točkova {#slip-ratio-from-the-wheels}

Tamo gdje krug nema `slipRatio.*`, ali ima brzine točkova, omjer klizanja je
`(wheel - car) / car` po točku, iz:

- `wheelSurfaceSpeed.*` (brzina kontaktne površine, m/s) direktno, kada se šalje (EA WRC, DiRT,
  BeamNG);
- inače `wheelSpeed.*` (rotacija, rad/s) puta **radijus kotrljanja izmjeren na krugu**:
  medijan `speed / |omega|` preko uzoraka u kojima automobil klizi pravolinijski (iznad
  10 m/s, nije u zraku, gas ispod 0,3, kočnica ispod 0,05, uzdužno ubrzanje ispod
  3 m/s²); s manje od 20 takvih uzoraka, svaki uzorak iznad 10 m/s. Radijus izvan
  0,1-1 m se odbacuje.

Samo kada se mogu izvesti sva četiri točka; `meta.slip` kruga tada postaje `physical`. Ispod
3 m/s klizanje je 0.

### U zraku {#airborne}

`airborne` je 1 tamo gdje je svaki točak odvojen od tla, prema prvom od ovoga što krug ima
za sva četiri točka:

1. `groundContact.*` (BeamNG): nijedan točak iznad 0,5;
2. `wheelLoad.*` (AC igre, RBR, BeamNG): nijedan točak iznad 5% svog medijana opterećenja;
3. `suspension.*` (0..1 hoda): nijedan točak iznad 0,02, tj. svi potpuno ispruženi.

Jedan izolovani uzorak u zraku se briše. Trackmania sama zapisuje `airborne`.

### Rastresito tlo {#loose-ground}

Tamo gdje krug ima `surfaceRumble.*` (Forza), `loose` je 1 tamo gdje najmanje dva točka prijavljuju
vibraciju najmanje trećinu sekunde, s prazninama kraćim od jedne sekunde premoštenim (glatki
komad na šljunčanom putu i dalje je šljunčani put). Trackmania sama zapisuje `loose` iz
materijala tla pod točkovima.

### Brzina skretanja {#yaw-rate}

Tamo gdje krug ima `yaw`, ali nema `yawRate`, ona je promjena `yaw` preko susjednih uzoraka.

## Šta snimači sami izvode {#what-the-recorders-derive-themselves}

- **`suspension.*`** (0..1): svaki snimač osim Forze (koja je šalje) zapisuje ga iz
  `suspensionM.*` kao položaj unutar raspona koji je ovaj krug koristio (od minimuma do maksimuma). Služi
  za trake ovjesa automobila i uočavanje točka koji visi u zraku; nije
  apsolutni udio hoda.
- **`steer`** za Kunos igre, skaliran po krugu (pogledajte
  [Assetto Corsa igre](telemetry-assetto-corsa.md)).
- **Ubrzanja** za BeamNG, iz promjene svjetske brzine
  ([BeamNG.drive](telemetry-beamng.md)).
- **`speed`** i osa gore za Richard Burns Rally, iz pozicija
  ([Reli igre](telemetry-rally.md)).

## Ruka koordinatnog sistema {#handedness}

Tamo gdje je svijet igre lijevoruk - Forzin jeste - staza izlazi zrcaljena u
desnorukom pregledniku; vlastito upravljanje i ovjes krugova to odaju. Snimači ne
mijenjaju ruku: Z-gore svijet (BeamNG) okreće se u Y-gore rotacijom, koja je čuva, i
sve ostalo se zapisuje kako je poslano.
