param(
  [string]$Destination = "../assets/ffmpeg/bin"
)

$ErrorActionPreference = "Stop"
$zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$tempZip = Join-Path $env:TEMP "ffmpeg-release-essentials.zip"

Write-Host "Baixando ffmpeg..."
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip

$extractDir = Join-Path $env:TEMP "ffmpeg-release-essentials"
if (Test-Path $extractDir) {
  Remove-Item $extractDir -Recurse -Force
}

Expand-Archive -Path $tempZip -DestinationPath $extractDir
$ffmpegDir = Get-ChildItem -Path $extractDir | Where-Object { $_.PSIsContainer } | Select-Object -First 1

$binPath = Join-Path $ffmpegDir.FullName "bin"
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Copy-Item -Path (Join-Path $binPath "ffmpeg.exe") -Destination $Destination -Force
Copy-Item -Path (Join-Path $binPath "ffprobe.exe") -Destination $Destination -Force

Write-Host "ffmpeg copiado para $Destination"
