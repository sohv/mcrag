#!/bin/bash
# Load environment from root .env file
set -a
source ../.env
set +a

# Start the backend server using uv
uv run python -m uvicorn server:app --reload --host $BACKEND_HOST --port $BACKEND_PORT