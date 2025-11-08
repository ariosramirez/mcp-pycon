# 🎯 MCP PyCon Challenge: Extend the Demo!

Welcome! In this challenge, you'll extend the MCP demo by adding two powerful new features:
1. **📊 Client Summary Tool** - Analyze client engagement and activity
2. **📝 User Info Prompt** - Generate formatted user presentations

**Time estimate:** 10-15 minutes
**Difficulty:** Intermediate

## 🎓 What You'll Learn

- How to create **Tools** that aggregate data from multiple API endpoints
- How to implement **Prompts** that provide context to LLMs
- How to test MCP features with the Inspector
- Best practices for FastMCP implementation

---

## ✅ Prerequisites

Before starting, make sure you have:

### 1. Services Running

```bash
# Check all services are up
docker compose ps

# Should show:
# ✓ mcp-demo-localstack (healthy)
# ✓ mcp-demo-task-api (healthy)
# ✓ mcp-demo-mcp-server (running)
# ✓ mcp-demo-streamlit (running)
```

### 2. API has Data

```bash
# Test API is responding
curl http://localhost:8000/health

# Create a test user (save the ID!)
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Corp"
  }'
```

💡 **Tip:** Save the user ID from the response - you'll need it for testing!

---

## 🛠️ Challenge 1: Client Summary Tool

### What We're Building

A tool that provides a comprehensive overview of a client's activity by aggregating:
- User profile information
- All scheduled/completed calls
- All tasks and their status
- An activity score (0-10)

### Step 1: Add the Helper Function

**File:** `mcp_server/server.py`
**Location:** After the last `@mcp.tool` definition (around line 438)

```python
def _calculate_activity_score(total_calls: int, completed_calls: int, done_tasks: int) -> int:
    """Calculate a simple activity score (0-10) based on engagement metrics.

    Scoring:
    - Total calls: up to 5 points
    - Completed calls: up to 3 points
    - Completed tasks: up to 2 points
    """
    score = 0

    # Calls contribute up to 5 points
    score += min(total_calls, 5)

    # Completed calls contribute up to 3 points
    score += min(completed_calls, 3)

    # Completed tasks contribute up to 2 points
    score += min(done_tasks, 2)

    return min(score, 10)
```

### Step 2: Add the Tool

**File:** `mcp_server/server.py`
**Location:** Right after the helper function you just added

```python
@mcp.tool
async def get_client_summary(
    user_id: Annotated[str, "ID of the user/client to analyze"]
) -> str:
    """Get a comprehensive summary of a client's activity and engagement.

    This tool aggregates data from multiple sources (user profile, calls, tasks)
    to provide a complete overview of the client relationship.

    Use this when you need to:
    - Review a client's status before a meeting
    - Prepare a report on client engagement
    - Understand the full picture of client interactions
    """
    client = get_http_client()

    try:
        # Get user data
        user_response = await client.get(f"/users/{user_id}")
        user_response.raise_for_status()
        user = user_response.json()

        # Get all calls for this user
        calls_response = await client.get(f"/calls", params={"user_id": user_id})
        calls_response.raise_for_status()
        calls = calls_response.json()

        # Get all tasks for this user
        tasks_response = await client.get(f"/tasks", params={"user_id": user_id})
        tasks_response.raise_for_status()
        tasks = tasks_response.json()

        # Analyze call status
        scheduled_calls = sum(1 for c in calls if c['status'] == 'scheduled')
        completed_calls = sum(1 for c in calls if c['status'] == 'completed')
        cancelled_calls = sum(1 for c in calls if c['status'] == 'cancelled')

        # Analyze task status
        todo_tasks = sum(1 for t in tasks if t['status'] == 'todo')
        in_progress_tasks = sum(1 for t in tasks if t['status'] == 'in_progress')
        done_tasks = sum(1 for t in tasks if t['status'] == 'done')

        # Calculate activity score
        activity_score = _calculate_activity_score(len(calls), completed_calls, done_tasks)

        # Determine status
        if scheduled_calls > 0:
            status = "🟢 Active"
        elif completed_calls > 0:
            status = "🟡 Follow-up needed"
        else:
            status = "🔴 Inactive"

        # Build summary
        summary = f"""📊 **Client Summary: {user['name']}**

**Profile:**
- Company: {user['company']}
- Email: {user['email']}
- Type: {user['user_type']}
- Joined: {user['created_at']}

**Engagement:**
- Total Calls: {len(calls)}
  • Scheduled: {scheduled_calls}
  • Completed: {completed_calls}
  • Cancelled: {cancelled_calls}

- Total Tasks: {len(tasks)}
  • To Do: {todo_tasks}
  • In Progress: {in_progress_tasks}
  • Done: {done_tasks}

**Activity Score:** {activity_score}/10

**Status:** {status}
"""

        if user.get('notes'):
            summary += f"\n**Notes:** {user['notes']}"

        return summary

    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for get_client_summary: {error_detail}")
        raise ToolError(f"Failed to get client summary: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing get_client_summary: {e}")
        raise ToolError(f"Error getting client summary: {str(e)}")
```

### Step 3: Restart the MCP Server

```bash
# If using Docker
docker compose restart mcp-server

# If running locally
# Stop the server (Ctrl+C) and restart:
python -m mcp_server.server
```

### Step 4: Test with MCP Inspector

```bash
# Launch the inspector
npx @modelcontextprotocol/inspector uv run fastmcp run mcp_server/server.py:mcp
```

1. Open http://localhost:5173
2. Find `get_client_summary` in the tools list
3. Enter your test user ID
4. Click "Call Tool"
5. You should see a formatted summary! 🎉

---

## 📝 Challenge 2: User Info Prompt

### What We're Building

A prompt template that helps LLMs present user information in a professional, formatted way. This demonstrates the **Prompts** primitive of MCP.

### Step 1: Add Required Imports

**File:** `mcp_server/server.py`
**Location:** At the top with other imports (around line 14)

Check if these are already imported, if not, add them:

```python
from mcp.types import PromptMessage, TextContent
```

### Step 2: Add the Prompt

**File:** `mcp_server/server.py`
**Location:** After the `get_client_summary` tool

```python
@mcp.prompt()
async def show_user_info(
    user_id: Annotated[str, "ID of the user to show information for"]
) -> list[PromptMessage]:
    """Generate a prompt template for displaying formatted user information.

    This prompt helps the LLM present user data in a clear, professional format
    suitable for reports, dashboards, or client-facing communications.

    The LLM will receive the user's data pre-loaded and can format it in
    multiple ways: executive summary, profile card, meeting prep sheet, etc.
    """
    client = get_http_client()

    try:
        # Get user data
        response = await client.get(f"/users/{user_id}")
        response.raise_for_status()
        user = response.json()

        # Create prompt message with embedded data
        prompt_text = f"""You have access to information about a client. Present it in a professional, easy-to-read format.

**Client Details:**
- Name: {user['name']}
- Email: {user['email']}
- Company: {user['company']}
- Type: {user['user_type']}
- Member since: {user['created_at']}
{f"- Notes: {user['notes']}" if user.get('notes') else ""}

Please format this information in a way that would be suitable for:
1. An executive summary
2. A client profile card
3. A meeting preparation sheet

Be concise and highlight the most important details."""

        return [
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=prompt_text)
            )
        ]

    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for show_user_info: {error_detail}")
        raise ToolError(f"Failed to get user info: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing show_user_info: {e}")
        raise ToolError(f"Error getting user info: {str(e)}")
```

### Step 3: Restart MCP Server Again

```bash
docker compose restart mcp-server
```

### Step 4: Test with MCP Inspector

1. Open http://localhost:5173
2. Go to the **Prompts** tab
3. Find `show_user_info`
4. Enter your test user ID
5. Click "Get Prompt"
6. You should see the formatted prompt! 📄

---

## 🧪 Testing Your Implementation

### Test 1: Client Summary via Streamlit

1. Open http://localhost:8501
2. Navigate to any scenario
3. Try: **"Dame un resumen del cliente con ID [your-user-id]"**
4. The LLM should call `get_client_summary` and show the results!

### Test 2: User Info Prompt

Try in Streamlit:
- **"Usa el prompt show_user_info para el cliente [your-user-id]"**
- The LLM should use the prompt to format the information

### Test 3: Combined Usage

Try this advanced request:
```
"Analiza al cliente [user-id] y luego crea un reporte ejecutivo profesional"
```

The LLM should:
1. Call `get_client_summary` to get the data
2. Use the insights to create a professional report

---

## 🎁 Bonus: Advanced Examples

### Example 1: Bulk Analysis

```python
# Add this tool for extra credit!
@mcp.tool
async def analyze_top_clients(
    limit: Annotated[int, Field(ge=1, le=10)] = 5
) -> str:
    """Analyze the top N most active clients."""
    # Get all users
    # Call get_client_summary for each
    # Rank by activity score
    # Return top N
```

### Example 2: Custom Prompt Variations

Create additional prompts:
- `meeting_prep_prompt` - Pre-meeting briefing
- `executive_report_prompt` - C-level summary
- `onboarding_checklist_prompt` - New client setup

---

## 🔧 Troubleshooting

### Error: "Import error for PromptMessage"

**Solution:** Add the import at the top of `mcp_server/server.py`:
```python
from mcp.types import PromptMessage, TextContent
```

### Error: "Tool not found in Inspector"

**Solution:**
1. Make sure you saved the file
2. Restart the MCP server: `docker compose restart mcp-server`
3. Refresh the Inspector page

### Error: "User not found"

**Solution:**
1. Create a test user first (see Prerequisites)
2. Make sure you're using the correct user ID
3. Check the API is responding: `curl http://localhost:8000/users`

### Error: "Connection refused"

**Solution:**
```bash
# Check services are running
docker compose ps

# Restart if needed
docker compose up -d
```

---

## 🎓 What You Learned

Congratulations! You've successfully:

✅ Created a **Tool** that aggregates data from multiple sources
✅ Implemented an activity scoring algorithm
✅ Built a **Prompt** template with embedded context
✅ Tested both features with the MCP Inspector
✅ Understood the difference between Tools and Prompts

### Key Takeaways

1. **Tools** are for **actions** - they fetch, process, and analyze data
2. **Prompts** are for **context** - they provide pre-formatted instructions to LLMs
3. **FastMCP** makes both incredibly easy to implement
4. The **MCP Inspector** is invaluable for testing

---

## 🚀 Next Steps

Want to keep learning? Try these:

1. **Add a Resource**: Create `user://[id]` resources for user profiles
2. **Add filtering**: Extend `get_client_summary` with date ranges
3. **Add charts**: Generate ASCII charts for activity over time
4. **Build a dashboard**: Create a tool that summarizes ALL clients
5. **Export functionality**: Add a tool to export summaries as PDF/CSV

### Learn More

- **MCP Documentation**: https://modelcontextprotocol.io
- **FastMCP Guide**: https://gofastmcp.com
- **Project README**: [README.md](README.md)

---

## 🙋 Need Help?

- Check the [troubleshooting section](#-troubleshooting)
- Review the [main README](README.md)
- Look at existing tools in `mcp_server/server.py` for patterns

---

**¡Felicidades! You've completed the MCP Challenge! 🎉**

Share what you built with #MCPyConChallenge
