"""Main FastAPI application for the Task API.

This API demonstrates a real-world service that can be securely accessed
by LLMs through the Model Context Protocol (MCP).
"""

import logging
from datetime import datetime
from typing import List
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .models import (
    User, UserCreate,
    ScheduledCall, ScheduleCallCreate,
    Task, TaskCreate,
    APIResponse, HealthResponse,
    CallStatus, TaskStatus
)
from .storage import get_storage_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize settings and app
settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage client
storage = get_storage_client()


# Security dependency
def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify the API key from request headers.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key != settings.task_api_key:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return x_api_key


# Health check endpoint (no auth required)
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running."""
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.utcnow()
    )


# User endpoints
@app.post("/users", response_model=User, tags=["Users"], status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, api_key: str = Header(..., alias="X-API-Key")):
    """Create a new user in the system.

    This endpoint registers a new user (client, prospect, or partner) in the system.
    The user data is stored in S3 as a JSON file.

    Args:
        user: User creation data
        api_key: API key for authentication

    Returns:
        The created user with generated ID and timestamps
    """
    verify_api_key(api_key)

    # Create user object
    new_user = User(**user.model_dump())

    # Save to storage
    storage.save("users", new_user.id, new_user)

    logger.info(f"Created user: {new_user.id} - {new_user.name} ({new_user.company})")

    return new_user


@app.get("/users", response_model=List[User], tags=["Users"])
async def list_users(api_key: str = Header(..., alias="X-API-Key")):
    """List all users in the system.

    Returns:
        List of all registered users
    """
    verify_api_key(api_key)

    users_data = storage.list_all("users")
    users = [User(**user_data) for user_data in users_data]

    logger.info(f"Retrieved {len(users)} users")
    return users


@app.get("/users/{user_id}", response_model=User, tags=["Users"])
async def get_user(user_id: str, api_key: str = Header(..., alias="X-API-Key")):
    """Get a specific user by ID.

    Args:
        user_id: User ID to retrieve

    Returns:
        The requested user

    Raises:
        HTTPException: If user not found
    """
    verify_api_key(api_key)

    user_data = storage.get("users", user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    return User(**user_data)


# Scheduled Calls endpoints
@app.post("/calls", response_model=ScheduledCall, tags=["Calls"], status_code=status.HTTP_201_CREATED)
async def schedule_call(call: ScheduleCallCreate, api_key: str = Header(..., alias="X-API-Key")):
    """Schedule a call with a user.

    This endpoint creates a scheduled call with a registered user.
    Useful for onboarding calls, check-ins, demos, etc.

    Args:
        call: Call scheduling data
        api_key: API key for authentication

    Returns:
        The scheduled call with generated ID and timestamps
    """
    verify_api_key(api_key)

    # Verify user exists
    user_data = storage.get("users", call.user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {call.user_id} not found"
        )

    # Create scheduled call
    new_call = ScheduledCall(**call.model_dump())

    # Save to storage
    storage.save("calls", new_call.id, new_call)

    logger.info(f"Scheduled call: {new_call.id} - {new_call.title} for user {call.user_id}")

    return new_call


@app.get("/calls", response_model=List[ScheduledCall], tags=["Calls"])
async def list_calls(
    user_id: str | None = None,
    status_filter: CallStatus | None = None,
    api_key: str = Header(..., alias="X-API-Key")
):
    """List all scheduled calls, optionally filtered by user or status.

    Args:
        user_id: Optional user ID to filter calls
        status_filter: Optional status to filter calls

    Returns:
        List of scheduled calls
    """
    verify_api_key(api_key)

    calls_data = storage.list_all("calls")
    calls = [ScheduledCall(**call_data) for call_data in calls_data]

    # Apply filters
    if user_id:
        calls = [call for call in calls if call.user_id == user_id]
    if status_filter:
        calls = [call for call in calls if call.status == status_filter]

    logger.info(f"Retrieved {len(calls)} calls")
    return calls


@app.get("/calls/{call_id}", response_model=ScheduledCall, tags=["Calls"])
async def get_call(call_id: str, api_key: str = Header(..., alias="X-API-Key")):
    """Get a specific scheduled call by ID.

    Args:
        call_id: Call ID to retrieve

    Returns:
        The requested call

    Raises:
        HTTPException: If call not found
    """
    verify_api_key(api_key)

    call_data = storage.get("calls", call_id)
    if not call_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )

    return ScheduledCall(**call_data)


@app.patch("/calls/{call_id}/status", response_model=ScheduledCall, tags=["Calls"])
async def update_call_status(
    call_id: str,
    new_status: CallStatus,
    api_key: str = Header(..., alias="X-API-Key")
):
    """Update the status of a scheduled call.

    Args:
        call_id: Call ID to update
        new_status: New status for the call

    Returns:
        The updated call

    Raises:
        HTTPException: If call not found
    """
    verify_api_key(api_key)

    call_data = storage.get("calls", call_id)
    if not call_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call {call_id} not found"
        )

    # Update status
    call = ScheduledCall(**call_data)
    call.status = new_status

    # Save updated call
    storage.update("calls", call_id, call)

    logger.info(f"Updated call {call_id} status to {new_status}")

    return call


# Task endpoints
@app.post("/tasks", response_model=Task, tags=["Tasks"], status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, api_key: str = Header(..., alias="X-API-Key")):
    """Create a new task.

    Tasks can be general or associated with a specific user.

    Args:
        task: Task creation data
        api_key: API key for authentication

    Returns:
        The created task with generated ID and timestamps
    """
    verify_api_key(api_key)

    # If user_id provided, verify user exists
    if task.user_id:
        user_data = storage.get("users", task.user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {task.user_id} not found"
            )

    # Create task
    new_task = Task(**task.model_dump())

    # Save to storage
    storage.save("tasks", new_task.id, new_task)

    logger.info(f"Created task: {new_task.id} - {new_task.title}")

    return new_task


@app.get("/tasks", response_model=List[Task], tags=["Tasks"])
async def list_tasks(
    user_id: str | None = None,
    status_filter: TaskStatus | None = None,
    api_key: str = Header(..., alias="X-API-Key")
):
    """List all tasks, optionally filtered by user or status.

    Args:
        user_id: Optional user ID to filter tasks
        status_filter: Optional status to filter tasks

    Returns:
        List of tasks
    """
    verify_api_key(api_key)

    tasks_data = storage.list_all("tasks")
    tasks = [Task(**task_data) for task_data in tasks_data]

    # Apply filters
    if user_id:
        tasks = [task for task in tasks if task.user_id == user_id]
    if status_filter:
        tasks = [task for task in tasks if task.status == status_filter]

    logger.info(f"Retrieved {len(tasks)} tasks")
    return tasks


@app.get("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
async def get_task(task_id: str, api_key: str = Header(..., alias="X-API-Key")):
    """Get a specific task by ID.

    Args:
        task_id: Task ID to retrieve

    Returns:
        The requested task

    Raises:
        HTTPException: If task not found
    """
    verify_api_key(api_key)

    task_data = storage.get("tasks", task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    return Task(**task_data)


@app.patch("/tasks/{task_id}/status", response_model=Task, tags=["Tasks"])
async def update_task_status(
    task_id: str,
    new_status: TaskStatus,
    api_key: str = Header(..., alias="X-API-Key")
):
    """Update the status of a task.

    Args:
        task_id: Task ID to update
        new_status: New status for the task

    Returns:
        The updated task

    Raises:
        HTTPException: If task not found
    """
    verify_api_key(api_key)

    task_data = storage.get("tasks", task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Update status
    task = Task(**task_data)
    task.status = new_status

    # Save updated task
    storage.update("tasks", task_id, task)

    logger.info(f"Updated task {task_id} status to {new_status}")

    return task


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "task_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
