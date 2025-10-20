# 🚀 Start LegalBot Full Stack
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "🔄 Starting Docker Desktop..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Start-Sleep -Seconds 30
}
Write-Host "🧩 Building and starting containers..."
docker compose up --build -d
Start-Process "http://localhost:8602"
