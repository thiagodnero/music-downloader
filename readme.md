# PermittedAudioDownloader

Aplicativo Windows para baixar áudio de YouTube ou SoundCloud **apenas de fontes permitidas**, com conversão para WAV.

## ⚠️ Aviso Legal
Este software deve ser utilizado **somente para conteúdos com permissão do autor** ou disponibilizados legalmente para download.
O usuário é responsável pelo uso.

## Stack
- Python 3.11+
- PySide6 (GUI)
- yt-dlp (download de áudio)
- ffmpeg (conversão para WAV)
- PyInstaller (build do .exe)

## Estrutura
- app/: código principal
- assets/: binários (ffmpeg)
- scripts/: scripts auxiliares
- tests/: testes básicos

## Build (Windows)
Ver `build.ps1`
