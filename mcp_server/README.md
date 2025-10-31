# 🔌 MCP Server - FastMCP Bridge to Task API

A secure Model Context Protocol (MCP) server built with FastMCP that exposes the Task API as LLM-callable tools. This server acts as a secure bridge, keeping API credentials isolated from LLMs while enabling natural language interactions.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Testing with MCP Inspector](#-testing-with-mcp-inspector)
- [Available Tools](#-available-tools)
- [Architecture](#-architecture)
- [Adding New Tools](#-adding-new-tools)
- [Configuration](#-configuration)
- [Integration Examples](#-integration-examples)

---

## 🚀 Quick Start

### Prerequisites

1. **Task API running** - The MCP server connects to the Task API
   ```bash
   # In a separate terminal, start Task API
   cd task_api
   docker compose up -d
   ```

2. **Environment variables configured**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env and set:
   # TASK_API_URL=http://localhost:8000
   # TASK_API_KEY=demo-secret-key-change-in-production
   ```

### Option 1: Direct Execution

```bash
# From project root
python -m mcp_server.server
```

The server will start in stdio mode, ready to accept MCP client connections.

### Option 2: With MCP Inspector (Recommended for Testing)

```bash
# Launch inspector with integrated MCP server
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

**The Inspector UI will be available at:** http://localhost:5173

---

## 🔍 Testing with MCP Inspector

The MCP Inspector provides an interactive web interface to test your MCP tools without building a full client.

### Launch Inspector

```bash
# Make sure Task API is running first!
# cd task_api && docker compose up -d

# Then launch inspector
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

### Using the Inspector

1. **Open http://localhost:5173** in your browser

2. **View Available Tools**
   - All 9 tools are automatically discovered
   - Each tool shows its description and parameter schema

3. **Test a Tool: Register User**
   ```json
   {
     "name": "María García",
     "email": "maria@example.com",
     "company": "Test Corp",
     "user_type": "client",
     "notes": "Testing from MCP Inspector"
   }
   ```

   Click "Call Tool" and see the response:
   ```
   ✅ User registered successfully!

   ID: 550e8400-e29b-41d4-a716-446655440000
   Name: María García
   Email: maria@example.com
   Company: Test Corp
   Type: client
   ```

4. **Inspect Requests/Responses**
   - View the raw JSON-RPC request
   - See the tool's response payload
   - Debug parameter validation errors

### Complete Testing Flow

```bash
# 1. Register a user
Tool: register_user
{
  "name": "Test User",
  "email": "test@example.com",
  "company": "Test Company"
}
# Save the user ID from response!

# 2. List all users
Tool: list_users
{}

# 3. Get specific user
Tool: get_user
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}

# 4. Schedule a call
Tool: schedule_call
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Onboarding Call",
  "scheduled_for": "2025-10-25T10:00:00Z",
  "duration_minutes": 30
}
# Save the call ID from response!

# 5. List calls
Tool: list_calls
{}

# 6. Create a task
Tool: create_task
{
  "title": "Prepare onboarding materials",
  "description": "Create custom deck",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}

# 7. Update call status
Tool: update_call_status
{
  "call_id": "call-123-456",
  "status": "completed"
}

# 8. List tasks
Tool: list_tasks
{}

# 9. Update task status
Tool: update_task_status
{
  "task_id": "task-789-012",
  "status": "done"
}
```

---

## 🛠️ Available Tools

The MCP server exposes 9 tools that mirror the Task API functionality:

### User Management

#### `register_user`
Register a new user (client, prospect, or partner) in the system.

**Parameters:**
- `name` (string, required) - Full name of the user
- `email` (string, required) - Email address
- `company` (string, required) - Company name
- `user_type` (enum, optional) - Type: `client`, `prospect`, or `partner` (default: `client`)
- `notes` (string, optional) - Additional notes about the user

**Example:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "company": "Acme Corp",
  "user_type": "client"
}
```

#### `list_users`
List all registered users in the system.

**Parameters:** None

#### `get_user`
Get details of a specific user by their ID.

**Parameters:**
- `user_id` (string, required) - The unique ID of the user

### Call Scheduling

#### `schedule_call`
Schedule a call with a registered user.

**Parameters:**
- `user_id` (string, required) - ID of the user
- `title` (string, required) - Title or purpose of the call
- `scheduled_for` (string, required) - Date and time (ISO 8601 format)
- `duration_minutes` (integer, optional) - Duration (15-240 minutes, default: 30)
- `notes` (string, optional) - Optional notes for the call

**Example:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Product Demo",
  "scheduled_for": "2025-10-25T14:00:00Z",
  "duration_minutes": 45
}
```

#### `list_calls`
List scheduled calls, optionally filtered by user or status.

**Parameters:**
- `user_id` (string, optional) - Filter by user ID
- `status` (enum, optional) - Filter by status: `scheduled`, `completed`, `cancelled`, or `rescheduled`

#### `update_call_status`
Update the status of a scheduled call.

**Parameters:**
- `call_id` (string, required) - ID of the call to update
- `status` (enum, required) - New status: `scheduled`, `completed`, `cancelled`, or `rescheduled`

### Task Management

#### `create_task`
Create a new task (general or user-associated).

**Parameters:**
- `title` (string, required) - Title of the task
- `description` (string, optional) - Detailed description
- `user_id` (string, optional) - Associated user ID
- `due_date` (string, optional) - Due date (ISO 8601 format)

**Example:**
```json
{
  "title": "Prepare Q1 report",
  "description": "Compile metrics and create presentation",
  "due_date": "2025-10-30T17:00:00Z"
}
```

#### `list_tasks`
List all tasks, optionally filtered by user or status.

**Parameters:**
- `user_id` (string, optional) - Filter by user ID
- `status` (enum, optional) - Filter by status: `todo`, `in_progress`, `done`, or `cancelled`

#### `update_task_status`
Update the status of a task.

**Parameters:**
- `task_id` (string, required) - ID of the task to update
- `status` (enum, required) - New status: `todo`, `in_progress`, `done`, or `cancelled`

---

## 🏗️ Architecture

### Security Model

```
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐
│             │         │   MCP Server    │         │             │
│  LLM/User   │────────▶│                 │────────▶│  Task API   │
│             │  MCP    │  • Has API Key  │  HTTP   │             │
│             │ Protocol│  • Validates    │  + Key  │  • Validates│
└─────────────┘         │  • Translates   │         │  • Executes │
                        └─────────────────┘         └─────────────┘
                                                            │
                                                            ▼
                                                     ┌─────────────┐
                                                     │ S3 Storage  │
                                                     └─────────────┘
```

**Critical Security Principle:** The API key lives ONLY in the MCP Server's environment variables and is NEVER exposed to the LLM or client.

### Request Flow

1. **LLM sends tool call** via MCP protocol
2. **MCP Server receives** and validates parameters (FastMCP)
3. **Server injects API key** into HTTP headers
4. **Makes authenticated request** to Task API
5. **Receives response** from API
6. **Formats for LLM** and returns via MCP

### Why FastMCP?

This server uses **FastMCP**, a modern framework that dramatically simplifies MCP server development:

**Traditional MCP SDK:**
```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="...", inputSchema={...})]  # Manual JSON schema

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "register_user":  # Manual routing
        # logic
        return [TextContent(type="text", text="...")]  # Manual wrapping
```

**FastMCP:**
```python
@mcp.tool
async def register_user(
    name: Annotated[str, "Full name of the user"],
    email: Annotated[str, "Email address"],
) -> str:
    """Register a new user."""
    # logic
    return "✅ User registered!"  # Auto-wrapped!
```

**Benefits:**
- ✅ 60% less boilerplate code
- ✅ Automatic schema generation from type hints
- ✅ Built-in parameter validation (Pydantic)
- ✅ Type-safe with Python 3.11+ features
- ✅ Cleaner error handling with `ToolError`
- ✅ Modern patterns: `Annotated`, `Literal`, `Field`

---

## ➕ Adding New Tools

### Step 1: Add API Endpoint

First, add the endpoint to the Task API ([task_api/main.py](../task_api/main.py)):

```python
@app.post("/your-endpoint")
async def your_endpoint(
    data: YourModel,
    api_key: str = Header(..., alias="X-API-Key")
):
    verify_api_key(api_key)
    # endpoint logic
    return {"result": "success"}
```

### Step 2: Add MCP Tool

Add a tool function in [mcp_server/server.py](server.py) using the `@mcp.tool` decorator:

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

    Provide a detailed description for the LLM to understand
    when and how to use this tool. This docstring becomes
    the tool's description in the MCP protocol.
    """
    client = get_http_client()

    try:
        payload = {"param1": param1, "count": count, "status": status}
        response = await client.post("/your-endpoint", json=payload)
        response.raise_for_status()
        result = response.json()

        return f"✅ Action completed!\n\nDetails:\n{result}"
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for your_new_tool: {error_detail}")
        raise ToolError(f"Failed to perform action: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing your_new_tool: {e}")
        raise ToolError(f"Error: {str(e)}")
```

### FastMCP Patterns

**Type Annotations:**
```python
# Simple description
param: Annotated[str, "Description"]

# With validation constraints
count: Annotated[int, Field(ge=1, le=100, description="Count between 1-100")]

# Enum-like choices
status: Annotated[Literal["active", "inactive", "pending"], "Status"]

# Optional with default
notes: Annotated[str, "Optional notes"] = ""
```

**Return Values:**
- Return `str` directly - FastMCP auto-converts to `TextContent`
- Use emojis (✅, ❌) to help LLMs understand success/failure
- Format clearly with newlines for readability

**Error Handling:**
```python
# User-facing errors
raise ToolError("User-friendly error message")

# Logged but not shown to LLM
logger.error(f"Internal details: {technical_info}")
```

### Step 3: Test with Inspector

```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

Your new tool will appear automatically in the inspector!

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_API_URL` | `http://localhost:8000` | Task API base URL |
| `TASK_API_KEY` | `demo-secret-key-change-in-production` | API authentication key (MUST match Task API) |

### Configure via .env

Create or edit `.env` in the project root:

```bash
# MCP Server Configuration
TASK_API_URL=http://localhost:8000
TASK_API_KEY=demo-secret-key-change-in-production

# For production (AWS App Runner Task API)
# TASK_API_URL=https://your-api.apprunner.com
# TASK_API_KEY=your-production-key
```

### Configure via Environment

```bash
# Linux/macOS
export TASK_API_URL=http://localhost:8000
export TASK_API_KEY=demo-secret-key-change-in-production

# Windows (PowerShell)
$env:TASK_API_URL="http://localhost:8000"
$env:TASK_API_KEY="demo-secret-key-change-in-production"

# Then run
python -m mcp_server.server
```

---

## 🔗 Integration Examples

### Claude Desktop

Add to Claude Desktop config (`claude_desktop_config.json`):

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

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool
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

### Using with LLM (Azure AI Inference)

```python
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage

# Initialize with MCP tools
client = ChatCompletionsClient(endpoint="...", credential="...")

response = client.complete(
    messages=[
        SystemMessage("You are a helpful assistant with access to a task management API."),
        UserMessage("Register a new user named María García from Test Corp with email maria@test.com")
    ],
    tools=mcp_tools,  # Tools from MCP server
    tool_choice="auto"
)

# LLM decides to call register_user tool
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"LLM wants to call: {tool_call.function.name}")
        print(f"With arguments: {tool_call.function.arguments}")
```

---

## 🧪 Testing Workflow

### 1. Start Task API
```bash
cd task_api
docker compose up -d
```

### 2. Verify API is Ready
```bash
curl http://localhost:8000/health
```

### 3. Launch MCP Inspector
```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

### 4. Open Browser
Go to http://localhost:5173 and test tools interactively!

### 5. View Logs
```bash
# In terminal where you ran inspector
# You'll see MCP server logs in real-time
```

---

## 📊 Tool Response Format

All tools return formatted text responses optimized for LLM consumption:

### Success Response
```
✅ Action completed successfully!

Details:
Field1: value1
Field2: value2
```

### Error Response
```
❌ Error: User not found

The user ID you provided does not exist in the system.
```

### List Response
```
Found 3 user(s):

• María García (Test Corp) - maria@test.com
  ID: 550e8400-e29b-41d4-a716-446655440000, Type: client

• John Doe (Acme Corp) - john@acme.com
  ID: 660f9511-f3ac-52e5-b827-557766551111, Type: prospect

• Jane Smith (Partner Co) - jane@partner.com
  ID: 770fa622-g4bd-63f6-c938-668877662222, Type: partner
```

---

## 🐛 Troubleshooting

### Server won't start

**Check Task API is running:**
```bash
curl http://localhost:8000/health
```

**Check environment variables:**
```bash
echo $TASK_API_URL
echo $TASK_API_KEY
```

**Check logs:**
```bash
# The server logs to stdout/stderr
python -m mcp_server.server
```

### Tools failing with authentication error

**Error:** `❌ Error: Invalid API key`

**Solution:** Verify `TASK_API_KEY` matches the key configured in Task API:
```bash
# Check Task API environment
docker compose -f task_api/docker-compose.yml exec task-api env | grep TASK_API_KEY

# Should match your MCP server's TASK_API_KEY
```

### Inspector not connecting

**Error:** Inspector shows "Connection failed"

**Solutions:**
1. Make sure you're using the correct command:
   ```bash
   npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
   ```

2. Verify the path is correct (run from project root)

3. Check Python can import the module:
   ```bash
   python -c "import mcp_server.server"
   ```

### Tool returning empty response

**Check Task API logs:**
```bash
docker compose -f task_api/docker-compose.yml logs -f task-api
```

**Verify the API endpoint works directly:**
```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","company":"Test Co"}'
```

---

## 🎯 Quick Reference

### Start MCP Server (stdio mode)
```bash
python -m mcp_server.server
```

### Start with Inspector
```bash
npx @modelcontextprotocol/inspector fastmcp run mcp_server/server.py:mcp
```

### Test Connection
```bash
curl http://localhost:8000/health  # Task API must be running
```

### View Tool Schemas
```bash
# In Inspector: http://localhost:5173
# Or programmatically via MCP client
```

---

## 📚 Additional Resources

- **Project Root README:** [../README.md](../README.md) - Complete project documentation
- **FastMCP Documentation:** https://gofastmcp.com - Framework reference
- **MCP Protocol Spec:** https://modelcontextprotocol.io - Protocol details
- **MCP Inspector:** https://github.com/modelcontextprotocol/inspector - Testing tool
- **Task API README:** [../task_api/README.md](../task_api/README.md) - API documentation

---

## 🆘 Need Help?

- **Server not connecting to API?** Check `TASK_API_URL` and ensure Task API is running
- **Authentication errors?** Verify `TASK_API_KEY` matches Task API configuration
- **Inspector not working?** Make sure you're running from project root with correct path
- **Tools not appearing?** Check server logs for Python import errors

---

**Built with ❤️ for PyCon - Powered by FastMCP**
