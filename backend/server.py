from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import our models and services
from models import (
    CodeSubmission, CodeSubmissionCreate, ReviewSession, LLMFeedback, 
    HumanFeedback, HumanFeedbackCreate, ReviewResult, ReviewStatus,
    StatusCheck, StatusCheckCreate
)
from review_workflow import ReviewWorkflow

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Multi-LLM Code Review System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize review workflow
review_workflow = ReviewWorkflow(db)

# Original status check endpoints
@api_router.get("/")
async def root():
    return {"message": "Multi-LLM Code Review System API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status")
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# New Code Review endpoints
@api_router.post("/submit-code", response_model=CodeSubmission)
async def submit_code_for_review(submission: CodeSubmissionCreate):
    """Submit code for multi-LLM review."""
    try:
        # Create code submission
        code_submission = CodeSubmission(**submission.dict())
        
        # Save to database
        await db.code_submissions.insert_one(code_submission.dict())
        
        return code_submission
    except Exception as e:
        logging.error(f"Error submitting code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting code: {str(e)}")

@api_router.post("/start-review/{submission_id}")
async def start_code_review(submission_id: str):
    """Start the multi-LLM review process for a code submission."""
    try:
        # Get submission
        submission_doc = await db.code_submissions.find_one({"id": submission_id})
        if not submission_doc:
            raise HTTPException(status_code=404, detail="Code submission not found")
        
        submission = CodeSubmission(**submission_doc)
        
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
        session_doc = await db.review_sessions.find_one({"id": session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        session = ReviewSession(**session_doc)
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
        session_doc = await db.review_sessions.find_one({"id": session_id})
        if not session_doc:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        session = ReviewSession(**session_doc)
        
        # Create human feedback
        human_feedback = HumanFeedback(
            session_id=session_id,
            submission_id=session.submission_id,
            **feedback.dict()
        )
        
        # Save to database
        await db.human_feedbacks.insert_one(human_feedback.dict())
        
        # Update session
        session.human_feedback_ids.append(human_feedback.id)
        await db.review_sessions.update_one(
            {"id": session_id},
            {"$set": {"human_feedback_ids": session.human_feedback_ids}}
        )
        
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
        submissions_cursor = db.code_submissions.find().sort("created_at", -1)
        submissions = []
        async for submission_doc in submissions_cursor:
            submission = CodeSubmission(**submission_doc)
            
            # Get associated session if exists
            session_doc = await db.review_sessions.find_one({"submission_id": submission.id})
            session_id = session_doc["id"] if session_doc else None
            
            submissions.append({
                "submission": submission,
                "session_id": session_id
            })
        
        return submissions
    except Exception as e:
        logging.error(f"Error getting submissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting submissions: {str(e)}")

@api_router.get("/llm-feedbacks/{session_id}")
async def get_llm_feedbacks(session_id: str):
    """Get all LLM feedbacks for a session."""
    try:
        feedbacks_cursor = db.llm_feedbacks.find({"session_id": session_id})
        feedbacks = []
        async for feedback_doc in feedbacks_cursor:
            feedbacks.append(LLMFeedback(**feedback_doc))
        
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
async def shutdown_db_client():
    client.close()