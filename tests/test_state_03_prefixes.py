"""state_03_prefixes: user:, app:, temp: 접두어의 범위.

테스트 하나 안에서는 러너 하나를 여러 세션이 함께 쓴다. user: 와
app: 값은 러너가 가진 세션 서비스 안에 있으므로 러너를 새로 만들면
함께 사라진다.
"""

from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session

from adk_study.testing import FakeLlm, call_reply, run_in_session, text_reply
from agents.state_03_prefixes.agent import root_agent


def bump_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[call_reply("bump_counter", {}), text_reply("올렸어요")]
    )


async def bump(runner: InMemoryRunner, user_id: str) -> tuple[list, Session]:
    """user_id 로 새 세션을 만들어 한 번 올리고 저장된 세션을 돌려준다.

    run_in_session 이 돌려주는 이벤트에는 세션 state 전체가 없으므로
    get_session 으로 다시 읽는다. 이때 세션 서비스가 user: 와 app: 을
    합쳐서 돌려주므로 세 범위를 한 dict 에서 비교할 수 있다.
    """
    session = await runner.session_service.create_session(
        app_name="test", user_id=user_id
    )
    # FakeLlm 은 답을 하나씩 소비하므로 턴마다 새로 끼운다.
    root_agent.model = bump_then_answer()
    events = await run_in_session(runner, session, "올려")
    stored = await runner.session_service.get_session(
        app_name="test", user_id=user_id, session_id=session.id
    )
    assert stored is not None
    return events, stored


async def test_temp_key_is_dropped_from_delta_and_state():
    """temp: 는 도구가 썼어도 이벤트 delta 와 저장된 state 에 없다."""
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    events, stored = await bump(runner, "u1")

    # events[0] 은 function_call, events[1] 은 도구가 쓴 delta 를
    # 실은 function_response 이벤트다. 도구는 temp:last_call 도 썼지만
    # 세션 서비스가 저장 전에 지웠으므로 세 키만 남는다.
    delta = events[1].actions.state_delta
    assert delta == {"count": 1, "user:total": 1, "app:hits": 1}
    assert "temp:last_call" not in stored.state


async def test_user_key_is_shared_across_sessions_of_same_user():
    """같은 user_id 의 새 세션에서 count 는 새로, user: 는 이어서 센다."""
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    await bump(runner, "u1")
    _, second = await bump(runner, "u1")

    assert second.state["count"] == 1
    assert second.state["user:total"] == 2


async def test_app_key_is_shared_across_users():
    """다른 user_id 의 세션에서 app: 만 이어서 센다."""
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    await bump(runner, "u1")
    _, other = await bump(runner, "u2")

    assert other.state["app:hits"] == 2
    assert other.state["user:total"] == 1


async def test_new_session_starts_with_merged_user_and_app_state():
    """create_session 이 돌려주는 세션에 user: 와 app: 값이 이미 있다.

    세션 자체는 비어 있다. 세션 서비스가 사용자 저장소와 앱 저장소의
    값에 접두어를 다시 붙여 합쳐서 돌려준다.
    """
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    await bump(runner, "u1")

    fresh = await runner.session_service.create_session(
        app_name="test", user_id="u1"
    )

    assert fresh.state == {"user:total": 1, "app:hits": 1}
    # InMemorySessionService 는 접두어를 뗀 키로 범위별 dict 에 보관한다.
    # SqliteSessionService 도 같은 방식으로 user_states, app_states
    # 테이블에 나눠 둔다.
    service = runner.session_service
    assert service.user_state["test"]["u1"] == {"total": 1}
    assert service.app_state["test"] == {"hits": 1}
