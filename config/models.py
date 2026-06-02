"""
config/models.py — Vega CLI Model Registry
All supported models across NVIDIA, Google, Groq, and DeepSeek providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
#  Data Types
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class ModelDef:
    """Immutable definition of a single model."""
    id:           str            # API model identifier
    name:         str            # Human-readable name
    provider:     str            # "nvidia" | "google" | "groq" | "deepseek"
    context:      int            # Context window in tokens
    max_output:   int            # Max output tokens
    supports_streaming: bool = True
    supports_vision:    bool = False
    supports_tools:     bool = False
    notes:        str = ""

    @property
    def display_name(self) -> str:
        return f"{self.provider.upper()} / {self.name}"

    @property
    def context_str(self) -> str:
        if self.context >= 1_000_000:
            return f"{self.context // 1_000_000}M"
        if self.context >= 1_000:
            return f"{self.context // 1_000}k"
        return str(self.context)

    def as_dict(self) -> dict:
        return {
            "id":                 self.id,
            "name":               self.name,
            "provider":           self.provider,
            "context":            self.context_str,
            "max_output":         self.max_output,
            "supports_streaming": self.supports_streaming,
            "supports_vision":    self.supports_vision,
            "supports_tools":     self.supports_tools,
            "notes":              self.notes,
        }


# ─────────────────────────────────────────────
#  NVIDIA (via NVIDIA NIM / build.nvidia.com)
# ─────────────────────────────────────────────

NVIDIA_MODELS: list[ModelDef] = [
    ModelDef(
        id="moonshotai/kimi-k2-instruct",
        name="Kimi K2.6",
        provider="nvidia",
        context=32_768,
        max_output=8_192,
        supports_tools=True,
        notes="Moonshot Kimi-K2.6 model",
    ),
    ModelDef(
        id="meta/llama-3.1-405b-instruct",
        name="Llama 3.1 405B Instruct",
        provider="nvidia",
        context=128_000,
        max_output=4_096,
        supports_tools=True,
        notes="Flagship open model — best for complex reasoning & code",
    ),
    ModelDef(
        id="meta/llama-3.1-70b-instruct",
        name="Llama 3.1 70B Instruct",
        provider="nvidia",
        context=128_000,
        max_output=4_096,
        supports_tools=True,
        notes="Balanced performance and speed",
    ),
    ModelDef(
        id="meta/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="nvidia",
        context=128_000,
        max_output=4_096,
        supports_tools=True,
        notes="Lightweight — ideal for fast responses",
    ),
    ModelDef(
        id="meta/llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct",
        provider="nvidia",
        context=128_000,
        max_output=8_192,
        supports_tools=True,
        notes="Latest Llama 3.3 — improved coding",
    ),
    ModelDef(
        id="nvidia/llama-3.1-nemotron-70b-instruct",
        name="Nemotron 70B Instruct",
        provider="nvidia",
        context=128_000,
        max_output=32_768,
        supports_tools=True,
        notes="NVIDIA-tuned — RLHF optimised for helpfulness",
    ),
    ModelDef(
        id="nvidia/llama-3.1-nemotron-nano-8b-v1",
        name="Nemotron Nano 8B",
        provider="nvidia",
        context=128_000,
        max_output=8_192,
        notes="Ultra-fast nano model",
    ),
    ModelDef(
        id="mistralai/mistral-7b-instruct-v0.3",
        name="Mistral 7B Instruct v0.3",
        provider="nvidia",
        context=32_768,
        max_output=4_096,
        notes="Efficient European open model",
    ),
    ModelDef(
        id="mistralai/mixtral-8x7b-instruct-v0.1",
        name="Mixtral 8×7B Instruct",
        provider="nvidia",
        context=32_768,
        max_output=4_096,
        notes="MoE architecture — strong at code & math",
    ),
    ModelDef(
        id="mistralai/mixtral-8x22b-instruct-v0.1",
        name="Mixtral 8×22B Instruct",
        provider="nvidia",
        context=65_536,
        max_output=8_192,
        notes="High-capacity MoE",
    ),
    ModelDef(
        id="qwen/qwen2-7b-instruct",
        name="Qwen2 7B Instruct",
        provider="nvidia",
        context=131_072,
        max_output=4_096,
        notes="Alibaba open model — strong multilingual",
    ),
    ModelDef(
        id="qwen/qwen2.5-coder-32b-instruct",
        name="Qwen2.5 Coder 32B",
        provider="nvidia",
        context=131_072,
        max_output=8_192,
        supports_tools=True,
        notes="State-of-the-art code model",
    ),
    ModelDef(
        id="deepseek-ai/deepseek-r1",
        name="DeepSeek-R1 (via NVIDIA)",
        provider="nvidia",
        context=64_000,
        max_output=8_192,
        notes="Reasoning model via NVIDIA NIM",
    ),
]

# ─────────────────────────────────────────────
#  Google (Gemini)
# ─────────────────────────────────────────────

GOOGLE_MODELS: list[ModelDef] = [
    ModelDef(
        id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="google",
        context=1_048_576,
        max_output=8_192,
        supports_streaming=True,
        supports_vision=True,
        supports_tools=True,
        notes="Next-gen multimodal — fast & capable",
    ),
    ModelDef(
        id="gemini-2.0-flash-thinking-exp",
        name="Gemini 2.0 Flash Thinking",
        provider="google",
        context=1_048_576,
        max_output=8_192,
        supports_streaming=True,
        supports_vision=True,
        notes="Experimental chain-of-thought reasoning",
    ),
    ModelDef(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="google",
        context=2_097_152,
        max_output=8_192,
        supports_streaming=True,
        supports_vision=True,
        supports_tools=True,
        notes="2M token context — best for large codebases",
    ),
    ModelDef(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="google",
        context=1_048_576,
        max_output=8_192,
        supports_streaming=True,
        supports_vision=True,
        supports_tools=True,
        notes="Speed-optimised with 1M context",
    ),
    ModelDef(
        id="gemini-1.5-flash-8b",
        name="Gemini 1.5 Flash 8B",
        provider="google",
        context=1_048_576,
        max_output=8_192,
        supports_streaming=True,
        supports_vision=True,
        notes="Smallest Flash — lowest latency",
    ),
]

# ─────────────────────────────────────────────
#  Groq (ultra-fast inference)
# ─────────────────────────────────────────────

GROQ_MODELS: list[ModelDef] = [
    ModelDef(
        id="meta-llama/llama-4-scout-17b-16e-instruct",
        name="Llama 4 Scout",
        provider="groq",
        context=128_000,
        max_output=8_192,
        supports_tools=True,
        notes="Fast open MoE reasoning model on Groq",
    ),
    ModelDef(
        id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B Versatile",
        provider="groq",
        context=128_000,
        max_output=32_768,
        supports_tools=True,
        notes="Best overall on Groq — versatile & fast",
    ),
    ModelDef(
        id="llama-3.1-70b-versatile",
        name="Llama 3.1 70B Versatile",
        provider="groq",
        context=128_000,
        max_output=32_768,
        supports_tools=True,
        notes="Reliable 70B on Groq hardware",
    ),
    ModelDef(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant",
        provider="groq",
        context=128_000,
        max_output=8_000,
        supports_tools=True,
        notes="Fastest on Groq — near-instant responses",
    ),
    ModelDef(
        id="mixtral-8x7b-32768",
        name="Mixtral 8×7B",
        provider="groq",
        context=32_768,
        max_output=32_768,
        supports_tools=True,
        notes="MoE model on Groq LPU — extremely fast",
    ),
    ModelDef(
        id="gemma2-9b-it",
        name="Gemma 2 9B IT",
        provider="groq",
        context=8_192,
        max_output=8_192,
        notes="Google Gemma 2 on Groq",
    ),
    ModelDef(
        id="gemma-7b-it",
        name="Gemma 7B IT",
        provider="groq",
        context=8_192,
        max_output=8_192,
        notes="Original Gemma on Groq LPU",
    ),
    ModelDef(
        id="llama3-groq-70b-8192-tool-use-preview",
        name="Llama 3 70B Tool Use",
        provider="groq",
        context=8_192,
        max_output=8_192,
        supports_tools=True,
        notes="Optimised for tool/function calling",
    ),
    ModelDef(
        id="llama3-groq-8b-8192-tool-use-preview",
        name="Llama 3 8B Tool Use",
        provider="groq",
        context=8_192,
        max_output=8_192,
        supports_tools=True,
        notes="Fast tool-use model",
    ),
    ModelDef(
        id="deepseek-r1-distill-llama-70b",
        name="DeepSeek-R1 Distill (Llama 70B)",
        provider="groq",
        context=128_000,
        max_output=16_000,
        notes="R1 reasoning distilled into Llama 70B",
    ),
    ModelDef(
        id="qwen-qwq-32b",
        name="QwQ 32B",
        provider="groq",
        context=128_000,
        max_output=16_000,
        notes="Alibaba QwQ reasoning model on Groq",
    ),
]

# ─────────────────────────────────────────────
#  DeepSeek
# ─────────────────────────────────────────────

DEEPSEEK_MODELS: list[ModelDef] = [
    ModelDef(
        id="deepseek-chat",
        name="DeepSeek-V3",
        provider="deepseek",
        context=64_000,
        max_output=8_000,
        supports_tools=True,
        notes="Best general-purpose model from DeepSeek",
    ),
    ModelDef(
        id="deepseek-reasoner",
        name="DeepSeek-R1",
        provider="deepseek",
        context=64_000,
        max_output=8_000,
        supports_tools=False,
        notes="Chain-of-thought reasoning model — strong at math & code",
    ),
    ModelDef(
        id="deepseek-coder",
        name="DeepSeek Coder",
        provider="deepseek",
        context=16_000,
        max_output=4_000,
        supports_tools=True,
        notes="Code-specialised model",
    ),
]

# ─────────────────────────────────────────────
#  Unified Registry
# ─────────────────────────────────────────────

ALL_MODELS: list[ModelDef] = (
    NVIDIA_MODELS
    + GOOGLE_MODELS
    + GROQ_MODELS
    + DEEPSEEK_MODELS
)

MODELS_BY_PROVIDER: dict[str, list[ModelDef]] = {
    "nvidia":   NVIDIA_MODELS,
    "google":   GOOGLE_MODELS,
    "groq":     GROQ_MODELS,
    "deepseek": DEEPSEEK_MODELS,
}

MODELS_BY_ID: dict[str, ModelDef] = {m.id: m for m in ALL_MODELS}

# Default model per provider
DEFAULT_MODELS: dict[str, str] = {
    "nvidia":   "meta/llama-3.1-405b-instruct",
    "google":   "gemini-2.0-flash",
    "groq":     "llama-3.3-70b-versatile",
    "deepseek": "deepseek-chat",
}

# Alias map for short-hand model names
MODEL_ALIASES: dict[str, str] = {
    # NVIDIA
    "llama405b":   "meta/llama-3.1-405b-instruct",
    "llama70b":    "meta/llama-3.1-70b-instruct",
    "llama8b":     "meta/llama-3.1-8b-instruct",
    "nemotron":    "nvidia/llama-3.1-nemotron-70b-instruct",
    "qwencoder":   "qwen/qwen2.5-coder-32b-instruct",
    "kimi":        "moonshotai/kimi-k2-instruct",
    # Google
    "gemini-pro":  "gemini-1.5-pro",
    "gemini-flash":"gemini-2.0-flash",
    # Groq
    "mixtral":     "mixtral-8x7b-32768",
    "groq-fast":   "llama-3.1-8b-instant",
    "scout":       "meta-llama/llama-4-scout-17b-16e-instruct",
    # DeepSeek
    "deepseek":    "deepseek-chat",
    "r1":          "deepseek-reasoner",
    "coder":       "deepseek-coder",
}


# ─────────────────────────────────────────────
#  Lookup Functions
# ─────────────────────────────────────────────

def get_model(model_id: str) -> Optional[ModelDef]:
    """
    Resolve a model by its full ID or an alias.

    Args:
        model_id: Model ID string or alias key.

    Returns:
        ModelDef if found, else None.
    """
    # Direct lookup
    if model_id in MODELS_BY_ID:
        return MODELS_BY_ID[model_id]
    # Alias lookup
    resolved = MODEL_ALIASES.get(model_id.lower())
    if resolved:
        return MODELS_BY_ID.get(resolved)
    return None


def list_models(provider: Optional[str] = None) -> list[ModelDef]:
    """
    List all models, optionally filtered by provider.

    Args:
        provider: Optional provider name to filter.

    Returns:
        List of ModelDef objects.
    """
    if provider is None:
        return ALL_MODELS
    return MODELS_BY_PROVIDER.get(provider.lower(), [])


def get_default_model(provider: str) -> str:
    """
    Return the default model ID for a given provider.

    Args:
        provider: Provider name.

    Returns:
        Model ID string.

    Raises:
        ValueError: If provider is unknown.
    """
    p = provider.lower()
    if p not in DEFAULT_MODELS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Choose from: {list(DEFAULT_MODELS.keys())}"
        )
    return DEFAULT_MODELS[p]


def validate_model(provider: str, model_id: str) -> bool:
    """
    Check whether a model ID is valid for the given provider.

    Args:
        provider: Provider name.
        model_id: Model ID to check.

    Returns:
        True if valid, False otherwise.
    """
    provider_models = MODELS_BY_PROVIDER.get(provider.lower(), [])
    valid_ids = {m.id for m in provider_models}
    resolved = MODEL_ALIASES.get(model_id.lower(), model_id)
    return resolved in valid_ids


def models_as_dicts(provider: Optional[str] = None) -> list[dict]:
    """Return model definitions as plain dicts (for display/serialisation)."""
    return [m.as_dict() for m in list_models(provider)]


SUPPORTED_PROVIDERS: list[str] = list(MODELS_BY_PROVIDER.keys())
