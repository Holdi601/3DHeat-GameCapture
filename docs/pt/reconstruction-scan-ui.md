---
title: "A janela de digitalização"
nav_order: 1
lang: "pt"
source: reconstruction-scan-ui.md
source_hash: "829cfd5ef4de"
nav_exclude: true
search_exclude: true
---
# A janela de digitalização {#the-scan-window}

```bash
python -m heat3d_capture.ui        # ou faça duplo clique em scan.bat
```

Código: [`ui/app.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/app.py),
[`ui/overlay.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/overlay.py),
[`ui/hotkeys.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/hotkeys.py),
[`ui/preview.py`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/heat3d_capture/ui/preview.py).
A janela é uma vista simples sobre `scan/session.py` e `scan/reconstruct.py`; não tem lógica de
digitalização nem de geometria.

## Inicialização {#starting-up}

1. **Verificação de atualizações** - ver [Atualizações](updates.md).
2. **Verificação de dependências** - cada pacote que o digitalizador precisa é verificado antes de se importar
   qualquer coisa; os que faltam são listados com a sua função e o tamanho da transferência, e só são instalados
   depois de "Download and install". Cancelar sai sem alterar nada. Ver
   [Execução e dependências](runtime.md#first-run-preflight).
3. **Janela** - "3DHeat — Level digitalizador", 1420 x 900, estilo Fusion do Qt.
4. **Verificação de hardware** - é escolhido o melhor backend de inferência, o modelo de profundidade é carregado
   e a sua vazão é medida em 6 quadros; a caixa de veredicto no canto superior esquerdo diz como será o
   digitalização (ver [Execução](runtime.md#what-to-expect-from-this-machine)).
5. **As teclas de atalho globais** são registadas por último.

### Quando ainda não há modelo de profundidade {#when-there-is-no-depth-model-yet}

Se `models/` não tiver nenhum `depth-*.onnx`, o veredicto diz **"One more thing to set up."** (falta mais uma
coisa para configurar), o Iniciar fica desativado, e aparece um botão **Set up the depth model** (configurar o
modelo de profundidade). Este:

- verifica o PyTorch, o `transformers` e o `onnxscript` (cerca de 945 MB no total), e pergunta antes de instalá-los;
- executa `tools/export_onnx.py --size small` como um processo separado (para que o PyTorch nunca fique na memória
  do digitalizador), com um limite de 30 minutos. A janela não responde enquanto corre;
- em caso de sucesso, repete a verificação de hardware; em caso de falha, mostra os últimos 600 caracteres da saída
  do conversor.

Quando estão presentes vários modelos, a escolha é **pela licença, não pelo nome do ficheiro**: `depth-small-*`
(Apache-2.0, utilização comercial permitido) sempre que existe um, depois Base, depois Large (ambos não comerciais). A
caixa de veredicto e a linha cinzenta por baixo dos botões indicam o ficheiro em uso, a sua licença, e quaisquer
outros ficheiros de modelo presentes e não usados - por exemplo `Depth model: depth-small-518.onnx (Apache-2.0,
commercial use permitted); also present, not used: depth-base-518.onnx`. Para digitalizar com Base, tire o ficheiro
Small de `models/`.

## Coluna da esquerda: definições {#left-column-settings}

| Grupo | Controlo | Padrão | Intervalo / valores | O que faz |
|---|---|---|---|---|
| (topo) | Caixa de veredicto | "Checking your graphics card…" (a verificar a sua placa gráfica) | colorida a verde, âmbar ou vermelho conforme o nível | Título, `<device> via <API> — N views per second`, uma nota, e `Depth model: <file> (<licence>)` |
| O que digitalizar | Fonte | Whole screen (ecrã inteira) | Whole screen, A window, A video file | De onde vêm os quadros |
| | Which (qual) | `1` | número do monitor / título da janela / caminho para um vídeo | `monitor:<n>`, `window:<title>`, ou um caminho de ficheiro |
| | Choose file… (escolher ficheiro…) | mostrado para vídeo | `*.mp4 *.mkv *.avi *.mov` | Preenche o caminho |
| Com que cuidado | Preset (padrão de qualidade) | Balanced (equilibrado) | Draft (rascunho), Balanced (equilibrado), Detailed (detalhado) | Resolução de captura e o quão seletiva é a escolha de quadros-chave (abaixo); um resumo de uma linha aparece por baixo |
| | Game field of view (campo de visão do jogo) | 90° | 30-140° | O campo de visão **horizontal** do jogo. Se for estreito demais, o nível é reconstruído mais fundo do que é; se for largo demais, fica achatado. Os jogos de corrida ficam mais perto de 65° |
| | Surface detail (detalhe da superfície) | 0,25 m | 0,05-2,0 m, passo 0,05 | Tamanho do voxel da superfície. Mais pequeno é mais fino e mais pesado |
| Parar depois de | Time (tempo) | sem limite | 0-120 min | Termina a digitalização depois deste tempo (0 = sem limite) |
| | Views kept (vistas guardadas) | 3000 | 0-100 000 | Termina a digitalização depois deste número de quadros-chave, como proteção de memória (0 = sem limite) |
| O que ignorar | Ignore HUD and anything on the camera (ignorar o HUD e tudo o que está na câmara) | ligado | | Aprende e mascara o HUD, a mira, a arma, o capô, o cockpit ([Captura](reconstruction-capture.md#what-is-not-the-world)). A linha por baixo diz o que o detetor decide neste momento |
| Enquanto joga | Show feedback over the game (mostrar feedback sobre o jogo) | ligado | | Abre a sobreposição que deixa passar cliques enquanto digitaliza. A dica por baixo: rode o jogo em **modo janela sem bordas**; o ecrã inteiro exclusiva não pode ser desenhada por cima por nada |
| Telemetria de corrida (Forza) | Listen for position data (ouvir dados de posição) | desligado | | Toma o caminho da câmara do Data Out do Forza em vez do estimar a partir da imagem ([Pose](reconstruction-pose.md#telemetry-poses)) |
| | (porta) | 5300 | 1-65535 | A porta do Data Out |
| | (linha de estado) | | | `N packets — poses come from the game, not from the picture` (pacotes; as poses vêm do jogo, não da imagem), ou `no packets yet — check Data Out is on and pointed at 127.0.0.1` (ainda sem pacotes - verifique se o Data Out está ligado e apontado para 127.0.0.1) |
| | **Start scanning** / **Stop scanning** (iniciar / parar a digitalização) | | | Inicia ou para; mostra a tecla de atalho quando foi registada |
| | **Set up the depth model** (configurar o modelo de profundidade) | oculto | | Ver acima |
| | **Save level…** (guardar nível…) | desativado | | Ativado depois de uma digitalização que produziu voxels de superfície; pede um nome de ficheiro (padrão `scan.glb`) |
| | (linha cinzenta) | | | `Model: <file> (<licence>) · Available: <backends>` (modelo, licença, backends disponíveis), mais notas de definição como instalar o `onnxruntime-gpu` |

### Os padrões de qualidade {#the-presets}

| Padrão | Lado maior da captura | Quantil de manutenção | Limiar inicial | Resumo mostrado |
|---|---|---|---|---|
| Draft (rascunho) | 640 px | 0,85 | 0,020 | Rápido e grosseiro. Bom para verificar um percurso antes de uma digitalização a sério. |
| Balanced (equilibrado) | 960 px | 0,65 | 0,010 | A escolha habitual. Ande a um ritmo normal. |
| Detailed (detalhado) | 1280 px | 0,40 | 0,004 | Lento e minucioso. Ande de propósito e vire devagar. |

O quantil de manutenção quer dizer "guardar um quadro quando mudou mais do que este quantil das mudanças dos
últimos 240 quadros" - o Draft guarda cerca dos 15% mais ativos, o Detailed os 60% mais ativos. Ver
[Quadros-chave](reconstruction-capture.md#keyframes).

### Definições fixas na janela {#settings-that-are-fixed-in-the-window}

A janela reconstrói sempre enquanto digitaliza, usa uma altura de câmara de **1,15 m** para a escala do plano do chão
(o valor de andar, 1,70 m, não é selecionável), e deixa a ordem de backends escolher a GPU. Estes são campos de
`ScanSettings` (`camera_height`, `prefer_backend`) que só um script pode alterar.

## Coluna da direita: o que a digitalização está a fazer {#right-column-what-the-scan-is-doing}

| Elemento | Mostra |
|---|---|
| **What the camera sees** (o que a câmara vê) | o último quadro-chave |
| **Shape it is reading** (forma que está a ler) | a sua profundidade prevista, colorida com o mapa de cores Turbo, normalizada entre o 2º e o 98º percentil desse quadro (para que um pixel de céu não achate o intervalo) |
| **Coverage — where you have been, and how well** (cobertura - onde esteve, e quão bem) | uma vista em planta (ver abaixo) |
| **Worth another look** (vale a pena olhar outra vez) | os pontos fracos, numerados para corresponder aos anéis do mapa, cada um com uma instrução; do pior (maior) para o menor, no máximo 8; depois os pontos que marcou (`M1.  Marked by you, at x …, z … m — drive past again.`, ou seja, marcado por si; passe de novo) |
| Barra de velocidade de caminhada | `walk speed — N% of the way to the next view` (velocidade de caminhada - N% do caminho até a próxima vista): a mudança de imagem do último quadro dividida pelo **limiar em uso** - o valor inicial do padrão nos primeiros 30 quadros, o valor ajustado depois disso ([Quadros-chave](reconstruction-capture.md#keyframes)) |
| Linha de saúde | a saúde do seguimento, ou um aviso de captura (abaixo) |
| Linha de tamanho | `Size: ...`, como a escala do nível foi fixada ou porque não foi ([Escala](reconstruction-pose.md#scale)) |
| Linha de estatísticas | `views  frames  dropped  depth-per-second  seconds` (vistas, quadros, descartados, profundidade por segundo, segundos), e enquanto reconstrói `placed  cells  % well seen  metres` (colocados, células, % bem vistas, metros), mais `recovered` e `loops closed` (recuperados e ciclos fechados) quando algum é diferente de zero |
| Linha de teclas | as teclas registadas, ou porque não puderam ser registadas |
| Linha de dica (âmbar) | conselhos ao vivo (abaixo), a mensagem final da digitalização e as marcas |

### O mapa de cobertura {#the-coverage-map}

Redesenhado a cada 900 ms numa thread de fundo (nunca na thread da interface), em 200 x 200 células reduzidas a 420 px:

- cada coluna da grade de cobertura fica com a **melhor** qualidade de observação dentro dela (assim um chão bem visto
  não é pintado de âmbar por um teto mal visto por cima);
- a escala vai do vermelho (mau) - âmbar (fino) - amarelo (aceitável) - verde (bom);
- as células nunca observadas são de um cinzento escuro distinto, para que um canto não explorado não pareça mal
  digitalizado;
- o percurso andado é desenhado como uma linha fina e clara, a posição atual como um ponto branco;
- os pontos fracos são anéis brancos com o seu número;
- os pontos que marcou são quadrados âmbar com o rótulo `M1`, `M2`, …

Como a qualidade e os pontos fracos são calculados: [Fusão, cobertura e cor](reconstruction-fusion-and-texture.md#coverage).

### A linha de saúde {#the-health-line}

| Saúde do seguimento (quadros colocados / quadros) | Texto | Cor |
|---|---|---|
| ainda sem quadros | Waiting for the first frame. (aguardando o primeiro quadro) | cinzento |
| 90% ou mais | Tracking well — N of M quadros placed. (acompanhando bem - N de M quadros colocados) | verde |
| 60% ou mais | Tracking is patchy — N of M quadros could not be placed. Turn more slowly. (o seguimento é irregular - N de M quadros não puderam ser colocados. Vire mais devagar.) | âmbar |
| abaixo de 60% | Losing track — only N of M quadros placed. Move slowly, and avoid blank walls and sky. (perdendo o seguimento - só N de M quadros colocados. Ande devagar e evite paredes lisas e céu.) | vermelho |

Um aviso de captura da grade de cobertura substitui esta linha (vermelho quando a digitalização é considerado não
reconstruível, âmbar no resto): quase nenhuma paralaxe, tudo visto a mais de 25 m, ou paralaxe fina. Ver
[Cobertura](reconstruction-fusion-and-texture.md#is-this-reconstructable).

### A linha de dica {#the-hint-line}

| Condição | Dica |
|---|---|
| mais de metade dos quadros descartados, depois de 6 s | Falling behind — N quadros dropped ... Try Draft quality, or a coarser surface detail. (ficando para trás - N quadros descartados... Experimente a qualidade Draft, ou um detalhe de superfície mais grosseiro.) |
| menos de 0,3 vistas guardadas por segundo, depois de 8 s | Very little is being kept — you may be standing still, or looking at something featureless. Move sideways rather than turning on the spot. (quase nada está a ser guardado - pode estar parado, ou olhando para algo sem detalhe. Mova-se para o lado em vez de girar no mesmo lugar.) |
| mais de 8 vistas guardadas por segundo, depois de 8 s | Keeping a lot. Slow down a little for cleaner geometry. (a guardar muito. Desacelere um pouco para uma geometria mais limpa.) |
| digitalização terminado | a mensagem da sessão: `stopped` (parado), `finished` (terminado), `reached the Ns limit` (atingiu o limite de N segundos), `reached N keyframes` (atingiu N quadros-chave), ou `failed: <error>` (falhou) |

## Teclas de atalho {#hotkeys}

Registadas no Windows (`RegisterHotKey`), por isso funcionam enquanto o jogo tem o foco. Alt-tab para fora de um jogo em ecrã inteiro é exatamente o que estraga uma captura.

| Teclas | Ação |
|---|---|
| **Ctrl+Alt+F9** | Iniciar / parar a digitalização |
| **Ctrl+Alt+F10** | Marcar este ponto para revisitar (enquanto digitaliza) |
| **Ctrl+Alt+F11** | Mostrar / ocultar a sobreposição (alterna a caixa "Show feedback over the game") |

- São registadas uma vez, quando a janela abre, e libertadas quando fecha; enquanto estão registadas, estas
  combinações de teclas ficam indisponíveis para todos os outros programas, incluindo o jogo. As teclas F com dois modificadores
  foram escolhidas porque os jogos raramente as usam.
- A repetição automática é suprimida (`MOD_NOREPEAT`), por isso manter uma tecla premida não alterna a digitalização
  dezenas de vezes.
- Uma tecla que outro programa já tem é reportada (`... unavailable: another program already has this key`, indisponível:
  outro programa já tem esta tecla) e as outras continuam a funcionar. Um botão só anuncia uma tecla que foi
  realmente registada.
- As teclas estão fixas no código (`HOTKEY_TOGGLE`, `HOTKEY_MARK`, `HOTKEY_OVERLAY`); o analisador aceita F1-F12 com
  `ctrl`, `alt` e `shift`. Fora do Windows não há teclas de atalho globais e a janela diz isso.
- **Mark** (marcar) regista a posição atual da câmara (a do último quadro colocado) e mostra "Marked MN. Marked spots
  are on the map and saved with the level." (marcado MN. Os pontos marcados estão no mapa e são guardados com o nível.)
  Antes de qualquer quadro ter sido colocado, diz que não há onde marcar. Os pontos marcados são desenhados no mapa da
  janela e da sobreposição como quadrados âmbar com o rótulo `M1`, `M2`, …, listados por baixo dos pontos fracos,
  contados na linha de estatísticas da sobreposição, e guardados com o nível (abaixo).

## A sobreposição {#the-overlay}

Um painel pequeno fixado por cima do jogo, para que o feedback esteja onde os olhos já estão.

- Sem moldura, sempre no topo, uma janela de ferramenta (não aparece na barra de tarefas nem no alt-tab), transparente
  aos cliques no Qt e tornada transparente aos cliques no Windows (`WS_EX_TRANSPARENT | WS_EX_LAYERED`), por isso um clique
  destinado ao jogo nunca é engolido. Mostrada sem tirar o foco.
- Canto superior direito do ecrã principal, a 18 px das bordas; 214 x 358 px.
- Abre quando uma digitalização começa (se "Show feedback over the game" estiver ligado), fecha quando para.
- **Precisa do modo janela sem bordas**: nada pode ser desenhado sobre o ecrã inteiro exclusiva - nem isto, nem a
  sobreposição do Steam, nem a do Discord.

De cima para baixo mostra:

| Elemento | Conteúdo |
|---|---|
| Mapa de cobertura | 190 px, o mesmo mapa da janela numa grade mais grosseira de 120 x 120, com o percurso, os anéis dos pontos fracos e os pontos marcados |
| Saúde | o mesmo texto e cor da linha de saúde da janela |
| Estatísticas | `N placed · M to revisit · X m` (N colocados, M a revisitar, X m), com `· K marked` (K marcados) quando há algum |
| Barra de **movimento** | igual à barra de velocidade de andamento da janela: a mudança de imagem do último quadro sobre o limiar em uso, cheia quando o próximo quadro for guardado |
| Barra de **nitidez** | nitidez relativa à mediana desta própria captura: verde a partir de 0,75, âmbar a partir de 0,45, vermelho abaixo |
| Conselho | uma instrução, verde / âmbar / vermelho (a negrito quando não é "ok") - ver [qualidade do quadro](reconstruction-capture.md#frame-quality-and-advice) |
| Teclas | as teclas registadas |

Se atualizar a sobreposição alguma vez lançar uma exceção, passa para um painel vermelho **"Feedback stopped"** (feedback
parado), que diz que tudo o que foi mostrado antes está desatualizado, que a digitalização continua a correr e que a
janela principal continua correta, com o erro e uma contagem. Um painel que congelou em verde continuaria a ser lido
como confirmação.

## Guardar {#saving}

**Save level…** escreve a reconstrução como `.glb` (ver [O resultado .glb](glb-output.md)). Se o volume não produzir
nenhuma superfície, "Nothing to save" (nada para guardar) explica que o seguimento provavelmente se perdeu durante a
maior parte da digitalização. Em caso de sucesso: "Written to <path> ... Load it in 3DHeat through the Level panel."
(escrito em <caminho> ... carregue-o no 3DHeat através do painel Nível), indicando também o ficheiro de marcas quando há
pontos marcados.

Os pontos marcados são escritos ao lado do nível como **`<name>.marks.json`**:

```json
{
  "format": "heat3d-scan-marks",
  "version": 1,
  "level": "scan.glb",
  "scale": 100.0,
  "marks": [
    {"number": 1, "position": [1250.0, 115.0, -830.5], "metres": [12.5, 1.15, -8.305]}
  ]
}
```

`position` está nas coordenadas próprias do nível (a escala do GLB aplicada, para que uma marca fique sobre a malha em que
foi feita), `metres` em metros; `number` corresponde a `M1`, `M2`, … na janela. Quando a escala foi encontrada num
quadro-chave posterior ([Escala](reconstruction-pose.md#scale)), ambos incluem esse fator.

Parar uma digitalização mantém o que foi recolhido; um novo **Start** descarta a digitalização anterior.
**Fechar a janela não pergunta se quer guardar**: para a digitalização, liberta as teclas de atalho e fecha a sobreposição.
