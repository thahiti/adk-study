"""basics_02_tool: 도구 하나를 가진 에이전트."""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.basics_02_tool.agent import root_agent


async def test_hello_returns_model_text_as_final_event():
    fake = FakeLlm(replies=[text_reply("안녕하세요, 반가워요")])
    root_agent.model = fake

    events = await run_turn(root_agent, "안녕")

    assert events[-1].author == "dice"
    assert events[-1].is_final_response()
    assert events[-1].content.parts[0].text == "안녕하세요, 반가워요"


async def test_instruction_is_sent_as_system_instruction():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    system = fake.requests[0].config.system_instruction
    assert "한국어" in str(system)
