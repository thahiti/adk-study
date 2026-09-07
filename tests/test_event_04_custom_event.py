"""event_04_custom_event: 직접 만든 Event 를 yield 하는 에이전트."""

from adk_study.testing import run_turn
from agents.event_04_custom_event.agent import root_agent


async def test_custom_agent_yields_two_events_without_llm():
    events = await run_turn(root_agent, "시작")

    assert [e.content.parts[0].text for e in events] == [
        "첫 번째 알림",
        "두 번째 알림",
    ]
    assert {e.author for e in events} == {"event_custom"}


async def test_events_share_invocation_id_from_context():
    events = await run_turn(root_agent, "시작")

    assert events[0].invocation_id == events[1].invocation_id
    assert events[0].invocation_id.startswith("e-")


async def test_second_event_carries_state_delta():
    events = await run_turn(root_agent, "시작")

    assert events[0].actions.state_delta == {}
    assert events[1].actions.state_delta == {"announced": 2}
