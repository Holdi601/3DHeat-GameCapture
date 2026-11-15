---
title: "Runtime i zavisnosti"
nav_order: 8
lang: "bs"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Runtime, zavisnosti i performanse {#runtime-dependencies-and-performance}

Kod: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dvaput kliknite na njega. Sam radi samo dvije stvari:

1. **Pronalazi Python** (`python`, zatim `py`). Ako ga nema, pita
   `Install it now with winget [Y,N]?`; na Y pokreće
   `winget install -e --id Python.Python.3.12`, a zatim traži da zatvorite prozor i ponovo pokrenete
   `scan.bat` da Windows preuzme novi PATH. Na N se ništa ne instalira.
2. **Pravi privatno okruženje**, `.venv` pored `scan.bat`, ako ga nema, i nadograđuje
   njegov pip - tako da se ništa ne instalira u sistemski Python.

Zatim pokreće `.venv\Scripts\python.exe -m heat3d_capture.ui`. Sve ostalo - utvrđivanje šta
nedostaje, objašnjenje čemu služi, pitanje - dešava se u Pythonu, kao dijalog.

## Provjera pri prvom pokretanju {#first-run-preflight}

Prije nego što prozor uveze bilo šta teško, provjerava se svaki zahtjev (pomoću
`importlib.util.find_spec`, pa se napola uklonjen paket računa kao nedostajući). Pravila:

- **Prvo se provjerava sve.** Cijeli spisak se prikupi prije nego što se išta kaže, pa popravak
  jednog paketa nikad ne vodi direktno u sljedeću grešku.
- **Pitajte, nikad ne pretpostavljajte.** Dijalog navodi svaki nedostajući paket, čemu služi i ukupno
  preuzimanje, i ne radi ništa bez **Download and install**. Cancel izlazi: "Nothing was
  installed and nothing was changed."
- **Šutnja nije pristanak.** Bez Qt-a provjera se vraća na konzolu i pita
  `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` znače da); bez terminala za odgovor
  (kraj ulaza), ne instalira ništa.
- **U vlastito okruženje ovog alata.** Instalacija je `<running python> -m pip install ...` kao
  podproces - uz `scan.bat`, privatni `.venv`. Ako ne uspije, dijalog prikazuje posljednju liniju
  pipovog izlaza i komandu koju treba probati ručno.

| Paket | Uvozi se kao | Prikazano kao čemu služi | Okvirno preuzimanje |
|---|---|---|---|
| numpy | `numpy` | aritmetika na kojoj je sve ostalo izgrađeno | 20 MB |
| opencv-python | `cv2` | čitanje video datoteka i kadrova kamere | 40 MB |
| onnxruntime-directml na Windowsu, onnxruntime drugdje | `onnxruntime` | pokretanje modela dubine na vašoj grafičkoj kartici | 120 MB |
| PySide6-Essentials | `PySide6` | prozor i njegove kontrole | 90 MB |
| scipy | `scipy` | zaglađivanje rekonstruisane površine | 45 MB |
| scikit-image | `skimage` | pretvaranje mjerenja u 3D površinu | 30 MB |
| windows-capture | `windows_capture` | snimanje prozora igre uživo (opcionalno: bez njega video datoteke i dalje rade) | 5 MB |

Pretvaranje modela dubine treba još tri, tražena zasebno i samo kada pritisnete "Set up
the depth model": `torch` (oko 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). Sam skener
ih nikad ne uvozi.

Offline komanda `reconstruct` ima vlastitu provjeru, koja se pokreće nakon ispisa linije o licenci
i samo u terminalu: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`,
`huggingface_hub`, `Pillow`, i `vggt` iz Metinog GitHub repozitorija (instalira se s `--no-deps`,
jer njegovi metapodaci propisuju numpy ispod 2). Isti spisak je `requirements-offline.txt`; pogledajte
[Offline rekonstrukcija](reconstruction-offline.md#requirements).

Ponuđeni ONNX Runtime paket je onaj koji `requirements.txt` bira za platformu:
`onnxruntime-directml` na Windowsu, `onnxruntime` drugdje. Ako se `onnxruntime` već može
uvesti (na primjer `onnxruntime-gpu`), ništa se ne instalira: provjera je po imenu modula.

## Ručna instalacija {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

`requirements.txt` propisuje: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4`
(samo Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`,
`onnxruntime-directml>=1.19` na Windowsu i `onnxruntime>=1.19` drugdje.

`requirements-offline.txt` dodaje ono što treba samo `reconstruct`: `transformers`, `einops`,
`safetensors`, `huggingface_hub` i `Pillow`, s linijom za instalaciju `vggt` (`--no-deps`) i
napomenom o VGGT licenci u zaglavlju. ni PyTorch nije u njemu, iz razloga ispod.

**PyTorch je namjerno izostavljen.** Ispravan wheel zavisi od GPU-a i verzije CUDA-e, a propisivanje
jednog instaliralo bi CPU verziju na mašinama kojima najviše treba GPU verzija. Ako ga želite (konverzija
modela, offline putanja `reconstruct`), instalirajte ga **prije** `requirements.txt`: torch
wheelovi se mogu smjestiti na numpy 1.x, protiv kojeg scipy onda odbija raditi, a greška se pojavi kao
`module numpy has no attribute long` iznutra iz scipyja, daleko od uzroka.

`onnxruntime-directml` i `onnxruntime-gpu` su u sukobu: instalirajte samo jedan.

Provjereno od strane programera: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, na NVIDIA
RTX 5080, i isto okruženje bez ijednog paketa specifičnog za NVIDIA.

## Pozadine zaključivanja {#inference-backends}

ONNX Runtime dolazi do GPU-ova preko izvršnih pružatelja, a koji postoje zavisi od toga kako je
onnxruntime instaliran, ne od hardvera. Zato se dostupnost otkriva, najbolji prvi:

| Rang | Pružatelj | Prikazano kao | Hardver |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | bilo koji Direct3D 12 GPU: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | bilo šta |

**DirectML je zadana instalacija** jer dopire do AMD i Intel GPU-ova kao i NVIDIA.
NVIDIA je brža s vlastitim pružateljima - instalacija `onnxruntime-gpu` dodaje CUDA-u, a prozor
to kaže kad vidi NVIDIA karticu na DirectML-u - ali NVIDIA ne smije biti jedina
opcija. CPU je uvijek posljednji, pa mašina bez upotrebljivog GPU-a dobija sporo skeniranje, a ne nikakvo, i
dodaje se kao rezerva kad se kreira GPU sesija.

Ime adaptera čita se iz ključa klase adaptera ekrana u registru Windowsa (a ne iz
alata proizvođača kao `nvidia-smi`, koji postoji samo na nekim mašinama), preskačući Basic Render
Driver. Pružatelji vezani za proizvođača imenuju odgovarajući adapter; DirectML se prikazuje na prvom
nabrojanom adapteru, koji je zadani sistemski. Ime je samo za prikaz.

`ScanSettings.prefer_backend` (samo skripte) može imenovati pružatelja ili kratko ime.

## Šta očekivati od ove mašine {#what-to-expect-from-this-machine}

Prozor pri pokretanju mjeri stvarnu propusnost modela dubine na ovoj mašini (6 kadrova nakon
zagrijavanja) umjesto da traži GPU u tabeli - termičko stanje, profili napajanja laptopa i
verzije drajvera previše je pomjeraju - i navodi kakvo će biti skeniranje prije nego išta može početi:

| Izmjereno pogleda u sekundi | Nivo | Naslov | Savjet |
|---|---|---|---|
| 25 ili više | realtime | Live scanning at full detail. | Walk at a normal pace; the overlay will keep up. |
| 12 do 25 | workable | Live scanning, with fewer views kept than at full speed. | Walk slowly and turn gently — fast turns will leave gaps. Draft keeps fewer views, which helps the depth model keep up. |
| 2 do 12 | slow | Record first, reconstruct afterwards. | Record a video of the walk and reconstruct from the file afterwards. The result is identical; only the feedback is not live. |
| ispod 2 | impractical | This machine is too slow to scan usefully. | A shorter route, or a smaller model. **Start is disabled.** |

Na CPU-u napomena dodaje da instalacija `onnxruntime-directml` obično to rješava na Windowsu. Ništa
samo od sebe ne mijenja rezoluciju snimanja: ne bi pomoglo, jer model dubine radi na svojoj
fiksnoj ulaznoj veličini šta god mu se preda; ono što drži sporiju mašinu u koraku je zadržavanje manje pogleda,
što radi Draft.

### Izmjereno od strane programera {#measured-by-the-developer}

Ista ONNX datoteka, isti izlaz, RTX 5080:

| Pozadina | Propusnost dubine |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Probni klip kroz isporučenu ONNX putanju:

| Postavka | Zadržani pogledi | Propusnost dubine |
|---|---|---|
| Draft | oko 1 od 7 | oko 50 /s |
| Balanced | oko 1 od 4 | oko 50 /s |
| Detailed | oko 1 od 2 | oko 40 /s |

Dubina je znatno brža od snimanja, pa skeniranje uživo nije ograničeno dubinom. Okruženje
aplikacije je oko 349 MiB bez PyTorcha, naspram otprilike 3,5 GB za torch s CUDA-om.

Offline putanja `reconstruct` je drugačija: minute po prozoru od 16 kadrova na desktop GPU-u.

## Memorija {#memory}

- Kadrovi se ne čuvaju nakon fuzije, osim **160** za bojenje mreže.
- Skeniranje se zaustavlja na **3000** zadržanih pogleda zadano ("Views kept"), kao zaštita.
- Red snimanja uživo drži 4 kadra; međuspremnik telemetrijskih poza 30 sekundi.
- Obje mreže voksela su rijetke, a mreža trokuta se izdvaja blok po blok, pa memorija prati ono što je
  skenirano, a ne granični okvir.

## Platforma {#platform}

Skener i Assetto Corsa snimači su u praksi samo za Windows: snimanje uživo koristi Windows
Graphics Capture, prečice i click-through overlay koriste Win32 API, a Kunos stranice
su Windows dijeljena memorija. Video datoteke se mogu skenirati i UDP snimači rade drugdje, ali to
nije provjereno.
