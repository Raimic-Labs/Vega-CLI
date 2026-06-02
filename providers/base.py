"""
providers/base.py — Abstract base class for all Vega providers.

Every provider must implement:
  - stream()    → yields str tokens one by one
  - complete()  → returns full response as str
  - validate()  → checks API key & connectivity
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generator, Iterator, Optional


# ─────────────────────────────────────────────
#  Data types
# ─────────────────────────────────────────────

@dataclass
class Message:
    """A single conversation message."""
    role:    str   # "system" | "user" | "assistant"
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class StreamChunk:
    """A single token/delta returned from a streaming call."""
    text:       str
    is_final:   bool = False
    finish_reason: Optional[str] = None   # "stop" | "length" | "error"


@dataclass
class CompletionResponse:
    """Full response after streaming is complete."""
    text:          str
    model:         str
    provider:      str
    input_tokens:  int = 0
    output_tokens: int = 0
    elapsed_s:     float = 0.0
    finish_reason: str = "stop"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# ─────────────────────────────────────────────
#  Exceptions
# ─────────────────────────────────────────────

class VegaProviderError(Exception):
    """Raised when a provider call fails in a recoverable way."""
    def __init__(self, provider: str, message: str, status_code: int = 0) -> None:
        self.provider    = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


class VegaAuthError(VegaProviderError):
    """Raised on 401 / invalid API key."""


class VegaRateLimitError(VegaProviderError):
    """Raised on 429 / quota exceeded."""


class VegaTimeoutError(VegaProviderError):
    """Raised when a request times out."""


class VegaModelError(VegaProviderError):
    """Raised when the requested model is unavailable or invalid."""


# ─────────────────────────────────────────────
#  Retry helper
# ─────────────────────────────────────────────

def _with_retry(
    fn,
    *,
    provider: str,
    max_retries: int = 1,
    retry_delay: float = 2.0,
    retry_on: tuple = (VegaTimeoutError,),
):
    """
    Call *fn()* up to *max_retries + 1* times.
    Only retries on exception types listed in *retry_on*.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue
        except Exception:
            raise
    raise last_exc  # type: ignore[misc]


# ─────────────────────────────────────────────
#  Abstract Base Provider
# ─────────────────────────────────────────────

class BaseProvider(ABC):
    """
    Abstract base class for all Vega LLM providers.

    Subclasses must implement:
      - stream()
      - complete()
      - validate()

    Attributes:
        name        Human-readable provider name.
        api_key     API key for authentication.
        model       Active model ID.
        temperature Sampling temperature (0.0 – 2.0).
        max_tokens  Maximum output tokens.
        timeout     HTTP timeout in seconds.
    """

    #: Override in subclass
    name: str = "base"

    def __init__(
        self,
        api_key:     str,
        model:       str,
        temperature: float = 0.7,
        max_tokens:  int   = 4096,
        timeout:     float = 60.0,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.api_key       = api_key
        self.model         = model
        self.temperature   = temperature
        self.max_tokens    = max_tokens
        self.timeout       = timeout
        self.system_prompt = system_prompt

        self._validate_api_key()

    # ── Abstract interface ────────────────────

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> Iterator[StreamChunk]:
        """
        Yield StreamChunk objects one at a time as tokens arrive.

        The last chunk will have is_final=True.
        Implementations MUST handle timeouts and re-raise as VegaTimeoutError.
        """
        ...

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> CompletionResponse:
        """
        Return a CompletionResponse with the full text assembled.
        Default implementation collects from stream(); override for efficiency.
        """
        ...

    @abstractmethod
    def validate(self) -> bool:
        """
        Ping the API with a minimal request to confirm the key works.
        Returns True on success, raises VegaAuthError on failure.
        """
        ...

    # ── Helpers available to subclasses ──────

    def _validate_api_key(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise VegaAuthError(
                self.name,
                f"API key is empty. Run: vega config set {self.name}_api_key <your-key>",
            )

    def _build_messages(self, messages: list[Message]) -> list[dict]:
        """Prepend system prompt if configured, convert to dicts."""
        result: list[dict] = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend(m.to_dict() for m in messages)
        return result

    def _collect_stream(self, messages: list[Message], **kwargs) -> CompletionResponse:
        """
        Utility: collect all stream chunks into a CompletionResponse.
        Subclasses may call this inside complete() if they don't have a
        dedicated non-streaming endpoint.
        """
        start   = time.perf_counter()
        parts: list[str] = []
        finish_reason = "stop"

        for chunk in self.stream(messages, **kwargs):
            if chunk.text:
                parts.append(chunk.text)
            if chunk.is_final and chunk.finish_reason:
                finish_reason = chunk.finish_reason

        elapsed = time.perf_counter() - start
        full_text = "".join(parts)

        return CompletionResponse(
            text          = full_text,
            model         = self.model,
            provider      = self.name,
            elapsed_s     = elapsed,
            finish_reason = finish_reason,
        )

    def stream_with_retry(
        self,
        messages: list[Message],
        **kwargs,
    ) -> Iterator[StreamChunk]:
        """stream() wrapped with one automatic retry on timeout."""
        attempt = 0
        while True:
            try:
                yield from self.stream(messages, **kwargs)
                return
            except VegaTimeoutError:
                if attempt >= 1:
                    raise
                attempt += 1
                print("⏱ Timed out — retrying once...")
                time.sleep(2.0)

    def complete_with_retry(
        self,
        messages: list[Message],
        **kwargs,
    ) -> CompletionResponse:
        """complete() wrapped with one automatic retry on timeout."""
        try:
            return self.complete(messages, **kwargs)
        except VegaTimeoutError:
            print("⏱ Timed out — retrying once...")
            time.sleep(2.0)
            return self.complete(messages, **kwargs)

    # ── Dunder ───────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model!r}>"
