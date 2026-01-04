"""Google Gemini LLM client."""

from typing import Optional, List, Dict
import aiohttp
from .base import BaseLLMClient, CompletionResult


class GeminiClient(BaseLLMClient):
    """Google Gemini API client."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-2.0-flash"
    
    def __init__(self, api_key: str, model: str = None, requests_per_minute: float = 30.0):
        super().__init__(api_key, requests_per_minute)
        self.model = model or self.DEFAULT_MODEL
    
    def get_provider_name(self) -> str:
        return "gemini"
    
    def get_model_name(self) -> str:
        return self.model
    
    async def _call_api(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Single-prompt completion (original mode)."""
        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max(max_tokens, 1000),
                "topP": 0.95,
                "topK": 40,
            },
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Defensive parsing
                candidates = data.get("candidates", [])
                if not candidates:
                    raise Exception(f"Gemini: No candidates")
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                
                if not parts:
                    finish_reason = candidates[0].get("finishReason", "UNKNOWN")
                    raise Exception(f"Gemini: No output. Reason: {finish_reason}")
                
                text = parts[0].get("text", "")
                
                usage = data.get("usageMetadata", {})
                
                return CompletionResult(
                    text=text,
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=usage.get("promptTokenCount"),
                    completion_tokens=usage.get("candidatesTokenCount"),
                )
    
    async def _call_api_messages(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str],
        max_tokens: int, 
        temperature: float
    ) -> CompletionResult:
        """Conversation-aware completion (longitudinal mode)."""
        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        
        # Convert messages to Gemini format
        # Gemini uses "user" and "model" roles with parts array
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max(max_tokens, 1000),
                "topP": 0.95,
                "topK": 40,
            },
        }
        
        # Gemini uses systemInstruction for system prompts
        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
                
                data = await response.json()
                
                # Defensive parsing
                candidates = data.get("candidates", [])
                if not candidates:
                    raise Exception(f"Gemini: No candidates")
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                
                if not parts:
                    finish_reason = candidates[0].get("finishReason", "UNKNOWN")
                    raise Exception(f"Gemini: No output. Reason: {finish_reason}")
                
                text = parts[0].get("text", "")
                
                usage = data.get("usageMetadata", {})
                
                return CompletionResult(
                    text=text,
                    provider=self.get_provider_name(),
                    model=self.model,
                    prompt_tokens=usage.get("promptTokenCount"),
                    completion_tokens=usage.get("candidatesTokenCount"),
                )