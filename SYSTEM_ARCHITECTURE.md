# MCRAG - Multi-LLM Code Review and Generation System

## System Overview

MCRAG is an automated code generation and review system that uses multiple Large Language Models (LLMs) to generate, critique, and iteratively refine code based on user prompts. The system employs a Generator-Critic architecture where one LLM generates code while two other LLMs provide critical feedback, creating a collaborative AI coding environment.

## Architecture Components

### 1. Frontend (React Application)
- **Technology**: React with Tailwind CSS
- **Port**: 3000
- **Purpose**: User interface for code generation requests and result display

### 2. Backend (FastAPI Server)
- **Technology**: FastAPI with Python
- **Port**: 8000
- **Purpose**: API server, workflow orchestration, and LLM integration

### 3. Storage Layer
- **Technology**: Redis
- **Purpose**: Session management, temporary data storage, and workflow state persistence

### 4. LLM Integration
- **Generator**: Gemini 2.0 Flash Experimental (Google)
- **Critic 1**: GPT-4o (OpenAI)
- **Critic 2**: DeepSeek R1 (with Gemini fallback)

## Detailed System Flow

### Phase 1: User Request Submission

#### Frontend Process:
1. **User Input**: User enters a coding prompt in the web interface
2. **Request Creation**: Frontend creates a `CodeGenerationCreate` object with:
   - `user_prompt`: The coding request
   - `language`: Programming language (Python, JavaScript, etc.)
   - `requirements`: Optional additional requirements

3. **API Call**: POST request to `/api/generate-code`

#### Backend Process:
1. **Request Validation**: FastAPI validates the incoming request
2. **UUID Generation**: Creates unique request ID for tracking
3. **Redis Storage**: Stores request data with 24-hour expiration
4. **Background Task**: Initiates workflow in background thread
5. **Immediate Response**: Returns request ID to frontend for status polling

### Phase 2: Code Generation Workflow

#### Initial Code Generation:
```
Generator (Gemini) → Generates initial code based on user prompt
```

1. **Prompt Construction**: System creates detailed prompt including:
   - User's original request
   - Programming language specifications
   - Code quality guidelines
   - Documentation requirements

2. **Rate Limiting**: Implements 6-second intervals between Gemini calls (free tier: 10 requests/minute)

3. **Code Extraction**: Parses response to separate code from explanation

#### Parallel Critic Review:
```
Generated Code → [Critic 1 (GPT-4o), Critic 2 (Gemini)] → Reviews
```

1. **Concurrent Reviews**: Both critics analyze code simultaneously
2. **Critic 1 (GPT-4o)**: Focuses on:
   - Code correctness and bugs
   - Security issues
   - Best practices
   - Maintainability

3. **Critic 2 (DeepSeek/Gemini)**: Focuses on:
   - Performance optimization
   - Advanced design patterns
   - Scalability considerations
   - Algorithm efficiency

#### Review Ranking and Planning:
```
Generator (Gemini) → Ranks critic feedback → Creates incorporation plan
```

1. **Feedback Analysis**: Generator evaluates both critic reviews
2. **Quality Scoring**: Assigns scores (0.0-1.0) based on feedback value:
   - High scores (0.7-1.0): Valuable, actionable feedback
   - Low scores (0.0-0.3): Poor or irrelevant feedback

3. **Incorporation Planning**: Creates detailed plan for code improvements

### Phase 3: Iterative Refinement

#### Refinement Decision Logic:
```python
def should_stop_refinement():
    if iteration >= max_iterations:  # Max 3 iterations
        return True
    if both_critics_score < 0.3:    # Poor feedback quality
        return True
    if ranking_failed:              # Error state
        return True
    return False  # Continue refining
```

#### Code Refinement Process:
1. **Context Assembly**: Combines original prompt, current code, critic reviews, and incorporation plan
2. **Refinement Generation**: Generator creates improved code version
3. **Version Tracking**: Increments version number for code evolution tracking

### Phase 4: Status Monitoring and Completion

#### Frontend Polling:
```javascript
// Polls every 2 seconds for status updates
setInterval(() => {
    fetch(`/api/generation-status/${requestId}`)
        .then(response => response.json())
        .then(updateUI);
}, 2000);
```

#### Status Progression:
1. **PENDING**: Initial request created
2. **GENERATING**: Creating or refining code
3. **REVIEWING**: Critics analyzing code
4. **REFINING**: Generator ranking feedback and planning improvements
5. **COMPLETED**: Workflow finished
6. **FAILED**: Error occurred during process

## Data Models and Storage

### Core Data Structures:

#### CodeGenerationRequest
```python
- id: UUID
- user_prompt: str
- language: ProgrammingLanguage
- requirements: Optional[str]
- status: GenerationStatus
- session_id: Optional[UUID]
- created_at: datetime
```

#### CodeGenerationSession
```python
- id: UUID
- request_id: UUID
- status: GenerationStatus
- refinement_iterations: int (0-2)
- max_iterations: int (3)
- current_code_id: Optional[UUID]
- critic1_review_id: Optional[UUID]
- critic2_review_id: Optional[UUID]
- ranking_id: Optional[UUID]
```

#### GeneratedCode
```python
- id: UUID
- request_id: UUID
- session_id: UUID
- generated_code: str
- explanation: str
- version: int
- created_at: datetime
```

#### CriticReview
```python
- id: UUID
- session_id: UUID
- code_id: UUID
- critic_type: FeedbackType (CRITIC1/CRITIC2)
- llm_model: str
- review_text: str
- suggestions: List[str]
- severity_rating: int (1-5)
- confidence_score: float
- processing_time: float
```

#### ReviewRanking
```python
- id: UUID
- session_id: UUID
- code_id: UUID
- critic1_review_id: UUID
- critic2_review_id: UUID
- ranking_explanation: str
- critic1_score: float (0.0-1.0)
- critic2_score: float (0.0-1.0)
- incorporation_plan: str
```

### Redis Storage Strategy:
- **Keys**: `request:{id}`, `session:{id}`, `code:{id}`, `review:{id}`, `ranking:{id}`
- **TTL**: 24 hours (86400 seconds)
- **Serialization**: JSON with datetime handling

## API Endpoints

### Main Endpoints:

#### POST `/api/generate-code`
- **Purpose**: Initialize code generation workflow
- **Input**: CodeGenerationCreate
- **Output**: CodeGenerationRequest with unique ID
- **Process**: Creates background task for workflow execution

#### GET `/api/generation-status/{request_id}`
- **Purpose**: Get current workflow status
- **Output**: Status object with iteration count and progress
- **Polling**: Frontend calls every 2 seconds

#### GET `/api/final-code/{session_id}`
- **Purpose**: Retrieve completed code generation result
- **Output**: Final code with full generation history

#### GET `/api/llm-status`
- **Purpose**: Check availability of all LLM services
- **Output**: Health status of Gemini, OpenAI, and DeepSeek APIs

## Error Handling and Rate Limiting

### Rate Limiting Strategy:
```python
class LLMService:
    def __init__(self):
        self.gemini_min_interval = 6  # seconds
        self.gemini_last_request_time = 0
    
    async def _wait_for_gemini_rate_limit(self):
        # Ensures 6-second gaps between Gemini calls
        # Prevents 429 rate limit errors
```

### Error Recovery:
1. **Rate Limit Errors**: Automatic retry with exponential backoff
2. **API Failures**: Graceful degradation with error messaging
3. **Infinite Loop Prevention**: Multiple safety checks:
   - Max iteration limits
   - Error state detection
   - Timeout handling

### Fallback Mechanisms:
- **DeepSeek Unavailable**: Uses Gemini as Critic 2
- **Network Issues**: Retries with suggested delays
- **Parsing Failures**: Returns default values with error flags

## Security and Configuration

### Environment Variables:
```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
DEEPSEEK_API_KEY=sk-...
REDIS_URL=redis://localhost:6379
```

### CORS Configuration:
- Allows frontend (localhost:3000) to access backend (localhost:8000)
- Handles preflight OPTIONS requests
- Supports all standard HTTP methods

## Monitoring and Logging

### Logging Levels:
- **INFO**: Workflow progress, API calls, status changes
- **WARNING**: Rate limits, retries, degraded functionality
- **ERROR**: API failures, parsing errors, workflow failures

### Key Metrics Tracked:
- Processing times for each LLM call
- Iteration counts and completion rates
- Error rates and types
- API response times

## Future Enhancements

### Potential Improvements:
1. **Caching**: Store common code patterns and responses
2. **Load Balancing**: Multiple backend instances for scalability
3. **WebSocket Integration**: Real-time status updates instead of polling
4. **Code Execution**: Sandbox environment for testing generated code
5. **User Authentication**: Persistent sessions and request history
6. **Advanced Analytics**: Code quality metrics and improvement tracking

## System Requirements

### Development Environment:
- **Python 3.8+**: Backend dependencies
- **Node.js 16+**: Frontend build tools
- **Redis Server**: Data persistence
- **API Keys**: Valid credentials for all LLM services

### Production Considerations:
- **Rate Limits**: Monitor API usage and costs
- **Scaling**: Consider paid tiers for higher throughput
- **Monitoring**: Implement health checks and alerting
- **Security**: Secure API key management and HTTPS

## Troubleshooting Common Issues

### 1. Infinite Loop in Refinement:
- **Cause**: Ranking failures return scores that continue iteration
- **Solution**: Error detection in `_should_stop_refinement()`

### 2. Rate Limit Exceeded:
- **Cause**: Too many API calls in short time
- **Solution**: Implement proper rate limiting and backoff

### 3. Frontend Not Updating:
- **Cause**: Request status not being updated during iterations
- **Solution**: Ensure all workflow steps update request status in Redis

### 4. Code Generation Failures:
- **Cause**: Invalid prompts or API issues
- **Solution**: Better prompt validation and error handling

This system provides a robust, scalable foundation for AI-assisted code generation with built-in quality assurance through multi-LLM collaboration.
