"""loop_05_plugin: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.loop_05_plugin.agent import child, root_agent
from agents.loop_05_plugin.main import run_turns


def arrange() -> tuple[FakeLlm, FakeLlm]:
    root_agent.model = FakeLlm(
        replies=[
            call_reply("transfer_to_agent", {"agent_name": "loop_specialist"})
        ]
    )
    child.model = FakeLlm(replies=[text_reply("첫 답"), text_reply("둘째 답")])
    return root_agent.model, child.model


async def test_second_turn_goes_straight_to_child():
    arrange()

    turns = await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    assert [e.author for e in turns[0]] == [
        "loop_router",
        "loop_router",
        "loop_specialist",
    ]
    assert [e.author for e in turns[1]] == ["loop_specialist"]


async def test_parent_model_is_not_called_in_second_turn():
    parent_model, child_model = arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    assert len(parent_model.requests) == 1
    assert len(child_model.requests) == 2


async def test_turn_lines_show_authors(capsys):
    arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[-1] == "turn 2: loop_specialist"
