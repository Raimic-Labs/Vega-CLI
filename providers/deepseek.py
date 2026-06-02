"""
providers/deepseek.py — DeepSeek Provider
Uses the OpenAI-compatible DeepSeek API (pip install openai).
API base: https://api.deepseek.com/v1

Supported models:
  - deepseek-chat    (DeepSeek-V3 — general purpose)
  - deepseek-reasoner (DeepSeek-R1 — chain-of-thought reasoning)
  - deepseek-coder   (code-specialised)
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

try:
    from openai import OpenAI, APITimeoutError, APIConnectionError, APIStatusError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "openai package is required for the DeepSeek provider.\n"
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

DEEPSEEK_BASE_URL   = "https://api.deepseek.com/v1"
DEFAULT_MODEL       = "deepseek-chat"       # DeepSeek-V3
REASONER_MODEL      = "deepseek-reasoner"   # DeepSeek-R1
CODER_MODEL         = "deepseek-coder"
DEEPSEEK_TIMEOUT    = 120.0  # R1 reasoning can be slow


# ─────────────────────────────────────────────
#  Provider
# ─────────────────────────────────────────────

class DeepSeekProvider(BaseProvider):
    """
    DeepSeek provider — world-class coding & reasoning models.

    Usage:
        provider = DeepSeekProvider(api_key="sk-...", model="deepseek-chat")
        for chunk in provider.stream_with_retry(messages):
            print(chunk.text, end="", flush=True)

    Note on deepseek-reasoner (R1):
        R1 returns a <think>…</think> block before the final answer.
        Set strip_thinking=True to hide the internal reasoning in stream output.
    """

    name = "deepseek"

    def __init__(
        self,
        api_key:        str,
        model:          str   = DEFAULT_MODEL,
        temperature:    float = 0.7,
        max_tokens:     int   = 8000,
        timeout:        float = DEEPSEEK_TIMEOUT,
        system_prompt:  Optional[str] = None,
        strip_thinking: bool  = False,
    ) -> None:
        super().__init__(
            api_key       = api_key,
            model         = model,
            temperature   = temperature,
            max_tokens    = max_tokens,
            timeout       = timeout,
            system_prompt = system_prompt,
        )
        self.strip_thinking = strip_thinking
        self._client = OpenAI(
            api_key  = self.api_key,
            base_url = DEEPSEEK_BASE_URL,
            timeout  = timeout,
        )

    # ── Helpers ───────────────────────────────

    @property
    def _is_reasoner(self) -> bool:
        return self.model == REASONER_MODEL

    def _maybe_strip_thinking(self, text: str) -> str:
        """
        Remove <think>…</think> blocks emitted by DeepSeek-R1 if
        strip_thinking is enabled.
        """
        if not self.strip_thinking:
            return text
        import re
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).lstrip()

    # ── Core streaming ────────────────────────

    def stream(
        self,
        messages:    list[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens:  Optional[int]   = None,
    ) -> Iterator[StreamChunk]:
        """
        Stream tokens from DeepSeek one chunk at a time.

        For deepseek-reasoner, reasoning tokens (<think> blocks) are
        streamed first, followed by the final answer unless strip_thinking=True.

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

        # DeepSeek-R1 doesn't support temperature — must be 1.0
        if self._is_reasoner:
            t = 1.0

        try:
            stream = self._client.chat.completions.create(
                model       = self.model,
                messages    = payload,  # type: ignore[arg-type]
                temperature = t,
                max_tokens  = toks,
                stream      = True,
            )

            finish_reason:   Optional[str] = None
            in_think_block:  bool          = False
            buffer:          str           = ""

            for event in stream:
                choice = event.choices[0] if event.choices else None
                if choice is None:
                    continue

                delta  = choice.delta
                reason = choice.finish_reason
                if reason:
                    finish_reason = reason

                # R1 may emit reasoning_content separately
                text = ""
                if delta:
                    reasoning = getattr(delta, "reasoning_content", None) or ""
                    content   = delta.content or ""

                    if reasoning and not self.strip_thinking:
                        # Wrap reasoning in think tags for downstream consumers
                        if not in_think_block:
                            text += "<think>"
                            in_think_block = True
                        text += reasoning
                    elif content:
                        if in_think_block:
                            text += "</think>\n"
                            in_think_block = False
                        text += content

                # Apply strip_thinking filter on the assembled text
                if self.strip_thinking and text:
                    buffer += text
                    # Only emit content outside <think> blocks
                    safe, buffer = _extract_outside_think(buffer)
                    text = safe

                is_final = reason is not None
                if text or is_final:
                    yield StreamChunk(
                        text          = text,
                        is_final      = is_final,
                        finish_reason = finish_reason if is_final else None,
                    )

            # Flush any remaining buffer
            if self.strip_thinking and buffer:
                clean = _extract_outside_think(buffer)[0]
                if clean:
                    yield StreamChunk(text=clean, is_final=False)

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
                self.name, f"Connection error reaching DeepSeek: {exc}"
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
        """Return the full DeepSeek response as a CompletionResponse."""
        payload = self._build_messages(messages)
        t       = temperature if temperature is not None else self.temperature
        toks    = max_tokens  if max_tokens  is not None else self.max_tokens

        if self._is_reasoner:
            t = 1.0

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

            text = choice.message.content or ""

            # R1 may include reasoning in a separate field
            reasoning = getattr(choice.message, "reasoning_content", None) or ""
            if reasoning and not self.strip_thinking:
                text = f"<think>\n{reasoning}\n</think>\n\n{text}"
            elif reasoning and self.strip_thinking:
                pass  # drop reasoning

            if self.strip_thinking:
                text = self._maybe_strip_thinking(text)

            return CompletionResponse(
                text          = text,
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
                self.name, f"Connection error reaching DeepSeek: {exc}"
            ) from exc

        except APIStatusError as exc:
            _raise_from_status(self.name, exc)

    # ── Connectivity check ────────────────────

    def validate(self) -> bool:
        """Verify the DeepSeek API key with a minimal request."""
        try:
            self._client.chat.completions.create(
                model      = self.model,
                messages   = [{"role": "user", "content": "hi"}],
                max_tokens = 1,
                stream     = False,
            )
            return True
        except APIStatusError as exc:
            if exc.status_code in (401, 403):
                raise VegaAuthError(
                    self.name,
                    "Invalid API key. Get yours at https://platform.deepseek.com",
                    status_code=exc.status_code,
                ) from exc
            raise VegaProviderError(
                self.name, f"Validation failed: {exc}", status_code=exc.status_code
            ) from exc
        except (APITimeoutError, APIConnectionError) as exc:
            if isinstance(exc, APIConnectionError):
                print("📡 No internet connection detected")
                print("Check your connection and try again")
            raise VegaTimeoutError(
                self.name, f"Could not reach DeepSeek API: {exc}"
            ) from exc

    # ── Convenience constructors ──────────────

    @classmethod
    def with_v3(
        cls,
        api_key:        str,
        temperature:    float = 0.7,
        max_tokens:     int   = 8000,
        system_prompt:  Optional[str] = None,
    ) -> "DeepSeekProvider":
        """Return a provider pre-configured for DeepSeek-V3 (deepseek-chat)."""
        return cls(
            api_key       = api_key,
            model         = DEFAULT_MODEL,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )

    @classmethod
    def with_r1(
        cls,
        api_key:        str,
        max_tokens:     int   = 8000,
        system_prompt:  Optional[str] = None,
        strip_thinking: bool  = False,
    ) -> "DeepSeekProvider":
        """
        Return a provider pre-configured for DeepSeek-R1 (deepseek-reasoner).

        R1 is a chain-of-thought reasoning model — ideal for hard math,
        multi-step coding problems, and logical deduction.

        Args:
            strip_thinking: If True, the <think>…</think> blocks are removed
                            from the output shown to the user.
        """
        return cls(
            api_key         = api_key,
            model           = REASONER_MODEL,
            temperature     = 1.0,   # R1 requires exactly 1.0
            max_tokens      = max_tokens,
            system_prompt   = system_prompt,
            strip_thinking  = strip_thinking,
        )

    @classmethod
    def with_coder(
        cls,
        api_key:       str,
        temperature:   float = 0.3,
        max_tokens:    int   = 8000,
        system_prompt: Optional[str] = None,
    ) -> "DeepSeekProvider":
        """Return a provider pre-configured for DeepSeek-Coder."""
        return cls(
            api_key       = api_key,
            model         = CODER_MODEL,
            temperature   = temperature,
            max_tokens    = max_tokens,
            system_prompt = system_prompt,
        )


# ─────────────────────────────────────────────
#  Thinking block filter
# ─────────────────────────────────────────────

def _extract_outside_think(text: str) -> tuple[str, str]:
    """
    From a partial stream buffer, return:
      (safe_to_emit, remaining_buffer)

    Emits everything outside <think>…</think> tags.
    Keeps partial tags in the buffer until they close.
    """
    import re
    out    = []
    rest   = text
    while rest:
        start_idx = rest.find("<think>")
        if start_idx == -1:
            # No opening tag → safe to emit everything
            out.append(rest)
            rest = ""
            break
        # Emit content before the tag
        out.append(rest[:start_idx])
        rest = rest[start_idx:]
        # Find closing tag
        end_idx = rest.find("</think>")
        if end_idx == -1:
            # Opening tag found but no closing yet → keep in buffer
            break
        # Skip the entire <think>…</think> block
        rest = rest[end_idx + len("</think>"):]

    return "".join(out), rest


# ─────────────────────────────────────────────
#  Error mapping
# ─────────────────────────────────────────────

def _raise_from_status(provider: str, exc: "APIStatusError") -> None:
    code = exc.status_code
    body = str(exc.message) if hasattr(exc, "message") else str(exc)

    if code == 401:
        print("❌ Invalid API key for deepseek")
        print("Get your key at https://platform.deepseek.com")
        raise VegaAuthError(
            provider,
            f"Invalid API key. Get yours at https://platform.deepseek.com  ({body})",
            status_code=code,
        ) from exc
    if code == 402:
        raise VegaProviderError(
            provider,
            f"DeepSeek account balance insufficient. Top up at platform.deepseek.com ({body})",
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
            f"Model not found. Run `vega models --provider deepseek` to list valid models. ({body})",
            status_code=code,
        ) from exc
    if code == 429:
        print("⚡ Rate limit hit on deepseek — switching...")
        from config.settings import fallback_provider
        fallback_provider("deepseek")
        raise VegaRateLimitError(
            provider,
            f"Rate limit exceeded — slow down or check your plan. ({body})",
            status_code=code,
        ) from exc
    if code in (500, 503):
        raise VegaProviderError(
            provider,
            f"DeepSeek server error {code} — try again shortly. ({body})",
            status_code=code,
        ) from exc
    raise VegaProviderError(
        provider, f"API error {code}: {body}", status_code=code
    ) from exc
