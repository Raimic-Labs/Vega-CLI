"""
tests/test_router.py — Unit tests for the intent router.
"""

import pytest
from vega.router import route, Intent, is_exit, is_command


# ─────────────────────────────────────────────
#  Slash command routing
# ─────────────────────────────────────────────

class TestSlashCommands:
    def test_help(self):
        r = route("/help")
        assert r.intent == Intent.CMD_HELP
        assert r.command == "help"

    def test_help_alias(self):
        assert route("/h").intent == Intent.CMD_HELP

    def test_exit(self):
        r = route("/exit")
        assert r.intent == Intent.CMD_EXIT
        assert is_exit(r)

    def test_quit_alias(self):
        assert route("/quit").intent == Intent.CMD_EXIT
        assert route("/q").intent == Intent.CMD_EXIT
        assert route("/bye").intent == Intent.CMD_EXIT

    def test_clear(self):
        assert route("/clear").intent == Intent.CMD_CLEAR
        assert route("/cls").intent == Intent.CMD_CLEAR

    def test_model_no_args(self):
        r = route("/model")
        assert r.intent == Intent.CMD_MODEL
        assert r.args == []

    def test_model_with_arg(self):
        r = route("/model gpt-4o")
        assert r.intent == Intent.CMD_MODEL
        assert r.args == ["gpt-4o"]

    def test_model_alias(self):
        assert route("/m deepseek-chat").intent == Intent.CMD_MODEL

    def test_provider(self):
        r = route("/provider nvidia")
        assert r.intent == Intent.CMD_PROVIDER
        assert r.args == ["nvidia"]

    def test_provider_alias(self):
        assert route("/p groq").intent == Intent.CMD_PROVIDER

    def test_switch_alias(self):
        assert route("/switch").intent == Intent.CMD_PROVIDER

    def test_models(self):
        assert route("/models").intent == Intent.CMD_MODELS

    def test_config_no_args(self):
        r = route("/config")
        assert r.intent == Intent.CMD_CONFIG
        assert r.args == []

    def test_config_key_value(self):
        r = route("/config temperature 0.9")
        assert r.intent == Intent.CMD_CONFIG
        assert r.args == ["temperature", "0.9"]

    def test_config_alias(self):
        assert route("/cfg").intent == Intent.CMD_CONFIG

    def test_history(self):
        assert route("/history").intent == Intent.CMD_HISTORY

    def test_export(self):
        r = route("/export my-file.md")
        assert r.intent == Intent.CMD_EXPORT
        assert "my-file.md" in r.remainder

    def test_reset(self):
        assert route("/reset").intent == Intent.CMD_RESET

    def test_tokens(self):
        assert route("/tokens").intent == Intent.CMD_TOKENS

    def test_system_no_args(self):
        r = route("/system")
        assert r.intent == Intent.CMD_SYSTEM
        assert r.remainder == ""

    def test_system_with_prompt(self):
        r = route("/system You are a Python expert.")
        assert r.intent == Intent.CMD_SYSTEM
        assert "Python expert" in r.remainder

    def test_system_alias(self):
        assert route("/sys prompt").intent == Intent.CMD_SYSTEM

    def test_agent(self):
        r = route("/agent build a todo app")
        assert r.intent == Intent.CMD_AGENT
        assert "todo" in r.remainder

    def test_unknown_command(self):
        r = route("/foobar")
        assert r.intent == Intent.UNKNOWN_CMD
        assert r.command == "foobar"

    def test_is_command_true(self):
        assert is_command(route("/help"))
        assert is_command(route("/model gpt-4"))
        assert is_command(route("/exit"))

    def test_is_command_false_for_chat(self):
        assert not is_command(route("hello, how are you?"))

    def test_is_command_false_for_build(self):
        assert not is_command(route("build me a todo app"))


# ─────────────────────────────────────────────
#  Build intent routing
# ─────────────────────────────────────────────

class TestBuildIntent:
    def test_build_me_a(self):
        r = route("build me a portfolio website")
        assert r.intent == Intent.BUILD

    def test_create_me_a(self):
        r = route("create me a CLI tool in Python")
        assert r.intent == Intent.BUILD

    def test_make_me_a(self):
        r = route("make me a REST API with Flask")
        assert r.intent == Intent.BUILD

    def test_generate_a_project(self):
        r = route("generate a full project for a todo app")
        assert r.intent == Intent.BUILD

    def test_scaffold(self):
        r = route("scaffold a new React app")
        assert r.intent == Intent.BUILD

    def test_build_without_me(self):
        r = route("build a fastapi app")
        assert r.intent == Intent.BUILD

    def test_write_complete(self):
        r = route("write me a complete Python web scraper")
        assert r.intent == Intent.BUILD


# ─────────────────────────────────────────────
#  Chat intent routing
# ─────────────────────────────────────────────

class TestChatIntent:
    def test_plain_question(self):
        r = route("what is a REST API?")
        assert r.intent == Intent.CHAT

    def test_greeting(self):
        r = route("hello there")
        assert r.intent == Intent.CHAT

    def test_explain_request(self):
        r = route("explain async/await in Python")
        assert r.intent == Intent.CHAT

    def test_empty_ish_input(self):
        r = route("  ")  # spaces
        assert r.intent == Intent.CHAT

    def test_raw_is_preserved(self):
        raw = "  hello world  "
        r = route(raw)
        assert r.raw == raw

    def test_remainder_is_stripped(self):
        r = route("  hello world  ")
        # remainder for CHAT is the stripped text
        assert r.remainder == "hello world"


# ─────────────────────────────────────────────
#  RouteResult fields
# ─────────────────────────────────────────────

class TestRouteResultFields:
    def test_args_parsed(self):
        r = route("/model gemini-2.0-flash")
        assert r.args == ["gemini-2.0-flash"]

    def test_remainder_multi_word(self):
        r = route("/system You are a helpful assistant")
        assert r.remainder == "You are a helpful assistant"

    def test_command_lowercase(self):
        r = route("/HELP")
        assert r.command == "help"
        assert r.intent == Intent.CMD_HELP

    def test_mixed_case_command(self):
        r = route("/Model gpt-4")
        assert r.command == "model"
