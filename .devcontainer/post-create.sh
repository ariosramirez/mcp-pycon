#!/bin/bash
# Post-create script for Codespaces
# Runs once when the Codespace is first created

set -e

echo "🚀 Running post-create setup..."

# Navigate to workspace (Codespaces default is /workspaces/<repo-name>)
cd "${CODESPACE_VSCODE_FOLDER:-$(pwd)}"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Sync dependencies using uv
echo "📦 Installing Python dependencies with uv..."
uv sync

# Install development dependencies
echo "🛠️  Installing development dependencies..."
uv sync --extra dev

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please add your GITHUB_API_KEY to the .env file"
    echo "   Get your key at: https://github.com/marketplace/models"
fi

# Set permissions for shell scripts
chmod +x .devcontainer/post-start.sh 2>/dev/null || true
chmod +x task_api/test_api.sh 2>/dev/null || true

echo ""
echo "✅ Post-create setup complete!"
echo ""
echo "📚 Next steps:"
echo "   1. Add your GITHUB_API_KEY to .env file"
echo "   2. Services will start automatically"
echo "   3. Access Streamlit demo at http://localhost:8501"
echo "   4. API docs at http://localhost:8000/docs"