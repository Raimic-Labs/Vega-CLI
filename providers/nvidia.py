"""
providers/nvidia.py — NVIDIA NIM Provider
API base: https://integrate.api.nvidia.com/v1  (OpenAI-compatible)
Free tier available at build.nvidia.com

Supported models include:
  - meta/llama-3.1-405b-instruct
  - moonshotai/kimi-k2  (kimi-k2.6)
  - nvidia/llama-3.1-nemotron-70b-instruct
  - qwen/qwen2.5-coder-32b-instruct
  - deepseek-ai/deepseek-r1
  ... (see config/models.py for full list)
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

try:
    from openai import OpenAI, APITimeoutError, APIConnectionError, APIStatusError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "openai package is required for the NVIDIA provider.\n"
        "Install it with: pip install openai"
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

NVIDIA_BASE_URL   = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL     = "meta/llama-3.1-405b-instruct"
KIMI_K2_MODEL     = "moonshotai/kimi-k2"       # Kimi-K2.6 on NVIDIA NIM
CONNECT_TIMEOUT   = 10.0   # seconds for initial connection
READ_TIMEOUT      = 120.0  # seconds for streaming reads


# ─────────────────────────────────────────────
#  Provider
# ─────────────────────────────────────────────

class NvidiaProvider(BaseProvider):
    """
    NVIDIA NIM provider — wraps the OpenAI-compatible NIM endpoint.

    Usage:
        provider = NvidiaProvider(api_key="nvapi-...", model="moonshotai/kimi-k2")
        for chunk in provider.stream_with_retry(messages):
            print(chunk.text, end="", flush=True)
    """

    name = "nvidia"

    def __init__(
        self,
        api_key:       str,
        model:         str   = DEFAULT_MODEL,
        temperature:   float = 0.7,
        max_tokens:    int   = 4096,
        timeout:       float = READ_TIMEOUT,
        system_prompt: Optional[str] = None,
        base_url:      str   = NVIDIA_BASE_URL,
    ) -> None:
        super().__init__(
            api_key       = api_key,
            model         = model,
            temperature   = temperature,
            max_tokens    = max_tokens,
            timeout       = timeout,
            system_prompt = system_prompt,
        )
        self._client = OpenAI(
            api_key  = self.api_key,
            base_url = base_url,
            timeout  = timeout,
        )

    # ── Core streaming ────────────────────────

    def stream(
        self,
        messages:    list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> Iterator[StreamChunk]:
        """
        Stream tokens from NVIDIA NIM one chunk at a time.

        Yields:
            StreamChunk with text fragments; last chunk has is_final=True.

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
            response = self._client.chat.completions.create(
                model       = self.model,
                messages    = payload,    # type: ignore[arg-type]
                temperature = t,
                max_tokens  = toks,
                stream      = True,
            )

            finish_reason: Optional[str] = None

            for event in response:
                delta  = event.choices[0].delta if event.choices else None
                reason = event.choices[0].finish_reason if event.choices else None

                if reason:
                    finish_reason = reason

                text = (delta.content or "") if delta else ""

                is_final = reason is not None
                yield StreamChunk(
                    text          = text,
                    is_final      = is_final,
                    finish_reason = finish_reason if is_final else None,
                )

            # Ensure we always close with a final chunk
            if finish_reason is None:
                yield StreamChunk(text="", is_final=True, finish_reason="stop")

        except APITimeoutError as exc:
            raise VegaTimeoutError(
                self.name, f"Request timed out after {self.timeout}s"
            ) from exc

        except APIConnectionError as exc:
            raise VegaTimeoutError(
                self.name, f"Connection error: {exc}"
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
        """
        Return full response without streaming.
        Falls back to collecting stream chunks for models that require it.
        """
        payload = self._build_messages(messages)
        t       = temperature if temperature is not None else self.temperature
        toks    = max_tokens  if max_tokens  is not None else self.max_tokens

        start = time.perf_counter()

        try:
            resp = self._client.chat.completions.create(
                model       = self.model,
                messages    = payload,    # type: ignore[arg-type]
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
            raise VegaTimeoutError(
                self.name, f"Connection error: {exc}"
            ) from exc

        except APIStatusError as exc:
            _raise_from_status(self.name, exc)

    # ── Connectivity check ────────────────────

    def validate(self) -> bool:
        """
        Send a minimal ping to verify the API key works.

        Returns:
            True if valid.

        Raises:
            VegaAuthError on 401.
        """
        try:
            self._client.models.list()
            return True
        except APIStatusError as exc:
            if exc.status_code == 401:
                raise VegaAuthError(
                    self.name,
                    "Invalid API key. Get yours free at https://build.nvidia.com",
                    status_code=401,
                ) from exc
            raise VegaProviderError(
                self.name, f"Validation failed: {exc}", status_code=exc.status_code
            ) from exc
        except (APITimeoutError, APIConnectionError) as exc:
            raise VegaTimeoutError(
                self.name, f"Could not reach NVIDIA NIM: {exc}"
            ) from exc

    # ── Convenience: Kimi-K2 shortcut ────────

    @classmethod
    def with_kimi_k2(
        cls,
        api_key:       str,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        system_prompt: Optional[str] = None,
    ) -> "NvidiaProvider":
        """
        Return a provider pre-configured for Moonshot Kimi-K2 (kimi-k2.6).

        Example:
            provider = NvidiaProvider.with_kimi_k2(api_key="nvapi-...")
        """
        return cls(
            api_key       = api_key,
            model         = KIMI_K2_MODEL,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )


# ─────────────────────────────────────────────
#  Error mapping helper
# ─────────────────────────────────────────────

def _raise_from_status(provider: str, exc: "APIStatusError") -> None:
    code = exc.status_code
    body = str(exc.message) if hasattr(exc, "message") else str(exc)

    if code == 401:
        raise VegaAuthError(
            provider,
            f"Invalid API key. Get yours at https://build.nvidia.com  ({body})",
            status_code=code,
        ) from exc
    if code == 403:
        raise VegaAuthError(
            provider,
            f"Access forbidden — check your API key permissions. ({body})",
            status_code=code,
        ) from exc
    if code == 404:
        raise VegaModelError(
            provider,
            f"Model not found. Check the model ID is correct. ({body})",
            status_code=code,
        ) from exc
    if code == 429:
        raise VegaRateLimitError(
            provider,
            f"Rate limit hit — wait a moment and retry. ({body})",
            status_code=code,
        ) from exc
    raise VegaProviderError(
        provider, f"API error {code}: {body}", status_code=code
    ) from exc
