---
title: Głębokość
nav_order: 3
lang: "pl"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Głębokość {#depth}

Jedyna rzecz, której zewnętrzne przechwytywanie nie może dać, to geometria. Gra zna głębię każdego piksela i leży ona w buforze, którego ten projekt celowo nie dotyka, więc głębokość jest **wnioskowana z obrazu**. To jest sufit dokładności całego podejścia.

Kod: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(czego używa skaner),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(ścieżka PyTorch i dopasowanie skali),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## Model {#the-model}

**Depth Anything V2**, wariant względny. Przewiduje *względną odwrotną głębokość*: pole podobne do dysparycji, poprawne tylko z dokładnością do nieznanego przekształcenia afinicznego, `metric_disparity = a * predicted + b`, różnego dla każdej klatki. Sieć dobrze radzi sobie z tym, co trudne z jednego obrazu (względny kształt, krawędzie, cienkie struktury), i milczy o tym, czego nie może wiedzieć (skala). Skala pochodzi skądinąd - zob. [Poza kamery i skala](reconstruction-pose.md).

| Rozmiar | Identyfikator Hugging Face | Licencja |
|---|---|---|
| **Mały** (domyślny) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - użycie komercyjne dozwolone |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - tylko niekomercyjnie |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - tylko niekomercyjnie |

Rekonstrukcja dziedziczy licencję modelu, który ją zrobił. Mały jest domyślny wszędzie właśnie po to, by skan nie niósł żadnego ograniczenia, chyba że ktoś wybierze inaczej. Warianty metryczne (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) są wymienione w kodzie, ale skaner ich nie używa. Zob. [Modele i licencje](models-and-licences.md).

## Budowanie modelu {#building-the-model}

Skaner uruchamia plik ONNX i nigdy nie importuje PyTorcha. Plik trzeba wygenerować raz:

- **Z okna**: „Set up the depth model” (zob. [Okno skanowania](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), które uruchamia poniższe polecenie z `--size small`.
- **Ręcznie**, w środowisku z PyTorch, `transformers` i `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opcja | Domyślnie | Znaczenie |
|---|---|---|
| `--size` | `small` | `small`, `base` lub `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | plik wyjściowy |
| `--side` | `518` | kwadratowy rozmiar wejścia; musi być wielokrotnością 14 (rozmiar łaty ViT); 518 = 14 x 37 to rozdzielczość treningowa |
| `--opset` | `17` | wersja opsetu ONNX; 17 jest szeroko obsługiwana przez DirectML i CUDA |

Co robi konwerter:

- Pobiera punkt kontrolny z Hugging Face (`AutoModelForDepthEstimation`).
- Opakowuje go tak, że **normalizacja ImageNet jest wewnątrz grafu**: model przyjmuje RGB w zakresie 0-255 jako float (`pixels`, kształt `batch x 3 x side x side`) i zwraca `inverse_depth`. Jest dokładnie jedna kopia średniej i odchylenia standardowego, więc nie mogą rozjechać się z punktem kontrolnym.
- **Stały rozmiar przestrzenny**, dynamiczny batch. DirectML i TensorRT kompilują się dla każdego kształtu; dynamiczna wysokość i szerokość kompilowałyby się przy pierwszej klatce każdej nowej rozdzielczości - widoczne zacięcie w żywym przechwytywaniu.
- Eksportuje przez **ścieżkę TorchScript** (`dynamo=False`): graf dynamo nie działał na DirectML na węźle Reshape, a jego wagi trafiały do osobnego pliku `.onnx.data`. Ścieżka TorchScript daje jeden samodzielny plik.
- Wypisuje plik i jego rozmiar. Ostrzeżenia tracera o zapisanych na stałe kształtach są oczekiwane.

Skaner szuka `models/depth-*.onnx` i wybiera według licencji, a nie nazwy pliku: Mały, gdy jest, a większy rozmiar tylko wtedy, gdy jest jedynym. Linia okna skanowania podaje nazwę pliku, jego licencję i każdy inny nieużyty model.

## Uruchamianie: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` tworzy jedną sesję ONNX Runtime, leniwie, z pełną optymalizacją grafu, na backendzie wybranym przez drabinkę, z CPU dołączonym jako zapas. Dzięki temu dostawca, który zawodzi przy tworzeniu sesji (stary sterownik), oznacza wolny skan, a nie awarię. Zob. [Środowisko uruchomieniowe i zależności](runtime.md#inference-backends).

- `warm_up()` tworzy sesję i uruchamia jedną pustą klatkę (pierwsze wnioskowanie na świeżym grafie jest kilka razy wolniejsze niż stan ustalony).
- `measure_throughput(frames)` mierzy czas tylu pustych klatek po rozgrzewce; okno używa 6 i podaje wynik jako widoki na sekundę.

### Letterbox, a nie rozciąganie {#letterboxing-not-stretching}

Graf przyjmuje stały kwadrat; rozgrywka jest 16:9. Wciśnięcie klatki w kwadrat zmieniłoby pozorny kształt wszystkiego, a ponieważ wynik jest oszacowaniem geometrycznym, byłby zfuzowany jako prawdziwa, błędna geometria. Więc każda klatka jest:

1. skalowana, by zmieścić się w kwadrat, zachowując proporcje (interpolacja obszarowa w dół, sześcienna w górę);
2. dopełniona **szarością 114** - czerń czy biel czytają się jak mocna krawędź i rozlewają fałszywą nieciągłość głębi na sąsiednią treść;
3. przepuszczona przez model;
4. dopełnienie jest przycinane z predykcji **przed** ponownym skalowaniem (sześciennym) do rozdzielczości klatki, więc margines nigdy nie rozlewa się na prawdziwe piksele.

Wynik to `DepthMap` z `metric=False` w rozmiarze klatki źródłowej.

## Ścieżka PyTorch {#the-pytorch-path}

`DepthEstimator` uruchamia model Hugging Face bezpośrednio (fp16 na CUDA, fp32 na CPU), grupowany według rozmiaru klatki, a każda predykcja jest skalowana z powrotem sześciennie. Skaner jej nie używa; używa jej polecenie `reconstruct` działające offline (zob. [Rekonstrukcja offline](reconstruction-offline.md)), co jest jednym z powodów, dla których to polecenie potrzebuje PyTorch i `transformers`.

## Od względnej do metrycznej: `fit_scale` i `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Zamiana przewidywanej odwrotnej głębokości na metry wymaga afinicznego `scale * predicted + shift`. Gdy dostępne są kotwice o znanej głębokości (punkty cech ztriangulowane między znanymi pozami albo zakotwiczona głębokość poprzedniej klatki), `fit_scale` to rozwiązuje:

- najmniejsze kwadraty **w dysparycji**, nie w głębokości - błąd sieci jest mniej więcej jednolity w dysparycji, a w głębokości kilka odległych kotwic (gdzie jeden piksel dysparycji to dziesiątki metrów) zdominowałoby wynik;
- **iteracyjnie przeważane** (12 iteracji, wagi w stylu Cauchy'ego `1 / (1 + (r / 3 MAD)^2)`), bo kotwice niosą grube wartości odstające (dopasowanie do poruszającego się samochodu, usterka śledzenia), a jedna taka kotwica w zwykłym dopasowaniu ciągnie całą klatkę;
- wymaga co najmniej 2 użytecznych kotwic; podaje medianę bezwzględnej reszty i liczbę punktów zgodnych (inliers; reszta w granicy 3 x mediana).

`AffineFit.apply` zwraca głębokość w metrach z **+inf** dla nieba. Sprawdza przewidywaną wartość, a nie tylko zakotwiczoną: piksel nieba przewidujący zero wyszedłby jako `shift` - mały, dodatni, skończony - i w przeciwnym razie wszystkie piksele nieba wylądowałyby na fantomowej powłoce w jednej odległości. Wszystko, co przewidziane jest na poziomie `1e-4` lub niżej, jest niebem, cokolwiek mówi dopasowanie.

Fuzja zachowuje tylko głębokości między 0,35 m a 60 m (zob. [Fuzja](reconstruction-fusion-and-texture.md#from-depth-to-points)).
