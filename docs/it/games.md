---
title: Giochi
nav_order: 4
lang: "it"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Giochi: registrazione e tracciati {#games-recording-and-courses}

Come viene registrato ogni gioco supportato, cosa invia e quali dei suoi tracciati
si possono esportare dai file del gioco stesso.

Le regole sono le stesse per ogni gioco: un tracciato arriva da file che l'utente
possiede, oppure viene ricostruito dal gameplay dell'utente. Gli archivi cifrati si
aprono solo con una chiave che l'utente già possiede - qui non viene distribuita né
recuperata nessuna chiave, e nulla si inietta nel processo di un gioco. La telemetria
arriva solo dalle interfacce che i giochi pubblicano per questo scopo (uscite UDP,
memoria condivisa, le loro interfacce di mod e plugin). Ciò su cui l'utente punta gli
strumenti resta soggetto alla licenza di quel gioco.

## Telemetria {#telemetry}

Ogni gioco finisce in file `heat3d-lap` ([`lap-format.md`](lap-format.md)), con nomi
di canale canonici e un blocco `meta` che spiega il significato dei suoi numeri - come
viene scalato il suo slittamento, circuito o rally o arcade, la superficie quando è
nota - così un lettore li tratta tutti allo stesso modo. Tutti i comandi sono
`python -m heat3d_capture ...` in questo repository.

| Gioco | Come registrare | Posizione | Gomme e slittamento | Angolo di deriva | Stato |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out via UDP: `heat3d_capture telemetry` (inoltra a FH Companion) - oppure il file `.tele.gz` di FH Companion accanto a ogni giro, caricato con il file del giro | XYZ nel mondo | rapporto di slittamento, angolo di slittamento, slittamento combinato per ruota, normalizzati; rumble della superficie | velocità nel sistema dell'auto | registratore testato; lettore `.tele.gz` verificato su giri reali |
| Forza Motorsport (incl. 2023) | lo stesso; distinti dalla lunghezza del pacchetto | XYZ nel mondo | lo stesso | lo stesso | registratore testato |
| Assetto Corsa, ACC, AC EVO | memoria condivisa: `telemetry --game ac / acc / acevo` | media dei punti di contatto delle gomme | rapporto e angolo di slittamento (fisici, scalati su un picco d'asfalto); ABS e TC in funzione (ACC, EVO) | velocità nel sistema dell'auto | registratore testato su pagine sintetiche |
| Assetto Corsa Rally | `telemetry --game acrally` | lo stesso | lo stesso; carichi delle ruote; temperature convertite da kelvin | velocità nel sistema dell'auto | registratore testato su pagine sintetiche |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documenti>/My Games/WRC/telemetry/config.json"` attiva il pacchetto predefinito `wrc` (il file viene prima copiato come backup) | XYZ nel mondo | velocità del punto di contatto per ruota; slittamento derivato | dagli assi dell'auto e dalla sua velocità | registratore testato su pacchetti costruiti dal layout documentato |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: imposta `<udp enabled="true" extradata="3" port="20777" delay="1" />` in `hardware_settings_config.xml`, poi `telemetry --game dirtrally2` (o `dirtrally`, `dirt4`) | XYZ nel mondo | velocità del punto di contatto per ruota; slittamento derivato. Nessun canale del freno a mano | dagli assi dell'auto e dalla sua velocità | lo stesso |
| Richard Burns Rally (RSF/NGP) | telemetria UDP di NGP (`udpTelemetry=1`): `telemetry --game rbr` | mondo, asse verticale ricavato dalla tappa | deflessione e forza della molla per ruota; nessuna velocità delle ruote | le velocità proprie dell'auto | lo stesso; assi e unità di velocità non documentati, gestiti dai dati |
| BeamNG.drive | la mod del protocollo `heat3d`: `telemetry --game beamng --install`, poi Opzioni > Altro > Protocolli > "others" | mondo, ruotato con Y verso l'alto | velocità superficiale della ruota, rotazione, carico, contatto con il suolo; slittamento derivato | dagli assi dell'auto e dalla sua velocità | registratore testato su pacchetti costruiti dalla struct della mod; la mod non è testata nel gioco |
| Trackmania (2020) | il plugin Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, caricato in modalità sviluppatore di Openplanet; un CSV per corsa nella sua cartella di archiviazione | XYZ nel mondo | coefficiente di slittamento di Trackmania per ruota; fondo sciolto dal materiale delle ruote; in aria | velocità frontale e laterale | lettore testato; il plugin non è testato nel gioco |
| iRacing | i suoi file `.ibt`; non serve nessun registratore | latitudine/longitudine/altitudine, proiettate su un piano tangente | nessuno slittamento (non registrato); velocità di imbardata e accelerazione laterale | dalla velocità di imbardata rispetto al percorso | lettore testato su un file sintetico |

Ciò che nessun gioco rally invia - lo slittamento delle gomme - viene calcolato da un
lettore: dalla velocità del punto di contatto di ogni ruota o dalla sua velocità di
superficie rispetto alla velocità dell'auto, dove un gioco ne invia una
(`(ruota - auto) / auto`), oppure dalla sua rotazione e da un raggio di rotolamento
misurato sul giro stesso, dove invia solo la rotazione. L'angolo di deriva viene dalla
velocità propria dell'auto (Forza, i giochi AC, Trackmania, RBR), dalla velocità nel
mondo proiettata sugli assi dell'auto (EA WRC, DiRT, BeamNG), oppure dalla direzione
dell'auto rispetto al percorso. Se l'auto è in aria si ricava dal contatto, dai carichi
o dalle sospensioni delle sue ruote.

Dove il mondo di un gioco è sinistrorso - quello di Forza lo è - il tracciato esce
specchiato in un visualizzatore destrorso; lo sterzo e le sospensioni dei giri stessi
lo rivelano. I giochi la cui lateralità non è documentata (RBR, BeamNG, Trackmania)
vengono trattati allo stesso modo: misurata, non data per scontata.

Oltre ai canali di guida, i registratori conservano ciò che ogni gioco aggiunge: su
i giochi AC, l'ABS e il controllo di trazione in funzione, la ripartizione della
frenata, DRS, limitatore di corsia dei box, turbo e durata delle pastiglie e dei
dischi; per iRacing, le impostazioni degli aiuti, la ripartizione della frenata,
carburante, temperature di olio e acqua, e ogni altro canale che registra con il proprio
nome.

### Fonti e cosa non è ancora confermato {#sources-and-what-is-not-yet-confirmed}

- **Forza:** la documentazione ufficiale di Data Out (Forza Motorsport; Forza
  Horizon 6) per i campi, le loro unità e il sistema dell'auto (x a destra, y verso
  l'alto, z in avanti - sinistrorso). Non è documentato con cosa Forza normalizza lo
  slittamento: misura dove la presa di ogni auto cala davvero invece di supporre che
  1 sia il limite.
- **Kunos:** l'SDK di AC1, la documentazione della memoria condivisa di ACC v1.8.12,
  `albertowd/live-telemetry-evo` (EVO, misurato; AC Rally usa il layout di ACC,
  "confermato con un probe byte per byte"), `LuizZak/AssettoCorsaRallyTelemetryReader`.
  Il lato verso cui punta l'asse x dell'auto è documentato in entrambi i sensi: usa la
  grandezza dell'angolo di deriva, non il suo segno.
- **EA SPORTS WRC:** la Guida UDP Telemetry v1.3 di EA e l'elenco dei canali che il
  gioco scrive in `readme/channels.json`; gli offset del pacchetto predefinito `wrc`
  come decodificati da nobonobo/obs-codemasters-telemetry. La porta predefinita di
  fabbrica non è documentata; il registratore attiva il pacchetto sulla porta 20777.
- **DiRT:** il documento UDP di Codemasters per DiRT 4, ErlerPhilipp/dr2_logger,
  soong-construction/dirt-rally-time-recorder. Il verso del vettore laterale e l'unità
  della posizione delle sospensioni sono documentati in entrambi i sensi; nessuno dei
  due decide un risultato.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` di NGP (tramite
  mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Gli assi di posizione, le unità
  dell'assetto e l'unità di velocità non sono documentati: il registratore prende
  l'asse verticale dalla tappa e la velocità dalle posizioni.
- **BeamNG:** documentation.beamng.com (protocolli; refNodes: veicolo +X a sinistra,
  -Y in avanti, Z verso l'alto), e i file `lua/vehicle/protocols.lua` e `wheels.lua`
  del gioco stesso. OutSim è un segnaposto nelle versioni attuali; OutGauge non ha la
  posizione e MotionSim non ha le ruote, da qui la mod.
- **Trackmania:** il plugin Openplanet `CSceneVehicleVisState` e VehicleState, il tempo
  di gara da `CSmScriptPlayer`. I plugin Openplanet non possono inviare UDP, quindi il
  plugin scrive file. I plugin non firmati si caricano solo in modalità sviluppatore,
  il che limita il gioco online; il plugin si può firmare su openplanet.dev.

Nessuno dei registratori è ancora stato eseguito contro i giochi veri qui; la prima
sessione reale di ciascuno è il test che conta, e `tests/test_kunos.py`,
`test_rally.py` e `test_beamng.py` fissano i layout per cui sono stati costruiti.
Ogni registratore controlla i pacchetti man mano che arrivano - la velocità contro la
velocità dell'auto, la dimensione della struct - e segnala quando un layout non
corrisponde.

## Tracciati: cosa si esporta, per gioco {#courses-what-is-exported-per-game}

Un tracciato aggiunge i cordoli, i muri e le vie di fuga che spiegano una traiettoria.
I tracciati vengono esportati da [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles)
(`python -m heat3d_gamefiles course <giro>`), dai file del gioco stesso, dove
l'esportazione è stata costruita e verificata su una copia installata. I dettagli sono
nella [documentazione di GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Gioco | Tracciato da un giro |
|---|---|
| Forza Horizon | sì |
| BeamNG.drive | sì |
| Assetto Corsa Rally | sì |
| Assetto Corsa EVO | no: il suo contenuto non è leggibile come file |
| iRacing | no: i modelli dei circuiti sono in un formato protetto |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | non ancora: ciascuno richiede una copia installata per essere costruito e verificato |

Nel frattempo, il percorso dal gameplay descritto sotto funziona per tutti.

## Il percorso che funziona per ogni gioco {#the-route-that-works-for-every-game}

GameCapture ricostruisce un livello dal video del gameplay. La sua parte difficile
è il percorso della camera, ed è esatto per Forza perché la telemetria dà la posa
dell'auto a ogni fotogramma. Ogni gioco qui sopra ora ha la stessa cosa: posizione e
assetto, in tempo reale, da un'interfaccia documentata. Passarli a
`pose/telemetry_pose.py` al posto di quelli di Forza è l'unico pezzo che rende esatto
il percorso dal gameplay per tutti - il resto della pipeline (profondità, fusione,
texture) non si cura di quale gioco ha disegnato i fotogrammi.
