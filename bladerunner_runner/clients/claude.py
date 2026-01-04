"""Claude (Anthropic) LLM client."""

from typing import Optional, List, Dict
import aiohttp
from .base import BaseLLMClient, CompletionResult


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client."""
    
    BASE_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    
    def __init__(self, api_key: str, model: str = None, requests_per_minute: float = 60.0):
        super().__init__(api_key, requests_per_minute)
        self.model = model or self.DEFAULT_MODEL
    
    def get_provider_name(self) -> str:
        return "claude"
    
    def get_model_name(self) -> str:
        return self.model
    
    async def _call_api(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Single-prompt completion (original mode)."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
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
                    raise Exception(f"Claude API error {response.status}: {error_text}")
                
                data = await response.json()
                
                return CompletionResult(
                    text=data["content"][0]["text"],
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=data.get("usage", {}).get("input_tokens"),
                    completion_tokens=data.get("usage", {}).get("output_tokens"),
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
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system:
            payload["system"] = system
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Claude API error {response.status}: {error_text}")
                
                data = await response.json()
                
                return CompletionResult(
                    text=data["content"][0]["text"],
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=data.get("usage", {}).get("input_tokens"),
                    completion_tokens=data.get("usage", {}).get("output_tokens"),
                )
