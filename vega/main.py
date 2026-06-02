"""
vega/main.py — Vega CLI Entry Point
Typer-based CLI for the `vega` command.

  vega              → interactive chat mode
  vega "prompt"     → one-shot direct prompt
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import Optional

import typer
from rich.text import Text
from rich.prompt import Prompt, Confirm

from vega import __version__, __tagline__, __author__
from vega.display import (
    console,
    print_logo,
    print_banner,
    ok,
    fail,
    info,
    warn,
    dim,
    rule,
    section,
    panel,
    info_panel,
    models_table,
    config_table,
    spinner,
)

# ─────────────────────────────────────────────
#  Typer app
# ─────────────────────────────────────────────

app = typer.Typer(
    name            = "vega",
    help            = f"Vega CLI — {__tagline__}  |  by {__author__}",
    add_completion  = False,
    rich_markup_mode= "rich",
    no_args_is_help = False,
    invoke_without_command=True,
    context_settings= {"help_option_names": []},
)


# ─────────────────────────────────────────────
#  First-run wizard
# ─────────────────────────────────────────────

_PROVIDERS_INFO = {
    "nvidia":   ("NVIDIA NIM (free tier)", "https://build.nvidia.com",     "nvapi-"),
    "google":   ("Google Gemini",           "https://aistudio.google.com", "AIza"),
    "groq":     ("Groq (free tier)",        "https://console.groq.com",    "gsk_"),
    "deepseek": ("DeepSeek",                "https://platform.deepseek.com", "sk-"),
}


def _run_first_time_wizard() -> None:
    """
    Interactive setup wizard shown on first launch when no API key is found.
    Lets the user pick a provider and enter their key, or skip for later.
    """
    from config import settings as cfg

    # 1. Create ~/.vega directory and save default config if not exists
    cfg.load()

    console.print()
    panel(
        Text.assemble(
            ("Welcome to Vega CLI!\n\n", "bold bright_cyan"),
            ("To get started, connect an AI provider.\n", "cyan"),
            ("NVIDIA NIM offers a ", "dim"),
            ("free tier", "bold cyan"),
            (" — grab a key in 30 seconds at build.nvidia.com", "dim"),
        ),
        title="  ✦ First Launch",
        border_style="bright_cyan",
    )
    console.print()

    # Provider choice
    console.print(Text("  Choose a provider:\n", style="vega.primary"))
    choices = list(_PROVIDERS_INFO.keys())
    for i, (prov, (label, url, _)) in enumerate(_PROVIDERS_INFO.items(), start=1):
        console.print(Text(f"    {i}. {label}  →  {url}", style="cyan"))
    console.print(Text("    5. Skip for now (set keys later with /connect)", style="dim"))
    console.print()

    raw = console.input(Text("  Choice [1-5]: ", style="bold cyan").markup).strip()

    if raw in ("5", "", "s", "skip"):
        warn("Skipped. Run /connect inside vega to set your API key anytime.")
        cfg.set_value("first_run", False)
        return

    try:
        idx      = int(raw) - 1
        provider = choices[idx]
    except (ValueError, IndexError):
        warn("Invalid choice. Skipping setup.")
        cfg.set_value("first_run", False)
        return

    label, url, prefix = _PROVIDERS_INFO[provider]
    console.print()
    info(f"Get your free key at: {url}")
    console.print()

    key = console.input(
        Text(f"  Paste your {label} API key: ", style="bold cyan").markup
    ).strip()

    if not key:
        warn("No key entered. You can set it later with /connect")
        cfg.set_value("first_run", False)
        return

    if not key.startswith(prefix):
        warn(f"Key looks unusual (expected prefix '{prefix}') — saving anyway.")

    cfg.set_api_key(provider, key)
    cfg.set_active_provider(provider)

    from config import models as mdl
    default_model = mdl.get_default_model(provider)
    cfg.set_active_model(default_model)

    cfg.set_value("first_run", False)

    ok(f"Connected to {label}!")
    ok(f"Default model: {default_model}")
    console.print()


def _has_any_api_key() -> bool:
    """Return True if at least one provider API key is configured."""
    from config import settings as cfg
    from providers import SUPPORTED_PROVIDERS
    for p in SUPPORTED_PROVIDERS:
        if cfg.get_api_key(p):
            return True
    return False


# ─────────────────────────────────────────────
#  Provider bootstrap
# ─────────────────────────────────────────────

def _boot_provider():
    """
    Initialise the active provider from saved config.
    Returns a BaseProvider instance ready to use.
    Raises SystemExit if no key is found.
    """
    from config import settings as cfg
    from config import models as mdl
    from providers import get_provider, SUPPORTED_PROVIDERS

    provider_name = cfg.get_active_provider()
    model_id      = cfg.get_active_model()
    api_key       = cfg.get_api_key(provider_name)

    if not api_key:
        # Try fallbacks
        for p in SUPPORTED_PROVIDERS:
            k = cfg.get_api_key(p)
            if k:
                provider_name = p
                model_id      = mdl.get_default_model(p)
                api_key       = k
                break

    if not api_key:
        fail("No API key found.")
        console.print(
            Text("  Run /connect to set up a provider, or set env var VEGA_NVIDIA_API_KEY", style="dim")
        )
        raise typer.Exit(1)

    try:
        return get_provider(
            provider_name = provider_name,
            api_key       = api_key,
            model         = model_id,
            system_prompt = cfg.get("system_prompt"),
        )
    except Exception as exc:
        fail(f"Could not initialise provider '{provider_name}': {exc}")
        raise typer.Exit(1)


# ─────────────────────────────────────────────
#  /connect command (inside REPL — handled here)
# ─────────────────────────────────────────────

def _handle_connect(session) -> None:
    """Re-run the provider wizard and hot-swap the session provider."""
    _run_first_time_wizard()
    if _has_any_api_key():
        try:
            new_provider = _boot_provider()
            session.switch_provider(new_provider)
        except SystemExit:
            pass


# ─────────────────────────────────────────────
#  Extended slash commands (not in chat.py)
# ─────────────────────────────────────────────

def _handle_extended_commands(raw: str, session) -> bool:
    """
    Handle Vega-specific slash commands not covered by chat.py's loop.

    Returns True if command was handled, False to pass through.
    """
    from vega.router import route, Intent
    from config import settings as cfg
    from config import models as mdl
    from vega.agents import VegaAgent, make_default_tools

    text = raw.strip().lower()

    # /connect → wizard
    if text.startswith("/connect"):
        _handle_connect(session)
        return True

    # /agents → show agent registry
    if text.startswith("/agents"):
        _print_agents_table()
        return True

    # /switch <provider> → same as /provider
    if text.startswith("/switch "):
        parts = text.split()
        if len(parts) >= 2:
            from vega.chat import run_chat_loop
            # Reuse the /provider logic via routing
            raw_redirect = f"/provider {parts[1]}"
            from vega.router import route as _route
            return False   # Let chat loop handle it after redirect

    # /build <goal> → project builder
    if text.startswith("/build "):
        goal = raw.strip()[7:].strip()
        if goal:
            import re as _re
            from vega.builder import ProjectBuilder
            slug   = _re.sub(r"[^\w]", "_", goal[:40]).strip("_").lower()
            outdir = Path(f"./{slug}")
            builder = ProjectBuilder(
                provider   = session.provider,
                output_dir = outdir,
                verbose    = True,
            )
            builder.build(goal)
        else:
            fail("Usage: /build <project description>")
        return True

    # /settings → alias for /config
    if text.startswith("/settings"):
        config_table(cfg.as_dict())
        return True

    # /version
    if text.startswith("/version"):
        console.print(
            Text.assemble(
                ("  Vega CLI ", "bold bright_cyan"),
                (f"v{__version__}", "cyan"),
                ("  by ", "dim"),
                (__author__, "vega.muted"),
            )
        )
        return True

    return False


def _print_agents_table() -> None:
    """Display the 6 specialised agents and their triggers."""
    from vega.display import make_table
    from rich import box as rbox

    tbl = make_table(
        title      = "Vega Agents",
        columns    = ["Badge", "Agent", "Model", "Triggers"],
        col_styles = ["vega.accent", "bold cyan", "vega.muted", "vega.dim"],
        show_lines = True,
        box_style  = rbox.ROUNDED,
    )
    agents_info = [
        ("⟡",  "CodeAgent",    "Kimi-K2 (NVIDIA)",  "build / create / make"),
        ("🎨", "ImageAgent",   "Gemini 2.0 Flash",  "image / draw / picture"),
        ("⚡", "FastAgent",    "Llama-4-Scout",     "what / explain / quick"),
        ("🗺", "PlannerAgent", "DeepSeek-V3",       "plan / architect / design"),
        ("🔧", "DebugAgent",   "Kimi-K2 (NVIDIA)",  "fix / bug / error / debug"),
        ("👁",  "ReviewAgent",  "DeepSeek-V3",       "review / refactor / improve"),
    ]
    for badge, name, model, triggers in agents_info:
        tbl.add_row(badge, name, model, triggers)
    console.print(tbl)


# ─────────────────────────────────────────────
#  Goodbye
# ─────────────────────────────────────────────

def _print_goodbye() -> None:
    console.print()
    console.print(
        Text.assemble(
            ("  ✦ ", "bold bright_cyan"),
            ("Thanks for using ", "cyan"),
            ("Vega", "bold bright_cyan"),
            (" — code at the speed of stars. ", "cyan"),
            ("✦\n", "bold bright_cyan"),
        )
    )


# ─────────────────────────────────────────────
#  Main callback (entry point)
# ─────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main(
    ctx:      typer.Context,
    prompt:   Optional[str] = typer.Argument(
        None,
        help="Optional one-shot prompt. If omitted, enters interactive mode.",
        metavar="PROMPT",
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p",
        help="Provider to use (nvidia / google / groq / deepseek)",
    ),
    model:    Optional[str] = typer.Option(
        None, "--model", "-m",
        help="Model ID to use",
    ),
    version:  bool = typer.Option(
        False, "--version", "-v",
        help="Print version and exit",
        is_eager=True,
    ),
    help:     bool = typer.Option(
        False, "--help", "-h",
        help="Show rich help table and exit",
        is_eager=True,
    ),
    no_logo:  bool = typer.Option(
        False, "--no-logo",
        help="Skip the ASCII logo on startup",
    ),
) -> None:
    """
    \b
    ██╗   ██╗███████╗ ██████╗  █████╗
    ██║   ██║██╔════╝██╔════╝ ██╔══██╗
    ██║   ██║█████╗  ██║  ███╗███████║
    ╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██║
     ╚████╔╝ ███████╗╚██████╔╝██║  ██║
      ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝

    Code at the speed of stars — by Raimic Labs
    """
    # ── --help flag ───────────────────────────
    if help:
        from vega.display import show_help_table
        show_help_table()
        raise typer.Exit()

    # ── --version flag ────────────────────────
    if version:
        print_banner()
        raise typer.Exit()

    # ── Sub-command was invoked → skip ────────
    if ctx.invoked_subcommand is not None:
        return

    # ── Logo ──────────────────────────────────
    if not no_logo:
        print_logo()

    # ── First-run wizard ──────────────────────
    from config import settings as cfg
    if cfg.get("first_run", True):
        _run_first_time_wizard()
        if not _has_any_api_key():
            # User skipped — show hint and exit
            info("Set your key anytime: vega /connect")
            raise typer.Exit()

    # ── Override provider / model if flags given ──
    if provider:
        cfg.set_active_provider(provider)
    if model:
        cfg.set_active_model(model)

    # ── Boot provider ─────────────────────────
    active_provider = _boot_provider()

    # ── Build ChatSession ─────────────────────
    from vega.chat import ChatSession, run_chat_loop
    from config import settings as cfg2

    session = ChatSession(
        provider      = active_provider,
        system_prompt = cfg2.get("system_prompt"),
        show_tokens   = cfg2.get("show_token_count", True),
    )

    # ── One-shot mode: vega "prompt text" ─────
    if prompt:
        try:
            from vega.router import route
            res = route(prompt)
            session.send(prompt, agent=res.agent)
        except Exception as exc:
            fail(f"{exc}")
            raise typer.Exit(1)
        _print_goodbye()
        return

    # ── Interactive mode ──────────────────────
    # Monkey-patch run_chat_loop to intercept extended commands
    _original_loop = run_chat_loop

    def _patched_loop(sess, show_welcome=True):
        """Wrap run_chat_loop to handle /connect, /agents, /build, /version, /settings."""
        from vega.router import route, Intent, is_exit, HELP_TEXT, is_command

        if show_welcome:
            console.print()
            console.print(
                Text.assemble(
                    ("  ✦ Vega ", "bold bright_cyan"),
                    (f"v{__version__} ", "vega.muted"),
                    ("is ready. Type ", "dim"),
                    ("/help", "bold cyan"),
                    (" for commands, ", "dim"),
                    ("/connect", "bold cyan"),
                    (" to switch provider.", "dim"),
                )
            )
            console.print()

        while True:
            try:
                raw = console.input(
                    Text.assemble(("\n  ✦ › ", "bold cyan")).markup
                ).strip()
            except EOFError:
                console.print()
                ok("Session saved. Goodbye! ✦")
                sess.save()
                break
            except KeyboardInterrupt:
                console.print()
                dim("  (Use /exit to quit)")
                continue

            if not raw:
                continue

            # Try extended commands first
            if _handle_extended_commands(raw, sess):
                continue

            # Then standard chat loop handler
            result = route(raw)

            if is_exit(result):
                ok("Goodbye! ✦")
                sess.save()
                _print_goodbye()
                break

            from vega.router import Intent as I
            if result.intent == I.CMD_HELP:
                _print_help()
                continue

            # Delegate everything else to the standard handler
            # Re-import and call inner handler logic
            _dispatch(raw, result, sess)

    _patched_loop(session)


# ─────────────────────────────────────────────
#  Inner dispatcher (avoids circular import)
# ─────────────────────────────────────────────

def _dispatch(raw: str, result, session) -> None:
    """Dispatch a RouteResult to the appropriate handler."""
    from vega.router import Intent
    from config import settings as cfg
    from config import models as mdl
    from providers import get_provider, SUPPORTED_PROVIDERS
    from vega.display import models_table, config_table, make_table
    from vega.chat import ChatSession, export_session_markdown
    from rich import box as rbox

    intent = result.intent

    if intent == Intent.CMD_CLEAR:
        session.clear()
        console.clear()

    elif intent == Intent.CMD_MODELS:
        pf = result.args[0] if result.args else None
        models_table(mdl.models_as_dicts(pf))

    elif intent == Intent.CMD_MODEL:
        if not result.args:
            info(f"Current model: {session.provider.model}")
        else:
            session.provider.model = result.args[0]
            cfg.set_active_model(result.args[0])
            ok(f"Model → {result.args[0]}")

    elif intent == Intent.CMD_PROVIDER:
        if not result.args:
            info(f"Current provider: {session.provider.name}")
        else:
            np = result.args[0].lower()
            if np not in SUPPORTED_PROVIDERS:
                fail(f"Unknown provider '{np}'")
            else:
                ak = cfg.get_api_key(np)
                nm = mdl.get_default_model(np)
                try:
                    new_p = get_provider(np, ak, nm)
                    session.switch_provider(new_p)
                    cfg.set_active_provider(np)
                    cfg.set_active_model(nm)
                except Exception as exc:
                    fail(str(exc))

    elif intent == Intent.CMD_SYSTEM:
        if result.remainder:
            session.set_system_prompt(result.remainder)
        else:
            cur = next((m.content for m in session.history if m.role == "system"), None)
            info(cur or "No system prompt set.")

    elif intent == Intent.CMD_CONFIG:
        if not result.args:
            config_table(cfg.as_dict())
        elif len(result.args) == 1:
            info(f"{result.args[0]} = {cfg.get(result.args[0])}")
        else:
            k = result.args[0]
            v: object = " ".join(result.args[1:])
            if str(v).lower() in ("true","false"):
                v = str(v).lower() == "true"
            elif str(v).replace(".","",1).lstrip("-").isdigit():
                v = float(str(v)) if "." in str(v) else int(str(v))
            cfg.set_value(k, v)
            ok(f"{k} = {v}")

    elif intent == Intent.CMD_HISTORY:
        sessions = ChatSession.list_sessions()
        if not sessions:
            dim("  No saved sessions.")
        else:
            tbl = make_table(
                title="Saved Sessions",
                columns=["ID", "Turns", "Modified", "Size"],
                col_styles=["vega.accent","vega.dim","vega.secondary","vega.dim"],
                show_lines=True, box_style=rbox.ROUNDED,
            )
            for s in sessions:
                tbl.add_row(s["id"][:14]+"…", str(s["turns"]), s["modified"], s["size"])
            console.print(tbl)

    elif intent == Intent.CMD_EXPORT:
        out = result.remainder.strip() or None
        export_session_markdown(session, Path(out) if out else None)

    elif intent == Intent.CMD_TOKENS:
        info(f"Turns: {session.turn_count} | Output tokens: ~{session.total_output} | Context messages: {len(session.history)}")

    elif intent == Intent.CMD_RESET:
        cfg.reset()
        ok("Config reset to defaults.")

    elif intent == Intent.CMD_AGENT:
        from vega.agents import VegaAgent, make_default_tools
        goal = result.remainder.strip() or console.input(
            Text("  Goal › ", style="bold cyan").markup
        ).strip()
        if goal:
            VegaAgent(provider=session.provider, tools=make_default_tools()).run(goal)

    elif intent == Intent.UNKNOWN_CMD:
        fail(f"Unknown command: /{result.command}  — type /help")

    elif intent == Intent.BUILD:
        import re as _re
        from vega.builder import ProjectBuilder
        slug   = _re.sub(r"[^\w]", "_", raw[:40]).strip("_").lower()
        outdir = Path(f"./{slug}")
        ProjectBuilder(provider=session.provider, output_dir=outdir).build(raw)

    else:
        try:
            session.send(raw, agent=result.agent)
        except Exception as exc:
            fail(str(exc))


# ─────────────────────────────────────────────
#  Help text
# ─────────────────────────────────────────────

def _print_help() -> None:
    from rich.table import Table
    from rich import box as rbox

    tbl = Table(
        box          = rbox.ROUNDED,
        border_style = "cyan",
        show_header  = False,
        padding      = (0, 2),
        expand       = False,
    )
    tbl.add_column("Command",  style="bold cyan",    min_width=22)
    tbl.add_column("Description", style="dim white")

    commands = [
        ("/help",              "Show this help message"),
        ("/exit  /quit",       "Exit Vega"),
        ("/connect",           "Set up or change API provider"),
        ("/provider [name]",   "Switch active provider"),
        ("/switch [name]",     "Alias for /provider"),
        ("/model [id]",        "Switch model"),
        ("/models [provider]", "List all available models"),
        ("/agents",            "Show specialised agent roster"),
        ("/build <goal>",      "Build a project (builder mode)"),
        ("/clear",             "Clear chat history"),
        ("/history",           "List saved sessions"),
        ("/export [path]",     "Export session to Markdown"),
        ("/settings",          "Show all config values"),
        ("/config [k] [v]",    "View or set a config key"),
        ("/system [prompt]",   "Set or view system prompt"),
        ("/tokens",            "Show token usage stats"),
        ("/agent [goal]",      "Run autonomous agent"),
        ("/reset",             "Reset config to defaults"),
        ("/version",           "Print Vega version"),
    ]
    for cmd, desc in commands:
        tbl.add_row(cmd, desc)

    console.print()
    console.print(
        Text("  ✦ Vega CLI — Commands", style="bold bright_cyan")
    )
    console.print(tbl)
    console.print(
        Text(
            "  Tip: start with \"build me a…\" to enter builder mode automatically.\n",
            style="dim"
        )
    )


# ─────────────────────────────────────────────
#  Sub-commands
# ─────────────────────────────────────────────

@app.command("models")
def cmd_models(
    provider: Optional[str] = typer.Argument(None, help="Filter by provider name"),
) -> None:
    """List all available AI models."""
    print_banner()
    from config import models as mdl
    models_table(mdl.models_as_dicts(provider))


@app.command("config")
def cmd_config(
    key:   Optional[str] = typer.Argument(None, help="Config key to read/set"),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
) -> None:
    """View or update Vega configuration."""
    from config import settings as cfg
    if key is None:
        config_table(cfg.as_dict())
    elif value is None:
        info(f"{key} = {cfg.get(key)}")
    else:
        cfg.set_value(key, value)
        ok(f"{key} = {value}")


@app.command("build")
def cmd_build(
    goal:     str           = typer.Argument(..., help="Project to build"),
    out:      Optional[str] = typer.Option(None, "--out", "-o", help="Output directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model:    Optional[str] = typer.Option(None, "--model", "-m"),
) -> None:
    """Build a full project from a natural language description."""
    print_logo(show_version=False)

    from config import settings as cfg
    if provider:
        cfg.set_active_provider(provider)
    if model:
        cfg.set_active_model(model)

    active_provider = _boot_provider()

    import re as _re
    from vega.builder import ProjectBuilder
    outdir = Path(out) if out else Path(_re.sub(r"[^\w]", "_", goal[:40]).strip("_").lower())
    ProjectBuilder(provider=active_provider, output_dir=outdir).build(goal)


@app.command("version")
def cmd_version() -> None:
    """Print Vega version."""
    print_banner()
