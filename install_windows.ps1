# Junmai AutoDev - Windows Installer Script
# Version: 2.0
# PowerShell 5.1+ required

param(
    [switch]$SkipDependencies,
    [switch]$SkipOllama,
    [switch]$SkipRedis,
    [switch]$Unattended,
    [string]$InstallPath = "C:\JunmaiAutoDev"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Color output functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }

# Banner
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           Junmai AutoDev - Windows Installer             ║
║                                                           ║
║     Lightroom × LLM 自動現像システム                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "管理者権限で実行することを推奨します"
    if (-not $Unattended) {
        $continue = Read-Host "続行しますか? (y/n)"
        if ($continue -ne "y") { exit 1 }
    }
}

Write-Info "インストール先: $InstallPath"
Write-Host ""

# Step 1: Check system requirements
Write-Info "Step 1/8: システム要件の確認..."

# Check Windows version
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-Error "Windows 10 以上が必要です"
    exit 1
}
Write-Success "OS: Windows $($osVersion.Major).$($osVersion.Minor)"

# Check available disk space
$drive = (Get-Item $InstallPath -ErrorAction SilentlyContinue).PSDrive.Name
if (-not $drive) { $drive = $InstallPath.Substring(0, 1) }
$freeSpace = (Get-PSDrive $drive).Free / 1GB
if ($freeSpace -lt 50) {
    Write-Warning "ディスク空き容量が不足しています: $([math]::Round($freeSpace, 2)) GB"
}
Write-Success "ディスク空き容量: $([math]::Round($freeSpace, 2)) GB"

# Check GPU (NVIDIA)
try {
    $gpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }
    if ($gpu) {
        Write-Success "GPU: $($gpu.Name)"
    } else {
        Write-Warning "NVIDIA GPU が検出されませんでした（CPU モードで動作します）"
    }
} catch {
    Write-Warning "GPU 情報を取得できませんでした"
}

Write-Host ""

# Step 2: Install Python
if (-not $SkipDependencies) {
    Write-Info "Step 2/8: Python のインストール確認..."
    
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonVersion = & python --version 2>&1
        Write-Success "Python インストール済み: $pythonVersion"
    } else {
        Write-Warning "Python が見つかりません"
        Write-Info "Python 3.9-3.11 をインストールしてください: https://www.python.org/downloads/"
        
        if (-not $Unattended) {
            $installPython = Read-Host "winget で Python をインストールしますか? (y/n)"
            if ($installPython -eq "y") {
                try {
                    winget install Python.Python.3.11
                    Write-Success "Python 3.11 をインストールしました"
                } catch {
                    Write-Error "Python のインストールに失敗しました: $_"
                    exit 1
                }
            } else {
                Write-Error "Python が必要です。インストール後に再実行してください"
                exit 1
            }
        }
    }
} else {
    Write-Info "Step 2/8: Python チェックをスキップ"
}

Write-Host ""

# Step 3: Install Redis
if (-not $SkipRedis -and -not $SkipDependencies) {
    Write-Info "Step 3/8: Redis のインストール確認..."
    
    $redisPath = "C:\Program Files\Redis\redis-server.exe"
    if (Test-Path $redisPath) {
        Write-Success "Redis インストール済み"
    } else {
        Write-Warning "Redis が見つかりません"
        Write-Info "Redis をダウンロード: https://github.com/microsoftarchive/redis/releases"
        
        if (-not $Unattended) {
            $installRedis = Read-Host "Redis のインストールをスキップしますか? (y/n)"
            if ($installRedis -ne "y") {
                Write-Info "Redis を手動でインストールしてください"
            }
        }
    }
} else {
    Write-Info "Step 3/8: Redis チェックをスキップ"
}

Write-Host ""

# Step 4: Install Ollama
if (-not $SkipOllama -and -not $SkipDependencies) {
    Write-Info "Step 4/8: Ollama のインストール確認..."
    
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        Write-Success "Ollama インストール済み"
        
        # Check if model is downloaded
        $models = & ollama list 2>&1
        if ($models -like "*llama3.1*") {
            Write-Success "Llama 3.1 モデル ダウンロード済み"
        } else {
            Write-Info "Llama 3.1 モデルをダウンロード中..."
            & ollama pull llama3.1:8b-instruct
            Write-Success "Llama 3.1 モデル ダウンロード完了"
        }
    } else {
        Write-Warning "Ollama が見つかりません"
        
        if (-not $Unattended) {
            $installOllama = Read-Host "winget で Ollama をインストールしますか? (y/n)"
            if ($installOllama -eq "y") {
                try {
                    winget install Ollama.Ollama
                    Write-Success "Ollama をインストールしました"
                    
                    Write-Info "Llama 3.1 モデルをダウンロード中..."
                    & ollama pull llama3.1:8b-instruct
                    Write-Success "Llama 3.1 モデル ダウンロード完了"
                } catch {
                    Write-Warning "Ollama のインストールに失敗しました: $_"
                }
            }
        }
    }
} else {
    Write-Info "Step 4/8: Ollama チェックをスキップ"
}

Write-Host ""

# Step 5: Create installation directory
Write-Info "Step 5/8: インストールディレクトリの作成..."

if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    Write-Success "ディレクトリを作成: $InstallPath"
} else {
    Write-Success "ディレクトリ存在確認: $InstallPath"
}

# Create subdirectories
$subdirs = @("data", "logs", "config", "config\presets", "data\cache", "data\backups")
foreach ($subdir in $subdirs) {
    $path = Join-Path $InstallPath $subdir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}
Write-Success "サブディレクトリを作成しました"

Write-Host ""

# Step 6: Copy application files
Write-Info "Step 6/8: アプリケーションファイルのコピー..."

$currentDir = Get-Location
$filesToCopy = @(
    @{Source="local_bridge"; Dest="local_bridge"},
    @{Source="gui_qt"; Dest="gui_qt"},
    @{Source="mobile_web"; Dest="mobile_web"},
    @{Source="JunmaiAutoDev.lrdevplugin"; Dest="plugins\JunmaiAutoDev.lrdevplugin"},
    @{Source="requirements.txt"; Dest="requirements.txt"},
    @{Source="README.md"; Dest="README.md"}
)

foreach ($item in $filesToCopy) {
    $sourcePath = Join-Path $currentDir $item.Source
    $destPath = Join-Path $InstallPath $item.Dest
    
    if (Test-Path $sourcePath) {
        $destDir = Split-Path $destPath -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
        Write-Success "コピー完了: $($item.Source)"
    } else {
        Write-Warning "ファイルが見つかりません: $($item.Source)"
    }
}

Write-Host ""

# Step 7: Install Python dependencies
Write-Info "Step 7/8: Python 依存関係のインストール..."

Push-Location $InstallPath

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Info "仮想環境を作成中..."
    & python -m venv venv
    Write-Success "仮想環境を作成しました"
}

# Activate virtual environment and install dependencies
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    
    Write-Info "依存関係をインストール中..."
    & python -m pip install --upgrade pip
    & pip install -r requirements.txt
    Write-Success "依存関係のインストール完了"
} else {
    Write-Error "仮想環境のアクティベートに失敗しました"
}

Pop-Location

Write-Host ""

# Step 8: Initialize database
Write-Info "Step 8/8: データベースの初期化..."

Push-Location (Join-Path $InstallPath "local_bridge")

try {
    & python init_database.py
    Write-Success "データベースを初期化しました"
} catch {
    Write-Warning "データベースの初期化に失敗しました: $_"
}

Pop-Location

Write-Host ""

# Installation complete
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              インストールが完了しました！                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Info "次のステップ:"
Write-Host "  1. Lightroom Classic を起動"
Write-Host "  2. ファイル > プラグインマネージャー を開く"
Write-Host "  3. 追加ボタンをクリックし、以下のフォルダを選択:"
Write-Host "     $InstallPath\plugins\JunmaiAutoDev.lrdevplugin"
Write-Host ""
Write-Host "  4. 初期設定ウィザードを実行:"
Write-Host "     cd $InstallPath"
Write-Host "     venv\Scripts\activate"
Write-Host "     python setup_wizard.py"
Write-Host ""
Write-Host "  5. アプリケーションを起動:"
Write-Host "     cd $InstallPath\gui_qt"
Write-Host "     python main.py"
Write-Host ""

Write-Info "詳細は docs/INSTALLATION_GUIDE.md を参照してください"

# Create desktop shortcut
if (-not $Unattended) {
    $createShortcut = Read-Host "デスクトップにショートカットを作成しますか? (y/n)"
    if ($createShortcut -eq "y") {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Junmai AutoDev.lnk")
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$InstallPath\start.ps1`""
        $Shortcut.WorkingDirectory = $InstallPath
        $Shortcut.IconLocation = "$InstallPath\gui_qt\resources\icon.ico"
        $Shortcut.Save()
        Write-Success "デスクトップショートカットを作成しました"
    }
}

Write-Host ""
Write-Success "インストールスクリプトを終了します"
