import os
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from models import ProgrammingLanguage, FeedbackType
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        self.openrouter_url = os.environ.get('OPENROUTER_URL', 'https://openrouter.ai/api/v1')
        
        # Model mappings for OpenRouter
        self.models = {
            'generator': os.environ.get('MODEL_GENERATOR', 'google/gemini-2.0-flash'),
            'critic1': os.environ.get('MODEL_CRITIC1', 'openai/gpt-4o'),
            'critic2': os.environ.get('MODEL_CRITIC2', 'deepseek/deepseek-r1')
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 1.0  # 1 second between requests to be safe

    def _get_system_prompt(self, role: str, language: ProgrammingLanguage) -> str:
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

    async def _wait_for_rate_limit(self):
        """Simple rate limiting to avoid overwhelming the API"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_interval:
            wait_time = self.min_interval - time_since_last_request
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds before request")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

    async def _make_openrouter_request(self, messages: List[Dict], model: str, temperature: float = 0.3) -> str:
        """Make a request to OpenRouter API"""
        if not self.openrouter_key:
            raise Exception("OpenRouter API key not configured")
        
        await self._wait_for_rate_limit()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://mcrag.dev",  # Optional: for analytics
            "X-Title": "MCRAG Code Review System"  # Optional: for analytics
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.openrouter_url}/chat/completions", 
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API request failed with status {response.status}: {error_text}")
                        raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error making OpenRouter request: {str(e)}")
            raise

    async def get_generator_response(self, prompt: str, language: str) -> Tuple[str, str, float]:
        start_time = time.time()
        
        try:
            system_prompt = self._get_system_prompt("generator", ProgrammingLanguage(language))
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response_text = await self._make_openrouter_request(messages, self.models['generator'])
            
            processing_time = time.time() - start_time
            
            # Parse response to extract code and explanation
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
        start_time = time.time()
        
        try:
            # Determine which model and role to use
            if model_name == "gpt-4o":
                role = "critic1"
                openrouter_model = self.models['critic1']
            else:  # deepseek-r1 or other
                role = "critic2"
                openrouter_model = self.models['critic2']
            
            system_prompt = self._get_system_prompt(role, ProgrammingLanguage(language))
            
            if role == "critic1":
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
            else:  # critic2
                review_prompt = f"""
Review this {language} code that was generated for the following request:

Original Request: {original_prompt}

Generated Code:
```{language}
{code}
```

Focus on performance optimization and advanced techniques. Provide:
1. Performance assessment
2. Optimization opportunities  
3. Advanced improvement suggestions
4. Severity rating (1-5) for the most critical issue
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": review_prompt}
            ]
            
            review_text = await self._make_openrouter_request(messages, openrouter_model, temperature=0.3)
            
            processing_time = time.time() - start_time
            
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
                    parsed_severity = int(severity_match.group(1))
                    # Ensure severity is within valid range (1-5)
                    severity = max(1, min(5, parsed_severity))
            
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
        start_time = time.time()
        
        try:
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
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ranking_prompt}
            ]
            
            response_text = await self._make_openrouter_request(messages, self.models['generator'])
            
            # Parse response
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
            # If ranking fails, return low scores to stop refinement (can't incorporate feedback properly)
            return f"Error during ranking: {str(e)}", 0.1, 0.1, "Unable to create incorporation plan - stopping refinement"

    async def check_llm_availability(self) -> Dict[str, bool]:
        """Check availability of models through OpenRouter"""
        results = {}
        
        if not self.openrouter_key:
            logger.warning("No OpenRouter API key provided")
            return {
                "generator": False,
                "critic1": False,
                "critic2": False
            }
        
        # Test each model through OpenRouter
        test_message = [{"role": "user", "content": "Hello"}]
        
        for role, model in self.models.items():
            try:
                await self._make_openrouter_request(test_message, model)
                results[role] = True
                logger.info(f"Model {model} ({role}) is available through OpenRouter")
            except Exception as e:
                logger.error(f"Model {model} ({role}) availability check failed: {str(e)}")
                results[role] = False
        
        return results
