import os
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
import openai
import google.generativeai as genai
from models import ProgrammingLanguage, FeedbackType
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.gemini_key = os.environ.get('GEMINI_API_KEY')
        self.deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        # Rate limiting for Gemini (10 requests per minute on free tier)
        self.gemini_last_request_time = 0
        self.gemini_min_interval = 6  # 6 seconds between requests (10 per minute)
        # Configure APIs
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)

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

    async def _wait_for_gemini_rate_limit(self):
        current_time = time.time()
        time_since_last_request = current_time - self.gemini_last_request_time
        
        if time_since_last_request < self.gemini_min_interval:
            wait_time = self.gemini_min_interval - time_since_last_request
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds before Gemini request")
            await asyncio.sleep(wait_time)
        
        self.gemini_last_request_time = time.time()

    async def _handle_rate_limit_error(self, error_str: str) -> bool:
        if "429" in error_str and "quota" in error_str.lower():
            # Extract retry delay if provided
            import re
            retry_match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)', error_str)
            if retry_match:
                retry_seconds = int(retry_match.group(1))
                logger.info(f"Rate limit hit, waiting {retry_seconds} seconds as suggested by API")
                await asyncio.sleep(retry_seconds)
                return True
            else:
                # Default backoff
                logger.info("Rate limit hit, waiting 60 seconds (default backoff)")
                await asyncio.sleep(60)
                return True
        return False

    async def get_generator_response(self, prompt: str, language: str) -> Tuple[str, str, float]:
        start_time = time.time()
        
        try:
            # Rate limiting for Gemini
            await self._wait_for_gemini_rate_limit()
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            system_prompt = self._get_system_prompt("generator", ProgrammingLanguage(language))
            
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, model.generate_content, full_prompt
            )
            
            processing_time = time.time() - start_time
            
            # Parse response to extract code and explanation
            response_text = response.text
            
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
            error_str = str(e)
            logger.error(f"Error getting generator response: {error_str}")
            
            # Try to handle rate limit with retry
            if await self._handle_rate_limit_error(error_str):
                try:
                    # Retry once after waiting
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, model.generate_content, full_prompt
                    )
                    
                    processing_time = time.time() - start_time
                    response_text = response.text
                    
                    # Parse response again
                    if "```" in response_text:
                        parts = response_text.split("```")
                        if len(parts) >= 3:
                            code = parts[1]
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
                except Exception as retry_e:
                    logger.error(f"Retry also failed: {str(retry_e)}")
            
            processing_time = time.time() - start_time
            return f"# Error generating code: {str(e)}", "Generation failed", processing_time

    async def get_critic_review(self, code: str, original_prompt: str, language: str, model_name: str) -> Tuple[str, List[str], int, float, float]:
        start_time = time.time()
        
        try:
            if model_name == "gpt-4o":
                client = openai.AsyncOpenAI(api_key=self.openai_key)
                role = "critic1"
                
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
                
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": review_prompt}
                    ],
                    temperature=0.3
                )
                
                review_text = response.choices[0].message.content
                
            else:  # DeepSeek R1 API call
                if model_name == "deepseek-r1" and self.deepseek_key:
                    role = "critic2"
                    system_prompt = self._get_system_prompt(role, ProgrammingLanguage(language))
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
                    # Call DeepSeek R1 API
                    api_url = "https://api.deepseek.com/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.deepseek_key}",
                    }
                    data = {
                        "model": "deepseek-reasoner",  # Use 'deepseek-reasoner' for R1 model
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": review_prompt}
                        ],
                        "stream": False
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(api_url, headers=headers, json=data) as response:
                            if response.status == 200:
                                result = await response.json()
                                review_text = result['choices'][0]['message']['content']
                            else:
                                logger.error(f"DeepSeek API request failed with status {response.status}")
                                # Fallback to Gemini if DeepSeek fails
                                await self._wait_for_gemini_rate_limit()
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                fallback_prompt = f"""
{system_prompt}

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
                                response = await asyncio.get_event_loop().run_in_executor(
                                    None, model.generate_content, fallback_prompt
                                )
                                review_text = response.text
                else:
                    # Fallback to Gemini if no DeepSeek key or different model
                    role = "critic2"
                    system_prompt = self._get_system_prompt(role, ProgrammingLanguage(language))
                    await self._wait_for_gemini_rate_limit()
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    review_prompt = f"""
{system_prompt}

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
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, model.generate_content, review_prompt
                    )
                    review_text = response.text
            
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
            await self._wait_for_gemini_rate_limit()
            model = genai.GenerativeModel('gemini-2.5-flash')
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
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, model.generate_content, ranking_prompt
            )
            
            # Parse response
            response_text = response.text
            
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
            # If ranking fails, return low scores to stop refinement (can't incorporate feedback properly)
            return f"Error during ranking: {str(e)}", 0.1, 0.1, "Unable to create incorporation plan - stopping refinement"

    async def check_llm_availability(self) -> Dict[str, bool]:
        results = {}
        
        # Test Gemini (Generator)
        try:
            await self._wait_for_gemini_rate_limit()
            model = genai.GenerativeModel('gemini-2.5-flash')
            await asyncio.get_event_loop().run_in_executor(
                None, model.generate_content, "Hello"
            )
            results["gemini-2.5-flash"] = True
        except Exception as e:
            logger.error(f"Gemini availability check failed: {str(e)}")
            results["gemini-2.5-flash"] = False
        
        # Test OpenAI (Critic 1)
        try:
            client = openai.AsyncOpenAI(api_key=self.openai_key)
            await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            results["gpt-4o"] = True
        except Exception as e:
            logger.error(f"OpenAI availability check failed: {str(e)}")
            results["gpt-4o"] = False
        
        # Test DeepSeek R1 (Critic 2)
        try:
            if self.deepseek_key:
                api_url = "https://api.deepseek.com/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.deepseek_key}",
                }
                
                data = {
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello"}
                    ],
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, headers=headers, json=data) as response:
                        if response.status == 200:
                            results["deepseek-r1"] = True
                        else:
                            logger.error(f"DeepSeek API test failed with status {response.status}")
                            results["deepseek-r1"] = False
            else:
                logger.warning("No DeepSeek API key provided")
                results["deepseek-r1"] = False
        except Exception as e:
            logger.error(f"DeepSeek availability check failed: {str(e)}")
            # Fallback to Gemini availability if DeepSeek fails
            results["deepseek-r1"] = results["gemini-2.5-flash"]
        
        return results
