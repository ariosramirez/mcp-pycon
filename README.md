# 🚀 MCP PyCon Demo: Bridging LLMs and Real-World APIs

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-0.9+-purple.svg)](https://modelcontextprotocol.io/)
[![AWS](https://img.shields.io/badge/AWS-App%20Runner-orange.svg)](https://aws.amazon.com/apprunner/)

A complete, demonstration of the **Model Context Protocol (MCP)** showcasing how to securely bridge Large Language Models with real-world APIs.

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

- **Task API** (FastAPI): RESTful API for managing users, calls, and tasks
- **MCP Server**: Secure bridge that exposes API as LLM tools
- **Demo Client**: Interactive presentation showcasing the integration
- **S3 Storage**: Simple, visual data persistence layer

## ✨ Features

- ✅ **Secure API Key Management**: Credentials never exposed to LLM
- ✅ **Natural Language Interface**: Spanish/English commands → API calls
- ✅ **Multi-step Orchestration**: Complex workflows handled intelligently
- ✅ **Complete CRUD Operations**: Users, scheduled calls, and tasks
- ✅ **Production-Ready**: FastAPI + AWS App Runner + S3
- ✅ **Interactive Demo**: Rich CLI presentation with scenarios
- ✅ **Docker Support**: Containerized deployment
- ✅ **Comprehensive Docs**: API documentation with Swagger UI

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- AWS Account (for S3 storage)
- Anthropic API Key (for Claude)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-pycon-demo
cd mcp-pycon-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Edit [.env](.env) file:

```bash
# Task API Configuration
TASK_API_KEY=your-secret-api-key-here
TASK_API_URL=http://localhost:8000

# AWS Configuration
AWS_REGION=us-east-2
AWS_S3_BUCKET=mcp-pycon-demo-bucket

# Github API Key (for demo client)
GITHUB_API_KEY=your-Github-api-key-here
```

### Running Locally

#### 1. Start the Task API

```bash
python -m task_api.main
```

The API will be available at http://localhost:8000

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 2. Start the MCP Server

In a new terminal:

```bash
python -m mcp_server.server
```

#### 3. Run the Interactive Demo

In another terminal:

```bash
python -m demo_client.client
```

This will launch an interactive presentation showcasing three scenarios:
1. Register user and schedule call
2. Query and update operations
3. Complex workflow orchestration

## 📚 API Documentation

### Endpoints

#### Users

- `POST /users` - Register a new user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user details

#### Scheduled Calls

- `POST /calls` - Schedule a call
- `GET /calls` - List all calls (filterable)
- `GET /calls/{call_id}` - Get call details
- `PATCH /calls/{call_id}/status` - Update call status

#### Tasks

- `POST /tasks` - Create a task
- `GET /tasks` - List all tasks (filterable)
- `GET /tasks/{task_id}` - Get task details
- `PATCH /tasks/{task_id}/status` - Update task status

#### Health

- `GET /health` - Health check (no auth required)

### Authentication

All endpoints (except `/health`) require an `X-API-Key` header:

```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María García",
    "email": "maria@techcorp.com",
    "company": "TechCorp International",
    "user_type": "client"
  }'
```

## 🧪 Testing

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Register a user
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Company"
  }'

# List users
curl http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### Testing with Python

```python
import httpx

client = httpx.Client(
    base_url="http://localhost:8000",
    headers={"X-API-Key": "demo-secret-key-change-in-production"}
)

# Create user
response = client.post("/users", json={
    "name": "María García",
    "email": "maria@techcorp.com",
    "company": "TechCorp International"
})
user = response.json()
print(f"Created user: {user['id']}")

# Schedule call
response = client.post("/calls", json={
    "user_id": user['id'],
    "title": "Onboarding Call",
    "scheduled_for": "2025-10-20T10:00:00Z",
    "duration_minutes": 30
})
call = response.json()
print(f"Scheduled call: {call['id']}")
```

## 🐳 Docker Deployment

### Build the image

```bash
docker build -f task_api/Dockerfile -t task-api:latest .
```

### Run locally with Docker

```bash
docker run -p 8000:8000 \
  -e TASK_API_KEY=your-secret-key \
  -e AWS_REGION=us-east-2 \
  -e AWS_S3_BUCKET=your-bucket \
  -e AWS_ACCESS_KEY_ID=your-access-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret-key \
  task-api:latest
```

## ☁️ AWS Deployment

### Prerequisites

- AWS CLI configured
- IAM role with S3 permissions
- App Runner service role

### Deploy to AWS App Runner

1. **Create S3 bucket**:

```bash
aws s3 mb s3://mcp-pycon-demo-bucket --region us-east-2
```

2. **Push to ECR** (or use GitHub integration):

```bash
# Create ECR repository
aws ecr create-repository --repository-name task-api

# Build and push
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-2.amazonaws.com
docker build -f task_api/Dockerfile -t task-api .
docker tag task-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-2.amazonaws.com/task-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-2.amazonaws.com/task-api:latest
```

3. **Create App Runner service**:

```bash
aws apprunner create-service \
  --service-name task-api-mcp-demo \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "YOUR_ACCOUNT.dkr.ecr.us-east-2.amazonaws.com/task-api:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "AWS_REGION": "us-east-2",
          "AWS_S3_BUCKET": "mcp-pycon-demo-bucket"
        }
      }
    }
  }' \
  --instance-configuration Cpu=1024,Memory=2048 \
  --region us-east-2
```

4. **Add secrets** via AWS Secrets Manager or App Runner console:
   - `TASK_API_KEY`

## 🎬 Demo Scenarios

The interactive demo showcases three scenarios:

### Scenario 1: Register & Schedule
**User says**: *"Por favor, registra a nuestro nuevo cliente 'TechCorp International' con el contacto María García (maria@techcorp.com) y agéndale una llamada de onboarding para este viernes a las 10am."*

**What happens**:
1. LLM understands the request
2. Calls `register_user` tool
3. Calls `schedule_call` tool
4. Returns confirmation

**Demonstrates**: Multi-step orchestration, secure API calls

### Scenario 2: Query & Update
**User says**: *"Muéstrame todas las llamadas pendientes y marca la primera como completada."*

**What happens**:
1. Calls `list_calls` with filter
2. Identifies first call
3. Calls `update_call_status`

**Demonstrates**: Data retrieval, intelligent processing, updates

### Scenario 3: Complex Workflow
**User says**: *"Crea una tarea de seguimiento para todos los clientes que tienen llamadas programadas esta semana."*

**What happens**:
1. Calls `list_calls` to get this week's calls
2. Extracts unique user IDs
3. Calls `create_task` for each user
4. Avoids duplicates

**Demonstrates**: Complex reasoning, data aggregation, orchestration

## 🔒 Security Best Practices

1. **Never expose API keys**: Keep them in MCP server only
2. **Use AWS Secrets Manager**: For production deployments
3. **Enable HTTPS**: Always use TLS in production
4. **Rotate keys regularly**: Implement key rotation policy
5. **Monitor access**: Log all API calls and tool uses
6. **Principle of least privilege**: Grant minimal S3 permissions

## 🛠️ Development

### Project Structure

```
mcp-pycon-demo/
├── task_api/              # FastAPI application
│   ├── __init__.py
│   ├── main.py           # API endpoints
│   ├── models.py         # Pydantic models
│   ├── storage.py        # S3 storage layer
│   └── config.py         # Configuration
├── mcp_server/           # MCP Server
│   ├── __init__.py
│   └── server.py         # MCP implementation
├── demo_client/          # Demo client
│   ├── __init__.py
│   └── client.py         # Interactive demo
├── demo/                 # Demo materials
│   ├── demo_script.md
│   └── example_usage.py
├── requirements.txt      # Dependencies
├── pyproject.toml        # Project metadata
└── README.md            # This file

Note: Deployment files (Dockerfile, apprunner.yaml, deploy.sh) are located in the task_api/ directory.
```

### Adding New Tools

To add a new MCP tool:

1. Add API endpoint in [task_api/main.py](task_api/main.py)
2. Add tool definition in [mcp_server/server.py](mcp_server/server.py) `list_tools()`
3. Add tool handler in [mcp_server/server.py](mcp_server/server.py) `call_tool()`

Example:

```python
# In list_tools()
Tool(
    name="your_new_tool",
    description="What this tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
)

# In call_tool()
elif name == "your_new_tool":
    response = await client.post("/your-endpoint", json=arguments)
    response.raise_for_status()
    return [TextContent(type="text", text="Result")]
```

## 📖 Resources

- **MCP Documentation**: https://modelcontextprotocol.io
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **AWS App Runner**: https://aws.amazon.com/apprunner/
- **Anthropic Claude**: https://anthropic.com/claude

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for PyCon presentation
- Powered by Anthropic's MCP and Claude
- FastAPI for the excellent framework
- AWS for serverless infrastructure

## 💡 Use Cases

This architecture is perfect for:

- **Internal Tool Integration**: Connect LLMs to company APIs securely
- **Multi-Service Orchestration**: Coordinate multiple microservices
- **Agent Architectures**: Build autonomous AI agents
- **Enterprise AI**: Production-grade LLM applications
- **API Democratization**: Make APIs accessible via natural language

## 📧 Contact

Have questions or feedback? Open an issue or reach out!

---

**¡Construyamos el futuro de la IA juntos!** 🚀
