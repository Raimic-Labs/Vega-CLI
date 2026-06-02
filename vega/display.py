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
    console.print(
        Text.assemble(
            ("✦ VEGA ", "vega.accent"),
            (f"{VERSION} ", "vega.muted"),
            ("— ", "vega.dim"),
            (TAGLINE, "vega.secondary"),
            (" — ", "vega.dim"),
            (BYLINE, "vega.muted"),
        )
    )


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
#  Demo (run directly to preview)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print_logo()
    section("Panels")
    info_panel("Everything is connected to the stars.")
    success_panel("Model loaded successfully.")
    warning_panel("Rate limit approaching.")
    error_panel("API key not set. Run `vega config set api_key <key>`.")

    section("Spinner")
    with spinner("Calling DeepSeek…"):
        time.sleep(2)
    ok("Response received.")

    section("Progress Bar")
    import random
    items = list(range(20))
    for _ in progress_track(items, description="Streaming tokens", total=len(items)):
        time.sleep(0.05)

    section("Models Table")
    models_table(
        [
            {"provider": "NVIDIA", "name": "Llama 3.1 405B", "id": "meta/llama-3.1-405b-instruct", "context": "128k", "notes": "Flagship"},
            {"provider": "Google", "name": "Gemini 1.5 Pro", "id": "gemini-1.5-pro", "context": "1M",    "notes": "Long context"},
            {"provider": "Groq",   "name": "Mixtral 8x7B",   "id": "mixtral-8x7b-32768",          "context": "32k",  "notes": "Fast"},
            {"provider": "DeepSeek","name": "DeepSeek-V3",   "id": "deepseek-chat",                "context": "64k",  "notes": "Coder"},
        ]
    )

    section("Chat UI")
    print_user_message("Write a Python async web scraper.")
    print_ai_message("Here's a minimal `asyncio` + `httpx` scraper:\n\n```python\nimport asyncio, httpx\n\nasync def fetch(url):\n    async with httpx.AsyncClient() as client:\n        r = await client.get(url)\n        return r.text\n\nasyncio.run(fetch('https://example.com'))\n```", model_name="DeepSeek-V3")

    section("Done")
    print_banner()
