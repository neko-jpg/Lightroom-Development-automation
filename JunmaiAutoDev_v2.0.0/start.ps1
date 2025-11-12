# Junmai AutoDev - Windows Startup Script
# This script starts all necessary services and the GUI

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              Junmai AutoDev を起動中...                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Error "仮想環境が見つかりません。install_windows.ps1 を実行してください"
    exit 1
}

# Activate virtual environment
Write-Info "仮想環境をアクティベート中..."
& "venv\Scripts\Activate.ps1"
Write-Success "仮想環境をアクティベートしました"

# Check Redis
Write-Info "Redis 接続を確認中..."
try {
    $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisTest.TcpTestSucceeded) {
        Write-Success "Redis 接続確認"
    } else {
        Write-Error "Redis に接続できません。Redis を起動してください"
    }
} catch {
    Write-Error "Redis 接続確認に失敗しました"
}

# Check Ollama
Write-Info "Ollama 接続を確認中..."
try {
    $ollamaTest = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
    if ($ollamaTest.StatusCode -eq 200) {
        Write-Success "Ollama 接続確認"
    }
} catch {
    Write-Error "Ollama に接続できません。Ollama を起動してください"
}

# Start backend server in background
Write-Info "バックエンドサーバーを起動中..."
$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location "$dir\local_bridge"
    & python app.py
} -ArgumentList $ScriptDir

Write-Success "バックエンドサーバーを起動しました (Job ID: $($backendJob.Id))"

# Wait for server to start
Start-Sleep -Seconds 3

# Start Celery worker in background
Write-Info "Celery ワーカーを起動中..."
$celeryJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location "$dir\local_bridge"
    & python start_worker.py
} -ArgumentList $ScriptDir

Write-Success "Celery ワーカーを起動しました (Job ID: $($celeryJob.Id))"

# Wait a bit more
Start-Sleep -Seconds 2

# Start GUI
Write-Info "GUI を起動中..."
Set-Location "$ScriptDir\gui_qt"

try {
    & python main.py
} catch {
    Write-Error "GUI の起動に失敗しました: $_"
}

# Cleanup: Stop background jobs when GUI closes
Write-Info "バックグラウンドジョブを停止中..."
Stop-Job -Job $backendJob, $celeryJob
Remove-Job -Job $backendJob, $celeryJob
Write-Success "すべてのサービスを停止しました"

Write-Host ""
Write-Info "Junmai AutoDev を終了しました"
