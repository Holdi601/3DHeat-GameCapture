---
title: "Jogos: gravação e percursos"
nav_order: 4
lang: "pt"
source: games.md
source_hash: "3b33173a3463"
nav_exclude: true
search_exclude: true
---
# Jogos: gravação e percursos {#games-recording-and-courses}

Como cada jogo suportado é gravado, o que ele envia e quais dos seus percursos podem ser exportados a partir dos próprios ficheiros do jogo.

As regras são as mesmas para todos os jogos: um percurso sai de ficheiros que o utilizador possui, ou é reconstruído a partir da própria jogabilidade do utilizador. Ficheiros criptografados só abrem com uma chave que o utilizador já tem - nada aqui traz chaves nem as recupera, e nada é injetado no processo de um jogo. A telemetria vem apenas das interfaces que os jogos publicam para isso (saídas UDP, memória partilhada, as próprias interfaces de mod e plugin). O que o utilizador aponta as ferramentas para continua sujeito à licença desse jogo.

## Telemetria {#telemetry}

Cada jogo termina em ficheiros `heat3d-lap` ([`lap-format.md`](lap-format.md)), com nomes de canais canónicos e um bloco `meta` que diz o que os números significam - como o deslizamento é escalado, se é circuito, rali ou arcade, a superfície quando é conhecida - para que o leitor trate todos da mesma forma. Todos os comandos são `python -m heat3d_capture ...` neste repositório.

| Jogo | Como gravar | Posição | Pneus e deslizamento | Ângulo de derrapagem | Situação |
|---|---|---|---|---|---|
| Forza Horizon 4/5/6 | Data Out por UDP: `heat3d_capture telemetry` (repassa ao FH Companion) - ou o `.tele.gz` do próprio FH Companion ao lado de cada volta, carregado junto com o ficheiro da volta | XYZ do mundo | razão de deslizamento, ângulo de deslizamento, deslizamento combinado por roda, normalizados; rugosidade da superfície | velocidade no referencial do carro | gravador testado; leitor do `.tele.gz` verificado em voltas reais |
| Forza Motorsport (incl. 2023) | o mesmo; distinguidos pelo tamanho do pacote | XYZ do mundo | o mesmo | o mesmo | gravador testado |
| Assetto Corsa, ACC, AC EVO | memória partilhada: `telemetry --game ac / acc / acevo` | média dos pontos de contacto dos pneus | razão e ângulo de deslizamento (físicos, escalados por um pico de asfalto); ABS e TC atuando (ACC, EVO) | velocidade no referencial do carro | gravador testado em páginas sintéticas |
| Assetto Corsa Rally | `telemetry --game acrally` | o mesmo | o mesmo; cargas nas rodas; temperaturas convertidas de kelvin | velocidade no referencial do carro | gravador testado em páginas sintéticas |
| EA SPORTS WRC | UDP: `telemetry --game wrc --configure "<Documentos>/My Games/WRC/telemetry/config.json"` liga o pacote `wrc` padrão (o ficheiro é copiado antes como cópia de segurança) | XYZ do mundo | velocidade do ponto de contacto por roda; deslizamento derivado | a partir dos eixos do carro e da sua velocidade | gravador testado com pacotes montados a partir do layout documentado |
| DiRT Rally 2.0, DiRT Rally, DiRT 4 | UDP: defina `<udp enabled="true" extradata="3" port="20777" delay="1" />` em `hardware_settings_config.xml`, depois `telemetry --game dirtrally2` (ou `dirtrally`, `dirt4`) | XYZ do mundo | velocidade do ponto de contacto por roda; deslizamento derivado. Sem canal de travão de mão | a partir dos eixos do carro e da sua velocidade | o mesmo |
| Richard Burns Rally (RSF/NGP) | telemetria UDP do NGP (`udpTelemetry=1`): `telemetry --game rbr` | mundo, eixo vertical encontrado a partir do trecho | deflexão e força da mola por roda; sem velocidades de roda | as próprias velocidades do carro | o mesmo; eixos e unidades de velocidade não são documentados e são tratados a partir dos dados |
| BeamNG.drive | o mod de protocolo `heat3d`: `telemetry --game beamng --install`, depois Options > Other > Protocols > "others" | mundo, girado para Y para cima | velocidade da superfície da roda, rotação, carga, contacto com o chão; deslizamento derivado | a partir dos eixos do carro e da sua velocidade | gravador testado com pacotes montados a partir da struct do mod; o mod não foi testado no jogo |
| Trackmania (2020) | o plugin do Openplanet `Heat3dRecorder`: `telemetry --game trackmania --install`, carregado no modo de programador do Openplanet; um CSV por corrida na pasta de armazenamento | XYZ do mundo | coeficiente de deslizamento do Trackmania por roda; chão solto a partir dos materiais das rodas; no ar | velocidade frontal e lateral | leitor testado; o plugin não foi testado no jogo |
| iRacing | os próprios ficheiros `.ibt`; não precisa de gravador | latitude/longitude/altitude, projetadas num plano tangente | sem deslizamento (não é registado); taxa de guinada e aceleração lateral | a partir da taxa de guinada em relação ao trajeto | leitor testado num ficheiro sintético |

O que nenhum dos jogos de rali envia - o deslizamento dos pneus - um leitor calcula: a partir da velocidade do ponto de contacto de cada roda ou da superfície em relação à velocidade do carro, quando o jogo envia uma delas (`(roda - carro) / carro`), ou a partir da rotação e de um raio de deslocação medido na própria volta, quando o jogo envia só a rotação. O ângulo de derrapagem vem da velocidade do próprio carro (Forza, os jogos AC, Trackmania, RBR), da velocidade do mundo projetada nos eixos do carro (EA WRC, DiRT, BeamNG), ou do rumo em relação ao trajeto. Se o carro está no ar vem do contacto, das cargas ou da suspensão das suas rodas.

Quando o mundo de um jogo é canhoto - o do Forza é -, o percurso sai espelhado num visualizador destrorso; a direção e a suspensão das próprias voltas denunciam isso. Jogos cuja lateralidade não está documentada (RBR, BeamNG, Trackmania) são tratados da mesma forma: medida, não presumida.

Além dos canais de condução, os gravadores guardam o que cada jogo acrescenta: ABS e controlo de tração atuando nos jogos AC, distribuição de travão, DRS, limitador de pit, boost e vida das pastilhas e dos discos de travão; no iRacing, as definições de auxílio, a distribuição de travão, o combustível, as temperaturas de óleo e de água, e cada outro canal que ele regista com o próprio nome.

### Fontes e o que ainda não está confirmado {#sources-and-what-is-not-yet-confirmed}

- **Forza:** a documentação oficial do Data Out (Forza Motorsport; Forza Horizon 6) para os campos, as unidades e o referencial do carro (x para a direita, y para cima, z para a frente - canhoto). Não está documentado em relação a que o Forza normaliza o deslizamento: meça onde a aderência de cada carro realmente cai, em vez de presumir que 1 é o limite.
- **Kunos:** o SDK do AC1, a documentação da memória partilhada do ACC v1.8.12, `albertowd/live-telemetry-evo` (EVO, medido; o AC Rally usa o layout do ACC, "confirmado por sondagem byte a byte"), `LuizZak/AssettoCorsaRallyTelemetryReader`. O lado para o qual aponta o eixo x do carro é documentado nos dois sentidos: use o tamanho do ângulo de derrapagem, não o sinal.
- **EA SPORTS WRC:** o Guia de Telemetria UDP v1.3 da EA e a lista de canais que o jogo grava em `readme/channels.json`; os deslocamentos do pacote `wrc` padrão, como decodificados por nobonobo/obs-codemasters-telemetry. A porta padrão de fábrica não está documentada; o gravador liga o pacote na porta 20777.
- **DiRT:** o documento UDP do DiRT 4 da Codemasters, ErlerPhilipp/dr2_logger, soong-construction/dirt-rally-time-recorder. O sentido do vetor lateral e a unidade da posição da suspensão são documentados nos dois sentidos; nenhum dos dois decide um resultado.
- **RBR:** `rbr.telemetry.data.TelemetryData.h` do NGP (via mika-n/RBRUDPTelemetryLogger, groybe/rbr-udp-telem). Os eixos de posição, as unidades de atitude e a unidade de velocidade não são documentados: o gravador tira o vertical do trecho e a velocidade das posições.
- **BeamNG:** documentation.beamng.com (protocolos; refNodes: vehicle +X à esquerda, -Y para a frente, Z para cima), e os ficheiros `lua/vehicle/protocols.lua` e `wheels.lua` do próprio jogo. O OutSim é um stub nas versões atuais; o OutGauge não tem posição e o MotionSim não tem rodas, daí o mod.
- **Trackmania:** o `CSceneVehicleVisState` e o plugin VehicleState do Openplanet, o tempo de corrida do `CSmScriptPlayer`. Plugins do Openplanet não enviam UDP, então o plugin grava ficheiros. Plugins não assinados só carregam no modo de programador, o que limita o jogo online; o plugin pode ser assinado em openplanet.dev.

Nenhum dos gravadores foi ainda executado contra os jogos ao vivo aqui; a primeira sessão real de cada um é o teste que importa, e `tests/test_kunos.py`, `test_rally.py` e `test_beamng.py` fixam os layouts para os quais foram construídos. Cada gravador verifica os pacotes conforme chegam - a velocidade contra a velocidade do carro, o tamanho da struct - e avisa quando um layout não bate.

## Percursos: o que é exportado, por jogo {#courses-what-is-exported-per-game}

Um percurso acrescenta as zebras, os muros e as áreas de escape que explicam uma linha. Os percursos são exportados pelo [3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (`python -m heat3d_gamefiles course <volta>`), a partir dos ficheiros do próprio jogo, onde isso foi construído e verificado numa cópia instalada. Os detalhes estão na [documentação do GameFiles](https://holdi601.github.io/3DHeat-GameFiles/).

| Jogo | Percurso a partir de uma volta |
|---|---|
| Forza Horizon | sim |
| BeamNG.drive | sim |
| Assetto Corsa Rally | sim |
| Assetto Corsa EVO | não: o conteúdo não é legível como ficheiros |
| iRacing | não: os modelos de pista vêm em formato protegido |
| Forza Motorsport, Assetto Corsa, Assetto Corsa Competizione, EA SPORTS WRC, DiRT Rally 2.0 / 1 / DiRT 4, Richard Burns Rally, Trackmania | ainda não: cada um precisa de uma cópia instalada para construir e verificar |

O caminho pela jogabilidade, descrito abaixo, funciona para todos eles enquanto isso.

## O caminho que funciona para todos os jogos {#the-route-that-works-for-every-game}

O GameCapture reconstrói um nível a partir de vídeo de jogabilidade. A parte difícil é o caminho da câmara, e no Forza ele é exato porque a telemetria dá a pose do carro a cada quadro. Agora todos os jogos acima têm o mesmo: posição e atitude, ao vivo, a partir de uma interface documentada. Alimentar essas informações em `pose/telemetry_pose.py` no lugar da do Forza é a única peça que torna o caminho pela jogabilidade exato para todos eles - o restante do pipeline (profundidade, fusão, texturização) não depende do jogo que desenhou os quadros.
