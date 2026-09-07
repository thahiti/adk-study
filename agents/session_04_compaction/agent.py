"""session_04_compaction: App 이 두 턴마다 이력을 요약해 압축한다."""

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
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
    name="session_compact",
    model=make_model(),
    description="자기 세션 정보를 알려 주는 에이전트",
    instruction="사용자가 세션에 대해 물으면 describe_session 도구를 쓰고 "
    "결과를 한국어로 알려 준다. 그 외 질문에는 한 문단으로 답한다.",
    tools=[describe_session],
)

# App 은 root_agent 에 앱 수준 설정(플러그인, 이력 압축 등)을 묶는
# 단위다. adk web 은 이 모듈에서 App 인스턴스인 app 을 root_agent 보다
# 먼저 찾아 쓰므로 root_agent 는 그대로 두고 app 만 더하면 된다.
app = App(
    # adk web 은 폴더명으로 세션을 만들고 Runner 는 app.name 으로 세션을
    # 찾는다. 둘이 다르면 세션을 못 찾으므로 폴더명과 같게 둔다.
    name="session_04_compaction",
    root_agent=root_agent,
    # 아직 요약에 안 들어간 턴이 compaction_interval 개가 되면 그 턴이
    # 끝난 뒤 요약한다. overlap_size 는 앞 요약 범위의 끝에서 몇 턴을
    # 겹쳐 다시 넣을지다. 0 이면 요약 범위가 겹치지 않아 어느 턴이 어느
    # 요약에 들어갔는지 보기 쉽다.
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=2, overlap_size=0
    ),
)
