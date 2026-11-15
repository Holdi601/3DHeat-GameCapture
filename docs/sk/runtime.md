---
title: "Runtime a závislosti"
nav_order: 8
lang: "sk"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, závislosti a výkon {#runtime-dependencies-and-performance}

Kód: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dvojklikom. Sám robí len dve veci:

1. **Nájde Python** (`python`, potom `py`). Ak ho niet, opýta sa
   `Install it now with winget [Y,N]?`; pri Y spustí
   `winget install -e --id Python.Python.3.12`, potom vás vyzve zavrieť okno a spustiť
   `scan.bat` znova, aby Windows zobral nový PATH. Pri N sa nič nenainštaluje.
2. **Vytvorí súkromné prostredie**, `.venv` vedľa `scan.bat`, ak neexistuje, a aktualizuje jeho pip –
   takže nič sa nedá do systémového Pythonu.

Potom spustí `.venv\Scripts\python.exe -m heat3d_capture.ui`. Všetko ostatné – zisťovanie, čo chýba,
vysvetľovanie, načo to je, pýtanie sa – sa deje v Pythone, ako dialóg.

## Kontrola pri prvom spustení {#first-run-preflight}

Predtým, než okno naimportuje čokoľvek ťažké, sa skontroluje každá požiadavka (cez
`importlib.util.find_spec`, takže polovične odstránený balík sa počíta ako chýbajúci). Pravidlá:

- **Najprv sa kontroluje všetko.** Úplný zoznam sa zozbiera skôr, než sa čokoľvek povie, takže oprava
  jedného balíka nevedie hneď na ďalšiu chybu.
- **Pýtať sa, nikdy nepredpokladať.** Dialóg vypíše každý chýbajúci balík, na čo je, a celkové
  stiahnutie, a nerobí nič bez **Download and install**. Cancel skončí: „Nothing was installed and
  nothing was changed.“
- **Ticho nie je súhlas.** Bez Qt sa kontrola vráti na konzolu a spýta sa `Install them now? [Y/n]`
  (Enter, `y`, `yes`, `j`, `ja` znamenajú áno); bez terminálu, kde odpovedať (koniec vstupu), nič
  nenainštaluje.
- **Do vlastného prostredia tohto nástroja.** Inštalácia je `<running python> -m pip install ...` ako
  podproces – so `scan.bat` súkromné `.venv`. Ak zlyhá, dialóg ukáže posledný riadok výstupu pipu a
  príkaz, ktorý treba vyskúšať ručne.

| Balík | Importuje sa ako | Zobrazený účel | Približné stiahnutie |
|---|---|---|---|
| numpy | `numpy` | aritmetika, na ktorej stoja všetky ostatné | 20 MB |
| opencv-python | `cv2` | čítanie video súborov a snímok z kamery | 40 MB |
| onnxruntime-directml na Windows, inak onnxruntime | `onnxruntime` | spúšťanie modelu hĺbky na grafickej karte | 120 MB |
| PySide6-Essentials | `PySide6` | okno a jeho ovládacie prvky | 90 MB |
| scipy | `scipy` | vyhladzovanie rekonštruovaného povrchu | 45 MB |
| scikit-image | `skimage` | premena meraní na 3D povrch | 30 MB |
| windows-capture | `windows_capture` | živé zachytávanie okna hry (voliteľné: bez neho stále fungujú video súbory) | 5 MB |

Prevod modelu hĺbky potrebuje tri ďalšie, pýtané osobitne a len keď stlačíte „Set up the depth model“:
`torch` (asi 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Samotný skener ich nikdy
neimportuje.

Offline príkaz `reconstruct` má vlastnú kontrolu, spustenú potom, čo vypíše riadok licencie, a len v
termináli: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`,
`Pillow`, a `vggt` z GitHub repozitára Meta (inštalované s `--no-deps`, lebo jeho metadáta pripínajú
numpy pod 2). Rovnaký zoznam je v `requirements-offline.txt`; pozrite
[Offline rekonštrukcia](reconstruction-offline.md#requirements).

Balík ONNX Runtime, ktorý sa ponúka, je ten, ktorý pre platformu vyberá `requirements.txt`:
`onnxruntime-directml` na Windows, `onnxruntime` inde. Ak je `onnxruntime` už importovateľný (napríklad
`onnxruntime-gpu`), nič sa neinštaluje: kontrola je podľa mena modulu.

## Inštalácia ručne {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` pripína: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(len Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` na Windows a `onnxruntime>=1.19` inde.

`requirements-offline.txt` pridáva to, čo potrebuje len `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` a `Pillow`, s riadkom inštalácie `vggt` (`--no-deps`) a poznámkou
o licencii VGGT v hlavičke. Ani PyTorch v ňom nie je, z dôvodu nižšie.

**PyTorch tu úmyselne chýba.** Správny wheel závisí od GPU a verzie CUDA; pripnutie jedného by na
strojoch, ktoré najviac potrebujú GPU verziu, nainštalovalo zostavu len pre CPU. Ak ho chcete (prevod
modelu, offline cesta `reconstruct`), nainštalujte ho **pred** `requirements.txt`: wheely torch sa
môžu usadiť na numpy 1.x, pri ktorom scipy odmietne bežať, a chyba sa ukáže ako
`module numpy has no attribute long` z vnútra scipy, ďaleko od príčiny.

`onnxruntime-directml` a `onnxruntime-gpu` sa vylučujú: nainštalujte len jeden.

Overil vývojár: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na NVIDIA RTX 5080, a rovnaké
prostredie bez balíka špecifického pre NVIDIA.

## Inferenčné backendy {#inference-backends}

ONNX Runtime sa dostane ku GPU cez poskytovateľov vykonávania, a ktorí existujú, závisí od toho, ako sa
onnxruntime nainštaloval, nie od hardvéru. Dostupnosť sa preto zisťuje, najlepší prvý:

| Poradie | Poskytovateľ | Zobrazený ako | Hardvér |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | ľubovoľná GPU s Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | čokoľvek |

**DirectML je predvolená inštalácia**, lebo dosiahne aj na AMD a Intel GPU, nielen na NVIDIA. NVIDIA je
rýchlejšia so svojimi poskytovateľmi – inštalácia `onnxruntime-gpu` pridá CUDA a okno to povie, keď na
DirectML uvidí kartu NVIDIA – ale NVIDIA nesmie byť jediná možnosť. CPU je vždy posledné, takže stroj
bez použiteľnej GPU dostane pomalý sken namiesto žiadneho, a pridáva sa ako záložné, keď sa vytvorí
relácia GPU.

Meno adaptéra sa číta z kľúča registra triedy zobrazovacích adaptérov Windows (nie z nástroja
výrobcu ako `nvidia-smi`, ktorý je len na niektorých strojoch), s preskočením Basic Render Driver.
Poskytovatelia viazaní na výrobcu pomenujú zodpovedajúci adaptér; DirectML sa zobrazuje na prvom
vymenovanom adaptéri, ktorý je predvoleným systémovým. Meno slúži len na zobrazenie.

`ScanSettings.prefer_backend` (len skripty) môže pomenovať poskytovateľa alebo krátke meno.

## Čo čakať na tomto stroji {#what-to-expect-from-this-machine}

Okno pri štarte zmeria skutočnú priepustnosť modelu hĺbky na tomto stroji (6 snímok po zahriatí),
namiesto aby hľadalo GPU v tabuľke – tepelný stav, režimy napájania notebookov a verzie ovládačov ju
hýbu príliš – a pred začatím povie, aký bude sken:

| Nameraných pohľadov za sekundu | Stupeň | Nadpis | Rada |
|---|---|---|---|
| 25 alebo viac | realtime | Živé skenovanie v plnom detaile. | Choďte normálnym tempom; prekrytie bude stíhať. |
| 12 až 25 | workable | Živé skenovanie, s menej zachovanými pohľadmi než pri plnej rýchlosti. | Choďte pomaly a zatáčajte jemne – rýchle otočky zanechajú medzery. Draft zachováva menej pohľadov, čo pomáha modelu hĺbky stíhať. |
| 2 až 12 | slow | Najprv nahrajte, potom rekonštruujte. | Nahrajte video prechádzky a rekonštruujte zo súboru. Výsledok je rovnaký; len spätná väzba nie je živá. |
| pod 2 | impractical | Tento stroj je príliš pomalý na použiteľné skenovanie. | Kratšia trasa alebo menší model. **Štart je vypnutý.** |

Na CPU poznámka dodá, že inštalácia `onnxruntime-directml` to na Windows zvyčajne opraví. Nič
nemení rozlíšenie zachytenia samo osebe: nepomohlo by to, lebo model hĺbky beží na svojej pevnej
vstupnej veľkosti bez ohľadu na to, čo dostane; čo drží pomalší stroj v chode, je zachovávanie menej
pohľadov, čo robí Draft.

### Namerané vývojárom {#measured-by-the-developer}

Ten istý súbor ONNX, ten istý výstup, RTX 5080:

| Backend | Priepustnosť hĺbky |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Testovací záznam cez dodávanú cestu ONNX:

| Predvoľba | Zachované pohľady | Priepustnosť hĺbky |
|---|---|---|
| Draft | asi 1 z 7 | asi 50 /s |
| Balanced | asi 1 zo 4 | asi 50 /s |
| Detailed | asi 1 z 2 | asi 40 /s |

Hĺbka je pohodlne rýchlejšia než zachytávanie, takže živé skenovanie nie je viazané hĺbkou. Prostredie
aplikácie má asi 349 MiB bez PyTorch, oproti zhruba 3,5 GB pre torch s CUDA.

Offline cesta `reconstruct` je iná: minúty na 16-snímkové okno na stolovom GPU.

## Pamäť {#memory}

- Snímky sa po fúzii neuchovávajú, okrem **160** na sfarbenie siete.
- Sken sa predvolene zastaví pri **3000** zachovaných pohľadoch („Views kept“), ako ochrana.
- Živý front zachytávania drží 4 snímky; buffer polôh z telemetrie 30 sekúnd.
- Obidve mriežky voxelov sú riedke a sieť sa extrahuje po blokoch, takže pamäť sleduje to, čo bolo
  naskenované, nie ohraničujúci box.

## Platforma {#platform}

Skener a rekordéry Assetto Corsa sú v praxi len pre Windows: živé zachytávanie používa Windows Graphics
Capture, klávesové skratky a prekrytie priehľadné pre kliknutie používajú Win32 API a stránky Kunos sú
zdieľaná pamäť Windows. Video súbory sa dajú skenovať a UDP rekordéry bežia aj inde, ale to nebolo
overené.
