---
title: L'output .glb
nav_order: 6
lang: "it"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# L'output .glb {#the-glb-output}

Una ricostruzione viene scritta come file glTF 2.0 binario (`.glb`) che il visualizzatore di 3DHeat carica
dal suo pannello Sfondo / livello senza nessun trattamento speciale - lo stesso contratto che scrive
l'esportatore per Unreal. Codice: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

È scritto a mano invece che con una libreria glTF: l'output è un sottoinsieme ristretto (un solo
buffer, compattato, senza animazioni né skinning), e una dipendenza capace di scrivere tutto glTF
porterebbe con sé i propri problemi di versione per poche centinaia di righe.

## Cosa contiene il file di una scansione {#what-is-in-a-scans-file}

| Parte (nome del nodo e della mesh) | Contenuto |
|---|---|
| `ground:<name>` | triangoli entro 35 gradi dalla direzione verso l'alto |
| `structure:<name>` | tutto il resto |

`<name>` è il nome del file senza estensione quando si salva dalla finestra, oppure il nome del
video per `reconstruct`. Una parte senza triangoli viene omessa. Una scansione non scrive mai una
parte `water:`. `asset.generator` vale `heat3d-capture-scan`.

## Il contratto {#the-contract}

- **Un nodo per parte**, chiamato con l'etichetta della parte; la mesh ripete il nome. Il visualizzatore
  legge prima il nome del *nodo*, quindi dare il nome solo alle mesh farebbe perdere la
  classificazione.
- L'etichetta è `<class>:<name>` con classe `ground`, `structure` o `water` - il prefisso che il
  visualizzatore riconosce (`^(ground|structure|water)\s*[:|]`) per prendere la classe così com'è, senza
  indovinarla dalla geometria. Il terreno viene disegnato pieno, le strutture quasi trasparenti.
- **Le coordinate sono nello spazio del visualizzatore**: Y verso l'alto, sistema destrorso, e **scalate in
  centimetri** (metri x 100) per corrispondere all'esportatore per Unreal, così una cattura e un
  export dal motore dello stesso posto si caricano alla stessa dimensione con la stessa
  inquadratura predefinita. Il campo `extras.unit_metres` al primo livello del file vale `0.01`
  (un'unità è un centimetro), così un lettore che lavora in metri, come [`locate`](locate.md), lo
  prende alla sua dimensione reale. Una scansione collocata dalla telemetria di Forza fa eccezione
  quanto al sistema di coordinate: resta nel mondo del gioco, Y verso l'alto e sistema sinistrorso,
  esattamente come i file di giro, così i giri registrati sopra di essa vi cadono sopra. Quando la
  scala di una scansione è stata trovata su un fotogramma chiave successivo
  ([Scala](reconstruction-pose.md#scale)), quel fattore viene incluso nella scala scritta.
- `COLOR_0` viene letto dal visualizzatore, che colora il terreno con esso quando nel pannello Sfondo /
  livello è attivo l'interruttore *Colore acquisito* (disattivato per impostazione predefinita).
- Una scansione con punti segnati a mano riceve accanto un file `<name>.marks.json`; vedi
  [Salvataggio](reconstruction-scan-ui.md#saving).
- Per primitiva: `POSITION` (VEC3 float, con `min` e `max`, da cui il visualizzatore inquadra la camera),
  `NORMAL` (VEC3 float), `COLOR_0` opzionale (VEC3 float, 0..1), `TEXCOORD_0` opzionale; gli indici
  sono a 16 bit quando ogni indice è sotto 65.536, altrimenti a 32 bit; modalità triangles.
- Ogni buffer view inizia allineato a 4 byte; il blocco JSON è riempito con spazi e il blocco BIN
  con zeri fino a 4 byte.

## Controlli prima di scrivere {#checks-before-writing}

Ogni parte viene validata e rifiutata con un messaggio che ne indica il nome se non ha vertici, se
il numero di indici non forma triangoli interi, se un indice è fuori intervallo o negativo, se ci
sono posizioni non finite, o se normali o colori non corrispondono al numero di vertici. Le normali
mancanti vengono calcolate **pesate per area** (il marching cubes lascia schegge accanto alle facce
grandi, e una media non pesata lascerebbe che i triangoli minuscoli prevalgano sulla faccia su cui
stanno); un vertice degenere riceve "in alto". Non scrivere nessuna parte è un errore.

L'export non restituisce nulla - e la finestra mostra "Nothing to save" - quando il volume non dà
alcuna superficie, invece di scrivere un file vuoto che sembrerebbe una scansione riuscita.

## Texture {#textures}

Il writer supporta una texture PNG del colore di base per parte (con UV, a doppia faccia, materiale
non metallico e completamente ruvido). Le scansioni non la usano: portano il colore per vertice.
Vedi [colore](reconstruction-fusion-and-texture.md#colour).

## Il livello di riferimento {#the-reference-level}

`geometry/reference.py` costruisce un livello sintetico di dimensione esattamente nota attraverso lo
stesso writer: un terreno di 400 m suddiviso, tre edifici di 20 x 20 x 12 m e uno stagno di 50 m
sotto il livello del terreno di 1,5 m, ogni classe con un colore piatto diverso. I test del visualizzatore
lo generano e lo leggono con il vero parser del visualizzatore, così il formato del file resta sotto test
da entrambi i lati, senza gioco né hardware di cattura.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
