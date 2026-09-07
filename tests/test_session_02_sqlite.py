"""session_02_sqlite: SQLite 세션 서비스로 이력을 남긴다."""

from pathlib import Path

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

    reopened = SqliteSessionService(db)
    runner_again = Runner(
        app_name="test", agent=root_agent, session_service=reopened
    )
    root_agent.model = describe_then_answer()
    events = await run_in_session(runner_again, session, "다시")

    seen = events[1].get_function_responses()[0].response
    assert seen["events"] == 6


async def test_session_list_is_read_from_the_file(tmp_path: Path):
    db = f"sqlite:///{tmp_path / 'sessions.db'}"
    service = SqliteSessionService(db)
    session = await service.create_session(app_name="test", user_id="user")

    listed = await SqliteSessionService(db).list_sessions(
        app_name="test", user_id="user"
    )

    assert [s.id for s in listed.sessions] == [session.id]
