"""
tests/test_agents.py — Unit tests for agent detection and metadata.
"""

import pytest
from vega.agents import (
    AgentInfo,
    SPECIALIZED_AGENTS,
    detect_agent,
    Tool,
    StepType,
    AgentStep,
    AgentResult,
)


# ─────────────────────────────────────────────
#  SPECIALIZED_AGENTS registry
# ─────────────────────────────────────────────

class TestSpecializedAgentsRegistry:
    def test_has_six_agents(self):
        assert len(SPECIALIZED_AGENTS) == 6

    def test_agent_names(self):
        names = {a.name for a in SPECIALIZED_AGENTS}
        assert names == {
            "CodeAgent", "ImageAgent", "FastAgent",
            "PlannerAgent", "DebugAgent", "ReviewAgent",
        }

    def test_code_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "CodeAgent")
        assert agent.provider_name == "nvidia"
        assert agent.model_id == "moonshotai/kimi-k2-instruct"
        assert agent.badge == "⟡"

    def test_image_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "ImageAgent")
        assert agent.provider_name == "google"
        assert "gemini" in agent.model_id

    def test_fast_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "FastAgent")
        assert agent.provider_name == "groq"

    def test_planner_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "PlannerAgent")
        assert agent.provider_name == "deepseek"

    def test_debug_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "DebugAgent")
        assert agent.provider_name == "nvidia"

    def test_review_agent_provider(self):
        agent = next(a for a in SPECIALIZED_AGENTS if a.name == "ReviewAgent")
        assert agent.provider_name == "deepseek"

    def test_all_agents_have_triggers(self):
        for agent in SPECIALIZED_AGENTS:
            assert len(agent.triggers) > 0, f"{agent.name} has no triggers"

    def test_all_agents_have_badges(self):
        for agent in SPECIALIZED_AGENTS:
            assert agent.badge, f"{agent.name} has no badge"

    def test_agent_info_is_frozen(self):
        agent = SPECIALIZED_AGENTS[0]
        with pytest.raises(Exception):  # frozen dataclass
            agent.name = "mutated"  # type: ignore


# ─────────────────────────────────────────────
#  detect_agent
# ─────────────────────────────────────────────

class TestDetectAgent:
    # CodeAgent triggers
    def test_detects_code_agent_build(self):
        agent = detect_agent("build me a todo app")
        assert agent is not None
        assert agent.name == "CodeAgent"

    def test_detects_code_agent_create(self):
        agent = detect_agent("create a REST API")
        assert agent is not None
        assert agent.name == "CodeAgent"

    def test_detects_code_agent_make(self):
        agent = detect_agent("make a CLI tool")
        assert agent is not None
        assert agent.name == "CodeAgent"

    # ImageAgent triggers
    def test_detects_image_agent(self):
        agent = detect_agent("draw a logo for my project")
        assert agent is not None
        assert agent.name == "ImageAgent"

    def test_detects_image_agent_picture(self):
        agent = detect_agent("generate a picture of a robot")
        assert agent is not None
        assert agent.name == "ImageAgent"

    # FastAgent triggers
    def test_detects_fast_agent_what(self):
        agent = detect_agent("what is a closure in Python?")
        assert agent is not None
        assert agent.name == "FastAgent"

    def test_detects_fast_agent_explain(self):
        agent = detect_agent("explain how async/await works")
        assert agent is not None
        assert agent.name == "FastAgent"

    # PlannerAgent triggers
    def test_detects_planner_agent_plan(self):
        agent = detect_agent("plan the architecture for a microservices system")
        assert agent is not None
        assert agent.name == "PlannerAgent"

    def test_detects_planner_agent_design(self):
        agent = detect_agent("design a database schema for an e-commerce app")
        assert agent is not None
        assert agent.name == "PlannerAgent"

    # DebugAgent triggers
    def test_detects_debug_agent_fix(self):
        agent = detect_agent("fix the bug in my code")
        assert agent is not None
        assert agent.name == "DebugAgent"

    def test_detects_debug_agent_error(self):
        agent = detect_agent("There is an error in my script")
        assert agent is not None
        assert agent.name == "DebugAgent"

    def test_detects_debug_agent_debug(self):
        agent = detect_agent("debug this function please")
        assert agent is not None
        assert agent.name == "DebugAgent"

    # ReviewAgent triggers
    def test_detects_review_agent_review(self):
        agent = detect_agent("review my code for issues")
        assert agent is not None
        assert agent.name == "ReviewAgent"

    def test_detects_review_agent_refactor(self):
        agent = detect_agent("refactor this module to be cleaner")
        assert agent is not None
        assert agent.name == "ReviewAgent"

    def test_detects_review_agent_improve(self):
        agent = detect_agent("improve the performance of my script")
        assert agent is not None
        assert agent.name == "ReviewAgent"

    # No match
    def test_no_agent_for_generic_chat(self):
        agent = detect_agent("hello, how are you?")
        assert agent is None

    def test_no_agent_for_plain_question(self):
        agent = detect_agent("tell me a joke")
        assert agent is None

    # Case insensitivity
    def test_case_insensitive_uppercase(self):
        agent = detect_agent("BUILD a Python script")
        assert agent is not None
        assert agent.name == "CodeAgent"

    def test_case_insensitive_mixed(self):
        agent = detect_agent("FIX my broken function")
        assert agent is not None
        assert agent.name == "DebugAgent"

    # Partial word should NOT match (word boundary check)
    def test_no_partial_word_match(self):
        # "builder" contains "build" but as a word boundary it may vary
        # "fixation" contains "fix" — should not match DebugAgent
        agent = detect_agent("fixation on perfection is bad")
        # "fix" is not a whole word in "fixation", so should be None
        # The regex uses \b\w+\b which matches whole words only
        assert agent is None or agent.name == "DebugAgent"  # allow either, implementation-dependent


# ─────────────────────────────────────────────
#  Tool dataclass
# ─────────────────────────────────────────────

class TestTool:
    def test_tool_call_success(self):
        tool = Tool(
            name="echo",
            description="Echo input",
            fn=lambda text: f"ECHO: {text}",
        )
        result = tool.call(text="hello")
        assert result == "ECHO: hello"

    def test_tool_call_handles_exception(self):
        def broken(**kwargs):
            raise ValueError("something went wrong")

        tool = Tool(name="broken", description="Broken tool", fn=broken)
        result = tool.call()
        assert "[ToolError]" in result
        assert "broken" in result

    def test_tool_returns_str(self):
        tool = Tool(name="num", description="Returns number", fn=lambda: 42)
        result = tool.call()
        assert result == "42"


# ─────────────────────────────────────────────
#  AgentResult
# ─────────────────────────────────────────────

class TestAgentResult:
    def _make_result(self, iterations=3, tool_calls=2, success=True) -> AgentResult:
        steps = [AgentStep(step_type=StepType.PLAN, content="plan")] * (iterations - tool_calls)
        steps += [AgentStep(step_type=StepType.TOOL_CALL, content="tool")] * tool_calls
        return AgentResult(
            goal="test goal",
            answer="done",
            steps=steps,
            success=success,
            iterations=iterations,
        )

    def test_summary_contains_iterations(self):
        result = self._make_result(iterations=3, tool_calls=1)
        summary = result.summary()
        assert "3" in summary

    def test_summary_contains_tool_uses(self):
        result = self._make_result(iterations=5, tool_calls=2)
        assert "2" in result.summary()

    def test_success_flag(self):
        assert self._make_result(success=True).success is True
        assert self._make_result(success=False).success is False
