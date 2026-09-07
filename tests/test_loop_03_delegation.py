"""loop_03_delegation: 커스텀 에이전트가 자식을 돌리고 이벤트를 올린다."""

from adk_study.testing import FakeLlm, text_reply
from agents.loop_03_delegation.agent import child, root_agent
from agents.loop_03_delegation.main import run

# child 는 모듈 전역이라 테스트끼리 같은 객체를 공유한다. FakeLlm 은
# replies 를 pop 하며 소진하므로 테스트마다 새 FakeLlm 을 끼운다.


async def test_child_events_are_reyielded_between_parent_events():
    """자식 이벤트가 부모 이벤트 사이에 author 를 유지한 채 올라온다."""
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert [(e.author, e.content.parts[0].text) for e in events] == [
        ("loop_orchestrator", "시작"),
        ("loop_child", "자식이 답함"),
        ("loop_orchestrator", "끝"),
    ]


async def test_child_shares_invocation_and_knows_parent():
    """ctx 복사는 agent 만 바꾸고, parent_agent 는 생성 시점에 붙는다."""
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    # 자식이 부모 ctx 를 복사해 쓰므로 invocation_id 가 하나뿐이다.
    assert len({e.invocation_id for e in events}) == 1
    # sub_agents=[child] 로 Orchestrator 를 만들 때 설정된 값이다.
    assert child.parent_agent is root_agent


async def test_child_keeps_parent_branch():
    """부모가 ctx 를 그대로 넘기므로 branch 도 부모 것을 쓴다.

    ParallelAgent 는 여기서 갈린다. 자식마다 ctx 를 또 복사해
    branch 를 새로 붙이므로 자식 이벤트의 branch 가 서로 달라진다.
    """
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    events = await run(root_agent, "시작")

    assert [e.branch for e in events] == [None, None, None]


async def test_runner_line_appears_between_child_and_end(capsys):
    """자식 이벤트가 러너를 거친 뒤에야 부모의 다음 줄이 돈다."""
    child.model = FakeLlm(replies=[text_reply("자식이 답함")])

    await run(root_agent, "시작")

    lines = capsys.readouterr().out.strip().splitlines()
    assert lines.index("runner: got 자식이 답함") < lines.index(
        "agent: after child"
    )
