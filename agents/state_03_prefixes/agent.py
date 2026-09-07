"""state_03_prefixes: user:, app:, temp: 접두어로 범위를 나눈다."""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def bump_counter(tool_context: ToolContext) -> int:
    """세션, 사용자, 앱 범위의 카운터를 각각 1 올린다."""
    state = tool_context.state
    count = state.get("count", 0) + 1
    state["count"] = count
    state["user:total"] = state.get("user:total", 0) + 1
    state["app:hits"] = state.get("app:hits", 0) + 1
    state["temp:last_call"] = "bump_counter"
    return count


root_agent = LlmAgent(
    name="state_scoped",
    model=make_model(),
    description="부를 때마다 카운터를 올리는 에이전트",
    instruction="사용자가 올리라고 하면 bump_counter 도구를 쓰고 새 값을 "
    "한국어로 알려 준다. 직전 답: {last_answer?}",
    tools=[bump_counter],
    output_key="last_answer",
)
