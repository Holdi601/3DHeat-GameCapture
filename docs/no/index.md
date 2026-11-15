---
title: Hjem
nav_order: 1
lang: "no"
source: index.md
source_hash: "af8f09bf55f3"
nav_exclude: true
search_exclude: true
permalink: /no/
---
# 3DHeat GameCapture {#dheat-gamecapture}

**Hva er det?** Et verktøy som skriver ned det et racingspill forteller om kjøringen din,
én fil per runde. Det kan også lage en grov 3D-modell av et nivå fra en video av deg
som spiller.

**Hvorfor skulle jeg bruke det?** For å se rundene dine i [3DHeat-visningsprogrammet](https://holdi601.github.io/3DHeat/):
der du bremset, der du var treg, og hvordan to runder skiller seg. Og for å ha nivået
under varmekartet ditt når ingen har en 3D-modell av det.

**Eksempel:** slå på Forzas Data Out, kjør én kommando, og kjør to runder. To rundefiler
dukker opp i `laps\`. Slipp dem på visningsprogrammets fane for løpsanalyse.

![telemetri som tar opp to runder fra en syntetisk Forza-strøm](../assets/img/telemetry-run.svg)

Ny til kommandolinjen? Les [Før du begynner](before-you-start.md) først.

## De tre jobbene {#the-three-jobs}

1. **Rundetelemetri.** Den tar opp alle kanaler et racingspill publiserer - Forzas Data Out, Assetto Corsa-spillenes
   delte minne, rallyspillenes nettverksstrømmer, en BeamNG-mod, en Trackmania-plugin - og skriver én
   `heat3d-lap`-fil per runde eller etappe, for visningsprogrammets fane for løpsanalyse. iRacing trenger ingen
   opptaker: visningsprogrammet leser sine egne `.ibt`-filer.
2. **Nivåer fra spilling.** Den gjør det skjermen viste mens du gikk eller kjørte gjennom et nivå, om til en
   `.glb`-3D-modell, som visningsprogrammet legger under varmekartet.
3. **Din egen kamp, etterpå.** `hud` leser HUD-en i din egen opptak - dine handlinger, dødsfall, minikartets
   spor og drapsloggen. `locate` (eksperimentell: den plasserer få ekte bilder så langt) finner ut hvor hvert
   bilde ble tatt, på et nivås 3D-modell.

Alle tre følger én regel: **ingenting injiseres i et spill, og ingenting kobles inn**. Bilder kommer fra det
offentlige skjermfangst-API-et, telemetri fra grensesnitt spillene publiserer for det. Se [Reglene](rules.md).

![Hva som går inn, hvilken kommando, hva som kommer ut, og hvor visningsprogrammet viser det](../assets/img/no/overview.svg)

Koden er Python (pakke `heat3d_capture`), MIT-lisensiert. Dybde- og posemodellene den kan kjøre,
har sine egne lisenser - se [Modeller og lisenser](models-and-licences.md).

## Hurtigstart {#quick-start}

### Ta opp runder {#record-laps}

Du trenger Python 3.10 eller nyere ([Før du begynner](before-you-start.md)). I PowerShell:

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# Forza: Settings -> HUD and Gameplay -> Data Out = ON, IP 127.0.0.1, port 5300
.venv\Scripts\python -m heat3d_capture telemetry -o laps
```

**Du bør se** `listening on port 5300. Laps go to laps. Ctrl+C to stop.`, deretter en linje per runde når du
passerer målstreken, som på bildet ovenfor. Trykk Ctrl+C for å stoppe. Slipp filene fra `laps\` på
visningsprogrammets fane for løpsanalyse. Hvert annet spill er ett `--game`-valg unna:

```powershell
.venv\Scripts\python -m heat3d_capture telemetry --game acc -o laps
.venv\Scripts\python -m heat3d_capture telemetry --game dirtrally2 -o laps
```

Se [Telemetriopptakere](telemetry.md) for alle spill og alternativer.

### Skann et nivå {#scan-a-level}

Dobbeltklikk på **`scan.bat`** i verktøyets mappe. Den finner Python (og tilbyr å installere det med
winget hvis det ikke finnes), lager en privat `.venv`, og åpner skannevinduet. Vinduet sier hva som mangler,
hva hver pakke er til for og hvor stor nedlastingen er, og installerer ingenting uten et ja. Se
[Kjøretid og avhengigheter](runtime.md) og [Skannevinduet](reconstruction-scan-ui.md).

For hånd: `.venv\Scripts\python -m heat3d_capture.ui`.

For å rekonstruere en opptak frakoblet, med kamerabanen løst på én gang (krever PyTorch, pakken `vggt` og en GPU -
se [Frakoblet rekonstruksjon](reconstruction-offline.md)):

```powershell
.venv\Scripts\python -m heat3d_capture reconstruct lap.mp4 -o lap.glb
```

## Oversikt over dokumentasjonen {#map-of-the-documentation}

| Side | Hva den dekker |
|---|---|
| [Før du begynner](before-you-start.md) | Python, en terminal, den første kommandoen, vanlige feil |
| [Reglene](rules.md) | Ingen injeksjon, kun publiserte grensesnitt, og hva det koster |
| [Telemetriopptakere](telemetry.md) | Kommandoen `telemetry` og en oversikt over hvert spill |
| [Forza](telemetry-forza.md) | Data Out, oppdagelse av layout, FH Companion-reléen og dens `.tele.gz` |
| [Assetto Corsa-spill](telemetry-assetto-corsa.md) | AC, ACC, AC EVO, AC Rally fra delt minne |
| [Rallyspill](telemetry-rally.md) | EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally |
| [BeamNG.drive](telemetry-beamng.md) | `heat3d`-protokollmodden |
| [Trackmania](telemetry-trackmania.md) | `Heat3dRecorder`-Openplanet-pluginen |
| [iRacing](telemetry-iracing.md) | Lesing av `.ibt`-filer i visningsprogrammet |
| [Deling av runder og etapper](lap-splitting.md) | `LapSplitter`, `CounterSplitter`, `LineSplitter`, `StageSplitter` |
| [Slip, drift og avledede kanaler](slip-and-drift.md) | Hvordan slip skaleres, og hva visningsprogrammet avleder |
| [heat3d-lap-filen](lap-format.md) | Rundefilformatet, kanaler, enheter, `meta` |
| [Spill](games.md) | Per spill: hvordan du tar opp, hva som sendes, hvilke baner som kan eksporteres |
| [Kommandoer](commands.md) | `route`, `telemetry`, `laps`, `reconstruct`, `hud`, `locate`, steg for steg |
| [Kommandoreferanse](../cli-reference.md) | hvert alternativ, generert fra `--help` |
| [Lese HUD-en fra en opptak](hud-video.md) | `hud`: egne handlinger, dødsfall, minikartets spor og drapsloggen fra en opptak |
| [Finne bilder i et nivå](locate.md) | `locate`: hvor hvert bilde ble tatt, mot nivåets geometri |
| [Nivårekonstruksjon](reconstruction.md) | Rørledningen fra bilder til en `.glb` |
| [Skannevinduet](reconstruction-scan-ui.md) | Hver kontroll, hurtigtast og overlegg-element |
| [Fangst, masker og bildekvalitet](reconstruction-capture.md) | Windows Graphics Capture, nøkkelbilder, HUD-masker, kvalitetsråd |
| [Dybde](reconstruction-depth.md) | Depth Anything V2, ONNX Runtime, bygging av modellen |
| [Kameraposisjon og skala](reconstruction-pose.md) | Odometri, relokalisering, telemetriposisjoner, bakkeskala, bundle adjustment |
| [Sammensmelting, dekning og farge](reconstruction-fusion-and-texture.md) | Okkupasjonsvolumet, dekningsnettet, svake punkter, vertekselfarge |
| [.glb-utdata](glb-output.md) | Filen visningsprogrammet laster |
| [Frakoblet rekonstruksjon](reconstruction-offline.md) | `reconstruct`, VGGT-vinduer og sammenstilling |
| [Modeller og lisenser](models-and-licences.md) | Størrelser for Depth Anything V2, VGGT, pakkene |
| [Kjøretid og avhengigheter](runtime.md) | Forhåndssjekk, bakender, ytelsesnivåer |
| [Begrensninger og verifisering](limits.md) | Hva som ikke er gjort, og hva som ikke er kontrollert |
| [Oppdateringer](updates.md) | Utgivelsessjekken og `python -m heat3d_update` |
| [Utvikling](development.md) | Tester, det virtuelle miljøet, depotoppsettet |
| [Vedlikehold av dokumentasjonen](maintaining.md) | Utgivelsessjekklisten for kode og dokumentasjon |

## Del av 3DHeat {#part-of-3dheat}

Filene dette skriver lastes av **3DHeat-visningsprogrammet** -
[kildekode](https://github.com/Holdi601/3DHeat), [dokumentasjon](https://holdi601.github.io/3DHeat/).
Rundefiler går til fanen for løpsanalyse, `.glb`-nivåer til panelet for Bakgrunn / nivå, og `hud`- og
`locate`-tabellene til varmekart-fanen; hvordan visningsprogrammet leser tabeller og kampfiler står i
[Én fil per kamp (.3dheat)](https://holdi601.github.io/3DHeat/container.html) og
[Få inn data](https://holdi601.github.io/3DHeat/getting-data-in.html).

| Verktøy | Hva det gjør | Dokumentasjon |
|---|---|---|
| [3DHeat-visningsprogram](https://github.com/Holdi601/3DHeat) | viser varmekart, løp og kamper i 3D, i nettleseren | [dokumentasjon](https://holdi601.github.io/3DHeat/) |
| [GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) | baner og nivåer fra filene spill leveres med, som 3D-modeller | [dokumentasjon](https://holdi601.github.io/3DHeat-GameFiles/) |
| [GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) | rundetelemetri fra racingspill; nivåer rekonstruert fra spillvideo | [dokumentasjon](https://holdi601.github.io/3DHeat-GameCapture/) |
| [Unreal Exporter](https://github.com/Holdi601/3DHeat-UnrealExporter) | et Unreal Editor-tillegg som eksporterer et nivå som en 3D-modell | [dokumentasjon](https://holdi601.github.io/3DHeat-UnrealExporter/) |
| [CS2](https://github.com/Holdi601/3DHeat-CS2) | Counter-Strike 2-demoer til kampfiler; kart til 3D-modeller | [dokumentasjon](https://holdi601.github.io/3DHeat-CS2/) |
| [Watcher](https://github.com/Holdi601/3DHeat-Watcher) | tar opp spilling din i bakgrunnen, fra det spill publiserer | [dokumentasjon](https://holdi601.github.io/3DHeat-Watcher/) |
| [Ext-WarThunder](https://github.com/Holdi601/3DHeat-Ext-WarThunder) | War Thunder-replays til tabeller og kampdokumenter | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-WarThunder/) |
| [Ext-WoT](https://github.com/Holdi601/3DHeat-Ext-WoT) | World of Tanks-replays til tabeller og kampdokumenter | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-WoT/) |
| [Ext-WoWs](https://github.com/Holdi601/3DHeat-Ext-WoWs) | World of Warships-replays til tabeller og kampdokumenter | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-WoWs/) |
| [Ext-Squad](https://github.com/Holdi601/3DHeat-Ext-Squad) | Squad-serverdemoer til tabeller og kampdokumenter | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Squad/) |
| [Ext-DCS](https://github.com/Holdi601/3DHeat-Ext-DCS) | DCS World-kart til 3D-modeller | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-DCS/) |
| [Ext-IL2](https://github.com/Holdi601/3DHeat-Ext-IL2) | IL-2 Sturmovik-kart til 3D-modeller | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-IL2/) |
| [Ext-Dota](https://github.com/Holdi601/3DHeat-Ext-Dota) | Dota 2-kartet fra din egen installasjon som et 3D-nivå | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Dota/) |
| [Ext-DotaReplay](https://github.com/Holdi601/3DHeat-Ext-DotaReplay) | Dota 2-replays | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-DotaReplay/) |
| [Ext-Riot](https://github.com/Holdi601/3DHeat-Ext-Riot) | League of Legends- og VALORANT-replays (det de bærer ukryptert) | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Riot/) |
| [Ext-Forza](https://github.com/Holdi601/3DHeat-Ext-Forza) | Forza-baner, løp og biler fra din egen installasjon | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Forza/) |
| [Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield) | Battlefield-nivåer (Frostbite) som 3D-nivåer | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Battlefield/) |
| [Ext-BeamNG](https://github.com/Holdi601/3DHeat-Ext-BeamNG) | BeamNG.drive-baner | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-BeamNG/) |
| [Ext-ACRally](https://github.com/Holdi601/3DHeat-Ext-ACRally) | Assetto Corsa Rally-etapper som baner | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-ACRally/) |
| [Ext-Reforger](https://github.com/Holdi601/3DHeat-Ext-Reforger) | Arma Reforger-verdener (Enfusion) som 3D-nivåer | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-Reforger/) |
| [Ext-R6](https://github.com/Holdi601/3DHeat-Ext-R6) | Rainbow Six Siege-kampreplays | [dokumentasjon](https://holdi601.github.io/3DHeat-Ext-R6/) |

En utvikler med spillets prosjekt åpent bør bruke Unreal-eksporteren, som leser den ekte geometrien
og er nøyaktig. Der et spills egne arkiver kan leses, henter GameFiles den nøyaktige banen. Rekonstruksjon
fra spilling er til for tilfellet der bare skjermen er tilgjengelig.
