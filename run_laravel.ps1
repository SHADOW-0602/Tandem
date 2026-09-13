# Run Laravel Control Plane for Tandem
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Starting Tandem Laravel 11 API Control Plane   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend-laravel"

Set-Location $backendDir

Write-Host "`n[1/2] Running database migrations..." -ForegroundColor Yellow
php artisan migrate --force

Write-Host "`n[2/2] Launching Laravel on http://127.0.0.1:8000..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor Gray
php artisan serve --host=127.0.0.1 --port=8000
