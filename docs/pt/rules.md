---
title: As regras
nav_order: 2
lang: "pt"
source: rules.md
source_hash: "032350a1f53a"
nav_exclude: true
search_exclude: true
---
# As regras em que isto assenta {#the-rules-this-is-built-under}

Cada parte do 3DHeat GameCapture segue as mesmas restrições. São decisões de desenho, não avisos legais, e várias delas custam precisão de propósito.

## Nada é injetado, nada é interceptado {#nothing-is-injected-nothing-is-hooked}

Nenhuma parte disto se liga a um processo de jogo, lê a sua memória ou toca na sua API gráfica.

- **Os quadros** vêm do Windows Graphics Capture, a API pública que os gravadores de ecrã usam (através do pacote `windows-capture`), ou de um ficheiro de vídeo. Ver [Captura, máscaras e qualidade dos quadros](reconstruction-capture.md).
- **A telemetria** vem apenas das interfaces que os jogos publicam para isso:
  - o feed UDP do Data Out do Forza, ligado nas definições do jogo;
  - as páginas de memória partilhada com nome que os jogos da Kunos publicam para aplicações (`Local\acpmf_physics` e afins). São abertas só para leitura com `mmap`; esta é a forma documentada das aplicações as lerem, não é leitura da memória do processo do jogo;
  - a telemetria UDP que o EA SPORTS WRC, os jogos DiRT e o Richard Burns Rally (através do plugin RSF/NGP) enviam quando ligada nos seus próprios ficheiros de definições;
  - a interface de protocolo do BeamNG, através de um pequeno mod Lua de "protocolo" que o próprio `lua/vehicle/protocols.lua` do jogo carrega e envia;
  - a interface do plugin Openplanet do Trackmania, através de um plugin que só lê o que o Openplanet expõe e escreve ficheiros;
  - os ficheiros de telemetria `.ibt` do próprio iRacing.

## Porque importa {#why-it-matters}

O jogo conhece a profundidade de cada pixel com exatidão, e um buffer de profundidade interceptado tornaria a reconstrução de níveis quase perfeita e trivial. Significaria também injetar código em processos que podem estar protegidos por anti-trapaça, o que arrisca a conta de quem o executa. Por isso, a profundidade é *estimada* a partir da imagem ([Profundidade](reconstruction-depth.md)), e grande parte do percurso de reconstrução existe para recuperar o máximo possível dessa precisão perdida a partir de fontes que podem ser usadas livremente: poses de telemetria onde um jogo as publica, uma escala de plano de chão onde não as publica, e máscaras que mantêm o HUD e o cockpit fora da resolução.

O buffer de profundidade do ReShade foi considerado e não usado. O ReShade desativa o acesso à profundidade em sessões multijogador por desenho, por isso só ajudaria títulos para um jogador (ver [`LICENSES.md`](https://github.com/Holdi601/3DHeat-GameCapture/blob/main/LICENSES.md)).

## O que a ferramenta altera na sua máquina, e só quando lhe é pedido {#things-the-tool-changes-on-your-machine-and-only-when-asked}

| Ação | Quando | O quê, exatamente |
|---|---|---|
| Instala pacotes Python | na primeira execução da janela de digitalização, depois de uma caixa de diálogo e de uma confirmação | `pip install` no interpretador que executa a ferramenta - com `scan.bat`, o `.venv` privado ao lado. Nunca em todo o sistema por si só. |
| Converte o modelo de profundidade | botão "Set up the depth model", depois de uma segunda caixa de diálogo para o PyTorch e afins | escreve `models/depth-small-518.onnx` |
| Edita o `config.json` do EA SPORTS WRC | `telemetry --game wrc --configure <file>` | liga o pacote `wrc` / `session_update` para 127.0.0.1; o ficheiro antigo fica guardado como `config.json.bak` |
| Copia o mod do BeamNG | `telemetry --game beamng --install` | copia `mods/beamng/heat3d` para `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current\mods\unpacked\heat3d` (substituindo uma cópia mais antiga) |
| Copia o plugin do Trackmania | `telemetry --game trackmania --install` | copia `mods/trackmania/Heat3dRecorder` para `%USERPROFILE%\OpenplanetNext\Plugins\Heat3dRecorder` (substituindo uma cópia mais antiga) |
| Regista atalhos globais | enquanto a janela de digitalização está aberta (Windows) | Ctrl+Alt+F9 / F10 / F11, libertados quando a janela fecha |
| Atualiza a ferramenta | depois de confirmar o aviso de atualização, ou executar `python -m heat3d_update` | ver [Atualizações](updates.md) |

Os ficheiros `hardware_settings_config.xml` dos jogos DiRT e o `RichardBurnsRally.ini` do Richard Burns Rally **não** são editados pela ferramenta; ligue a saída UDP deles por si próprio (ver [Jogos de rali](telemetry-rally.md)).

## O que é lido e o que fica na sua máquina {#what-is-read-and-what-stays-on-your-machine}

As ferramentas leem o que o jogo mostra no ecrã e a telemetria e os ficheiros que ele publica para isso, no seu próprio computador. Nada de um jogo é incluído nem redistribuído: nenhum recurso do jogo, nenhum código do jogo, nenhuma DLL. Os ficheiros de voltas, as gravações, as reconstruções e os circuitos exportados ficam na sua máquina; o `.gitignore` do repositório mantém gravações, ficheiros de voltas, malhas, pesos de modelos e vídeo fora do controlo de versões por pasta e por tipo de ficheiro.

O 3DHeat GameCapture não é afiliado a nenhum editor de jogos nem aprovado por nenhum. Os nomes dos jogos e as marcas relacionadas pertencem aos seus proprietários. Titulares de direitos: abram um issue em [github.com/Holdi601/3DHeat-GameCapture/issues](https://github.com/Holdi601/3DHeat-GameCapture/issues) - respondemos depressa e removemos o que for pedido.
