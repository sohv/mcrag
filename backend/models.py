from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class GenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    REFINING = "refining"
    COMPLETED = "completed"
    FAILED = "failed"

class FeedbackType(str, Enum):
    GENERATOR = "generator"
    CRITIC1 = "critic1"
    CRITIC2 = "critic2"
    REFINEMENT = "refinement"

class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"

class CodeGenerationRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_prompt: str
    language: ProgrammingLanguage
    requirements: Optional[str] = None
    status: GenerationStatus = GenerationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CodeGenerationCreate(BaseModel):
    user_prompt: str
    language: ProgrammingLanguage
    requirements: Optional[str] = None

class GeneratedCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    session_id: str
    generated_code: str
    explanation: Optional[str] = None
    version: int = 1  # Tracks refinement iterations
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CriticReview(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    code_id: str
    critic_type: FeedbackType  # CRITIC1 or CRITIC2
    llm_model: str
    review_text: str
    suggestions: List[str] = Field(default_factory=list)
    severity_rating: int = Field(ge=1, le=5)  # 1=minor, 5=critical
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewRanking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    code_id: str
    critic1_review_id: str
    critic2_review_id: str
    ranking_explanation: str
    critic1_score: float = Field(ge=0, le=1)  # How valuable critic1's feedback is
    critic2_score: float = Field(ge=0, le=1)  # How valuable critic2's feedback is
    incorporation_plan: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CodeGenerationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    current_code_id: Optional[str] = None
    critic1_review_id: Optional[str] = None
    critic2_review_id: Optional[str] = None
    ranking_id: Optional[str] = None
    refinement_iterations: int = 0
    max_iterations: int = 3
    status: GenerationStatus = GenerationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GenerationResult(BaseModel):
    session: CodeGenerationSession
    request: CodeGenerationRequest
    generated_codes: List[GeneratedCode] = Field(default_factory=list)
    critic_reviews: List[CriticReview] = Field(default_factory=list)
    rankings: List[ReviewRanking] = Field(default_factory=list)
    final_code: Optional[str] = None
    generation_summary: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    status: str
    message: str