"""DeepSeek LLM client (OpenAI-compatible API)."""

from typing import Optional, List, Dict
import aiohttp
from .base import BaseLLMClient, CompletionResult


class DeepSeekClient(BaseLLMClient):
    """DeepSeek API client (OpenAI-compatible)."""
    
    BASE_URL = "https://api.deepseek.com/chat/completions"
    DEFAULT_MODEL = "deepseek-chat"
    
    def __init__(self, api_key: str, model: str = None, requests_per_minute: float = 60.0):
        super().__init__(api_key, requests_per_minute)
        self.model = model or self.DEFAULT_MODEL
    
    def get_provider_name(self) -> str:
        return "deepseek"
    
    def get_model_name(self) -> str:
        return self.model
    
    async def _call_api(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Single-prompt completion (original mode)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek API error {response.status}: {error_text}")
                
                data = await response.json()
                
                return CompletionResult(
                    text=data["choices"][0]["message"]["content"],
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=data.get("usage", {}).get("prompt_tokens"),
                    completion_tokens=data.get("usage", {}).get("completion_tokens"),
                )
    
    async def _call_api_messages(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str],
        max_tokens: int, 
        temperature: float
    ) -> CompletionResult:
        """Conversation-aware completion (longitudinal mode)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # DeepSeek uses OpenAI format - system message in array
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages.extend(messages)
        
        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek API error {response.status}: {error_text}")
                
                data = await response.json()
                
                return CompletionResult(
                    text=data["choices"][0]["message"]["content"],
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=data.get("usage", {}).get("prompt_tokens"),
                    completion_tokens=data.get("usage", {}).get("completion_tokens"),
                )