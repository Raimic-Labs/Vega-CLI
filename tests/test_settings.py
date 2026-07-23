"""
tests/test_settings.py — Unit tests for config/settings.py
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _patch_vega_dir(tmp_path: Path):
    """Return context manager patches that redirect ~/.vega to tmp_path."""
    config_file = tmp_path / "config.json"
    return (
        patch("config.settings.VEGA_DIR", tmp_path),
        patch("config.settings.CONFIG_FILE", config_file),
        patch("config.settings.HISTORY_FILE", tmp_path / "history.jsonl"),
        patch("config.settings.LOG_FILE", tmp_path / "vega.log"),
    )


# ─────────────────────────────────────────────
#  load() — creates file on first run
# ─────────────────────────────────────────────

class TestLoad:
    def test_creates_config_on_first_run(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        patches = _patch_vega_dir(tmp_path)
        with patches[0], patches[1], patches[2], patches[3]:
            import config.settings as s
            # Force module-level reload of patched paths
            s.VEGA_DIR = tmp_path
            s.CONFIG_FILE = cfg_file
            result = s.load()

        assert cfg_file.exists()
        assert "provider" in result
        assert "api_keys" in result

    def test_returns_defaults_on_empty(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        import config.settings as s
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            result = s.load()

        assert result["provider"] == "nvidia"
        assert result["first_run"] is True

    def test_merges_missing_keys(self, tmp_path):
        """Keys missing from disk config are filled from DEFAULT_CONFIG."""
        cfg_file = tmp_path / "config.json"
        # Write a partial config
        cfg_file.write_text(json.dumps({"provider": "groq"}))

        import config.settings as s
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            result = s.load()

        assert result["provider"] == "groq"          # preserved
        assert "api_keys" in result                  # merged in
        assert "temperature" in result               # merged in

    def test_raises_on_corrupt_json(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("{invalid json}")

        import config.settings as s
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            with pytest.raises(RuntimeError, match="Failed to read config"):
                s.load()


# ─────────────────────────────────────────────
#  get_api_key() — env var resolution order
# ─────────────────────────────────────────────

class TestGetApiKey:
    def test_env_vega_namespaced_wins(self, tmp_path):
        import config.settings as s
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", tmp_path / "config.json"), \
             patch.dict(os.environ, {"VEGA_NVIDIA_API_KEY": "nvapi-env-key"}):
            result = s.get_api_key("nvidia")
        assert result == "nvapi-env-key"

    def test_config_file_fallback(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({
            **s.DEFAULT_CONFIG,
            "api_keys": {"nvidia": "nvapi-from-config"},
        }))
        # No env var set
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file), \
             patch.dict(os.environ, {}, clear=False):
            # Remove VEGA_NVIDIA_API_KEY if present
            env = {k: v for k, v in os.environ.items() if "NVIDIA" not in k}
            with patch.dict(os.environ, env, clear=True):
                result = s.get_api_key("nvidia")
        assert result == "nvapi-from-config"

    def test_empty_string_when_not_set(self, tmp_path):
        import config.settings as s
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", tmp_path / "config.json"), \
             patch.dict(os.environ, {}, clear=True):
            result = s.get_api_key("nvidia")
        assert result == ""

    def test_case_insensitive_provider(self, tmp_path):
        import config.settings as s
        with patch.dict(os.environ, {"VEGA_GROQ_API_KEY": "gsk-test"}):
            result = s.get_api_key("groq")
        assert result == "gsk-test"


# ─────────────────────────────────────────────
#  set_value() / get()
# ─────────────────────────────────────────────

class TestSetGet:
    def test_set_and_get(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_value("temperature", 0.95)
            result = s.get("temperature")
        assert result == 0.95

    def test_get_missing_key_returns_default(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            result = s.get("nonexistent_key", "default_val")
        assert result == "default_val"

    def test_set_persists_to_disk(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_value("max_tokens", 8192)
            # Re-read from disk
            on_disk = json.loads(cfg_file.read_text())
        assert on_disk["max_tokens"] == 8192


# ─────────────────────────────────────────────
#  set_api_key()
# ─────────────────────────────────────────────

class TestSetApiKey:
    def test_saves_api_key(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_api_key("nvidia", "nvapi-test-123")
            on_disk = json.loads(cfg_file.read_text())
        assert on_disk["api_keys"]["nvidia"] == "nvapi-test-123"

    def test_saves_multiple_providers(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_api_key("google", "AIza-abc")
            s.set_api_key("groq", "gsk-xyz")
            on_disk = json.loads(cfg_file.read_text())
        assert on_disk["api_keys"]["google"] == "AIza-abc"
        assert on_disk["api_keys"]["groq"] == "gsk-xyz"


# ─────────────────────────────────────────────
#  Active provider / model
# ─────────────────────────────────────────────

class TestActiveProviderModel:
    def test_set_get_active_provider(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_active_provider("groq")
            assert s.get_active_provider() == "groq"

    def test_set_get_active_model(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_active_model("deepseek-chat")
            assert s.get_active_model() == "deepseek-chat"


# ─────────────────────────────────────────────
#  reset()
# ─────────────────────────────────────────────

class TestReset:
    def test_reset_restores_defaults(self, tmp_path):
        import config.settings as s
        cfg_file = tmp_path / "config.json"
        with patch.object(s, "VEGA_DIR", tmp_path), \
             patch.object(s, "CONFIG_FILE", cfg_file):
            s.set_value("temperature", 1.5)
            s.reset()
            on_disk = json.loads(cfg_file.read_text())
        assert on_disk["temperature"] == s.DEFAULT_CONFIG["temperature"]


# ─────────────────────────────────────────────
#  _deep_merge()
# ─────────────────────────────────────────────

class TestDeepMerge:
    def test_basic_merge(self):
        from config.settings import _deep_merge
        base = {"a": 1, "b": 2}
        override = {"b": 99, "c": 3}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_nested_merge(self):
        from config.settings import _deep_merge
        base = {"api_keys": {"nvidia": "old", "google": "old"}}
        override = {"api_keys": {"nvidia": "new"}}
        result = _deep_merge(base, override)
        assert result["api_keys"]["nvidia"] == "new"
        assert result["api_keys"]["google"] == "old"

    def test_base_not_mutated(self):
        from config.settings import _deep_merge
        base = {"a": 1}
        override = {"b": 2}
        _deep_merge(base, override)
        assert "b" not in base
