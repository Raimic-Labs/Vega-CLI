"""
vega/router.py — Intent router
Classifies raw user input and dispatches to the right handler:
  - /commands  → command handler
  - build/make requests → builder mode
  - everything else → chat mode
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vega.agents import AgentInfo

# ─────────────────────────────────────────────
#  Intent types
# ─────────────────────────────────────────────

class Intent(Enum):
    CHAT         = auto()   # Regular conversational message
    BUILD        = auto()   # "Build me a …" / project generation
    CMD_HELP     = auto()   # /help
    CMD_EXIT     = auto()   # /exit | /quit | /bye
    CMD_CLEAR    = auto()   # /clear
    CMD_MODEL    = auto()   # /model [name]
    CMD_PROVIDER = auto()   # /provider [name]
    CMD_MODELS   = auto()   # /models
    CMD_CONFIG   = auto()   # /config [key] [value]
    CMD_HISTORY  = auto()   # /history
    CMD_EXPORT   = auto()   # /export
    CMD_RESET    = auto()   # /reset
    CMD_TOKENS   = auto()   # /tokens
    CMD_SYSTEM   = auto()   # /system [prompt]
    CMD_AGENT    = auto()   # /agent
    UNKNOWN_CMD  = auto()   # /something unrecognised


@dataclass
class RouteResult:
    intent:    Intent
    raw:       str             # original user input
    command:   Optional[str]   # slash command without leading /
    args:      list[str]       # tokens after the command
    remainder: str             # everything after command + first arg
    agent:     Optional[AgentInfo] = None


# ─────────────────────────────────────────────
#  Build-intent keywords
# ─────────────────────────────────────────────

_BUILD_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"^build\s+(me\s+)?a\b",
        r"^create\s+(me\s+)?a\b",
        r"^make\s+(me\s+)?a\b",
        r"^generate\s+(a\s+)?(full\s+)?(project|app|website|api|cli|script|tool)\b",
        r"^scaffold\b",
        r"^init(ialize)?\s+(a\s+)?(project|repo|app)\b",
        r"^set\s+up\s+(a\s+)?",
        r"^write\s+(me\s+)?(a\s+)?(full|complete|working)\s+",
    ]
]

# ─────────────────────────────────────────────
#  Command registry
# ─────────────────────────────────────────────

_COMMAND_MAP: dict[str, Intent] = {
    "help":     Intent.CMD_HELP,
    "h":        Intent.CMD_HELP,
    "exit":     Intent.CMD_EXIT,
    "quit":     Intent.CMD_EXIT,
    "bye":      Intent.CMD_EXIT,
    "q":        Intent.CMD_EXIT,
    "clear":    Intent.CMD_CLEAR,
    "cls":      Intent.CMD_CLEAR,
    "model":    Intent.CMD_MODEL,
    "m":        Intent.CMD_MODEL,
    "provider": Intent.CMD_PROVIDER,
    "p":        Intent.CMD_PROVIDER,
    "switch":   Intent.CMD_PROVIDER,
    "models":   Intent.CMD_MODELS,
    "config":   Intent.CMD_CONFIG,
    "cfg":      Intent.CMD_CONFIG,
    "history":  Intent.CMD_HISTORY,
    "export":   Intent.CMD_EXPORT,
    "reset":    Intent.CMD_RESET,
    "tokens":   Intent.CMD_TOKENS,
    "system":   Intent.CMD_SYSTEM,
    "sys":      Intent.CMD_SYSTEM,
    "agent":    Intent.CMD_AGENT,
}

HELP_TEXT = """
╭──────────────────────────────────────────────────╮
│              Vega CLI — Commands                 │
├──────────────────────────────────────────────────┤
│  /help              Show this help message       │
│  /exit              Exit Vega                    │
│  /clear             Clear chat history           │
│  /model  [id]       Switch model                 │
│  /models            List all available models    │
│  /provider [name]   Switch provider              │
│  /config  [k] [v]   View or set config value     │
│  /system  [prompt]  Set system prompt            │
│  /history           Show conversation history    │
│  /export            Export chat to file          │
│  /tokens            Show token usage             │
│  /agent             Enter agent/build mode       │
│  /reset             Reset to default settings    │
╰──────────────────────────────────────────────────╯
  Tip: Start a message with "build me a…" to enter
  builder mode and auto-generate full projects.
"""


# ─────────────────────────────────────────────
#  Router
# ─────────────────────────────────────────────

def route(raw: str) -> RouteResult:
    """
    Classify *raw* user input and return a RouteResult.

    Routing priority:
      1. Slash commands  (/help, /model, etc.)
      2. Build-intent keywords (build me a …)
      3. Default → CHAT

    Args:
        raw: Raw user input string (may have leading/trailing whitespace).

    Returns:
        RouteResult with resolved intent and parsed args.
    """
    text = raw.strip()

    # ── 1. Slash commands ─────────────────────
    if text.startswith("/"):
        parts   = text[1:].split()
        cmd     = parts[0].lower() if parts else ""
        args    = parts[1:] if len(parts) > 1 else []
        rest    = " ".join(args)
        intent  = _COMMAND_MAP.get(cmd, Intent.UNKNOWN_CMD)
        return RouteResult(
            intent    = intent,
            raw       = raw,
            command   = cmd,
            args      = args,
            remainder = rest,
        )

    # ── 2. Build-intent ───────────────────────
    from vega.agents import detect_agent
    agent = detect_agent(text)

    for pattern in _BUILD_PATTERNS:
        if pattern.search(text):
            return RouteResult(
                intent    = Intent.BUILD,
                raw       = raw,
                command   = None,
                args      = [],
                remainder = text,
                agent     = agent,
            )

    # ── 3. Default chat ───────────────────────
    return RouteResult(
        intent    = Intent.CHAT,
        raw       = raw,
        command   = None,
        args      = [],
        remainder = text,
        agent     = agent,
    )


def is_exit(result: RouteResult) -> bool:
    return result.intent == Intent.CMD_EXIT


def is_command(result: RouteResult) -> bool:
    return result.intent not in (Intent.CHAT, Intent.BUILD)
