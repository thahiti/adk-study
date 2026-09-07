"""runner_03_run_config: RunConfig 와 state_delta 로 한 턴을 조정한다."""

from pathlib import Path

from google.adk.sessions.sqlite_session_service import SqliteSessionService

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
