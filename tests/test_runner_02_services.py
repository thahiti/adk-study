"""runner_02_services: 세션 서비스를 SQLite 로 바꾸고 다른 서비스도 넣는다.

FakeLlm 은 replies 를 pop 하며 소진하므로 run 을 부를 때마다
root_agent.model 에 새 FakeLlm 을 끼운다. 프로세스 재시작은
SqliteSessionService 를 새로 만드는 것으로 대신한다.
"""

from pathlib import Path

from google.adk.sessions.sqlite_session_service import SqliteSessionService

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.runner_02_services.agent import root_agent
from agents.runner_02_services.main import APP_NAME, describe, run


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

    assert [e.author for e in events] == ["runner_services"] * 3
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

    assert describe(events[0]).startswith("[runner_services] function_call")
    assert describe(events[2]).startswith("[runner_services] text")


def test_app_name_matches_folder():
    """adk web 은 폴더 이름을 app_name 으로 쓴다.

    스크립트와 adk web 이 같은 sessions.db 를 열었을 때 서로의
    세션을 보려면 두 app_name 이 같아야 한다.
    """
    assert APP_NAME == "runner_02_services"


async def test_same_session_id_continues_across_runs(tmp_path: Path):
    """같은 session_id 로 두 번 부르면 세션 하나에 이벤트가 쌓인다.

    run 은 부를 때마다 Runner 와 세션 서비스를 새로 만들지만
    SqliteSessionService 는 파일만 기억하므로 이전 실행이 남긴
    세션을 그대로 찾는다. 한 번 실행에 사용자 메시지 1 개와 for
    루프에 나온 이벤트 3 개가 저장되므로 두 번이면 8 개다.
    """
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


async def test_second_run_sends_previous_turn_to_model(tmp_path: Path):
    """두 번째 실행의 모델 요청에 첫 실행의 대화가 들어 있다.

    모델이 이전 대화를 "기억" 하는 이유는 세션에 쌓인 이벤트를
    Runner 가 매 요청에 통째로 실어 보내기 때문이다.
    """
    db_path = str(tmp_path / "s.db")
    root_agent.model = count_then_answer()
    await run(root_agent, "첫 번째", db_path=db_path, session_id="s1")
    second = count_then_answer()
    root_agent.model = second

    await run(root_agent, "두 번째", db_path=db_path, session_id="s1")

    texts = [
        part.text
        for content in second.requests[0].contents
        for part in content.parts
        if part.text
    ]
    assert texts == ["첫 번째", "5글자예요", "두 번째"]


async def test_different_session_id_starts_fresh(tmp_path: Path):
    """session_id 가 다르면 같은 파일 안에서도 세션이 따로 생긴다."""
    db_path = str(tmp_path / "s.db")
    root_agent.model = count_then_answer()
    await run(root_agent, "첫 번째", db_path=db_path, session_id="s1")
    root_agent.model = count_then_answer()

    await run(root_agent, "두 번째", db_path=db_path, session_id="s2")

    listed = await SqliteSessionService(f"sqlite:///{db_path}").list_sessions(
        app_name=APP_NAME, user_id="user"
    )
    assert {s.id for s in listed.sessions} == {"s1", "s2"}
