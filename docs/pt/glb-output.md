---
title: A saída .glb
nav_order: 6
lang: "pt"
source: glb-output.md
source_hash: "ef4602372650"
nav_exclude: true
search_exclude: true
---
# A saída .glb {#the-glb-output}

Uma reconstrução é escrita como um ficheiro glTF 2.0 binário (`.glb`) que o visualizador do 3DHeat carrega pelo seu painel Fundo / nível sem tratamento especial - o mesmo contrato que o exportador do Unreal escreve. Código: [`geometry/glb.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/geometry/glb.py).

É escrito manualmente e não com uma biblioteca glTF: a saída é um subconjunto estreito (um buffer, compactado, sem animação, sem skinning) e uma dependência capaz de escrever todo o glTF traria junto os seus problemas de versão, para poupar apenas algumas centenas de linhas.

## O que está no ficheiro de uma digitalização {#what-is-in-a-scans-file}

| Parte (nome do nó e da malha) | Conteúdo |
|---|---|
| `ground:<name>` | triângulos até 35 graus de inclinação virados para cima |
| `structure:<name>` | tudo o resto |

O `<name>` é o nome do ficheiro sem extensão ao guardar a partir da janela, ou o nome do vídeo para `reconstruct`. Uma parte sem triângulos fica de fora. Uma digitalização nunca escreve uma parte `water:`. `asset.generator` é `heat3d-capture-scan`.

## O contrato {#the-contract}

- **Um nó por parte**, com o nome do rótulo da parte; a malha repete o nome. O visualizador lê primeiro o nome do *nó*, por isso dar nome só às malhas perderia a classificação.
- O rótulo é `<class>:<name>`, com classe `ground`, `structure` ou `water` - o prefixo que o visualizador reconhece (`^(ground|structure|water)\s*[:|]`) para tomar a classe pelo que diz, em vez da adivinhar pela geometria. O chão é desenhado sólido, as estruturas quase transparentes.
- **As coordenadas são do espaço do visualizador**: Y para cima, mão direita, e **em centímetros** (metros x 100) para coincidirem com o exportador do Unreal; assim, uma captura e uma exportação do motor do mesmo local carregam com o mesmo tamanho e com os mesmos ângulos iniciais de câmara. O `extras.unit_metres` ao nível superior do ficheiro é `0.01` (uma unidade é um centímetro), por isso quem lê em metros, como o [`locate`](locate.md), usa-o no tamanho real. Uma digitalização colocada pela telemetria do Forza é a exceção no sistema de coordenadas: fica no mundo do próprio jogo, Y para cima e mão esquerda, exatamente como os ficheiros de volta, para que as voltas gravadas sobre ela caiam nela. Quando a escala de uma digitalização foi encontrada num quadro-chave posterior ([Escala](reconstruction-pose.md#scale)), esse fator é incorporado na escala escrita.
- `COLOR_0` é lido pelo visualizador, que sombreia o chão com ele quando o interruptor *Cor capturada* do seu painel Fundo / nível está ligado (desligado por padrão).
- Uma digitalização com pontos marcados manualmente recebe um `<name>.marks.json` ao lado; ver [Guardar](reconstruction-scan-ui.md#saving).
- Por primitiva: `POSITION` (float VEC3, com `min` e `max`, a partir dos quais o visualizador enquadra a câmara), `NORMAL` (float VEC3), `COLOR_0` opcional (float VEC3, 0..1), `TEXCOORD_0` opcional; índices de 16 bits quando todos são inferiores a 65 536, senão de 32 bits; modo triângulos.
- Cada vista de buffer começa alinhada a 4 bytes; o bloco JSON é preenchido com espaços e o bloco BIN com zeros até 4 bytes.

## Verificações antes de escrever {#checks-before-writing}

Cada parte é validada e recusada com uma mensagem que a nomeia quando não tem vértices, quando o número de índices não forma triângulos inteiros, quando um índice está fora do intervalo ou é negativo, quando as posições não são finitas, ou quando as normais ou as cores não coincidem com o número de vértices. As normais são calculadas quando faltam, **ponderadas pela área** (o marching cubes deixa lascas ao lado de faces grandes, e uma média não ponderada deixa que triângulos minúsculos decidam contra a face em que assentam); um vértice degenerado recebe "para cima". Escrever nenhuma parte é um erro.

A exportação não devolve nada - e a janela diz «Nothing to save» - quando o volume não dá superfície, em vez de escrever um ficheiro vazio que pareceria uma digitalização bem-sucedida.

## Texturas {#textures}

O escritor suporta uma textura PNG de cor base por parte (com UVs, um material de dupla face, não metálico e totalmente rugoso). As digitalizações não a usam; levam cor por vértice. Ver [cor](reconstruction-fusion-and-texture.md#colour).

## O nível de referência {#the-reference-level}

`geometry/reference.py` constrói, através do mesmo escritor, um nível sintético de tamanho exatamente conhecido: um chão de 400 m subdividido, três edifícios de 20 x 20 x 12 m e uma lagoa de 50 m, 1,5 m abaixo do chão, cada classe numa cor plana distinta. Os testes do próprio visualizador o geram e o analisam com o analisador real do visualizador; assim, o formato do ficheiro continua testado dos dois lados, sem jogo nem equipamento de captura.

```bash
python -m heat3d_capture.geometry.reference .out/reference.glb
```
