---
title: "Profundidade"
nav_order: 3
lang: "pt"
source: reconstruction-depth.md
source_hash: "640f483b0b71"
nav_exclude: true
search_exclude: true
---
# Profundidade {#depth}

A única coisa que a captura externa não consegue dar é a geometria. O jogo conhece a profundidade de cada pixel e ela fica num buffer que este projeto deliberadamente não toca, então a profundidade é **inferida a partir da imagem**. Esse é o limite de precisão de toda a abordagem.

Código: [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)
(o que o digitalizador executa),
[`depth/estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/estimator.py)
(o caminho PyTorch e o ajuste de escala),
[`tools/export_onnx.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/tools/export_onnx.py).

## O modelo {#the-model}

**Depth Anything V2**, variante relativa. Ele prevê *inverso de profundidade relativo*: um campo do tipo disparidade, correto apenas a menos de uma transformação afim desconhecida, `metric_disparity = a * predicted + b`, diferente para cada quadro. A rede é boa no que é difícil a partir de uma só imagem (forma relativa, bordas, estrutura fina) e silenciosa sobre o que não consegue saber (a escala). A escala vem de outro lugar - veja [Pose da câmara e escala](reconstruction-pose.md).

| Tamanho | Id no Hugging Face | Licença |
|---|---|---|
| **Small** (padrão) | `depth-anything/Depth-Anything-V2-Small-hf` | **Apache-2.0** - utilização comercial permitida |
| Base | `depth-anything/Depth-Anything-V2-Base-hf` | CC-BY-NC-4.0 - só não comercial |
| Large | `depth-anything/Depth-Anything-V2-Large-hf` | CC-BY-NC-4.0 - só não comercial |

Uma reconstrução herda a licença do modelo que a fez. O Small é o padrão em todo lugar justamente para que uma digitalização não tenha restrição alguma, a menos que alguém escolha outra coisa. As variantes métricas (`Depth-Anything-V2-Metric-Outdoor-Small-hf`, `...-Indoor-Small-hf`) são citadas no código, mas o digitalizador não as usa. Veja [Modelos e licenças](models-and-licences.md).

## Construindo o modelo {#building-the-model}

O digitalizador executa um ficheiro ONNX e nunca importa o PyTorch. O ficheiro precisa de ser feito uma vez:

- **Pela janela**: "Set up the depth model" (veja [A janela de digitalização](reconstruction-scan-ui.md#when-there-is-no-depth-model-yet)), que executa o comando abaixo com `--size small`.
- **Manualmente**, num ambiente com PyTorch, `transformers` e `onnxscript`:

```bash
python tools/export_onnx.py                       # models/depth-small-518.onnx
python tools/export_onnx.py --size base --out models/depth-base.onnx
```

| Opção | Padrão | Significado |
|---|---|---|
| `--size` | `small` | `small`, `base` ou `large` |
| `--out` | `models/depth-<size>-<side>.onnx` | ficheiro de saída |
| `--side` | `518` | tamanho quadrado de entrada; precisa de ser múltiplo de 14 (o tamanho do patch do ViT); 518 = 14 x 37 é a resolução de treino |
| `--opset` | `17` | opset do ONNX; 17 é bem suportado pelo DirectML e pelo CUDA |

O que o conversor faz:

- Transfere o checkpoint do Hugging Face (`AutoModelForDepthEstimation`).
- Envolve o modelo para que a **normalização ImageNet fique dentro do grafo**: o modelo recebe RGB na faixa 0-255 como float (`pixels`, formato `lote x 3 x lado x lado`) e produz `inverse_depth`. Existe exatamente uma cópia da média e do desvio padrão, então eles não podem divergir do checkpoint.
- **Tamanho espacial fixo**, lote dinâmico. O DirectML e o TensorRT compilam por formato; uma altura e largura dinâmicas recompilariam no primeiro quadro de cada nova resolução, uma parada visível numa captura ao vivo.
- Exporta pelo **caminho TorchScript** (`dynamo=False`): o grafo dynamo falhou no DirectML num nó Reshape, e ele grava os pesos como um ficheiro `.onnx.data` separado. O caminho TorchScript produz um único ficheiro autocontido.
- Mostra o ficheiro e o seu tamanho. Os avisos do seguidor sobre formatos fixados no grafo são esperados.

O digitalizador procura `models/depth-*.onnx` e escolhe pela licença, não pelo nome do ficheiro: o Small sempre que ele está presente, um tamanho maior só quando é o único. A linha da janela de digitalização diz o ficheiro, a licença dele e qualquer outro modelo que ficou sem uso.

## Executando: ONNX Runtime {#running-it-onnx-runtime}

`OnnxDepthEstimator` cria uma única sessão do ONNX Runtime, de forma preguiçosa, com otimização completa do grafo, no backend que a ordem escolheu, com a CPU acrescentada como alternativa para que um fornecedor que falhe na criação da sessão (um driver antigo) signifique uma digitalização lenta, e não um erro. Veja [Execução e dependências](runtime.md#inference-backends).

- `warm_up()` cria a sessão e executa um quadro em branco (a primeira inferência num grafo novo é várias vezes mais lenta que o estado estável).
- `measure_throughput(frames)` mede esse número de quadros em branco depois do aquecimento; a janela usa 6 e informa o resultado como vistas por segundo.

### Letterbox, não esticar {#letterboxing-not-stretching}

O grafo recebe um quadrado fixo; o jogo é 16:9. Espremer um quadro num quadrado mudaria a forma aparente de tudo, e como a saída é uma estimativa geométrica ela seria fundida como geometria real errada. Então cada quadro passa por:

1. ser redimensionado para caber no quadrado, mantendo a proporção (interpolação por área para reduzir, cúbica para ampliar);
2. ser preenchido com **cinza médio (114)** - preto ou branco são lidos como uma borda forte e vazam uma descontinuidade de profundidade falsa para o conteúdo ao lado;
3. passar pelo modelo;
4. o preenchimento ser cortado da previsão **antes** de ser redimensionado de volta (cúbico) para a resolução do quadro, para que a margem nunca vaze para os pixels reais.

O resultado é um `DepthMap` com `metric=False` no tamanho do quadro de origem.

## O caminho PyTorch {#the-pytorch-path}

`DepthEstimator` executa o modelo do Hugging Face diretamente (fp16 na CUDA, fp32 na CPU), em lotes por tamanho de quadro, com cada previsão redimensionada de volta de forma cúbica. O digitalizador não o usa; o comando offline `reconstruct` usa (veja [Reconstrução offline](reconstruction-offline.md)), que é uma das razões pelas quais esse comando precisa de PyTorch e `transformers`.

## De relativo para métrico: `fit_scale` e `AffineFit` {#from-relative-to-metric-fitscale-and-affinefit}

Transformar o inverso de profundidade previsto em metros precisa da afim `scale * predicted + shift`. Quando âncoras de profundidade conhecida estão disponíveis (pontos de características triangulados entre poses conhecidas, ou a profundidade ancorada do quadro anterior), `fit_scale` a resolve:

- mínimos quadrados **em disparidade**, não em profundidade - o erro da rede é aproximadamente uniforme em disparidade, enquanto em profundidade algumas âncoras distantes (onde um pixel de disparidade equivale a dezenas de metros) dominariam;
- **reponderado iterativamente** (12 iterações, pesos do tipo Cauchy `1 / (1 + (r / 3 MAD)^2)`), porque as âncoras trazem outliers grosseiros (um correspondência num carro em movimento, uma falha de seguimento) e uma única dessas âncoras num ajuste simples arrasta o quadro inteiro;
- precisa de pelo menos 2 âncoras utilizáveis; informa o resíduo absoluto mediano e a contagem de inliers (resíduo dentro de 3 x a mediana).

`AffineFit.apply` retorna a profundidade em metros com **+inf** para o céu. Ele verifica o valor previsto além do ancorado: um pixel de céu que prevê zero sairia em `shift` - pequeno, positivo, finito - e, de outra forma, poria todos os pixels de céu numa casca fantasma a uma distância. Qualquer coisa prevista em ou abaixo de `1e-4` é céu, qualquer que seja o ajuste.

Depois, a fusão mantém só profundidades entre 0,35 m e 60 m (veja [Fusão](reconstruction-fusion-and-texture.md#from-depth-to-points)).
