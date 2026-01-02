# PermittedAudioDownloader

Aplicativo Windows para baixar áudio de YouTube ou SoundCloud **apenas de fontes permitidas**, com conversão para WAV.

## ⚠️ Aviso Legal
Este software deve ser utilizado **somente para conteúdos com permissão do autor** ou disponibilizados legalmente para download.
O usuário é responsável pelo uso. O app não implementa qualquer mecanismo de bypass de DRM/proteções.

## Stack
- Python 3.11+
- PySide6 (GUI)
- yt-dlp (download de áudio)
- ffmpeg (conversão para WAV)
- PyInstaller (build do .exe)

## Estrutura
- `permitted_audio_downloader/app`: código principal
- `permitted_audio_downloader/assets`: binários (ffmpeg)
- `permitted_audio_downloader/scripts`: scripts auxiliares
- `permitted_audio_downloader/tests`: testes básicos

## Como rodar em desenvolvimento (Windows)
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_app.py
```

## Build do executável (Windows)
```powershell
./build.ps1
```

### ffmpeg
1. Preferencial: coloque `ffmpeg.exe` e `ffprobe.exe` em `permitted_audio_downloader/assets/ffmpeg/bin/`.
2. Fallback: se não existir, o app tenta usar o `ffmpeg` disponível no PATH e exibirá instruções caso não encontre.

## Limitações e compliance
- Domínios permitidos: `youtube.com`, `www.youtube.com`, `youtu.be`, `m.youtube.com`, `soundcloud.com`, `www.soundcloud.com`.
- Qualquer outra URL será bloqueada com a mensagem **"Domínio não suportado"**.
- Sem coleta de dados do usuário ou telemetria.

## Comandos principais
- Rodar: `python run_app.py`
- Build: `./build.ps1`
