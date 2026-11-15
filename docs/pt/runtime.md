---
title: "Execução e dependências"
nav_order: 8
lang: "pt"
source: runtime.md
source_hash: "f59339917d0d"
nav_exclude: true
search_exclude: true
---
# Execução, dependências e desempenho {#runtime-dependencies-and-performance}

Código: [`runtime/preflight.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/preflight.py),
[`runtime/device.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/runtime/device.py),
[`scan.bat`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/scan.bat),
[`requirements.txt`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/requirements.txt).

## scan.bat {#scanbat}

Dê um clique duplo nele. Ele faz apenas duas coisas por conta própria:

1. **Encontra o Python** (`python`, depois `py`). Se não houver nenhum, pergunta `Install it now with winget [Y,N]?`; com Y, executa `winget install -e --id Python.Python.3.12` e pede que feche a janela e execute `scan.bat` de novo, para que o Windows reconheça o novo PATH. Com N, nada é instalado.
2. **Cria um ambiente privado**, `.venv` ao lado de `scan.bat`, se não existir, e atualiza o seu pip - então nada é instalado no Python do sistema.

Depois executa `.venv\Scripts\python.exe -m heat3d_capture.ui`. Todo o resto - descobrir o que falta, explicar para que serve, perguntar - acontece no Python, como uma caixa de diálogo.

## Verificação na primeira execução {#first-run-preflight}

Antes que a janela importe qualquer coisa pesada, cada requisito é verificado (com `importlib.util.find_spec`, então um pacote meio removido conta como faltando). As regras:

- **Tudo é verificado primeiro.** A lista completa é reunida antes de qualquer aviso, então corrigir um pacote nunca leva direto ao erro seguinte.
- **Perguntar, nunca presumir.** A caixa de diálogo lista cada pacote faltante, para que ele serve e a transferência total, e não faz nada sem **Download and install**. Cancelar sai: "Nothing was installed and nothing was changed."
- **Silêncio não é consentimento.** Sem o Qt, a verificação recorre ao console e pergunta `Install them now? [Y/n]` (Enter, `y`, `yes`, `j`, `ja` significam sim); sem um terminal para responder (fim da entrada), não instala nada.
- **No ambiente desta ferramenta.** A instalação é `<python em execução> -m pip install ...` como subprocesso - com o `scan.bat`, o `.venv` privado. Se falhar, a caixa de diálogo mostra a última linha da saída do pip e o comando para tentar manualmente.

| Pacote | Importado como | Mostrado como para que serve | Transferência aproximada |
|---|---|---|---|
| numpy | `numpy` | a aritmética sobre a qual tudo o mais é construído | 20 MB |
| opencv-python | `cv2` | ler ficheiros de vídeo e quadros da câmara | 40 MB |
| onnxruntime-directml no Windows, onnxruntime nos demais | `onnxruntime` | executar o modelo de profundidade na sua placa de vídeo | 120 MB |
| PySide6-Essentials | `PySide6` | a janela e os seus controlos | 90 MB |
| scipy | `scipy` | suavizar a superfície reconstruída | 45 MB |
| scikit-image | `skimage` | transformar medições numa superfície 3D | 30 MB |
| windows-capture | `windows_capture` | capturar uma janela de jogo ao vivo (opcional: sem ele, os ficheiros de vídeo ainda funcionam) | 5 MB |

Converter o modelo de profundidade precisa de mais três, pedidos à parte e só ao premir "Set up the depth model": `torch` (cerca de 900 MB), `transformers` (30 MB), `onnxscript` (15 MB). O digitalizador em si nunca os importa.

O comando `reconstruct` offline tem uma verificação própria, executada depois que ele imprime a linha de licença e só no terminal: `torch` (900 MB), `transformers` (30 MB), `einops`, `safetensors`, `huggingface_hub`, `Pillow`, e `vggt` do repositório GitHub da Meta (instalado com `--no-deps`, porque os metadados dele fixam o numpy abaixo da versão 2). A mesma lista está no `requirements-offline.txt`; veja [Reconstrução offline](reconstruction-offline.md#requirements).

O pacote do ONNX Runtime oferecido é o que o `requirements.txt` escolhe para a plataforma: `onnxruntime-directml` no Windows, `onnxruntime` nos demais. Se o `onnxruntime` já puder ser importado (por exemplo, `onnxruntime-gpu`), nada é instalado: a verificação é pelo nome do módulo.

## Instalando manualmente {#installing-by-hand}

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m heat3d_capture.ui
```

O `requirements.txt` fixa: `numpy>=2.0,<2.8`, `opencv-python>=4.10`, `windows-capture>=1.4` (só Windows), `scipy>=1.11`, `scikit-image>=0.22`, `pytest>=8.0`, `PySide6-Essentials>=6.6`, `onnxruntime-directml>=1.19` no Windows e `onnxruntime>=1.19` nos demais.

O `requirements-offline.txt` acrescenta o que só o `reconstruct` precisa: `transformers`, `einops`, `safetensors`, `huggingface_hub` e `Pillow`, com a linha de instalação do `vggt` (`--no-deps`) e a nota de licença do VGGT no cabeçalho. O PyTorch também não está nele, pelo motivo abaixo.

**O PyTorch fica de propósito de fora.** A versão certa depende da GPU e da versão do CUDA, e fixar uma instalaria uma compilação para CPU nas máquinas que mais precisam da compilação para GPU. Se quiser o PyTorch (conversão do modelo, o caminho offline `reconstruct`), instale-o **antes** do `requirements.txt`: os pacotes do torch podem fixar o numpy na versão 1.x, que o scipy então recusa executar, e a falha aparece como `module numpy has no attribute long` de dentro do scipy, longe da causa.

`onnxruntime-directml` e `onnxruntime-gpu` entram em conflito: instale só um.

Verificado pelo programador: Python 3.13, onnxruntime-directml 1.24.4, PySide6 6.11, numa NVIDIA RTX 5080, e o mesmo ambiente sem nenhum pacote específico da NVIDIA.

## Backends de inferência {#inference-backends}

O ONNX Runtime chega às GPUs por fornecedores de execução, e quais existem depende de como o onnxruntime foi instalado, não do hardware. Então a disponibilidade é descoberta, do melhor para o pior:

| Posição | Fornecedor | Mostrado como | Hardware |
|---|---|---|---|
| 1 | `TensorrtExecutionProvider` | TensorRT | NVIDIA |
| 2 | `CUDAExecutionProvider` | CUDA | NVIDIA |
| 3 | `DmlExecutionProvider` | DirectML | qualquer GPU Direct3D 12: AMD, Intel, NVIDIA |
| 4 | `ROCMExecutionProvider` | ROCm | AMD |
| 5 | `CoreMLExecutionProvider` | CoreML | Apple |
| 6 | `CPUExecutionProvider` | CPU | qualquer um |

**O DirectML é a instalação padrão** porque alcança GPUs AMD e Intel, além da NVIDIA. A NVIDIA é mais rápida com os próprios fornecedores - instalar o `onnxruntime-gpu` adiciona o CUDA, e a janela avisa quando vê uma placa NVIDIA a correr no DirectML -, mas a NVIDIA não pode ser a única opção. A CPU fica sempre por último, então uma máquina sem GPU utilizável tem uma digitalização lenta em vez de nenhuma, e ela é acrescentada como alternativa quando uma sessão em GPU é criada.

O nome do adaptador é lido da chave de classe de adaptadores de vídeo do Windows no registo (não de uma ferramenta do fabricante, como o `nvidia-smi`, que existe só em algumas máquinas), saltando o Basic Render Driver. Fornecedores presos a um fabricante identificam o adaptador correspondente; o DirectML é mostrado no primeiro adaptador enumerado, que é o padrão do sistema. O nome serve só para apresentação.

`ScanSettings.prefer_backend` (só para scripts) pode indicar um fornecedor, pelo nome completo ou abreviado.

## O que esperar desta máquina {#what-to-expect-from-this-machine}

A janela mede a velocidade real do modelo de profundidade nesta máquina na inicialização (6 quadros depois de um aquecimento), em vez de procurar a GPU numa tabela - o estado térmico, os perfis de energia de notebooks e as versões de driver mudam isso demais - e informa como será uma digitalização antes que qualquer coisa possa começar:

| Vistas medidas por segundo | Nível | Título | Conselho |
|---|---|---|---|
| 25 ou mais | tempo real | Digitalização ao vivo em detalhe total. | Ande em ritmo normal; a sobreposição acompanhará. |
| 12 a 25 | viável | Digitalização ao vivo, com menos vistas guardadas do que em velocidade total. | Ande devagar e faça curvas suaves - curvas rápidas deixarão lacunas. O Draft guarda menos vistas, o que ajuda o modelo de profundidade a acompanhar. |
| 2 a 12 | lento | Grave primeiro, reconstrua depois. | Grave um vídeo do percurso e reconstrua a partir do ficheiro depois. O resultado é idêntico; só o retorno não é ao vivo. |
| abaixo de 2 | impraticável | Esta máquina é lenta demais para digitalizar com utilidade. | Um percurso menor, ou um modelo menor. **O início fica desativado.** |

Na CPU, a nota acrescenta que instalar o `onnxruntime-directml` geralmente resolve no Windows. Nada muda a resolução de captura por conta própria: não ajudaria, porque o modelo de profundidade executa-se no seu tamanho fixo de entrada, independentemente do que receba; o que mantém uma máquina mais lenta funcionando é guardar menos vistas, que é o que o Draft faz.

### Medido pelo programador {#measured-by-the-developer}

Mesmo ficheiro ONNX, mesma saída, RTX 5080:

| Backend | Vazão de profundidade |
|---|---|
| DirectML | 54 fps |
| CPU | 3,5 fps |

Um clip de teste pelo caminho ONNX entregue:

| Padrão | Vistas guardadas | Vazão de profundidade |
|---|---|---|
| Draft | cerca de 1 em 7 | cerca de 50 /s |
| Balanced | cerca de 1 em 4 | cerca de 50 /s |
| Detailed | cerca de 1 em 2 | cerca de 40 /s |

A profundidade é folgadamente mais rápida que a captura, então a digitalização ao vivo não fica limitada pela profundidade. O ambiente da aplicação tem cerca de 349 MiB sem PyTorch, contra cerca de 3,5 GB do torch com CUDA.

O caminho offline `reconstruct` é diferente: minutos por janela de 16 quadros numa GPU de desktop.

## Memória {#memory}

- Os quadros não são mantidos depois da fusão, exceto **160** para colorir a malha.
- Uma digitalização para em **3000** vistas guardadas por padrão ("Views kept"), como proteção.
- A fila de captura ao vivo guarda 4 quadros; o buffer de poses de telemetria guarda 30 segundos.
- As duas grades de voxels são esparsas, e a malha é extraída bloco a bloco, então a memória acompanha o que foi digitalizado, não a caixa delimitadora.

## Plataforma {#platform}

O digitalizador e os gravadores de Assetto Corsa são, na prática, só para Windows: a captura ao vivo usa o Windows Graphics Capture, os atalhos e a sobreposição sem clique usam a API Win32, e as páginas da Kunos são memória partilhada do Windows. Ficheiros de vídeo podem ser digitalizados e os gravadores UDP correm noutros sistemas, mas isso não foi verificado.
