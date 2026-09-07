"""state_03_prefixes: user:, app:, temp: 접두어의 범위."""

from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session

from adk_study.testing import FakeLlm, call_reply, run_in_session, text_reply
from agents.state_03_prefixes.agent import root_agent


def bump_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[call_reply("bump_counter", {}), text_reply("올렸어요")]
    )


async def bump(runner: InMemoryRunner, user_id: str) -> tuple[list, Session]:
    """user_id 로 새 세션을 만들어 한 번 올리고 저장된 세션을 돌려준다."""
    session = await runner.session_service.create_session(
        app_name="test", user_id=user_id
    )
    root_agent.model = bump_then_answer()
    events = await run_in_session(runner, session, "올려")
    stored = await runner.session_service.get_session(
        app_name="test", user_id=user_id, session_id=session.id
    )
    assert stored is not None
    return events, stored


async def test_temp_key_is_dropped_from_delta_and_state():
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    events, stored = await bump(runner, "u1")

    delta = events[1].actions.state_delta
    assert delta == {"count": 1, "user:total": 1, "app:hits": 1}
    assert "temp:last_call" not in stored.state


async def test_user_key_is_shared_across_sessions_of_same_user():
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    await bump(runner, "u1")
    _, second = await bump(runner, "u1")

    assert second.state["count"] == 1
    assert second.state["user:total"] == 2


async def test_app_key_is_shared_across_users():
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    await bump(runner, "u1")
    _, other = await bump(runner, "u2")

    assert other.state["app:hits"] == 2
    assert other.state["user:total"] == 1
