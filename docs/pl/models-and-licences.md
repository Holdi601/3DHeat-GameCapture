---
title: "Modele i licencje"
nav_order: 7
lang: "pl"
source: models-and-licences.md
source_hash: "87be1ce962da"
nav_exclude: true
search_exclude: true
---
# Modele i licencje {#models-and-licences}

Wszystko, co napisano dla tego repozytorium, jest objęte **licencją MIT**
([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). Czego MIT nie obejmuje, to
z czym działają narzędzia: pakiety, które importują, modele, których używa rekonstrukcja, i gry, które
czytają. Pełny zapis ze źródłami znajduje się w
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); jego licencje odczytano
z metadanych pakietów i kart modeli we wrześniu 2026. Jeśli warunki komponentu zmieniły się od tej pory,
liczy się źródło, a nie ta strona. Nic tutaj nie jest poradą prawną.

## Model głębi - ten, który decyduje o użyciu komercyjnym {#the-depth-model---the-one-that-decides-commercial-use}

Depth Anything V2 **nie ma tej samej licencji we wszystkich rozmiarach**, a rekonstrukcja dziedziczy licencję
modelu, który ją stworzył:

| Model | Licencja | Użycie komercyjne | Używany przez |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **dozwolone** | domyślny: przekonwertowany model skanera (`tools/export_onnx.py` domyślnie właśnie go wybiera, a przycisk okna „Set up the depth model” zawsze go buduje) oraz głębia ścieżki offline (fuzja); VGGT dostarcza jego pozy |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | tylko niekomercyjnie | tylko jeśli sam go przekonwertujesz (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | tylko niekomercyjnie | tylko jeśli sam go przekonwertujesz (`--size large`) |

Base i Large dają lepszą głębię. Ich konwersja jest dozwolona; sprawia ona jednak, że ten plik modelu i każda
rekonstrukcja z nim powstała są niekomercyjne. To decyzja osoby, która go uruchamia, a nie wartość domyślna do
przejęcia. Skaner wybiera spośród plików `models/depth-*.onnx` **według licencji, a nie nazwy**: zawsze
`depth-small-*`, jeśli taki jest, potem Base, potem Large (`choose_model` w
[`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)).
Okno podaje nazwę pliku, który wzięło, jego licencję i wszystkie inne pliki modeli, które znalazło, a nie
użyło; by skanować z Base, przenieś plik Small z `models/`.

## VGGT - tylko rekonstrukcja offline {#vggt---offline-reconstruction-only}

| Model | Licencja | Dostępność |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - tylko niekomercyjnie**; rekonstrukcje z nim dziedziczą to ograniczenie | publiczny; domyślny |
| `facebook/VGGT-1B-Commercial` | licencja osobna; sprawdź warunki, które dostałeś | z ograniczonym dostępem: dostęp zamawia się u Meta i przyznaje dla konta; bez niego pobieranie się nie uda. Wybierany poleceniem `reconstruct --model vggt-1b-commercial` |

VGGT używa tylko `python -m heat3d_capture reconstruct`; skaner na żywo nigdy go nie wczytuje. Polecenie
wypisuje wiersz z licencją, zanim ruszy. Rekonstrukcja z wideo to ta część projektu, którą uruchomiłby gracz,
a warunki niekomercyjne do tego pasują; do pracy komercyjnej drogą jest eksport z silnika albo eksporter
plików gry, a oba i tak są dokładne.

## Lokalizowanie klatek - `locate` {#locating-frames---locate}

| Model | Licencja | Rola |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | znajduje renderowania pokazujące to samo miejsce |
| ALIKED `aliked-n16` | BSD-3-Clause | punkty kluczowe i deskryptory |
| LightGlue (wariant ALIKED) | Apache-2.0 | dopasowuje je |

Wszystkie trzy dopuszczają użycie komercyjne i są pobierane przy pierwszym użyciu. SuperPoint, zwykły partner
LightGlue, nie jest używany: jego wagi są niekomercyjne. Zobacz [Lokalizowanie klatek w poziomie](locate.md).

## Pakiety Pythona {#python-packages}

| Pakiet | Licencja | Rola |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | arytmetyka, wygładzanie, marching cubes |
| opencv-python | Apache-2.0 | wideo, cechy, przepływ optyczny |
| onnxruntime, onnxruntime-directml | MIT | wnioskowanie o głębi |
| windows-capture | MIT | przechwytywanie na żywo przez Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | okno |
| pytest | MIT | tylko do rozwoju |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | jednorazowa konwersja modelu; ścieżka offline |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | ścieżka offline (`requirements-offline.txt`) |
| vggt | Meta's „VGGT License” (umowa o materiałach badawczych z polityką dopuszczalnego użycia) | ścieżka offline; instalowany z GitHub poleceniem `--no-deps` |
| moderngl, glcontext | MIT | `locate`: renderowanie poziomu poza ekranem (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: punkty kluczowe i dopasowywanie |

**PySide6 ma warunki.** LGPL-3.0 dopuszcza użycie zastrzeżone i komercyjne, pod warunkiem że Qt pozostaje
biblioteką *wymienialną*. Tutaj jest używany jako zwykły, dynamicznie łączony import, co to spełnia, a jego
informacja o licencji musi towarzyszyć każdej dystrybucji. Spakowanie narzędzia w jeden plik wykonywalny
musiałoby zachować Qt jako wymienialne.

Licencja samego pakietu `vggt` została odczytana z jego `LICENSE.txt` i zapisana w `LICENSES.md`; dotyczy
kodu, osobno od wag CC-BY-NC-4.0.

## Gry {#the-games}

Telemetria pochodzi tylko z interfejsów, które gry publikują; klatki pochodzą z ekranu. Zobacz
[Obowiązujące zasady](rules.md). To, na co użytkownik kieruje narzędzia, nadal podlega licencji i EULA tej
gry, a ten obowiązek spoczywa na tym, kto uruchamia narzędzie.
