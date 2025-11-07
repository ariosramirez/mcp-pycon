# 🔌 MCP Server - FastMCP Bridge to Task API

A secure Model Context Protocol (MCP) server built with FastMCP that exposes the Task API as LLM-callable tools. Acts as a secure bridge, keeping API credentials isolated from LLMs while enabling natural language interactions.

## 🚀 Quick Start

### Prerequisites

1. **Task API running**: `docker compose up -d task-api`
2. **Environment configured**: Copy `.env.example` to `.env` and set `TASK_API_KEY`

### Launch with MCP Inspector (Recommended)

```bash
# Make sure Task API is running first
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

Open http://localhost:5173 to test tools interactively.

### Direct Execution

```bash
python -m mcp_server.server
```

Server starts in stdio mode, ready for MCP client connections.

---

## 🔍 Using MCP Inspector

The Inspector provides a web UI to test tools without building a full client.

### Test Flow Example

1. **Register a user** → Save the user ID
2. **List users** → Verify user appears
3. **Schedule a call** → Use the user ID
4. **Create a task** → Associate with user
5. **Update statuses** → Mark call/task as completed

See [Complete Testing Flow](#complete-testing-flow) section for detailed examples.

---

## 🛠️ Available Tools

**User Management:** `register_user`, `list_users`, `get_user`
**Call Scheduling:** `schedule_call`, `list_calls`, `update_call_status`
**Task Management:** `create_task`, `list_tasks`, `update_task_status`

### Tool Parameter Patterns

```json
// register_user
{
  "name": "María García",
  "email": "maria@example.com",
  "company": "Test Corp",
  "user_type": "client"  // client|prospect|partner
}

// schedule_call
{
  "user_id": "uuid-here",
  "title": "Onboarding Call",
  "scheduled_for": "2025-10-25T10:00:00Z",
  "duration_minutes": 30
}

// create_task
{
  "title": "Prepare materials",
  "description": "Create deck",
  "user_id": "uuid-here"
}

// Filters (optional)
{
  "user_id": "uuid-here",
  "status": "scheduled"  // or "completed", "cancelled", etc.
}
```

---

## 🏗️ Architecture

### Security Model

```
LLM/User ──MCP──> MCP Server (has API key) ──HTTP+Key──> Task API ──> S3
```

**Critical:** API key lives ONLY in MCP Server environment, NEVER exposed to LLM.

### Request Flow

1. LLM sends tool call via MCP protocol
2. MCP Server validates parameters (FastMCP)
3. Server injects API key into HTTP headers
4. Makes authenticated request to Task API
5. Formats response for LLM

### Why FastMCP?

Traditional MCP SDK requires 60% more code with manual JSON schema definitions and routing logic. FastMCP uses decorators and Python type hints for automatic schema generation.

**Before (Traditional):**
```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="...", inputSchema={...})]  # Manual JSON schema

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "register_user":  # Manual routing
        return [TextContent(type="text", text="...")]  # Manual wrapping
```

**After (FastMCP):**
```python
@mcp.tool
async def register_user(
    name: Annotated[str, "Full name"],
    email: Annotated[str, "Email address"],
) -> str:
    """Register a new user."""
    return "✅ User registered!"  # Auto-wrapped!
```

---

## ➕ Adding New Tools

### Step 1: Add API Endpoint

In [task_api/main.py](../task_api/main.py):

```python
@app.post("/your-endpoint")
async def your_endpoint(
    data: YourModel,
    api_key: str = Header(..., alias="X-API-Key")
):
    verify_api_key(api_key)
    return {"result": "success"}
```

### Step 2: Add MCP Tool

In [mcp_server/server.py](server.py):

```python
from typing import Annotated, Literal
from fastmcp.exceptions import ToolError
from pydantic import Field

@mcp.tool
async def your_new_tool(
    param1: Annotated[str, "Description of param1"],
    count: Annotated[int, Field(ge=1, le=100, description="Count (1-100)")] = 10,
    status: Annotated[Literal["active", "inactive"], "Status filter"] = "active"
) -> str:
    """What this tool does.

    Detailed description for LLM to understand when to use this tool.
    """
    client = get_http_client()

    try:
        payload = {"param1": param1, "count": count}
        response = await client.post("/your-endpoint", json=payload)
        response.raise_for_status()
        result = response.json()

        return f"✅ Action completed!\n\nDetails:\n{result}"
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error: {error_detail}")
        raise ToolError(f"Failed: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        raise ToolError(f"Error: {str(e)}")
```

### FastMCP Type Annotation Patterns

```python
# Simple description
param: Annotated[str, "Description"]

# With validation
count: Annotated[int, Field(ge=1, le=100, description="Count 1-100")]

# Enum choices (use Literal | None for optional filters)
status: Annotated[Literal["active", "inactive"] | None, "Status"] = None

# Optional with default
notes: Annotated[str, "Optional notes"] = ""
```

**Return Values:**
- Return `str` directly (FastMCP auto-converts to TextContent)
- Use emojis (✅, ❌) for clarity
- Format with newlines for readability

**Error Handling:**
```python
raise ToolError("User-friendly error message")  # Shown to LLM
logger.error(f"Internal details: {technical_info}")  # Logged only
```

### Step 3: Test with Inspector

```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

Your new tool appears automatically!

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_API_URL` | `http://localhost:8000` | Task API base URL |
| `TASK_API_KEY` | `demo-secret-key-change-in-production` | API key (MUST match Task API) |

### Via .env File

```bash
TASK_API_URL=http://localhost:8000
TASK_API_KEY=demo-secret-key-change-in-production

# Production example
# TASK_API_URL=https://your-api.apprunner.com
# TASK_API_KEY=your-production-key
```

---

## 🔗 Integration Examples

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "task-api": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/mcp-pycon-demo",
      "env": {
        "TASK_API_URL": "http://localhost:8000",
        "TASK_API_KEY": "demo-secret-key-change-in-production"
      }
    }
  }
}
```

### Python MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        env={
            "TASK_API_URL": "http://localhost:8000",
            "TASK_API_KEY": "demo-secret-key-change-in-production"
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available: {[t.name for t in tools.tools]}")

            # Call tool
            result = await session.call_tool(
                "register_user",
                arguments={
                    "name": "Test User",
                    "email": "test@example.com",
                    "company": "Test Corp"
                }
            )
            print(f"Result: {result.content[0].text}")

asyncio.run(main())
```

---

## 🧪 Complete Testing Flow

### 1. Start Services

```bash
# Start Task API
docker compose up -d task-api

# Verify ready
curl http://localhost:8000/health
```

### 2. Launch Inspector

```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

Open http://localhost:5173

### 3. Test Tools Sequentially

**Register user:**
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "company": "Test Company"
}
```
→ Save the user ID!

**List users:**
```json
{}
```

**Get specific user:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Schedule call:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Onboarding Call",
  "scheduled_for": "2025-10-25T10:00:00Z",
  "duration_minutes": 30
}
```
→ Save the call ID!

**List calls:**
```json
{}
```

**Create task:**
```json
{
  "title": "Prepare onboarding materials",
  "description": "Create custom deck",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Update call status:**
```json
{
  "call_id": "call-123-456",
  "status": "completed"
}
```

**Update task status:**
```json
{
  "task_id": "task-789-012",
  "status": "done"
}
```

---

## 🐛 Troubleshooting

### Server won't start

```bash
# Check Task API
curl http://localhost:8000/health

# Check environment
echo $TASK_API_URL
echo $TASK_API_KEY
```

### Authentication errors

Verify keys match:
```bash
docker compose exec task-api env | grep TASK_API_KEY
```

### Inspector not connecting

1. Use correct command from project root
2. Verify Python can import: `python -c "import mcp_server.server"`

### Tool returning empty response

```bash
# Check Task API logs
docker compose logs -f task-api

# Test API directly
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","company":"Test Co"}'
```

---

## 📚 Resources

- **FastMCP Documentation:** https://gofastmcp.com
- **MCP Protocol Spec:** https://modelcontextprotocol.io
- **MCP Inspector:** https://github.com/modelcontextprotocol/inspector
- **Project README:** [../README.md](../README.md)
- **Task API README:** [../task_api/README.md](../task_api/README.md)

---

**Built with ❤️ for PyCon - Powered by FastMCP**
