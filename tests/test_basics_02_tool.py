"""basics_02_tool: 도구 하나를 가진 에이전트."""

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.basics_02_tool.agent import roll_die, root_agent


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


def test_roll_die_stays_in_range():
    for _ in range(50):
        assert 1 <= roll_die(6) <= 6


async def test_tool_call_produces_call_and_response_events():
    fake = FakeLlm(
        replies=[call_reply("roll_die", {"sides": 6}), text_reply("굴렸어요")]
    )
    root_agent.model = fake

    events = await run_turn(root_agent, "주사위 굴려")

    assert events[0].get_function_calls()[0].name == "roll_die"
    result = events[1].get_function_responses()[0].response["result"]
    assert 1 <= result <= 6
    assert events[2].is_final_response()


async def test_tool_schema_is_sent_to_model():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    assert "roll_die" in fake.requests[0].tools_dict
