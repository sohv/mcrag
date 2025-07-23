import os
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import ProgrammingLanguage, FeedbackType
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.gemini_key = os.environ.get('GEMINI_API_KEY')
        self.deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        
    def _get_system_prompt(self, role: str, language: ProgrammingLanguage) -> str:
        """Generate system prompts based on role and programming language."""
        base_context = f"You are an expert {language.value} developer working on a code generation and review system."
        
        if role == "generator":
            return f"""{base_context}

Your role is GENERATOR. You will:
1. Generate code based on user prompts
2. Rank critic feedback and incorporate improvements
3. Refine code iteratively based on critic reviews

Guidelines for Generation:
- Write clean, well-structured, documented code
- Follow language best practices and conventions
- Include helpful comments explaining complex logic
- Consider edge cases and error handling
- Make code readable and maintainable

Guidelines for Ranking Reviews:
- Evaluate each critic's feedback objectively
- Assign scores (0-1) based on feedback quality and relevance
- Higher scores for more valuable, accurate, actionable feedback
- Create incorporation plans that address the most important issues

Response format varies by task - follow specific instructions in each prompt."""

        elif role == "critic1":
            return f"""{base_context}

Your role is CRITIC 1 (GPT-4o). You will review generated code and provide detailed feedback.

Guidelines:
1. Analyze code for correctness, efficiency, and best practices
2. Check for potential bugs, security issues, and edge cases
3. Evaluate code structure, readability, and maintainability
4. Suggest specific improvements with clear rationale
5. Rate severity of issues (1=minor to 5=critical)
6. Be thorough but practical

Response format:
- Overall assessment
- List of specific issues found
- Concrete suggestions for improvement
- Severity ratings for each issue"""

        elif role == "critic2":
            return f"""{base_context}

Your role is CRITIC 2 (DeepSeek-R1). You will review generated code with a focus on optimization and advanced techniques.

Guidelines:
1. Focus on performance optimization and algorithmic efficiency
2. Identify opportunities for better design patterns
3. Suggest advanced language features that could improve the code
4. Check for scalability and robustness
5. Evaluate error handling and fault tolerance
6. Consider maintainability and extensibility

Response format:
- Performance and design assessment
- Optimization opportunities
- Advanced improvement suggestions
- Scalability considerations"""

        return ""

    async def get_generator_response(self, prompt: str, language: str) -> Tuple[str, str, float]:
        """Get response from the generator (Gemini 2.0 Flash)."""
        start_time = time.time()
        
        try:
            chat = LlmChat(
                provider="gemini",
                model="gemini-2.0-flash-exp",
                api_key=self.gemini_key
            )
            
            system_prompt = self._get_system_prompt("generator", ProgrammingLanguage(language))
            
            response = await chat.send_message_async(
                UserMessage(prompt),
                system_prompt=system_prompt,
                temperature=0.7
            )
            
            processing_time = time.time() - start_time
            
            # Parse response to extract code and explanation
            response_text = response.content
            
            # Try to extract code and explanation
            if "```" in response_text:
                parts = response_text.split("```")
                if len(parts) >= 3:
                    code = parts[1]
                    # Remove language identifier if present
                    if code.startswith(language):
                        code = code[len(language):].strip()
                    explanation = parts[0] + (parts[2] if len(parts) > 2 else "")
                else:
                    code = response_text
                    explanation = "Code generated"
            else:
                code = response_text
                explanation = "Code generated"
            
            return code.strip(), explanation.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Error getting generator response: {str(e)}")
            processing_time = time.time() - start_time
            return f"# Error generating code: {str(e)}", "Generation failed", processing_time

    async def get_critic_review(self, code: str, original_prompt: str, language: str, model_name: str) -> Tuple[str, List[str], int, float, float]:
        """Get review from a critic."""
        start_time = time.time()
        
        try:
            if model_name == "gpt-4o":
                chat = LlmChat(
                    provider="openai",
                    model="gpt-4o",
                    api_key=self.openai_key
                )
                role = "critic1"
            else:  # deepseek-r1
                chat = LlmChat(
                    provider="deepseek",
                    model="deepseek-r1",
                    api_key=self.deepseek_key
                )
                role = "critic2"
            
            system_prompt = self._get_system_prompt(role, ProgrammingLanguage(language))
            
            review_prompt = f"""
Review this {language} code that was generated for the following request:

Original Request: {original_prompt}

Generated Code:
```{language}
{code}
```

Please provide a thorough review following your role guidelines.
Include:
1. Overall assessment
2. Specific issues (if any)
3. Suggestions for improvement
4. Severity rating (1-5) for the most critical issue found
"""
            
            response = await chat.send_message_async(
                UserMessage(review_prompt),
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            processing_time = time.time() - start_time
            
            # Parse response
            review_text = response.content
            
            # Extract suggestions (look for bullet points or numbered lists)
            suggestions = []
            lines = review_text.split('\n')
            for line in lines:
                line = line.strip()
                if (line.startswith('- ') or line.startswith('* ') or 
                    (len(line) > 2 and line[0].isdigit() and line[1:3] in ['. ', ') '])):
                    suggestions.append(line[2:] if line.startswith(('- ', '* ')) else line[3:])
            
            # Extract severity rating (default to 3 if not found)
            severity = 3
            if "severity" in review_text.lower():
                import re
                severity_match = re.search(r'severity[^\d]*(\d)', review_text.lower())
                if severity_match:
                    severity = int(severity_match.group(1))
            
            # Confidence score based on response length and specificity
            confidence = min(0.9, len(review_text) / 1000 + 0.3)
            
            return review_text, suggestions[:5], severity, confidence, processing_time
            
        except Exception as e:
            logger.error(f"Error getting critic review from {model_name}: {str(e)}")
            processing_time = time.time() - start_time
            return f"Error during review: {str(e)}", [], 5, 0.1, processing_time

    async def rank_reviews_and_plan(self, code: str, original_prompt: str, 
                                  critic1_review: str, critic1_suggestions: List[str],
                                  critic2_review: str, critic2_suggestions: List[str],
                                  language: str) -> Tuple[str, float, float, str]:
        """Generator ranks critic reviews and creates incorporation plan."""
        start_time = time.time()
        
        try:
            chat = LlmChat(
                provider="gemini",
                model="gemini-2.0-flash-exp",
                api_key=self.gemini_key
            )
            
            system_prompt = self._get_system_prompt("generator", ProgrammingLanguage(language))
            
            ranking_prompt = f"""
You generated this {language} code for the request: {original_prompt}

Your Generated Code:
```{language}
{code}
```

Now review the feedback from two critics and rank their reviews:

CRITIC 1 REVIEW:
{critic1_review}

Critic 1 Suggestions:
{chr(10).join([f"- {s}" for s in critic1_suggestions])}

CRITIC 2 REVIEW:
{critic2_review}

Critic 2 Suggestions:
{chr(10).join([f"- {s}" for s in critic2_suggestions])}

Tasks:
1. Evaluate each critic's feedback quality and relevance
2. Assign scores (0.0-1.0) to each critic based on value of their feedback
3. Create a plan for incorporating the most valuable feedback

Respond in this format:
RANKING EXPLANATION:
[Your analysis of both reviews]

CRITIC 1 SCORE: [0.0-1.0]
CRITIC 2 SCORE: [0.0-1.0]

INCORPORATION PLAN:
[Detailed plan for how to improve the code based on the most valuable feedback]
"""
            
            response = await chat.send_message_async(
                UserMessage(ranking_prompt),
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            # Parse response
            response_text = response.content
            
            # Extract scores and plan
            import re
            
            critic1_score_match = re.search(r'CRITIC 1 SCORE:\s*([0-9.]+)', response_text)
            critic2_score_match = re.search(r'CRITIC 2 SCORE:\s*([0-9.]+)', response_text)
            
            critic1_score = float(critic1_score_match.group(1)) if critic1_score_match else 0.5
            critic2_score = float(critic2_score_match.group(1)) if critic2_score_match else 0.5
            
            # Ensure scores are in valid range
            critic1_score = max(0.0, min(1.0, critic1_score))
            critic2_score = max(0.0, min(1.0, critic2_score))
            
            # Extract explanation and plan
            parts = response_text.split('INCORPORATION PLAN:')
            explanation = parts[0].replace('RANKING EXPLANATION:', '').strip()
            plan = parts[1].strip() if len(parts) > 1 else "No specific plan provided"
            
            return explanation, critic1_score, critic2_score, plan
            
        except Exception as e:
            logger.error(f"Error ranking reviews: {str(e)}")
            return f"Error during ranking: {str(e)}", 0.5, 0.5, "Unable to create incorporation plan"

    async def check_llm_availability(self) -> Dict[str, bool]:
        """Check availability of all LLM services."""
        results = {}
        
        # Test Gemini (Generator)
        try:
            chat = LlmChat(provider="gemini", model="gemini-2.0-flash-exp", api_key=self.gemini_key)
            await chat.send_message_async(UserMessage("Hello"), temperature=0.1)
            results["gemini-2.0-flash-exp"] = True
        except Exception as e:
            logger.error(f"Gemini availability check failed: {str(e)}")
            results["gemini-2.0-flash-exp"] = False
        
        # Test OpenAI (Critic 1)
        try:
            chat = LlmChat(provider="openai", model="gpt-4o", api_key=self.openai_key)
            await chat.send_message_async(UserMessage("Hello"), temperature=0.1)
            results["gpt-4o"] = True
        except Exception as e:
            logger.error(f"OpenAI availability check failed: {str(e)}")
            results["gpt-4o"] = False
        
        # Test DeepSeek (Critic 2)
        try:
            chat = LlmChat(provider="deepseek", model="deepseek-r1", api_key=self.deepseek_key)
            await chat.send_message_async(UserMessage("Hello"), temperature=0.1)
            results["deepseek-r1"] = True
        except Exception as e:
            logger.error(f"DeepSeek availability check failed: {str(e)}")
            results["deepseek-r1"] = False
        
        return results
