"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.loop_04_transfer_next_turn.agent import child, root_agent
from agents.loop_04_transfer_next_turn.main import run_turns


def arrange() -> tuple[FakeLlm, FakeLlm]:
    """부모는 한 번 넘기고 자식은 두 턴을 답하도록 세운다.

    FakeLlm 은 replies 를 앞에서부터 꺼내 쓰므로, 넣은 개수가 곧
    그 에이전트가 불릴 것으로 기대하는 횟수다.
    """
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

    # 첫 턴은 도구 호출, 도구 응답, 자식의 답 세 이벤트다.
    assert [e.author for e in turns[0]] == [
        "loop_router",
        "loop_router",
        "loop_specialist",
    ]
    assert [e.author for e in turns[1]] == ["loop_specialist"]


async def test_parent_model_is_not_called_in_second_turn():
    parent_model, child_model = arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    # author 만 보면 부모가 조용히 돌았을 가능성이 남는다. 요청 수를
    # 세야 부모 모델이 둘째 턴에 아예 안 불린 것이 드러난다.
    assert len(parent_model.requests) == 1
    assert len(child_model.requests) == 2


async def test_child_can_transfer_back_to_parent():
    """자식에게도 부모로 돌아가는 전환 도구가 붙어 있다."""
    parent_model, child_model = arrange()
    parent_model.replies.append(text_reply("부모가 다시 답함"))
    child_model.replies[1] = call_reply(
        "transfer_to_agent", {"agent_name": "loop_router"}
    )

    turns = await run_turns(root_agent, ["넘겨 줘", "다시 부모로"])

    assert [e.author for e in turns[1]] == [
        "loop_specialist",
        "loop_specialist",
        "loop_router",
    ]


async def test_disallow_transfer_to_parent_sends_next_turn_to_root():
    """전환을 막으면 러너가 자식을 다음 턴 주인으로 인정하지 않는다.

    자식이 root 까지 부모로 되돌아갈 수 없으면 러너는 그 자식을
    건너뛰고 더 앞의 이벤트를 보다가 root_agent 를 고른다.
    """
    parent_model, _ = arrange()
    parent_model.replies.append(text_reply("부모가 둘째 턴을 맡음"))
    child.disallow_transfer_to_parent = True
    try:
        turns = await run_turns(root_agent, ["넘겨 줘", "하나 더"])
    finally:
        # 모듈 수준 에이전트라 다른 테스트에 새지 않도록 되돌린다.
        child.disallow_transfer_to_parent = False

    assert [e.author for e in turns[1]] == ["loop_router"]


async def test_turn_lines_show_authors(capsys):
    arrange()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[-1] == "turn 2: loop_specialist"
