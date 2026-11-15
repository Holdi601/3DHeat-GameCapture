---
title: Reconstrução de níveis
nav_order: 6
lang: "pt"
source: reconstruction.md
source_hash: "335908a1ed4a"
nav_exclude: true
search_exclude: true
---
# Reconstrução de níveis a partir da jogabilidade {#level-reconstruction-from-gameplay}

Percorra um nível devagar, ou conduza numa pista, e o digitalizador transforma o que o ecrã mostrou num `.glb` que o visualizador do 3DHeat carrega como contexto por baixo da telemetria - o mesmo contrato de ficheiro que o exportador do Unreal escreve. Serve para o caso em que ninguém exportou o mapa e os ficheiros do jogo não podem ser lidos; uma exportação do motor ou dos ficheiros do jogo é exata, isto é uma estimativa.

## O percurso {#the-pipeline}

```text
 frames              keyframes            depth                pose                 fusion              output
 ------              ---------            -----                ----                 ------              ------
 Windows Graphics -> picture-change   ->  Depth Anything V2 -> visual odometry   -> occupancy volume -> marching cubes
 Capture, or a       threshold            (ONNX Runtime,        (ORB + PnP), or      + coverage grid     -> ground/structure
 video file          (adaptive)           letterboxed)          Forza telemetry,     (live map,          -> vertex colour
                                                                or a VGGT solve      weak spots)         -> .glb
                     HUD / cockpit masks, frame-quality advice, ground-plane scale
```

| Etapa | Digitalização ao vivo (`heat3d_capture.ui`) | Offline (`reconstruct`) | Página |
|---|---|---|---|
| Quadros | monitor, janela ou vídeo, redimensionado ao lado mais longo do padrão | vídeo, amostrado duas vezes (plano de resolução e intervalo de fusão) | [Captura](reconstruction-capture.md) |
| Quadros-chave | guardados conforme o quanto a imagem mudou, com limiar adaptado à captura | a cada `--fuse-interval` segundos | [Captura](reconstruction-capture.md#keyframes) |
| Máscaras | `ScreenMask` baseada em alterações, depois `FlowMask` baseada em fluxo após 40 quadros-chave | `FlowMask` aprendida a partir de quatro passagens do vídeo; não aplicada ao solucionador | [Captura](reconstruction-capture.md#what-is-not-the-world) |
| Profundidade | modelo ONNX no melhor backend da GPU | Depth Anything V2 Small em PyTorch | [Profundidade](reconstruction-depth.md) |
| Pose | odometria visual, ou telemetria exata do Forza | janelas VGGT unidas num único caminho, interpoladas | [Pose](reconstruction-pose.md), [Offline](reconstruction-offline.md) |
| Escala | altura da câmara acima do chão (1,15 m) uma vez, ou telemetria | as unidades do próprio caminho resolvido | [Pose](reconstruction-pose.md#scale) |
| Fusão | ocupação ponderada, voxels esparsos; grade de cobertura | o mesmo | [Fusão](reconstruction-fusion-and-texture.md) |
| Saída | `.glb`, partes de chão/estrutura, cor por vértice, centímetros | o mesmo | [A saída .glb](glb-output.md) |

Código: [`heat3d_capture/scan/`](https://github.com/Holdi601/3DHeat-GameCapture/tree/main/heat3d_capture/scan) (`session.py` - as definições e o ritmo de uma digitalização; `reconstruct.py` - quadros-chave em geometria; `offline.py` - o caminho offline), com as etapas em `capture/`, `depth/`, `pose/`, `fusion/` e `geometry/`.

## De onde vem a precisão {#where-accuracy-comes-from}

A profundidade monocular só está certa a menos de uma escala desconhecida - uma fotografia de uma sala e de uma casa de bonecas são a mesma imagem. Assim, deixa a rede fazer o que faz bem (forma relativa, arestas, estruturas finas), e a escala e o caminho da câmara vêm de algum lugar que os conhece:

| Jogo | Caminho da câmara | Escala |
|---|---|---|
| Forza Horizon / Motorsport com telemetria ligada | exato, do Data Out, interpolado para o instante de captura de cada quadro | exata: a profundidade fica ancorada por triangulação de características entre duas poses conhecidas |
| Qualquer outro, ao vivo | odometria visual, encadeada quadro a quadro | fixada uma vez a partir de uma altura de câmara presumida acima do chão |
| Uma gravação, offline | VGGT, resolvido sobre janelas sobrepostas | as unidades da própria resolução (não métricas) |

O único número que o digitalizador recebe em vez de medir é o **campo de visão horizontal** do jogo (90 graus por padrão na janela; os jogos de corrida ficam mais perto de 65). Estreito demais e o nível se reconstrói mais fundo do que é; largo demais e ele fica achatado.

## Avisar o utilizador cedo {#telling-the-user-early}

Uma digitalização é um ato físico - alguém percorre um nível durante vários minutos - e a falha cara é acabar a caminhada e descobrir que não serviu. Por isso, a janela mede a vazão de profundidade desta máquina antes de qualquer coisa poder começar e diz como será a digitalização ([Execução](runtime.md#what-to-expect-from-this-machine)); durante a digitalização mostra um mapa de cobertura com pontos fracos numerados, a saúde do seguimento, uma barra de velocidade de caminhada, uma barra de nitidez e uma instrução de cada vez, na janela e numa sobreposição clicável por cima do jogo ([A janela de digitalização](reconstruction-scan-ui.md)).

## Medido numa verdade de referência sintética {#measured-on-synthetic-ground-truth}

O `tests/test_accuracy.py` renderiza uma sala de 12 x 8 m (4 m de altura) a partir de um caminho de câmara conhecido, com profundidade analítica (não da rede), e reconstrói-a com voxels de 0,2 m. Afirma que mais de 90% dos quadros são colocados, que o erro médio do caminho é inferior a 0,35 m (o pior, inferior a 1 m), que a distância percorrida fica a 10% da verdade, que a sala sai com a largura certa a 1,5 m, que mais de 75% da superfície das paredes fica a 0,45 m de uma parede real, que uma caminhada de levantamento obtém uma cobertura claramente melhor do que andar sempre em frente, e que uma cena sem características é recusada em vez de inventada. A profundidade analítica isola a pose, a escala e a fusão da rede; a forma como a rede se comporta na jogabilidade real é outra questão, que nenhuma cena sintética responde. O `tests/test_track_width.py` verifica que uma volta conduzida fora do centro de uma estrada de largura conhecida reconstrói a largura da estrada, e não apenas a linha conduzida.

## Páginas {#pages}

- [A janela de digitalização](reconstruction-scan-ui.md) - cada controlo, atalho e elemento de sobreposição
- [Captura, máscaras e qualidade dos quadros](reconstruction-capture.md)
- [Profundidade](reconstruction-depth.md)
- [Pose da câmara e escala](reconstruction-pose.md)
- [Fusão, cobertura e cor](reconstruction-fusion-and-texture.md)
- [A saída .glb](glb-output.md)
- [Reconstrução offline](reconstruction-offline.md)
