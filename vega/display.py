"""
display.py — Vega CLI Rich UI
Cyan-themed terminal UI: logo, panels, progress bars, tables, spinners.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator, Iterable, Optional, Sequence

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.rule import Rule
from rich.spinner import Spinner
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ─────────────────────────────────────────────
#  Theme & Console
# ─────────────────────────────────────────────

VEGA_THEME = Theme(
    {
        "vega.primary":    "bold cyan",
        "vega.secondary":  "cyan",
        "vega.accent":     "bold bright_cyan",
        "vega.muted":      "dim cyan",
        "vega.success":    "bold green",
        "vega.warning":    "bold yellow",
        "vega.error":      "bold red",
        "vega.info":       "bold blue",
        "vega.user":       "bold white",
        "vega.ai":         "bold cyan",
        "vega.dim":        "dim white",
        "vega.highlight":  "on cyan",
        "vega.border":     "cyan",
        "vega.title":      "bold bright_cyan",
    }
)

console = Console(theme=VEGA_THEME, highlight=False)

# ─────────────────────────────────────────────
#  ASCII Logo
# ─────────────────────────────────────────────

VEGA_LOGO = r"""
 ██╗   ██╗███████╗ ██████╗  █████╗ 
 ██║   ██║██╔════╝██╔════╝ ██╔══██╗
 ██║   ██║█████╗  ██║  ███╗███████║
 ╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██║
  ╚████╔╝ ███████╗╚██████╔╝██║  ██║
   ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""

TAGLINE  = "Code at the speed of stars"
BYLINE   = "by Raimic Labs"
VERSION  = "v0.1.0"


def print_logo(show_version: bool = True) -> None:
    """Print the full Vega ASCII logo with tagline."""
    logo_text = Text(VEGA_LOGO, style="vega.accent")
    tagline    = Text(f"  {TAGLINE}", style="vega.secondary")
    byline     = Text(f"  {BYLINE}", style="vega.muted")
    ver        = Text(f"  {VERSION}", style="vega.dim") if show_version else Text("")

    content = Text.assemble(logo_text, "\n", tagline, "\n", byline, "\n", ver)

    panel = Panel(
        Align.center(content),
        border_style="vega.border",
        padding=(0, 4),
        box=box.DOUBLE_EDGE,
    )
    console.print(panel)
    console.print()


def print_banner() -> None:
    """Compact single-line banner for non-interactive contexts."""
    console.print(f"Vega {VERSION} {BYLINE}")


# ─────────────────────────────────────────────
#  Panels
# ─────────────────────────────────────────────

def panel(
    content: str | Text | Markdown,
    title: str = "",
    subtitle: str = "",
    border_style: str = "vega.border",
    padding: tuple[int, int] = (1, 2),
    expand: bool = True,
) -> None:
    """Render a styled panel."""
    console.print(
        Panel(
            content,
            title=Text(title, style="vega.title") if title else None,
            subtitle=Text(subtitle, style="vega.muted") if subtitle else None,
            border_style=border_style,
            padding=padding,
            expand=expand,
            box=box.ROUNDED,
        )
    )


def info_panel(message: str, title: str = "Info") -> None:
    panel(Text(message, style="vega.info"), title=f"ℹ  {title}", border_style="blue")


def success_panel(message: str, title: str = "Success") -> None:
    panel(Text(message, style="vega.success"), title=f"✔  {title}", border_style="green")


def error_panel(message: str, title: str = "Error") -> None:
    panel(Text(message, style="vega.error"), title=f"✖  {title}", border_style="red")


def warning_panel(message: str, title: str = "Warning") -> None:
    panel(Text(message, style="vega.warning"), title=f"⚠  {title}", border_style="yellow")


def code_panel(code: str, language: str = "python", title: str = "") -> None:
    """Render syntax-highlighted code inside a panel."""
    syntax = Syntax(
        code,
        language,
        theme="monokai",
        line_numbers=True,
        background_color="default",
    )
    panel(syntax, title=title or f"  {language.upper()}")


def markdown_panel(md_text: str, title: str = "") -> None:
    """Render Markdown content inside a panel."""
    panel(Markdown(md_text), title=title)


# ─────────────────────────────────────────────
#  Rules / Dividers
# ─────────────────────────────────────────────

def rule(title: str = "", style: str = "vega.muted") -> None:
    console.print(Rule(title=title, style=style))


def section(title: str) -> None:
    console.print()
    console.print(Rule(title=f" {title} ", style="vega.primary", align="left"))
    console.print()


# ─────────────────────────────────────────────
#  Spinner (context manager)
# ─────────────────────────────────────────────

@contextmanager
def spinner(message: str = "Thinking…", style: str = "dots2") -> Generator[None, None, None]:
    """
    Context manager that shows a spinner while work is being done.

    Usage:
        with spinner("Generating code…"):
            do_heavy_work()
    """
    spinner_text = Text.assemble(
        Spinner(style, style="vega.accent"),  # type: ignore[arg-type]
        ("  ", ""),
        (message, "vega.secondary"),
    )
    with Live(spinner_text, console=console, refresh_per_second=12, transient=True):
        yield


# ─────────────────────────────────────────────
#  Progress Bars
# ─────────────────────────────────────────────

def make_progress_bar(description: str = "Processing") -> Progress:
    """Return a configured Progress bar (caller must use as context manager)."""
    return Progress(
        SpinnerColumn(spinner_name="dots2", style="vega.accent"),
        TextColumn("[vega.secondary]{task.description}"),
        BarColumn(
            bar_width=40,
            style="vega.muted",
            complete_style="vega.accent",
            finished_style="vega.success",
        ),
        TaskProgressColumn(style="vega.primary"),
        MofNCompleteColumn(style="vega.dim"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )


def progress_track(
    iterable: Iterable,
    description: str = "Working",
    total: Optional[int] = None,
) -> Iterable:
    """
    Wrap an iterable with a live progress bar.

    Usage:
        for item in progress_track(items, "Processing files"):
            process(item)
    """
    bar = make_progress_bar()
    with bar:
        yield from bar.track(iterable, description=description, total=total)


@contextmanager
def progress_bar(description: str = "Working", total: int = 100) -> Generator:
    """
    Manual progress bar context manager.

    Usage:
        with progress_bar("Downloading", total=100) as (bar, task_id):
            bar.update(task_id, advance=10)
    """
    bar = make_progress_bar()
    with bar:
        task_id = bar.add_task(description, total=total)
        yield bar, task_id


# ─────────────────────────────────────────────
#  Tables
# ─────────────────────────────────────────────

def make_table(
    title: str = "",
    columns: Sequence[str] = (),
    col_styles: Optional[Sequence[str]] = None,
    show_header: bool = True,
    show_lines: bool = False,
    box_style: box.Box = box.SIMPLE_HEAVY,
) -> Table:
    """Create and return a styled Rich Table."""
    tbl = Table(
        title=Text(title, style="vega.title") if title else None,
        box=box_style,
        border_style="vega.border",
        header_style="vega.primary",
        show_header=show_header,
        show_lines=show_lines,
        highlight=True,
        expand=False,
    )
    col_styles = col_styles or ["vega.secondary"] * len(columns)
    for col, style in zip(columns, col_styles):
        tbl.add_column(col, style=style, overflow="fold")
    return tbl


def models_table(models: list[dict]) -> None:
    """
    Render a table of available models.

    Each dict: { "provider", "name", "id", "context", "notes" }
    """
    tbl = make_table(
        title="Available Models",
        columns=["#", "Provider", "Model", "ID", "Context", "Notes"],
        col_styles=[
            "vega.dim",
            "bold cyan",
            "vega.secondary",
            "vega.muted",
            "vega.dim",
            "vega.dim",
        ],
        show_lines=True,
        box_style=box.ROUNDED,
    )
    for i, m in enumerate(models, start=1):
        tbl.add_row(
            str(i),
            m.get("provider", "—"),
            m.get("name", "—"),
            m.get("id", "—"),
            m.get("context", "—"),
            m.get("notes", ""),
        )
    console.print(tbl)


def config_table(settings: dict) -> None:
    """Render current config settings as a two-column table."""
    tbl = make_table(
        title="Vega Configuration",
        columns=["Key", "Value"],
        col_styles=["vega.primary", "vega.secondary"],
        show_lines=True,
        box_style=box.ROUNDED,
    )
    for k, v in settings.items():
        tbl.add_row(str(k), str(v))
    console.print(tbl)


def key_value_table(data: dict, title: str = "") -> None:
    """Generic key-value table."""
    tbl = make_table(
        title=title,
        columns=["Key", "Value"],
        col_styles=["vega.primary", "vega.secondary"],
        show_lines=False,
        box_style=box.SIMPLE,
    )
    for k, v in data.items():
        tbl.add_row(str(k), str(v))
    console.print(tbl)


def columns_display(items: list[str], title: str = "") -> None:
    """Render a list as columns."""
    if title:
        console.print(Text(title, style="vega.title"))
    renderables = [Text(f"  • {item}", style="vega.secondary") for item in items]
    console.print(Columns(renderables, equal=True, expand=True))


# ─────────────────────────────────────────────
#  Chat UI helpers
# ─────────────────────────────────────────────

def print_user_message(message: str) -> None:
    label = Text("  You  ", style="bold black on cyan")
    bubble = Panel(
        Text(message, style="vega.user"),
        title=label,
        title_align="right",
        border_style="cyan",
        padding=(0, 2),
        box=box.ROUNDED,
    )
    console.print(bubble)
    console.print()


def print_ai_message(message: str, model_name: str = "Vega") -> None:
    label = Text(f"  ✦ {model_name}  ", style="bold black on bright_cyan")
    bubble = Panel(
        Markdown(message),
        title=label,
        title_align="left",
        border_style="bright_cyan",
        padding=(0, 2),
        box=box.ROUNDED,
    )
    console.print(bubble)
    console.print()


def print_ai_stream_start(model_name: str = "Vega") -> None:
    label = Text(f"  ✦ {model_name}  ", style="bold black on bright_cyan")
    console.print(
        Panel(
            Text("", style="vega.ai"),
            title=label,
            title_align="left",
            border_style="bright_cyan",
            padding=(0, 2),
            box=box.ROUNDED,
        )
    )


# ─────────────────────────────────────────────
#  Status / Notification helpers
# ─────────────────────────────────────────────

def ok(message: str) -> None:
    console.print(Text.assemble(("  ✔  ", "vega.success"), (message, "vega.secondary")))


def fail(message: str) -> None:
    console.print(Text.assemble(("  ✖  ", "vega.error"), (message, "vega.secondary")))


def warn(message: str) -> None:
    console.print(Text.assemble(("  ⚠  ", "vega.warning"), (message, "vega.secondary")))


def info(message: str) -> None:
    console.print(Text.assemble(("  ℹ  ", "vega.info"), (message, "vega.secondary")))


def dim(message: str) -> None:
    console.print(Text(f"  {message}", style="vega.dim"))


def highlight(message: str) -> None:
    console.print(Text(f"  {message}", style="vega.highlight"))


# ─────────────────────────────────────────────
#  Prompt helpers
# ─────────────────────────────────────────────

def prompt_prefix() -> str:
    """Return the styled chat prompt prefix as a plain string for input()."""
    return "  ✦ › "


def print_prompt_hint() -> None:
    console.print(
        Text.assemble(
            ("  Type ", "vega.dim"),
            ("/help", "vega.accent"),
            (" for commands, ", "vega.dim"),
            ("/exit", "vega.accent"),
            (" to quit", "vega.dim"),
        )
    )


# ─────────────────────────────────────────────
#  Production Hardened UI Functions (TASK 9)
# ─────────────────────────────────────────────

def show_logo() -> None:
    """Print the full Vega ASCII logo with tagline and cyan underline."""
    logo_text = Text(VEGA_LOGO, style="vega.accent")
    tagline    = Text(f"  {TAGLINE}", style="vega.secondary")
    byline     = Text(f"  {BYLINE}", style="vega.muted")
    ver        = Text(f"  {VERSION}", style="vega.dim")

    content = Text.assemble(logo_text, "\n", tagline, "\n", byline, "\n", ver)

    panel = Panel(
        Align.center(content),
        border_style="vega.border",
        padding=(0, 4),
        box=box.DOUBLE_EDGE,
    )
    console.print(panel)
    console.print()
    rule(style="cyan")


def show_welcome_panel() -> None:
    """Show the first-run welcome panel."""
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


def show_user_panel(msg: str) -> None:
    """Render the standard user panel."""
    print_user_message(msg)


def show_vega_panel(msg: str) -> None:
    """Render the standard Vega response panel."""
    print_ai_message(msg, model_name="Vega")


def show_agent_badge(agent) -> None:
    """Print the colored agent badge with icon."""
    if hasattr(agent, "badge") and hasattr(agent, "name"):
        badge = agent.badge
        name = agent.name
    elif isinstance(agent, dict):
        badge = agent.get("badge", "⟡")
        name = agent.get("name", "Agent")
    else:
        badge = "⟡"
        name = str(agent)
    console.print(Text.assemble(
        ("  ", ""),
        (f" {badge} {name} ", "bold black on bright_cyan"),
        (" active", "dim cyan"),
    ))


def show_file_tree(files: list) -> None:
    """Render a clean, folder-grouped file tree."""
    from rich.tree import Tree
    from pathlib import Path
    
    root_name = "./"
    tree = Tree(Text(f"📁 {root_name}", style="bold bright_cyan"), guide_style="dim cyan")
    nodes: dict = {}
    for f in files:
        if hasattr(f, "path"):
            p_str = f.path
        elif isinstance(f, dict):
            p_str = f.get("path", "")
        else:
            p_str = str(f)
        
        if not p_str:
            continue
        
        parts = Path(p_str).parts
        cur = nodes
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = None

    def _add_nodes(tree_node, subtree: dict) -> None:
        dirs  = sorted(k for k, v in subtree.items() if isinstance(v, dict))
        fls   = sorted(k for k, v in subtree.items() if v is None)
        for d in dirs:
            branch = tree_node.add(Text(f"📁 {d}/", style="bold cyan"))
            _add_nodes(branch, subtree[d])
        for fl in fls:
            suffix = Path(fl).suffix.lower()
            icon  = _file_icon(suffix)
            tree_node.add(Text(f"{icon} {fl}", style="vega.secondary"))

    _add_nodes(tree, nodes)
    console.print()
    console.print(tree)
    console.print()


def show_progress(n: int, total: int) -> None:
    """Show a progress bar indicating file count progress."""
    percent = int((n / total) * 100) if total > 0 else 100
    filled = int((n / total) * 30) if total > 0 else 30
    bar = "█" * filled + "░" * (30 - filled)
    console.print(Text.assemble(
        ("  Writing files: ", "vega.secondary"),
        (f"[{bar}]", "vega.accent"),
        (f" {n}/{total} ", "vega.primary"),
        (f" ({percent}%)", "vega.dim"),
    ))


def show_models_table(models: Optional[list[dict]] = None) -> None:
    """List key models with a star indicating the default/active model."""
    from config import settings as cfg
    active_model = cfg.get_active_model()
    
    if models is None:
        from config import models as mdl
        all_mdls = mdl.models_as_dicts()
        primary_ids = {
            "meta/llama-3.1-405b-instruct",
            "gemini-2.0-flash",
            "llama-3.3-70b-versatile",
            "deepseek-chat",
            "moonshotai/kimi-k2-instruct"
        }
        models = [m for m in all_mdls if m["id"] in primary_ids]
        if len(models) < 5:
            models = all_mdls[:5]

    tbl = make_table(
        title="Vega Models Registry",
        columns=["Status", "Provider", "Model Name", "Model ID", "Context", "Notes"],
        col_styles=[
            "bold yellow",
            "bold cyan",
            "vega.secondary",
            "vega.muted",
            "vega.dim",
            "vega.dim",
        ],
        show_lines=True,
        box_style=box.ROUNDED,
    )
    for m in models:
        is_active = (m["id"] == active_model)
        status = "★ Active" if is_active else " "
        tbl.add_row(
            status,
            m.get("provider", "—").upper(),
            m.get("name", "—"),
            m.get("id", "—"),
            m.get("context", "—"),
            m.get("notes", ""),
        )
    console.print(tbl)


def show_agents_table() -> None:
    """Render specialized agents roster as a rich table."""
    tbl = make_table(
        title="Vega Specialized Agents",
        columns=["Icon", "Agent", "Triggers", "Description"],
        col_styles=["vega.accent", "bold cyan", "vega.secondary", "vega.dim"],
        show_lines=True,
        box_style=box.ROUNDED,
    )
    agents_info = [
        ("⟡",  "CodeAgent",    "build, create, make, clone, duplicate, port, rewrite, scaffold, boilerplate, template, starter, init", "Code architect and generation wizard"),
        ("🎨", "ImageAgent",   "image, draw, picture", "Creative visual assets generator"),
        ("⚡", "FastAgent",    "what, explain, quick, what's, who is, how many, when was, list, show me, give me, summarize", "Lightning fast Q&A responder"),
        ("🗺", "PlannerAgent", "plan, architect, design", "Architectural layouts & structure planner"),
        ("🔧", "DebugAgent",   "fix, bug, error, debug, traceback, exception, failing, doesn't work, not running, syntax error, runtime error", "Diagnostic debugger & bug resolver"),
        ("👁",  "ReviewAgent",  "review, refactor, improve, audit, security, performance, lint, best practices, code quality", "Code auditor & quality inspector"),
    ]
    for icon, name, triggers, desc in agents_info:
        tbl.add_row(icon, name, triggers, desc)
    console.print(tbl)


def show_help_table() -> None:
    """Render /help command output as a rich table with a cyan border."""
    tbl = Table(
        box=box.ROUNDED,
        border_style="cyan",
        show_header=False,
        padding=(0, 2),
        expand=False,
    )
    tbl.add_column("Command", style="bold cyan", min_width=22)
    tbl.add_column("Description", style="dim white")

    commands = [
        ("/help",              "Show this help message"),
        ("/exit  /quit",       "Exit Vega"),
        ("/connect",           "Set up or change API provider"),
        ("/provider [name]",   "Switch active provider"),
        ("/switch",            "Interactively switch model"),
        ("/model [id]",        "Switch model"),
        ("/models",            "List key models (starred default)"),
        ("/agents",            "Show specialised agent roster"),
        ("/build <goal>",      "Build a project (builder mode)"),
        ("/clear",             "Clear chat history"),
        ("/history",           "Show last 10 prompts"),
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
    console.print(Text("  ✦ Vega CLI — Commands", style="bold bright_cyan"))
    console.print(tbl)
    console.print(Text("  Tip: start with \"build me a…\" to enter builder mode automatically.\n", style="dim"))


def show_settings(config: dict) -> None:
    """Render current configuration in a rich panel."""
    tbl = make_table(
        columns=["Key", "Value"],
        col_styles=["vega.primary", "vega.secondary"],
        show_lines=False,
        box_style=box.SIMPLE,
    )
    for k, v in config.items():
        tbl.add_row(str(k), str(v))
    p = Panel(
        tbl,
        title=Text("⚙  Vega Configuration", style="vega.title"),
        border_style="cyan",
        expand=False,
    )
    console.print(p)


def show_history(history: list[str]) -> None:
    """Render the last 10 prompts in a numbered list."""
    if not history:
        console.print(Text("  No history yet.", style="vega.dim"))
        return
    
    tbl = make_table(
        title="Prompt History (Last 10)",
        columns=["#", "Prompt"],
        col_styles=["vega.accent", "vega.secondary"],
        show_lines=False,
        box_style=box.SIMPLE,
    )
    for i, prompt in enumerate(history[-10:], start=1):
        tbl.add_row(f"{i}.", prompt)
    console.print(tbl)


def show_goodbye() -> None:
    """Show the exit goodbye panel."""
    p = Panel(
        Align.center(
            Text.assemble(
                ("Thanks for using ", "cyan"),
                ("Vega", "bold bright_cyan"),
                (" — code at the speed of stars.\n", "cyan"),
                ("★ Keep coding! ★", "bold yellow"),
            )
        ),
        border_style="bright_cyan",
        box=box.DOUBLE,
        expand=False,
    )
    console.print()
    console.print(p)
    console.print()


def show_error(msg: str) -> None:
    """Display a red error panel."""
    error_panel(msg)


def show_success(msg: str) -> None:
    """Display a green success panel."""
    success_panel(msg)


def show_spinner(msg: str = "Thinking…"):
    """Animated spinner context manager."""
    return spinner(msg)


def _file_icon(ext: str) -> str:
    """Return a terminal emoji icon for a given file extension."""
    icons = {
        ".py":    "🐍",
        ".js":    "📜",
        ".ts":    "📘",
        ".jsx":   "⚛️",
        ".tsx":   "⚛️",
        ".html":  "🌐",
        ".css":   "🎨",
        ".json":  "📋",
        ".toml":  "⚙️",
        ".yaml":  "⚙️",
        ".yml":   "⚙️",
        ".md":    "📝",
        ".txt":   "📄",
        ".sh":    "🔧",
        ".env":   "🔑",
        ".sql":   "🗄️",
        ".go":    "🐹",
        ".rs":    "🦀",
        ".java":  "☕",
        ".rb":    "💎",
        ".gitignore": "🚫",
        ".dockerfile": "🐳",
    }
    return icons.get(ext.lower(), "📄")


if __name__ == "__main__":
    show_logo()
    section("Panels")
    show_welcome_panel()
    show_user_panel("Write a Python async web scraper.")
    show_vega_panel("Here's a minimal example.")
    show_agent_badge({"badge": "⟡", "name": "CodeAgent"})
    
    section("Spinner")
    with show_spinner("Testing spinner…"):
        time.sleep(1)
    
    section("Progress Bar")
    show_progress(5, 10)
    
    section("Models Table")
    show_models_table()
    
    section("Agents Table")
    show_agents_table()

    section("Help Table")
    show_help_table()
    
    section("Settings")
    show_settings({"provider": "nvidia", "model": "meta/llama-3.1-405b-instruct"})
    
    section("Goodbye")
    show_goodbye()

