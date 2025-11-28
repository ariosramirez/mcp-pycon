#!/bin/bash
# Post-start script for Codespaces
# Runs every time the Codespace starts

set -e

echo "🔄 Running post-start setup..."

# Navigate to workspace
cd /workspace

# Wait for Docker to be ready
echo "⏳ Waiting for Docker to be ready..."
timeout=60
elapsed=0
while ! docker info > /dev/null 2>&1; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Docker failed to start within ${timeout}s"
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done
echo "✅ Docker is ready"

# Start all services with docker-compose
echo "🐳 Starting all services (LocalStack, Task API, MCP Server, Demo Client)..."
docker compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

# Show service URLs
echo ""
echo "🌐 Service URLs:"
echo "   - Streamlit Demo: http://localhost:8501"
echo "   - Task API: http://localhost:8000"
echo "   - Task API Docs: http://localhost:8000/docs"
echo "   - MCP Server: http://localhost:8001"
echo "   - LocalStack: http://localhost:4566"
echo ""

# Check if GITHUB_API_KEY is set
if grep -q "GITHUB_API_KEY=$" .env 2>/dev/null || [ -z "$(grep GITHUB_API_KEY .env 2>/dev/null | cut -d'=' -f2)" ]; then
    echo "⚠️  WARNING: GITHUB_API_KEY is not set in .env file"
    echo "   The demo will not work without this key."
    echo "   Get your key at: https://github.com/marketplace/models"
    echo ""
fi

echo "✅ Post-start setup complete!"
echo ""
echo "💡 Quick commands:"
echo "   - View logs: docker compose logs -f"
echo "   - Stop services: docker compose down"
echo "   - Restart services: docker compose restart"
echo "   - Test API: bash task_api/test_api.sh"
