from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FeedbackType(str, Enum):
    CODER = "coder"
    CRITIC1 = "critic1"
    CRITIC2 = "critic2"
    HUMAN = "human"

class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"

class CodeSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_code: str
    language: ProgrammingLanguage
    description: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CodeSubmissionCreate(BaseModel):
    original_code: str
    language: ProgrammingLanguage
    description: Optional[str] = None

class LLMFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    submission_id: str
    feedback_type: FeedbackType
    llm_model: str
    feedback_text: str
    suggested_code: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HumanFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    submission_id: str
    feedback_text: str
    rating: Optional[int] = None  # 1-5 rating on LLM feedback quality
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HumanFeedbackCreate(BaseModel):
    feedback_text: str
    rating: Optional[int] = None

class ReviewSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    submission_id: str
    coder_feedback_id: Optional[str] = None
    critic1_feedback_id: Optional[str] = None
    critic2_feedback_id: Optional[str] = None
    human_feedback_ids: List[str] = Field(default_factory=list)
    final_code: Optional[str] = None
    consensus_score: Optional[float] = None
    conflict_resolution: Optional[Dict[str, Any]] = None
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewResult(BaseModel):
    session: ReviewSession
    submission: CodeSubmission
    coder_feedback: Optional[LLMFeedback] = None
    critic_feedbacks: List[LLMFeedback] = Field(default_factory=list)
    human_feedbacks: List[HumanFeedback] = Field(default_factory=list)
    final_recommendations: Optional[str] = None

class ConflictResolution(BaseModel):
    conflicting_points: List[str]
    resolution_strategy: str
    final_decision: str
    confidence: float