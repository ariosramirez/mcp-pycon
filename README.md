# 🚀 MCP PyCon Demo: Bridging LLMs and Real-World APIs

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-purple.svg)](https://gofastmcp.com/)
[![AWS](https://img.shields.io/badge/AWS-App%20Runner-orange.svg)](https://aws.amazon.com/apprunner/)

A complete demonstration of the **Model Context Protocol (MCP)** showcasing how to securely bridge Large Language Models with real-world APIs.

## 🎯 The Challenge

When integrating LLMs with internal APIs, you face three critical problems:

1. **🌉 The Language Barrier**: LLMs speak natural language, APIs speak HTTP+JSON
2. **🔒 The Security Dilemma**: How to give LLMs API access without exposing credentials
3. **🎪 The Orchestration Burden**: Where does the business logic live?

**This demo solves all three elegantly using MCP.**

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Usuario   │─────▶│      LLM    │─────▶│ MCP Server  │─────▶│  Task API   │
│  (Español)  │◀─────│  (Reasoning)│◀─────│  (Bridge)   │◀─────│  (FastAPI)  │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                            │                      │                    │
                     Natural Language      API Key (Secure)      Stores in S3
                     Understanding         Translation Layer     JSON Files
```

### Components

- **Task API** ([FastAPI](task_api/)): RESTful API for managing users, calls, and tasks
- **MCP Server** ([FastMCP](mcp_server/)): Secure bridge exposing API as LLM tools with modern Python decorators
- **Demo Client** ([Streamlit](demo_client/)): Interactive web app showcasing the integration
- **S3 Storage**: Simple, persistent data layer (LocalStack for local dev)

## ✨ Features

- ✅ **FastMCP Framework**: Decorator-based MCP server with automatic schema generation
- ✅ **Secure Credential Isolation**: API keys never exposed to LLM
- ✅ **Natural Language Interface**: Spanish/English commands → API calls
- ✅ **Multi-step Orchestration**: Complex workflows handled intelligently
- ✅ **Complete CRUD Operations**: Users, scheduled calls, and tasks
- ✅ **Production-Ready**: FastAPI + AWS App Runner + S3
- ✅ **Interactive Demo**: Streamlit web app with visual scenarios
- ✅ **MCP Inspector**: Debug and test tools interactively
- ✅ **Docker Support**: Full containerized deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized setup)
- GitHub API Key (for LLM features)
- [More details](https://docs.google.com/document/d/1OwkOYV8CIKLso3VAw8lLu3D1z2Ke3nhi5X6zrANw1BQ/edit?usp=sharing)

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/mcp-pycon-demo
cd mcp-pycon-demo

# Set GitHub API key for LLM features
export GITHUB_API_KEY=your-github-token-here

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

**Services available at:**
- Task API: http://localhost:8000 ([docs](http://localhost:8000/docs))
- MCP Server: http://localhost:8001
- Streamlit Demo: http://localhost:8501
- LocalStack S3: http://localhost:4566

### Option 2: Local Development

```bash
# Install dependencies
uv sync
# OR
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - TASK_API_KEY
# - GITHUB_API_KEY
# - AWS configuration (for LocalStack: AWS_ENDPOINT_URL=http://localhost:4566)
```

**Start services in separate terminals:**

```bash
# Terminal 1: Start Task API (with LocalStack)
cd task_api
docker compose up -d
# OR run directly
python -m task_api.main

# Terminal 2: Start MCP Server
python -m mcp_server.server

# Terminal 3: Start Streamlit Demo
streamlit run demo_client/streamlit_app.py
```

## 🔍 MCP Inspector

Test and debug MCP tools interactively:

```bash
# Make sure Task API is running
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

Open http://localhost:5173 to:
- View all available tools with schemas
- Test tool calls with custom parameters
- Inspect request/response payloads
- Debug in real-time

**Example: Test `register_user` tool**
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "company": "Test Corp"
}
```

## 🎬 Demo Scenarios

The Streamlit demo showcases three scenarios demonstrating MCP's capabilities:

### Scenario 1: Register & Schedule
*"Por favor, registra a nuestro nuevo cliente 'Azollon International' con el contacto María García (maria@test-azollon.com) y agéndale una llamada de onboarding para este viernes a las 10am."*

**Demonstrates**: Multi-step orchestration, secure API calls

### Scenario 2: Query & Update
*"Muéstrame todas las llamadas pendientes y marca la primera como completada."*

**Demonstrates**: Data retrieval, intelligent processing, updates

### Scenario 3: Complex Workflow
*"Crea una tarea de seguimiento para todos los clientes que tienen llamadas programadas esta semana."*

**Demonstrates**: Complex reasoning, data aggregation, orchestration

## 🚀 Why FastMCP?

FastMCP reduces boilerplate by **60%** compared to traditional MCP SDK:

**Traditional MCP SDK:**
```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="...", inputSchema={...})]  # Manual JSON schema

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "register_user":  # Manual routing
        return [TextContent(type="text", text="...")]
```

**FastMCP:**
```python
@mcp.tool
async def register_user(
    name: Annotated[str, "Full name of the user"],
    email: Annotated[str, "Email address"],
) -> str:
    """Register a new user."""
    return "✅ User registered!"  # Auto-wrapped!
```

**Benefits:**
- Automatic schema generation from type hints
- Built-in parameter validation (Pydantic)
- Type-safe with modern Python features
- Cleaner error handling with `ToolError`

## 📚 API Overview

### Users
- `POST /users` - Register user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user details

### Scheduled Calls
- `POST /calls` - Schedule call
- `GET /calls` - List calls (filterable by user_id, status_filter)
- `PATCH /calls/{call_id}/status` - Update status

### Tasks
- `POST /tasks` - Create task
- `GET /tasks` - List tasks (filterable by user_id, status_filter)
- `PATCH /tasks/{task_id}/status` - Update status

### Authentication

All endpoints require `X-API-Key` header (except `/health`):

```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María García",
    "email": "maria@test-azollon.com",
    "company": "Azollon International"
  }'
```

**Default key:** `demo-secret-key-change-in-production`

## 🧪 Testing

### Quick Health Check

```bash
curl http://localhost:8000/health
```

### Test with Python

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:8000",
    headers={"X-API-Key": "demo-secret-key-change-in-production"}
)

# Create user
response = client.post("/users", json={
    "name": "María García",
    "email": "maria@test-azollon.com",
    "company": "Azollon International"
})
user = response.json()

# Schedule call
response = client.post("/calls", json={
    "user_id": user['id'],
    "title": "Onboarding Call",
    "scheduled_for": "2025-10-20T10:00:00Z",
    "duration_minutes": 30
})
```

## 🔒 Security Best Practices

1. **API Key Isolation**: Keys live ONLY in MCP Server environment, never exposed to LLM
2. **AWS Secrets Manager**: Use for production credential management
3. **HTTPS/TLS**: Always enable in production
4. **Key Rotation**: Implement regular rotation policy
5. **Access Logging**: Monitor all API calls and tool uses
6. **Least Privilege**: Grant minimal S3 permissions

## 🛠️ Project Structure

```
mcp-pycon-demo/
├── task_api/              # FastAPI application
│   ├── main.py           # API endpoints
│   ├── models.py         # Pydantic models
│   ├── storage.py        # S3 storage layer
│   ├── Dockerfile        # Container image
│   └── README.md         # API documentation
├── mcp_server/           # MCP Server
│   ├── server.py         # FastMCP implementation
│   └── README.md         # MCP server documentation
├── demo_client/          # Streamlit Demo
│   ├── streamlit_app.py  # Web UI
│   ├── langgraph_agent.py # LLM agent with LangGraph
│   └── azure_chat_wrapper.py # GitHub Models integration
├── docker-compose.yml    # Container orchestration
├── pyproject.toml        # Project metadata
└── README.md            # This file
```

## ➕ Adding New Tools

### 1. Add API Endpoint

In [task_api/main.py](task_api/main.py):

```python
@app.post("/your-endpoint")
async def your_endpoint(
    data: YourModel,
    api_key: str = Header(..., alias="X-API-Key")
):
    verify_api_key(api_key)
    return {"result": "success"}
```

### 2. Add MCP Tool

In [mcp_server/server.py](mcp_server/server.py):

```python
from typing import Annotated, Literal
from fastmcp.exceptions import ToolError
from pydantic import Field

@mcp.tool
async def your_new_tool(
    param: Annotated[str, "Parameter description"],
    count: Annotated[int, Field(ge=1, le=100)] = 10,
    status: Annotated[Literal["active", "inactive"] | None, "Filter"] = None
) -> str:
    """Tool description for LLM."""
    client = get_http_client()

    try:
        response = await client.post("/your-endpoint", json={"param": param})
        response.raise_for_status()
        return f"✅ Success: {response.json()}"
    except httpx.HTTPStatusError as e:
        raise ToolError(f"Failed: {e.response.json().get('message')}")
```

FastMCP handles schema generation, validation, and error formatting automatically!

## 🐳 Docker Commands

```bash
# Start all services
docker compose up -d

# View logs (all)
docker compose logs -f

# View logs (specific service)
docker compose logs -f task-api

# Rebuild and restart
docker compose up -d --build

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## 💡 Use Cases

This architecture is ideal for:

- **Internal Tool Integration**: Connect LLMs to company APIs securely
- **Multi-Service Orchestration**: Coordinate multiple microservices
- **Agent Architectures**: Build autonomous AI agents
- **Enterprise AI**: Production-grade LLM applications
- **API Democratization**: Natural language access to APIs

## 📖 Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **MCP Protocol**: https://modelcontextprotocol.io
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
- **FastAPI**: https://fastapi.tiangolo.com
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **GitHub Models**: https://github.com/marketplace/models

## 🎯 Challenge for Attendees

Want to extend the demo? Try the **PyCon Challenge**:

**[CHALLENGE.md](CHALLENGE.md)** - Step-by-step guide to add:
- 📊 Client Summary Tool (data aggregation)
- 📝 User Info Prompt (template generation)
- Complete with code, testing instructions, and troubleshooting

**Time:** 30-40 minutes | **Difficulty:** Intermediate

## 📁 Documentation

- [Task API README](task_api/README.md) - API endpoints, testing, Docker setup
- [MCP Server README](mcp_server/README.md) - MCP tools, FastMCP patterns, Inspector usage
- [CLAUDE.md](CLAUDE.md) - Development guidelines for Claude Code
- [CHALLENGE.md](CHALLENGE.md) - Hands-on challenge for workshop attendees

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for PyCon presentation
- Powered by FastMCP framework
- Anthropic's Model Context Protocol
- FastAPI for the web framework
- AWS for serverless infrastructure
- GitHub Models for LLM access

---

**¡Construyamos el futuro de la IA juntos!** 🚀
