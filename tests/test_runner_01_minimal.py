"""runner_01_minimal: Runner 를 직접 만들어 for 루프에서 이벤트를 받는다."""

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.runner_01_minimal.agent import root_agent
from agents.runner_01_minimal.main import APP_NAME, describe, run


def count_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            text_reply("5글자예요"),
        ]
    )


async def test_run_returns_every_event_the_runner_yields():
    root_agent.model = count_then_answer()

    events = await run(root_agent, "안녕 하세요 글자 수 세 줘")

    assert [e.author for e in events] == ["runner_tool"] * 3
    assert events[-1].content.parts[0].text == "5글자예요"


async def test_run_prints_one_line_per_event_in_order(capsys):
    root_agent.model = count_then_answer()

    await run(root_agent, "안녕 하세요 글자 수 세 줘")

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 3
    assert "function_call" in lines[0]
    assert "function_response" in lines[1]
    assert "5글자예요" in lines[2]


async def test_describe_shows_author_and_kind():
    root_agent.model = count_then_answer()
    events = await run(root_agent, "안녕 하세요 글자 수 세 줘")

    assert describe(events[0]).startswith("[runner_tool] function_call")
    assert describe(events[2]).startswith("[runner_tool] text")


def test_app_name_matches_folder():
    assert APP_NAME == "runner_01_minimal"
