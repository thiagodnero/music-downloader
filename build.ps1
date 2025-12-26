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
  --add-data "assets;assets" `
  app\main.py
