#!/bin/bash
# Junmai AutoDev - macOS Installer Script
# Version: 2.0
# Requires: macOS 12+ (Monterey or later)

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Output functions
success() { echo -e "${GREEN}笨・{NC} $1"; }
info() { echo -e "${CYAN}邃ｹ${NC} $1"; }
warning() { echo -e "${YELLOW}笞${NC} $1"; }
error() { echo -e "${RED}笨・{NC} $1"; }

# Default values
INSTALL_PATH="$HOME/JunmaiAutoDev"
SKIP_DEPENDENCIES=false
SKIP_OLLAMA=false
SKIP_REDIS=false
UNATTENDED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-dependencies)
            SKIP_DEPENDENCIES=true
            shift
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        --skip-redis)
            SKIP_REDIS=true
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

笊披武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊・笊・                                                          笊・笊・           Junmai AutoDev - macOS Installer              笊・笊・                                                          笊・笊・    Lightroom ﾃ・LLM 閾ｪ蜍慕樟蜒上す繧ｹ繝・Β                      笊・笊・                                                          笊・笊壺武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊・
EOF

info "繧､繝ｳ繧ｹ繝医・繝ｫ蜈・ $INSTALL_PATH"
echo ""

# Step 1: Check system requirements
info "Step 1/8: 繧ｷ繧ｹ繝・Β隕∽ｻｶ縺ｮ遒ｺ隱・.."

# Check macOS version
OS_VERSION=$(sw_vers -productVersion)
MAJOR_VERSION=$(echo $OS_VERSION | cut -d. -f1)
if [ "$MAJOR_VERSION" -lt 12 ]; then
    error "macOS 12 (Monterey) 莉･荳翫′蠢・ｦ√〒縺・
    exit 1
fi
success "OS: macOS $OS_VERSION"

# Check available disk space
FREE_SPACE=$(df -g "$HOME" | awk 'NR==2 {print $4}')
if [ "$FREE_SPACE" -lt 50 ]; then
    warning "繝・ぅ繧ｹ繧ｯ遨ｺ縺榊ｮｹ驥上′荳崎ｶｳ縺励※縺・∪縺・ ${FREE_SPACE} GB"
fi
success "繝・ぅ繧ｹ繧ｯ遨ｺ縺榊ｮｹ驥・ ${FREE_SPACE} GB"

# Check for Apple Silicon or Intel
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    success "繝励Ο繧ｻ繝・し: Apple Silicon (M1/M2/M3)"
elif [ "$ARCH" = "x86_64" ]; then
    success "繝励Ο繧ｻ繝・し: Intel"
else
    warning "荳肴・縺ｪ繝励Ο繧ｻ繝・し繧｢繝ｼ繧ｭ繝・け繝√Ε: $ARCH"
fi

echo ""

# Step 2: Install Homebrew
if ! $SKIP_DEPENDENCIES; then
    info "Step 2/8: Homebrew 縺ｮ遒ｺ隱・.."
    
    if command -v brew &> /dev/null; then
        success "Homebrew 繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩"
    else
        warning "Homebrew 縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ"
        
        if ! $UNATTENDED; then
            read -p "Homebrew 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺吶°? (y/n): " install_brew
            if [ "$install_brew" = "y" ]; then
                info "Homebrew 繧偵う繝ｳ繧ｹ繝医・繝ｫ荳ｭ..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                success "Homebrew 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺励◆"
            else
                error "Homebrew 縺悟ｿ・ｦ√〒縺吶ゅう繝ｳ繧ｹ繝医・繝ｫ蠕後↓蜀榊ｮ溯｡後＠縺ｦ縺上□縺輔＞"
                exit 1
            fi
        fi
    fi
else
    info "Step 2/8: Homebrew 繝√ぉ繝・け繧偵せ繧ｭ繝・・"
fi

echo ""

# Step 3: Install Python
if ! $SKIP_DEPENDENCIES; then
    info "Step 3/8: Python 縺ｮ繧､繝ｳ繧ｹ繝医・繝ｫ遒ｺ隱・.."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        success "Python 繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩: $PYTHON_VERSION"
    else
        warning "Python 縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ"
        
        if ! $UNATTENDED; then
            read -p "Homebrew 縺ｧ Python 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺吶°? (y/n): " install_python
            if [ "$install_python" = "y" ]; then
                brew install python@3.11
                success "Python 3.11 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺励◆"
            else
                error "Python 縺悟ｿ・ｦ√〒縺吶ゅう繝ｳ繧ｹ繝医・繝ｫ蠕後↓蜀榊ｮ溯｡後＠縺ｦ縺上□縺輔＞"
                exit 1
            fi
        fi
    fi
else
    info "Step 3/8: Python 繝√ぉ繝・け繧偵せ繧ｭ繝・・"
fi

echo ""

# Step 4: Install Redis
if ! $SKIP_REDIS && ! $SKIP_DEPENDENCIES; then
    info "Step 4/8: Redis 縺ｮ繧､繝ｳ繧ｹ繝医・繝ｫ遒ｺ隱・.."
    
    if command -v redis-server &> /dev/null; then
        success "Redis 繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩"
        
        # Check if Redis is running
        if brew services list | grep redis | grep started &> /dev/null; then
            success "Redis 繧ｵ繝ｼ繝薙せ螳溯｡御ｸｭ"
        else
            info "Redis 繧ｵ繝ｼ繝薙せ繧定ｵｷ蜍穂ｸｭ..."
            brew services start redis
            success "Redis 繧ｵ繝ｼ繝薙せ繧定ｵｷ蜍輔＠縺ｾ縺励◆"
        fi
    else
        warning "Redis 縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ"
        
        if ! $UNATTENDED; then
            read -p "Homebrew 縺ｧ Redis 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺吶°? (y/n): " install_redis
            if [ "$install_redis" = "y" ]; then
                brew install redis
                brew services start redis
                success "Redis 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∬ｵｷ蜍輔＠縺ｾ縺励◆"
            fi
        fi
    fi
else
    info "Step 4/8: Redis 繝√ぉ繝・け繧偵せ繧ｭ繝・・"
fi

echo ""

# Step 5: Install Ollama
if ! $SKIP_OLLAMA && ! $SKIP_DEPENDENCIES; then
    info "Step 5/8: Ollama 縺ｮ繧､繝ｳ繧ｹ繝医・繝ｫ遒ｺ隱・.."
    
    if command -v ollama &> /dev/null; then
        success "Ollama 繧､繝ｳ繧ｹ繝医・繝ｫ貂医∩"
        
        # Check if Ollama service is running
        if pgrep -x "ollama" > /dev/null; then
            success "Ollama 繧ｵ繝ｼ繝薙せ螳溯｡御ｸｭ"
        else
            info "Ollama 繧ｵ繝ｼ繝薙せ繧定ｵｷ蜍穂ｸｭ..."
            ollama serve &> /dev/null &
            sleep 2
            success "Ollama 繧ｵ繝ｼ繝薙せ繧定ｵｷ蜍輔＠縺ｾ縺励◆"
        fi
        
        # Check if model is downloaded
        if ollama list | grep "llama3.1" &> /dev/null; then
            success "Llama 3.1 繝｢繝・Ν 繝繧ｦ繝ｳ繝ｭ繝ｼ繝画ｸ医∩"
        else
            info "Llama 3.1 繝｢繝・Ν繧偵ム繧ｦ繝ｳ繝ｭ繝ｼ繝我ｸｭ..."
            ollama pull llama3.1:8b-instruct
            success "Llama 3.1 繝｢繝・Ν 繝繧ｦ繝ｳ繝ｭ繝ｼ繝牙ｮ御ｺ・
        fi
    else
        warning "Ollama 縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ"
        
        if ! $UNATTENDED; then
            read -p "Homebrew 縺ｧ Ollama 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺吶°? (y/n): " install_ollama
            if [ "$install_ollama" = "y" ]; then
                brew install ollama
                ollama serve &> /dev/null &
                sleep 2
                success "Ollama 繧偵う繝ｳ繧ｹ繝医・繝ｫ縺励∪縺励◆"
                
                info "Llama 3.1 繝｢繝・Ν繧偵ム繧ｦ繝ｳ繝ｭ繝ｼ繝我ｸｭ..."
                ollama pull llama3.1:8b-instruct
                success "Llama 3.1 繝｢繝・Ν 繝繧ｦ繝ｳ繝ｭ繝ｼ繝牙ｮ御ｺ・
            fi
        fi
    fi
else
    info "Step 5/8: Ollama 繝√ぉ繝・け繧偵せ繧ｭ繝・・"
fi

echo ""

# Step 6: Create installation directory
info "Step 6/8: 繧､繝ｳ繧ｹ繝医・繝ｫ繝・ぅ繝ｬ繧ｯ繝医Μ縺ｮ菴懈・..."

if [ ! -d "$INSTALL_PATH" ]; then
    mkdir -p "$INSTALL_PATH"
    success "繝・ぅ繝ｬ繧ｯ繝医Μ繧剃ｽ懈・: $INSTALL_PATH"
else
    success "繝・ぅ繝ｬ繧ｯ繝医Μ蟄伜惠遒ｺ隱・ $INSTALL_PATH"
fi

# Create subdirectories
SUBDIRS=("data" "logs" "config" "config/presets" "data/cache" "data/backups")
for subdir in "${SUBDIRS[@]}"; do
    mkdir -p "$INSTALL_PATH/$subdir"
done
success "繧ｵ繝悶ョ繧｣繝ｬ繧ｯ繝医Μ繧剃ｽ懈・縺励∪縺励◆"

echo ""

# Step 7: Copy application files
info "Step 7/8: 繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ繝輔ぃ繧､繝ｫ縺ｮ繧ｳ繝斐・..."

CURRENT_DIR=$(pwd)
FILES_TO_COPY=(
    "local_bridge:local_bridge"
    "gui_qt:gui_qt"
    "mobile_web:mobile_web"
    "JunmaiAutoDev.lrdevplugin:plugins/JunmaiAutoDev.lrdevplugin"
    "requirements.txt:requirements.txt"
    "README.md:README.md"
)

for item in "${FILES_TO_COPY[@]}"; do
    SOURCE="${item%%:*}"
    DEST="${item##*:}"
    
    if [ -e "$CURRENT_DIR/$SOURCE" ]; then
        DEST_DIR="$INSTALL_PATH/$(dirname "$DEST")"
        mkdir -p "$DEST_DIR"
        cp -R "$CURRENT_DIR/$SOURCE" "$INSTALL_PATH/$DEST"
        success "繧ｳ繝斐・螳御ｺ・ $SOURCE"
    else
        warning "繝輔ぃ繧､繝ｫ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ: $SOURCE"
    fi
done

echo ""

# Step 8: Install Python dependencies
info "Step 8/8: Python 萓晏ｭ倬未菫ゅ・繧､繝ｳ繧ｹ繝医・繝ｫ..."

cd "$INSTALL_PATH"

# Create virtual environment
if [ ! -d "venv" ]; then
    info "莉ｮ諠ｳ迺ｰ蠅・ｒ菴懈・荳ｭ..."
    python3 -m venv venv
    success "莉ｮ諠ｳ迺ｰ蠅・ｒ菴懈・縺励∪縺励◆"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate

info "萓晏ｭ倬未菫ゅｒ繧､繝ｳ繧ｹ繝医・繝ｫ荳ｭ..."
pip install --upgrade pip
pip install -r requirements.txt
success "萓晏ｭ倬未菫ゅ・繧､繝ｳ繧ｹ繝医・繝ｫ螳御ｺ・

# Initialize database
info "繝・・繧ｿ繝吶・繧ｹ縺ｮ蛻晄悄蛹・.."
cd "$INSTALL_PATH/local_bridge"
python init_database.py && success "繝・・繧ｿ繝吶・繧ｹ繧貞・譛溷喧縺励∪縺励◆" || warning "繝・・繧ｿ繝吶・繧ｹ縺ｮ蛻晄悄蛹悶↓螟ｱ謨励＠縺ｾ縺励◆"

cd "$INSTALL_PATH"

echo ""

# Installation complete
cat << "EOF"

笊披武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊・笊・                                                          笊・笊・             繧､繝ｳ繧ｹ繝医・繝ｫ縺悟ｮ御ｺ・＠縺ｾ縺励◆・・                 笊・笊・                                                          笊・笊壺武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊絶武笊・
EOF

info "谺｡縺ｮ繧ｹ繝・ャ繝・"
echo "  1. Lightroom Classic 繧定ｵｷ蜍・
echo "  2. 繝輔ぃ繧､繝ｫ > 繝励Λ繧ｰ繧､繝ｳ繝槭ロ繝ｼ繧ｸ繝｣繝ｼ 繧帝幕縺・
echo "  3. 霑ｽ蜉繝懊ち繝ｳ繧偵け繝ｪ繝・け縺励∽ｻ･荳九・繝輔か繝ｫ繝繧帝∈謚・"
echo "     $INSTALL_PATH/plugins/JunmaiAutoDev.lrdevplugin"
echo ""
echo "  4. 蛻晄悄險ｭ螳壹え繧｣繧ｶ繝ｼ繝峨ｒ螳溯｡・"
echo "     cd $INSTALL_PATH"
echo "     source venv/bin/activate"
echo "     python setup_wizard.py"
echo ""
echo "  5. 繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ繧定ｵｷ蜍・"
echo "     cd $INSTALL_PATH/gui_qt"
echo "     python main.py"
echo ""

info "隧ｳ邏ｰ縺ｯ docs/INSTALLATION_GUIDE.md 繧貞盾辣ｧ縺励※縺上□縺輔＞"

# Create launch script
cat > "$INSTALL_PATH/start.sh" << 'LAUNCH_SCRIPT'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
cd gui_qt
python main.py
LAUNCH_SCRIPT

chmod +x "$INSTALL_PATH/start.sh"
success "襍ｷ蜍輔せ繧ｯ繝ｪ繝励ヨ繧剃ｽ懈・縺励∪縺励◆: $INSTALL_PATH/start.sh"

echo ""
success "繧､繝ｳ繧ｹ繝医・繝ｫ繧ｹ繧ｯ繝ｪ繝励ヨ繧堤ｵゆｺ・＠縺ｾ縺・
