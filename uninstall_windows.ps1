# Junmai AutoDev - Windows Uninstaller Script
# Version: 2.0

param(
    [string]$InstallPath = "C:\JunmaiAutoDev",
    [switch]$KeepData,
    [switch]$Unattended
)

$ErrorActionPreference = "Stop"

# Color output functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }

# Banner
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          Junmai AutoDev - アンインストーラー              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Yellow

Write-Warning "このスクリプトは Junmai AutoDev をアンインストールします"
Write-Info "インストール先: $InstallPath"

if (-not $Unattended) {
    $confirm = Read-Host "続行しますか? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Info "アンインストールをキャンセルしました"
        exit 0
    }
}

Write-Host ""

# Step 1: Stop running processes
Write-Info "Step 1/5: 実行中のプロセスを停止中..."

$processNames = @("python", "redis-server", "ollama")
foreach ($procName in $processNames) {
    $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($proc in $processes) {
            if ($proc.Path -like "*$InstallPath*") {
                Stop-Process -Id $proc.Id -Force
                Write-Success "プロセスを停止: $procName (PID: $($proc.Id))"
            }
        }
    }
}

Write-Host ""

# Step 2: Remove Lightroom plugin
Write-Info "Step 2/5: Lightroom プラグインを削除中..."

$pluginPath = "$env:APPDATA\Adobe\Lightroom\Modules\JunmaiAutoDev.lrdevplugin"
if (Test-Path $pluginPath) {
    Remove-Item -Path $pluginPath -Recurse -Force
    Write-Success "プラグインを削除しました"
} else {
    Write-Info "プラグインが見つかりません（スキップ）"
}

Write-Host ""

# Step 3: Backup data (if requested)
if ($KeepData) {
    Write-Info "Step 3/5: データをバックアップ中..."
    
    $backupPath = "$env:USERPROFILE\Documents\JunmaiAutoDev_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    
    $dataItems = @("data", "logs", "config")
    foreach ($item in $dataItems) {
        $sourcePath = Join-Path $InstallPath $item
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $backupPath -Recurse -Force
            Write-Success "バックアップ: $item"
        }
    }
    
    Write-Success "バックアップ先: $backupPath"
} else {
    Write-Info "Step 3/5: データバックアップをスキップ"
}

Write-Host ""

# Step 4: Remove installation directory
Write-Info "Step 4/5: インストールディレクトリを削除中..."

if (Test-Path $InstallPath) {
    try {
        Remove-Item -Path $InstallPath -Recurse -Force
        Write-Success "ディレクトリを削除: $InstallPath"
    } catch {
        Write-Error "ディレクトリの削除に失敗しました: $_"
        Write-Info "手動で削除してください: $InstallPath"
    }
} else {
    Write-Info "インストールディレクトリが見つかりません"
}

Write-Host ""

# Step 5: Remove desktop shortcut
Write-Info "Step 5/5: デスクトップショートカットを削除中..."

$shortcutPath = "$env:USERPROFILE\Desktop\Junmai AutoDev.lnk"
if (Test-Path $shortcutPath) {
    Remove-Item -Path $shortcutPath -Force
    Write-Success "ショートカットを削除しました"
} else {
    Write-Info "ショートカットが見つかりません（スキップ）"
}

Write-Host ""

# Completion message
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          アンインストールが完了しました                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Info "以下のコンポーネントは手動でアンインストールしてください:"
Write-Host "  - Python (必要に応じて)"
Write-Host "  - Redis (必要に応じて)"
Write-Host "  - Ollama (必要に応じて)"
Write-Host ""

if ($KeepData) {
    Write-Info "データは以下の場所にバックアップされています:"
    Write-Host "  $backupPath"
    Write-Host ""
}

Write-Success "アンインストールスクリプトを終了します"
