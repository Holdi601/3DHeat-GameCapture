---
title: "Fusão, cobertura e cor"
nav_order: 5
lang: "pt"
source: reconstruction-fusion-and-texture.md
source_hash: "0b3ff873cd94"
nav_exclude: true
search_exclude: true
---
# Fusão, cobertura e cor {#fusion-coverage-and-colour}

Código: [`scan/reconstruct.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/reconstruct.py),
[`fusion/volume.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/volume.py),
[`fusion/voxelindex.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/voxelindex.py),
[`fusion/coverage.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/coverage.py),
[`fusion/texture.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/fusion/texture.py).

Cada quadro-chave posicionado atualiza duas grades esparsas ao mesmo tempo: o **volume de superfície**, que vira a malha, e a **grade de cobertura**, que diz o quanto acreditar nela e para onde voltar. As duas são atualizadas por quadro-chave, não no fim, porque o mapa de cobertura é aquilo por que o jogador se guia.

## Da profundidade aos pontos {#from-depth-to-points}

Para cada quadro-chave cuja pose é conhecida **e** cuja profundidade tem escala:

1. Um a cada dois pixels em cada direção é usado (`PIXEL_STRIDE = 2`; pixels vizinhos de uma mesma superfície não são medições independentes).
2. A profundidade é convertida para metros pela afim do quadro.
3. Mantida só entre **0,35 m** (mais perto é a arma, o HUD, o capô) e **60 m** (o erro monocular cresce aproximadamente com o quadrado da distância, então pontos distantes são ruído com forma de geometria), e só nos pixels de mundo da máscara.
4. Elevada pelo modelo de câmara e levada ao mundo pela pose.
5. Cada ponto carrega a cor do pixel.

Um quadro que está posicionado mas não tem escala de profundidade é contado como *posicionado*, mas não *fundido*.

## O volume de superfície {#the-surface-volume}

`SurfaceVolume(voxel=0.25)` - o voxel é o "Surface detail" (detalhe da superfície) da janela.

### Ocupação ponderada, não um TSDF {#weighted-occupancy-not-a-tsdf}

Um campo de distância com sinal truncado (TSDF) escava ao longo do raio de cada pixel e acerta paredes finas e espaço livre limpo, porque sabe que um raio passou *através* de um espaço vazio. Isso significa percorrer o raio para cada um de centenas de milhões de pixels. Este volume, em vez disso, acumula **ocupação ponderada** por voxel e executa marching cubes no resultado suavizado: rápido o bastante para correr durante a digitalização, numa máquina sem GPU utilizável, e a saída é uma superfície fechada e não uma nuvem de pontos. O custo: estruturas finas e espaço livre ficam piores do que um TSDF obteria.

### Integrando um quadro {#integrating-a-frame}

- Os pontos são agrupados em voxels (`floor(ponto / voxel)`).
- Cada voxel tocado recebe `peso x sqrt(contagem / contagem_máxima)`, onde `contagem` é quantos pontos do quadro caíram nele e `peso = max(0,1, confiança da pose)`. Raiz quadrada: depois de um certo ponto, mais pixels da mesma superfície, do mesmo lugar, deixam de ser evidência; ponderar pela confiança da pose impede que uma pose duvidosa empurre a superfície para o lugar errado.
- A cor é uma média ponderada corrente por voxel.

A grade é **esparsa**: uma rota percorrida toca uma fração minúscula da sua caixa delimitadora. As coordenadas do voxel são empacotadas numa única chave de 64 bits (21 bits por eixo, até ±1.048.575 voxels - a 0,25 m, cerca de ±262 km) e consultadas com um array ordenado e busca binária, totalmente vetorizadas.

### Extraindo a malha {#extracting-the-mesh}

1. Voxels com peso abaixo de **0,35** são descartados (pontos isolados perdidos nas bordas da silhueta virariam espinhos).
2. Os pesos são escalados pelo **75º percentil** da digitalização e limitados a 1.
3. O espaço ocupado é cortado em **blocos de 64 voxels** por lado, cada um montado com uma **margem de 3 voxels** dos dados dos vizinhos (sem ela, cada borda de bloco se fecharia numa parede, e uma estrada sairia como uma fileira de caixas).
4. O campo de cada bloco é suavizado com um Gaussiano (sigma 0,8 voxel) para remover a rugosidade que o ruído de profundidade deixa.
5. **Primeira passagem**: o 99º percentil do campo suavizado, amostrado em todos os blocos (no máximo 2 milhões de valores), define uma escala de nível global. Normalizar por bloco promoveria um outlier isolado a uma superfície inteira no seu próprio bloco vazio.
6. **Segunda passagem**: o campo de cada bloco, dividido por essa escala, com marching cubes em **0,5**. Um triângulo pertence ao bloco onde cai o seu **centroide**, então triângulos que cruzam uma junção são emitidos exatamente uma vez.
7. Os vértices vão para unidades do mundo nos centros dos voxels; cada vértice recebe a cor do seu voxel (cinza médio onde cai fora de um voxel ocupado).

A extração bloco a bloco é o que torna possível uma digitalização do tamanho de uma pista: um único array denso sobre uma caixa de um quilómetro quadrado a 0,25 m teria bilhões de células. `tests/test_track_scale.py` garante que funciona nessa escala, com memória proporcional ao que foi digitalizado.

### Chão e estrutura {#ground-and-structure}

`classify` rotula cada triângulo pela sua normal (orientada pelas normais dos vértices extraídos): a até **35 graus da vertical para cima** é `ground` (chão), todo o resto é `structure` (estrutura). O visualizador desenha o chão sólido e as estruturas quase transparentes. **A água nunca é reivindicada** - ela não pode ser distinguida do chão plano pela forma, e um rótulo errado faria um pátio aparecer como um lago. Cada rótulo vira uma parte do `.glb` ([A saída .glb](glb-output.md)).

## Cobertura {#coverage}

`CoverageGrid(voxel=0.5)` regista, por célula de meio metro, quatro coisas que não são a mesma coisa:

| Termo | Guardado | Pontuação (cada uma limitada a 0..1) | Por que conta separadamente |
|---|---|---|---|
| Quantas vezes foi visto | contagem de quadros-chave que viram a célula | `contagem / 3` | uma vez é um palpite sem nada com que fazer a média |
| De quantas direções | soma dos vetores unitários de visão | `(1 - dispersão) / (1 - 0,93)`, onde dispersão = comprimento da soma / contagem | vinte quadros a andar direto para uma parede não têm paralaxe entre si; duas vistas separadas por trinta graus valem mais |
| De quão longe | distância de visão mais próxima | `1 - mais próxima / 40 m` | o erro de profundidade cresce aproximadamente com o quadrado da distância |
| Quão bem a câmara estava posicionada | melhor confiança da pose | a própria confiança | geometria fundida com uma pose duvidosa cai no lugar errado |

Os pontos de um quadro são agrupados por célula primeiro, então dez mil pixels de uma parede contam como uma observação de uma direção.

**Qualidade = o produto dos quatro termos**, não a média: são condições que precisam valer cada uma. Um lugar visto duzentas vezes de uma só direção a sessenta metros está mal observado, e uma média esconderia isso atrás de um termo excelente.

Números de resumo (`summary`): células ocupadas, a fração com qualidade de pelo menos 0,5 ("% bem visto" na janela), qualidade média e volume.

### Pontos fracos {#weak-spots}

`weak_spots(threshold=0.35, min_cluster=8, limit=8)`:

1. células com qualidade abaixo de 0,35 são fracas;
2. as células fracas são agrupadas por **conectividade** (vizinhança de 26, union-find só sobre as células ocupadas - não uma varredura sobre a caixa delimitadora, que numa rota longa são milhões de células vazias);
3. grupos com menos de 8 células são ignorados;
4. o motivo de cada grupo é o *termo fraco* mais comum entre as suas células, e a sua posição é a média das suas células;
5. ordenados do maior para o menor (depois pela pior qualidade), no máximo 8.

| Motivo | Conselho apresentado |
|---|---|
| poucas vistas | Visto só uma ou duas vezes - passe por ele de novo. |
| uma direção | Visto só de um ângulo. Dê um passo para o lado e olhe de novo. |
| distante | Visto só de longe. Chegue mais perto. |
| seguimento ruim | A câmara não foi bem localizada aqui. Aproxime-se mais devagar. |

A conectividade importa: agrupar por uma grade de blocos fixa reporta uma sala lateral negligenciada como vários anéis separados, e ninguém consegue distinguir oito lugares de um só lugar contado oito vezes.

### A vista de planta {#the-plan-view}

`top_down(resolution)` projeta as células em x/z e mantém a **melhor** qualidade por coluna (alguém parado numa sala tem pouca cobertura do teto e excelente cobertura do chão; uma média pintaria a sala de âmbar). Colunas nunca observadas são marcadas à parte. A janela desenha em 200 x 200, a sobreposição em 120 x 120 ([A janela de digitalização](reconstruction-scan-ui.md#the-coverage-map)).

### Isto é reconstruível? {#is-this-reconstructable}

A cada 25 quadros fundidos, quando há pelo menos 500 células:

| Conclusão | Veredito | Mensagem (resumida) |
|---|---|---|
| menos de 2% das células têm dispersão de visão abaixo de 0,93 | não reconstruível | Quase nenhuma paralaxe. Ou a câmara nunca olha para o lado, ou o seguimento está a derivar, então a mesma superfície nunca cai duas vezes no mesmo lugar. Verifique a contagem de quadros posicionados: se ela for alta, é deriva. |
| mediana da distância mais próxima acima de 25 m | não reconstruível | Tudo foi visto a N m de distância ou mais... Chegue mais perto do que quer. |
| menos de 6% com boa dispersão | reconstruível, com aviso | Paralaxe fraca - a geometria ficará grosseira. Mover-se de lado em relação ao que se olha ajuda mais. |

A baixa paralaxe tem duas causas que isto não consegue distinguir, e é por isso que a mensagem cita as duas.

## Cor {#colour}

A cor por voxel da fusão é barata e ao vivo, e borrada: cada pixel de uma célula de um quarto de metro é uma média, inclusive os vistos de lado a trinta metros. Então, na exportação, a malha é colorida de novo, uma vez, a partir dos próprios quadros:

- **Quadros guardados**: até **160** quadros-chave (imagem e pose), escolhidos por amostragem de reservatório para se espalhar pela digitalização inteiro em vez de na sua cauda.
- **Por vértice** (`project_colours`), cada quadro guardado contribui se o vértice estiver na frente da câmara e dentro da imagem, a superfície estiver voltada no máximo a cerca de 70 graus de frente para a câmara (`|normal . visão| > 0,34`), estiver mais perto que **35 m**, e nada mais próximo estiver na frente dele (abaixo).
- Cada visão assim recebe a pontuação `frente x (1 - distância / 35)`, então uma visão de frente e de perto vence uma visão distante e rasante. As **4 visões de maior pontuação** de cada vértice são mantidas - seja qual for a ordem dos quadros, uma visão melhor substitui a mais fraca das quatro - e misturadas, ponderadas por essa mesma pontuação.
- **Oclusão**: em cada quadro, os próprios vértices da malha que estão na vista são desenhados num buffer de profundidade de células de 2 pixels, a guardar o mais próximo de cada célula. Um vértice mais de `0,3 m + 5%` da sua distância atrás do mais próximo da sua célula estava escondido naquele quadro - uma parede entre a câmara e a estrada além - e aquela visão não conta nada. O teste só conhece a malha: um oclusor que nunca foi fundido (um carro passando, um pilar da cabine fora da máscara do HUD) não é detetado.
- Um vértice que nenhum quadro viu mantém a cor do seu voxel; um vértice sem nenhum dos dois fica cinza médio (preto pareceria um buraco).

A cor é gravada como `COLOR_0` por vértice, não como um atlas de textura. O visual padrão do visualizador é um mapa cinza sob calor saturado; a cor serve para encontrar a estrada numa pista digitalizada, onde a geometria sozinha não separa a pista da beira, e aparece atrás da opção **Cor capturada** do painel Fundo / nível do visualizador. Um atlas multiplicaria o tamanho do ficheiro e precisaria de um desdobrador, para uma visão que deliberadamente não é o padrão. O Blender e outras ferramentas glTF leem `COLOR_0`.
