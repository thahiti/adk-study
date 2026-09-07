"""session_01_inmemory: Session 의 구조와 이벤트 누적."""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.session_01_inmemory.agent import root_agent


async def test_text_reply_yields_exactly_one_event():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    events = await run_turn(root_agent, "날씨 어때")

    assert len(events) == 1


async def test_event_carries_identity_fields():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    event = (await run_turn(root_agent, "날씨 어때"))[0]

    assert event.id
    assert event.invocation_id.startswith("e-")
    assert event.author == "session_inspector"
    assert event.timestamp > 0


async def test_event_content_and_actions_defaults():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    event = (await run_turn(root_agent, "날씨 어때"))[0]

    assert event.content.role == "model"
    assert event.content.parts[0].text == "오늘은 맑아요"
    assert event.partial is None
    assert event.actions.state_delta == {}
    assert event.actions.transfer_to_agent is None
    assert event.is_final_response()
