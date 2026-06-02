"""
config/__init__.py — Config package
Re-exports the most commonly used functions from settings and models.
"""

from config.settings import (
    load,
    save,
    get,
    set_value,
    set_api_key,
    get_api_key,
    reset,
    get_active_provider,
    get_active_model,
    set_active_provider,
    set_active_model,
    as_dict,
    Settings,
    CONFIG_FILE,
    VEGA_DIR,
)

from config.models import (
    ModelDef,
    ALL_MODELS,
    MODELS_BY_PROVIDER,
    MODELS_BY_ID,
    DEFAULT_MODELS,
    MODEL_ALIASES,
    SUPPORTED_PROVIDERS,
    get_model,
    list_models,
    get_default_model,
    validate_model,
    models_as_dicts,
)

__all__ = [
    # settings
    "load", "save", "get", "set_value",
    "set_api_key", "get_api_key", "reset",
    "get_active_provider", "get_active_model",
    "set_active_provider", "set_active_model",
    "as_dict", "Settings", "CONFIG_FILE", "VEGA_DIR",
    # models
    "ModelDef", "ALL_MODELS", "MODELS_BY_PROVIDER",
    "MODELS_BY_ID", "DEFAULT_MODELS", "MODEL_ALIASES",
    "SUPPORTED_PROVIDERS", "get_model", "list_models",
    "get_default_model", "validate_model", "models_as_dicts",
]
