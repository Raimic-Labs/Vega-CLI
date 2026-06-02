"""
vega/chat.py — Chat session manager
Maintains conversation history, streams AI responses,
handles token counting, and persists sessions to disk.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from providers.base import BaseProvider, Message, StreamChunk
from vega.agents import AgentInfo
from vega.display import (
    console,
    print_user_message,
    print_ai_message,
    spinner,
    ok,
    fail,
    info,
    dim,
    rule,
)

# ─────────────────────────────────────────────
#  Session storage
# ─────────────────────────────────────────────

SESSIONS_DIR = Path.home() / ".vega" / "sessions"


def _session_path(session_id: str) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR / f"{session_id}.jsonl"


# ─────────────────────────────────────────────
#  Chat session
# ─────────────────────────────────────────────

class ChatSession:
    """
    Manages a single multi-turn conversation with an LLM provider.

    Responsibilities:
      - Maintains message history (list[Message])
      - Streams and prints AI responses token-by-token
      - Tracks token usage across turns
      - Saves / loads sessions from ~/.vega/sessions/<id>.jsonl
    """

    def __init__(
        self,
        provider:      BaseProvider,
        system_prompt: Optional[str] = None,
        session_id:    Optional[str] = None,
        show_tokens:   bool = True,
    ) -> None:
        self.provider      = provider
        self.show_tokens   = show_tokens
        self.session_id    = session_id or str(uuid.uuid4())
        self.created_at    = datetime.utcnow().isoformat()
        self.history:      list[Message] = []
        self.total_input   = 0
        self.total_output  = 0
        self._turn_count   = 0

        if system_prompt:
            self.history.append(Message(role="system", content=system_prompt))

    # ── Public API ────────────────────────────

    def send(self, user_text: str, agent: Optional[AgentInfo] = None) -> str:
        """
        Add user message, stream AI response, return full reply text.

        Args:
            user_text: The user's message string.
            agent: Optional AgentInfo if an agent is routed.

        Returns:
            The complete AI response as a string.
        """
        user_msg = Message(role="user", content=user_text)
        self.history.append(user_msg)
        self._turn_count += 1

        print_user_message(user_text)

        reply, elapsed = self._stream_response(agent=agent)

        self.history.append(Message(role="assistant", content=reply))
        self._save_turn(user_msg, reply, elapsed)

        if self.show_tokens:
            self._print_token_status(elapsed, len(reply.split()))

        return reply

    def send_silent(self, user_text: str) -> str:
        """
        Send a message and collect the reply without printing to screen.
        Useful for agent sub-calls.

        Args:
            user_text: User message text.

        Returns:
            AI reply text.
        """
        self.history.append(Message(role="user", content=user_text))
        parts: list[str] = []
        start = time.perf_counter()
        for chunk in self.provider.stream_with_retry(self.history):
            if chunk.text:
                parts.append(chunk.text)
        elapsed = time.perf_counter() - start
        reply   = "".join(parts)
        self.history.append(Message(role="assistant", content=reply))
        return reply

    def clear(self) -> None:
        """Clear history, keeping only the system prompt if present."""
        system = [m for m in self.history if m.role == "system"]
        self.history    = system
        self._turn_count = 0
        self.total_input  = 0
        self.total_output = 0
        ok("Chat history cleared.")

    def set_system_prompt(self, prompt: str) -> None:
        """Replace or set the system prompt in history."""
        self.history = [m for m in self.history if m.role != "system"]
        self.history.insert(0, Message(role="system", content=prompt))
        ok("System prompt updated.")

    def switch_provider(self, new_provider: BaseProvider) -> None:
        """Hot-swap the provider mid-session (history is preserved)."""
        self.provider = new_provider
        info(f"Switched to {new_provider.name} / {new_provider.model}")

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def context_messages(self) -> list[Message]:
        """Return only non-system messages (user + assistant)."""
        return [m for m in self.history if m.role != "system"]

    # ── Streaming internals ───────────────────

    def _stream_response(self, agent: Optional[AgentInfo] = None) -> tuple[str, float]:
        """
        Stream the AI response token-by-token and return (full_text, elapsed_s).
        Renders each token live to the terminal.
        """
        from rich.live import Live
        from rich.text import Text
        from rich.panel import Panel
        from rich import box
        from config import settings as cfg
        from providers import get_provider

        parts:  list[str] = []
        start = time.perf_counter()

        provider_to_use = self.provider
        temp_provider = None

        if agent:
            # Check if agent's provider has configured API key
            agent_api_key = cfg.get_api_key(agent.provider_name)
            if agent_api_key:
                try:
                    temp_provider = get_provider(
                        provider_name = agent.provider_name,
                        api_key       = agent_api_key,
                        model         = agent.model_id,
                        system_prompt = self.provider.system_prompt,
                    )
                    provider_to_use = temp_provider
                except Exception:
                    pass

        if agent:
            model_label = f"{agent.badge} {agent.name}"
        else:
            model_label = f"✦ {provider_to_use.model}"

        if temp_provider and self.provider != temp_provider:
            dim(f"  Routed to {agent.name} ({agent.model_id})")

        try:
            # We manually manage Live rendering to stream inside a panel
            with Live(
                _render_ai_panel("", model_label),
                console       = console,
                refresh_per_second = 15,
                transient     = False,
            ) as live:
                for chunk in provider_to_use.stream_with_retry(self.history):
                    if chunk.text:
                        parts.append(chunk.text)
                        assembled = "".join(parts)
                        live.update(_render_ai_panel(assembled, model_label))

        except KeyboardInterrupt:
            # Allow graceful abort mid-stream
            assembled = "".join(parts)
            if not assembled:
                assembled = "[interrupted]"
            dim("  ⚡ Interrupted by user.")

        except Exception as exc:  # noqa: BLE001
            fail(f"Stream error: {exc}")
            assembled = "".join(parts)

        elapsed  = time.perf_counter() - start
        full_text = "".join(parts)
        return full_text, elapsed

    # ── Session persistence ───────────────────

    def _save_turn(
        self,
        user_msg: Message,
        reply:    str,
        elapsed:  float,
    ) -> None:
        """Append this turn to the session JSONL file."""
        try:
            record = {
                "turn":       self._turn_count,
                "ts":         datetime.utcnow().isoformat(),
                "provider":   self.provider.name,
                "model":      self.provider.model,
                "user":       user_msg.content,
                "assistant":  reply,
                "elapsed_s":  round(elapsed, 3),
            }
            with _session_path(self.session_id).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass   # Non-fatal — don't crash the chat

    def save(self) -> Path:
        """Force-save session metadata and return path."""
        meta = {
            "session_id":  self.session_id,
            "created_at":  self.created_at,
            "provider":    self.provider.name,
            "model":       self.provider.model,
            "turns":       self._turn_count,
            "saved_at":    datetime.utcnow().isoformat(),
        }
        path = _session_path(self.session_id)
        ok(f"Session saved → {path}")
        return path

    @classmethod
    def load(
        cls,
        session_id: str,
        provider:   BaseProvider,
    ) -> "ChatSession":
        """
        Restore a previous session from ~/.vega/sessions/<id>.jsonl.

        Args:
            session_id: UUID string of the session to restore.
            provider:   Provider instance to attach (may differ from original).

        Returns:
            ChatSession with history populated from disk.
        """
        path = _session_path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        session = cls(provider=provider, session_id=session_id)
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    session.history.append(
                        Message(role="user", content=record["user"])
                    )
                    session.history.append(
                        Message(role="assistant", content=record["assistant"])
                    )
                    session._turn_count += 1
                except (json.JSONDecodeError, KeyError):
                    continue

        info(f"Loaded session {session_id} ({session._turn_count} turns)")
        return session

    @staticmethod
    def list_sessions() -> list[dict]:
        """List all saved sessions from ~/.vega/sessions/."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        sessions: list[dict] = []
        for f in sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
            turns = sum(1 for _ in f.open() if _.strip())
            sessions.append({
                "id":       f.stem,
                "turns":    turns,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size":     f"{f.stat().st_size // 1024}KB" if f.stat().st_size > 1024 else f"{f.stat().st_size}B",
            })
        return sessions

    # ── Formatting helpers ────────────────────

    def _print_token_status(self, elapsed: float, approx_words: int) -> None:
        approx_toks  = int(approx_words * 1.35)
        self.total_output += approx_toks
        tps  = approx_toks / elapsed if elapsed > 0 else 0
        dim(f"  ⏱  {elapsed:.1f}s  ·  ~{approx_toks} tokens  ·  {tps:.0f} tok/s")

    def __repr__(self) -> str:
        return (
            f"<ChatSession id={self.session_id[:8]}… "
            f"provider={self.provider.name} "
            f"turns={self._turn_count}>"
        )


# ─────────────────────────────────────────────
#  Render helper (used inside stream loop)
# ─────────────────────────────────────────────

def _render_ai_panel(text: str, model_label: str):
    """Build a Rich panel for the live-updating AI response."""
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    label = Text(f"  {model_label}  ", style="bold black on bright_cyan")
    return Panel(
        Markdown(text) if text else Text("…", style="dim cyan"),
        title        = label,
        title_align  = "left",
        border_style = "bright_cyan",
        padding      = (0, 2),
        box          = box.ROUNDED,
    )


# ─────────────────────────────────────────────
#  Export helpers
# ─────────────────────────────────────────────

def export_session_markdown(session: ChatSession, output_path: Optional[Path] = None) -> Path:
    """
    Export a session to a Markdown file.

    Args:
        session:     The ChatSession to export.
        output_path: Destination path (auto-generated if None).

    Returns:
        Path to the written file.
    """
    if output_path is None:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"vega_export_{ts}.md")

    lines = [
        f"# Vega Chat Export",
        f"",
        f"**Session**: `{session.session_id}`  ",
        f"**Provider**: {session.provider.name} / `{session.provider.model}`  ",
        f"**Turns**: {session.turn_count}  ",
        f"**Exported**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        "---",
        "",
    ]

    for msg in session.history:
        if msg.role == "system":
            lines += [f"> **System:** {msg.content}", ""]
        elif msg.role == "user":
            lines += [f"## 🧑 You", "", msg.content, ""]
        elif msg.role == "assistant":
            lines += [f"## ✦ Vega", "", msg.content, ""]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    ok(f"Exported → {output_path}")
    return output_path


# ─────────────────────────────────────────────
#  Interactive REPL loop
# ─────────────────────────────────────────────

def run_chat_loop(
    session:      ChatSession,
    show_welcome: bool = True,
) -> None:
    """
    Start the interactive Vega chat REPL.

    Reads user input, routes slash commands, and streams AI responses.
    Exits cleanly on /exit, EOF (Ctrl-D), or KeyboardInterrupt (Ctrl-C).

    Args:
        session:      An initialised ChatSession.
        show_welcome: Print the welcome hint on entry.
    """
    from vega.router import route, Intent, is_exit, HELP_TEXT, is_command
    from config import models as model_registry
    from providers import get_provider, SUPPORTED_PROVIDERS
    from config import settings as cfg_mod
    from rich.text import Text
    from rich.prompt import Prompt

    if show_welcome:
        console.print()
        console.print(
            Text.assemble(
                ("  ✦ Vega ", "bold bright_cyan"),
                ("is ready. ", "cyan"),
                ("Type ", "dim"),
                ("/help", "bold cyan"),
                (" for commands.", "dim"),
            )
        )
        console.print()

    while True:
        # ── Read input ────────────────────────
        try:
            raw = console.input(
                Text.assemble(
                    ("\n  ✦ › ", "bold cyan"),
                ).markup
            ).strip()
        except EOFError:
            # Ctrl-D — clean exit
            console.print()
            ok("Goodbye! Session saved.")
            session.save()
            break
        except KeyboardInterrupt:
            console.print()
            dim("  (Use /exit to quit, or Ctrl-D)")
            continue

        if not raw:
            continue

        # ── Route ────────────────────────────
        result = route(raw)

        # ── /exit ────────────────────────────
        if is_exit(result):
            ok("Goodbye! ✦")
            session.save()
            break

        # ── /help ────────────────────────────
        elif result.intent == Intent.CMD_HELP:
            console.print(Text(HELP_TEXT, style="cyan"))

        # ── /clear ───────────────────────────
        elif result.intent == Intent.CMD_CLEAR:
            session.clear()
            console.clear()

        # ── /models ──────────────────────────
        elif result.intent == Intent.CMD_MODELS:
            from vega.display import models_table
            provider_filter = result.args[0] if result.args else None
            models_table(model_registry.models_as_dicts(provider_filter))

        # ── /model <id> ──────────────────────
        elif result.intent == Intent.CMD_MODEL:
            if not result.args:
                info(f"Current model: {session.provider.model}")
            else:
                new_model = result.args[0]
                session.provider.model = new_model
                cfg_mod.set_active_model(new_model)
                ok(f"Model → {new_model}")

        # ── /provider <name> ─────────────────
        elif result.intent == Intent.CMD_PROVIDER:
            if not result.args:
                info(f"Current provider: {session.provider.name}")
                info(f"Supported: {', '.join(SUPPORTED_PROVIDERS)}")
            else:
                new_prov = result.args[0].lower()
                if new_prov not in SUPPORTED_PROVIDERS:
                    fail(f"Unknown provider '{new_prov}'. Choose: {SUPPORTED_PROVIDERS}")
                else:
                    api_key   = cfg_mod.get_api_key(new_prov)
                    new_model = cfg_mod.get_active_model() if cfg_mod.get("provider") == new_prov \
                                else model_registry.get_default_model(new_prov)
                    try:
                        new_provider = get_provider(new_prov, api_key, new_model)
                        session.switch_provider(new_provider)
                        cfg_mod.set_active_provider(new_prov)
                        cfg_mod.set_active_model(new_model)
                    except Exception as exc:
                        fail(f"Could not switch provider: {exc}")

        # ── /system <prompt> ─────────────────
        elif result.intent == Intent.CMD_SYSTEM:
            if result.remainder:
                session.set_system_prompt(result.remainder)
            else:
                current = next((m.content for m in session.history if m.role == "system"), None)
                if current:
                    info(f"System prompt:\n  {current}")
                else:
                    dim("  No system prompt set.")

        # ── /config [key] [value] ────────────
        elif result.intent == Intent.CMD_CONFIG:
            from vega.display import config_table
            if not result.args:
                config_table(cfg_mod.as_dict())
            elif len(result.args) == 1:
                val = cfg_mod.get(result.args[0])
                info(f"{result.args[0]} = {val}")
            else:
                key, val = result.args[0], " ".join(result.args[1:])
                # Type coerce
                if val.lower() in ("true", "false"):
                    val = val.lower() == "true"
                elif val.replace(".", "", 1).lstrip("-").isdigit():
                    val = float(val) if "." in val else int(val)
                cfg_mod.set_value(key, val)
                ok(f"Config: {key} = {val}")

        # ── /history ─────────────────────────
        elif result.intent == Intent.CMD_HISTORY:
            sessions = ChatSession.list_sessions()
            if not sessions:
                dim("  No saved sessions found.")
            else:
                from vega.display import make_table
                from rich import box as rbox
                tbl = make_table(
                    title   = "Saved Sessions",
                    columns = ["ID (short)", "Turns", "Modified", "Size"],
                    col_styles = ["vega.accent", "vega.dim", "vega.secondary", "vega.dim"],
                    box_style  = rbox.ROUNDED,
                    show_lines = True,
                )
                for s in sessions:
                    tbl.add_row(s["id"][:12] + "…", str(s["turns"]), s["modified"], s["size"])
                console.print(tbl)

        # ── /export ──────────────────────────
        elif result.intent == Intent.CMD_EXPORT:
            out = result.remainder.strip() or None
            export_session_markdown(session, Path(out) if out else None)

        # ── /tokens ──────────────────────────
        elif result.intent == Intent.CMD_TOKENS:
            info(
                f"Turns: {session.turn_count}  |  "
                f"~{session.total_output} output tokens  |  "
                f"Messages in context: {len(session.history)}"
            )

        # ── /reset ───────────────────────────
        elif result.intent == Intent.CMD_RESET:
            cfg_mod.reset()
            ok("Config reset to defaults.")

        # ── /agent ───────────────────────────
        elif result.intent == Intent.CMD_AGENT:
            from vega.agents import VegaAgent, make_default_tools
            goal = result.remainder.strip()
            if not goal:
                goal = console.input(
                    Text.assemble(("  Goal › ", "bold cyan")).markup
                ).strip()
            if goal:
                agent = VegaAgent(provider=session.provider, tools=make_default_tools())
                agent.run(goal)

        # ── Unknown command ───────────────────
        elif result.intent == Intent.UNKNOWN_CMD:
            fail(f"Unknown command: /{result.command}  — type /help for commands")

        # ── BUILD intent ─────────────────────
        elif result.intent == Intent.BUILD:
            from vega.builder import ProjectBuilder
            import re as _re
            slug   = _re.sub(r"[^\w]", "_", raw[:40]).strip("_").lower()
            outdir = Path(f"./{slug}")
            builder = ProjectBuilder(
                provider   = session.provider,
                output_dir = outdir,
                auto_zip   = False,
                verbose    = True,
            )
            builder.build(raw)

        # ── CHAT intent ──────────────────────
        else:
            try:
                session.send(raw)
            except Exception as exc:
                fail(f"Error: {exc}")
                dim("  (Check your API key and internet connection)")
