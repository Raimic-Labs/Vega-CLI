"""
providers/__init__.py — Provider factory & registry

Usage:
    from providers import get_provider

    provider = get_provider(
        provider_name = "nvidia",
        api_key       = "nvapi-...",
        model         = "moonshotai/kimi-k2",
    )
    for chunk in provider.stream_with_retry(messages):
        print(chunk.text, end="", flush=True)
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from providers.base import (   # re-export for convenience
    BaseProvider,
    CompletionResponse,
    Message,
    StreamChunk,
    VegaAuthError,
    VegaModelError,
    VegaProviderError,
    VegaRateLimitError,
    VegaTimeoutError,
)

if TYPE_CHECKING:
    pass


# ─────────────────────────────────────────────
#  Lazy imports (avoid paying import cost for
#  unused providers at startup)
# ─────────────────────────────────────────────

def _load_nvidia():
    from providers.nvidia   import NvidiaProvider
    return NvidiaProvider

def _load_google():
    from providers.google   import GoogleProvider
    return GoogleProvider

def _load_groq():
    from providers.groq     import GroqProvider
    return GroqProvider

def _load_deepseek():
    from providers.deepseek import DeepSeekProvider
    return DeepSeekProvider


_PROVIDER_LOADERS = {
    "nvidia":   _load_nvidia,
    "google":   _load_google,
    "groq":     _load_groq,
    "deepseek": _load_deepseek,
}

SUPPORTED_PROVIDERS: list[str] = list(_PROVIDER_LOADERS.keys())


# ─────────────────────────────────────────────
#  Factory
# ─────────────────────────────────────────────

def get_provider(
    provider_name: str,
    api_key:       str,
    model:         str,
    temperature:   float = 0.7,
    max_tokens:    int   = 4096,
    timeout:       float = 120.0,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> BaseProvider:
    """
    Instantiate and return the correct provider for *provider_name*.

    Args:
        provider_name: One of "nvidia", "google", "groq", "deepseek".
        api_key:       Provider API key.
        model:         Model ID (must be valid for the provider).
        temperature:   Sampling temperature (0.0 – 2.0).
        max_tokens:    Maximum output tokens.
        timeout:       HTTP timeout in seconds.
        system_prompt: Optional system-level instruction.
        **kwargs:      Extra kwargs passed to the provider constructor
                       (e.g. strip_thinking=True for DeepSeek-R1).

    Returns:
        An initialised BaseProvider subclass instance.

    Raises:
        ValueError:         If provider_name is not recognised.
        VegaAuthError:      If the API key is empty / invalid format.
        ImportError:        If the required SDK is not installed.
    """
    key = provider_name.lower().strip()
    loader = _PROVIDER_LOADERS.get(key)
    if loader is None:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Supported: {SUPPORTED_PROVIDERS}"
        )

    ProviderClass = loader()
    return ProviderClass(
        api_key       = api_key,
        model         = model,
        temperature   = temperature,
        max_tokens    = max_tokens,
        timeout       = timeout,
        system_prompt = system_prompt,
        **kwargs,
    )


def list_providers() -> list[str]:
    """Return all supported provider names."""
    return SUPPORTED_PROVIDERS.copy()


__all__ = [
    # Factory
    "get_provider",
    "list_providers",
    "SUPPORTED_PROVIDERS",
    # Base types (re-exported)
    "BaseProvider",
    "Message",
    "StreamChunk",
    "CompletionResponse",
    # Exceptions (re-exported)
    "VegaProviderError",
    "VegaAuthError",
    "VegaRateLimitError",
    "VegaTimeoutError",
    "VegaModelError",
]
