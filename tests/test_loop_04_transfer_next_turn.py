"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from adk_study.testing import FakeLlm, text_reply
from agents.loop_04_transfer_next_turn.agent import child, root_agent
from agents.loop_04_transfer_next_turn.main import run


async def test_child_events_are_reyielded_between_parent_events():
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert [(e.author, e.content.parts[0].text) for e in events] == [
        ("loop_orchestrator", "시작"),
        ("loop_child", "자식이 답함"),
        ("loop_orchestrator", "끝"),
    ]


async def test_child_shares_invocation_and_knows_parent():
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert len({e.invocation_id for e in events}) == 1
    assert child.parent_agent is root_agent


async def test_runner_line_appears_between_child_and_end(capsys):
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines.index("runner: got 자식이 답함") < lines.index(
        "agent: after child"
    )
