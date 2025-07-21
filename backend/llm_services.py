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
        base_context = f"You are an expert {language.value} developer working on a code review system."
        
        if role == "coder":
            return f"""{base_context}

Your role is CODER. You will receive code from users and provide thoughtful improvements and suggestions.

Guidelines:
1. Analyze the code for best practices, efficiency, readability, and maintainability
2. Suggest specific improvements with clear explanations
3. Provide improved code snippets when helpful
4. Focus on practical, actionable feedback
5. Consider security, performance, and scalability aspects
6. Be constructive and educational

Response format:
- Start with a brief summary of the code's purpose
- List 3-5 key improvement areas
- Provide specific code suggestions
- End with overall assessment and priority recommendations

Keep your response focused and actionable."""

        elif role == "critic1":
            return f"""{base_context}

Your role is CRITIC 1. You will review the CODER's suggestions and provide critical feedback.

Guidelines:
1. Evaluate the coder's suggestions for accuracy and completeness
2. Identify any missed issues or incorrect recommendations
3. Assess whether the suggested improvements are practical and beneficial
4. Point out any potential problems with the coder's approach
5. Suggest alternative solutions if needed
6. Focus on technical accuracy and best practices

Response format:
- Evaluate each major suggestion from the coder
- Highlight what was done well
- Point out areas that need improvement or are incorrect
- Suggest additional considerations
- Provide an overall assessment of the coder's review quality

Be thorough but constructive in your criticism."""

        else:  # critic2
            return f"""{base_context}

Your role is CRITIC 2. You will review both the original code and the CODER's suggestions from a different perspective.

Guidelines:
1. Focus on maintainability, team collaboration, and long-term codebase health
2. Consider the business context and practical implementation challenges
3. Evaluate code documentation and clarity aspects
4. Assess testing considerations and error handling
5. Review the coder's suggestions for real-world applicability
6. Consider alternative approaches or architectural patterns

Response format:
- Assess the code from a maintainability and team perspective
- Evaluate the practical impact of suggested changes
- Consider deployment, testing, and operational aspects
- Suggest additional improvements not covered by the coder
- Provide perspective on trade-offs and priorities

Focus on the broader implications and practical considerations."""

    async def get_coder_feedback(self, code: str, language: ProgrammingLanguage, description: Optional[str] = None) -> Tuple[str, Optional[str], float]:
        """Get feedback from the coder LLM (Gemini)."""
        start_time = time.time()
        
        try:
            session_id = f"coder_{int(time.time())}"
            system_prompt = self._get_system_prompt("coder", language)
            
            chat = LlmChat(
                api_key=self.gemini_key,
                session_id=session_id,
                system_message=system_prompt
            ).with_model("gemini", "gemini-2.0-flash")
            
            user_prompt = f"""Please review the following {language.value} code and provide improvement suggestions:

{f'**Description:** {description}' if description else ''}

**Code:**
```{language.value}
{code}
```

Please provide your analysis and suggestions following the guidelines in your system prompt."""

            user_message = UserMessage(text=user_prompt)
            response = await chat.send_message(user_message)
            
            processing_time = time.time() - start_time
            
            # Extract suggested code if present (basic pattern matching)
            suggested_code = None
            if "```" in response:
                code_blocks = response.split("```")
                for i, block in enumerate(code_blocks):
                    if i % 2 == 1 and (language.value in code_blocks[i-1].lower() if i > 0 else True):
                        # Remove language identifier from start of block
                        lines = block.strip().split('\n')
                        if lines and lines[0].strip().lower() in [language.value, language.value.lower()]:
                            lines = lines[1:]
                        suggested_code = '\n'.join(lines).strip()
                        break
            
            return response, suggested_code, processing_time
            
        except Exception as e:
            logger.error(f"Error getting coder feedback: {str(e)}")
            raise

    async def get_critic_feedback(self, original_code: str, coder_feedback: str, language: ProgrammingLanguage, critic_number: int, suggested_code: Optional[str] = None) -> Tuple[str, float]:
        """Get feedback from critic LLMs (OpenAI or DeepSeek)."""
        start_time = time.time()
        
        try:
            session_id = f"critic{critic_number}_{int(time.time())}"
            role = f"critic{critic_number}"
            system_prompt = self._get_system_prompt(role, language)
            
            if critic_number == 1:
                # Use OpenAI for Critic 1
                chat = LlmChat(
                    api_key=self.openai_key,
                    session_id=session_id,
                    system_message=system_prompt
                ).with_model("openai", "gpt-4o")
            else:
                # Use DeepSeek for Critic 2
                # Try with DeepSeek v3, fall back to available model if needed
                try:
                    chat = LlmChat(
                        api_key=self.deepseek_key,
                        session_id=session_id,
                        system_message=system_prompt
                    ).with_model("deepseek", "deepseek-v3")  # Use full model name
                except:
                    # If deepseek-v3 doesn't work, try with OpenAI as fallback
                    logger.warning("DeepSeek deepseek-v3 not available, falling back to OpenAI")
                    chat = LlmChat(
                        api_key=self.openai_key,
                        session_id=session_id,
                        system_message=system_prompt
                    ).with_model("openai", "gpt-4o")
            
            user_prompt = f"""Please review the following code review scenario:

**Original {language.value} Code:**
```{language.value}
{original_code}
```

**Coder's Feedback:**
{coder_feedback}

{f'''**Coder's Suggested Code:**
```{language.value}
{suggested_code}
```''' if suggested_code else ''}

Please provide your critical analysis following the guidelines in your system prompt."""

            user_message = UserMessage(text=user_prompt)
            response = await chat.send_message(user_message)
            
            processing_time = time.time() - start_time
            return response, processing_time
            
        except Exception as e:
            logger.error(f"Error getting critic {critic_number} feedback: {str(e)}")
            raise

    def analyze_conflicts(self, coder_feedback: str, critic1_feedback: str, critic2_feedback: str) -> Dict:
        """Analyze conflicts between different LLM feedbacks and suggest resolution."""
        # Simple conflict detection based on keywords and sentiment
        # In a production system, this would be more sophisticated
        
        conflicts = []
        
        # Keywords that might indicate disagreement
        disagreement_keywords = ["wrong", "incorrect", "disagree", "however", "but", "actually", "instead"]
        agreement_keywords = ["agree", "correct", "good point", "excellent", "right"]
        
        # Check if critics disagree with coder
        critic1_disagrees = any(keyword in critic1_feedback.lower() for keyword in disagreement_keywords)
        critic2_disagrees = any(keyword in critic2_feedback.lower() for keyword in disagreement_keywords)
        
        if critic1_disagrees:
            conflicts.append("Critic 1 disagrees with some of the coder's suggestions")
            
        if critic2_disagrees:
            conflicts.append("Critic 2 disagrees with some of the coder's suggestions")
        
        # Simple resolution strategy
        resolution_strategy = "consensus_based"
        if len(conflicts) == 0:
            final_decision = "All LLMs are in general agreement. Follow the coder's suggestions with minor adjustments from critics."
            confidence = 0.9
        elif len(conflicts) == 1:
            final_decision = "Mixed feedback received. Prioritize the coder's suggestions but carefully consider the critical feedback."
            confidence = 0.7
        else:
            final_decision = "Significant disagreement detected. Human review recommended before implementing changes."
            confidence = 0.5
        
        return {
            "conflicting_points": conflicts,
            "resolution_strategy": resolution_strategy,
            "final_decision": final_decision,
            "confidence": confidence
        }