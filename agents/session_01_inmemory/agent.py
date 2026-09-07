"""session_01_inmemory: 도구가 보는 Session 의 구조.

에이전트 코드는 event_01_text 에 describe_session 도구 하나를 더한
것이다. 도구는 답을 만들지 않고 자기가 실행되는 세션의 id, user_id,
events 수를 그대로 돌려준다. 세션이 어디에 어떤 모양으로 있고 턴을
거듭하면 무엇이 쌓이는지 보는 것이 목적이다.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def describe_session(tool_context: ToolContext) -> dict[str, object]:
    """지금 실행 중인 세션의 id, 사용자, 이벤트 수를 돌려준다.

    tool_context.session 은 Runner 가 이번 턴을 시작할 때
    SessionService 에서 꺼내 온 Session 객체다. Runner 는 이벤트가
    생길 때마다 이 객체에 먼저 붙이고 저장소에도 반영하므로 도구는
    이번 턴의 사용자 메시지와 자기를 부른 function_call 이벤트까지
    센다.
    """
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
