# 🚀 Task API - FastAPI REST API with S3 Storage

A production-ready REST API for managing users, scheduled calls, and tasks. Built with FastAPI, secured with API key authentication, and backed by AWS S3 storage.

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
# Start all services (API + LocalStack)
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f task-api
```

**API available at:** http://localhost:8000
**Interactive docs:** http://localhost:8000/docs

### Local Development

```bash
python -m task_api.main
```

---

## 📡 API Endpoints

### Health Check
- `GET /health` - No authentication required

### Users
- `POST /users` - Create user
- `GET /users` - List all users
- `GET /users/{user_id}` - Get user by ID

### Calls
- `POST /calls` - Schedule call
- `GET /calls` - List calls (filterable by user_id, status_filter)
- `GET /calls/{call_id}` - Get call by ID
- `PATCH /calls/{call_id}/status` - Update status

### Tasks
- `POST /tasks` - Create task
- `GET /tasks` - List tasks (filterable by user_id, status_filter)
- `GET /tasks/{task_id}` - Get task by ID
- `PATCH /tasks/{task_id}/status` - Update status

---

## 🧪 Testing with curl

### Health Check

```bash
curl http://localhost:8000/health
```

### Create User

```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María García",
    "email": "maria@test-azollon.com",
    "company": "Test Azollon",
    "user_type": "client"
  }'
```

💡 **Save the `id` from response - you'll need it for calls and tasks!**

### List Users

```bash
curl http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### Schedule Call

```bash
curl -X POST http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{USER_ID}",
    "title": "Onboarding Call",
    "scheduled_for": "2025-10-25T10:00:00Z",
    "duration_minutes": 45
  }'
```

### Filter Calls

```bash
# By user
curl "http://localhost:8000/calls?user_id={USER_ID}" \
  -H "X-API-Key: demo-secret-key-change-in-production"

# By status
curl "http://localhost:8000/calls?status_filter=scheduled" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

### Update Call Status

```bash
curl -X PATCH "http://localhost:8000/calls/{CALL_ID}/status?new_status=completed" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Available statuses:** `scheduled`, `completed`, `cancelled`, `rescheduled`

### Create Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare onboarding materials",
    "description": "Create custom deck",
    "user_id": "{USER_ID}",
    "due_date": "2025-10-26T12:00:00Z"
  }'
```

### Update Task Status

```bash
curl -X PATCH "http://localhost:8000/tasks/{TASK_ID}/status?new_status=in_progress" \
  -H "X-API-Key: demo-secret-key-change-in-production"
```

**Available statuses:** `todo`, `in_progress`, `done`, `cancelled`

---

## 🐳 Docker Compose Architecture

```
┌─────────────────────┐      ┌─────────────────────┐
│   Task API          │─────▶│   LocalStack        │
│   (Port 8000)       │      │   (Port 4566)       │
│   FastAPI Service   │      │   S3 Emulator       │
└─────────────────────┘      └─────────────────────┘
```

### Services

**localstack**
- Simulates AWS S3 locally (no AWS account needed)
- Ports: 4566 (gateway), 4571 (dashboard)

**task-api**
- FastAPI REST API service
- Port: 8000

### Commands

```bash
# Start
docker compose up -d

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f task-api

# Check health
docker compose ps

# Stop
docker compose stop

# Stop and remove
docker compose down

# Rebuild
docker compose up -d --build
```

### Verification

```bash
# Check LocalStack
curl http://localhost:4566/_localstack/health

# Check Task API
curl http://localhost:8000/health
```

### Troubleshooting

**API not starting?**
```bash
docker compose logs task-api
# Common: LocalStack not ready - wait for health check
```

**Can't connect?**
```bash
curl http://localhost:8000/health
docker compose ps  # Is task-api running?
```

**LocalStack issues?**
```bash
docker compose logs localstack
curl http://localhost:4566/_localstack/health
```

---

## 📖 Authentication

All endpoints (except `/health`) require `X-API-Key` header.

**Default key:** `demo-secret-key-change-in-production`

**Change it:** Set `TASK_API_KEY` in `docker-compose.yml`

### Error Responses

**403 Forbidden:**
```json
{
  "success": false,
  "message": "Invalid API key"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "User abc-123 not found"
}
```

**422 Validation Error:**
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
  "id": "uuid",
  "name": "string (1-100 chars)",
  "email": "string (valid email)",
  "company": "string (1-100 chars)",
  "user_type": "client|prospect|partner",
  "notes": "string (optional, max 500)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### Scheduled Call
```json
{
  "id": "uuid",
  "user_id": "uuid (must exist)",
  "title": "string (1-200 chars)",
  "scheduled_for": "datetime (ISO 8601)",
  "duration_minutes": "integer (15-240)",
  "notes": "string (optional, max 500)",
  "status": "scheduled|completed|cancelled|rescheduled",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### Task
```json
{
  "id": "uuid",
  "title": "string (1-200 chars)",
  "description": "string (optional, max 1000)",
  "user_id": "uuid (optional)",
  "status": "todo|in_progress|done|cancelled",
  "due_date": "datetime (optional, ISO 8601)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

---

## 🧪 Complete Testing Flow

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Create user
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "company": "Test Company"
  }')

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
echo "Created user: $USER_ID"

# 3. Schedule call
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

# 4. Create task
TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Follow up\",
    \"user_id\": \"$USER_ID\"
  }")

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
echo "Created task: $TASK_ID"

# 5. List everything
echo "\n=== Users ==="
curl -s http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n=== Calls ==="
curl -s http://localhost:8000/calls \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n=== Tasks ==="
curl -s http://localhost:8000/tasks \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

# 6. Update statuses
curl -s -X PATCH "http://localhost:8000/calls/$CALL_ID/status?new_status=completed" \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

curl -s -X PATCH "http://localhost:8000/tasks/$TASK_ID/status?new_status=done" \
  -H "X-API-Key: demo-secret-key-change-in-production" | jq

echo "\n✅ Complete testing flow executed!"
```

**Save as `test_api.sh`:** `chmod +x test_api.sh && ./test_api.sh`

---

## 🔗 Interactive Documentation

**Swagger UI:** http://localhost:8000/docs
- Interactive API explorer
- Try endpoints in browser

**ReDoc:** http://localhost:8000/redoc
- Beautiful documentation
- Export OpenAPI spec

---

## 📂 S3 Storage Structure

```
mcp-pycon-demo-bucket/
├── users/
│   └── {uuid}.json
├── calls/
│   └── {uuid}.json
└── tasks/
    └── {uuid}.json
```

### View S3 Contents

```bash
# List buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# List users
aws --endpoint-url=http://localhost:4566 s3 ls s3://mcp-pycon-demo-bucket/users/

# Download file
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://mcp-pycon-demo-bucket/users/{USER_ID}.json \
  ./user.json

# View
cat user.json | jq
```

---

## 🛠️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TASK_API_KEY` | `demo-secret-key-change-in-production` | API key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_S3_BUCKET` | `mcp-pycon-demo-bucket` | S3 bucket |
| `AWS_ENDPOINT_URL` | `http://localstack:4566` | S3 endpoint |
| `AWS_ACCESS_KEY_ID` | `test` | AWS key (LocalStack) |
| `AWS_SECRET_ACCESS_KEY` | `test` | AWS secret (LocalStack) |

### Modify Configuration

Edit `docker-compose.yml`:

```yaml
task-api:
  environment:
    - TASK_API_KEY=your-custom-key
    - AWS_S3_BUCKET=your-bucket-name
```

Restart: `docker compose down && docker compose up -d`

---

## 🎯 Quick Reference

```bash
# Start
docker compose up -d && docker compose logs -f

# Health check
curl http://localhost:8000/health

# Create test user
curl -X POST http://localhost:8000/users \
  -H "X-API-Key: demo-secret-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","company":"Test Co"}'

# View logs
docker compose logs -f task-api

# Stop
docker compose down
```

---

## 📚 Resources

- **Project README:** [../README.md](../README.md)
- **MCP Server README:** [../mcp_server/README.md](../mcp_server/README.md)
- **FastAPI Documentation:** https://fastapi.tiangolo.com

---

**Built with ❤️ for PyCon - Demonstrating MCP + FastAPI + S3**
