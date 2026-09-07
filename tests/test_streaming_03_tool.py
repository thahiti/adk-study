"""streaming_03_tool: SSE 모드에서 partial 이벤트를 조각으로 받는다."""

from adk_study.testing import FakeStreamLlm, call_reply
from agents.streaming_03_tool.agent import root_agent
from agents.streaming_03_tool.main import APP_NAME, describe, run


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


def tool_then_chunks() -> FakeStreamLlm:
    """도구 호출 응답 뒤에 조각으로 된 최종 답이 온다."""
    return FakeStreamLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            ["5글", "자예", "요"],
        ]
    )


async def test_tool_call_is_never_partial():
    root_agent.model = tool_then_chunks()

    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    kinds = [
        "call"
        if e.get_function_calls()
        else "response"
        if e.get_function_responses()
        else f"text:{e.partial}"
        for e in events
    ]
    assert kinds == [
        "call",
        "response",
        "text:True",
        "text:True",
        "text:True",
        "text:False",
    ]


async def test_only_non_partial_events_are_stored():
    root_agent.model = tool_then_chunks()

    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert sum(1 for e in events if not e.partial) == 3


async def test_describe_marks_partial_events():
    root_agent.model = tool_then_chunks()
    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert describe(events[2]) == "[stream_with_tool] partial 5글"
    assert describe(events[-1]) == "[stream_with_tool] text 5글자예요"
