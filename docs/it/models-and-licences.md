---
title: Modelli e licenze
nav_order: 7
lang: "it"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modelli e licenze {#models-and-licences}

Tutto ciò che è stato scritto per questo repository è sotto la **licenza MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Ciò che la MIT non
può coprire è ciò con cui girano i tool: i pacchetti che importano, i modelli che usa la
ricostruzione, e i giochi che leggono. La documentazione completa, con le fonti, è in
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); le sue
licenze sono state lette dai metadati dei pacchetti e dalle schede dei modelli a settembre 2026.
Dove i termini di un componente sono cambiati da allora, conta la fonte, non questa pagina. Niente
qui è consulenza legale.

## Il modello di profondità - quello che decide l'uso commerciale {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **non ha la stessa licenza in tutte le sue dimensioni**, e una ricostruzione
eredita la licenza del modello che l'ha prodotta:

| Modello | Licenza | Uso commerciale | Usato da |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **consentito** | il predefinito: il modello convertito dello scanner (`tools/export_onnx.py` lo usa come predefinito, e il pulsante "Set up the depth model" della finestra lo crea sempre), e la profondità del percorso offline (fusione); VGGT fornisce le sue pose |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | solo non commerciale | solo se lo converti tu (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | solo non commerciale | solo se lo converti tu (`--size large`) |

Base e Large danno una profondità migliore. Convertirli è consentito; questo rende non commerciale
quel file di modello, e ogni ricostruzione fatta con esso. È una decisione di chi lo usa, non un
valore predefinito da ereditare. Lo scanner sceglie tra i file `models/depth-*.onnx` **in base alla licenza, non
al nome**: `depth-small-*` quando ce n'è uno, poi Base, poi Large (`choose_model` in
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
La finestra indica il file che ha preso, la sua licenza, e gli altri file di modello trovati e non
usati; per scansionare con Base, sposta il file Small fuori da `models/`.

## VGGT - solo ricostruzione offline {#vggt---offline-reconstruction-only}

| Modello | Licenza | Disponibilità |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - solo non commerciale**; le ricostruzioni fatte con esso ereditano questa licenza | pubblico; il predefinito |
| `facebook/VGGT-1B-Commercial` | licenza separata; verifica i termini che ti sono stati concessi | con accesso limitato: l'accesso si richiede a Meta e viene concesso per account; senza, il download fallisce. Si sceglie con `reconstruct --model vggt-1b-commercial` |

VGGT è usato solo da `python -m heat3d_capture reconstruct`; lo scanner dal vivo non lo carica mai.
Il comando stampa la riga della licenza prima di partire. La ricostruzione da video è la parte di
questo progetto che un giocatore farebbe girare, e i termini non commerciali le si adattano; per il
lavoro commerciale la strada è un export dal motore o l'esportatore dei file di gioco, e sono
entrambi esatti comunque.

## Localizzare i fotogrammi - `locate` {#locating-frames---locate}

| Modello | Licenza | Ruolo |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | trova i render che mostrano lo stesso posto |
| ALIKED `aliked-n16` | BSD-3-Clause | punti chiave e descrittori |
| LightGlue (variante ALIKED) | Apache-2.0 | li abbina |

Tutti e tre consentono l'uso commerciale, e vengono scaricati al primo utilizzo. SuperPoint, il
partner abituale di LightGlue, non viene usato: i suoi pesi sono non commerciali. Vedi
[Localizzare i fotogrammi in un livello](locate.md).

## Pacchetti Python {#python-packages}

| Pacchetto | Licenza | Ruolo |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmetica, smoothing, marching cubes |
| opencv-python | Apache-2.0 | video, feature, flusso ottico |
| onnxruntime, onnxruntime-directml | MIT | inferenza della profondità |
| windows-capture | MIT | cattura dal vivo tramite Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | la finestra |
| pytest | MIT | solo sviluppo |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | conversione una tantum del modello; il percorso offline |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | il percorso offline (`requirements-offline.txt`) |
| vggt | "VGGT License" di Meta (accordo sui materiali di ricerca con una policy d'uso accettabile) | il percorso offline; installato da GitHub con `--no-deps` |
| moderngl, glcontext | MIT | `locate`: rendering offscreen del livello (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: punti chiave e matching |

**PySide6 ha delle condizioni.** La LGPL-3.0 consente l'uso proprietario e commerciale a patto che Qt
resti una libreria *sostituibile*. Qui viene usata come un normale import collegato dinamicamente,
il che lo soddisfa, e il suo avviso di licenza deve accompagnare ogni distribuzione. Impacchettare il
tool in un unico eseguibile dovrebbe mantenere Qt sostituibile.

La licenza del pacchetto `vggt` è stata letta dal suo `LICENSE.txt` ed è registrata in
`LICENSES.md`; copre il codice, separatamente dai pesi, che sono CC-BY-NC-4.0.

## I giochi {#the-games}

La telemetria viene solo dalle interfacce che i giochi pubblicano; i fotogrammi vengono dallo
schermo. Vedi [Le regole](rules.md). Ciò a cui un utente punta i tool resta soggetto alla licenza e
all'EULA di quel gioco, e quell'obbligo spetta a chi esegue il tool.
