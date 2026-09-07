"""streaming_03_tool: 도구 호출 턴을 SSE 로 돌렸을 때의 이벤트 순서.

앞쪽 테스트는 streaming_01_sse 와 같은 텍스트 턴이고, tool_then_chunks
부터가 이 단계에서 더한 도구 턴이다.
"""

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_study.testing import FakeStreamLlm, call_reply
from agents.streaming_03_tool.agent import root_agent
from agents.streaming_03_tool.main import APP_NAME, USER_ID, describe, run


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
    """도구 호출 응답 뒤에 조각으로 된 최종 답이 온다.

    첫 원소는 Content 라 FakeStreamLlm 이 조각 없이 non-partial 로
    내고, 둘째 원소는 조각 목록이라 partial 로 흘려 보낸다. LiteLlm 이
    도구 호출을 모아서 내고 텍스트만 조각으로 내는 순서를 흉내 낸다.
    """
    return FakeStreamLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            ["5글", "자예", "요"],
        ]
    )


async def test_tool_call_is_never_partial():
    """function_call 과 function_response 는 조각 없이 먼저 오고,
    도구 결과를 본 두 번째 모델 호출의 답만 조각으로 온다."""
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
    """Runner 는 partial 이 아닌 이벤트만 세션에 넣으므로 non-partial
    이벤트 수가 곧 이 턴에서 세션에 저장되는 이벤트 수다."""
    root_agent.model = tool_then_chunks()

    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert sum(1 for e in events if not e.partial) == 3


async def test_session_keeps_user_call_response_and_final():
    """세션을 직접 열어 도구 턴 뒤에 남는 이벤트 넷을 확인한다.

    run 은 세션 서비스를 안에서 만들어 돌려주지 않으므로 여기서는
    InMemoryRunner 를 직접 써서 같은 SSE 턴을 돌린다.
    """
    root_agent.model = tool_then_chunks()
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="글자 수 세 줘")]
    )
    async for _ in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=message,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        pass

    stored = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    assert stored is not None
    assert [describe(e) for e in stored.events] == [
        "[user] text 글자 수 세 줘",
        "[stream_with_tool] function_call count_chars {'text': '안녕 하세요'}",
        "[stream_with_tool] function_response {'result': 5}",
        "[stream_with_tool] text 5글자예요",
    ]


async def test_describe_marks_partial_events():
    """같은 텍스트 이벤트라도 partial 여부에 따라 표시가 갈린다."""
    root_agent.model = tool_then_chunks()
    events = await run(root_agent, "글자 수 세 줘", streaming=True)

    assert describe(events[2]) == "[stream_with_tool] partial 5글"
    assert describe(events[-1]) == "[stream_with_tool] text 5글자예요"
