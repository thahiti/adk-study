"""state_03_prefixes: user:, app:, temp: 접두어의 범위."""

from google.adk.runners import InMemoryRunner

from adk_study.testing import (
    FakeLlm,
    call_reply,
    run_in_session,
    run_turn,
    text_reply,
)
from agents.state_03_prefixes.agent import root_agent


def bump_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[call_reply("bump_counter", {}), text_reply("올렸어요")]
    )


async def test_tool_write_appears_in_function_response_delta():
    root_agent.model = bump_then_answer()

    events = await run_turn(root_agent, "올려")

    response = events[1]
    assert response.get_function_responses()[0].response == {"result": 1}
    assert response.actions.state_delta == {"count": 1}


async def test_counter_accumulates_across_turns():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    root_agent.model = bump_then_answer()
    await run_in_session(runner, session, "올려")
    root_agent.model = bump_then_answer()
    events = await run_in_session(runner, session, "또 올려")

    assert events[1].get_function_responses()[0].response == {"result": 2}
    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    assert stored.state["count"] == 2


async def test_output_key_still_saves_final_text():
    root_agent.model = bump_then_answer()

    events = await run_turn(root_agent, "올려")

    assert events[-1].actions.state_delta == {"last_answer": "올렸어요"}
