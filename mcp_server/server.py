"""MCP Server implementation using FastMCP.

This server acts as a secure bridge between LLMs and the Task API.
It exposes API functionality as MCP tools while keeping the API key secure.
"""

import logging
import os
from typing import Annotated, Literal

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Server configuration from environment
API_URL = os.getenv("TASK_API_URL", "http://localhost:8000")
API_KEY = os.getenv("TASK_API_KEY", "demo-secret-key-change-in-production")

# Create FastMCP server instance
mcp = FastMCP("task-api-mcp-server")

# HTTP client for API calls (reusable across tool calls)
http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client with API authentication."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            base_url=API_URL,
            headers={"X-API-Key": API_KEY},
            timeout=30.0
        )
    return http_client


# ============================================================================
# USER MANAGEMENT TOOLS
# ============================================================================

@mcp.tool
async def register_user(
    name: Annotated[str, "Full name of the user"],
    email: Annotated[str, "Email address of the user"],
    company: Annotated[str, "Company name"],
    user_type: Annotated[
        Literal["client", "prospect", "partner"],
        "Type of user"
    ] = "client",
    notes: Annotated[str, Field(description="Optional notes about the user")] = "",
) -> str:
    """Register a new user (client, prospect, or partner) in the system.

    Use this when someone asks to add, register, or create a new user or client.
    Returns the created user with ID and timestamps.
    """
    client = get_http_client()

    try:
        payload = {
            "name": name,
            "email": email,
            "company": company,
            "user_type": user_type,
        }
        if notes:
            payload["notes"] = notes

        response = await client.post("/users", json=payload)
        response.raise_for_status()
        result = response.json()

        return (
            f"✅ User registered successfully!\n\n"
            f"ID: {result['id']}\n"
            f"Name: {result['name']}\n"
            f"Email: {result['email']}\n"
            f"Company: {result['company']}\n"
            f"Type: {result['user_type']}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for register_user: {error_detail}")
        raise ToolError(f"Failed to register user: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing register_user: {e}")
        raise ToolError(f"Error registering user: {str(e)}")


@mcp.tool
async def list_users() -> str:
    """List all registered users in the system.

    Use this to see all clients, prospects, or partners.
    """
    client = get_http_client()

    try:
        response = await client.get("/users")
        response.raise_for_status()
        users = response.json()

        if not users:
            return "No users found in the system."

        users_text = f"Found {len(users)} user(s):\n\n"
        for user in users:
            users_text += (
                f"• {user['name']} ({user['company']}) - {user['email']}\n"
                f"  ID: {user['id']}, Type: {user['user_type']}\n"
            )

        return users_text
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for list_users: {error_detail}")
        raise ToolError(f"Failed to list users: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing list_users: {e}")
        raise ToolError(f"Error listing users: {str(e)}")


@mcp.tool
async def get_user(
    user_id: Annotated[str, "The unique ID of the user"]
) -> str:
    """Get details of a specific user by their ID.

    Use this to look up information about a specific user.
    """
    client = get_http_client()

    try:
        response = await client.get(f"/users/{user_id}")
        response.raise_for_status()
        user = response.json()

        return (
            f"User Details:\n\n"
            f"Name: {user['name']}\n"
            f"Email: {user['email']}\n"
            f"Company: {user['company']}\n"
            f"Type: {user['user_type']}\n"
            f"ID: {user['id']}\n"
            f"Created: {user['created_at']}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for get_user: {error_detail}")
        raise ToolError(f"Failed to get user: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing get_user: {e}")
        raise ToolError(f"Error getting user: {str(e)}")


# ============================================================================
# CALL SCHEDULING TOOLS
# ============================================================================

@mcp.tool
async def schedule_call(
    user_id: Annotated[str, "ID of the user to schedule the call with"],
    title: Annotated[str, "Title or purpose of the call"],
    scheduled_for: Annotated[str, "Date and time for the call (ISO 8601 format)"],
    duration_minutes: Annotated[
        int,
        Field(ge=15, le=240, description="Duration of the call in minutes")
    ] = 30,
    notes: Annotated[str, "Optional notes for the call"] = "",
) -> str:
    """Schedule a call with a registered user.

    Use this for onboarding calls, demos, check-ins, or any scheduled conversation.
    Requires a valid user_id from an existing user.
    """
    client = get_http_client()

    try:
        payload = {
            "user_id": user_id,
            "title": title,
            "scheduled_for": scheduled_for,
            "duration_minutes": duration_minutes,
        }
        if notes:
            payload["notes"] = notes

        response = await client.post("/calls", json=payload)
        response.raise_for_status()
        result = response.json()

        return (
            f"✅ Call scheduled successfully!\n\n"
            f"ID: {result['id']}\n"
            f"Title: {result['title']}\n"
            f"Scheduled for: {result['scheduled_for']}\n"
            f"Duration: {result['duration_minutes']} minutes\n"
            f"User ID: {result['user_id']}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for schedule_call: {error_detail}")
        raise ToolError(f"Failed to schedule call: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing schedule_call: {e}")
        raise ToolError(f"Error scheduling call: {str(e)}")


@mcp.tool
async def list_calls(
    user_id: Annotated[str, "Optional: Filter calls by user ID"] = "",
    status: Annotated[
        Literal["scheduled", "completed", "cancelled", "rescheduled", ""],
        "Optional: Filter calls by status"
    ] = "",
) -> str:
    """List scheduled calls, optionally filtered by user or status.

    Use this to see upcoming calls, completed calls, or calls for a specific user.
    """
    client = get_http_client()

    try:
        params = {}
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status_filter"] = status

        response = await client.get("/calls", params=params)
        response.raise_for_status()
        calls = response.json()

        if not calls:
            return "No calls found."

        calls_text = f"Found {len(calls)} call(s):\n\n"
        for call in calls:
            calls_text += (
                f"• {call['title']} - {call['scheduled_for']}\n"
                f"  ID: {call['id']}, Status: {call['status']}, "
                f"Duration: {call['duration_minutes']}min\n"
            )

        return calls_text
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for list_calls: {error_detail}")
        raise ToolError(f"Failed to list calls: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing list_calls: {e}")
        raise ToolError(f"Error listing calls: {str(e)}")


@mcp.tool
async def update_call_status(
    call_id: Annotated[str, "ID of the call to update"],
    status: Annotated[
        Literal["scheduled", "completed", "cancelled", "rescheduled"],
        "New status for the call"
    ],
) -> str:
    """Update the status of a scheduled call.

    Use this to mark calls as completed, cancelled, or rescheduled.
    """
    client = get_http_client()

    try:
        response = await client.patch(
            f"/calls/{call_id}/status",
            params={"new_status": status}
        )
        response.raise_for_status()
        result = response.json()

        return (
            f"✅ Call status updated to '{result['status']}' "
            f"for call: {result['title']}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for update_call_status: {error_detail}")
        raise ToolError(f"Failed to update call status: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing update_call_status: {e}")
        raise ToolError(f"Error updating call status: {str(e)}")


# ============================================================================
# TASK MANAGEMENT TOOLS
# ============================================================================

@mcp.tool
async def create_task(
    title: Annotated[str, "Title of the task"],
    description: Annotated[str, "Optional detailed description of the task"] = "",
    user_id: Annotated[str, "Optional: ID of user this task is related to"] = "",
    due_date: Annotated[str, "Optional: Due date for the task (ISO 8601 format)"] = "",
) -> str:
    """Create a new task.

    Tasks can be general or associated with a specific user.
    Use this for follow-ups, action items, or any work that needs to be tracked.
    """
    client = get_http_client()

    try:
        payload = {"title": title}
        if description:
            payload["description"] = description
        if user_id:
            payload["user_id"] = user_id
        if due_date:
            payload["due_date"] = due_date

        response = await client.post("/tasks", json=payload)
        response.raise_for_status()
        result = response.json()

        task_text = (
            f"✅ Task created successfully!\n\n"
            f"ID: {result['id']}\n"
            f"Title: {result['title']}\n"
            f"Status: {result['status']}\n"
        )
        if result.get('user_id'):
            task_text += f"User ID: {result['user_id']}\n"

        return task_text
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for create_task: {error_detail}")
        raise ToolError(f"Failed to create task: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing create_task: {e}")
        raise ToolError(f"Error creating task: {str(e)}")


@mcp.tool
async def list_tasks(
    user_id: Annotated[str, "Optional: Filter tasks by user ID"] = "",
    status: Annotated[
        Literal["todo", "in_progress", "done", "cancelled", ""],
        "Optional: Filter tasks by status"
    ] = "",
) -> str:
    """List all tasks, optionally filtered by user or status.

    Use this to see pending tasks, completed work, or tasks for a specific user.
    """
    client = get_http_client()

    try:
        params = {}
        if user_id:
            params["user_id"] = user_id
        if status:
            params["status_filter"] = status

        response = await client.get("/tasks", params=params)
        response.raise_for_status()
        tasks = response.json()

        if not tasks:
            return "No tasks found."

        tasks_text = f"Found {len(tasks)} task(s):\n\n"
        for task in tasks:
            tasks_text += f"• {task['title']} - Status: {task['status']}\n"
            tasks_text += f"  ID: {task['id']}\n"
            if task.get('description'):
                tasks_text += f"  Description: {task['description']}\n"

        return tasks_text
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for list_tasks: {error_detail}")
        raise ToolError(f"Failed to list tasks: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing list_tasks: {e}")
        raise ToolError(f"Error listing tasks: {str(e)}")


@mcp.tool
async def update_task_status(
    task_id: Annotated[str, "ID of the task to update"],
    status: Annotated[
        Literal["todo", "in_progress", "done", "cancelled"],
        "New status for the task"
    ],
) -> str:
    """Update the status of a task.

    Use this to mark tasks as in progress, done, or cancelled.
    """
    client = get_http_client()

    try:
        response = await client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": status}
        )
        response.raise_for_status()
        result = response.json()

        return (
            f"✅ Task status updated to '{result['status']}' "
            f"for task: {result['title']}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("message", str(e))
        logger.error(f"API error for update_task_status: {error_detail}")
        raise ToolError(f"Failed to update task status: {error_detail}")
    except Exception as e:
        logger.error(f"Error executing update_task_status: {e}")
        raise ToolError(f"Error updating task status: {str(e)}")


# ============================================================================
# SERVER ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Task API MCP Server (FastMCP)")
    logger.info(f"Connecting to API at: {API_URL}")
    mcp.run()
