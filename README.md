# Multi Code Review And Generation (MCRAG)

MCRAG is an intelligent code generation system that uses multiple Large Language Models to generate, review, and iteratively refine code based on user prompts. The system employs a collaborative AI approach where one LLM generates code while two critic LLMs provide feedback for continuous improvement.

👉 Click [here](https://www.youtube.com/watch?v=yCULGu7LPDE) for the project demo !

## Architecture Overview

The system consists of three main components:

### Backend (FastAPI + Redis)
- **FastAPI Server**: RESTful API endpoints for code generation requests
- **Redis Database**: Session storage and data persistence
- **Multi-LLM Integration**: Gemini 2.5 Flash (generator), GPT-4o (critic1), DeepSeek R1 (critic2)
- **Background Processing**: Asynchronous workflow execution
- **Rate Limiting**: Built-in API rate limiting with exponential backoff

### Frontend (React)
- **Modern React Interface**: Clean, responsive user interface
- **Real-time Status Updates**: Live progress tracking during generation
- **Code Display**: Syntax-highlighted code output with copy functionality
- **Iteration Tracking**: Complete history of code evolution and reviews

### Workflow Engine
- **Iterative Refinement**: Up to 3 cycles of generation and improvement
- **Multi-LLM Collaboration**: Generator creates code, critics provide feedback
- **Intelligent Stopping**: Automatic termination based on feedback quality
- **Error Recovery**: Comprehensive error handling and recovery mechanisms

## Technology Stack

### Backend Technologies
- **FastAPI**: Modern Python web framework
- **Redis**: In-memory data structure store
- **Pydantic**: Data validation and serialization
- **AsyncIO**: Asynchronous programming support
- **Uvicorn**: ASGI server implementation

### Frontend Technologies
- **React 18**: Modern React with hooks
- **Tailwind CSS**: Utility-first CSS framework
- **Heroicons**: Beautiful SVG icons
- **Axios**: HTTP client for API communication
- **CRACO**: Create React App Configuration Override

### AI/ML Integration
- **OpenAI API**: GPT-4o for critic reviews
- **Google Generative AI**: Gemini 2.5 Flash for code generation
- **DeepSeek API**: Alternative critic perspective
- **Rate Limiting**: Intelligent API usage management

## Project Structure

```
mcrag/
├── .env                        
├── .env.example               # Environment template
├── .gitignore
├── README.md
├── start-dev.sh              # main development startup script
├── backend/
│   ├── llm_services.py       # LLM integration and services
│   ├── models.py             # Pydantic data models
│   ├── requirements.txt      # Python dependencies
│   ├── review_workflow.py    # Code generation workflow engine
│   ├── server.py            # FastAPI server and routes
│   └── start-dev.sh         # Backend startup script
├── evaluation/
│   ├── evaluate_mcrag.py     # Comprehensive evaluation framework
│   ├── quality_evaluator.py  # Code quality assessment
│   ├── quick_eval.py         # Quick single-case testing
│   ├── requirements.txt      # Evaluation dependencies
│   └── test_cases.py         # Test case definitions
└── frontend/
    ├── craco.config.js       # Create React App configuration
    ├── package.json          # Node.js dependencies and scripts
    ├── postcss.config.js     # PostCSS configuration
    ├── tailwind.config.js    # Tailwind CSS configuration
    ├── start-dev.sh          # Frontend startup script
    ├── public/
    │   └── index.html        # HTML template
    └── src/
        ├── App.css          # Application styles
        ├── App.js           # Main React application
        ├── index.css        # Global styles
        ├── index.js         # React entry point
        └── components/
            ├── CodeSubmission.js  # Code generation form
            ├── ReviewProgress.js  # Progress tracking component
            └── ReviewResult.js    # Results display component
```

## Installation and Setup

### Prerequisites
- Python 3.8+ with pip or uv
- Node.js 16+ with npm
- Redis server
- API keys for OpenAI, Gemini AI, and DeepSeek

### Quick Start (Recommended)

1. **Clone and navigate to the project:**
```bash
git clone <repository-url>
cd mcrag
```

2. **Set up environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

3. **Start the development environment:**
```bash
# This starts both backend and frontend automatically
./start-dev.sh
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8001
- **API Documentation**: http://127.0.0.1:8001/docs

### Environment Configuration

This project uses a centralized `.env` file in the root directory. Both backend and frontend reference this shared configuration.

#### Key Environment Variables

**Server Configuration:**
- `BACKEND_HOST=127.0.0.1` - Backend server host
- `BACKEND_PORT=8001` - Backend server port  
- `FRONTEND_PORT=3000` - Frontend development server port
- `REACT_APP_BACKEND_URL=http://127.0.0.1:8001` - Frontend API endpoint

**Database Configuration:**
- `REDIS_URL=redis://localhost:6379` - Redis connection
- `MONGO_URL=mongodb://localhost:27017` - MongoDB connection (if used)
- `DB_NAME=test_database` - Database name

**LLM API Keys:**
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o
- `GEMINI_API_KEY` - Google Gemini API key for code generation
- `DEEPSEEK_API_KEY` - DeepSeek API key for criticism
- `OPENROUTER_API_KEY` - OpenRouter API key (optional, for multi-LLM support)

**Model Configuration:**
- `MODEL_GENERATOR=gemini-2.5-flash` - Default generator model
- `MODEL_CRITIC1=gpt-4o` - First critic model
- `MODEL_CRITIC2=deepseek-r1` - Second critic model

#### Alternative Startup Methods

**Start services individually:**
```bash
# Backend only
cd backend && ./start-dev.sh

# Frontend only (in another terminal)
cd frontend && ./start-dev.sh
```

**Manual setup:**
```bash
# Backend
cd backend
pip install -r requirements.txt  # or: uv pip install -r requirements.txt
source ../.env
uvicorn server:app --reload --host $BACKEND_HOST --port $BACKEND_PORT

# Frontend (in another terminal)
cd frontend
npm install
source ../.env
npm start
```

### Manual Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

3. Start Redis server (if not running):
```bash
redis-server
```

4. Run the FastAPI server:
```bash
# Using environment from root .env
source ../.env
uvicorn server:app --reload --host $BACKEND_HOST --port $BACKEND_PORT

# Or use the startup script
./start-dev.sh
```

### Manual Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
# Using environment from root .env
source ../.env
npm start

# Or use the startup script
./start-dev.sh
```

## Workflow Process

### 1. Initial Generation
- User submits prompt with language and requirements
- Generator LLM creates initial code version
- System saves code with version 1

### 2. Critic Review Phase
- Critic 1 (GPT-4o) analyzes code for quality and improvements
- Critic 2 (DeepSeek R1) provides alternative perspective
- Both critics provide scores, suggestions, and severity ratings

### 3. Ranking and Planning
- Generator LLM evaluates both critic reviews
- Ranks feedback quality and usefulness
- Creates incorporation plan for improvements

### 4. Refinement Decision
- System decides whether to continue or stop refinement
- Continues if critic feedback is valuable (high scores)
- Stops if max iterations reached or poor feedback quality

### 5. Code Refinement
- Generator implements improvements based on critic feedback
- Creates new code version incorporating suggestions
- Process repeats until completion criteria met

### 6. Final Result
- Complete generation history preserved
- Final code version marked as result
- All iterations and reviews available for analysis

## Evaluation Framework

MCRAG includes a comprehensive evaluation system to quantify performance across multiple dimensions:

### Quick Evaluation
Test the system with a single case:
```bash
cd evaluation
python quick_eval.py
```

### Full Evaluation
Run comprehensive testing across all languages:
```bash
cd evaluation  
python evaluate_mcrag.py
```

### Language-Specific Testing
Test specific programming languages:
```bash
python evaluate_mcrag.py --languages python javascript
```

### Metrics Measured
- **Functionality** (25%) - Syntax correctness, logic implementation
- **Code Quality** (20%) - Style, structure, best practices  
- **Completeness** (20%) - Required features, edge cases
- **Efficiency** (15%) - Algorithm optimality, performance
- **Error Handling** (10%) - Exception handling, validation
- **Documentation** (10%) - Comments, clarity, maintainability

### Sample Results
```
MCRAG EVALUATION SUMMARY
============================================================
Total Tests: 15
Successful: 14  
Success Rate: 93.3%
Avg Processing Time: 45.2s

QUALITY METRICS
------------------------------
Overall         0.812 (±0.082)
Functionality   0.892 (±0.067)
Code Quality    0.834 (±0.089)
Completeness    0.876 (±0.074)
```

## Data Models

### CodeGenerationRequest
```python
{
  "id": "uuid",
  "user_prompt": "string",
  "language": "enum",
  "requirements": "optional string",
  "status": "enum",
  "session_id": "uuid"
}
```

### GeneratedCode
```python
{
  "id": "uuid",
  "request_id": "uuid",
  "session_id": "uuid",
  "generated_code": "string",
  "explanation": "string",
  "version": "integer",
  "created_at": "datetime"
}
```

### CriticReview
```python
{
  "id": "uuid",
  "session_id": "uuid",
  "code_id": "uuid",
  "critic_type": "CRITIC1|CRITIC2",
  "llm_model": "string",
  "review_text": "string",
  "suggestions": "list[string]",
  "severity_rating": "float",
  "confidence_score": "float",
  "processing_time": "float"
}
```

## Configuration

### Environment Variables

All configuration is managed through the centralized `.env` file in the project root. Copy `.env.example` to `.env` and configure the following:

#### Required API Keys
- `OPENAI_API_KEY`: OpenAI API access for GPT-4o
- `GEMINI_API_KEY`: Google AI API for Gemini models  
- `DEEPSEEK_API_KEY`: DeepSeek API access

#### Server Configuration
- `BACKEND_HOST`: Backend server host (default: 127.0.0.1)
- `BACKEND_PORT`: Backend server port (default: 8001)
- `FRONTEND_PORT`: Frontend development server port (default: 3000)
- `REACT_APP_BACKEND_URL`: Frontend API endpoint (default: http://127.0.0.1:8001)

#### Database Configuration
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379)
- `MONGO_URL`: MongoDB connection string (optional)
- `DB_NAME`: Database name (optional)

#### Model Configuration
- `MODEL_GENERATOR`: Generator model (default: gemini-2.5-flash)
- `MODEL_CRITIC1`: First critic model (default: gpt-4o)
- `MODEL_CRITIC2`: Second critic model (default: deepseek-r1)

#### Optional Configuration
- `OPENROUTER_API_KEY`: OpenRouter API for multi-LLM support
- `MAX_ITERATIONS`: Maximum refinement cycles (default: 3)
- `DEBUG`: Enable debug mode (default: true)
- `LOG_LEVEL`: Logging level (default: INFO)

### Rate Limiting
The system implements intelligent rate limiting for free tier APIs:
- Gemini API: 6-second intervals (10 requests/minute limit)
- Exponential backoff for rate limit errors
- Automatic retry mechanisms with proper delays

### Environment Variable Priority
1. System environment variables
2. Root `.env` file
3. Default values in code

## Development Guidelines

### Code Style
- Minimal, clean code generation with brief comments
- Modern language features and best practices
- No multi-line comments or verbose documentation in generated code
- Separation of code and explanations

### Contributing
1. Follow existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure rate limiting compliance for new LLM integrations

## Future Enhancements

### Planned Features
- Support for additional programming languages
- Custom critic model configuration
- Advanced code analysis and quality metrics
- Integration with popular development tools

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For questions, issues, or contributions, please refer to the project's issue tracker and documentation (to be updated).
