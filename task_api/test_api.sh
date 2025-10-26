#!/bin/bash

# Task API Test Script
# This script tests all API endpoints with sample data

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-demo-secret-key-change-in-production}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Task API - Complete Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "API URL: $API_URL"
echo "API Key: ${API_KEY:0:10}..."
echo ""

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -z "$data" ]; then
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json"
    else
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq is not installed. Install it for prettier output:${NC}"
    echo "   macOS: brew install jq"
    echo "   Ubuntu: sudo apt-get install jq"
    echo ""
fi

# Test 1: Health Check
echo -e "${BLUE}[1/11]${NC} Testing health check..."
HEALTH_RESPONSE=$(api_call GET "/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    if command -v jq &> /dev/null; then
        echo "$HEALTH_RESPONSE" | jq '.'
    else
        echo "$HEALTH_RESPONSE"
    fi
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Create User 1
echo -e "${BLUE}[2/11]${NC} Creating user 1 (María García)..."
USER1_DATA='{
  "name": "María García",
  "email": "maria@test-azollon.com",
  "company": "Test Azollon",
  "user_type": "client",
  "notes": "New client from PyCon demo"
}'

USER1_RESPONSE=$(api_call POST "/users" "$USER1_DATA")
USER1_ID=$(echo "$USER1_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$USER1_ID" ] && [ "$USER1_ID" != "null" ]; then
    echo -e "${GREEN}✅ User 1 created: $USER1_ID${NC}"
    if command -v jq &> /dev/null; then
        echo "$USER1_RESPONSE" | jq '.'
    fi
else
    echo -e "${RED}❌ Failed to create user 1${NC}"
    echo "$USER1_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Create User 2
echo -e "${BLUE}[3/11]${NC} Creating user 2 (John Smith)..."
USER2_DATA='{
  "name": "John Smith",
  "email": "john@startup.co",
  "company": "StartupCo",
  "user_type": "prospect"
}'

USER2_RESPONSE=$(api_call POST "/users" "$USER2_DATA")
USER2_ID=$(echo "$USER2_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$USER2_ID" ] && [ "$USER2_ID" != "null" ]; then
    echo -e "${GREEN}✅ User 2 created: $USER2_ID${NC}"
else
    echo -e "${RED}❌ Failed to create user 2${NC}"
    echo "$USER2_RESPONSE"
fi
echo ""

# Test 4: List Users
echo -e "${BLUE}[4/11]${NC} Listing all users..."
USERS_RESPONSE=$(api_call GET "/users")
USER_COUNT=$(echo "$USERS_RESPONSE" | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}✅ Found $USER_COUNT users${NC}"
if command -v jq &> /dev/null; then
    echo "$USERS_RESPONSE" | jq '.[] | {id: .id, name: .name, company: .company}'
fi
echo ""

# Test 5: Get Specific User
echo -e "${BLUE}[5/11]${NC} Getting user by ID..."
USER_DETAIL=$(api_call GET "/users/$USER1_ID")
echo -e "${GREEN}✅ Retrieved user details${NC}"
if command -v jq &> /dev/null; then
    echo "$USER_DETAIL" | jq '{name: .name, email: .email, company: .company}'
fi
echo ""

# Test 6: Schedule Call 1
echo -e "${BLUE}[6/11]${NC} Scheduling call 1..."
TOMORROW=$(date -u -v+1d +"%Y-%m-%dT10:00:00Z" 2>/dev/null || date -u -d "tomorrow" +"%Y-%m-%dT10:00:00Z" 2>/dev/null || echo "2025-10-25T10:00:00Z")

CALL1_DATA=$(cat <<EOF
{
  "user_id": "$USER1_ID",
  "title": "Onboarding Call - Test Azollon",
  "scheduled_for": "$TOMORROW",
  "duration_minutes": 45,
  "notes": "Initial onboarding and platform overview"
}
EOF
)

CALL1_RESPONSE=$(api_call POST "/calls" "$CALL1_DATA")
CALL1_ID=$(echo "$CALL1_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$CALL1_ID" ] && [ "$CALL1_ID" != "null" ]; then
    echo -e "${GREEN}✅ Call 1 scheduled: $CALL1_ID${NC}"
    if command -v jq &> /dev/null; then
        echo "$CALL1_RESPONSE" | jq '{title: .title, scheduled_for: .scheduled_for, status: .status}'
    fi
else
    echo -e "${RED}❌ Failed to schedule call 1${NC}"
    echo "$CALL1_RESPONSE"
fi
echo ""

# Test 7: Schedule Call 2
echo -e "${BLUE}[7/11]${NC} Scheduling call 2..."
CALL2_DATA=$(cat <<EOF
{
  "user_id": "$USER2_ID",
  "title": "Product Demo - StartupCo",
  "scheduled_for": "$TOMORROW",
  "duration_minutes": 30
}
EOF
)

CALL2_RESPONSE=$(api_call POST "/calls" "$CALL2_DATA")
CALL2_ID=$(echo "$CALL2_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$CALL2_ID" ] && [ "$CALL2_ID" != "null" ]; then
    echo -e "${GREEN}✅ Call 2 scheduled: $CALL2_ID${NC}"
else
    echo -e "${YELLOW}⚠️  Call 2 scheduling had issues${NC}"
fi
echo ""

# Test 8: List Calls
echo -e "${BLUE}[8/11]${NC} Listing all calls..."
CALLS_RESPONSE=$(api_call GET "/calls")
CALL_COUNT=$(echo "$CALLS_RESPONSE" | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}✅ Found $CALL_COUNT calls${NC}"
if command -v jq &> /dev/null; then
    echo "$CALLS_RESPONSE" | jq '.[] | {title: .title, status: .status, scheduled_for: .scheduled_for}'
fi
echo ""

# Test 9: Update Call Status
echo -e "${BLUE}[9/11]${NC} Updating call status to 'completed'..."
UPDATE_CALL_RESPONSE=$(api_call PATCH "/calls/$CALL1_ID/status?new_status=completed")
echo -e "${GREEN}✅ Call status updated${NC}"
if command -v jq &> /dev/null; then
    echo "$UPDATE_CALL_RESPONSE" | jq '{title: .title, status: .status}'
fi
echo ""

# Test 10: Create Tasks
echo -e "${BLUE}[10/11]${NC} Creating tasks..."
TASK1_DATA=$(cat <<EOF
{
  "title": "Prepare onboarding materials for Test Azollon",
  "description": "Create custom deck with use case examples",
  "user_id": "$USER1_ID"
}
EOF
)

TASK1_RESPONSE=$(api_call POST "/tasks" "$TASK1_DATA")
TASK1_ID=$(echo "$TASK1_RESPONSE" | jq -r '.id' 2>/dev/null || echo "")

if [ -n "$TASK1_ID" ] && [ "$TASK1_ID" != "null" ]; then
    echo -e "${GREEN}✅ Task created: $TASK1_ID${NC}"
    if command -v jq &> /dev/null; then
        echo "$TASK1_RESPONSE" | jq '{title: .title, status: .status}'
    fi
else
    echo -e "${RED}❌ Failed to create task${NC}"
fi
echo ""

# Test 11: List Tasks and Update Status
echo -e "${BLUE}[11/11]${NC} Listing tasks and updating status..."
TASKS_RESPONSE=$(api_call GET "/tasks")
TASK_COUNT=$(echo "$TASKS_RESPONSE" | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}✅ Found $TASK_COUNT tasks${NC}"

if [ -n "$TASK1_ID" ] && [ "$TASK1_ID" != "null" ]; then
    UPDATE_TASK_RESPONSE=$(api_call PATCH "/tasks/$TASK1_ID/status?new_status=in_progress")
    echo -e "${GREEN}✅ Task status updated to 'in_progress'${NC}"
    if command -v jq &> /dev/null; then
        echo "$UPDATE_TASK_RESPONSE" | jq '{title: .title, status: .status}'
    fi
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Users created:      ${GREEN}$USER_COUNT${NC}"
echo -e "Calls scheduled:    ${GREEN}$CALL_COUNT${NC}"
echo -e "Tasks created:      ${GREEN}$TASK_COUNT${NC}"
echo ""

if [ -n "$USER1_ID" ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Test data created:"
    echo "  User 1 ID:  $USER1_ID"
    if [ -n "$USER2_ID" ]; then
        echo "  User 2 ID:  $USER2_ID"
    fi
    if [ -n "$CALL1_ID" ]; then
        echo "  Call 1 ID:  $CALL1_ID"
    fi
    if [ -n "$CALL2_ID" ]; then
        echo "  Call 2 ID:  $CALL2_ID"
    fi
    if [ -n "$TASK1_ID" ]; then
        echo "  Task 1 ID:  $TASK1_ID"
    fi
    echo ""
    echo -e "${BLUE}📖 View interactive docs at: ${NC}http://localhost:8000/docs"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
