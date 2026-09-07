"""state_03_prefixes: 도구가 state 를 읽고 쓴다."""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def bump_counter(tool_context: ToolContext) -> int:
    """세션의 count 를 1 올리고 새 값을 돌려준다."""
    count = tool_context.state.get("count", 0) + 1
    tool_context.state["count"] = count
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
