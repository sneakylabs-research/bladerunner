"""
Base class for LLM clients.

Handles rate limiting and common interface.
All clients use asyncio for concurrency.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict
import time


@dataclass
class CompletionResult:
    """Result from an LLM completion."""
    text: str
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: Optional[float] = None


class RateLimiter:
    """
    Async rate limiter using token bucket algorithm.
    
    Ensures minimum delay between requests to respect API limits.
    """
    
    def __init__(self, requests_per_minute: float):
        self.min_interval = 60.0 / requests_per_minute
        self.last_request: float = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until we can make another request."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_request
            
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)
            
            self.last_request = time.monotonic()


class BaseLLMClient(ABC):
    """Abstract base for all LLM clients."""
    
    def __init__(self, api_key: str, requests_per_minute: float = 60.0):
        self.api_key = api_key
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name. e.g., 'claude'"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return model name. e.g., 'claude-sonnet-4-5-20250929'"""
        pass
    
    @abstractmethod
    async def _call_api(self, prompt: str, max_tokens: int, temperature: float) -> CompletionResult:
        """Make the actual API call. Implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _call_api_messages(
        self, 
        messages: List[Dict[str, str]], 
        system: Optional[str],
        max_tokens: int, 
        temperature: float
    ) -> CompletionResult:
        """Make API call with conversation history. Implemented by subclasses."""
        pass
    
    async def complete(
        self, 
        prompt: str, 
        max_tokens: int = 100, 
        temperature: float = 0.3
    ) -> CompletionResult:
        """
        Get a completion from the LLM.
        
        Handles rate limiting automatically.
        """
        await self.rate_limiter.acquire()
        
        start_time = time.monotonic()
        result = await self._call_api(prompt, max_tokens, temperature)
        latency = (time.monotonic() - start_time) * 1000
        
        result.latency_ms = latency
        return result
    
    async def complete_with_messages(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 100,
        temperature: float = 0.3
    ) -> CompletionResult:
        """
        Get a completion with full conversation history.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system: Optional system prompt
            max_tokens: Max response tokens
            temperature: Sampling temperature
        """
        await self.rate_limiter.acquire()
        
        start_time = time.monotonic()
        result = await self._call_api_messages(messages, system, max_tokens, temperature)
        latency = (time.monotonic() - start_time) * 1000
        
        result.latency_ms = latency
        return result
    
    async def get_single_digit(self, prompt: str) -> int:
        """
        Get a single digit (1-5) response.
        
        Parses the response to extract a rating.
        Returns 3 (neutral) if parsing fails.
        """
        result = await self.complete(prompt, max_tokens=10, temperature=0.3)
        return self._parse_digit(result.text)
    
    def _parse_digit(self, text: str) -> int:
        """Extract a 1-5 rating from text."""
        cleaned = text.strip().replace(".", "").replace(",", "")
        
        # Try direct parse
        try:
            score = int(cleaned)
            if 1 <= score <= 5:
                return score
        except ValueError:
            pass
        
        # Scan for first valid digit
        for char in cleaned:
            if char.isdigit():
                digit = int(char)
                if 1 <= digit <= 5:
                    return digit
        
        # Default to neutral
        return 3
