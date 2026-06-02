"""
providers/groq.py — Groq Provider
Uses the official groq Python SDK (pip install groq).
Groq LPU delivers some of the fastest inference available.

Supported models include:
  - meta-llama/llama-4-scout-17b-16e-instruct  (llama-4-scout)
  - llama-3.3-70b-versatile
  - llama-3.1-8b-instant
  - mixtral-8x7b-32768
  - deepseek-r1-distill-llama-70b
  - qwen-qwq-32b
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

try:
    from groq import Groq
    from groq import APITimeoutError, APIConnectionError, APIStatusError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "groq package is required for the Groq provider.\n"
        "Install it with: pip install groq"
    ) from exc

from providers.base import (
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

# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────

DEFAULT_MODEL       = "llama-3.3-70b-versatile"
LLAMA4_SCOUT_MODEL  = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_TIMEOUT        = 60.0   # Groq is fast — 60s is generous


# ─────────────────────────────────────────────
#  Provider
# ─────────────────────────────────────────────

class GroqProvider(BaseProvider):
    """
    Groq LPU provider — ultra-fast inference for open models.

    Usage:
        provider = GroqProvider(api_key="gsk_...", model="meta-llama/llama-4-scout-17b-16e-instruct")
        for chunk in provider.stream_with_retry(messages):
            print(chunk.text, end="", flush=True)
    """

    name = "groq"

    def __init__(
        self,
        api_key:       str,
        model:         str   = DEFAULT_MODEL,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        timeout:       float = GROQ_TIMEOUT,
        system_prompt: Optional[str] = None,
    ) -> None:
        super().__init__(
            api_key       = api_key,
            model         = model,
            temperature   = temperature,
            max_tokens    = max_tokens,
            timeout       = timeout,
            system_prompt = system_prompt,
        )
        self._client = Groq(api_key=self.api_key, timeout=timeout)

    # ── Core streaming ────────────────────────

    def stream(
        self,
        messages:    list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> Iterator[StreamChunk]:
        """
        Stream tokens from Groq one chunk at a time.

        Yields:
            StreamChunk objects; last chunk has is_final=True.

        Raises:
            VegaAuthError      on 401
            VegaRateLimitError on 429
            VegaModelError     on 404
            VegaTimeoutError   on timeout / connection error
            VegaProviderError  on other API errors
        """
        payload = self._build_messages(messages)
        t       = temperature if temperature is not None else self.temperature
        toks    = max_tokens  if max_tokens  is not None else self.max_tokens

        try:
            stream = self._client.chat.completions.create(
                model       = self.model,
                messages    = payload,     # type: ignore[arg-type]
                temperature = t,
                max_tokens  = toks,
                stream      = True,
            )

            finish_reason: Optional[str] = None

            for event in stream:
                choice = event.choices[0] if event.choices else None
                if choice is None:
                    continue

                delta  = choice.delta
                reason = choice.finish_reason

                if reason:
                    finish_reason = reason

                text     = (delta.content or "") if delta else ""
                is_final = reason is not None

                yield StreamChunk(
                    text          = text,
                    is_final      = is_final,
                    finish_reason = finish_reason if is_final else None,
                )

            if finish_reason is None:
                yield StreamChunk(text="", is_final=True, finish_reason="stop")

        except APITimeoutError as exc:
            raise VegaTimeoutError(
                self.name, f"Request timed out after {self.timeout}s"
            ) from exc

        except APIConnectionError as exc:
            print("📡 No internet connection detected")
            print("Check your connection and try again")
            raise VegaProviderError(
                self.name, f"Connection error reaching Groq: {exc}"
            ) from exc

        except APIStatusError as exc:
            _raise_from_status(self.name, exc)

    # ── Non-streaming complete ────────────────

    def complete(
        self,
        messages:    list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> CompletionResponse:
        """Return the full Groq response as a CompletionResponse."""
        payload = self._build_messages(messages)
        t       = temperature if temperature is not None else self.temperature
        toks    = max_tokens  if max_tokens  is not None else self.max_tokens

        start = time.perf_counter()

        try:
            resp    = self._client.chat.completions.create(
                model       = self.model,
                messages    = payload,  # type: ignore[arg-type]
                temperature = t,
                max_tokens  = toks,
                stream      = False,
            )
            elapsed = time.perf_counter() - start
            choice  = resp.choices[0]
            usage   = resp.usage

            return CompletionResponse(
                text          = choice.message.content or "",
                model         = resp.model,
                provider      = self.name,
                input_tokens  = usage.prompt_tokens     if usage else 0,
                output_tokens = usage.completion_tokens if usage else 0,
                elapsed_s     = elapsed,
                finish_reason = choice.finish_reason or "stop",
            )

        except APITimeoutError as exc:
            raise VegaTimeoutError(
                self.name, f"Request timed out after {self.timeout}s"
            ) from exc

        except APIConnectionError as exc:
            print("📡 No internet connection detected")
            print("Check your connection and try again")
            raise VegaProviderError(
                self.name, f"Connection error reaching Groq: {exc}"
            ) from exc

        except APIStatusError as exc:
            _raise_from_status(self.name, exc)

    # ── Connectivity check ────────────────────

    def validate(self) -> bool:
        """Verify the Groq API key by listing available models."""
        try:
            self._client.models.list()
            return True
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise VegaAuthError(
                    self.name,
                    "Invalid API key. Get yours at https://console.groq.com",
                    status_code=401,
                ) from exc
            raise VegaProviderError(
                self.name, f"Validation failed: {exc}", status_code=exc.status_code
            ) from exc
        except (APITimeoutError, APIConnectionError) as exc:
            if isinstance(exc, APIConnectionError):
                print("📡 No internet connection detected")
                print("Check your connection and try again")
            raise VegaTimeoutError(
                self.name, f"Could not reach Groq: {exc}"
            ) from exc

    # ── Convenience constructors ──────────────

    @classmethod
    def with_llama4_scout(
        cls,
        api_key:       str,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        system_prompt: Optional[str] = None,
    ) -> "GroqProvider":
        """
        Return a provider pre-configured for Llama 4 Scout on Groq.

        Llama 4 Scout (17B × 16E MoE) offers excellent performance at
        blazing Groq LPU speeds.
        """
        return cls(
            api_key       = api_key,
            model         = LLAMA4_SCOUT_MODEL,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )

    @classmethod
    def with_fast(
        cls,
        api_key:       str,
        system_prompt: Optional[str] = None,
    ) -> "GroqProvider":
        """Return the fastest available model (Llama 3.1 8B Instant)."""
        return cls(
            api_key       = api_key,
            model         = "llama-3.1-8b-instant",
            temperature   = 0.6,
            max_tokens    = 4096,
            system_prompt = system_prompt,
        )


# ─────────────────────────────────────────────
#  Error mapping
# ─────────────────────────────────────────────

def _raise_from_status(provider: str, exc: "APIStatusError") -> None:
    code = exc.status_code
    body = str(exc.message) if hasattr(exc, "message") else str(exc)

    if code == 401:
        print("❌ Invalid API key for groq")
        print("Get your key at https://console.groq.com")
        raise VegaAuthError(
            provider,
            f"Invalid API key. Get yours at https://console.groq.com  ({body})",
            status_code=code,
        ) from exc
    if code == 403:
        raise VegaAuthError(
            provider,
            f"Access forbidden — check key permissions. ({body})",
            status_code=code,
        ) from exc
    if code == 404:
        raise VegaModelError(
            provider,
            f"Model not found. Run `vega models --provider groq` to list valid models. ({body})",
            status_code=code,
        ) from exc
    if code == 429:
        print("⚡ Rate limit hit on groq — switching...")
        from config.settings import fallback_provider
        fallback_provider("groq")
        raise VegaRateLimitError(
            provider,
            f"Rate limit hit — Groq free tier has per-minute limits. ({body})",
            status_code=code,
        ) from exc
    if code == 503:
        raise VegaProviderError(
            provider,
            f"Groq service unavailable — try again in a moment. ({body})",
            status_code=code,
        ) from exc
    raise VegaProviderError(
        provider, f"API error {code}: {body}", status_code=code
    ) from exc
