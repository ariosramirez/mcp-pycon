# Dockerfile for MCP Server with HTTP/SSE transport using uv
# Build from project root: docker build -f mcp_server/Dockerfile -t mcp-server .

FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (frozen lockfile for reproducibility)
RUN uv sync --frozen --no-install-project --no-dev

# Final stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy MCP server code
COPY mcp_server/ ./mcp_server/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    MCP_TRANSPORT=sse \
    MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8001

# Expose MCP server port
EXPOSE 8001

# Health check - verify HTTP server is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run MCP server with HTTP/SSE transport
CMD ["python", "-m", "mcp_server.server", "--http"]
