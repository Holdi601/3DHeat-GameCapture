---
title: "Beperkingen en controle"
nav_order: 9
lang: "nl"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Beperkingen en wat is gecontroleerd {#limits-and-what-is-verified}

Een eerlijke lijst: wat de tools niet doen, en wat niet tegen een draaiend spel is gecontroleerd.

## Telemetrie {#telemetry}

| Recorder | Status |
|---|---|
| Forza | Gebouwd op de officiële Data Out-documentatie; de indeling wordt uit de pakketten zelf herkend. De `.tele.gz`-lezer van de FH Companion in de viewer is op echte ronden gecontroleerd. |
| AC, ACC, AC EVO, AC Rally | Getest op synthetische pagina's die uit de gepubliceerde indelingen zijn gebouwd. **Nog niet tegen de echte spellen gedraaid.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Getest op pakketten die uit de gedocumenteerde indelingen zijn gebouwd. **Nog niet tegen de echte spellen gedraaid.** De assen, de houding en de snelheidseenheden van RBR zijn niet gedocumenteerd en worden uit de data afgeleid. |
| BeamNG.drive | De recorder is getest op pakketten die uit de struct van de mod zijn gebouwd. **De mod is niet in het spel gedraaid.** |
| Trackmania | De CSV-lezer van de viewer is getest. **De plugin is niet in het spel gedraaid.** Hij laadt alleen in de ontwikkelaarsmodus van Openplanet. |
| iRacing | De `.ibt`-lezer van de viewer is getest op een synthetisch bestand. |

Andere beperkingen van de telemetrie:

- De normalisatie van de slip van Forza is niet gedocumenteerd; de slip van Kunos wordt geschaald naar een
  gebruikelijke piek op asfalt, een benadering.
- De zin van sommige laterale assen van het autoframe (Kunos, DiRT) is op beide manieren gedocumenteerd; de
  grootte van de driftshoek is betrouwbaar, het teken niet.
- Geen van de rally-spellen stuurt de slip van de banden; die wordt in de viewer afgeleid. RBR stuurt geen
  wielsnelheden.
- Het wegdek van een rallyetappe wordt alleen geschreven wanneer `--surface` is opgegeven; anders noemt het
  bestand er geen en leidt de viewer het af (naam van de etappe of het evenement, dan de rijstijl, standaard
  los).
- Ronde-detectie zonder rondeteller (AC EVO, AC Rally, BeamNG) gebruikt het punt waar de opname begon als
  de lijn, dus begin de opname op de startlijn.
- Een reset van een BeamNG-voertuig sluit de ronde die op dat moment open stond: ze wordt geschreven als
  een gedeeltelijke run wanneer ze de minimumafstand (300 m) bedekte, anders weggegooid.
- `route` slaat ongeveer elke 2 seconden op tijdens het rijden; bij een crash of een afgebroken proces gaan
  hooguit de posities sinds de laatste keer opslaan verloren.
- Forza Horizon stuurt geen baannaam, dus Forza-rondebestanden hebben `"track": null`; Forza Motorsport
  (2023) stuurt alleen een getal, bewaard als `lap.trackOrdinal`.

## Reconstructie {#reconstruction}

- **De diepte wordt geschat, niet uitgelezen.** Het plafond van de hele aanpak, en de prijs van het nooit
  aanraken van het spelproces.
- **Het gezichtsveld wordt aangenomen, niet gemeten.** Te smal, en het level wordt dieper gereconstrueerd dan
  het is.
- **De globale schaal** komt van een aangenomen camerahoogte (1,15 m in het venster), of uit de telemetrie.
  Ze wordt op het eerste keyframe gemeten; als dat geen bruikbare grond heeft, worden de volgende keyframes
  geprobeerd (tot 30 beelden), en een later gevonden schaal wordt bij het schrijven op het hele level
  toegepast. De regel "Size:" van het venster zegt wat er gebeurd is; als er helemaal geen grond is gevonden,
  blijft de scan zonder eenheden. De voxelgrootte staat dan in de eenheden van het eerste beeld, dus de grootte
  in meters verschilt van de instelling. Offline reconstructies staan in de eigen eenheden van de oplossing.
- **Lusafsluiting staat uit** en is geen pose-graaf wanneer die in de code wordt aangezet; de drift wordt
  alleen begrensd door de kwaliteit van het volgen van beeld tot beeld.
- **Vensterbundel-aanpassing bestaat, maar is niet aangesloten**; die stortte in op echte beelden in elkaar.
- **Het oppervlak is gewogen bezetting, geen TSDF**: dunne structuren en vrije ruimte zijn slechter dan een
  TSDF zou halen.
- **Geen textuuratlas.** De kleur zit per hoekpunt (`COLOR_0`), gemengd uit de 4 beste aanzichten van de
  160 bewaarde beelden. De zichtbaarheidstest is grof: hij toetst aan de eigen hoekpunten van het mesh in een
  dieptebuffer van 2 pixels, dus een afdekkend object dat het mesh niet bevat (een passerende auto) wordt niet
  gevangen.
- **Water wordt nooit gelabeld**; alles is grond of structuur.
- **Oplossen vanuit het model is niet live**: het heeft eerst de opname nodig. De adaptieve herberekening van
  moeilijke stukken is niet gebouwd.
- **Telemetrie-poses** plaatsen de camera bij de auto (de verschuiving van een achtervolgingscamera is
  onbekend). Posities worden overgenomen zoals Forza ze stuurt (y omhoog, zoals in de rondebestanden); de
  zin van gier, helling en rol is afgelezen aan opgenomen ronden (rijrichting, helling, welke kant van de
  ophanging indrukt), niet aan de camera van het draaiende spel.
- De overlay kan niet over **exclusief volledig scherm** tekenen; gebruik randloos venster.
- Globale sneltoetsen, de klik-doorlatende overlay en live opname werken alleen op **Windows**.
- Het sluiten van het venster vraagt niet om op te slaan.

## Wat is gemeten {#what-is-measured}

- `tests/test_accuracy.py`: een synthetische kamer met een bekend pad en analytische diepte - geplaatste
  beelden, padfout, afgelegde afstand, kamergrootte, oppervlak op de muren
  ([Levelreconstructie](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: een weg met bekende breedte, uit het midden gereden, reconstrueert zijn breedte.
- `tests/test_track_scale.py`: oppervlakte-extractie op racebaanschaal, geheugen evenredig met wat gescand is,
  blokken die samenvoegen tot één oppervlak.
- `tests/test_glb.py` plus de eigen tests van de viewer: het `.glb`-contract van beide kanten.
- Hoe het dieptenetwerk het doet op echt gameplay is niet iets wat een synthetische scène kan beantwoorden, en
  wordt niet door de testsuite gemeten.
