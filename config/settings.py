"""
config/settings.py — Vega CLI Settings Manager
Loads and saves ~/.vega/config.json with typed defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

# ─────────────────────────────────────────────
#  Paths
# ─────────────────────────────────────────────

VEGA_DIR     = Path.home() / ".vega"
CONFIG_FILE  = VEGA_DIR / "config.json"
HISTORY_FILE = VEGA_DIR / "history.jsonl"
LOG_FILE     = VEGA_DIR / "vega.log"

# ─────────────────────────────────────────────
#  Default Configuration
# ─────────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    # Active provider ("nvidia" | "google" | "groq" | "deepseek")
    "provider": "nvidia",

    # First launch wizard indicator
    "first_run": True,

    # Active model ID (resolved against models.py)
    "model": "meta/llama-3.1-405b-instruct",

    # API keys (populated via `vega config set`)
    "api_keys": {
        "nvidia":   "",
        "google":   "",
        "groq":     "",
        "deepseek": "",
    },

    # Chat behaviour
    "stream":            True,   # Stream tokens in real-time
    "temperature":       0.7,
    "max_tokens":        4096,
    "system_prompt":     (
        "You are Vega, an expert AI coding assistant built by Raimic Labs. "
        "You write clean, efficient, production-ready code. "
        "Be concise, precise, and always prefer working examples."
    ),

    # Builder / agent behaviour
    "auto_write_files":  False,  # Write generated files to disk automatically
    "confirm_writes":    True,   # Ask before writing files when auto_write_files=True
    "output_dir":        ".",    # Default output directory for generated projects

    # UI
    "theme":             "cyan",
    "show_logo":         True,
    "show_token_count":  True,

    # Telemetry (off by default)
    "telemetry":         False,
}

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _ensure_vega_dir() -> None:
    """Create ~/.vega/ and its subdirectories if they don't exist."""
    VEGA_DIR.mkdir(parents=True, exist_ok=True)
    (VEGA_DIR / "sessions").mkdir(exist_ok=True)
    (VEGA_DIR / "exports").mkdir(exist_ok=True)


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge *override* into *base*.
    Keys in *override* take precedence; missing keys are filled from *base*.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ─────────────────────────────────────────────
#  Core API
# ─────────────────────────────────────────────

def load() -> dict[str, Any]:
    """
    Load configuration from ~/.vega/config.json.

    If the file doesn't exist, creates it with DEFAULT_CONFIG.
    Missing keys in an existing file are filled from DEFAULT_CONFIG.

    Returns:
        dict: Merged configuration dictionary.
    """
    _ensure_vega_dir()

    if not CONFIG_FILE.exists():
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as fh:
            on_disk = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"[Vega] Failed to read config at {CONFIG_FILE}: {exc}"
        ) from exc

    # Merge so new defaults are always present
    merged = _deep_merge(DEFAULT_CONFIG, on_disk)

    # If merge added new keys, persist them back
    if merged != on_disk:
        save(merged)

    return merged


def save(config: dict[str, Any]) -> None:
    """
    Persist *config* to ~/.vega/config.json (pretty-printed).

    Args:
        config: Full configuration dictionary to write.
    """
    _ensure_vega_dir()
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(
            f"[Vega] Failed to write config at {CONFIG_FILE}: {exc}"
        ) from exc


def get(key: str, default: Any = None) -> Any:
    """
    Read a single top-level key from the config.

    Args:
        key:     Config key name.
        default: Value returned if the key is absent.

    Returns:
        The stored value, or *default*.
    """
    cfg = load()
    return cfg.get(key, default)


def set_value(key: str, value: Any) -> None:
    """
    Update a single top-level key and persist to disk.

    Args:
        key:   Config key name.
        value: New value (must be JSON-serialisable).
    """
    cfg = load()
    cfg[key] = value
    save(cfg)


def set_api_key(provider: str, api_key: str) -> None:
    """
    Store an API key for a given provider.

    Args:
        provider: One of "nvidia", "google", "groq", "deepseek".
        api_key:  The API key string.
    """
    cfg = load()
    if "api_keys" not in cfg or not isinstance(cfg["api_keys"], dict):
        cfg["api_keys"] = {}
    cfg["api_keys"][provider.lower()] = api_key
    save(cfg)


def get_api_key(provider: str) -> str:
    """
    Retrieve the API key for a provider.

    Resolution order:
      1. Environment variable  VEGA_<PROVIDER>_API_KEY  (e.g. VEGA_NVIDIA_API_KEY)
      2. ~/.vega/config.json   api_keys.<provider>
      3. Generic env var       <PROVIDER>_API_KEY        (e.g. NVIDIA_API_KEY)

    Args:
        provider: Provider name (case-insensitive).

    Returns:
        API key string, or "" if not found.
    """
    p = provider.upper()

    # 1. Vega-namespaced env var
    env_vega = os.environ.get(f"VEGA_{p}_API_KEY", "")
    if env_vega:
        return env_vega

    # 2. Config file
    cfg = load()
    key_from_cfg: str = cfg.get("api_keys", {}).get(provider.lower(), "")
    if key_from_cfg:
        return key_from_cfg

    # 3. Generic env var
    env_generic = os.environ.get(f"{p}_API_KEY", "")
    return env_generic


def reset() -> None:
    """
    Reset configuration to defaults (overwrites ~/.vega/config.json).
    """
    save(DEFAULT_CONFIG.copy())


def get_active_provider() -> str:
    """Return the currently active provider name."""
    return str(get("provider", DEFAULT_CONFIG["provider"]))


def get_active_model() -> str:
    """Return the currently active model ID."""
    return str(get("model", DEFAULT_CONFIG["model"]))


def set_active_provider(provider: str) -> None:
    """Set the active provider and persist."""
    set_value("provider", provider.lower())


def set_active_model(model_id: str) -> None:
    """Set the active model ID and persist."""
    set_value("model", model_id)


def as_dict() -> dict[str, Any]:
    """Return a flattened dict of key settings for display."""
    cfg = load()
    return {
        "provider":        cfg.get("provider"),
        "model":           cfg.get("model"),
        "stream":          cfg.get("stream"),
        "temperature":     cfg.get("temperature"),
        "max_tokens":      cfg.get("max_tokens"),
        "auto_write_files":cfg.get("auto_write_files"),
        "confirm_writes":  cfg.get("confirm_writes"),
        "output_dir":      cfg.get("output_dir"),
        "show_logo":       cfg.get("show_logo"),
        "show_token_count":cfg.get("show_token_count"),
        "telemetry":       cfg.get("telemetry"),
        "config_file":     str(CONFIG_FILE),
    }
def fallback_provider(current_provider: str) -> bool:
    """
    Finds a fallback provider with an API key, sets it as active,
    and returns True if a fallback was successfully set.
    """
    from providers import SUPPORTED_PROVIDERS
    from config import models as mdl
    for p in SUPPORTED_PROVIDERS:
        if p != current_provider:
            api_key = get_api_key(p)
            if api_key:
                set_active_provider(p)
                default_model = mdl.get_default_model(p)
                set_active_model(default_model)
                return True
    return False


# ─────────────────────────────────────────────
#  CLI-friendly wrapper
# ─────────────────────────────────────────────

class Settings:
    """
    Object-oriented wrapper around the settings functions.

    Provides attribute-style access to a loaded config snapshot.

    Usage:
        s = Settings()
        print(s.provider)       # "nvidia"
        s.set("model", "...")
    """

    def __init__(self) -> None:
        self._cfg: dict[str, Any] = load()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._cfg.get(name)

    def reload(self) -> "Settings":
        self._cfg = load()
        return self

    def set(self, key: str, value: Any) -> None:
        set_value(key, value)
        self._cfg[key] = value

    def to_dict(self) -> dict[str, Any]:
        return self._cfg.copy()

    @property
    def api_key(self) -> str:
        return get_api_key(self.provider or "nvidia")

    def __repr__(self) -> str:
        return f"<Settings provider={self.provider!r} model={self.model!r}>"
