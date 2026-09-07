"""event_01_text: 텍스트 응답 이벤트의 구조."""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.event_01_text.agent import root_agent


async def test_hello_returns_model_text_as_final_event():
    fake = FakeLlm(replies=[text_reply("안녕하세요, 반가워요")])
    root_agent.model = fake

    events = await run_turn(root_agent, "안녕")

    assert events[-1].author == "event_text"
    assert events[-1].is_final_response()
    assert events[-1].content.parts[0].text == "안녕하세요, 반가워요"


async def test_instruction_is_sent_as_system_instruction():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    system = fake.requests[0].config.system_instruction
    assert "한국어" in str(system)
