---
title: "Pose da câmara e escala"
nav_order: 4
lang: "pt"
source: reconstruction-pose.md
source_hash: "b4e80fd24449"
nav_exclude: true
search_exclude: true
---
# Pose da câmara e escala {#camera-pose-and-scale}

Um mapa de profundidade diz quão longe as coisas estão de *um* ponto de vista. Para transformar muitos deles num só nível, é preciso saber onde estava cada ponto de vista, e em que unidades. Esta página trata dos caminhos ao vivo; a solução offline por feed-forward está em [Reconstrução offline](reconstruction-offline.md).

Código: [`pose/odometry.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/odometry.py),
[`pose/telemetry_pose.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/telemetry_pose.py),
[`pose/groundscale.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/groundscale.py),
[`pose/bundle.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/bundle.py),
[`pose/tracks.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/tracks.py),
[`pose/windowed.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/pose/windowed.py).

## O modelo de câmara {#the-camera-model}

`Intrinsics.from_fov(width, height, fov)` monta uma câmara pinhole a partir do **campo de visão horizontal** que se define na janela: `fx = (width / 2) / tan(fov / 2)`, pixels quadrados (`fy = fx`), o ponto principal no centro do quadro. Um jogo não publica a sua projeção, então este é o único número presumido: estreito demais e a cena parece mais funda do que é. O caminho offline usa 65 graus.

Uma `Pose` é guardada **mundo-da-câmara**: `rotation` (3 x 3) e `translation` = o centro da câmara no mundo, que é o que a trajetória, o mapa de cobertura e a sobreposição precisam.

## Odometria visual (o padrão) {#visual-odometry-the-default}

`VisualOdometry` rastreia cada quadro-chave em relação ao anterior:

1. **Características**: ORB, até 1500 por quadro, detetadas só na máscara do mundo (veja [Captura](reconstruction-capture.md#what-is-not-the-world)).
2. **Correspondências** com o quadro-chave anterior: força bruta, distância de Hamming, com verificação cruzada (só pares mutuamente melhores).
3. **Elevação para 3D**: a profundidade do quadro anterior já está em unidades do mundo, então seus pixels emparelhados viram pontos do mundo.
4. **Posicionar a câmara**: `solvePnPRansac` entre esses pontos (erro de reprojeção de 3 px, confiança 0,999, 200 iterações). A translação sai nas mesmas unidades, então **a escala atravessa o intervalo**.
5. **Ancorar a profundidade deste quadro**: a sua própria profundidade inversa prevista é ajustada (`fit_scale`) contra as profundidades dos inliers do PnP, e o ciclo se repete.

O **primeiro quadro** é a origem: pose identidade, e a sua afim de profundidade é ou a calibração pelo chão abaixo, ou, sem ela, a identidade (a reconstrução fica então consistente consigo mesma, mas sem unidade).

Uma pose precisa de pelo menos **18 inliers do RANSAC** - bem mais que o mínimo de seis do PnP, já que uma solução com pontos apenas suficientes é exatamente a que está confiantemente errada.

### Confiança {#confidence}

Cada quadro posicionado recebe uma confiança entre 0 e 1 que pondera a sua fusão e a sua cobertura:

| Pose vinda de | Confiança |
|---|---|
| telemetria | 1,0 |
| uma solução feed-forward | 0,85 |
| seguimento visual | `inliers / casamentos x min(1, inliers / 60)` |

### Quando o seguimento quebra {#when-tracking-breaks}

Um quadro que não pode ser posicionado é reportado, nunca chutado: `no features in the frame (N found)`, `too few matches to place the camera`, `could not relocalise`. Nenhuma pose é registada, e nada é fundido. Continuar a partir da última pose, ou começar uma nova origem, colocaria o trecho seguinte do nível num deslocamento arbitrário - uma costura que parece geometria real.

Depois de uma quebra, cada novo quadro é **relocalizado** contra um conjunto de quadros-chave passados (cada 4.º quadro seguido é adicionado, até 120, descartando o mais antigo), do mais recente para o mais antigo, com o mesmo passo de correspondência e PnP. Enquanto nenhum funciona, os quadros são descartados. Um quadro recuperado continua no mesmo sistema de coordenadas. As recuperações são contadas e mostradas na janela (`N recovered`).

### Fecho de ciclo: desligado {#loop-closure-off}

O mesmo conjunto suporta o fecho de ciclo: emparelhar com quadros-chave de muito antes para detetar uma revisita e puxar a trajetória de volta para cima dela. **Está desligado por padrão, e o digitalizador nunca o liga** (`Reconstructor(loop_closure=False)`). Em cenários repetitivos - uma etapa de rali, um corredor, uma fileira de árvores - cada trecho parece com todos os outros, e o correspondência de características confirma revisitas falsas, o que prende a câmara perto de onde começou enquanto ela segue em frente. Fazê-lo bem exige reconhecimento de lugar (um vocabulário de bag-of-words ou um descritor aprendido) e verificação geométrica contra um mapa, o que não está construído.

Quando ligado a partir do código, um fecho precisa de: um quadro-chave com pelo menos 60 quadros-chave de idade, a menos de 6 m da pose atual, emparelhado com pelo menos 90 inliers, movendo a pose em mais de 0,02 m e menos de 6 m. Mesmo assim, ele só substitui a pose atual; não é um grafo de poses e não move quadros anteriores nem a geometria já fundida.

## Poses da telemetria {#telemetry-poses}

Com **Racing telemetry (Forza) -> Listen for position data** ligado, o caminho da câmara vem do Data Out do Forza em vez das imagens (`ForzaPoseSource`):

- Uma thread escuta em `127.0.0.1:<porta>` (5300 por padrão) com a mesma deteção de layout dos gravadores ([Forza](telemetry-forza.md)); os pacotes são usados enquanto `isRaceOn` estiver ligado. Uma porta ocupada é reportada, não levantada como exceção: a telemetria é um complemento e a digitalização segue visualmente.
- Cada pacote é carimbado com o **tempo monotônico em que chegou** - o mesmo relógio com que a captura carimba os quadros. O timestamp próprio do jogo conta a partir de algo sem relação, então não é usado para o alinhamento. Um jitter de loopback de um ou dois milissegundos equivale a cerca de 6 cm a 200 km/h.
- Um buffer rolante de 30 segundos é mantido. A pose de um quadro é **interpolada** das amostras de cada lado do seu instante de captura: posição linear, rotação por interpolação esférica (uma matriz mesclada não é uma rotação e deformaria todos os pontos). Através de uma lacuna maior que **0,35 s**, ou fora do buffer, não há pose.
- `pose_from_forza`: a câmara é posicionada no carro (o deslocamento de uma câmara de perseguição não é publicado). **As posições são mantidas exatamente como o jogo as envia**: o mundo do Forza já é Y para cima (x e z pelo mapa, y a altura), que é como os ficheiros de volta e de rota o escrevem, então a superfície cai nas mesmas coordenadas das voltas gravadas sobre ela. (Uma versão anterior trocava y e z para um mundo "Z para cima" e deitava a pista de lado.)
- A rotação é guinada, arfagem e deslocação, nesta ordem, com os sentidos lidos de voltas gravadas: a direção de movimento `atan2(dx, dz)` é igual à guinada, a subida do terreno é igual a menos a arfagem (positiva é nariz para baixo), e a deslocação é positiva quando a suspensão do lado direito está comprimida (positiva abaixa o lado direito). Os eixos do carro (x para a direita, y para cima, z para a frente) são então convertidos nos da câmara (x para a direita, y para baixo, z para a frente) invertendo y.
- O mundo do Forza é **canhoto** e o referencial da câmara não é, então a matriz mundo-da-câmara resultante é uma reflexão (determinante -1), e a digitalização sai canhoto como os ficheiros de volta. A interpolação não é afetada (a curva entre duas dessas poses é uma rotação própria).
- Quando um quadro não tem pose de telemetria (uma lacuna), o reconstrutor recorre ao **seguimento visual** para aquele quadro, continuando a partir da última pose de telemetria, e volta às poses do feed assim que ele responde. O PnP só devolve rotações, então num mundo espelhado ele é resolvido com o mundo espelhado em z e o espelho dobrado de volta; o quadro cai nas coordenadas do jogo. Só se o seguimento visual também falhar o quadro fica sem seguimento.

### Escala de profundidade a partir da telemetria {#depth-scale-from-telemetry}

O jogo diz onde está a câmara, não o quão longe estão as coisas, então a profundidade de cada quadro ainda precisa ser ancorada - mas não encadeando a partir do quadro zero, cuja unidade é arbitrária enquanto as poses estão em metros. Em vez disso, as características emparelhadas entre o quadro anterior e o atual (pelo menos 8) são **triangulados diretamente a partir das duas poses conhecidas**, em metros, e o mapa de profundidade é ajustado aos pontos na frente da câmara. Cada quadro é ancorado contra a telemetria, então não há cadeia que derive.

Se as duas poses estão a menos de **0,05 m** uma da outra, os raios são quase paralelos e a triangulação é ruído, então o quadro fica sem ancoragem: posicionado com exatidão, mas não fundido ("positioned, but its depth has no scale yet"). É por isso que a janela conta os quadros *posicionados* e os *fundidos* separadamente.

## Escala {#scale}

A odometria visual encadeia corretamente a escala relativa, mas o nível inteiro ainda flutua num fator desconhecido. A saída relativa do Depth Anything sai em unidades arbitrárias, então deixar o primeiro quadro na identidade põe o mundo a metros da câmara num tamanho arbitrário.

`GroundCalibrator` fixa esse fator a partir de **quão alta a câmara está acima do chão**, medido no **primeiro quadro-chave** e, quando ele não tem chão utilizável, nos seguintes:

- Altura da câmara: **1,15 m** (a linha dos olhos de um motorista) - a janela sempre usa esse valor; scripts podem passar 1,70 m (`WALKING_HEIGHT`, um jogador em pé) ou `None` (sem calibração).
- Amostra do chão: linhas de 62% a 92% da altura do quadro (abaixo do horizonte, acima do capô ou da arma) e colunas de 30% a 70% da largura (longe das beiras).
- Cada pixel ali com uma previsão utilizável é elevado com profundidade `1 / predicted` nas unidades da rede; pontos abaixo do eixo óptico dão uma altura abaixo da câmara. A mediana deles é a altura da câmara nas unidades da rede, então `metros por unidade = 1,15 / mediana`, e a afim do quadro é `scale = 1 / metros_por_unidade`, deslocamento 0.
- Só é confiável com pelo menos 200 amostras de chão e uma **dispersão** (desvio absoluto mediano sobre a mediana) abaixo de **0,60**.
- No primeiro quadro-chave, o ajuste vira a unidade da origem, então a digitalização está em metros desde o início. Quando o primeiro quadro-chave não tem chão utilizável, a digitalização começa sem unidade e cada quadro-chave seguido seguinte é tentado, até **30 quadros** no total. O primeiro que calibra dá *metros por unidade*: a mediana, sobre a faixa do chão, da profundidade que o chão implica dividida pela profundidade que a cadeia deu àquele quadro. Tudo já fundido está na unidade do primeiro quadro, então o fator não é realimentado na cadeia; ele é aplicado ao nível inteiro (e aos pontos marcados) quando é escrito, e à distância mostrada enquanto isso. O tamanho do voxel fica então nas unidades do primeiro quadro, então o seu tamanho em metros difere da definição por esse fator.
- Depois de 30 quadros sem chão, a digitalização fica sem unidade, e diz isso.
- Com telemetria, os quadros-chave seguintes não são tentados: a profundidade é ancorada aos metros da telemetria.

Estar dentro de dez por cento do tamanho real é melhor que estar errado por um fator de mil; a telemetria, quando disponível, torna isso desnecessário. A nota aparece na janela sob a linha de seguimento, como `Size: ...`: `measuring the ground`, `no flat ground in view yet - still looking (N frames tried)`, `scaled from a 1.15 m camera height, ...` (com `found on frame N, so the level is scaled by F when it is written` quando veio depois), `no usable ground in the first N frames - sizes are relative, not metres`, ou `in metres, from the telemetry's positions`.

## Ajuste de feixes e trilhas longas (não conectados) {#bundle-adjustment-and-long-tracks-not-wired-in}

Duas peças existem para um futuro solver em janelas e **não são usadas pelo digitalizador**:

- **`FeatureTracks`** mantém a identidade das características ao longo de centenas de quadros com seguimento Lucas-Kanade (600 características, semeadas de novo abaixo de 60%, tolerância de ida e volta de 1 px, novas características a 10 px de outras existentes), que é o que o ajuste de feixes precisa - o correspondência de descritores entre quadros consecutivos só dá pares.
- **`bundle_adjust`** refina uma janela de poses e pontos juntos com `scipy.optimize.least_squares` (região de confiança, perda soft-L1 com escala de 2 px, padrão de esparsidade do jacobiano explícito, câmaras fixas restauradas exatamente). Testado contra verdades conhecidas em `tests/test_bundle.py`.

`WindowedOdometry` combina os dois (janelas de 12 quadros-chave, uma solução a cada 3 quadros-chave, as duas primeiras câmaras fixas, pontos com mais de 6 px de erro descartados, saltos de mais de 6 vezes o passo recente recusados). A sua docstring regista que, em filmagens reais, ele **colapsou a trajetória e foi muito mais lento** que o seguimento quadro a quadro, com a liberdade de escala (gauge) e um bootstrap baseado em profundidade como causas conhecidas e uma terceira causa não identificada. Então a odometria quadro a quadro continua a ser o padrão; a correção provável indicada no código é um bootstrap de matriz essencial de duas vistas, com a linha de base fixada pela calibração do plano do chão.
