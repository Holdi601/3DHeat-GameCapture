---
title: iRacing
nav_order: 6
lang: "it"
source: telemetry-iracing.md
source_hash: "db9e52dfff86"
nav_exclude: true
search_exclude: true
---
# iRacing {#iracing}

iRacing **non ha bisogno di un registratore**. Il simulatore scrive i propri file di telemetria, `.ibt`,
quando la registrazione della telemetria è attiva (Alt+L nell'auto): l'intera sessione a 60 Hz, ogni
canale che il simulatore espone, con la descrizione YAML della sessione accanto. Trascina il file `.ibt`
nella scheda Analisi di gara del visualizzatore.

Il lettore si trova nel visualizzatore, non in questo repository (`src/race/ibt.ts` nel visualizzatore di 3DHeat). È
testato su un file sintetico; è documentato qui perché è la metà iRacing della stessa storia di
registrazione dei giri.

## Cosa contiene il file, e come viene letto {#what-the-file-holds-and-how-it-is-read}

Il file è il layout di memoria documentato del simulatore, scritto su disco:

| Parte | Dimensione | Contiene |
|---|---|---|
| Intestazione | 112 byte | versione, frequenza dei tick, dove si trovano lo YAML e la tabella delle variabili, la lunghezza di una riga di campioni, dove iniziano le righe |
| Sotto-intestazione del disco | 32 byte | data e ora di inizio, numero di giri, numero di righe |
| Tabella delle variabili | 144 byte per canale | tipo, offset nella riga, conteggio, nome, descrizione, unità |
| YAML | | `WeekendInfo`, `DriverInfo`, ... |
| Righe | una per tick | |

Un file viene rifiutato quando è più corto di 144 byte, quando la sua intestazione non è sensata
(nessuna variabile, una tabella delle variabili fuori dal file, una lunghezza di riga zero), quando
manca uno tra `SessionTime`, `Lap`, `Lat`, `Lon`, o quando nessun campione ha un fix di posizione.

## Posizione {#position}

iRacing riporta latitudine, longitudine e altitudine, non una posizione nel sistema di riferimento della
pista. Le posizioni vengono disposte in metri su un piano tangente al primo campione con un fix (raggio
terrestre 6.371.008,8 m): `x` verso est, `z` verso sud, `y` l'altitudine - così che, visto dall'alto
con l'orientamento predefinito della camera del visualizzatore, il nord è in alto nello schermo.

## Giri {#laps}

La sessione viene suddivisa in base al contatore `Lap` del simulatore. Un giro viene tenuto solo se ha
più di 60 campioni, parte sotto il 5% della distanza del giro (`LapDistPct`) e finisce sopra il 95% -
cioè giri percorsi da linea a linea. Se nessun giro si qualifica, il file viene rifiutato con un
messaggio che indica la lunghezza della pista dal YAML. `distance` è `LapDist` riportato all'inizio del
giro, oppure la distanza percorsa dalle posizioni quando `LapDist` manca; `time` è `SessionTime` dall'inizio
del giro.

## Canali {#channels}

| iRacing | Canale | Conversione |
|---|---|---|
| `Speed`, `Throttle`, `Brake`, `Gear`, `RPM` | `speed`, `throttle`, `brake`, `gear`, `rpm` | nessuna |
| `Clutch` | `clutch` | `1 - valore` (iRacing considera la frizione innestata; il canale è il pedale) |
| `SteeringWheelAngle` | `steer` | `-angolo / SteeringWheelAngleMax` (radianti, antiorario positivo, a -1..1 destro positivo; π quando il massimo manca) |
| `LatAccel`, `LongAccel`, `VertAccel` | `latAcc`, `longAcc`, `vertAcc` | nessuna |
| `Yaw`, `Pitch`, `Roll`, `YawRate` | `yaw`, `pitch`, `roll`, `yawRate` | nessuna |
| `BrakeABSactive` | `absActive` | |
| `dcABS`, `dcTractionControl` | `absLevel`, `tcLevel` | impostazioni degli aiuti |
| `dcBrakeBias` | `brakeBias` | diviso per 100 quando supera 1,5 (una percentuale su alcune auto) |
| `dcPitSpeedLimiterToggle` | `pitLimiter` | |
| `FuelLevel`, `WaterTemp`, `OilTemp` | `fuel`, `waterTemp`, `oilTemp` | |
| `LFtempCM` ... `RRtempCM` | `tireTemp.FL` ... `.RR` | temperatura della carcassa al centro |
| `..shockDefl` | `suspensionM.*` | |
| `..pressure` | `tirePressure.*` | kPa per 0,145038, in psi |
| `..wearM` | `tireWear.*` | `1 - valore` |

Ogni altro canale con un valore per campione (e non un singolo byte) viene passato con il proprio nome;
un prefisso di ruota (`LF`, `RF`, `LR`, `RR`) diventa un suffisso (`.FL`, `.FR`, `.RL`, `.RR`), così i
grafici del visualizzatore lo offrono senza che nessuno debba descriverlo.

L'auto viene da `DriverInfo`: la voce il cui `CarIdx` corrisponde a `DriverCarIdx` fornisce
`CarScreenName`, `CarID` e `CarClassShortName`. La pista è `TrackDisplayName` (oppure `TrackName`).

## Ciò che iRacing non fornisce {#what-iracing-does-not-give}

Non viene registrato nessuno slip degli pneumatici, quindi non ci sono canali di slip. L'angolo di
deriva viene ricavato dalla velocità di imbardata rispetto al percorso (vedi
[Slittamento, deriva e canali derivati](slip-and-drift.md)). I modelli delle piste sono distribuiti in un formato
protetto e non sono un obiettivo di estrazione dei file (vedi [Giochi](games.md)).
