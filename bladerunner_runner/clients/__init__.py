"""LLM clients for Bladerunner."""

from .base import BaseLLMClient, CompletionResult, RateLimiter
from .claude import ClaudeClient
from .openai import OpenAIClient
from .deepseek import DeepSeekClient
from .gemini import GeminiClient
from .xai import XAIClient

__all__ = [
    'BaseLLMClient',
    'CompletionResult',
    'RateLimiter',
    'ClaudeClient',
    'OpenAIClient',
    'DeepSeekClient',
    'GeminiClient',
    'xai',
    'create_client',
    'list_providers',
]

_PROVIDERS = {
    'claude': ClaudeClient,
    'openai': OpenAIClient,
    'deepseek': DeepSeekClient,
    'gemini': GeminiClient,
    'xai': xai,
}


def create_client(provider: str, api_key: str, **kwargs) -> BaseLLMClient:
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(_PROVIDERS.keys())}")
    return _PROVIDERS[provider](api_key, **kwargs)


def list_providers() -> list:
    return list(_PROVIDERS.keys())