import asyncio
import json
from datetime import datetime
from typing import Optional
from models import (
    CodeGenerationRequest, CodeGenerationSession, GeneratedCode, CriticReview,
    ReviewRanking, GenerationResult, GenerationStatus, FeedbackType
)
from llm_services import LLMService
import logging

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime objects
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def to_json(data):
    return json.dumps(data, default=json_serializer)

def from_json(data):
    return json.loads(data)

class CodeGenerationWorkflow:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.llm_service = LLMService()
        
    async def start_generation(self, request: CodeGenerationRequest) -> CodeGenerationSession:
        # Function documentation.
        logger.info(f"Starting code generation for request {request.id}")
        
        # Create generation session
        session = CodeGenerationSession(
            request_id=request.id,
            status=GenerationStatus.GENERATING
        )
        
        # Update request status and link to session
        request.status = GenerationStatus.GENERATING
        request.session_id = session.id  # This was missing!
        
        # Save initial session and update request
        await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
        await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
        
        try:
            # Start the iterative generation and refinement process
            await self._run_generation_cycle(session, request)
            
        except Exception as e:
            logger.error(f"Generation workflow failed: {str(e)}")
            session.status = GenerationStatus.FAILED
            request.status = GenerationStatus.FAILED
            await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
            await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
            raise
        
        return session

    async def _run_generation_cycle(self, session: CodeGenerationSession, request: CodeGenerationRequest):
        # Function documentation.
        
        previous_code = None  # Track previous code for verification
        
        while session.refinement_iterations < session.max_iterations:
            logger.info(f"Starting iteration {session.refinement_iterations + 1}")
            
            # Step 1: Generate code (or refine existing code)
            if session.current_code_id is None:
                # Initial generation
                generated_code = await self._generate_initial_code(session, request)
            else:
                # Refine based on critic feedback
                generated_code = await self._refine_code(session, request)
            
            session.current_code_id = generated_code.id
            
            # Step 2: PARALLEL EXECUTION - Get critic reviews AND verify previous iteration
            # This is where we save time by overlapping verification with critics
            session.status = GenerationStatus.REVIEWING
            request.status = GenerationStatus.REVIEWING 
            await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
            await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
            
            # Build parallel tasks
            tasks = [
                self._get_critic_review(generated_code, FeedbackType.CRITIC1),
                self._get_critic_review(generated_code, FeedbackType.CRITIC2)
            ]
            
            # Add verification task if we have previous code to verify
            verification_task = None
            if previous_code is not None and session.ranking_id is not None:
                # Get ranking to verify
                ranking_data = await self.redis.get(f"ranking:{session.ranking_id}")
                ranking = ReviewRanking(**from_json(ranking_data))
                
                # Check if we should verify with LLM (hybrid logic)
                if await self._should_verify_with_llm(previous_code, generated_code, ranking, session, request):
                    logger.info("Running LLM verification in parallel with critics...")
                    verification_task = self._verify_incorporation(
                        previous_code, generated_code, ranking, session, request
                    )
                    tasks.append(verification_task)
                else:
                    logger.info("Skipping LLM verification (metrics only)")
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks)
            critic1_review = results[0]
            critic2_review = results[1]
            verification_result = results[2] if len(results) > 2 else None
            
            # Link verification to previous ranking if it was done
            if verification_result and session.ranking_id:
                ranking_data = await self.redis.get(f"ranking:{session.ranking_id}")
                ranking = ReviewRanking(**from_json(ranking_data))
                ranking.verification_id = verification_result.id
                await self.redis.setex(f"ranking:{ranking.id}", 86400, to_json(ranking.dict()))
            
            session.critic1_review_id = critic1_review.id
            session.critic2_review_id = critic2_review.id
            
            # Step 3: Generator ranks the reviews and decides on refinements
            session.status = GenerationStatus.REFINING
            request.status = GenerationStatus.REFINING
            await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
            await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
            
            ranking = await self._rank_and_plan_refinement(generated_code, critic1_review, critic2_review)
            session.ranking_id = ranking.id
            
            # Check if refinement is needed
            if await self._should_stop_refinement(ranking, session):
                # Before stopping, verify the final iteration if needed
                if previous_code is not None and not verification_result:
                    await self._verify_final_iteration(previous_code, generated_code, ranking, session, request)
                
                session.status = GenerationStatus.COMPLETED
                request.status = GenerationStatus.COMPLETED
                await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
                await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
                break
            
            # Store current code as previous for next iteration's verification
            previous_code = generated_code
            
            # Continue to next iteration
            session.refinement_iterations += 1
            session.status = GenerationStatus.GENERATING
            request.status = GenerationStatus.GENERATING
            await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
            await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
        
        # If we've reached max iterations, mark as completed
        if session.status != GenerationStatus.COMPLETED:
            session.status = GenerationStatus.COMPLETED
            request.status = GenerationStatus.COMPLETED
            await self.redis.setex(f"session:{session.id}", 86400, to_json(session.dict()))
            await self.redis.setex(f"request:{request.id}", 86400, to_json(request.dict()))
    
    async def _generate_initial_code(self, session: CodeGenerationSession, request: CodeGenerationRequest) -> GeneratedCode:
        # Function documentation.
        logger.info("Generating initial code...")
        
        prompt = f"""
        Generate minimal, clean {request.language.value} code based on this request:
        
        User Prompt: {request.user_prompt}
        
        Additional Requirements: {request.requirements or 'None specified'}
        
        Requirements:
        1. Write minimal, concise code using modern {request.language.value} features
        2. Use only brief single-line comments where absolutely necessary
        3. NO multi-line comments or block comments
        4. Focus on clean, readable code structure over verbose explanations
        5. Use recent language version features and best practices
        
        Provide only the code - explanations will be handled separately.
        """
        
        code_response, explanation, processing_time = await self.llm_service.get_generator_response(
            prompt, request.language.value
        )
        
        # Check if code generation failed
        if code_response.startswith("# Error generating code"):
            logger.error(f"Code generation failed: {explanation}")
            # Still create the object but mark it clearly as failed
            explanation = f"GENERATION FAILED: {explanation}"
        
        generated_code = GeneratedCode(
            request_id=request.id,
            session_id=session.id,
            generated_code=code_response,
            explanation=explanation,
            version=1
        )
        
        # Save generated code
        await self.redis.setex(f"code:{generated_code.id}", 86400, to_json(generated_code.dict()))
        
        return generated_code

    async def _refine_code(self, session: CodeGenerationSession, request: CodeGenerationRequest) -> GeneratedCode:
        # Function documentation.
        logger.info("Refining code based on critic feedback...")
        
        # Get current code and latest ranking
        current_code_data = await self.redis.get(f"code:{session.current_code_id}")
        current_code = GeneratedCode(**from_json(current_code_data))
        
        ranking_data = await self.redis.get(f"ranking:{session.ranking_id}")
        ranking = ReviewRanking(**from_json(ranking_data))
        
        # Get critic reviews
        critic1_data = await self.redis.get(f"review:{session.critic1_review_id}")
        critic1_review = CriticReview(**from_json(critic1_data))
        
        critic2_data = await self.redis.get(f"review:{session.critic2_review_id}")
        critic2_review = CriticReview(**from_json(critic2_data))
        
        prompt = f"""
        Refine this {request.language.value} code based on the critic feedback and your ranking:
        
        Original Request: {request.user_prompt}
        
        Current Code:
        {current_code.generated_code}
        
        Critic 1 Review (Score: {ranking.critic1_score}):
        {critic1_review.review_text}
        Suggestions: {', '.join(critic1_review.suggestions)}
        
        Critic 2 Review (Score: {ranking.critic2_score}):
        {critic2_review.review_text}
        Suggestions: {', '.join(critic2_review.suggestions)}
        
        Your Incorporation Plan:
        {ranking.incorporation_plan}
        
        Requirements for refined code:
        1. Write minimal, concise code using modern {request.language.value} features
        2. Use only brief single-line comments where absolutely necessary
        3. NO multi-line comments or block comments
        4. Focus on implementing the improvements without verbose explanations
        5. Use recent language version features and best practices
        
        Provide only the refined code - change explanations will be handled separately.
        """
        
        refined_code_response, explanation, processing_time = await self.llm_service.get_generator_response(
            prompt, request.language.value
        )
        
        # Check if code refinement failed
        if refined_code_response.startswith("# Error generating code"):
            logger.error(f"Code refinement failed: {explanation}")
            explanation = f"REFINEMENT FAILED: {explanation}"
        
        refined_code = GeneratedCode(
            request_id=request.id,
            session_id=session.id,
            generated_code=refined_code_response,
            explanation=explanation,
            version=current_code.version + 1
        )
        
        # Save refined code
        await self.redis.setex(f"code:{refined_code.id}", 86400, to_json(refined_code.dict()))
        
        # Note: Verification now happens in parallel with next iteration's critics
        # See _run_generation_cycle for the parallel execution logic
        
        return refined_code

    async def _get_critic_review(self, generated_code: GeneratedCode, critic_type: FeedbackType) -> CriticReview:
        # Function documentation.
        logger.info(f"Getting {critic_type.value} review...")
        
        # Get the original request for context
        request_data = await self.redis.get(f"request:{generated_code.request_id}")
        request = CodeGenerationRequest(**from_json(request_data))
        
        model_name = "gpt-4o" if critic_type == FeedbackType.CRITIC1 else "deepseek-r1"
        
        review_text, suggestions, severity, confidence, processing_time = await self.llm_service.get_critic_review(
            generated_code.generated_code,
            request.user_prompt,
            request.language.value,
            model_name
        )
        
        critic_review = CriticReview(
            session_id=generated_code.session_id,
            code_id=generated_code.id,
            critic_type=critic_type,
            llm_model=model_name,
            review_text=review_text,
            suggestions=suggestions,
            severity_rating=severity,
            confidence_score=confidence,
            processing_time=processing_time
        )
        
        # Save critic review
        await self.redis.setex(f"review:{critic_review.id}", 86400, to_json(critic_review.dict()))
        
        return critic_review

    async def _rank_and_plan_refinement(self, generated_code: GeneratedCode, 
                                      critic1_review: CriticReview, 
                                      critic2_review: CriticReview) -> ReviewRanking:
        # Function documentation.
        logger.info("Ranking critic reviews and planning refinement...")
        
        # Get the original request for context
        request_data = await self.redis.get(f"request:{generated_code.request_id}")
        request = CodeGenerationRequest(**from_json(request_data))
        
        ranking_text, critic1_score, critic2_score, plan = await self.llm_service.rank_reviews_and_plan(
            generated_code.generated_code,
            request.user_prompt,
            critic1_review.review_text,
            critic1_review.suggestions,
            critic2_review.review_text,
            critic2_review.suggestions,
            request.language.value
        )
        
        # Check if ranking failed due to errors (like rate limits)
        if "Error during ranking" in ranking_text:
            logger.warning(f"Ranking failed, forcing completion: {ranking_text}")
        
        ranking = ReviewRanking(
            session_id=generated_code.session_id,
            code_id=generated_code.id,
            critic1_review_id=critic1_review.id,
            critic2_review_id=critic2_review.id,
            ranking_explanation=ranking_text,
            critic1_score=critic1_score,
            critic2_score=critic2_score,
            incorporation_plan=plan
        )
        
        # Save ranking
        await self.redis.setex(f"ranking:{ranking.id}", 86400, to_json(ranking.dict()))
        
        return ranking

    async def _should_verify_with_llm(self, original_code: GeneratedCode, refined_code: GeneratedCode,
                                      ranking: ReviewRanking, session: CodeGenerationSession,
                                      request: CodeGenerationRequest) -> bool:
        """Hybrid logic: Decide if LLM verification is needed or if metrics are enough"""
        from models import VerificationMode
        
        mode = session.verification_mode
        
        # Check verification mode
        if mode == VerificationMode.DISABLED:
            return False
        
        if mode == VerificationMode.METRICS_ONLY:
            return False
        
        if mode == VerificationMode.ALWAYS:
            return True
        
        # Calculate quick objective metrics (instant, no LLM)
        metrics = self.llm_service.calculate_objective_metrics(
            original_code.generated_code,
            refined_code.generated_code,
            request.language.value
        )
        
        if mode == VerificationMode.FINAL_ONLY:
            # Only verify last iteration
            return session.refinement_iterations >= session.max_iterations - 1
        
        if mode == VerificationMode.SMART:
            # Hybrid: Verify with LLM only when needed
            
            # Red flag: No improvements detected by metrics
            if metrics.get('assessment') == 'no_improvement':
                logger.info("LLM verification triggered: No objective improvements detected")
                return True
            
            # Red flag: Critics strongly disagree (>0.4 difference)
            score_diff = abs(ranking.critic1_score - ranking.critic2_score)
            if score_diff > 0.4:
                logger.info(f"LLM verification triggered: Critics disagree (diff={score_diff:.2f})")
                return True
            
            # Always verify final iteration
            if session.refinement_iterations >= session.max_iterations - 1:
                logger.info("LLM verification triggered: Final iteration")
                return True
            
            # Skip LLM verification - metrics are enough
            logger.info(f"Metrics assessment: {metrics.get('assessment')} - Skipping LLM verification")
            return False
        
        # Default: don't verify
        return False
    
    async def _verify_incorporation(self, original_code: GeneratedCode, refined_code: GeneratedCode,
                                   ranking: ReviewRanking, session: CodeGenerationSession,
                                   request: CodeGenerationRequest):
        """Run verification (LLM + metrics) and save results"""
        from models import VerificationResult
        
        logger.info("Running verification...")
        
        # LLM verification
        verification_text, incorporation_score = await self.llm_service.verify_incorporation(
            original_code.generated_code,
            refined_code.generated_code,
            ranking.incorporation_plan,
            request.language.value
        )
        
        # Objective metrics
        objective_metrics = self.llm_service.calculate_objective_metrics(
            original_code.generated_code,
            refined_code.generated_code,
            request.language.value
        )
        
        # Create verification result
        verification = VerificationResult(
            session_id=session.id,
            original_code_id=original_code.id,
            refined_code_id=refined_code.id,
            incorporation_plan=ranking.incorporation_plan,
            verification_text=verification_text,
            incorporation_score=incorporation_score,
            objective_improvements=objective_metrics
        )
        
        # Save verification
        await self.redis.setex(f"verification:{verification.id}", 86400, to_json(verification.dict()))
        
        logger.info(f"Verification complete - Score: {incorporation_score:.2f}, "
                   f"Assessment: {objective_metrics.get('assessment', 'unknown')}")
        
        return verification
    
    async def _verify_final_iteration(self, original_code: GeneratedCode, refined_code: GeneratedCode,
                                      ranking: ReviewRanking, session: CodeGenerationSession,
                                      request: CodeGenerationRequest):
        """Verify final iteration if it wasn't verified during parallel execution"""
        from models import VerificationMode
        
        if session.verification_mode in [VerificationMode.DISABLED, VerificationMode.METRICS_ONLY]:
            return
        
        logger.info("Running final verification before completion...")
        verification = await self._verify_incorporation(
            original_code, refined_code, ranking, session, request
        )
        
        # Link to ranking
        ranking.verification_id = verification.id
        await self.redis.setex(f"ranking:{ranking.id}", 86400, to_json(ranking.dict()))

    async def _should_stop_refinement(self, ranking: ReviewRanking, session: CodeGenerationSession) -> bool:
        # Function documentation.
        
        logger.info(f"Refinement decision - Iteration: {session.refinement_iterations + 1}/{session.max_iterations}, "
                   f"Critic scores: C1={ranking.critic1_score:.2f}, C2={ranking.critic2_score:.2f}")
        
        # Stop if we're at max iterations
        if session.refinement_iterations >= session.max_iterations - 1:
            logger.info(f"STOP: Reached max iterations ({session.refinement_iterations + 1}/{session.max_iterations})")
            return True
        
        # Stop if ranking failed (error state)
        if "Error during ranking" in ranking.ranking_explanation:
            logger.info(f"STOP: Ranking failed - {ranking.ranking_explanation}")
            return True
        
        # NEW: Check verification results if available
        if ranking.verification_id:
            try:
                verification_data = await self.redis.get(f"verification:{ranking.verification_id}")
                if verification_data:
                    from models import VerificationResult
                    verification = VerificationResult(**from_json(verification_data))
                    
                    # Stop if incorporation score is low (feedback wasn't actually addressed)
                    if verification.incorporation_score < 0.4:
                        logger.info(f"STOP: Low incorporation score ({verification.incorporation_score:.2f}) - "
                                   f"feedback not being properly addressed")
                        return True
                    
                    # Stop if no objective improvements
                    if verification.objective_improvements.get('assessment') == 'no_improvement':
                        logger.info(f"STOP: No objective improvements detected")
                        return True
                    
                    # Stop if high incorporation (>0.8) but low critic scores (<0.4)
                    # This means we're incorporating everything but critics still finding issues = diminishing returns
                    if verification.incorporation_score > 0.8 and ranking.critic1_score < 0.4 and ranking.critic2_score < 0.4:
                        logger.info(f"STOP: High incorporation but low critic scores - diminishing returns")
                        return True
                        
            except Exception as e:
                logger.warning(f"Could not check verification: {e}")
        
        # Stop if both critics gave low scores (poor feedback quality - nothing useful to incorporate)
        if ranking.critic1_score < 0.3 and ranking.critic2_score < 0.3:
            logger.info(f"STOP: Both critics gave low scores - poor feedback quality")
            return True
        
        # Continue refinement if critics provided valuable feedback (high scores)
        logger.info(f"CONTINUE: Critics provided valuable feedback worth incorporating")
        return False

    async def get_generation_result(self, session_id: str) -> Optional[GenerationResult]:
        # Function documentation.
        try:
            # Get session
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return None
            
            session = CodeGenerationSession(**from_json(session_data))
            
            # Get request
            request_data = await self.redis.get(f"request:{session.request_id}")
            if not request_data:
                return None
            
            request = CodeGenerationRequest(**from_json(request_data))
            
            # Get all generated codes for this session
            generated_codes = []
            
            # Scan Redis for all codes belonging to this session
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match="code:*", count=100)
                for key in keys:
                    code_data = await self.redis.get(key)
                    if code_data:
                        code = GeneratedCode(**from_json(code_data))
                        if code.session_id == session_id:
                            generated_codes.append(code)
                if cursor == 0:
                    break
            
            # Sort generated codes by version (iteration order)
            generated_codes.sort(key=lambda x: x.version)
            
            # Get all critic reviews
            critic_reviews = []
            if session.critic1_review_id:
                review_data = await self.redis.get(f"review:{session.critic1_review_id}")
                if review_data:
                    critic_reviews.append(CriticReview(**from_json(review_data)))
            
            if session.critic2_review_id:
                review_data = await self.redis.get(f"review:{session.critic2_review_id}")
                if review_data:
                    critic_reviews.append(CriticReview(**from_json(review_data)))
            
            # Get rankings
            rankings = []
            if session.ranking_id:
                ranking_data = await self.redis.get(f"ranking:{session.ranking_id}")
                if ranking_data:
                    rankings.append(ReviewRanking(**from_json(ranking_data)))
            
            # Get verifications
            from models import VerificationResult
            verifications = []
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match="verification:*", count=100)
                for key in keys:
                    verification_data = await self.redis.get(key)
                    if verification_data:
                        verification = VerificationResult(**from_json(verification_data))
                        if verification.session_id == session_id:
                            verifications.append(verification)
                if cursor == 0:
                    break
            
            # Get final code
            final_code = None
            if generated_codes:
                final_code = generated_codes[-1].generated_code  # Latest version
            
            return GenerationResult(
                session=session,
                request=request,
                generated_codes=generated_codes,
                critic_reviews=critic_reviews,
                rankings=rankings,
                verifications=verifications,
                final_code=final_code,
                generation_summary=self._create_summary(session, generated_codes, critic_reviews, verifications)
            )
            
        except Exception as e:
            logger.error(f"Error getting generation result: {str(e)}")
            return None

    def _create_summary(self, session: CodeGenerationSession, 
                       generated_codes: list, critic_reviews: list, verifications: list = None) -> str:
        # Function documentation.
        summary = f"Generation completed in {session.refinement_iterations + 1} iterations.\n"
        
        if generated_codes:
            summary += f"Final code version: {generated_codes[-1].version}\n"
        
        if critic_reviews:
            summary += f"Total critic reviews: {len(critic_reviews)}\n"
        
        if verifications:
            avg_incorporation = sum(v.incorporation_score for v in verifications) / len(verifications)
            summary += f"Average incorporation score: {avg_incorporation:.2f}\n"
            
            improvements = [v.objective_improvements.get('assessment', 'unknown') for v in verifications]
            significant_count = improvements.count('significant_improvement')
            moderate_count = improvements.count('moderate_improvement')
            summary += f"Improvements: {significant_count} significant, {moderate_count} moderate\n"
        
        summary += f"Status: {session.status.value}"
        
        return summary
