"""
vega/builder.py — Project Builder
Generates complete multi-file projects from a natural language description.
Uses the active provider to plan, generate, and write all files to disk.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from providers.base import BaseProvider, Message
from tools.file_writer import write_file, write_project
from tools.zip_export  import zip_project
from vega.display import (
    console,
    ok,
    fail,
    info,
    warn,
    dim,
    spinner,
    section,
    panel,
    code_panel,
    progress_bar,
    rule,
)
from rich.text import Text

# ─────────────────────────────────────────────
#  Data types
# ─────────────────────────────────────────────

@dataclass
class ProjectFile:
    """A single file that will be written to disk."""
    path:    str    # relative path e.g. "src/main.py"
    content: str    # file content


@dataclass
class BuildPlan:
    """The structured plan produced before code generation."""
    description:  str
    stack:        list[str]          # e.g. ["Python", "FastAPI", "SQLite"]
    files:        list[str]          # list of relative file paths
    instructions: str                # prose description of what will be built


@dataclass
class BuildResult:
    """The result of a completed build."""
    goal:        str
    plan:        BuildPlan
    files:       list[ProjectFile]
    output_dir:  Path
    zip_path:    Optional[Path]
    success:     bool
    errors:      list[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)


# ─────────────────────────────────────────────
#  Prompts
# ─────────────────────────────────────────────

_PLAN_PROMPT = """\
You are Vega, an expert AI software architect by Raimic Labs.

The user wants to build:
{goal}

Respond with a JSON object ONLY (no markdown, no explanation) with this exact shape:
{{
  "description": "One-sentence description of the project",
  "stack": ["Tech1", "Tech2", "..."],
  "files": ["path/to/file1.py", "path/to/file2.py", "..."],
  "instructions": "Brief description of architecture and key decisions"
}}

Rules:
- Include ALL files needed for a complete, working project
- Always include README.md, requirements.txt or package.json, .gitignore
- Use sensible relative paths (no leading /)
- For Python: include __init__.py, setup.py or pyproject.toml
- For Node/TS: include package.json, tsconfig.json
- Maximum 20 files for focused projects
"""

_FILE_PROMPT = """\
You are Vega, an expert AI software engineer by Raimic Labs.

Project: {description}
Tech stack: {stack}
Architecture: {instructions}

Write the COMPLETE contents of this file:
  {filepath}

Rules:
- Output ONLY the file contents. No markdown fences. No explanation.
- The code must be complete, working, and production-ready.
- Include all imports, docstrings, error handling.
- Do NOT truncate or add "# ... rest of code" placeholders.
"""

_REVIEW_PROMPT = """\
You are Vega, an expert code reviewer by Raimic Labs.

Review the following file for correctness and completeness:
File: {filepath}

Content:
{content}

If the code is correct and complete, respond with exactly:
  OK

If there are issues, respond with:
  FIX: <one-line description of the problem>
"""


# ─────────────────────────────────────────────
#  Builder
# ─────────────────────────────────────────────

class ProjectBuilder:
    """
    Generates a complete multi-file project from a natural language goal.

    Workflow:
      1. plan()     — ask LLM to produce a structured build plan (JSON)
      2. generate() — generate each file's content one by one
      3. write()    — write all files to the output directory
      4. zip()      — optionally zip the project

    Usage:
        builder = ProjectBuilder(provider=provider, output_dir=Path("./my_project"))
        result  = builder.build("Build a FastAPI REST API with SQLite and JWT auth")
        print(f"Done! {result.file_count} files written to {result.output_dir}")
    """

    def __init__(
        self,
        provider:   BaseProvider,
        output_dir: Path = Path("."),
        auto_zip:   bool = False,
        verbose:    bool = True,
    ) -> None:
        self.provider   = provider
        self.output_dir = Path(output_dir)
        self.auto_zip   = auto_zip
        self.verbose    = verbose
        self._errors:   list[str] = []

    # ── Main entrypoint ───────────────────────

    def build(self, goal: str) -> BuildResult:
        """
        Full pipeline: plan → generate → write → (zip).

        Args:
            goal: Natural-language description of what to build.

        Returns:
            BuildResult with all generated files.
        """
        if self.verbose:
            section(f"Vega Builder — {goal[:70]}{'…' if len(goal) > 70 else ''}")

        # Step 1: Plan
        plan = self._plan(goal)
        self._print_plan(plan)

        # Step 2: Generate files
        files = self._generate_files(plan)

        # Step 3: Write to disk
        self._write_files(files)

        # Step 4: Show file tree
        self._print_file_tree(files)

        # Step 5: Zip
        zip_path = None
        if self.auto_zip:
            with spinner("Creating ZIP archive…"):
                zip_path = zip_project(self.output_dir)
            ok(f"Archive → {zip_path}")

        result = BuildResult(
            goal       = goal,
            plan       = plan,
            files      = files,
            output_dir = self.output_dir,
            zip_path   = zip_path,
            success    = len(self._errors) == 0,
            errors     = self._errors.copy(),
        )

        self._print_summary(result)

        # Step 6: Post-build prompts (browser / ZIP)
        self._prompt_actions(result)

        return result

    # ── Step 1: Plan ──────────────────────────

    def _plan(self, goal: str) -> BuildPlan:
        """Ask the LLM to produce a JSON build plan."""
        prompt = _PLAN_PROMPT.format(goal=goal)
        messages = [Message(role="user", content=prompt)]

        with spinner("Planning project structure…"):
            parts: list[str] = []
            for chunk in self.provider.stream_with_retry(messages):
                if chunk.text:
                    parts.append(chunk.text)
            raw = "".join(parts)

        # Strip markdown fences if LLM added them
        raw = _strip_fences(raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON object from response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                fail("Could not parse build plan. Using fallback.")
                data = {
                    "description":  goal,
                    "stack":        ["Python"],
                    "files":        ["main.py", "README.md", "requirements.txt"],
                    "instructions": "Basic project structure.",
                }

        return BuildPlan(
            description  = data.get("description", goal),
            stack        = data.get("stack", []),
            files        = data.get("files", []),
            instructions = data.get("instructions", ""),
        )

    # ── Step 2: Generate files ─────────────────

    def _generate_files(self, plan: BuildPlan) -> list[ProjectFile]:
        """Generate content for each file in the build plan."""
        generated: list[ProjectFile] = []
        total = len(plan.files)

        with progress_bar(description="Generating files", total=total) as (bar, task):
            for i, filepath in enumerate(plan.files):
                if self.verbose:
                    dim(f"  [{i+1}/{total}] {filepath}")

                content = self._generate_one_file(plan, filepath)
                generated.append(ProjectFile(path=filepath, content=content))
                bar.update(task, advance=1, description=f"Generated: {filepath}")

        return generated

    def _generate_one_file(self, plan: BuildPlan, filepath: str) -> str:
        """Call the LLM to generate the content of a single file."""
        prompt = _FILE_PROMPT.format(
            description  = plan.description,
            stack        = ", ".join(plan.stack),
            instructions = plan.instructions,
            filepath     = filepath,
        )
        messages = [Message(role="user", content=prompt)]

        parts: list[str] = []
        try:
            for chunk in self.provider.stream_with_retry(messages):
                if chunk.text:
                    parts.append(chunk.text)
        except Exception as exc:
            warn(f"Error generating {filepath}: {exc}")
            self._errors.append(f"{filepath}: {exc}")
            return f"# Error generating this file\n# {exc}\n"

        content = "".join(parts)
        return _strip_fences(content)

    # ── Step 3: Write files ────────────────────

    def _write_files(self, files: list[ProjectFile]) -> None:
        """Write all generated files to the output directory."""
        with spinner(f"Writing {len(files)} files to {self.output_dir}…"):
            file_dict = {f.path: f.content for f in files}
            write_project(str(self.output_dir), file_dict)
        ok(f"All files written → {self.output_dir.resolve()}")

    # ── Display helpers ───────────────────────

    def _print_plan(self, plan: BuildPlan) -> None:
        from rich.table import Table
        from rich import box as rbox

        tbl = Table(box=rbox.SIMPLE, border_style="cyan", show_header=False, expand=False)
        tbl.add_column("", style="dim cyan", width=12)
        tbl.add_column("", style="cyan")
        tbl.add_row("Project",  plan.description)
        tbl.add_row("Stack",    ", ".join(plan.stack))
        tbl.add_row("Files",    str(len(plan.files)))
        tbl.add_row("Output",   str(self.output_dir.resolve()))
        console.print(tbl)

        dim("  Files to generate:")
        for f in plan.files:
            dim(f"    • {f}")
        console.print()

    def _print_file_tree(self, files: list["ProjectFile"]) -> None:
        """Render a Rich Tree showing the generated project structure."""
        from rich.tree import Tree
        from rich.text import Text as RText

        tree = Tree(
            RText(f"  📁 {self.output_dir.name}/", style="bold bright_cyan"),
            guide_style="dim cyan",
        )

        # Build nested dict to represent directory structure
        nodes: dict = {}
        for f in files:
            parts = Path(f.path).parts
            cur   = nodes
            for part in parts[:-1]:          # directories
                cur = cur.setdefault(part, {})
            cur[parts[-1]] = None            # file leaf

        def _add_nodes(tree_node, subtree: dict) -> None:
            dirs  = sorted(k for k, v in subtree.items() if isinstance(v, dict))
            fls   = sorted(k for k, v in subtree.items() if v is None)
            for d in dirs:
                branch = tree_node.add(
                    RText(f"📁 {d}/", style="bold cyan")
                )
                _add_nodes(branch, subtree[d])
            for fl in fls:
                ext   = Path(fl).suffix.lower()
                icon  = _file_icon(ext)
                tree_node.add(RText(f"{icon} {fl}", style="vega.secondary"))

        _add_nodes(tree, nodes)
        console.print()
        console.print(tree)
        console.print()

    def _prompt_actions(self, result: "BuildResult") -> None:
        """Ask the user if they want to open in browser or export ZIP."""
        from rich.text import Text as RText

        # Detect if it's a web project (has index.html)
        is_web = any(
            Path(f.path).name in ("index.html", "index.htm")
            for f in result.files
        )

        # ── Export ZIP? ──────────────────────
        try:
            zip_ans = console.input(
                RText.assemble(
                    ("  Export ZIP? ", "cyan"),
                    ("[y/N] ", "dim"),
                ).markup
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            zip_ans = "n"

        if zip_ans in ("y", "yes"):
            with spinner("Creating ZIP archive…"):
                zip_path = zip_project(result.output_dir)
            ok(f"Archive → {zip_path}")
            result.zip_path = zip_path

        # ── Open in browser? (web projects only) ──
        if is_web:
            try:
                browser_ans = console.input(
                    RText.assemble(
                        ("  Open index.html in browser? ", "cyan"),
                        ("[y/N] ", "dim"),
                    ).markup
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                browser_ans = "n"

            if browser_ans in ("y", "yes"):
                import webbrowser
                index = result.output_dir / "index.html"
                webbrowser.open(index.resolve().as_uri())
                ok(f"Opened → {index.resolve()}")

    def _print_summary(self, result: "BuildResult") -> None:
        console.print()
        rule()
        if result.success:
            ok(f"Build complete!  {result.file_count} files  →  {result.output_dir.resolve()}")
        else:
            warn(f"Build finished with {len(result.errors)} error(s).")
            for err in result.errors:
                fail(f"  {err}")
        if result.zip_path:
            ok(f"Archive  →  {result.zip_path}")
        console.print()


# ─────────────────────────────────────────────
#  Utilities
# ─────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """Remove markdown code fences from LLM output."""
    text = text.strip()
    # Remove ```lang and ``` wrappers
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


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
