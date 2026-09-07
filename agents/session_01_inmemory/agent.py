"""session_01_inmemory: 도구가 보는 Session 의 구조."""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def describe_session(tool_context: ToolContext) -> dict[str, object]:
    """지금 실행 중인 세션의 id, 사용자, 이벤트 수를 돌려준다."""
    session = tool_context.session
    return {
        "id": session.id,
        "user_id": session.user_id,
        "events": len(session.events),
    }


root_agent = LlmAgent(
    name="session_inspector",
    model=make_model(),
    description="자기 세션 정보를 알려 주는 에이전트",
    instruction="사용자가 세션에 대해 물으면 describe_session 도구를 쓰고 "
    "결과를 한국어로 알려 준다. 그 외 질문에는 한 문단으로 답한다.",
    tools=[describe_session],
)
