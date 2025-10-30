set -e  # exit on any error

echo "Starting MCRAG Development Environment..."

# check for the virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up..."
    ./setup-venv.sh
fi

# activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# ensure all dependencies are up to date
echo "Updating dependencies from requirements.txt with UV..."
if command -v uv &> /dev/null; then
    uv pip install -q -r requirements.txt
else
    pip install -q -r requirements.txt
fi

# load environment variables
if [ -f .env ]; then
    echo "Loading environment from .env..."
    set -a
    source .env
    set +a
else
    echo ".env file not found in root directory"
    exit 1
fi

# check and install frontend dependencies
echo "Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "Frontend dependencies installed"
else
    echo "Frontend dependencies already installed"
fi

# start backend
start_backend() {
    echo "Starting backend server on ${BACKEND_HOST}:${BACKEND_PORT}..."
    cd backend
    # Use python from activated virtual environment
    python -m uvicorn server:app --reload --host $BACKEND_HOST --port $BACKEND_PORT &
    BACKEND_PID=$!
    cd ..
    echo "Backend started with PID: $BACKEND_PID"
}

# start frontend  
start_frontend() {
    echo " starting frontend server on port ${FRONTEND_PORT}..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo " frontend started with PID: $FRONTEND_PID"
}

# cleanup processes on exit
cleanup() {
    echo " shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo " goodbye!"
}

# trap signals to cleanup
trap cleanup EXIT INT TERM

# check if ports are available
echo "Checking port availability..."
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo " Port $BACKEND_PORT is already in use. Please check running processes."
    echo "   Use: lsof -i :$BACKEND_PORT to see what's using it"
    echo "   Use: kill <PID> to stop the conflicting process"
    exit 1
fi

if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo " Port $FRONTEND_PORT is already in use. Please check running processes."
    exit 1
fi

# start services
start_backend
sleep 2  # give backend time to start

start_frontend
sleep 2  # give frontend time to start

echo ""
echo " Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo " Frontend: http://localhost:${FRONTEND_PORT}"
echo " API Docs: http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# wait for user interrupt
wait