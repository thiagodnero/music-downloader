Write-Host "=== Build PermittedAudioDownloader ==="

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
  permitted_audio_downloader\app\main.py
