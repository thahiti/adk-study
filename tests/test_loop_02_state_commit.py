"""loop_02_state_commit: yield 뒤에 state_delta 가 세션에 반영되어 있다."""

from google.adk.runners import InMemoryRunner

from adk_study.testing import run_in_session
from agents.loop_02_state_commit.agent import root_agent
from agents.loop_02_state_commit.main import APP_NAME, USER_ID, run


async def test_state_is_visible_only_after_yield(capsys):
    """세 줄의 순서로 반영 시점이 yield 사이라는 것을 보인다.

    러너 쪽 출력이 두 읽기 사이에 있어야 delta 가 합쳐진 곳이
    에이전트 안이 아니라 러너 안이라는 것이 드러난다.
    """
    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    before = lines.index("agent: announced before yield = None")
    got = lines.index("runner: got 두 번째 알림")
    after = lines.index("agent: announced after yield = 2")
    assert before < got < after


async def test_third_event_reports_committed_value():
    """셋째 이벤트는 읽은 값을 알리기만 하고 delta 를 싣지 않는다."""
    events = await run(root_agent, "시작")

    assert events[-1].content.parts[0].text == "state 반영 확인: 2"
    assert events[-1].actions.state_delta == {}


async def test_session_service_keeps_committed_state():
    """세션 서비스에 남은 state 도 2 다.

    에이전트가 읽는 ctx.session 은 세션 서비스가 내준 사본이라,
    거기서 2 가 보인다고 저장된 세션까지 바뀌었다는 보장은 없다.
    턴이 끝난 뒤 다시 조회해 저장 쪽도 2 인지 따로 확인한다.
    """
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    await run_in_session(runner, session, "시작")

    stored = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    assert stored is not None
    assert stored.state["announced"] == 2
