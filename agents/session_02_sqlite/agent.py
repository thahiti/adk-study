"""session_02_sqlite: 코드는 같고 세션 서비스만 SQLite 로 바꾼다.

session_01_inmemory 와 비교해 에이전트 이름만 다르다.
세션을 메모리에 둘지 파일에 남길지는 에이전트가 아니라
Runner 에 넣는 SessionService 가 정하므로 이 파일은 손댈 곳이 없다.
도구도 tool_context.session 만 읽을 뿐 저장소가 무엇인지 모른다.
"""

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
    name="session_persistent",
    model=make_model(),
    description="자기 세션 정보를 알려 주는 에이전트",
    instruction="사용자가 세션에 대해 물으면 describe_session 도구를 쓰고 "
    "결과를 한국어로 알려 준다. 그 외 질문에는 한 문단으로 답한다.",
    tools=[describe_session],
)
