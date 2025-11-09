#!/bin/bash
# Junmai AutoDev - macOS Uninstaller Script
# Version: 2.0

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Output functions
success() { echo -e "${GREEN}✁E{NC} $1"; }
info() { echo -e "${CYAN}ℹ${NC} $1"; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✁E{NC} $1"; }

# Default values
INSTALL_PATH="$HOME/JunmaiAutoDev"
KEEP_DATA=false
UNATTENDED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-data)
            KEEP_DATA=true
            shift
            ;;
        --unattended)
            UNATTENDED=true
            shift
            ;;
        --install-path)
            INSTALL_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Banner
cat << "EOF"

╔═══════════════════════════════════════════════════════════╁E╁E                                                          ╁E╁E         Junmai AutoDev - アンインスト�Eラー              ╁E╁E                                                          ╁E╚═══════════════════════════════════════════════════════════╁E
EOF

warning "こ�Eスクリプトは Junmai AutoDev をアンインスト�EルしまぁE
info "インスト�Eル允E $INSTALL_PATH"

if ! $UNATTENDED; then
    read -p "続行しますか? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        info "アンインスト�Eルをキャンセルしました"
        exit 0
    fi
fi

echo ""

# Step 1: Stop running processes
info "Step 1/5: 実行中のプロセスを停止中..."

# Stop Python processes
PYTHON_PIDS=$(pgrep -f "$INSTALL_PATH.*python" || true)
if [ -n "$PYTHON_PIDS" ]; then
    echo "$PYTHON_PIDS" | xargs kill -9 2>/dev/null || true
    success "Python プロセスを停止しました"
fi

# Stop Redis (if managed by this installation)
if brew services list | grep redis | grep started > /dev/null 2>&1; then
    info "Redis サービスは実行中です（他�Eアプリケーションで使用されてぁE��可能性があります！E
fi

# Stop Ollama (if managed by this installation)
OLLAMA_PIDS=$(pgrep -x "ollama" || true)
if [ -n "$OLLAMA_PIDS" ]; then
    info "Ollama サービスは実行中です（他�Eアプリケーションで使用されてぁE��可能性があります！E
fi

echo ""

# Step 2: Remove Lightroom plugin
info "Step 2/5: Lightroom プラグインを削除中..."

PLUGIN_PATH="$HOME/Library/Application Support/Adobe/Lightroom/Modules/JunmaiAutoDev.lrdevplugin"
if [ -d "$PLUGIN_PATH" ]; then
    rm -rf "$PLUGIN_PATH"
    success "プラグインを削除しました"
else
    info "プラグインが見つかりません�E�スキチE�E�E�E
fi

echo ""

# Step 3: Backup data (if requested)
if $KEEP_DATA; then
    info "Step 3/5: チE�EタをバチE��アチE�E中..."
    
    BACKUP_PATH="$HOME/Documents/JunmaiAutoDev_Backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_PATH"
    
    DATA_ITEMS=("data" "logs" "config")
    for item in "${DATA_ITEMS[@]}"; do
        SOURCE_PATH="$INSTALL_PATH/$item"
        if [ -e "$SOURCE_PATH" ]; then
            cp -R "$SOURCE_PATH" "$BACKUP_PATH/"
            success "バックアチE�E: $item"
        fi
    done
    
    success "バックアチE�E允E $BACKUP_PATH"
else
    info "Step 3/5: チE�EタバックアチE�EをスキチE�E"
fi

echo ""

# Step 4: Remove installation directory
info "Step 4/5: インスト�EルチE��レクトリを削除中..."

if [ -d "$INSTALL_PATH" ]; then
    rm -rf "$INSTALL_PATH"
    success "チE��レクトリを削除: $INSTALL_PATH"
else
    info "インスト�EルチE��レクトリが見つかりません"
fi

echo ""

# Step 5: Remove launch script from Applications
info "Step 5/5: アプリケーションショートカチE��を削除中..."

APP_SHORTCUT="$HOME/Applications/Junmai AutoDev.app"
if [ -d "$APP_SHORTCUT" ]; then
    rm -rf "$APP_SHORTCUT"
    success "ショートカチE��を削除しました"
else
    info "ショートカチE��が見つかりません�E�スキチE�E�E�E
fi

echo ""

# Completion message
cat << "EOF"

╔═══════════════════════════════════════════════════════════╁E╁E                                                          ╁E╁E         アンインスト�Eルが完亁E��ました                    ╁E╁E                                                          ╁E╚═══════════════════════════════════════════════════════════╁E
EOF

info "以下�Eコンポ�Eネント�E手動でアンインスト�Eルしてください:"
echo "  - Python (忁E��に応じて)"
echo "  - Redis (忁E��に応じて): brew uninstall redis"
echo "  - Ollama (忁E��に応じて): brew uninstall ollama"
echo ""

if $KEEP_DATA; then
    info "チE�Eタは以下�E場所にバックアチE�EされてぁE��ぁE"
    echo "  $BACKUP_PATH"
    echo ""
fi

success "アンインスト�Eルスクリプトを終亁E��まぁE
