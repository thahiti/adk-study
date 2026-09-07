"""runner_03_run_config: RunConfig 와 state_delta 로 한 턴을 조정한다."""

import asyncio
from pathlib import Path

import pytest
from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.runner_03_run_config.agent import root_agent
from agents.runner_03_run_config.main import APP_NAME, describe, run


def count_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            text_reply("5글자예요"),
        ]
    )


async def test_run_returns_every_event_the_runner_yields(tmp_path: Path):
    root_agent.model = count_then_answer()

    events = await run(
        root_agent, "안녕 하세요 글자 수 세 줘", db_path=str(tmp_path / "s.db")
    )

    assert [e.author for e in events] == ["runner_config"] * 3
    assert events[-1].content.parts[0].text == "5글자예요"


async def test_run_prints_one_line_per_event_in_order(tmp_path: Path, capsys):
    root_agent.model = count_then_answer()

    await run(
        root_agent, "안녕 하세요 글자 수 세 줘", db_path=str(tmp_path / "s.db")
    )

    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 3
    assert "function_call" in lines[0]
    assert "function_response" in lines[1]
    assert "5글자예요" in lines[2]


async def test_describe_shows_author_and_kind(tmp_path: Path):
    root_agent.model = count_then_answer()
    events = await run(
        root_agent, "안녕 하세요 글자 수 세 줘", db_path=str(tmp_path / "s.db")
    )

    assert describe(events[0]).startswith("[runner_config] function_call")
    assert describe(events[2]).startswith("[runner_config] text")


def test_app_name_matches_folder():
    assert APP_NAME == "runner_03_run_config"


async def test_same_session_id_continues_across_runs(tmp_path: Path):
    db_path = str(tmp_path / "s.db")
    root_agent.model = count_then_answer()
    await run(root_agent, "첫 번째", db_path=db_path, session_id="s1")
    root_agent.model = count_then_answer()

    await run(root_agent, "두 번째", db_path=db_path, session_id="s1")

    stored = await SqliteSessionService(f"sqlite:///{db_path}").get_session(
        app_name=APP_NAME, user_id="user", session_id="s1"
    )
    assert stored is not None
    assert len(stored.events) == 8


async def test_different_session_id_starts_fresh(tmp_path: Path):
    db_path = str(tmp_path / "s.db")
    root_agent.model = count_then_answer()
    await run(root_agent, "첫 번째", db_path=db_path, session_id="s1")
    root_agent.model = count_then_answer()

    await run(root_agent, "두 번째", db_path=db_path, session_id="s2")

    listed = await SqliteSessionService(f"sqlite:///{db_path}").list_sessions(
        app_name=APP_NAME, user_id="user"
    )
    assert {s.id for s in listed.sessions} == {"s1", "s2"}


async def test_max_llm_calls_stops_a_tool_loop(tmp_path: Path):
    """상한을 넘는 호출은 모델에 닿기 전에 예외로 끊긴다.

    가짜 모델은 도구 호출을 다섯 번 요청한 뒤에야 텍스트로 답한다.
    상한이 없으면 여섯 번째 호출까지 가서 끝나지만, 상한 3 에서는
    네 번째 호출 직전에 LlmCallsLimitExceededError 가 난다.
    """
    root_agent.model = FakeLlm(
        replies=[call_reply("count_chars", {"text": "a"})] * 5
        + [text_reply("끝")]
    )

    with pytest.raises(LlmCallsLimitExceededError):
        await run(
            root_agent,
            "세 줘",
            db_path=str(tmp_path / "s.db"),
            max_llm_calls=3,
        )

    # 카운터를 먼저 올리고 상한과 비교하므로 네 번째 요청은 모델에
    # 도착하지 않는다. 모델이 받은 요청은 정확히 상한만큼이다.
    assert len(root_agent.model.requests) == 3


async def test_limit_error_leaves_earlier_events_in_the_session(
    tmp_path: Path,
):
    """예외가 나도 그전까지의 이벤트는 세션에 남는다.

    이벤트는 나올 때마다 세션에 저장되므로 예외가 났다고 되돌아가지
    않는다. 사용자 메시지 하나와 도구 호출, 응답 쌍 셋이 남는다.
    """
    root_agent.model = FakeLlm(
        replies=[call_reply("count_chars", {"text": "a"})] * 5
    )
    db_path = str(tmp_path / "s.db")

    with pytest.raises(LlmCallsLimitExceededError):
        await run(root_agent, "세 줘", db_path=db_path, max_llm_calls=3)

    stored = await SqliteSessionService(f"sqlite:///{db_path}").get_session(
        app_name=APP_NAME, user_id="user", session_id="runner-demo"
    )
    assert stored is not None
    assert [e.author for e in stored.events] == ["user"] + [
        "runner_config"
    ] * 6


async def test_state_arg_is_visible_to_the_agent(tmp_path: Path):
    """state 인자는 첫 모델 요청부터 instruction 에 치환돼 들어간다.

    run 이 돌려주는 events 에는 에이전트 이벤트만 있고 사용자 메시지
    이벤트는 없다. Runner 가 사용자 메시지를 세션에 저장만 하고
    yield 하지 않기 때문이다. 그래서 state_delta 가 어디에 실렸는지는
    세션을 다시 읽어 첫 이벤트에서 확인한다.
    """
    fake = FakeLlm(replies=[text_reply("안녕 철수")])
    root_agent.model = fake

    events = await run(
        root_agent,
        "안녕",
        db_path=str(tmp_path / "s.db"),
        state={"user_name": "철수"},
    )

    assert "철수" in str(fake.requests[0].config.system_instruction)
    stored = await SqliteSessionService(
        f"sqlite:///{tmp_path / 's.db'}"
    ).get_session(app_name=APP_NAME, user_id="user", session_id="runner-demo")
    assert stored is not None
    assert stored.events[0].actions.state_delta == {"user_name": "철수"}
    # state 는 사용자 메시지 이벤트에만 실린다. 에이전트가 만든 이벤트는
    # 자기가 바꾼 state 가 없으므로 state_delta 가 비어 있다.
    assert events[-1].actions.state_delta == {}


def test_runner_run_is_a_sync_wrapper_over_run_async():
    """runner.run 은 이벤트 루프 없는 동기 코드에서 쓰는 래퍼다.

    별도 스레드에서 run_async 를 돌리고 이벤트를 큐로 넘겨 주므로
    보통의 for 문으로 이벤트를 받는다. run_async 와 달리 state_delta
    인자는 없고 run_config 만 받는다.
    """
    root_agent.model = FakeLlm(replies=[text_reply("동기")])
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    # 세션 만들기는 async 뿐이라 여기서만 asyncio.run 을 쓴다.
    session = asyncio.run(
        runner.session_service.create_session(
            app_name=APP_NAME, user_id="user"
        )
    )
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="안녕")]
    )

    events = list(
        runner.run(
            user_id="user",
            session_id=session.id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=1),
        )
    )

    assert [e.content.parts[0].text for e in events] == ["동기"]


async def test_run_debug_creates_the_session_itself():
    """run_debug 는 세션이 없으면 만들고 문자열을 바로 메시지로 보낸다.

    user_id 와 session_id 를 주지 않으면 debug_user_id 와
    debug_session_id 를 쓴다. quiet=True 는 콘솔 출력만 끈다.
    """
    root_agent.model = FakeLlm(replies=[text_reply("디버그")])
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)

    events = await runner.run_debug("안녕", quiet=True)

    assert events[-1].content.parts[0].text == "디버그"
    stored = await runner.session_service.get_session(
        app_name=APP_NAME,
        user_id="debug_user_id",
        session_id="debug_session_id",
    )
    assert stored is not None
