"""streaming_01_sse: SSE 모드에서 partial 이벤트를 조각으로 받는다.

FakeStreamLlm 은 LlmFlow 가 넘기는 stream 인자를 그대로 따른다.
stream=True 면 조각마다 partial=True 응답을 내고 마지막에 합친
응답을 내며, stream=False 면 합친 응답만 낸다. 그래서 모델 호출
없이도 SSE 와 NONE 두 모드의 차이를 그대로 볼 수 있다.
"""

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from adk_study.testing import FakeStreamLlm
from agents.streaming_01_sse.agent import root_agent
from agents.streaming_01_sse.main import APP_NAME, USER_ID, run


def chunked_answer() -> FakeStreamLlm:
    # 조각 세 개가 "안녕하세요" 한 문장으로 합쳐지는지 보려고 어절
    # 경계와 다르게 자른다.
    return FakeStreamLlm(replies=[["안녕", "하세", "요"]])


async def test_sse_yields_partials_then_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    # 조각 셋 뒤에 합친 텍스트가 온다. 최종 이벤트는 조각을 이어 붙인
    # 결과가 아니라 모델이 따로 낸 응답이다.
    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕", True),
        ("하세", True),
        ("요", True),
        ("안녕하세요", False),
    ]
    # partial 이면 is_final_response 가 False 라 마지막 것만 최종이다.
    assert [e.is_final_response() for e in events] == [
        False,
        False,
        False,
        True,
    ]


async def test_none_mode_yields_only_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=False)

    # 같은 모델이라도 stream=False 로 불리면 조각을 내지 않는다.
    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕하세요", False),
    ]


async def test_partials_are_printed_inline_then_final_line(capsys):
    root_agent.model = chunked_answer()

    await run(root_agent, "인사해 줘", streaming=True)

    # 조각은 개행 없이 이어져 한 줄이 되고 요약은 그 다음 줄에 온다.
    out = capsys.readouterr().out
    assert out.startswith("안녕하세요\n")
    assert "[stream_tool] text 안녕하세요" in out


async def test_all_events_share_one_invocation():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    # 조각이 여러 이벤트로 오더라도 run_async 호출 한 번의 산물이다.
    assert len({e.invocation_id for e in events}) == 1


async def test_session_keeps_only_final_event():
    # run 은 세션 서비스를 안에서 만들어 돌려주지 않으므로 여기서만
    # Runner 를 직접 만들어 세션에 무엇이 남는지 본다.
    root_agent.model = chunked_answer()
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=root_agent, session_service=session_service
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="인사해 줘")]
    )

    events = [
        event
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=message,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    ]

    # 루프에는 조각 셋과 최종 하나가 오지만 세션에는 사용자 메시지와
    # 최종 이벤트만 남는다. Runner 가 partial 이벤트는 저장하지 않는다.
    assert len(events) == 4
    saved = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    assert saved is not None
    assert [(e.author, e.partial) for e in saved.events] == [
        ("user", None),
        ("stream_tool", False),
    ]
    assert saved.events[-1].content.parts[0].text == "안녕하세요"


def test_app_name_matches_folder():
    assert APP_NAME == "streaming_01_sse"
