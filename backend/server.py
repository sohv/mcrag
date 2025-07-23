from fastapi import FastAPI, APIRouter, HTTPException
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
    CodeSubmission, CodeSubmissionCreate, ReviewSession, LLMFeedback, 
    HumanFeedback, HumanFeedbackCreate, ReviewResult, ReviewStatus,
    StatusCheck, StatusCheckCreate
)
from review_workflow import ReviewWorkflow

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
app = FastAPI(title="Multi-LLM Code Review System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize review workflow
review_workflow = ReviewWorkflow(redis_client)

# Original status check endpoints
@api_router.get("/")
async def root():
    return {"message": "Multi-LLM Code Review System API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    # Store in Redis with expiration (24 hours)
    await redis_client.setex(f"status:{status_obj.id}", 86400, to_json(status_obj.dict()))
    return status_obj

@api_router.get("/status")
async def get_status_checks():
    # Get all status check keys
    keys = await redis_client.keys("status:*")
    status_checks = []
    for key in keys:
        data = await redis_client.get(key)
        if data:
            status_checks.append(StatusCheck(**from_json(data)))
    return status_checks

# New Code Review endpoints
@api_router.post("/submit-code", response_model=CodeSubmission)
async def submit_code_for_review(submission: CodeSubmissionCreate):
    """Submit code for multi-LLM review."""
    try:
        # Create code submission
        code_submission = CodeSubmission(**submission.dict())
        
        # Save to Redis with expiration (24 hours)
        await redis_client.setex(f"submission:{code_submission.id}", 86400, to_json(code_submission.dict()))
        
        return code_submission
    except Exception as e:
        logging.error(f"Error submitting code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting code: {str(e)}")

@api_router.post("/start-review/{submission_id}")
async def start_code_review(submission_id: str):
    """Start the multi-LLM review process for a code submission."""
    try:
        # Get submission from Redis
        submission_data = await redis_client.get(f"submission:{submission_id}")
        if not submission_data:
            raise HTTPException(status_code=404, detail="Code submission not found")
        
        submission = CodeSubmission(**from_json(submission_data))
        
        if submission.status != ReviewStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Submission is not in pending status. Current status: {submission.status}")
        
        # Start review workflow (this will run in background)
        session = await review_workflow.start_review(submission)
        
        return {"session_id": session.id, "status": session.status, "message": "Review started successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error starting review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting review: {str(e)}")

@api_router.get("/review-result/{session_id}", response_model=ReviewResult)
async def get_review_result(session_id: str):
    """Get the complete review result for a session."""
    try:
        result = await review_workflow.get_review_result(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting review result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting review result: {str(e)}")

@api_router.get("/review-status/{session_id}")
async def get_review_status(session_id: str):
    """Get the current status of a review session."""
    try:
        session_data = await redis_client.get(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        session = ReviewSession(**from_json(session_data))
        return {
            "session_id": session.id,
            "status": session.status,
            "consensus_score": session.consensus_score,
            "has_coder_feedback": session.coder_feedback_id is not None,
            "has_critic1_feedback": session.critic1_feedback_id is not None,
            "has_critic2_feedback": session.critic2_feedback_id is not None,
            "human_feedback_count": len(session.human_feedback_ids)
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting review status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting review status: {str(e)}")

@api_router.post("/human-feedback/{session_id}")
async def add_human_feedback(session_id: str, feedback: HumanFeedbackCreate):
    """Add human feedback to a review session."""
    try:
        # Check if session exists
        session_data = await redis_client.get(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        session = ReviewSession(**from_json(session_data))
        
        # Create human feedback
        human_feedback = HumanFeedback(
            session_id=session_id,
            submission_id=session.submission_id,
            **feedback.dict()
        )
        
        # Save to Redis
        await redis_client.setex(f"human_feedback:{human_feedback.id}", 86400, to_json(human_feedback.dict()))
        
        # Update session
        session.human_feedback_ids.append(human_feedback.id)
        await redis_client.setex(f"session:{session_id}", 86400, to_json(session.dict()))
        
        return {"message": "Human feedback added successfully", "feedback_id": human_feedback.id}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error adding human feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding human feedback: {str(e)}")

@api_router.get("/submissions")
async def get_all_submissions():
    """Get all code submissions with their current status."""
    try:
        # Get all submission keys
        submission_keys = await redis_client.keys("submission:*")
        submissions = []
        
        for key in submission_keys:
            submission_data = await redis_client.get(key)
            if submission_data:
                submission = CodeSubmission(**from_json(submission_data))
                
                # Get associated session if exists
                session_keys = await redis_client.keys(f"session:*")
                session_id = None
                for session_key in session_keys:
                    session_data = await redis_client.get(session_key)
                    if session_data:
                        session = ReviewSession(**from_json(session_data))
                        if session.submission_id == submission.id:
                            session_id = session.id
                            break
                
                submissions.append({
                    "submission": submission,
                    "session_id": session_id
                })
        
        # Sort by created_at (newest first)
        submissions.sort(key=lambda x: x["submission"].created_at, reverse=True)
        return submissions
    except Exception as e:
        logging.error(f"Error getting submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting submissions: {str(e)}")

@api_router.get("/llm-feedbacks/{session_id}")
async def get_llm_feedbacks(session_id: str):
    """Get all LLM feedbacks for a session."""
    try:
        # Get all feedback keys and filter by session_id
        feedback_keys = await redis_client.keys("feedback:*")
        feedbacks = []
        
        for key in feedback_keys:
            feedback_data = await redis_client.get(key)
            if feedback_data:
                feedback = LLMFeedback(**from_json(feedback_data))
                if feedback.session_id == session_id:
                    feedbacks.append(feedback)
        
        return feedbacks
    except Exception as e:
        logging.error(f"Error getting LLM feedbacks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting LLM feedbacks: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_redis_client():
    await redis_client.close()