"""state_02_tool_context: 도구가 state 를 읽고 쓴다.

tool_context 인자가 모델에 보이지 않는 것, 도구가 쓴 값이
function_response 이벤트의 delta 에 실리는 것, 턴을 거듭하면 값이
누적되는 것, output_key 가 그대로 동작하는 것을 순서대로 검사한다.
"""

from google.adk.runners import InMemoryRunner

from adk_study.testing import (
    FakeLlm,
    call_reply,
    run_in_session,
    run_turn,
    text_reply,
)
from agents.state_02_tool_context.agent import root_agent


def bump_then_answer() -> FakeLlm:
    """도구를 한 번 부르고 답하는 턴을 꾸민다.

    한 턴에 모델이 두 번 불리므로 응답도 둘이다. 도구를 부르는
    턴마다 새 FakeLlm 이 필요해서 함수로 둔다.
    """
    return FakeLlm(
        replies=[call_reply("bump_counter", {}), text_reply("올렸어요")]
    )


async def test_tool_context_is_hidden_from_model():
    """tool_context 인자는 모델에 보내는 도구 스키마에서 빠진다.

    FakeLlm 이 받은 첫 요청에서 도구 선언을 꺼내 본다. 함수의 유일한
    매개변수가 tool_context 이므로 모델이 보는 선언에는 매개변수가
    하나도 없다.
    """
    fake = bump_then_answer()
    root_agent.model = fake

    await run_turn(root_agent, "올려")

    declaration = fake.requests[0].config.tools[0].function_declarations[0]
    assert declaration.name == "bump_counter"
    assert declaration.parameters is None


async def test_tool_write_appears_in_function_response_delta():
    """도구가 state 에 쓴 값은 function_response 이벤트의 delta 에 실린다.

    events[0] 은 function_call, events[1] 은 function_response 다.
    도구가 tool_context.state 에 쓴 것과 돌려준 것이 같은 이벤트에
    각각 actions.state_delta 와 response 로 들어간다.
    """
    root_agent.model = bump_then_answer()

    events = await run_turn(root_agent, "올려")

    response = events[1]
    assert response.get_function_responses()[0].response == {"result": 1}
    assert response.actions.state_delta == {"count": 1}


async def test_counter_accumulates_across_turns():
    """같은 세션이면 다음 턴의 도구가 앞 턴이 쓴 값을 읽는다.

    Runner 가 function_response 이벤트를 저장할 때 delta 가 세션
    state 에 합쳐지므로, 둘째 턴의 tool_context.state.get("count")
    는 1 을 돌려주고 도구는 2 를 쓴다.
    """
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
    """output_key 는 도구와 무관하게 최종 텍스트 이벤트에 실린다.

    도구가 쓴 count 는 function_response 이벤트에, output_key 가 쓴
    last_answer 는 마지막 이벤트에 따로 실린다. 이벤트마다 delta 가
    다르고 세션 state 에서 합쳐진다.
    """
    root_agent.model = bump_then_answer()

    events = await run_turn(root_agent, "올려")

    assert events[-1].actions.state_delta == {"last_answer": "올렸어요"}
