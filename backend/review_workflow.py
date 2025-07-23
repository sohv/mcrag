import asyncio
from typing import Optional
from models import (
    CodeSubmission, ReviewSession, LLMFeedback, ReviewResult, 
    ReviewStatus, FeedbackType, ConflictResolution, HumanFeedback
)
from llm_services import LLMService
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class ReviewWorkflow:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.llm_service = LLMService()
        
    async def start_review(self, submission: CodeSubmission) -> ReviewSession:
        """Start the complete review workflow."""
        logger.info(f"Starting review for submission {submission.id}")
        
        # Create review session
        session = ReviewSession(
            submission_id=submission.id,
            status=ReviewStatus.IN_PROGRESS
        )
        
        # Update submission status
        submission.status = ReviewStatus.IN_PROGRESS
        
        # Save initial session and update submission
        await self.db.review_sessions.insert_one(session.dict())
        await self.db.code_submissions.update_one(
            {"id": submission.id},
            {"$set": {"status": submission.status.value}}
        )
        
        try:
            # Step 1: Get coder feedback
            logger.info("Getting coder feedback...")
            coder_response, suggested_code, processing_time = await self.llm_service.get_coder_feedback(
                submission.original_code, 
                submission.language, 
                submission.description
            )
            
            coder_feedback = LLMFeedback(
                session_id=session.id,
                submission_id=submission.id,
                feedback_type=FeedbackType.CODER,
                llm_model="gemini-2.0-flash",
                feedback_text=coder_response,
                suggested_code=suggested_code,
                processing_time=processing_time
            )
            
            await self.db.llm_feedbacks.insert_one(coder_feedback.dict())
            session.coder_feedback_id = coder_feedback.id
            
            # Step 2: Get critic feedbacks in parallel
            logger.info("Getting critic feedbacks...")
            critic_tasks = [
                self.llm_service.get_critic_feedback(
                    submission.original_code, coder_response, submission.language, 1, suggested_code
                ),
                self.llm_service.get_critic_feedback(
                    submission.original_code, coder_response, submission.language, 2, suggested_code
                )
            ]
            
            critic_results = await asyncio.gather(*critic_tasks, return_exceptions=True)
            
            # Process critic 1 results
            if not isinstance(critic_results[0], Exception):
                critic1_response, critic1_time = critic_results[0]
                critic1_feedback = LLMFeedback(
                    session_id=session.id,
                    submission_id=submission.id,
                    feedback_type=FeedbackType.CRITIC1,
                    llm_model="gpt-4o",
                    feedback_text=critic1_response,
                    processing_time=critic1_time
                )
                await self.db.llm_feedbacks.insert_one(critic1_feedback.dict())
                session.critic1_feedback_id = critic1_feedback.id
            else:
                logger.error(f"Critic 1 failed: {critic_results[0]}")
            
            # Process critic 2 results
            if not isinstance(critic_results[1], Exception):
                critic2_response, critic2_time = critic_results[1]
                critic2_feedback = LLMFeedback(
                    session_id=session.id,
                    submission_id=submission.id,
                    feedback_type=FeedbackType.CRITIC2,
                    llm_model="deepseek-r1",  # Updated model name
                    feedback_text=critic2_response,
                    processing_time=critic2_time
                )
                await self.db.llm_feedbacks.insert_one(critic2_feedback.dict())
                session.critic2_feedback_id = critic2_feedback.id
            else:
                logger.error(f"Critic 2 failed: {critic_results[1]}")
            
            # Step 3: Analyze conflicts and generate consensus
            if session.critic1_feedback_id and session.critic2_feedback_id:
                logger.info("Analyzing conflicts and generating consensus...")
                conflict_analysis = self.llm_service.analyze_conflicts(
                    coder_response,
                    critic1_response if not isinstance(critic_results[0], Exception) else "",
                    critic2_response if not isinstance(critic_results[1], Exception) else ""
                )
                
                session.conflict_resolution = conflict_analysis
                session.consensus_score = conflict_analysis["confidence"]
            
            # Step 4: Generate final recommendations
            final_recommendations = self._generate_final_recommendations(
                coder_response,
                critic1_response if not isinstance(critic_results[0], Exception) else None,
                critic2_response if not isinstance(critic_results[1], Exception) else None,
                session.conflict_resolution
            )
            
            # Update session
            session.status = ReviewStatus.COMPLETED
            session.final_code = suggested_code
            
            await self.db.review_sessions.update_one(
                {"id": session.id},
                {"$set": session.dict()}
            )
            
            # Update submission
            await self.db.code_submissions.update_one(
                {"id": submission.id},
                {"$set": {"status": ReviewStatus.COMPLETED.value}}
            )
            
            logger.info(f"Review completed for submission {submission.id}")
            return session
            
        except Exception as e:
            logger.error(f"Review failed for submission {submission.id}: {str(e)}")
            # Update session and submission status to failed
            session.status = ReviewStatus.FAILED
            await self.db.review_sessions.update_one(
                {"id": session.id},
                {"$set": {"status": ReviewStatus.FAILED.value}}
            )
            await self.db.code_submissions.update_one(
                {"id": submission.id},
                {"$set": {"status": ReviewStatus.FAILED.value}}
            )
            raise
    
    def _generate_final_recommendations(
        self, 
        coder_feedback: str, 
        critic1_feedback: Optional[str], 
        critic2_feedback: Optional[str],
        conflict_resolution: Optional[dict]
    ) -> str:
        """Generate final recommendations based on all feedback."""
        
        recommendations = ["## Final Code Review Recommendations\n"]
        
        # Add coder's main points
        recommendations.append("### Primary Improvement Areas (from Coder)")
        recommendations.append(coder_feedback[:500] + "...\n" if len(coder_feedback) > 500 else coder_feedback + "\n")
        
        # Add critic insights
        if critic1_feedback:
            recommendations.append("### Critical Analysis (Critic 1)")
            recommendations.append(critic1_feedback[:300] + "...\n" if len(critic1_feedback) > 300 else critic1_feedback + "\n")
        
        if critic2_feedback:
            recommendations.append("### Practical Considerations (Critic 2)")
            recommendations.append(critic2_feedback[:300] + "...\n" if len(critic2_feedback) > 300 else critic2_feedback + "\n")
        
        # Add conflict resolution
        if conflict_resolution:
            recommendations.append("### Consensus and Resolution")
            recommendations.append(f"**Confidence Level:** {conflict_resolution['confidence']:.1%}")
            recommendations.append(f"**Decision:** {conflict_resolution['final_decision']}\n")
            
            if conflict_resolution['conflicting_points']:
                recommendations.append("**Conflicting Points:**")
                for point in conflict_resolution['conflicting_points']:
                    recommendations.append(f"- {point}")
        
        return "\n".join(recommendations)
    
    async def get_review_result(self, session_id: str) -> Optional[ReviewResult]:
        """Get complete review result for a session."""
        try:
            # Get session
            session_doc = await self.db.review_sessions.find_one({"id": session_id})
            if not session_doc:
                return None
            session = ReviewSession(**session_doc)
            
            # Get submission
            submission_doc = await self.db.code_submissions.find_one({"id": session.submission_id})
            if not submission_doc:
                return None
            submission = CodeSubmission(**submission_doc)
            
            # Get feedbacks
            coder_feedback = None
            if session.coder_feedback_id:
                feedback_doc = await self.db.llm_feedbacks.find_one({"id": session.coder_feedback_id})
                if feedback_doc:
                    coder_feedback = LLMFeedback(**feedback_doc)
            
            critic_feedbacks = []
            for critic_id in [session.critic1_feedback_id, session.critic2_feedback_id]:
                if critic_id:
                    feedback_doc = await self.db.llm_feedbacks.find_one({"id": critic_id})
                    if feedback_doc:
                        critic_feedbacks.append(LLMFeedback(**feedback_doc))
            
            # Get human feedbacks
            human_feedbacks = []
            if session.human_feedback_ids:
                human_feedback_cursor = self.db.human_feedbacks.find(
                    {"id": {"$in": session.human_feedback_ids}}
                )
                async for feedback_doc in human_feedback_cursor:
                    human_feedbacks.append(HumanFeedback(**feedback_doc))
            
            # Generate final recommendations
            final_recommendations = self._generate_final_recommendations(
                coder_feedback.feedback_text if coder_feedback else "",
                critic_feedbacks[0].feedback_text if len(critic_feedbacks) > 0 else None,
                critic_feedbacks[1].feedback_text if len(critic_feedbacks) > 1 else None,
                session.conflict_resolution
            )
            
            return ReviewResult(
                session=session,
                submission=submission,
                coder_feedback=coder_feedback,
                critic_feedbacks=critic_feedbacks,
                human_feedbacks=human_feedbacks,
                final_recommendations=final_recommendations
            )
            
        except Exception as e:
            logger.error(f"Error getting review result for session {session_id}: {str(e)}")
            return None