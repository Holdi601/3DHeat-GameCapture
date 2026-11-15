---
title: "Başlamadan önce"
nav_order: 1.5
lang: "tr"
source: before-you-start.md
source_hash: "0c8bf313b1db"
nav_exclude: true
search_exclude: true
---
# Başlamadan önce {#before-you-start}

Komut satırında yeni misiniz? Bu sayfa sizi hiçbir şeyden ilk çalışan komuta kadar götürür. Bir kez yapılır, yaklaşık on dakika sürer.

## 1. Python'u kurun {#install-python}

GameCapture bir Python programıdır. **Python 3.10 veya daha yeni** gerekir.

1. [python.org/downloads](https://www.python.org/downloads/) adresine gidin ve Windows için en yeni Python'u indirin.
2. Kurulum programını çalıştırın. İlk ekranda **"Add python.exe to PATH" kutusunu işaretleyin**. Bu işaret olmadan terminal Python'u bulamaz.
3. *Install Now* (Şimdi yükle) düğmesine tıklayın.

Ya da bir terminalde: `winget install Python.Python.3.12`.

## 2. Git'i kurun {#install-git}

Git aracı indirir. [git-scm.com](https://git-scm.com/download/win) adresinden alın ya da `winget install Git.Git` çalıştırın. Git istemiyorsanız, [GitHub sayfasında](https://github.com/Holdi601/3DHeat-GameCapture) *Code > Download ZIP* (Kod > ZIP dosyasını indir) seçeneğini kullanın ve açın.

## 3. Bir klasörde terminal açın {#open-a-terminal-in-a-folder}

Terminal, komutları yazdığınız bir penceredir. Bu sayfalar her Windows bilgisayarda bulunan **PowerShell**'i kullanır.

- Klasörü Dosya Gezgini'nde açın, adres çubuğuna tıklayın, `powershell` yazın ve Enter'a basın. PowerShell **o klasörde** açılır.
- Ya da Başlat menüsünden PowerShell'i açın ve `cd` ile bir klasöre geçin:

```powershell
cd "C:\Games\Tools"
```

## 4. Bu sayfalardaki komutları okuyun {#read-the-commands-on-these-pages}

- Her komut satırını yazın ve Enter'a basın.
- `<...>` içindeki metin bir **yer tutucu**dur: kendi değerinizi oraya yazın, işaretleri yazmadan. `<recording>.mp4` `match1.mp4` gibi bir dosya adı demektir.
- `[--fps 5]` gibi `[...]` içindeki metin **isteğe bağlıdır**.
- Boşluk içeren bir yol tırnak ister: `"C:\My Videos\match1.mp4"`.
- `#` ile başlayan satırlar açıklamadır. Bunları yazmazsınız.

## 5. Aracı ve paketlerini alın {#get-the-tool-and-its-packages}

```powershell
git clone https://github.com/Holdi601/3DHeat-GameCapture
cd 3DHeat-GameCapture
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

`python -m venv .venv` aracın paketleri için özel bir klasör oluşturur; böylece bilgisayarınızdaki başka şeylerle karışmazlar. Her komut bundan sonra `.venv\Scripts\python` ile başlar.

**Şunu görmelisiniz:** son satır `Successfully installed ...` der. Aracın çalıştığını denetleyin:

```powershell
.venv\Scripts\python -m heat3d_capture --help
```

**Şunu görmelisiniz:** `usage: heat3d_capture` ile başlayan bir komut listesi.

![--help komutunun yazdırdığı komut listesi](../assets/img/cli-help.svg)

Klasörü bir kez *etkinleştirebilir* ve sonra yalnızca `python` yazabilirsiniz:

| Terminal | Etkinleştir | Sonra |
|---|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` | `python -m heat3d_capture --help` |
| cmd | `.venv\Scripts\activate.bat` | `python -m heat3d_capture --help` |

PowerShell *betik çalıştırma devre dışı* derse, bir kez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` çalıştırın ya da etkinleştirmeden devam edin.

## 6. Bazı komutların ihtiyaç duyduğu ek programlar {#extra-programs-some-commands-need}

| Komut | Gerekenler | Kurulum |
|---|---|---|
| `hud` | **ffmpeg** ve **ffprobe** (video dosyalarını okur) | `winget install Gyan.FFmpeg`, sonra yeni bir terminal açın. `ffmpeg -version` ile denetleyin. |
| `reconstruct`, `locate` | **PyTorch**, diğer paketlerden önce kurulur | [pytorch.org](https://pytorch.org/get-started/locally/) adresindeki, GPU'nuz için komut |

## Bir şey ters giderse {#when-something-goes-wrong}

| Gördüğünüz | Anlamı | Yapın |
|---|---|---|
| `'python' is not recognized` | Python PATH üzerinde değil | PATH işaretiyle Python'u yeniden kurun, sonra yeni bir terminal açın. |
| `No module named heat3d_capture` | terminal aracın klasöründe değil | `3DHeat-GameCapture` klasörüne `cd` ile girin. |
| `No module named numpy` (ya da başka bir paket) | paketler kurulu değil ya da başka bir Python kullandınız | `.venv\Scripts\python` ile `pip install -r requirements.txt` satırını yeniden çalıştırın. |
| `'.venv' is not recognized` | cmd'de `/` yazdınız | Ters eğik çizgi kullanın: `.venv\Scripts\python`. |
| `ffmpeg was not found on PATH` | ffmpeg eksik | 6. adıma bakın, sonra yeni bir terminal açın. |

Sonraki: [Ana sayfa](index.md) her iş için bir ilk örnek verir.
