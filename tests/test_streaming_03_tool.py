"""streaming_03_tool: SSE 모드에서 partial 이벤트를 조각으로 받는다."""

from adk_study.testing import FakeStreamLlm
from agents.streaming_03_tool.agent import root_agent
from agents.streaming_03_tool.main import APP_NAME, run


def chunked_answer() -> FakeStreamLlm:
    return FakeStreamLlm(replies=[["안녕", "하세", "요"]])


async def test_sse_yields_partials_then_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕", True),
        ("하세", True),
        ("요", True),
        ("안녕하세요", False),
    ]
    assert [e.is_final_response() for e in events] == [
        False,
        False,
        False,
        True,
    ]


async def test_none_mode_yields_only_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=False)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕하세요", False),
    ]


async def test_partials_are_printed_inline_then_final_line(capsys):
    root_agent.model = chunked_answer()

    await run(root_agent, "인사해 줘", streaming=True)

    out = capsys.readouterr().out
    assert out.startswith("안녕하세요\n")
    assert "[stream_with_tool] text 안녕하세요" in out


async def test_all_events_share_one_invocation():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert len({e.invocation_id for e in events}) == 1


def test_app_name_matches_folder():
    assert APP_NAME == "streaming_03_tool"
