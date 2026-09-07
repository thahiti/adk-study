"""session_01_inmemory: Session 의 구조와 이벤트 누적."""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, call_reply, run_in_session, text_reply
from agents.session_01_inmemory.agent import root_agent


def describe_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[
            call_reply("describe_session", {}),
            text_reply("알려 드렸어요"),
        ]
    )


async def test_new_session_has_identity_and_empty_history():
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    assert session.app_name == "test"
    assert session.user_id == "user"
    assert session.id
    assert session.state == {}
    assert session.events == []


async def test_tool_sees_session_with_events_so_far():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    root_agent.model = describe_then_answer()
    first = await run_in_session(runner, session, "세션 알려 줘")
    root_agent.model = describe_then_answer()
    second = await run_in_session(runner, session, "다시")

    seen_first = first[1].get_function_responses()[0].response
    seen_second = second[1].get_function_responses()[0].response
    assert seen_first == {"id": session.id, "user_id": "user", "events": 2}
    assert seen_second["events"] == 6


async def test_each_turn_appends_user_and_agent_events():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    root_agent.model = describe_then_answer()
    await run_in_session(runner, session, "세션 알려 줘")

    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    authors = [e.author for e in stored.events]
    assert authors == ["user"] + ["session_inspector"] * 3
    assert stored.last_update_time >= session.last_update_time


async def test_sessions_of_same_user_are_independent():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    first = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )
    root_agent.model = describe_then_answer()
    await run_in_session(runner, first, "세션 알려 줘")

    second = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    listed = await runner.session_service.list_sessions(
        app_name="test", user_id="user"
    )
    assert {s.id for s in listed.sessions} == {first.id, second.id}
    assert second.events == []
