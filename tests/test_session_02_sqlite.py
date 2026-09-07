"""session_02_sqlite: SQLite 세션 서비스로 이력을 남긴다.

앞 단계까지는 InMemoryRunner 를 썼다.
InMemoryRunner 는 InMemorySessionService 를 대신 넣어 주는 축약이라
저장소를 바꾸려면 Runner 를 직접 만들고 session_service 를 넘겨야 한다.
Runner 생성자에서 session_service 는 기본값이 없는 필수 인자다.

프로세스 재시작은 테스트에서 재현하기 어려우므로
같은 파일을 가리키는 SqliteSessionService 를 하나 더 만들어 대신한다.
SqliteSessionService 는 경로 외에 아무것도 메모리에 들고 있지 않고
호출마다 새 연결을 열기 때문에 두 번째 인스턴스는 새 프로세스와 같다.
"""

from pathlib import Path

import pytest
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from adk_study.testing import FakeLlm, call_reply, run_in_session, text_reply
from agents.session_02_sqlite.agent import root_agent


def describe_then_answer() -> FakeLlm:
    return FakeLlm(
        replies=[
            call_reply("describe_session", {}),
            text_reply("알려 드렸어요"),
        ]
    )


async def test_history_survives_a_new_service_instance(tmp_path: Path):
    # tmp_path 가 / 로 시작하므로 sqlite:/// 뒤에 붙이면 슬래시가
    # 넷이 된다. sqlite:///a.db 는 상대경로, sqlite:////a.db 는
    # 절대경로라는 SQLAlchemy 규칙을 ADK 도 따른다.
    db = f"sqlite:///{tmp_path / 'sessions.db'}"
    first_service = SqliteSessionService(db)
    runner = Runner(
        app_name="test", agent=root_agent, session_service=first_service
    )
    session = await first_service.create_session(
        app_name="test", user_id="user"
    )
    root_agent.model = describe_then_answer()
    await run_in_session(runner, session, "세션 알려 줘")

    # 첫 서비스와 아무것도 공유하지 않는 인스턴스로 파일만 다시 읽는다.
    reopened = SqliteSessionService(db)
    stored = await reopened.get_session(
        app_name="test", user_id="user", session_id=session.id
    )

    assert stored is not None
    assert [e.author for e in stored.events] == ["user"] + [
        "session_persistent"
    ] * 3


async def test_tool_counts_events_from_previous_process(tmp_path: Path):
    db = f"sqlite:///{tmp_path / 'sessions.db'}"
    first_service = SqliteSessionService(db)
    runner = Runner(
        app_name="test", agent=root_agent, session_service=first_service
    )
    session = await first_service.create_session(
        app_name="test", user_id="user"
    )
    root_agent.model = describe_then_answer()
    await run_in_session(runner, session, "세션 알려 줘")

    # 두 번째 Runner 는 첫 Runner 의 session 객체를 받지 않는다.
    # run_in_session 은 user_id 와 id 만 넘기고 Runner 가 그 id 로
    # 자기 session_service 에서 세션을 다시 읽는다.
    reopened = SqliteSessionService(db)
    runner_again = Runner(
        app_name="test", agent=root_agent, session_service=reopened
    )
    root_agent.model = describe_then_answer()
    events = await run_in_session(runner_again, session, "다시")

    # 파일에서 읽은 앞 턴의 넷에 이번 턴의 둘을 더한 수다.
    seen = events[1].get_function_responses()[0].response
    assert seen["events"] == 6


async def test_session_list_is_read_from_the_file(tmp_path: Path):
    db = f"sqlite:///{tmp_path / 'sessions.db'}"
    service = SqliteSessionService(db)
    session = await service.create_session(app_name="test", user_id="user")

    # adk web 을 다시 켰을 때 왼쪽 목록이 채워지는 것과 같은 경로다.
    listed = await SqliteSessionService(db).list_sessions(
        app_name="test", user_id="user"
    )

    assert [s.id for s in listed.sessions] == [session.id]


async def test_relative_url_resolves_from_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # README 의 sqlite:///sessions.db 가 어디에 파일을 만드는지 확인한다.
    # 슬래시 셋은 adk web 을 실행한 디렉터리 기준 상대경로다.
    monkeypatch.chdir(tmp_path)
    service = SqliteSessionService("sqlite:///sessions.db")

    # 파일은 첫 쿼리 때 만들어지므로 세션을 하나 만들어 본다.
    await service.create_session(app_name="test", user_id="user")

    assert (tmp_path / "sessions.db").exists()
