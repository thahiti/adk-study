"""state_01_output_key: 응답을 state 에 저장하고 다음 턴에 읽는다.

output_key 가 응답을 이벤트 delta 에 싣는 것, Runner 가 그 delta 를
세션 state 에 반영하는 것, 다음 턴 instruction 에 그 값이 들어가는 것을
순서대로 검사한다.
"""

import pytest
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, run_turn, text_reply
from agents.state_01_output_key.agent import root_agent


async def test_final_event_carries_answer_in_state_delta():
    """output_key 는 응답 이벤트의 actions.state_delta 에 실린다.

    event_01_text 에서는 같은 자리가 빈 사전이었다.
    """
    root_agent.model = FakeLlm(replies=[text_reply("파란색이 좋아요")])

    events = await run_turn(root_agent, "무슨 색이 좋아")

    assert events[-1].actions.state_delta == {"last_answer": "파란색이 좋아요"}


async def test_answer_is_stored_in_session_state():
    """delta 는 Runner 가 이벤트를 저장할 때 세션 state 에 합쳐진다.

    run_turn 은 세션을 안에서 만들고 버리므로, 저장된 state 를
    다시 읽으려면 세션을 직접 만들어 session_service 로 조회한다.
    """
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
    """{last_answer?} 는 턴마다 그 시점의 state 값으로 치환된다.

    FakeLlm 이 받은 요청을 requests 에 쌓아 두므로, 각 턴의
    system_instruction 을 꺼내 첫 턴은 비어 있고 둘째 턴부터
    직전 답이 들어가는지 본다.
    """
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


async def test_required_placeholder_fails_when_key_is_missing():
    """`?` 가 없는 {last_answer} 는 키가 없는 첫 턴에 KeyError 를 낸다.

    치환은 모델을 부르기 전에 요청을 만들면서 일어나므로,
    예외가 run_async 밖으로 나오고 그 턴은 응답 없이 끝난다.
    """
    strict = LlmAgent(
        name="state_strict",
        model=FakeLlm(replies=[text_reply("파란색이 좋아요")]),
        instruction="직전 답: {last_answer}",
    )

    with pytest.raises(KeyError):
        await run_turn(strict, "무슨 색이 좋아")
