"""streaming_01_sse: Runner 를 직접 만들어 for 루프에서 이벤트를 받는다.

이전 단계는 도우미 run_turn 으로 돌렸지만 여기서는 main.py 의 run 을
그대로 부른다. Runner 를 만들고 세션을 여는 코드가 이 단계의 학습
대상이므로 그 코드 자체를 검증한다.
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.streaming_01_sse.agent import root_agent
from agents.streaming_01_sse.main import APP_NAME, USER_ID, describe, run


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

    # 사용자 메시지는 루프에 나오지 않으므로 에이전트 이벤트 셋뿐이다.
    assert [e.author for e in events] == ["stream_tool"] * 3
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

    assert describe(events[0]).startswith("[stream_tool] function_call")
    assert describe(events[2]).startswith("[stream_tool] text")


async def test_loop_advances_agent_one_yield_at_a_time():
    # run 은 루프를 끝까지 돌리므로 여기서만 Runner 를 직접 만들어
    # 이벤트 하나를 받은 시점의 상태를 본다.
    model = count_then_answer()
    root_agent.model = model
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=APP_NAME, agent=root_agent, session_service=session_service
    )
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="세 줘")]
    )
    events = runner.run_async(
        user_id=USER_ID, session_id=session.id, new_message=message
    )

    first = await anext(events)

    # function_call 을 받은 시점에는 두 번째 모델 호출이 아직 없다.
    assert first.get_function_calls()
    assert len(model.requests) == 1
    # 이벤트는 루프에 나오기 전에 세션에 저장된다.
    # 사용자 메시지는 세션에는 있지만 루프에는 나오지 않는다.
    saved = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    assert saved is not None
    assert [e.author for e in saved.events] == ["user", "stream_tool"]

    await events.aclose()


def test_app_name_matches_folder():
    # Runner 는 에이전트가 있는 폴더 이름을 app_name 으로 기대한다.
    assert APP_NAME == "streaming_01_sse"
