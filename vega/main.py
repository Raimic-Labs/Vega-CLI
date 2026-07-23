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


def _handle_switch(session) -> None:
    """Interactively switch active model/provider."""
    from vega.display import console, ok, fail, warn
    from config import settings as cfg
    from config import models as mdl
    from providers import get_provider

    primary_models = [
        ("nvidia", "meta/llama-3.1-405b-instruct", "Llama 3.1 405B (NVIDIA)"),
        ("google", "gemini-2.0-flash", "Gemini 2.0 Flash (Google)"),
        ("groq", "llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)"),
        ("deepseek", "deepseek-chat", "DeepSeek-V3 (DeepSeek)"),
        ("nvidia", "moonshotai/kimi-k2-instruct", "Kimi K2.6 (NVIDIA)"),
    ]

    console.print()
    console.print("  ✦ Switch Active Model", style="bold bright_cyan")
    console.print()
    for i, (p, m, name) in enumerate(primary_models, start=1):
        is_active = (cfg.get_active_model() == m and cfg.get_active_provider() == p)
        marker = "★" if is_active else " "
        console.print(f"    {i}. {marker} {name} ({m})", style="cyan")
    console.print()

    try:
        raw = console.input("  Choose a model [1-5]: ").strip()
        if not raw:
            return
        idx = int(raw) - 1
        if 0 <= idx < len(primary_models):
            p, m, name = primary_models[idx]
            api_key = cfg.get_api_key(p)
            if not api_key:
                warn(f"No API key set for {p}. Running /connect first.")
                _run_first_time_wizard()
                api_key = cfg.get_api_key(p)
                if not api_key:
                    fail(f"Failed to switch: no key for {p}.")
                    return
            new_provider = get_provider(p, api_key, m)
            session.switch_provider(new_provider)
            cfg.set_active_provider(p)
            cfg.set_active_model(m)
            ok(f"Switched active model to: {name}")
        else:
            fail("Invalid choice.")
    except Exception as exc:
        fail(f"Could not switch model: {exc}")


def handle_slash_command(raw: str, session) -> bool:
    """
    Handle all slash commands inside the REPL loop.
    Returns True if raw was a command, False if it was regular chat.
    """
    from vega.display import (
        console, show_help_table, show_models_table, show_agents_table,
        show_settings, show_history, show_goodbye, show_error, show_success,
        show_spinner,
    )
    from config import settings as cfg
    from config import models as mdl
    from providers import SUPPORTED_PROVIDERS, get_provider
    import sys
    from pathlib import Path

    text = raw.strip()
    if not text.startswith("/"):
        return False

    parts = text[1:].split()
    cmd = parts[0].lower() if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    remainder = " ".join(args)

    try:
        if cmd in ("help", "h"):
            show_help_table()
            return True

        elif cmd in ("exit", "quit", "q"):
            session.save()
            show_goodbye()
            sys.exit(0)

        elif cmd == "connect":
            _handle_connect(session)
            return True

        elif cmd in ("provider", "p"):
            if not args:
                info(f"Current provider: {session.provider.name}")
                info(f"Supported: {', '.join(SUPPORTED_PROVIDERS)}")
            else:
                p_name = args[0].lower()
                if p_name not in SUPPORTED_PROVIDERS:
                    show_error(f"Unknown provider '{p_name}'. Choose from: {SUPPORTED_PROVIDERS}")
                else:
                    api_key = cfg.get_api_key(p_name)
                    new_model = mdl.get_default_model(p_name)
                    new_provider = get_provider(p_name, api_key, new_model)
                    session.switch_provider(new_provider)
                    cfg.set_active_provider(p_name)
                    cfg.set_active_model(new_model)
                    show_success(f"Switched provider to {p_name} ({new_model})")
            return True

        elif cmd in ("switch", "s"):
            _handle_switch(session)
            return True

        elif cmd in ("model", "m"):
            if not args:
                info(f"Current model: {session.provider.model}")
            else:
                new_model = args[0]
                session.provider.model = new_model
                cfg.set_active_model(new_model)
                show_success(f"Model set to {new_model}")
            return True

        elif cmd == "models":
            show_models_table()
            return True

        elif cmd == "agents":
            show_agents_table()
            return True

        elif cmd == "build":
            goal = remainder.strip()
            if not goal:
                goal = console.input("  Project description › ").strip()
            if goal:
                import re as _re
                from vega.builder import ProjectBuilder
                slug = _re.sub(r"[^\w]", "_", goal[:40]).strip("_").lower()
                outdir = Path(f"./{slug}")
                builder = ProjectBuilder(
                    provider   = session.provider,
                    output_dir = outdir,
                    verbose    = True,
                )
                builder.build(goal)
            else:
                show_error("No project goal provided.")
            return True

        elif cmd in ("clear", "cls"):
            session.clear()
            console.clear()
            show_success("Terminal cleared and chat history reset.")
            return True

        elif cmd == "history":
            prompts = [m.content for m in session.history if m.role == "user"]
            show_history(prompts)
            return True

        elif cmd == "export":
            # ZIP current project
            from tools.zip_export import zip_project
            with show_spinner("Zipping project directory..."):
                zip_path = zip_project(".")
            show_success(f"Project directory zipped successfully!")
            info(f"Archive saved at: {zip_path.resolve()}")
            return True

        elif cmd == "settings":
            show_settings(cfg.as_dict())
            return True

        elif cmd in ("config", "cfg"):
            if not args:
                show_settings(cfg.as_dict())
            elif len(args) == 1:
                info(f"{args[0]} = {cfg.get(args[0])}")
            else:
                k = args[0]
                v = " ".join(args[1:])
                if v.lower() in ("true", "false"):
                    v = v.lower() == "true"
                elif v.replace(".", "", 1).lstrip("-").isdigit():
                    v = float(v) if "." in v else int(v)
                cfg.set_value(k, v)
                show_success(f"Config updated: {k} = {v}")
            return True

        elif cmd in ("system", "sys"):
            if remainder:
                session.set_system_prompt(remainder)
            else:
                cur = next((m.content for m in session.history if m.role == "system"), None)
                info(cur or "No system prompt set.")
            return True

        elif cmd == "tokens":
            info(f"Turns: {session.turn_count} | Output tokens: ~{session.total_output} | Context messages: {len(session.history)}")
            return True

        elif cmd == "reset":
            cfg.reset()
            show_success("Configuration reset to defaults.")
            return True

        elif cmd == "version":
            from vega import __version__, __tagline__, __url__
            console.print()
            console.print(Text.assemble(
                ("  Vega CLI ", "bold bright_cyan"),
                (f"v{__version__}\n", "cyan"),
                (f"  {__tagline__}\n", "dim"),
                ("  GitHub: ", "vega.muted"),
                (__url__, "underline cyan"),
            ))
            console.print()
            return True

        else:
            show_error(f"Unknown command: /{cmd} — type /help for available commands.")
            return True

    except Exception as exc:
        show_error(f"Command /{cmd} failed: {exc}")
        return True


# ─────────────────────────────────────────────
#  Goodbye
# ─────────────────────────────────────────────

def _print_goodbye() -> None:
    from vega.display import show_goodbye
    show_goodbye()

# NOTE: The interactive REPL loop (run_chat_loop) lives in vega/chat.py.


# ─────────────────────────────────────────────
#  Interactive REPL loop
# ─────────────────────────────────────────────

def run_chat_loop(
    session:      ChatSession,
    show_welcome: bool = True,
) -> None:
    """
    Start the interactive Vega chat REPL.
    """
    from vega.router import route, Intent
    from vega.display import console, ok, fail, dim, show_agent_badge, show_error

    if show_welcome:
        console.print()
        console.print(
            Text.assemble(
                ("  ✦ Vega ", "bold bright_cyan"),
                (f"v{__version__} ", "vega.muted"),
                ("is ready. Type ", "dim"),
                ("/help", "bold cyan"),
                (" for commands.", "dim"),
            )
        )
        console.print()

    while True:
        try:
            raw = console.input(
                Text.assemble(
                    ("\n  ✦ › ", "bold cyan"),
                ).markup
            ).strip()
        except EOFError:
            console.print()
            ok("Session saved. Goodbye! ✦")
            session.save()
            break
        except KeyboardInterrupt:
            console.print()
            dim("  (Use /exit to quit, or Ctrl-D)")
            continue

        if not raw:
            continue

        if raw.startswith("/"):
            handle_slash_command(raw, session)
            continue

        result = route(raw)

        if result.intent == Intent.BUILD:
            from vega.builder import ProjectBuilder
            import re as _re
            slug   = _re.sub(r"[^\w]", "_", raw[:40]).strip("_").lower()
            outdir = Path(f"./{slug}")
            try:
                builder = ProjectBuilder(
                    provider   = session.provider,
                    output_dir = outdir,
                    verbose    = True,
                )
                builder.build(raw)
            except Exception as exc:
                show_error(f"Build failed: {exc}")
        else:
            try:
                if result.agent:
                    show_agent_badge(result.agent)
                session.send(raw, agent=result.agent)
            except Exception as exc:
                show_error(str(exc))


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
#  (Goodbye is handled by _print_goodbye above)
# ─────────────────────────────────────────────


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
    from vega.chat import ChatSession
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
            from vega.display import show_agent_badge
            res = route(prompt)
            if res.agent:
                show_agent_badge(res.agent)
            session.send(prompt, agent=res.agent)
        except Exception as exc:
            fail(f"{exc}")
            raise typer.Exit(1)
        _print_goodbye()
        return

    # ── Interactive mode ──────────────────────
    run_chat_loop(session)


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
