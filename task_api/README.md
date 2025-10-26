# 🚀 Task API - FastAPI REST API with S3 Storage

A production-ready REST API for managing users, scheduled calls, and tasks. Built with FastAPI, secured with API key authentication, and backed by AWS S3 storage.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Testing with curl](#-testing-with-curl)
- [Docker Compose Setup](#-docker-compose-setup)
- [API Reference](#-api-reference)
- [Authentication](#-authentication)
- [Data Models](#-data-models)

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Testing)

```bash
# From the task_api directory
cd task_api

# Start all services (API + LocalStack)
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f task-api

# Stop services
docker compose down
```

**The API will be available at:** http://localhost:8000

**Interactive docs:** http://localhost:8000/docs

### Option 2: Local Development

```bash
# From project root
python -m task_api.main
```

---

## 📡 API Endpoints

### Health Check
- `GET /health` - Check API health (no authentication required)

### Users
- `POST /users` - Create a new user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user by ID

### Calls
- `POST /calls` - Schedule a new call
- `GET /calls` - List all calls (filterable)
- `GET /calls/{call_id}` - Get call by ID
- `PATCH /calls/{call_id}/status` - Update call status

### Tasks
- `POST /tasks` - Create a new task
- `GET /tasks` - List all tasks (filterable)
- `GET /tasks/{task_id}` - Get task by ID
- `PATCH /tasks/{task_id}/status` - Update task status

---

## 🧪 Testing with curl

### 1. Health Check

```bash
# No authentication needed
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-24T10:30:00.000000"
}
```

### 2. Create a User

```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María García",
    "email": "maria@test-azollon.com",
    "company": "Test Azollon",
    "user_type": "client",
    "notes": "New client from PyCon demo"
  }'
```

**Expected response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "María García",
  "email": "maria@test-azollon.com",
  "company": "Test Azollon",
  "user_type": "client",
  "notes": "New client from PyCon demo",
  "created_at": "2025-10-24T10:30:00.000000",
  "updated_at": "2025-10-24T10:30:00.000000"
}
```

**💡 Save the `id` from the response - you'll need it for scheduling calls!**

### 3. List All Users

```bash
curl http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Expected response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "María García",
    "email": "maria@test-azollon.com",
    "company": "Test Azollon",
    "user_type": "client",
    "notes": "New client from PyCon demo",
    "created_at": "2025-10-24T10:30:00.000000",
    "updated_at": "2025-10-24T10:30:00.000000"
  }
]
```

### 4. Get Specific User

```bash
# Replace {USER_ID} with actual user ID from step 2
curl http://localhost:8000/users/{USER_ID} \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### 5. Schedule a Call

```bash
# Replace {USER_ID} with the actual user ID
curl -X POST http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{USER_ID}",
    "title": "Onboarding Call - Test Azollon",
    "scheduled_for": "2025-10-25T10:00:00Z",
    "duration_minutes": 45,
    "notes": "Initial onboarding and platform overview"
  }'
```

**Expected response:**
```json
{
  "id": "call-123-456",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Onboarding Call - Test Azollon",
  "scheduled_for": "2025-10-25T10:00:00",
  "duration_minutes": 45,
  "notes": "Initial onboarding and platform overview",
  "status": "scheduled",
  "created_at": "2025-10-24T10:30:00.000000",
  "updated_at": "2025-10-24T10:30:00.000000"
}
```

### 6. List All Calls

```bash
# All calls
curl http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production"

# Filter by user
curl "http://localhost:8000/calls?user_id={USER_ID}" \
  -H "X-API-Key: demo-secret-key-change-in-production"

# Filter by status
curl "http://localhost:8000/calls?status_filter=scheduled" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### 7. Update Call Status

```bash
# Replace {CALL_ID} with actual call ID
curl -X PATCH "http://localhost:8000/calls/{CALL_ID}/status?new_status=completed" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Available statuses:** `scheduled`, `completed`, `cancelled`, `rescheduled`

### 8. Create a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare onboarding materials",
    "description": "Create custom deck with use case examples",
    "user_id": "{USER_ID}",
    "due_date": "2025-10-26T12:00:00Z"
  }'
```

**Expected response:**
```json
{
  "id": "task-789-012",
  "title": "Prepare onboarding materials",
  "description": "Create custom deck with use case examples",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "todo",
  "due_date": "2025-10-26T12:00:00",
  "created_at": "2025-10-24T10:30:00.000000",
  "updated_at": "2025-10-24T10:30:00.000000"
}
```

### 9. List All Tasks

```bash
# All tasks
curl http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production"

# Filter by user
curl "http://localhost:8000/tasks?user_id={USER_ID}" \
  -H "X-API-Key: demo-secret-key-change-in-production"

# Filter by status
curl "http://localhost:8000/tasks?status_filter=todo" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### 10. Update Task Status

```bash
# Replace {TASK_ID} with actual task ID
curl -X PATCH "http://localhost:8000/tasks/{TASK_ID}/status?new_status=in_progress" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Available statuses:** `todo`, `in_progress`, `done`, `cancelled`

---

## 🐳 Docker Compose Setup

### Architecture

```
┌─────────────────────┐      ┌─────────────────────┐
│   Task API          │─────▶│   LocalStack        │
│   (Port 8000)       │      │   (Port 4566)       │
│   FastAPI Service   │      │   S3 Emulator       │
└─────────────────────┘      └─────────────────────┘
```

### Services

#### 1. **localstack**
- **Image:** `localstack/localstack:latest`
- **Ports:**
  - `4566` - LocalStack gateway (AWS services)
  - `4571` - LocalStack dashboard
- **Purpose:** Simulates AWS S3 locally (no AWS account needed!)

#### 2. **task-api**
- **Image:** Built from `Dockerfile`
- **Port:** `8000` - API endpoints
- **Purpose:** FastAPI REST API service

### Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# View API logs only
docker compose logs -f task-api

# View LocalStack logs only
docker compose logs -f localstack

# Check service health
docker compose ps

# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v

# Rebuild and start
docker compose up -d --build
```

### Verification

```bash
# 1. Check LocalStack health
curl http://localhost:4566/_localstack/health

# Expected response:
{
  "services": {
    "s3": "running"
  }
}

# 2. Check Task API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-24T10:30:00.000000"
}
```

### Troubleshooting

#### API not starting?

```bash
# Check logs
docker compose logs task-api

# Common issues:
# - LocalStack not ready: Wait for health check to pass
# - Port 8000 in use: Change port in docker-compose.yml
```

#### LocalStack issues?

```bash
# Check logs
docker compose logs localstack

# Verify S3 service
curl http://localhost:4566/_localstack/health

# List S3 buckets (should show mcp-pycon-demo-bucket)
aws --endpoint-url=http://localhost:4566 s3 ls
```

#### Can't connect to API?

```bash
# From host machine
curl http://localhost:8000/health

# If fails, check:
docker compose ps  # Is task-api running?
docker compose logs task-api  # Any errors?
```

---

## 📖 API Reference

### Authentication

All endpoints (except `/health`) require authentication via the `X-API-Key` header.

```bash
curl http://localhost:8000/endpoint \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Default API Key:** `demo-secret-key-change-in-production`

**Change it:** Set `TASK_API_KEY` environment variable in `docker-compose.yml`

### Error Responses

#### 403 Forbidden (Invalid API Key)

```json
{
  "success": false,
  "message": "Invalid API key"
}
```

#### 404 Not Found

```json
{
  "success": false,
  "message": "User abc-123 not found"
}
```

#### 422 Unprocessable Entity (Validation Error)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 📊 Data Models

### User

```json
{
  "id": "string (UUID)",
  "name": "string (1-100 chars)",
  "email": "string (valid email)",
  "company": "string (1-100 chars)",
  "user_type": "client|prospect|partner",
  "notes": "string (optional, max 500 chars)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### Scheduled Call

```json
{
  "id": "string (UUID)",
  "user_id": "string (UUID, must exist)",
  "title": "string (1-200 chars)",
  "scheduled_for": "datetime (ISO 8601)",
  "duration_minutes": "integer (15-240)",
  "notes": "string (optional, max 500 chars)",
  "status": "scheduled|completed|cancelled|rescheduled",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### Task

```json
{
  "id": "string (UUID)",
  "title": "string (1-200 chars)",
  "description": "string (optional, max 1000 chars)",
  "user_id": "string (optional UUID)",
  "status": "todo|in_progress|done|cancelled",
  "due_date": "datetime (optional, ISO 8601)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

---

## 🧪 Complete Testing Flow

Here's a complete workflow to test all features:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Create a user
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Company"
  }')

# Extract user ID (requires jq)
USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "Created user: $USER_ID"

# 3. Schedule a call for this user
CALL_RESPONSE=$(curl -s -X POST http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"title\": \"Test Call\",
    \"scheduled_for\": \"2025-10-25T10:00:00Z\",
    \"duration_minutes\": 30
  }")

CALL_ID=$(echo $CALL_RESPONSE | jq -r '.id')
echo "Created call: $CALL_ID"

# 4. Create a task
TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Follow up with Test User\",
    \"user_id\": \"$USER_ID\"
  }")

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
echo "Created task: $TASK_ID"

# 5. List everything
echo "\n=== All Users ==="
curl -s http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n=== All Calls ==="
curl -s http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n=== All Tasks ==="
curl -s http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

# 6. Update statuses
curl -s -X PATCH "http://localhost:8000/calls/$CALL_ID/status?new_status=completed" \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

curl -s -X PATCH "http://localhost:8000/tasks/$TASK_ID/status?new_status=done" \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n✅ Complete testing flow executed!"
```

**Save this as `test_api.sh` and run:** `chmod +x test_api.sh && ./test_api.sh`

---

## 🔗 Interactive API Documentation

Once the API is running, visit:

- **Swagger UI:** http://localhost:8000/docs
  - Interactive API explorer
  - Try endpoints directly in browser
  - See request/response schemas

- **ReDoc:** http://localhost:8000/redoc
  - Beautiful API documentation
  - Detailed schema information
  - Export OpenAPI spec

---

## 📂 S3 Storage Structure

Data is stored in S3 (LocalStack) as JSON files:

```
mcp-pycon-demo-bucket/
├── users/
│   ├── 550e8400-e29b-41d4-a716-446655440000.json
│   └── 660f9511-f3ac-52e5-b827-557766551111.json
├── calls/
│   ├── call-123-456.json
│   └── call-789-012.json
└── tasks/
    ├── task-abc-def.json
    └── task-ghi-jkl.json
```

### View S3 contents

```bash
# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List users
aws --endpoint-url=http://localhost:4566 s3 ls s3://mcp-pycon-demo-bucket/users/

# Download a user file
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://mcp-pycon-demo-bucket/users/{USER_ID}.json \
  ./user.json

# View the file
cat user.json | jq
```

---

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_API_KEY` | `demo-secret-key-change-in-production` | API authentication key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_S3_BUCKET` | `mcp-pycon-demo-bucket` | S3 bucket name |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | S3 endpoint (LocalStack) |
| `AWS_ACCESS_KEY_ID` | `test` | AWS access key (LocalStack) |
| `AWS_SECRET_ACCESS_KEY` | `test` | AWS secret key (LocalStack) |

### Modify Configuration

Edit `docker-compose.yml`:

```yaml
task-api:
  environment:
    - TASK_API_KEY=your-custom-key
    - AWS_S3_BUCKET=your-bucket-name
```

Then restart:

```bash
docker compose down
docker compose up -d
```

---

## 🎯 Quick Reference

### Start Everything
```bash
docker compose up -d && docker compose logs -f
```

### Test API is Ready
```bash
curl http://localhost:8000/health
```

### Create Test Data
```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","company":"Test Co"}'
```

### View Logs
```bash
docker compose logs -f task-api
```

### Stop Everything
```bash
docker compose down
```

---

## 📚 Additional Resources

- **Project Root README:** `../README.md` - Complete project documentation
- **S3 Connection Guide:** `../S3_CONNECTION_GUIDE.md` - How S3 storage works
- **Deployment Guide:** `../DEPLOYMENT_GUIDE.md` - Production deployment
- **Demo Script:** `../demo/demo_script.md` - PyCon presentation guide

---

## 🆘 Need Help?

- **API not responding?** Check `docker compose logs task-api`
- **LocalStack issues?** Check `docker compose logs localstack`
- **Invalid API key?** Default is `demo-secret-key-change-in-production`
- **Port conflicts?** Change ports in `docker-compose.yml`

---

**Built with ❤️ for PyCon - Demonstrating MCP + FastAPI + S3**