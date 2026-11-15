---
title: Begränsningar och verifiering
nav_order: 9
lang: "sv"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Begränsningar och vad som är verifierat {#limits-and-what-is-verified}

En ärlig lista: vad verktygen inte gör, och vad som inte har kontrollerats mot ett spel som körs.

## Telemetri {#telemetry}

| Inspelare | Status |
|---|---|
| Forza | Byggd på den officiella Data Out-dokumentationen; layouten identifieras från paketen själva. Visarens läsare för FH Companions `.tele.gz` har kontrollerats på riktiga varv. |
| AC, ACC, AC EVO, AC Rally | Testad på syntetiska sidor byggda utifrån de publicerade layouterna. **Ännu inte körd mot de levande spelen.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testad på paket byggda utifrån de dokumenterade layouterna. **Ännu inte körd mot de levande spelen.** RBR:s axlar, attityd och hastighetsenheter är odokumenterade och hanteras utifrån datan. |
| BeamNG.drive | Inspelaren är testad på paket byggda utifrån modens struct. **Modden har inte körts i spelet.** |
| Trackmania | Visarens läsare av CSV-filen är testad. **Insticksprogrammet har inte körts i spelet.** Det laddas bara i Openplanets utvecklarläge. |
| iRacing | Visarens läsare av `.ibt` är testad på en syntetisk fil. |

Andra begränsningar för telemetrin:

- Forzas normalisering av sladd är odokumenterad; Kunos sladd skalas med en typisk asfaltstopp, en
  approximation.
- Riktningen för vissa sidoaxlar i bilens ram (Kunos, DiRT) är dokumenterad åt båda hållen; driftvinkelns
  storlek är tillförlitlig, dess tecken inte.
- Inget av rallyspelen skickar däcksladd; den beräknas i visaren. RBR skickar inga hjulhastigheter.
- En rallysträckas underlag skrivs bara när `--surface` anges; annars anger filen inget och visaren
  gissar (sträckans eller eventets namn, sedan körstilen, löst som standard).
- Varvdetektering utan varvräknare (AC EVO, AC Rally, BeamNG) använder punkten där inspelningen började som
  linje, så starta inspelningen vid startlinjen.
- En återställning av ett BeamNG-fordon stänger det öppna varvet just då: det skrivs som ett delvis
  varv när det täckte den minsta sträckan (300 m), och släpps annars.
- `route` sparar ungefär var 2:a sekund under körning; en krasch eller en avslutad process förlorar högst
  positionerna sedan den senaste sparningen.
- Forza Horizon skickar inget bannamn, så Forza-varvfiler har `"track": null`; Forza Motorsport (2023)
  skickar bara ett nummer, sparat som `lap.trackOrdinal`.

## Rekonstruktion {#reconstruction}

- **Djupet är uppskattat, inte läst.** Det är hela metodens tak, och priset för att aldrig röra spelprocessen.
- **Synfältet är antaget, inte uppmätt.** För smalt, och banan rekonstrueras djupare än den är.
- **Den globala skalan** kommer från en antagen kamerahöjd (1,15 m i fönstret), eller från telemetri. Den mäts
  på första nyckelbilden; när den saknar användbar mark prövas de följande nyckelbilderna (upp till 30 bildrutor),
  och en skala som hittas senare tillämpas på hela banan när den skrivs. Fönstrets rad "Size:" säger vad som
  hände; utan att någon mark hittas alls förblir skanningen utan enhet. Voxelstorleken anges då i den första
  bildrutans enheter, så dess storlek i meter skiljer sig från inställningen. Offline-rekonstruktioner är i
  lösningens egna enheter.
- **Slutning av slingor är avstängt** och är inte en postgraf när det slås på i koden; driften begränsas bara av
  kvaliteten på spårningen från bildruta till bildruta.
- **Ett fönster av bundle adjustment finns men är inte inkopplat**; det kollapsade på riktig film.
- **Ytan är viktad ockupation, inte en TSDF**: tunna strukturer och tomt utrymme blir sämre än de skulle bli med
  en TSDF.
- **Ingen texturatlas.** Färgen är per hörn (`COLOR_0`), blandad från de 4 bästa vyerna bland 160 sparade
  bildrutor. Ocklusionstestet är grovt: det prövar mot nätets egna hörn i en 2-pixlars djupbuffert, så en skymmare
  som nätet inte innehåller (en passerande bil) fångas inte.
- **Vatten märks aldrig**; allt är mark eller struktur.
- **Lösning med framåtmatning är inte live**: den kräver att inspelningen finns först. Den adaptiva omlösningen av
  svåra avsnitt är inte byggd.
- **Telemetriposer** placerar kameran vid bilen (en jaktkamera förskjutning är okänd). Positionerna tas som Forza
  skickar dem (Y upp, som i varvfilerna); riktningarna för gir, stigning och rulning lästes av inspelade varv
  (färdriktning, lutning, vilken sida av fjädringen som pressas ihop), inte av det körande spelets kamera.
- Överlägget kan inte rita över **exklusiv helskärm**; använd rutat fönsterläge utan kant.
- Globala snabbtangenter, överlägget som släpper igenom klick och liveinspelning är **bara för Windows**.
- Att stänga fönstret frågar inte om att spara.

## Vad som är uppmätt {#what-is-measured}

- `tests/test_accuracy.py`: ett syntetiskt rum med känd bana och analytiskt djup - bildrutor placerade,
  banfel, gången sträcka, rummets storlek, ytan på väggarna ([Nivårekonstruktion](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: en väg med känd bredd körd utanför mitten rekonstrueras med sin bredd.
- `tests/test_track_scale.py`: ytextraktion i racerbanans skala, minne proportionellt mot det som skannats, block
  som förenas till en yta.
- `tests/test_glb.py` tillsammans med visarens egna tester: `.glb`-kontraktet från båda sidor.
- Hur djupnätverket klarar sig på riktig spelning är inget en syntetisk scen kan besvara, och det mäts inte av
  testsviten.
