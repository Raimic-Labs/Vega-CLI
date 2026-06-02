"""
providers/google.py — Google Gemini Provider
Uses the google-genai SDK (pip install google-genai).

Supported models:
  - gemini-2.5-pro
  - gemini-2.0-flash
  - gemini-1.5-pro
  - gemini-1.5-flash
  - gemini-1.5-flash-8b
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

try:
    import google.genai as genai
    from google.genai import types as genai_types
    from google.genai.errors import APIError, ClientError, ServerError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "google-genai package is required for the Google provider.\n"
        "Install it with: pip install google-genai"
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

DEFAULT_MODEL  = "gemini-2.0-flash"
GEMINI_25_PRO  = "gemini-2.5-pro"
GEMINI_20_FLASH = "gemini-2.0-flash"


# ─────────────────────────────────────────────
#  Provider
# ─────────────────────────────────────────────

class GoogleProvider(BaseProvider):
    """
    Google Gemini provider via the google-genai SDK.

    Usage:
        provider = GoogleProvider(api_key="AIza...", model="gemini-2.5-pro")
        for chunk in provider.stream_with_retry(messages):
            print(chunk.text, end="", flush=True)
    """

    name = "google"

    def __init__(
        self,
        api_key:       str,
        model:         str   = DEFAULT_MODEL,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        timeout:       float = 120.0,
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
        self._client = genai.Client(api_key=self.api_key)

    # ── Helpers ───────────────────────────────

    def _to_genai_contents(
        self, messages: list[Message]
    ) -> list[genai_types.Content]:
        """Convert our Message list into genai Content objects."""
        contents: list[genai_types.Content] = []
        for msg in messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append(
                genai_types.Content(
                    role=role,
                    parts=[genai_types.Part(text=msg.content)],
                )
            )
        return contents

    def _gen_config(
        self,
        temperature: Optional[float],
        max_tokens:  Optional[int],
    ) -> genai_types.GenerateContentConfig:
        return genai_types.GenerateContentConfig(
            temperature       = temperature if temperature is not None else self.temperature,
            max_output_tokens = max_tokens  if max_tokens  is not None else self.max_tokens,
            system_instruction= self.system_prompt or genai_types.UNSET,
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
        Stream tokens from Gemini one chunk at a time.

        Yields:
            StreamChunk objects; last chunk has is_final=True.

        Raises:
            VegaAuthError      on 401 / permission denied
            VegaRateLimitError on 429
            VegaModelError     on 404 / invalid model
            VegaTimeoutError   on timeout
            VegaProviderError  on other SDK errors
        """
        contents   = self._to_genai_contents(messages)
        gen_config = self._gen_config(temperature, max_tokens)

        try:
            finish_reason: Optional[str] = None

            for chunk in self._client.models.generate_content_stream(
                model    = self.model,
                contents = contents,
                config   = gen_config,
            ):
                # Extract text from the first candidate
                text = ""
                if chunk.candidates:
                    cand = chunk.candidates[0]
                    if cand.content and cand.content.parts:
                        text = "".join(
                            p.text for p in cand.content.parts if p.text
                        )
                    raw_reason = cand.finish_reason
                    if raw_reason and raw_reason.name not in ("FINISH_REASON_UNSPECIFIED", ""):
                        finish_reason = raw_reason.name.lower()

                is_final = finish_reason is not None
                yield StreamChunk(
                    text          = text,
                    is_final      = is_final,
                    finish_reason = finish_reason if is_final else None,
                )

            if finish_reason is None:
                yield StreamChunk(text="", is_final=True, finish_reason="stop")

        except Exception as exc:
            _raise_from_google_exc(self.name, exc)

    # ── Non-streaming complete ────────────────

    def complete(
        self,
        messages:    list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> CompletionResponse:
        """Return the full Gemini response as a CompletionResponse."""
        contents   = self._to_genai_contents(messages)
        gen_config = self._gen_config(temperature, max_tokens)

        start = time.perf_counter()

        try:
            resp = self._client.models.generate_content(
                model    = self.model,
                contents = contents,
                config   = gen_config,
            )
            elapsed = time.perf_counter() - start

            text    = resp.text or ""
            usage   = resp.usage_metadata
            reason  = "stop"
            if resp.candidates:
                r = resp.candidates[0].finish_reason
                if r:
                    reason = r.name.lower()

            return CompletionResponse(
                text          = text,
                model         = self.model,
                provider      = self.name,
                input_tokens  = usage.prompt_token_count     if usage else 0,
                output_tokens = usage.candidates_token_count if usage else 0,
                elapsed_s     = elapsed,
                finish_reason = reason,
            )

        except Exception as exc:
            _raise_from_google_exc(self.name, exc)

    # ── Connectivity check ────────────────────

    def validate(self) -> bool:
        """Ping Gemini with a minimal request to verify the API key."""
        try:
            self._client.models.generate_content(
                model    = self.model,
                contents = [genai_types.Content(
                    role  = "user",
                    parts = [genai_types.Part(text="hi")],
                )],
                config = genai_types.GenerateContentConfig(max_output_tokens=1),
            )
            return True
        except Exception as exc:
            _raise_from_google_exc(self.name, exc)

    # ── Convenience constructors ──────────────

    @classmethod
    def with_gemini_25_pro(
        cls,
        api_key:       str,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        system_prompt: Optional[str] = None,
    ) -> "GoogleProvider":
        """Return a provider pre-configured for Gemini 2.5 Pro."""
        return cls(
            api_key       = api_key,
            model         = GEMINI_25_PRO,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )

    @classmethod
    def with_gemini_20_flash(
        cls,
        api_key:       str,
        temperature:   float = 0.7,
        max_tokens:    int   = 8192,
        system_prompt: Optional[str] = None,
    ) -> "GoogleProvider":
        """Return a provider pre-configured for Gemini 2.0 Flash."""
        return cls(
            api_key       = api_key,
            model         = GEMINI_20_FLASH,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )


# ─────────────────────────────────────────────
#  Error mapping
# ─────────────────────────────────────────────

def _raise_from_google_exc(provider: str, exc: Exception) -> None:
    msg = str(exc)

    # google-genai SDK exposes status codes on ClientError / ServerError
    status_code = getattr(exc, "status_code", 0) or getattr(exc, "code", 0) or 0

    if isinstance(exc, ClientError):
        if status_code == 400:
            raise VegaModelError(
                provider,
                f"Bad request — check model name or prompt. ({msg})",
                status_code=400,
            ) from exc
        if status_code in (401, 403) or "API_KEY" in msg.upper() or "permission" in msg.lower():
            print("❌ Invalid API key for google")
            print("Get your key at https://aistudio.google.com")
            raise VegaAuthError(
                provider,
                f"Invalid or missing Google API key. ({msg})",
                status_code=status_code,
            ) from exc
        if status_code == 404:
            raise VegaModelError(
                provider,
                f"Model not found: '{provider}'. ({msg})",
                status_code=404,
            ) from exc
        if status_code == 429:
            print("⚡ Rate limit hit on google — switching...")
            from config.settings import fallback_provider
            fallback_provider("google")
            raise VegaRateLimitError(
                provider,
                f"Rate limit exceeded — slow down or upgrade your quota. ({msg})",
                status_code=429,
            ) from exc

    if isinstance(exc, ServerError):
        raise VegaProviderError(
            provider,
            f"Google server error {status_code}: {msg}",
            status_code=status_code,
        ) from exc

    # Timeout / connection signals
    low = msg.lower()
    if "connection" in low or "socket" in low or "dns" in low or "unreachable" in low:
        print("📡 No internet connection detected")
        print("Check your connection and try again")
        raise VegaProviderError(provider, f"Connection error: {msg}") from exc
    if any(w in low for w in ("timeout", "timed out", "deadline")):
        raise VegaTimeoutError(provider, f"Request timed out: {msg}") from exc

    raise VegaProviderError(provider, f"Unexpected error: {msg}") from exc
