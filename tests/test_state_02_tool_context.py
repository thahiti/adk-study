"""state_02_tool_context: 도구가 state 를 읽고 쓴다."""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, run_turn, text_reply
from agents.state_02_tool_context.agent import root_agent


async def test_final_event_carries_answer_in_state_delta():
    root_agent.model = FakeLlm(replies=[text_reply("파란색이 좋아요")])

    events = await run_turn(root_agent, "무슨 색이 좋아")

    assert events[-1].actions.state_delta == {"last_answer": "파란색이 좋아요"}


async def test_answer_is_stored_in_session_state():
    root_agent.model = FakeLlm(replies=[text_reply("파란색이 좋아요")])
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "무슨 색이 좋아")

    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    assert stored.state == {"last_answer": "파란색이 좋아요"}


async def test_previous_answer_is_injected_into_instruction():
    fake = FakeLlm(replies=[text_reply("파란색이 좋아요"), text_reply("네")])
    root_agent.model = fake
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "무슨 색이 좋아")
    await run_in_session(runner, session, "아까 뭐라고 했지")

    first = str(fake.requests[0].config.system_instruction)
    second = str(fake.requests[1].config.system_instruction)
    assert "파란색이 좋아요" not in first
    assert "파란색이 좋아요" in second
