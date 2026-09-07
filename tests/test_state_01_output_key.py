"""state_01_output_key: 응답을 state 에 저장하고 다음 턴에 읽는다."""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.state_01_output_key.agent import root_agent


async def test_text_reply_yields_exactly_one_event():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    events = await run_turn(root_agent, "날씨 어때")

    assert len(events) == 1


async def test_event_carries_identity_fields():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    event = (await run_turn(root_agent, "날씨 어때"))[0]

    assert event.id
    assert event.invocation_id.startswith("e-")
    assert event.author == "state_memo"
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
