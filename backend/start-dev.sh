set -e

# Navigate to root directory
cd ..

# Load environment from root .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo ".env file not found in root directory"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    ./setup-venv.sh
fi

# Activate centralized virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Ensure dependencies are installed from root requirements.txt
echo "Checking dependencies..."
pip install -q -r requirements.txt

cd backend

# Start backend server
echo "Starting backend server on ${BACKEND_HOST}:${BACKEND_PORT}..."
python -m uvicorn server:app --reload --host $BACKEND_HOST --port $BACKEND_PORT