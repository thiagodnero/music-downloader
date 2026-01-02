Write-Host "=== Build PermittedAudioDownloader ==="

$ffmpegPath = "permitted_audio_downloader\\assets\\ffmpeg\\bin\\ffmpeg.exe"
$ffprobePath = "permitted_audio_downloader\\assets\\ffmpeg\\bin\\ffprobe.exe"

if (-Not (Test-Path $ffmpegPath) -or -Not (Test-Path $ffprobePath)) {
  Write-Error "ffmpeg.exe/ffprobe.exe não encontrados em permitted_audio_downloader\\assets\\ffmpeg\\bin. Execute o script de download ou copie os binários antes do build."
  exit 1
}

python -m venv .venv
. .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

pyinstaller `
  --noconfirm `
  --clean `
  --name PermittedAudioDownloader `
  --noconsole `
  --add-data "permitted_audio_downloader\assets;assets" `
  --add-binary "permitted_audio_downloader\assets\ffmpeg\bin\ffmpeg.exe;assets/ffmpeg/bin" `
  --add-binary "permitted_audio_downloader\assets\ffmpeg\bin\ffprobe.exe;assets/ffmpeg/bin" `
  run_app.py
