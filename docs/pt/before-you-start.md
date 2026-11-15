---
title: Antes de começar
nav_order: 1.5
lang: "pt"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Antes de começar {#before-you-start}

Nunca usou a linha de comando? Esta página leva você do zero ao primeiro comando funcionando. Leva
cerca de dez minutos, uma única vez.

## 1. Instalar o Python {#install-python}

O GameCapture é um programa Python. Você precisa de **Python 3.10 ou mais recente**.

1. Vá a [python.org/downloads](https://www.python.org/downloads/) e baixe a versão mais nova do
   Python para Windows.
2. Execute o instalador. Na primeira tela, **marque "Add python.exe to PATH"**. Sem a marcação,
   o terminal não vai encontrar o Python.
3. Clique em *Install Now*.

Ou, em um terminal: `winget install Python.Python.3.12`.

## 2. Instalar o Git {#install-git}

O Git baixa a ferramenta. Obtenha-o em [git-scm.com](https://git-scm.com/download/win), ou execute
`winget install Git.Git`. Se não quiser o Git, use *Code > Download ZIP* na
[página do GitHub](https://github.com/Holdi601/3DHeat-GameCapture) e descompacte.

## 3. Abrir um terminal em uma pasta {#open-a-terminal-in-a-folder}

Um terminal é uma janela onde você digita comandos. Estas páginas usam o **PowerShell**, que todo
PC com Windows tem.

- Abra a pasta no Explorador de Arquivos, clique na barra de endereço, digite `powershell` e pressione
  Enter. O PowerShell abre **nessa pasta**.
- Ou abra o PowerShell pelo menu Iniciar e vá para uma pasta com `cd`:

```powershell
cd "C:\Jogos\Ferramentas"
```

## 4. Ler os comandos destas páginas {#read-the-commands-on-these-pages}

- Digite cada linha de comando e pressione Enter.
- Texto entre sinais de menor e maior é um **marcador**: coloque ali o seu próprio valor, sem os sinais.
  `<gravação>.mp4` significa um nome de arquivo como `partida1.mp4`.
- Texto entre colchetes, como `[--fps 5]`, é **opcional**.
- Um caminho com espaços precisa de aspas: `"C:\Meus Vídeos\partida1.mp4"`.
- Linhas que começam com `#` são comentários. Você não as digita.

## 5. Obter a ferramenta e os seus pacotes {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` cria uma pasta privada para os pacotes da ferramenta, para que não se misturem
com nada mais no seu PC. Todo comando então começa com `.venv\Scripts\python`.

**Você deve ver** a última linha dizer `Successfully installed ...`. Confira se a ferramenta funciona:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Você deve ver** uma lista de comandos, começando com `usage: heat3d_capture`.

![A lista de comandos que o --help mostra](../assets/img/cli-help.svg)

Você também pode *ativar* a pasta uma vez, e depois digitar só `python`:

| Terminal | Ativar | Depois |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

Se o PowerShell disser *running scripts is disabled*, execute uma vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou pule a ativação.

## 6. Programas extras que alguns comandos precisam {#extra-programs-some-commands-need}

| Comando | Precisa de | Instalação |
|---|---|---|
| `hud` | **ffmpeg** e **ffprobe** (leem arquivos de vídeo) | `winget install Gyan.FFmpeg`, depois abra um novo terminal. Confira com `ffmpeg -version`. |
| `reconstruct`, `locate` | **PyTorch**, instalado antes dos outros pacotes | o comando de [pytorch.org](https://pytorch.org/get-started/locally/) para a sua GPU |

## Quando algo dá errado {#when-something-goes-wrong}

| Você vê | Significa | Faça isto |
|---|---|---|
| `'python' is not recognized` | o Python não está no PATH | Instale o Python de novo com a marcação do PATH, depois abra um novo terminal. |
| `No module named heat3d_capture` | o terminal não está na pasta da ferramenta | Use `cd` para entrar na pasta `3DHeat-GameCapture`. |
| `No module named numpy` (ou outro pacote) | os pacotes não estão instalados, ou você usou outro Python | Execute de novo a linha `pip install -r requirements.txt`, com `.venv\Scripts\python`. |
| `'.venv' is not recognized` | você digitou `/` no cmd | Use barras invertidas: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | o ffmpeg está faltando | Veja o passo 6, depois abra um novo terminal. |

Próximo: [Início](index.md) tem um primeiro exemplo para cada tarefa.
