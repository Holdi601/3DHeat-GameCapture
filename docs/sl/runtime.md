---
title: "Izvajanje in odvisnosti"
nav_order: 8
lang: "sl"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Izvajanje, odvisnosti in zmogljivost {#runtime-dependencies-and-performance}

Koda: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py), [`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py), [`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat), [`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dvakrat kliknite nanj. Sam naredi samo dve stvari:

1. **Poišče Python** (`python`, nato `py`). Če ga ni, vpraša `Install it now with winget [Y,N]?`; na Y zažene `winget install -e --id Python.Python.3.12`, nato vas prosi, da zaprete okno in zaženete `scan.bat` znova, da Windows prevzame nov PATH. Na N se ne namesti nič.
2. **Ustvari zasebno okolje**, `.venv` poleg `scan.bat`, če ga ni, in posodobi njegov pip – tako se nič ne namesti v sistemski Python.

Nato zažene `.venv\Scripts\python.exe -m heat3d_capture.ui`. Vse ostalo – ugotavljanje, kaj manjka, razlaga, zakaj, in vprašanja – se zgodi v Pythonu, kot okno.

## Preverjanje ob prvem zagonu {#first-run-preflight}

Preden okno uvozi kaj težkega, se preveri vsaka zahteva (z `importlib.util.find_spec`, da se napol odstranjen paket šteje kot manjkajoč). Pravila:

- **Vse se preveri najprej.** Celoten seznam se zbere, preden se karkoli pove, da popravilo enega paketa ne pripelje takoj do naslednje napake.
- **Vprašajte, ne predpostavljajte.** Pogovorno okno našteje vsak manjkajoč paket, čemu je namenjen, in skupni prenos, ter ne naredi ničesar brez **Download and install**. Preklic konča: "Nothing was installed and nothing was changed."
- **Molk ni privolitev.** Brez Qt preverjanje preide na konzolo in vpraša `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` pomenijo da); brez terminala, kjer bi lahko odgovorili (konec vnosa), ne namesti ničesar.
- **V lastno okolje tega orodja.** Namestitev je `<running python> -m pip install ...` kot podproces – s `scan.bat` v zasebnem `.venv`. Če ne uspe, pogovorno okno pokaže zadnjo vrstico pipovega izpisa in ukaz, ki ga poskusite ročno.

| Paket | Uvoženo kot | Prikazano kot namen | Približen prenos |
|---|---|---|---|
| numpy | `numpy` | aritmetika, na kateri stoji vse ostalo | 20 MB |
| opencv-python | `cv2` | branje video datotek in okvirjev kamere | 40 MB |
| onnxruntime-directml na Windows, sicer onnxruntime | `onnxruntime` | zagon modela globine na grafični kartici | 120 MB |
| PySide6-Essentials | `PySide6` | okno in njegovi gumbi | 90 MB |
| scipy | `scipy` | glajenje rekonstruirane površine | 45 MB |
| scikit-image | `skimage` | pretvorba meritev v 3D površino | 30 MB |
| windows-capture | `windows_capture` | živi zajem okna igre (neobvezno: brez njega video datoteke še vedno delujejo) | 5 MB |

Pretvorba modela globine potrebuje še tri, ki se zahtevajo ločeno in samo ob pritisku na "Set up the depth model": `torch` (okoli 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Sam skener jih nikoli ne uvozi.

Offline ukaz `reconstruct` ima svoje preverjanje, ki teče za izpisom licenčne vrstice in samo v terminalu: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow` in `vggt` z GitHuba Metinega repozitorija (nameščen z `--no-deps`, ker njegovi metapodatki zahtevajo numpy pod 2). Isti seznam je v `requirements-offline.txt`; glejte [Rekonstrukcija brez povezave](reconstruction-offline.md#requirements).

Paket ONNX Runtime, ki se ponudi, je tisti, ki ga `requirements.txt` izbere za platformo: `onnxruntime-directml` na Windows, `onnxruntime` drugod. Če je `onnxruntime` že mogoče uvoziti (na primer `onnxruntime-gpu`), se ne namesti nič: preverjanje je po imenu modula.

## Ročna namestitev {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` zahteva: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (samo Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` na Windows in `onnxruntime>=1.19` drugod.

`requirements-offline.txt` doda, kar potrebuje samo `reconstruct`: `transformers`, `einops`, `safetensors`, `huggingface_hub` in `Pillow`, z ukazom za namestitev `vggt` (`--no-deps`) in opombo o licenci VGGT v glavi datoteke. PyTorch tudi v njej ni, iz razloga spodaj.

**PyTorch je namerno odsoten.** Pravi paket je odvisen od grafične kartice in različice CUDA; če bi ga pripeli, bi se na računalnikih, ki najbolj potrebujejo GPU različico, namestil CPU. Če ga želite (pretvorba modela, offline pot `reconstruct`), ga namestite **pred** `requirements.txt`: paketi torch lahko vzamejo numpy 1.x, scipy pa z njim ne deluje, napaka pa se pokaže kot `module numpy has no attribute long` znotraj scipyja, daleč od vzroka.

`onnxruntime-directml` in `onnxruntime-gpu` si nasprotujeta: namestite samo enega.

Razvijalec je preveril: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na NVIDIA RTX 5080, in isto okolje brez paketa, specifičnega za NVIDIA.

## Izvajalniki za sklepanje {#inference-backends}

ONNX Runtime doseže grafične kartice prek izvajalnih ponudnikov (execution providers), a kateri obstajajo, je odvisno od tega, kako je bil onnxruntime nameščen, ne od strojne opreme. Zato se odkrijejo, najboljši prvi:

| Rang | Ponudnik | Prikazano kot | Strojna oprema |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | katera koli grafična kartica Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | karkoli |

**DirectML je privzeta namestitev**, ker doseže tudi grafične kartice AMD in Intel, ne samo NVIDIA. NVIDIA je z lastnimi ponudniki hitrejša – namestitev `onnxruntime-gpu` doda CUDA, okno pa to pove, kadar vidi karto NVIDIA na DirectML – vendar NVIDIA ne sme biti edina možnost. CPU je vedno zadnji, zato računalnik brez uporabne grafične kartice dobi počasen zajem, ne pa nobenega, in se doda kot rezerva, kadar se seja z GPU ustvari.

Ime adapterja se prebere iz registrskega ključa razreda prikazovalnih adapterjev v Windows (ne iz orodja proizvajalca, kot je `nvidia-smi`, ki je na nekaterih računalnikih sploh ni), pri čemer se preskoči Basic Render Driver. Ponudniki, vezani na proizvajalca, imenujejo ustrezen adapter; DirectML se prikaže na prvem naštetem adapterju, ki je privzeti sistemski. Ime je samo za prikaz.

`ScanSettings.prefer_backend` (samo za skripte) lahko imenuje ponudnika ali kratko ime.

## Kaj pričakovati na tem računalniku {#what-to-expect-from-this-machine}

Okno ob zagonu izmeri dejansko prepustnost modela globine na tem računalniku (6 okvirov po ogrevanju), namesto da bi grafično kartico poiskalo v tabeli – toplotno stanje, profili porabe v prenosnikih in različice gonilnikov premikajo rezultat preveč – in pove, kakšen bo zajem, preden se karkoli lahko začne:

| Izmerjeni pogledi na sekundo | Stopnja | Naslov | Nasvet |
|---|---|---|---|
| 25 ali več | v realnem času | Živo skeniranje v polni podrobnosti. | Hodite s normalno hitrostjo; pregled bo sledil. |
| 12 do 25 | sprejemljivo | Živo skeniranje, z manj ohranjenimi pogledi kot pri polni hitrosti. | Hodite počasi in zavijajte nežno – hitri zavoji bodo pustili luknje. Draft ohrani manj pogledov, kar pomaga modelu globine slediti. |
| 2 do 12 | počasno | Najprej posnemite, nato rekonstruirajte. | Posnemite video sprehoda in rekonstruirajte iz datoteke pozneje. Rezultat je isti; povratna informacija ni živa. |
| pod 2 | nepraktično | Ta računalnik je prepočasen za koristno skeniranje. | Krajša pot ali manjši model. **Zagon je onemogočen.** |

Na CPU opomba doda, da namestitev `onnxruntime-directml` na Windows ponavadi to popravi. Nič ne spremeni ločljivosti zajema samo po sebi: to ne bi pomagalo, ker model globine teče na svoji fiksni vhodni velikosti, ne glede na to, kar dobi; kar počasnejši računalnik drži v koraku, je manj ohranjenih pogledov, kar naredi Draft.

### Izmerjeno razvijalca {#measured-by-the-developer}

Isti ONNX model, isti izpis, RTX 5080:

| Izvajalnik | Prepustnost globine |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Testni posnetek skozi dobavljeno pot ONNX:

| Prednastavitev | Ohranjeni pogledi | Prepustnost globine |
|---|---|---|
| Draft | okoli 1 od 7 | okoli 50 /s |
| Balanced | okoli 1 od 4 | okoli 50 /s |
| Detailed | okoli 1 od 2 | okoli 40 /s |

Globina je dovolj hitra glede na zajem, zato živo skeniranje ni omejeno z globino. Okolje aplikacije je okoli 349 MiB brez PyTorcha, v primerjavi z okoli 3,5 GB za torch s CUDA.

Offline pot `reconstruct` je drugačna: minute na 16-okvirno okno na namiznem GPU.

## Pomnilnik {#memory}

- Okvirji se po združitvi ne hranijo, razen **160** za barvanje mreže.
- Skeniranje se privzeto ustavi pri **3000** ohranjenih pogledih ("Views kept"), kot zaščita.
- Medpomnilnik zajema ima 4 okvirje; medpomnilnik položajev telemetrije 30 sekund.
- Obe mreži voksrov sta redki, mreža pa se izvleče blok za blokom, zato pomnilnik sledi temu, kar je bilo skenirano, ne okvirju.

## Platforma {#platform}

Skener in snemalniki Assetto Corsa delujejo praktično samo v Windows: živi zajem uporablja Windows Graphics Capture, bližnjice in prosojni prekrivni sloj pa Win32 API, strani Kunos pa so deljeni pomnilnik Windows. Video datoteke se lahko skenirajo in snemalniki UDP delujejo tudi drugje, vendar tega ni preverjeno.
