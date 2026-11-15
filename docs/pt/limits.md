---
title: "Limites e verificação"
nav_order: 9
lang: "pt"
source: limits.md
source_hash: "f145d00c4d10"
nav_exclude: true
search_exclude: true
---
# Limites e o que está verificado {#limits-and-what-is-verified}

Uma lista honesta: o que as ferramentas não fazem, e o que não foi verificado contra um jogo em execução.

## Telemetria {#telemetry}

| Gravador | Estado |
|---|---|
| Forza | Construído sobre a documentação oficial do Data Out; o layout é detetado a partir dos próprios pacotes. O leitor `.tele.gz` do FH Companion do visualizador foi verificado em voltas reais. |
| AC, ACC, AC EVO, AC Rally | Testado em páginas sintéticas construídas a partir dos layouts publicados. **Ainda não foi executado contra os jogos reais.** |
| EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, RBR | Testado em pacotes construídos a partir dos layouts documentados. **Ainda não foi executado contra os jogos reais.** Os eixos, a atitude e as unidades de velocidade do RBR não são documentados e são tratados a partir dos dados. |
| BeamNG.drive | O gravador é testado em pacotes construídos a partir da estrutura do mod. **O mod ainda não foi executado no jogo.** |
| Trackmania | O leitor do CSV no visualizador é testado. **O plugin ainda não foi executado no jogo.** Só carrega no modo de programador do Openplanet. |
| iRacing | O leitor de `.ibt` do visualizador é testado num ficheiro sintético. |

Outros limites da telemetria:

- A normalização do deslizamento do Forza não é documentada; o deslizamento da Kunos é escalado por um pico típico de
  asfalto, uma aproximação.
- O sentido de alguns eixos laterais do referencial do carro (Kunos, DiRT) está documentado nos dois sentidos; o
  tamanho do ângulo de derrapagem é fiável, o seu sinal não.
- Nenhum dos jogos de rali envia o deslizamento dos pneus; ele é derivado no visualizador. O RBR não envia velocidades
  das rodas.
- A superfície de um trecho de rali só é escrita quando se dá `--surface`; caso contrário, o ficheiro não indica
  nenhuma e o visualizador a infere (nome do trecho ou do evento, depois o estilo de condução, com aproximação por
  padrão).
- A deteção de voltas sem contador de voltas (AC EVO, AC Rally, BeamNG) usa o ponto onde a gravação começou como
  linha, por isso comece a gravar na linha de largada.
- Um reinício do veículo no BeamNG fecha a volta aberta nesse momento: é escrita como uma corrida parcial quando
  cobriu a distância mínima (300 m), e descartada caso contrário.
- O `route` guarda a cada 2 segundos, mais ou menos enquanto conduz; uma falha ou um processo morto perde no máximo as
  posições desde o último registo.
- O Forza Horizon não envia nome de pista, por isso os ficheiros de volta do Forza têm `"track": null`; o Forza
  Motorsport (2023) envia apenas um número, guardado como `lap.trackOrdinal`.

## Reconstrução {#reconstruction}

- **A profundidade é estimada, não lida.** O teto de toda a abordagem, e o preço de nunca tocar no processo do jogo.
- **O campo de visão é assumido, não medido.** Se for estreito demais, o nível é reconstruído mais fundo do que é.
- **A escala global** vem de uma altura de câmara assumida (1,15 m na janela), ou da telemetria. É medida no primeiro
  quadro-chave; quando esse não tem chão utilizável, tentam-se os quadros-chave seguintes (até 30 quadros),
  e uma escala encontrada mais tarde é aplicada a todo o nível quando é escrito. A linha «Size:» da janela diz o que
  aconteceu; sem chão nenhum encontrado, a digitalização fica sem unidades. O tamanho do voxel fica então nas unidades
  do primeiro quadro, por isso o seu tamanho em metros difere da definição. As reconstruções offline ficam nas
  unidades da própria solução.
- **O fecho de ciclo está desligado** e não é um grafo de poses quando é ligado no código; a deriva é limitada apenas
  pela qualidade do seguimento de quadro para quadro.
- **O ajuste de feixes por janela existe mas não está ligado**; colapsou com imagens reais.
- **A superfície é uma ocupação ponderada, não um TSDF**: estruturas finas e espaço livre saem piores do que um TSDF
  daria.
- **Sem atlas de texturas.** A cor é por vértice (`COLOR_0`), misturada a partir das 4 melhores vistas entre 160
  quadros guardados. O teste de oclusão é grosseiro: testa contra os próprios vértices da malha num buffer de
  profundidade de 2 pixels, por isso um oclusor que a malha não contém (um carro que passa) não é apanhado.
- **A água nunca é rotulada**; tudo é chão ou estrutura.
- **A resolução por feed-forward não é ao vivo**: precisa primeiro da gravação. O recálculo adaptativo de trechos
  difíceis não está construído.
- **As poses de telemetria** põem a câmara no carro (o deslocamento de uma câmara de perseguição é desconhecido). As
  posições são tomadas como o Forza as envia (Y para cima, como nos ficheiros de volta); os sentidos de guinada,
  arfagem e rolamento foram lidos de voltas gravadas (sentido de marcha, inclinação, que lado da suspensão comprime),
  não da câmara do jogo em execução.
- A sobreposição não consegue desenhar sobre o **ecrã inteiro exclusivo**; use o modo janela sem bordas.
- As teclas de atalho globais, a sobreposição que deixa passar cliques e a captura ao vivo são **só do Windows**.
- Fechar a janela não pergunta se quer guardar.

## O que é medido {#what-is-measured}

- `tests/test_accuracy.py`: uma sala sintética com um percurso conhecido e profundidade analítica - quadros
  posicionados, erro do percurso, distância percorrida, tamanho da sala, superfície nas paredes
  ([Reconstrução do nível](reconstruction.md#measured-on-synthetic-ground-truth)).
- `tests/test_track_width.py`: uma estrada de largura conhecida percorrida fora do centro reconstrói a sua largura.
- `tests/test_track_scale.py`: extração de superfície à escala de uma pista de corridas, memória proporcional ao que
  foi digitalizado, blocos que se juntam numa só superfície.
- `tests/test_glb.py` mais os testes do próprio visualizador: o contrato do `.glb` vista dos dois lados.
- O desempenho da rede de profundidade em jogabilidade real não é algo que uma cena sintética consiga responder, e não
  é medido pelo conjunto de testes.
