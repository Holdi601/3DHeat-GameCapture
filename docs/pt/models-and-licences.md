---
title: Modelos e licenças
nav_order: 7
lang: "pt"
source: models-and-licences.md
source_hash: "b5410116f001"
nav_exclude: true
search_exclude: true
---
# Modelos e licenças {#models-and-licences}

Tudo o que está escrito para este repositório está sob a **licença MIT** ([`LICENSE`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSE)). O que a MIT não consegue cobrir é aquilo com que as ferramentas funcionam: os pacotes que importam, os modelos que a reconstrução usa e os jogos que leem. O registo completo, com fontes, está em [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md); as suas licenças foram lidas nos metadados dos pacotes e nas descrições dos modelos em setembro de 2026. Quando os termos de um componente mudaram desde então, conta a fonte, não esta página. Nada aqui é aconselhamento jurídico.

## O modelo de profundidade - o que decide a utilização comercial {#the-depth-model---the-one-that-decides-commercial-use}

O Depth Anything V2 **não tem a mesma licença em todos os tamanhos**, e uma reconstrução herda a licença do modelo que a fez:

| Modelo | Licença | Utilização comercial | Usado por |
|---|---|---|---|
| **Depth-Anything-V2-Small** | **Apache-2.0** | **permitida** | o padrão: o modelo convertido do digitalizador (`tools/export_onnx.py` usa-o por padrão, e o botão "Set up the depth model" da janela constrói sempre este) e a profundidade do caminho offline (fusão); o VGGT fornece as suas poses |
| Depth-Anything-V2-Base | CC-BY-NC-4.0 | apenas não comercial | só se o converter por si (`--size base`) |
| Depth-Anything-V2-Large | CC-BY-NC-4.0 | apenas não comercial | só se o converter por si (`--size large`) |

O Base e o Large dão uma profundidade melhor. Convertê-los é permitido; isso torna esse ficheiro de modelo, e todas as reconstruções feitas com ele, não comerciais. É uma decisão de quem o executa, não um padrão a herdar. O digitalizador escolhe entre os ficheiros `models/depth-*.onnx` **pela licença, não pelo nome**: `depth-small-*` sempre que exista um, depois o Base, depois o Large (`choose_model` em [`depth/onnx_estimator.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/depth/onnx_estimator.py)). A janela indica o ficheiro que tomou, a sua licença e quaisquer outros ficheiros de modelo que encontrou e não usou; para digitalizar com o Base, tire o ficheiro Small de `models/`.

## VGGT - só reconstrução offline {#vggt---offline-reconstruction-only}

| Modelo | Licença | Disponibilidade |
|---|---|---|
| `facebook/VGGT-1B` | **CC-BY-NC-4.0 - só não comercial**; as reconstruções feitas com ele herdam isso | público; o padrão |
| `facebook/VGGT-1B-Commercial` | licença separada; confirme os termos que lhe foram concedidos | com acesso restrito: o acesso é pedido à Meta e concedido por conta; sem ele, a transferência falha. Escolhido com `reconstruct --model vggt-1b-commercial` |

O VGGT só é usado por `python -m heat3d_capture reconstruct`; o digitalizador ao vivo nunca o carrega. O comando imprime a linha da licença antes de começar. A reconstrução a partir de vídeo é a parte deste projeto que um jogador executaria, e os termos não comerciais encaixam nisso; para trabalho comercial, o caminho é uma exportação do motor ou o exportador de ficheiros de jogo, e ambos são exatos de qualquer forma.

## Localizar quadros - `locate` {#locating-frames---locate}

| Modelo | Licença | Função |
|---|---|---|
| DINOv2 ViT-B/14 (`facebook/dinov2-base`) | Apache-2.0 | encontra as renderizações que mostram o mesmo local |
| ALIKED `aliked-n16` | BSD-3-Clause | pontos-chave e descritores |
| LightGlue (variante ALIKED) | Apache-2.0 | faz a correspondência entre eles |

Os três permitem utilização comercial e são transferidos no primeiro uso. O SuperPoint, o parceiro habitual do LightGlue, não é usado: os seus pesos são não comerciais. Ver [Localizar quadros num nível](locate.md).

## Pacotes Python {#python-packages}

| Pacote | Licença | Função |
|---|---|---|
| numpy, scipy, scikit-image | BSD-3-Clause | aritmética, suavização, marching cubes |
| opencv-python | Apache-2.0 | vídeo, características, fluxo óptico |
| onnxruntime, onnxruntime-directml | MIT | inferência de profundidade |
| windows-capture | MIT | captura ao vivo através do Windows Graphics Capture |
| **PySide6-Essentials** | **LGPL-3.0** | a janela |
| pytest | MIT | só desenvolvimento |
| torch, transformers, onnxscript | BSD-3-Clause / Apache-2.0 | conversão de modelos feita uma só vez; o caminho offline |
| einops, safetensors, huggingface_hub, Pillow | MIT / Apache-2.0 / Apache-2.0 / MIT-CMU | o caminho offline (`requirements-offline.txt`) |
| vggt | "VGGT License" da Meta (acordo de materiais de investigação com uma política de uso aceitável) | o caminho offline; instalado a partir do GitHub com `--no-deps` |
| moderngl, glcontext | MIT | `locate`: renderização do nível fora do ecrã (`requirements-locate.txt`) |
| kornia, kornia-rs | Apache-2.0 | `locate`: pontos-chave e correspondência |

**O PySide6 tem condições.** A LGPL-3.0 permite uso proprietário e comercial desde que o Qt continue a ser uma biblioteca *substituível*. Aqui é usado como uma importação normal ligada dinamicamente, o que o cumpre, e o seu aviso de licença precisa acompanhar qualquer distribuição. Empacotar a ferramenta num único executável teria de manter o Qt substituível.

A licença do próprio pacote `vggt` foi lida no seu `LICENSE.txt` e está registada no `LICENSES.md`; abrange o código, separadamente da CC-BY-NC-4.0 dos pesos.

## Os jogos {#the-games}

A telemetria vem apenas de interfaces que os jogos publicam; os quadros vêm do ecrã. Ver [As regras](rules.md). Nada de um jogo é incluído nem redistribuído, e o que as ferramentas produzem fica na máquina do utilizador. O 3DHeat GameCapture não é afiliado a nenhum editor de jogos nem aprovado por nenhum; os nomes dos jogos e as marcas relacionadas pertencem aos seus proprietários.
