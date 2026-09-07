"""FakeLlm 과 run_turn 이 실제 Runner 흐름을 재현하는지 확인한다."""

from google.adk.agents import LlmAgent

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply


def echo(word: str) -> str:
    """받은 단어를 그대로 돌려준다."""
    return word


async def test_text_reply_becomes_final_event():
    fake = FakeLlm(replies=[text_reply("안녕하세요")])
    agent = LlmAgent(name="t", model=fake, instruction="인사")

    events = await run_turn(agent, "안녕")

    assert len(events) == 1
    assert events[0].is_final_response()
    assert events[0].content.parts[0].text == "안녕하세요"
    assert len(fake.requests) == 1


async def test_call_reply_runs_tool_then_final():
    fake = FakeLlm(
        replies=[call_reply("echo", {"word": "x"}), text_reply("끝")]
    )
    agent = LlmAgent(name="t", model=fake, instruction="", tools=[echo])

    events = await run_turn(agent, "x 라고 말해")

    assert events[0].get_function_calls()[0].name == "echo"
    assert events[1].get_function_responses()[0].response == {"result": "x"}
    assert events[2].is_final_response()
    assert len(fake.requests) == 2
