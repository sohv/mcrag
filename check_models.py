#!/usr/bin/env python3
"""
Check available models on OpenRouter
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

async def check_available_models():
    load_dotenv()
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("No OpenRouter API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://openrouter.ai/api/v1/models", headers=headers) as response:
                if response.status == 200:
                    models = await response.json()
                    
                    print("Available models on OpenRouter:")
                    print("=" * 50)
                    
                    # Filter for the models we're interested in
                    relevant_models = []
                    for model in models.get('data', []):
                        model_id = model.get('id', '')
                        name = model.get('name', '')
                        
                        if any(keyword in model_id.lower() for keyword in ['gemini', 'gpt-4o', 'deepseek']):
                            relevant_models.append((model_id, name))
                    
                    print("\nRelevant models for MCRAG:")
                    for model_id, name in relevant_models:
                        print(f"  {model_id} - {name}")
                    
                    print(f"\nTotal models available: {len(models.get('data', []))}")
                    print(f"Relevant models found: {len(relevant_models)}")
                    
                else:
                    error_text = await response.text()
                    print(f"Error fetching models: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_available_models())