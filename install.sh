#!/bin/bash

# Tipitaka PTS Browser - Installation Script for Linux
# Enhanced Edition with ROTA support, advanced search, and apparatus criticus

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Tipitaka PTS Browser"
APP_VERSION="1.0.0"
INSTALL_DIR="/opt/tipitaka-pts-browser"
DESKTOP_FILE="/usr/share/applications/tipitaka-pts-browser.desktop"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
BIN_SYMLINK="/usr/local/bin/tipitaka-pts-browser"
DATA_DIR="$HOME/.local/share/tipitaka-pts-browser"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Some user-specific configurations may not work correctly."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking system dependencies..."

    local missing_deps=()

    # Check for Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Found Python $PYTHON_VERSION"
    fi

    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("python3-pip")
    fi

    # Check for Qt dependencies (for Debian/Ubuntu)
    if [[ -f /etc/debian_version ]]; then
        if ! dpkg -l | grep -q "libqt6core6"; then
            missing_deps+=("libqt6core6")
        fi
        if ! dpkg -l | grep -q "libqt6gui6"; then
            missing_deps+=("libqt6gui6")
        fi
        if ! dpkg -l | grep -q "libqt6qml6"; then
            missing_deps+=("libqt6qml6")
        fi
    fi

    # Check for other dependencies
    if ! command -v sqlite3 &> /dev/null; then
        missing_deps+=("sqlite3")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"

        if [[ -f /etc/debian_version ]]; then
            print_info "You can install them with:"
            echo "sudo apt update && sudo apt install ${missing_deps[*]}"
        elif [[ -f /etc/redhat-release ]]; then
            print_info "You can install them with:"
            echo "sudo dnf install ${missing_deps[*]}"
        elif [[ -f /etc/arch-release ]]; then
            print_info "You can install them with:"
            echo "sudo pacman -S ${missing_deps[*]}"
        fi

        exit 1
    fi

    print_success "All dependencies are satisfied"
}

# Function to install Python packages
install_python_packages() {
    print_info "Installing Python packages..."

    # Create virtual environment if it doesn't exist
    if [[ ! -d "$INSTALL_DIR/venv" ]]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv "$INSTALL_DIR/venv"
    fi

    # Activate virtual environment and install packages
    source "$INSTALL_DIR/venv/bin/activate"

    # Install required packages
    pip install --upgrade pip

    # Check if setup.py exists
    if [[ -f "$INSTALL_DIR/src/setup.py" ]]; then
        print_info "Installing from setup.py..."
        pip install -e "$INSTALL_DIR"
    else
        print_info "Installing core dependencies..."
        pip install PyQt6 rapidfuzz python-Levenshtein charset-normalizer
    fi

    deactivate

    print_success "Python packages installed"
}

# Function to copy application files
copy_application_files() {
    print_info "Copying application files..."

    # Create installation directory
    sudo mkdir -p "$INSTALL_DIR"

    # Copy all files from current directory
    sudo cp -r ./* "$INSTALL_DIR/"

    # Set proper permissions
    sudo chmod -R 755 "$INSTALL_DIR"
    sudo chown -R root:root "$INSTALL_DIR"

    # Make main script executable
    if [[ -f "$INSTALL_DIR/AppRun" ]]; then
        sudo chmod +x "$INSTALL_DIR/AppRun"
    fi

    print_success "Application files copied to $INSTALL_DIR"
}

# Function to create data directory
create_data_directory() {
    print_info "Creating data directory..."

    mkdir -p "$DATA_DIR"

    # Check if data files exist in installation directory
    if [[ -d "$INSTALL_DIR/data" ]]; then
        print_info "Copying data files..."
        cp -r "$INSTALL_DIR/data"/* "$DATA_DIR/" 2>/dev/null || true
    fi

    # Set permissions for data directory
    chmod -R 755 "$DATA_DIR"

    print_success "Data directory created at $DATA_DIR"
}

# Function to create desktop entry
create_desktop_entry() {
    print_info "Creating desktop entry..."

    # Create icon directory if it doesn't exist
    sudo mkdir -p "$ICON_DIR"

    # Copy icon if it exists
    if [[ -f "$INSTALL_DIR/tipitaka-pts-browser.png" ]]; then
        sudo cp "$INSTALL_DIR/tipitaka-pts-browser.png" "$ICON_DIR/"
    fi

    # Create desktop file
    cat << EOF | sudo tee "$DESKTOP_FILE" > /dev/null
[Desktop Entry]
Type=Application
Name=Tipitaka PTS Browser
Comment=Browse and study Pali Tipitaka texts with ROTA edition support
Exec=$INSTALL_DIR/AppRun
Icon=tipitaka-pts-browser
Terminal=false
Categories=Education;Religion;
Keywords=Tipitaka;Pali;Buddhism;Text;Browser;
StartupNotify=true
EOF

    # Update desktop database
    sudo update-desktop-database

    print_success "Desktop entry created"
}

# Function to create symbolic link
create_symlink() {
    print_info "Creating symbolic link..."

    # Create wrapper script
    cat << EOF | sudo tee "$INSTALL_DIR/tipitaka-wrapper" > /dev/null
#!/bin/bash
# Wrapper script for Tipitaka PTS Browser

# Set data directory
export TIPITAKA_DATA_DIR="$DATA_DIR"

# Run the application
exec "$INSTALL_DIR/AppRun" "\$@"
EOF

    sudo chmod +x "$INSTALL_DIR/tipitaka-wrapper"

    # Create symlink
    sudo ln -sf "$INSTALL_DIR/tipitaka-wrapper" "$BIN_SYMLINK"

    print_success "Symbolic link created at $BIN_SYMLINK"
}

# Function to create uninstall script
create_uninstall_script() {
    print_info "Creating uninstall script..."

    cat << EOF | sudo tee "$INSTALL_DIR/uninstall.sh" > /dev/null
#!/bin/bash
# Uninstall script for Tipitaka PTS Browser

set -e

echo "Uninstalling Tipitaka PTS Browser..."

# Remove symbolic link
if [[ -L "/usr/local/bin/tipitaka-pts-browser" ]]; then
    sudo rm -f "/usr/local/bin/tipitaka-pts-browser"
    echo "Removed symbolic link"
fi

# Remove desktop entry
if [[ -f "/usr/share/applications/tipitaka-pts-browser.desktop" ]]; then
    sudo rm -f "/usr/share/applications/tipitaka-pts-browser.desktop"
    sudo update-desktop-database
    echo "Removed desktop entry"
fi

# Remove icon
if [[ -f "/usr/share/icons/hicolor/256x256/apps/tipitaka-pts-browser.png" ]]; then
    sudo rm -f "/usr/share/icons/hicolor/256x256/apps/tipitaka-pts-browser.png"
    echo "Removed icon"
fi

# Remove installation directory
if [[ -d "/opt/tipitaka-pts-browser" ]]; then
    sudo rm -rf "/opt/tipitaka-pts-browser"
    echo "Removed installation directory"
fi

# Ask about removing data directory
read -p "Remove user data directory (\$HOME/.local/share/tipitaka-pts-browser)? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]$ ]]; then
    rm -rf "\$HOME/.local/share/tipitaka-pts-browser"
    echo "Removed user data directory"
fi

echo "Uninstallation complete!"
EOF

    sudo chmod +x "$INSTALL_DIR/uninstall.sh"

    print_success "Uninstall script created at $INSTALL_DIR/uninstall.sh"
}

# Function to verify installation
verify_installation() {
    print_info "Verifying installation..."

    local errors=0

    # Check if installation directory exists
    if [[ ! -d "$INSTALL_DIR" ]]; then
        print_error "Installation directory not found: $INSTALL_DIR"
        errors=$((errors + 1))
    fi

    # Check if desktop entry exists
    if [[ ! -f "$DESKTOP_FILE" ]]; then
        print_error "Desktop entry not found: $DESKTOP_FILE"
        errors=$((errors + 1))
    fi

    # Check if symlink exists
    if [[ ! -L "$BIN_SYMLINK" ]]; then
        print_error "Symbolic link not found: $BIN_SYMLINK"
        errors=$((errors + 1))
    fi

    # Check if data directory exists
    if [[ ! -d "$DATA_DIR" ]]; then
        print_warning "Data directory not found: $DATA_DIR"
    fi

    if [[ $errors -eq 0 ]]; then
        print_success "Installation verified successfully"
        return 0
    else
        print_error "Installation verification failed with $errors error(s)"
        return 1
    fi
}

# Function to display usage information
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  install     Install Tipitaka PTS Browser (default)"
    echo "  uninstall   Uninstall Tipitaka PTS Browser"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install      # Install the application"
    echo "  $0 uninstall    # Uninstall the application"
    echo "  $0              # Same as 'install'"
}

# Function to uninstall
uninstall() {
    print_info "Starting uninstallation..."

    # Check if uninstall script exists
    if [[ -f "$INSTALL_DIR/uninstall.sh" ]]; then
        sudo bash "$INSTALL_DIR/uninstall.sh"
    else
        print_error "Uninstall script not found. Manual removal required."
        echo "To manually uninstall:"
        echo "1. sudo rm -f $BIN_SYMLINK"
        echo "2. sudo rm -f $DESKTOP_FILE"
        echo "3. sudo rm -f $ICON_DIR/tipitaka-pts-browser.png"
        echo "4. sudo rm -rf $INSTALL_DIR"
        echo "5. rm -rf $DATA_DIR (optional)"
    fi
}

# Main installation function
install() {
    print_info "Starting installation of $APP_NAME $APP_VERSION"
    echo

    # Check if already installed
    if [[ -d "$INSTALL_DIR" ]]; then
        print_warning "Tipitaka PTS Browser seems to be already installed at $INSTALL_DIR"
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
        print_info "Proceeding with reinstallation..."
    fi

    # Run installation steps
    check_root
    check_dependencies
    copy_application_files
    install_python_packages
    create_data_directory
    create_desktop_entry
    create_symlink
    create_uninstall_script

    # Verify installation
    if verify_installation; then
        echo
        print_success "========================================="
        print_success "  Tipitaka PTS Browser installed successfully!"
        print_success "========================================="
        echo
        echo "You can now run the application in several ways:"
        echo "1. From the terminal: tipitaka-pts-browser"
        echo "2. From application menu: Look for 'Tipitaka PTS Browser'"
        echo "3. From the installation directory: $INSTALL_DIR/AppRun"
        echo
        echo "Data directory: $DATA_DIR"
        echo "Uninstall script: $INSTALL_DIR/uninstall.sh"
        echo
        print_info "Note: Make sure you have the tipitaka.sqlite database file"
        print_info "in the data directory for full functionality."
        echo
    else
        print_error "Installation completed with errors. Please check the output above."
        exit 1
    fi
}

# Main script logic
main() {
    local action="${1:-install}"

    case "$action" in
        install|"")
            install
            ;;
        uninstall)
            uninstall
            ;;
        help|-h|--help)
            show_usage
            ;;
        *)
            print_error "Unknown action: $action"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
