"""loop_01_pause_resume: yield 가 러너로 제어를 넘기고 다시 받는 지점."""

from agents.loop_01_pause_resume.agent import root_agent
from agents.loop_01_pause_resume.main import run


async def test_agent_and_runner_lines_interleave(capsys):
    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [
        "agent: before yield 1",
        "runner: got 첫 번째 알림",
        "agent: after yield 1",
        "agent: before yield 2",
        "runner: got 두 번째 알림",
        "agent: after yield 2",
    ]


async def test_run_collects_both_events():
    events = await run(root_agent, "시작")

    assert [e.content.parts[0].text for e in events] == [
        "첫 번째 알림",
        "두 번째 알림",
    ]
    assert events[1].actions.state_delta == {"announced": 2}
