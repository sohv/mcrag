from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime

# Import our models and services
from models import (
    CodeGenerationRequest, CodeGenerationCreate, CodeGenerationSession, 
    GeneratedCode, CriticReview, ReviewRanking, GenerationResult, GenerationStatus,
    StatusCheck, StatusCheckCreate
)
from review_workflow import CodeGenerationWorkflow

# Custom JSON encoder to handle datetime objects
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def to_json(data):
    return json.dumps(data, default=json_serializer)

def from_json(data):
    return json.loads(data)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Redis connection
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url, decode_responses=True)

# Create the main app without a prefix
app = FastAPI(title="Multi-LLM Code Generation System", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize code generation workflow
generation_workflow = CodeGenerationWorkflow(redis_client)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Multi-LLM Code Generation System API"}

# Health check
@api_router.get("/health")
async def health_check():
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Main endpoint: Generate code from prompt
@api_router.post("/generate-code", response_model=CodeGenerationRequest)
async def generate_code(request: CodeGenerationCreate, background_tasks: BackgroundTasks):
    # Function documentation.
    try:
        # Create generation request
        generation_request = CodeGenerationRequest(**request.dict())
        
        # Save the request
        await redis_client.setex(f"request:{generation_request.id}", 86400, to_json(generation_request.dict()))
        
        # Start generation workflow in background
        background_tasks.add_task(start_generation_workflow, generation_request)
        
        logger.info(f"Code generation request {generation_request.id} created")
        return generation_request
        
    except Exception as e:
        logger.error(f"Error creating generation request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def start_generation_workflow(request: CodeGenerationRequest):
    # Function documentation.
    try:
        # Check if request is still pending
        request_data = await redis_client.get(f"request:{request.id}")
        if not request_data:
            logger.error(f"Request {request.id} not found")
            return
        
        current_request = CodeGenerationRequest(**from_json(request_data))
        if current_request.status != GenerationStatus.PENDING:
            logger.info(f"Request {request.id} already being processed")
            return
        
        # Start the generation workflow
        session = await generation_workflow.start_generation(current_request)
        logger.info(f"Generation workflow started for request {request.id}, session {session.id}")
        
    except Exception as e:
        logger.error(f"Error in generation workflow: {str(e)}")
        # Update request status to failed
        request.status = GenerationStatus.FAILED
        await redis_client.setex(f"request:{request.id}", 86400, to_json(request.dict()))

# Get generation result
@api_router.get("/generation-result/{session_id}", response_model=GenerationResult)
async def get_generation_result(session_id: str):
    # Function documentation.
    try:
        result = await generation_workflow.get_generation_result(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Generation result not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get generation status
@api_router.get("/generation-status/{request_id}")
async def get_generation_status(request_id: str):
    # Function documentation.
    try:
        # Get request
        request_data = await redis_client.get(f"request:{request_id}")
        if not request_data:
            raise HTTPException(status_code=404, detail="Generation request not found")
        
        request = CodeGenerationRequest(**from_json(request_data))
        
        # Get session if exists
        session = None
        session_data = await redis_client.get(f"session:{request.session_id}")
        if session_data:
            session = CodeGenerationSession(**from_json(session_data))
        
        return {
            "request_id": request_id,
            "status": request.status,
            "session_id": request.session_id if session else None,
            "current_iteration": session.refinement_iterations if session else 0,
            "max_iterations": session.max_iterations if session else 3,
            "created_at": request.created_at,
            "updated_at": request.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get final generated code
@api_router.get("/final-code/{session_id}")
async def get_final_code(session_id: str):
    # Function documentation.
    try:
        result = await generation_workflow.get_generation_result(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Generation result not found")
        
        if not result.final_code:
            raise HTTPException(status_code=404, detail="Final code not available yet")
        
        return {
            "session_id": session_id,
            "final_code": result.final_code,
            "status": result.session.status,
            "iterations": result.session.refinement_iterations,
            "summary": result.generation_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting final code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# List all generations (for debugging/monitoring)
@api_router.get("/list-generations")
async def list_generations():
    # Function documentation.
    try:
        keys = []
        async for key in redis_client.scan_iter(match="request:*"):
            keys.append(key)
        
        generations = []
        for key in keys[:20]:  # Limit to 20 most recent
            request_data = await redis_client.get(key)
            if request_data:
                request = CodeGenerationRequest(**from_json(request_data))
                generations.append({
                    "id": request.id,
                    "user_prompt": request.user_prompt[:100] + "..." if len(request.user_prompt) > 100 else request.user_prompt,
                    "language": request.language,
                    "status": request.status,
                    "created_at": request.created_at
                })
        
        # Sort by creation time (most recent first)
        generations.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"generations": generations}
        
    except Exception as e:
        logger.error(f"Error listing generations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy status endpoints for compatibility
@api_router.post("/status", response_model=StatusCheck)
async def create_status(status: StatusCheckCreate):
    # Function documentation.
    status_check = StatusCheck(**status.dict())
    await redis_client.setex(f"status:{status_check.id}", 86400, to_json(status_check.dict()))
    return status_check

@api_router.get("/status/{status_id}", response_model=StatusCheck)
async def get_status(status_id: str):
    # Function documentation.
    status_data = await redis_client.get(f"status:{status_id}")
    if not status_data:
        raise HTTPException(status_code=404, detail="Status not found")
    return StatusCheck(**from_json(status_data))

# LLM availability check
@api_router.get("/llm-status")
async def check_llm_status():
    # Function documentation.
    try:
        from llm_services import LLMService
        llm_service = LLMService()
        availability = await llm_service.check_llm_availability()
        
        return {
            "generator": {"model": "gemini-2.5-flash", "available": availability.get("gemini-2.5-flash", False)},
            "critic1": {"model": "gpt-4o", "available": availability.get("gpt-4o", False)},
            "critic2": {"model": "deepseek-r1", "available": availability.get("deepseek-r1", False)},
            "overall_health": all(availability.values())
        }
    except Exception as e:
        logger.error(f"Error checking LLM status: {str(e)}")
        return {
            "generator": {"model": "gemini-2.5-flash", "available": False},
            "critic1": {"model": "gpt-4o", "available": False},
            "critic2": {"model": "deepseek-r1", "available": False},
            "overall_health": False,
            "error": str(e)
        }

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
