---
title: "Captura, máscaras e qualidade do quadro"
nav_order: 2
lang: "pt"
source: reconstruction-capture.md
source_hash: "986c2c1fa3ca"
nav_exclude: true
search_exclude: true
---
# Captura, máscaras e qualidade do quadro {#capture-masks-and-frame-quality}

Código: [`capture/sources.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/sources.py),
[`capture/screenmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/screenmask.py),
[`capture/flowmask.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/flowmask.py),
[`capture/quality.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/capture/quality.py),
[`scan/session.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/scan/session.py).

## De onde vêm os quadros {#where-frames-come-from}

Um alvo de fonte é um dos seguintes:

| Alvo | Fonte | Observações |
|---|---|---|
| `monitor:<n>` | um monitor inteiro, ao vivo | a opção "Whole screen" da janela, com o número em "Which" |
| `window:<title>` | uma janela, ao vivo | a opção "A window" da janela, com o título dela |
| um caminho de ficheiro | um ficheiro de vídeo | a opção "A video file" da janela; qualquer formato que o OpenCV consiga ler |

### Captura ao vivo: Windows Graphics Capture {#live-capture-windows-graphics-capture}

`WindowSource` usa o pacote `windows-capture`, que encapsula o **Windows Graphics Capture** - a API pública que os gravadores de ecrã usam. Nada é injetado no jogo. O cursor não é capturado e nenhuma borda amarela de captura é desenhada.

A biblioteca de captura entrega os quadros a um callback na thread do compositor e espera que ele retorne imediatamente, então o callback só copia o quadro (o buffer é reaproveitado), converte BGRA para RGB, redimensiona, carimba e o coloca numa fila de **4 quadros**. Quando a fila está cheia, o **quadro mais antigo é descartado** e um contador sobe: ficar para trás deve custar quadros, não memória nem corretude, e a visão ao vivo deve mostrar onde o jogador está agora. Os quadros descartados aparecem na linha de estatísticas da janela, e se mais da metade for descartada aparece uma dica.

Cada quadro traz `t` (segundos desde o início da captura) e `monotonic` (o `time.monotonic()` bruto na captura), o mesmo relógio com que os pacotes de telemetria são carimbados - é isso que permite alinhar as poses do Forza aos quadros.

`windows-capture` é opcional na verificação de dependências: sem ele, um ficheiro de vídeo ainda pode ser digitalizado.

### Ficheiros de vídeo {#video-files}

`VideoSource` lê com o OpenCV, converte para RGB e redimensiona. Um contentor sem taxa de quadros é tratado como 30 fps. Os carimbos de tempo são o índice do quadro dividido pela taxa; um ficheiro não tem tempo de relógio, então a telemetria não pode ser alinhada a um vídeo.

### Resolução {#resolution}

Os quadros são redimensionados na fonte para que o lado maior seja o lado de captura da padrão (Draft 640, Balanced 960, Detailed 1280 px), com interpolação por área. Um quadro 4K tem trinta vezes os pixels que o modelo de profundidade usa.

## Quadros-chave {#keyframes}

Quase todo quadro de uma captura é redundante: ficar parado produz centenas de vistas de uma mesma coisa. O que a reconstrução quer é *paralaxe*. Então um quadro é guardado com base em **quanto a imagem mudou desde o último quadro guardado**, não num cronómetro.

`picture_change(a, b)`:

1. os dois quadros viram cinza e são reduzidos a uma grade de 16 x 16 de médias de blocos (médias de blocos reagem à imagem se movendo, não a granulação, folhagem, cintilação ou HUD);
2. a diferença absoluta média, como fração de 255;
3. quando uma máscara do mundo é conhecida, cada bloco é ponderado pela fração dele que é mundo, e não cabine, então um bloco metade painel conta como meio (usado quando a máscara cobre mais de 5% do peso da grade).

O limiar **se adapta à captura**: nos primeiros 30 quadros é o valor inicial da padrão (0,020 / 0,010 / 0,004); depois é o quantil da padrão (0,85 / 0,65 / 0,40) das últimas 240 mudanças medidas, nunca abaixo de 0,0001. Um quadro é guardado quando a sua mudança atinge o limiar; o primeiro quadro é sempre guardado. Um limiar fixo não funciona entre cenas - a mudança de quadro para quadro de uma volta com cabine escura é uma pequena fração da de uma sala brilhante e texturizada -, enquanto "guardar o terço mais movimentado" significa o mesmo nas duas. O limiar em uso sai com cada atualização de progresso (`ScanProgress.threshold`), e as barras de velocidade de caminhada na janela e na sobreposição medem a última mudança contra ele (`ScanProgress.toward_next_view`).

Só os quadros guardados passam pelo modelo de profundidade e pela reconstrução. Os quadros não são armazenados a menos que quem chama peça (`keep_frames`); 160 deles são guardados para colorir a malha (veja [cor](reconstruction-fusion-and-texture.md#colour)).

Uma digitalização termina quando é parado, quando um vídeo acaba, ou no limite de tempo ou de quadros-chave.

## O que não é o mundo {#what-is-not-the-world}

Duas coisas num quadro do jogo não são geometria do nível, e ambas arruínam uma reconstrução:

- **O HUD.** Uma mira é o elemento mais repetível de qualquer quadro. Um emparelhador de características a adora: ela casa perfeitamente entre cada par de quadros, e cada correspondência é evidência de que a câmara não se moveu - o que comprime a reconstrução inteira.
- **Coisas presas à câmara.** Uma arma, um capô, a armação da cabine, um painel. Geometria real no sistema de coordenadas errado: fundida, arrasta-se ao longo de todo o caminho percorrido.

Dois detetores as encontram. Ambos produzem uma máscara (255 = mundo, 0 = não mundo) ou `None` enquanto não há evidência suficiente; e `None` sempre significa "use tudo", nunca "não use nada".

A máscara é aplicada:

- na **deteção de características** da odometria visual (mascarar uma mira na saída enquanto ela ainda vota na pose corrigiria o sintoma visível e manteria o dano real);
- aos **pixels fundidos**, para que nenhuma geometria da cabine seja fundida;
- à medida de **nitidez e brilho**, porque uma cabine é sempre perfeitamente nítida;
- à **mudança de imagem** que decide os quadros-chave.

Ela **não** é aplicada aos quadros dados ao solver VGGT offline (veja [Reconstrução offline](reconstruction-offline.md#the-camera-mask-is-learned-not-applied)).

### ScreenMask: o que não muda {#screenmask-what-does-not-change}

Usado do primeiro quadro-chave até ao FlowMask estar pronto.

- Cada quadro vira cinza, é reduzido à metade e desfocado (Gaussiano 3 x 3) para que um tremor de um pixel num elemento estático do HUD não pareça movimento.
- A diferença absoluta por pixel em relação ao quadro anterior é acumulada numa média exponencial (decaimento 0,9), para que a máscara acompanhe um HUD que aparece ou some no meio da digitalização.
- Ele só aprende com quadros em que a câmara está sabidamente a mover-se (na digitalização: depois que pelo menos um quadro foi seguido) - uma câmara parada deixa tudo estático.
- Depois de **12** quadros de aprendizado, um pixel é estático quando a sua mudança média é abaixo de **0,22** da mudança mediana do quadro - relativo, então o limiar acompanha a velocidade com que o jogador se move.
- Se mais de **45%** do quadro for lido como estático, a premissa falhou (um menu, uma cena) e nada é mascarado.
- A máscara é erodida num pixel (as bordas serrilhadas do HUD não pertencem a nenhum dos lados) e reescalada ao tamanho total.

A nota dela na janela: `learning what is HUD (n/12 frames)`, `no HUD or attached geometry detected`, ou `ignoring N% of the frame — HUD or camera-mounted`.

### FlowMask: o que nunca se desloca {#flowmask-what-never-travels}

Uma cabine não é estática: agulhas se movem, o conta-rotações oscila, o minimapa gira, então um detetor de mudança classifica esses pixels como mundo - e são as piores características para entregar a um solver de pose. O FlowMask faz a pergunta melhor: **quais características persistem sem se deslocar?**

- Na captura ao vivo ele aprende uma única vez, a partir dos primeiros **40 quadros-chave** (em escala de cinza); depois substitui o ScreenMask pelo resto da digitalização.
- Os quadros são cortados em janelas de **30** quadros, sobrepostas pela metade. Em cada janela, até 800 cantos são semeados (`goodFeaturesToTrack`, qualidade 0,01, 8 px de distância) e seguidos com Lucas-Kanade piramidal (21 x 21, 4 níveis) com uma **verificação para frente e para trás**: um rasto cujo fluxo de volta não cai a 1 px de onde começou é descartado, porque um seguidor que deriva para um padrão vizinho fabricaria exatamente a assinatura "persistente mas parada" que se procura. Janelas com menos de 20 quadros são saltadas. Janelas curtas importam: numa corrida longa quase toda característica do mundo sai do quadro e a evidência se esvazia.
- O deslocamento líquido de cada característica sobrevivente é comparado com **2% da largura do quadro**: abaixo disso, ela está "parada"; acima, "se movendo". As contagens são acumuladas numa grade de **24 x 24** células do ecrã, pelo lugar onde cada característica começou.
- Uma célula é bloqueada quando tem pelo menos 2 características paradas e mais paradas do que móveis, **e** pelo menos 3 dos seus 8 vizinhos também estão bloqueados (uma célula isolada é ruído; imagens escuras produzem muitas delas).
- Só as regiões bloqueadas **conectadas à borda do quadro** são mantidas. Tudo o que está preso à câmara chega a uma borda do ecrã; o que fica no meio e não se desloca é o ponto de fuga - a conduzir para a frente, a estrada reta à frente não tem fluxo e é a geometria mais desejada.
- A região sobrevivente cresce uma célula (a borda de um painel de instrumentos é um gradiente).
- Se mais de **60%** do quadro seria mascarado, nada é mascarado: em imagens noturnas a maioria das células não tem característica rastreável, o que se lê igual a um mostrador.

A nota dele: `watching what moves`, `nothing attached to the camera`, `ignoring N% of the frame — it never travels`, ou, acima de 60%, uma mensagem explicando que ele não mascara nada.

O caminho offline aprende o mesmo FlowMask a partir de 4 execuções de 90 quadros consecutivos espalhadas pelo vídeo, em 960 x 540 ([Offline](reconstruction-offline.md)).

## Qualidade do quadro e conselhos {#frame-quality-and-advice}

`QualityWatcher` avalia cada quadro-chave e escolhe **uma** instrução, para que a sobreposição possa dizer "devagar" enquanto ainda há tempo.

Por quadro ele mede, só nos pixels do mundo (todos os pixels se a máscara deixar menos de 5%):

- **nitidez**: variância do Laplaciano - a medida padrão de uma passagem, e responde exatamente ao que o desfoque de movimento destrói;
- **luminância**: nível de cinza médio, 0-255.

A nitidez não tem escala absoluta (uma fase noturna e uma rua iluminada diferem numa ordem de grandeza, ambas em foco), então ela é julgada contra a **mediana corrente desta captura**: os últimos 90 quadros, precisando de 20 antes de qualquer julgamento. Cada quadro é comparado com o histórico *antes* de ser acrescentado, para que um longo trecho borrado não arraste a mediana até se igualar a si mesmo.

| Condição | Teste |
|---|---|
| plano | nitidez de no máximo 1,0 (um ecrã de carregamento, uma parede, o céu) |
| escuro | luminância abaixo de 26 |
| borrado | nitidez abaixo de 0,55 da mediana, e não plano |

O conselho, primeira condição que bate vence (ordenado pelo que mais bloqueia a digitalização):

| Situação | Conselho | Nível |
|---|---|---|
| menos de 20 quadros | A apanhar o jeito da imagem… | ok |
| plano | Nada para medir - aponte a câmara para o nível, não para o céu. | parar |
| escuro | Escuro demais para reconstruir. Acenda os faróis, ou dirija este trecho de dia. | parar |
| borrado | Borrado - diminua a velocidade. | alerta |
| menos da metade dos quadros seguidos | A perder o seguimento - diminua a velocidade e mantenha mais do nível no ecrã. | alerta |
| menos de 40% dos quadros seguidos fundidos | As posições estão boas, mas a profundidade não está a funcionar. Dirija mais perto do cenário. | alerta |
| existem pontos fracos | N pontos fracos - o mapa os marca. | ok |
| caso contrário | Bom - continue. | ok |

O nível colore a orientação da sobreposição (verde / âmbar / vermelho). A barra de **nitidez** da sobreposição é a nitidez do quadro em relação à mediana. (O código também tem "Borrado, e a câmara não está a mover-se. Verifique a captura." para uma câmara parada; a digitalização sempre informa a câmara como em movimento, então essa mensagem não aparece.)
