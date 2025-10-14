set -e

VENV_DIR="venv"

echo "Setting up MCRAG Python environment with UV..."

# Function to install UV if not present
install_uv() {
    if ! command -v uv &> /dev/null; then
        echo "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        echo "UV installed"
    else
        echo "UV already installed"
    fi
}

# Function to create virtual environment with UV
create_venv() {
    echo "Creating virtual environment with UV..."
    uv venv $VENV_DIR
    echo "Virtual environment created"
}

# Function to install dependencies with UV
install_deps() {
    echo "Installing dependencies with UV (super fast!)..."
    source $VENV_DIR/bin/activate
    uv pip install -r requirements.txt
    deactivate
    echo "Dependencies installed"
}

# Main setup process
main() {
    # Install UV if needed
    install_uv
    
    # Remove existing venv if present
    if [ -d "$VENV_DIR" ]; then
        echo "Removing existing virtual environment..."
        rm -rf $VENV_DIR
    fi
    
    # Create new virtual environment
    create_venv
    
    # Install dependencies
    install_deps
    
    echo ""
    echo "Virtual environment setup complete with UV!"
    echo "Location: $(pwd)/$VENV_DIR"
    echo "To activate: source $VENV_DIR/bin/activate"
    echo "To deactivate: deactivate"
    echo ""
    echo "Next steps:"
    echo "   1. Run: ./start-dev.sh"
    echo "   2. Or manually: source $VENV_DIR/bin/activate && python backend/server.py"
}

# Run main function
main "$@"