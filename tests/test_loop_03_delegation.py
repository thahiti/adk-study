"""loop_03_delegation: yield 뒤에 state_delta 가 세션에 반영되어 있다."""

from agents.loop_03_delegation.agent import root_agent
from agents.loop_03_delegation.main import run


async def test_state_is_visible_only_after_yield(capsys):
    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    before = lines.index("agent: announced before yield = None")
    got = lines.index("runner: got 두 번째 알림")
    after = lines.index("agent: announced after yield = 2")
    assert before < got < after


async def test_third_event_reports_committed_value():
    events = await run(root_agent, "시작")

    assert events[-1].content.parts[0].text == "state 반영 확인: 2"
    assert events[-1].actions.state_delta == {}
