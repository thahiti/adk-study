"""session_03_include_contents: 이력을 모델에 보내지 않는 에이전트.

세션에 쌓인 events 가 곧 모델 입력이 되는 것이 LlmAgent 의 기본이다.
include_contents 로 그 연결을 끊으면 세션 저장과 모델 컨텍스트가
별개라는 점이 드러난다.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def describe_session(tool_context: ToolContext) -> dict[str, object]:
    """지금 실행 중인 세션의 id, 사용자, 이벤트 수를 돌려준다.

    이 도구가 세는 events 는 모델이 받는 contents 와 다르다.
    include_contents="none" 이어도 세션에는 앞 턴이 그대로 남아
    있으므로 events 수는 턴마다 계속 늘어난다.
    """
    session = tool_context.session
    return {
        "id": session.id,
        "user_id": session.user_id,
        "events": len(session.events),
    }


root_agent = LlmAgent(
    name="session_forgetful",
    model=make_model(),
    description="이력을 보지 않고 매번 새로 답하는 에이전트",
    instruction="사용자가 세션에 대해 물으면 describe_session 도구를 쓰고 "
    "결과를 한국어로 알려 준다. 그 외 질문에는 한 문단으로 답한다.",
    tools=[describe_session],
    # 허용 값은 "default" 와 "none" 둘뿐이다.
    # "none" 은 이력을 통째로 빼는 것이 아니라 이번 턴, 즉 마지막
    # 사용자 메시지부터의 이벤트만 보낸다. 그래서 같은 턴 안에서
    # 일어난 도구 호출과 그 결과는 모델에 전달되어 도구가 정상으로
    # 동작한다.
    include_contents="none",
)
