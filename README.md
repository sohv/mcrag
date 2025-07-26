# Multi Code Review And Generation (MCRAG)

MCRAG is an intelligent code generation system that uses multiple Large Language Models to generate, review, and iteratively refine code based on user prompts. The system employs a collaborative AI approach where one LLM generates code while two critic LLMs provide feedback for continuous improvement.

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

## Key Features

### Code Generation
- Supports multiple programming languages (Python, JavaScript, TypeScript, Java, C++, etc.)
- Uses modern language features and best practices
- Generates minimal, clean code with brief single-line comments
- No verbose multi-line comments or documentation blocks

### Multi-LLM Review System
- **Generator (Gemini 2.5 Flash)**: Creates and refines code based on prompts
- **Critic 1 (GPT-4o)**: Provides detailed code analysis and suggestions
- **Critic 2 (DeepSeek R1)**: Offers alternative perspective and improvements
- **Fallback Support**: Gemini fallback for DeepSeek R1 when unavailable

### Intelligent Workflow
- **Iterative Improvement**: Each iteration incorporates critic feedback
- **Quality Assessment**: Critics rate code and provide scored feedback
- **Smart Termination**: Stops when feedback quality is low or max iterations reached
- **Consensus Building**: Generator ranks critic feedback and plans improvements

### Real-time Processing
- **Background Tasks**: Non-blocking code generation
- **Status Tracking**: Live updates on generation progress
- **Session Management**: Persistent sessions with unique identifiers
- **Result Retrieval**: Complete generation history and final results

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
├── .gitignore
├── README.md
├── SYSTEM_ARCHITECTURE.md
├── backend/
│   ├── llm_services.py
│   ├── models.py
│   ├── requirements.txt
│   ├── review_workflow.py
│   └── server.py
└── frontend/
    ├── craco.config.js
    ├── package-lock.json
    ├── package.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── yarn.lock
    ├── public/
    │   └── index.html
    └── src/
        ├── App.css
        ├── App.js
        ├── index.css
        ├── index.js
        └── components/
            ├── CodeSubmission.js
            ├── ReviewProgress.js
            └── ReviewResult.js
```

## Installation and Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 16+ with npm
- Redis server
- API keys for OpenAI, Gemini AI, and DeepSeek

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key"
export GOOGLE_API_KEY="your_google_api_key"
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export REDIS_URL="redis://localhost:6379"
```

4. Start Redis server:
```bash
redis-server
```

5. Run the FastAPI server:
```bash
uvicorn server:app --reload
```

### Frontend Setup

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
npm start
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

## Demo

[![Demo Video](https://img.shields.io/badge/▶️-Watch%20Demo-blue?style=for-the-badge)](https://github.com/sohan/mcrag/raw/main/mcrag.mp4)

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

#### Required API Keys
- `OPENAI_API_KEY`: OpenAI API access for GPT-4o
- `GOOGLE_API_KEY`: Google AI API for Gemini models
- `DEEPSEEK_API_KEY`: DeepSeek API access

#### Optional Configuration
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379)
- `MAX_ITERATIONS`: Maximum refinement cycles (default: 3)
- `RATE_LIMIT_DELAY`: Gemini API rate limiting delay (default: 6 seconds)

### Rate Limiting
The system implements intelligent rate limiting for free tier APIs:
- Gemini API: 6-second intervals (10 requests/minute limit)
- Exponential backoff for rate limit errors
- Automatic retry mechanisms with proper delays

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
