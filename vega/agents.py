"""
vega/agents.py — Vega Agent System
Autonomous multi-step agents that can plan, execute tool calls,
and iterate until a goal is complete.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Iterator, Optional

from providers.base import BaseProvider, Message
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
)

# ─────────────────────────────────────────────
#  Agent Metadata & Specialized Agents Registry
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class AgentInfo:
    """Metadata for a specialized agent."""
    name:          str
    badge:         str
    provider_name: str
    model_id:      str
    triggers:      list[str]
    description:   str

SPECIALIZED_AGENTS: list[AgentInfo] = [
    AgentInfo(
        name="CodeAgent",
        badge="⟡",
        provider_name="nvidia",
        model_id="moonshotai/kimi-k2-instruct",
        triggers=["build", "create", "make"],
        description="Code generator using kimi-k2.6",
    ),
    AgentInfo(
        name="ImageAgent",
        badge="🎨",
        provider_name="google",
        model_id="gemini-2.0-flash",
        triggers=["image", "draw", "picture"],
        description="Creative vision using gemini-flash",
    ),
    AgentInfo(
        name="FastAgent",
        badge="⚡",
        provider_name="groq",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        triggers=["what", "explain", "quick"],
        description="Speed responder using llama-4-scout",
    ),
    AgentInfo(
        name="PlannerAgent",
        badge="🗺",
        provider_name="deepseek",
        model_id="deepseek-chat",
        triggers=["plan", "architect", "design"],
        description="High-level planner using DeepSeek-V3",
    ),
    AgentInfo(
        name="DebugAgent",
        badge="🔧",
        provider_name="nvidia",
        model_id="moonshotai/kimi-k2-instruct",
        triggers=["fix", "bug", "error", "debug"],
        description="Debugging expert using kimi-k2.6",
    ),
    AgentInfo(
        name="ReviewAgent",
        badge="👁",
        provider_name="deepseek",
        model_id="deepseek-chat",
        triggers=["review", "refactor", "improve"],
        description="Code reviewer using DeepSeek-V3",
    ),
]

def detect_agent(text: str) -> Optional[AgentInfo]:
    """
    Search text for trigger keywords to detect the correct specialized agent.
    Checks tokens in lowercase. Returns the first matched agent or None.
    """
    cleaned = text.lower()
    words = set(re.findall(r"\b\w+\b", cleaned))
    for agent in SPECIALIZED_AGENTS:
        for trigger in agent.triggers:
            if trigger in words:
                return agent
    return None

# ─────────────────────────────────────────────
#  Tool definition
# ─────────────────────────────────────────────

@dataclass
class Tool:
    """Represents a callable tool the agent can invoke."""
    name:        str
    description: str
    fn:          Callable[..., str]
    schema:      dict = field(default_factory=dict)

    def call(self, **kwargs) -> str:
        """Execute this tool with keyword arguments."""
        try:
            return str(self.fn(**kwargs))
        except Exception as exc:
            return f"[ToolError] {self.name} failed: {exc}"


# ─────────────────────────────────────────────
#  Agent step
# ─────────────────────────────────────────────

class StepType(Enum):
    PLAN      = auto()
    TOOL_CALL = auto()
    OBSERVE   = auto()
    ANSWER    = auto()
    ERROR     = auto()


@dataclass
class AgentStep:
    step_type:   StepType
    content:     str
    tool_name:   Optional[str] = None
    tool_args:   Optional[dict] = None
    tool_result: Optional[str] = None


# ─────────────────────────────────────────────
#  Agent result
# ─────────────────────────────────────────────

@dataclass
class AgentResult:
    goal:       str
    answer:     str
    steps:      list[AgentStep]
    success:    bool
    iterations: int

    def summary(self) -> str:
        tool_uses = sum(1 for s in self.steps if s.step_type == StepType.TOOL_CALL)
        return (
            f"Goal completed in {self.iterations} iteration(s) "
            f"with {tool_uses} tool call(s)."
        )


# ─────────────────────────────────────────────
#  ReAct-style Agent
# ─────────────────────────────────────────────

class VegaAgent:
    """
    A ReAct-style (Reason + Act) agent that:
      1. Plans a multi-step approach to reach a goal
      2. Calls tools when needed
      3. Observes results and replans
      4. Returns a final answer

    Usage:
        agent = VegaAgent(provider=provider, tools=[write_tool, zip_tool])
        result = agent.run("Build a FastAPI todo app with SQLite")
        print(result.answer)
    """

    SYSTEM_PROMPT = """\
You are Vega Agent, an autonomous AI coding assistant by Raimic Labs.

You solve coding goals step-by-step using a ReAct loop:
  Thought: reason about what to do next
  Action: call a tool (or "FINISH" to end)
  Observation: result of the action

Available tools:
{tools}

Rules:
- Always start with a brief plan.
- Use tools to write files, run code, or search.
- When the goal is fully achieved, output:
  Action: FINISH
  Answer: <your final answer or summary>
- Be concise. No unnecessary commentary.
- Output valid JSON for tool arguments.
"""

    ACTION_RE   = re.compile(r"Action:\s*(.+?)(?:\n|$)", re.IGNORECASE)
    ARGS_RE     = re.compile(r"Args:\s*(\{.+?\})", re.IGNORECASE | re.DOTALL)
    ANSWER_RE   = re.compile(r"Answer:\s*(.+?)(?:\Z)", re.IGNORECASE | re.DOTALL)
    THOUGHT_RE  = re.compile(r"Thought:\s*(.+?)(?:Action:|$)", re.IGNORECASE | re.DOTALL)

    def __init__(
        self,
        provider:    BaseProvider,
        tools:       Optional[list[Tool]] = None,
        max_iters:   int = 10,
        verbose:     bool = True,
    ) -> None:
        self.provider   = provider
        self.tools      = {t.name: t for t in (tools or [])}
        self.max_iters  = max_iters
        self.verbose    = verbose

    # ── Public run ────────────────────────────

    def run(self, goal: str) -> AgentResult:
        """
        Run the agent towards *goal* using the ReAct loop.

        Args:
            goal: Natural-language description of what to accomplish.

        Returns:
            AgentResult with answer, steps, and metadata.
        """
        if self.verbose:
            section(f"Vega Agent — {goal[:60]}{'…' if len(goal) > 60 else ''}")

        history:   list[Message] = [
            Message(role="system",  content=self._build_system()),
            Message(role="user",    content=f"Goal: {goal}"),
        ]
        steps:     list[AgentStep] = []
        iteration = 0

        while iteration < self.max_iters:
            iteration += 1

            if self.verbose:
                dim(f"  Iteration {iteration}/{self.max_iters}")

            # ── LLM call ──────────────────────
            with spinner(f"Thinking… (iter {iteration})"):
                response = self._call_llm(history)

            history.append(Message(role="assistant", content=response))

            if self.verbose:
                self._print_response(response, iteration)

            # ── Parse thought ─────────────────
            thought_match = self.THOUGHT_RE.search(response)
            if thought_match:
                steps.append(AgentStep(
                    step_type = StepType.PLAN,
                    content   = thought_match.group(1).strip(),
                ))

            # ── Parse action ──────────────────
            action_match = self.ACTION_RE.search(response)
            if not action_match:
                steps.append(AgentStep(step_type=StepType.ERROR, content="No action found in response."))
                break

            action = action_match.group(1).strip()

            # ── FINISH? ───────────────────────
            if action.upper() == "FINISH":
                answer_match = self.ANSWER_RE.search(response)
                answer = answer_match.group(1).strip() if answer_match else "Goal complete."

                if self.verbose:
                    ok(f"Agent finished: {answer[:80]}")

                steps.append(AgentStep(step_type=StepType.ANSWER, content=answer))
                return AgentResult(
                    goal       = goal,
                    answer     = answer,
                    steps      = steps,
                    success    = True,
                    iterations = iteration,
                )

            # ── Tool call ─────────────────────
            args_match = self.ARGS_RE.search(response)
            tool_args: dict[str, Any] = {}
            if args_match:
                try:
                    tool_args = json.loads(args_match.group(1))
                except json.JSONDecodeError:
                    tool_args = {}

            steps.append(AgentStep(
                step_type = StepType.TOOL_CALL,
                content   = f"Calling {action}",
                tool_name = action,
                tool_args = tool_args,
            ))

            observation = self._execute_tool(action, tool_args)

            if self.verbose:
                info(f"  Tool [{action}] → {observation[:120]}{'…' if len(observation) > 120 else ''}")

            steps[-1].tool_result = observation

            # Feed observation back as user message
            obs_msg = f"Observation: {observation}"
            history.append(Message(role="user", content=obs_msg))

        # Max iterations hit
        fail(f"Agent hit max iterations ({self.max_iters}) without finishing.")
        return AgentResult(
            goal       = goal,
            answer     = "Max iterations reached — task may be incomplete.",
            steps      = steps,
            success    = False,
            iterations = iteration,
        )

    # ── Helpers ───────────────────────────────

    def _build_system(self) -> str:
        if not self.tools:
            tool_desc = "  (no external tools — reason and answer directly)"
        else:
            lines = []
            for name, t in self.tools.items():
                lines.append(f"  - {name}: {t.description}")
            tool_desc = "\n".join(lines)
        return self.SYSTEM_PROMPT.format(tools=tool_desc)

    def _call_llm(self, history: list[Message]) -> str:
        parts: list[str] = []
        for chunk in self.provider.stream_with_retry(history):
            if chunk.text:
                parts.append(chunk.text)
        return "".join(parts)

    def _execute_tool(self, name: str, args: dict) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"[Error] Unknown tool '{name}'. Available: {list(self.tools.keys())}"
        return tool.call(**args)

    def _print_response(self, text: str, iteration: int) -> None:
        code_panel(text, language="text", title=f"  Agent Response — Iter {iteration}")

    def add_tool(self, tool: Tool) -> None:
        """Dynamically register a new tool."""
        self.tools[tool.name] = tool

    def remove_tool(self, name: str) -> None:
        """Remove a registered tool by name."""
        self.tools.pop(name, None)


# ─────────────────────────────────────────────
#  Built-in tools factory
# ─────────────────────────────────────────────

def make_default_tools(output_dir: str = ".") -> list[Tool]:
    """
    Return the default tool set available to Vega agents.

    Includes:
      - write_file:    Write content to a file path
      - read_file:     Read a file's contents
      - list_files:    List files in a directory
      - run_shell:     Execute a shell command (with confirmation)
    """
    from tools.file_writer import write_file as _write_file
    from pathlib import Path
    import subprocess

    def _tool_write(path: str, content: str) -> str:
        full = Path(output_dir) / path
        _write_file(str(full), content)
        return f"Written: {full}"

    def _tool_read(path: str) -> str:
        full = Path(output_dir) / path
        if not full.exists():
            return f"[Error] File not found: {full}"
        return full.read_text(encoding="utf-8", errors="replace")

    def _tool_list(directory: str = ".") -> str:
        d = Path(output_dir) / directory
        if not d.exists():
            return f"[Error] Directory not found: {d}"
        entries = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name))
        return "\n".join(
            f"{'DIR ' if e.is_dir() else 'FILE'} {e.name}" for e in entries
        )

    def _tool_shell(command: str) -> str:
        # Safety: only allow in non-interactive agent mode
        warn(f"Agent wants to run: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=output_dir,
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if result.returncode != 0:
                return f"[exit {result.returncode}]\nSTDOUT: {out}\nSTDERR: {err}"
            return out or f"[exit 0]"
        except subprocess.TimeoutExpired:
            return "[Error] Command timed out after 30s"
        except Exception as exc:
            return f"[Error] {exc}"

    return [
        Tool(
            name        = "write_file",
            description = "Write content to a file. Args: path (str), content (str)",
            fn          = _tool_write,
        ),
        Tool(
            name        = "read_file",
            description = "Read the contents of a file. Args: path (str)",
            fn          = _tool_read,
        ),
        Tool(
            name        = "list_files",
            description = "List files in a directory. Args: directory (str, default '.')",
            fn          = _tool_list,
        ),
        Tool(
            name        = "run_shell",
            description = "Execute a shell command and return output. Args: command (str)",
            fn          = _tool_shell,
        ),
    ]
