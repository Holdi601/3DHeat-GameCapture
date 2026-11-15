---
title: "Pokretanje, ovisnosti i performanse"
nav_order: 8
lang: "hr"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Pokretanje, ovisnosti i performanse {#runtime-dependencies-and-performance}

Kod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dvaput kliknite na njega. Sam radi samo dvije stvari:

1. **Traži Python** (`python`, zatim `py`). Ako ga nema, pita
   `Install it now with winget [Y,N]?`; na Y pokreće
   `winget install -e --id Python.Python.3.12`, zatim traži da zatvorite prozor i ponovno
   pokrenete `scan.bat` kako bi Windows pokupio novi PATH. Na N ništa se ne instalira.
2. **Izrađuje privatno okruženje**, `.venv` pokraj `scan.bat`, ako ga nema, i nadograđuje
   njegov pip - pa se ništa ne instalira u sistemski Python.

Zatim pokreće `.venv\Scripts\python.exe -m heat3d_capture.ui`. Sve ostalo - utvrđivanje što
nedostaje, objašnjavanje čemu služi, pitanje - događa se u Pythonu, kao prozor s dijalogom.

## Provjera prije prvog pokretanja {#first-run-preflight}

Prije nego što prozor išta teško uveze, provjerava se svaki zahtjev (s
`importlib.util.find_spec`, pa se paket koji je napola uklonjen računa kao nedostajući). Pravila:

- **Sve se provjerava prvo.** Puni popis se skuplja prije nego što se išta kaže, pa popravak
  jednog paketa ne vodi odmah u sljedeću grešku.
- **Pitati, nikad pretpostaviti.** Dijalog navodi svaki nedostajući paket, čemu služi i ukupno
  preuzimanje, i ne radi ništa bez **Download and install**. Odustajanje izlazi:
  „Nothing was installed and nothing was changed.”
- **Šutnja nije pristanak.** Bez Qt-a provjera se vraća na konzolu i pita
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znače da); bez terminala za odgovor
  (kraj ulaza), ništa se ne instalira.
- **U okruženje ovog alata.** Instalacija je `<pokrenuti python> -m pip install ...` kao
  podproces - uz `scan.bat`, privatni `.venv`. Ako ne uspije, dijalog prikazuje zadnji redak
  pipova ispis i naredbu koju treba pokušati ručno.

| Paket | Uvozi se kao | Prikazano kao čemu služi | Otprilike preuzimanje |
|---|---|---|---|
| numpy | `numpy` | aritmetika na kojoj je sve ostalo izgrađeno | 20 MB |
| opencv-python | `cv2` | čitanje video datoteka i kadrova kamere | 40 MB |
| onnxruntime-directml na Windowsu, inače onnxruntime | `onnxruntime` | pokretanje modela dubine na vašoj grafičkoj kartici | 120 MB |
| PySide6-Essentials | `PySide6` | prozor i njegove kontrole | 90 MB |
| scipy | `scipy` | izglađivanje rekonstruirane površine | 45 MB |
| scikit-image | `skimage` | pretvaranje mjerenja u 3D površinu | 30 MB |
| windows-capture | `windows_capture` | uživo snimanje prozora igre (neobavezno: bez njega video datoteke i dalje rade) | 5 MB |

Pretvaranje modela dubine traži tri dodatna, traže se zasebno i samo kad pritisnete „Set up
the depth model”: `torch` (oko 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Skener
sam ih nikad ne uvozi.

Naredba `reconstruct` izvanmrežno ima vlastitu provjeru, pokrenutu nakon ispisa retka o licenci
i samo u terminalu: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, i `vggt` iz Metinog GitHub repozitorija (instaliran s `--no-deps`,
jer njegovi metapodaci fiksiraju numpy ispod 2). Isti popis je u `requirements-offline.txt`;
vidi [Izvanmrežna rekonstrukcija](reconstruction-offline.md#requirements).

Paket ONNX Runtime koji se nudi je onaj koji `requirements.txt` bira za platformu:
`onnxruntime-directml` na Windowsu, `onnxruntime` drugdje. Ako je `onnxruntime` već moguće
uvesti (na primjer `onnxruntime-gpu`), ništa se ne instalira: provjera je po imenu modula.

## Ručna instalacija {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` fiksira: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(samo Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` na Windowsu i `onnxruntime>=1.19` drugdje.

`requirements-offline.txt` dodaje ono što treba samo `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` i `Pillow`, s redom za instalaciju `vggt` (`--no-deps`) i
napomenom o licenci VGGT-a u zaglavlju. Ni PyTorch nije u njemu, iz razloga u nastavku.

**PyTorch je namjerno izostavljen.** Ispravan wheel ovisi o GPU-u i verziji CUDA-e, a
fiksiranje jednog bi na strojevima kojima je GPU najpotrebniji instaliralo CPU verziju. Ako ga
želite (pretvaranje modela, izvanmrežni put `reconstruct`), instalirajte ga **prije**
`requirements.txt`: torch wheelovi mogu povući numpy 1.x, s kojim scipy odbija raditi, a greška
se pokaže kao `module numpy has no attribute long` iz same scipy, daleko od uzroka.

`onnxruntime-directml` i `onnxruntime-gpu` se sukobljavaju: instalirajte samo jedan.

Razvojni programer provjerio je: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na
NVIDIA RTX 5080, i isto okruženje bez NVIDIA-specifičnog paketa.

## Pozadine zaključivanja {#inference-backends}

ONNX Runtime do GPU-a dolazi preko pružatelja izvršavanja, a koji postoje ovisi o tome kako je
onnxruntime instaliran, a ne o hardveru. Zato se dostupnost otkriva, od najbolje prema najlošijoj:

| Rang | Pružatelj | Prikazano kao | Hardver |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | svaka Direct3D 12 GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | bilo što |

**DirectML je zadana instalacija** jer dopire i do AMD-ovih i Intelovih GPU-a, uz NVIDIA-ine.
NVIDIA je brža uz vlastite pružatelje - instalacija `onnxruntime-gpu` dodaje CUDA-u, a prozor
to kaže kad vidi NVIDIA karticu na DirectML-u - ali NVIDIA ne smije biti jedina opcija. CPU je
uvijek zadnji, pa stroj bez upotrebljive GPU-e dobiva spor sken, a ne nikakav, i dodaje se kao
rezerva kad se stvara GPU sesija.

Naziv adaptera čita se iz Windows ključa klase display adaptera u registru (ne iz alata
proizvođača kao `nvidia-smi`, koji postoji samo na nekim strojevima), preskačući Basic Render
Driver. Pružatelji vezani uz proizvođača imenuju odgovarajući adapter; DirectML se prikazuje na
prvom nabrojanom adapteru, što je zadani sustava. Naziv je samo za prikaz.

`ScanSettings.prefer_backend` (samo za skripte) može imenovati pružatelja ili kratki naziv.

## Što očekivati na ovom računalu {#what-to-expect-from-this-machine}

Prozor mjeri stvarnu propusnost modela dubine na ovom računalu pri pokretanju (6 kadrova
nakon zagrijavanja), umjesto da gleda GPU u tablici - toplinsko stanje, profili napajanja na
prijenosnicima i verzije upravljačkih programa previše je pomiču - i kaže kakvo će skeniranje
biti prije nego što išta može započeti:

| Izmjerenih pogleda u sekundi | Razred | Naslov | Savjet |
|---|---|---|---|
| 25 ili više | u stvarnom vremenu | Skeniranje uživo punom detaljnošću. | Hodajte normalnim tempom; prekrivanje će stizati. |
| 12 do 25 | upotrebljivo | Skeniranje uživo, s manje zadržanih pogleda nego punom brzinom. | Hodajte sporo i okrećite se nježno - brzi zaokreti ostavit će rupe. Draft zadržava manje pogleda, što pomaže modelu dubine da stigne. |
| 2 do 12 | sporo | Prvo snimite, zatim rekonstruirajte. | Snimite video šetnje i rekonstruirajte iz datoteke poslije. Rezultat je isti; samo povratna informacija nije uživo. |
| ispod 2 | nepraktično | Ovo računalo je prespora za korisno skeniranje. | Kraća ruta ili manji model. **Početak je onemogućen.** |

Na CPU-u napomena dodaje da instalacija `onnxruntime-directml` obično to popravlja na Windowsu.
Ništa ne mijenja razlučivost snimanja sama po sebi: ne bi pomogla, jer model dubine radi na
svojoj fiksnoj ulaznoj veličini bez obzira na to što mu se preda; ono što sporijem stroju
održava korak je zadržavanje manje pogleda, što čini Draft.

### Izmjereno kod razvojnog programera {#measured-by-the-developer}

Isti ONNX datoteka, isti rezultat, RTX 5080:

| Pozadina | Propusnost dubine |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Testni isječak kroz isporučeni ONNX put:

| Postavka | Zadržani pogledi | Propusnost dubine |
|---|---|---|
| Draft | otprilike 1 od 7 | otprilike 50 /s |
| Balanced | otprilike 1 od 4 | otprilike 50 /s |
| Detailed | otprilike 1 od 2 | otprilike 40 /s |

Dubina je dovoljno brža od snimanja, pa živo skeniranje nije ograničeno dubinom. Okruženje
aplikacije je oko 349 MiB bez PyTorcha, naspram otprilike 3,5 GB za torch s CUDA-om.

Izvanmrežni put `reconstruct` je drukčiji: minute po prozoru od 16 kadrova na stolnoj GPU-i.

## Memorija {#memory}

- Kadrovi se ne čuvaju nakon spajanja, osim **160** za bojanje mreže.
- Skeniranje staje na **3000** zadržanih pogleda prema zadanom ("Views kept"), kao zaštita.
- Red živog snimanja drži 4 kadra; međuspremnik položaja telemetrije 30 sekundi.
- Obje voksel mreže su rijetke, a mreža se izvlači blok po blok, pa memorija prati ono što je
  skenirano, a ne okvir.

## Platforma {#platform}

Skener i Assetto Corsa snimači su u praksi samo za Windows: uživo snimanje koristi Windows
Graphics Capture, prečaci i prozirno prekrivanje koriste Win32 API, a stranice Kunos su
Windows dijeljena memorija. Video datoteke se mogu skenirati, a UDP snimači rade i drugdje, ali
to nije provjereno.
