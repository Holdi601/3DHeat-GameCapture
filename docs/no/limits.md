---
title: Begrensninger og verifisering
nav_order: 9
lang: "no"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Begrensninger og hva som er verifisert {#limits-and-what-is-verified}

En ærlig liste: hva verktøyene ikke gjør, og hva som ikke er sjekket mot et kjørende spill.

## Telemetri {#telemetry}

| Opptaker | Status |
|---|---|
| Forza | Bygget på den offisielle Data Out-dokumentasjonen; oppsettet oppdages fra pakkene selv. Visningsprogrammets `.tele.gz`-leser for FH Companion er sjekket på ekte runder. |
| AC, ACC, AC EVO, AC Rally | Testet på syntetiske sider bygget fra de publiserte oppsettene. **Ikke kjørt mot de levende spillene ennå.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testet på pakker bygget fra de dokumenterte oppsettene. **Ikke kjørt mot de levende spillene ennå.** RBRs akser, holdning og fartsenheter er ikke dokumentert og håndteres ut fra dataene. |
| BeamNG.drive | Opptakeren er testet på pakker bygget fra modens struct. **Modifikasjonen er ikke kjørt i spillet.** |
| Trackmania | Visningsprogrammets leser av CSV-filen er testet. **Pluginen er ikke kjørt i spillet.** Den lastes bare i utviklermodus i Openplanet. |
| iRacing | Visningsprogrammets leser for `.ibt` er testet på en syntetisk fil. |

Andre begrensninger for telemetri:

- Forzas normalisering av slip er ikke dokumentert. Kunos slip skaleres med en typisk asfalttopp, som er en tilnærming.
- Retningen på noen sideakser i bilens ramme (Kunos, DiRT) er dokumentert på begge måter. Størrelsen på driftvinkelen er pålitelig, fortegnet ikke.
- Ingen av rallyspillene sender dekkglidning. Den beregnes i visningsprogrammet. RBR sender ingen hjulhastigheter.
- Et rallyetappes underlag skrives bare når `--surface` er oppgitt. Ellers oppgir filen ingen, og visningsprogrammet utleder det (etappe- eller hendelsesnavn, deretter kjørestil, løst som standard).
- Rundedeteksjon uten rundeteller (AC EVO, AC Rally, BeamNG) bruker punktet der opptaket startet som linje. Start derfor opptaket på startstreken.
- En tilbakestilling av et BeamNG-kjøretøy avslutter runden som er åpen i det øyeblikket. Den skrives som en delvis kjøring når den dekket minsteavstanden (300 m), og forkastes ellers.
- `route` lagrer omtrent hvert 2. sekund mens man kjører. Et krasj eller en avsluttet prosess mister høyst posisjonene siden forrige lagring.
- Forza Horizon sender ikke et banenavn, så Forza-rundefiler har `"track": null`. Forza Motorsport (2023) sender bare et nummer, som lagres som `lap.trackOrdinal`.

## Rekonstruksjon {#reconstruction}

- **Dybden er estimert, ikke lest.** Det er grensen for hele tilnærmingen, og prisen for aldri å røre spillprosessen.
- **Synsfeltet er antatt, ikke målt.** For smalt, og nivået rekonstrueres dypere enn det er.
- **Global skala** kommer fra en antatt kamerahøyde (1,15 m i vinduet), eller fra telemetri. Den måles på den første nøkkelrammen. Når den ikke har brukbar bakke, prøves de neste nøkkelrammene (opptil 30 rammer), og en skala som finnes senere, brukes på hele nivået når det skrives. Linjen «Size:» i vinduet sier hva som skjedde. Uten at det finnes bakke i det hele tatt, forblir skanningen uten enheter. Voxel-størrelsen er da i enhetene til den første rammen, så størrelsen i meter avviker fra innstillingen. Offline-rekonstruksjoner er i løserens egne enheter.
- **Sløyfelukking er av**, og den er ikke en posegraf når den slås på i koden. Driften er bare begrenset av kvaliteten på sporingen fra ramme til ramme.
- **Vindusbasert bundle-justering finnes, men er ikke koblet inn.** Den kollapset på ekte opptak.
- **Overflaten er vektet okkupasjon, ikke en TSDF.** Tynne strukturer og fritt rom blir dårligere enn en TSDF ville gitt.
- **Ingen teksturatlas.** Fargen er per hjørne (`COLOR_0`), blandet fra de 4 beste synsvinklene blant 160 beholdte rammer. Okklusjonstesten er grov: den tester mot meshets egne hjørner i en 2-piksels dybdebuffer. Et okkluderende objekt som ikke finnes i meshet (en forbikjørende bil), fanges derfor ikke.
- **Vann merkes aldri**; alt er bakke eller struktur.
- **Løsning med fremoverkobling er ikke live**: den krever først opptaket. Den adaptive nyløsningen av vanskelige partier er ikke bygget.
- **Telemetriposisjoner** plasserer kameraet ved bilen (forskyvningen til et chase-kamera er ukjent). Posisjonene tas slik Forza sender dem (Y opp, som i rundefilene). Retningene for gir, stigning og rulling er lest av innspilte runder (kjøreretning, helning, hvilken side fjæringen trykkes sammen på), ikke av det kjørende spillets kamera.
- Overlegget kan ikke tegne over **eksklusiv fullskjerm**. Bruk kantløs fullskjerm.
- Globale hurtigtaster, det gjennomsiktige overlegget og direkte opptak fungerer bare på **Windows**.
- Når vinduet lukkes, spørres det ikke om lagring.

## Hva som er målt {#what-is-measured}

- `tests/test_accuracy.py`: et syntetisk rom med en kjent bane og analytisk dybde. Det måler plasserte rammer, banefeil, tilbakelagt avstand, romstørrelse og overflaten på veggene ([Nivårekonstruksjon](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: en vei med kjent bredde, kjørt forskjøvet fra midten, rekonstrueres med riktig bredde.
- `tests/test_track_scale.py`: overflateuttrekk i racerbanestørrelse, minnebruk proporsjonal med det som ble skannet, og blokker som settes sammen til én overflate.
- `tests/test_glb.py` pluss visningsprogrammets egne tester: `.glb`-kontrakten sett fra begge sider.
- Hvordan dybdenettverket fungerer på ekte spilling, kan ikke et syntetisk scenario svare på, og det måles ikke av testsuiten.
