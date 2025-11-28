# GitHub Codespaces Configuration

This directory contains the configuration for running the MCP PyCon Demo in GitHub Codespaces.

## What Gets Installed

### Features
- **Python 3.12+** - Runtime environment
- **Docker-in-Docker** - For running all services via docker-compose
- **AWS CLI** - For interacting with LocalStack (S3 emulation)
- **Common Utils** - Zsh, Oh My Zsh, and other helpful tools

### Extensions
- Python development tools (Pylance, Black, Ruff)
- Docker extension for container management
- YAML support for docker-compose files
- GitLens for enhanced Git integration
- GitHub Copilot (if available)

### Package Management
The project uses **uv** for fast, reliable Python dependency management. All dependencies from `pyproject.toml` are automatically installed.

## Automatic Setup

When you open this repository in Codespaces:

1. **Post-Create** (runs once on creation):
   - Installs `uv` package manager
   - Syncs all Python dependencies
   - Creates `.env` file from `.env.example`
   - Sets up shell script permissions

2. **Post-Start** (runs every time Codespace starts):
   - Starts Docker daemon
   - Launches all services via `docker compose up -d`:
     - LocalStack (S3 emulation)
     - Task API (FastAPI)
     - MCP Server (FastMCP)
     - Demo Client (Streamlit)
   - Displays service status and URLs

## Services & Ports

All ports are automatically forwarded and accessible:

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Streamlit Demo | 8501 | http://localhost:8501 | Interactive demo web app |
| Task API | 8000 | http://localhost:8000 | REST API for tasks |
| Task API Docs | 8000 | http://localhost:8000/docs | OpenAPI documentation |
| MCP Server | 8001 | http://localhost:8001 | MCP protocol bridge |
| LocalStack | 4566 | http://localhost:4566 | AWS S3 emulator |

## Configuration

### Required: GitHub API Key

The demo requires a GitHub Models API key. To set it up:

1. Get your key at: https://github.com/marketplace/models
2. Edit `.env` file in the workspace root
3. Set `GITHUB_API_KEY=your-key-here`
4. Restart the demo client: `docker compose restart demo-client`

### Environment Variables

All environment variables are pre-configured in `.env` for local development:
- `TASK_API_KEY` - API authentication key
- `AWS_*` - LocalStack S3 configuration
- `MCP_*` - MCP Server settings
- `GITHUB_API_KEY` - **YOU MUST SET THIS**

## Quick Commands

```bash
# View service logs
docker compose logs -f

# View specific service logs
docker compose logs -f task-api
docker compose logs -f mcp-server
docker compose logs -f demo-client

# Restart a service
docker compose restart task-api

# Stop all services
docker compose down

# Rebuild and restart all services
docker compose up -d --build

# Test the API
bash task_api/test_api.sh

# Install new Python packages
uv add package-name
uv sync

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .
```

## Troubleshooting

### Services not starting
```bash
# Check Docker status
docker info

# Restart Docker daemon (may require Codespace restart)
sudo systemctl restart docker

# Check service status
docker compose ps

# View detailed logs
docker compose logs
```

### Demo not connecting to MCP Server
```bash
# Check if MCP Server is healthy
curl http://localhost:8001/health

# Restart MCP Server
docker compose restart mcp-server
```

### LocalStack issues
```bash
# Check LocalStack health
curl http://localhost:4566/_localstack/health

# Recreate LocalStack
docker compose up -d --force-recreate localstack
```

### Missing GITHUB_API_KEY
The Streamlit demo will show an error if the key is missing. Edit `.env` and restart:
```bash
# Edit .env file and add your key
code .env

# Restart demo client
docker compose restart demo-client
```

## Development Workflow

1. **Make code changes** - Edit Python files in your preferred editor
2. **Services auto-reload** - FastAPI and Streamlit support hot reloading
3. **For MCP changes** - Restart: `docker compose restart mcp-server`
4. **For API changes** - Restart: `docker compose restart task-api`
5. **Format code** - `uv run black .`
6. **Run tests** - `uv run pytest`

## Architecture

The Codespace runs all services in Docker containers:

```
┌─────────────────────────────────────────────┐
│         GitHub Codespace (Ubuntu)           │
├─────────────────────────────────────────────┤
│  Docker Network: mcp-demo-network           │
│                                             │
│  ┌──────────────┐  ┌──────────────┐       │
│  │  LocalStack  │  │   Task API   │       │
│  │   (S3)       │◄─┤   (FastAPI)  │       │
│  └──────────────┘  └──────┬───────┘       │
│                            │                │
│                     ┌──────▼───────┐       │
│                     │  MCP Server  │       │
│                     │  (FastMCP)   │       │
│                     └──────┬───────┘       │
│                            │                │
│                     ┌──────▼───────┐       │
│                     │ Demo Client  │       │
│                     │ (Streamlit)  │       │
│                     └──────────────┘       │
└─────────────────────────────────────────────┘
         Ports forwarded to localhost
```

## VS Code Settings

The Codespace comes pre-configured with:
- Python interpreter pointing to uv-managed environment
- Black formatter (100 char line length)
- Ruff linter enabled
- Format on save
- Auto-import organization

## Additional Resources

- [Project README](../README.md) - Full project documentation
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [Task API Docs](http://localhost:8000/docs) - API reference (after starting)