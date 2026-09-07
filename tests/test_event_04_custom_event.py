"""event_04_custom_event: 직접 만든 Event 를 yield 하는 에이전트.

root_agent 가 모델을 갖지 않으므로 FakeLlm 없이 그대로 돌린다.
"""

from google.adk.runners import InMemoryRunner

from adk_study.testing import run_in_session, run_turn
from agents.event_04_custom_event.agent import root_agent


async def test_custom_agent_yields_two_events_without_llm():
    events = await run_turn(root_agent, "시작")

    # yield 한 Event 가 그대로 밖으로 나온다. Runner 는 LLM 이 만든
    # 이벤트와 직접 만든 이벤트를 구분하지 않는다.
    assert [e.content.parts[0].text for e in events] == [
        "첫 번째 알림",
        "두 번째 알림",
    ]
    assert {e.author for e in events} == {"event_custom"}


async def test_events_share_invocation_id_from_context():
    events = await run_turn(root_agent, "시작")

    # ctx.invocation_id 를 그대로 실었으므로 Runner 가 턴을 시작할 때
    # 만든 "e-" 값이 두 이벤트에 똑같이 들어 있다
    assert events[0].invocation_id == events[1].invocation_id
    assert events[0].invocation_id.startswith("e-")


async def test_second_event_carries_state_delta():
    events = await run_turn(root_agent, "시작")

    # actions 를 주지 않은 첫 이벤트는 기본값 EventActions() 라 비어 있다
    assert events[0].actions.state_delta == {}
    assert events[1].actions.state_delta == {"announced": 2}


async def test_state_delta_is_applied_to_session():
    """state_delta 는 세션에 기록되는 시점에 세션 상태로 반영된다.

    Runner 가 이벤트를 session_service.append_event 에 넘기고,
    거기서 state_delta 를 session.state 에 합친다. 에이전트는
    상태를 직접 고치지 않고 이벤트에 실어 보내기만 한다.
    """
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "시작")
    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )

    assert stored is not None
    # 사용자 메시지 뒤에 직접 만든 이벤트 둘이 순서대로 남는다
    assert [e.author for e in stored.events] == [
        "user",
        "event_custom",
        "event_custom",
    ]
    assert stored.state["announced"] == 2
