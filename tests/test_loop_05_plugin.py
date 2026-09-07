"""loop_05_plugin: 플러그인 콜백이 러너 루프의 단계를 드러낸다."""

from adk_study.testing import FakeLlm, call_reply, text_reply
from agents.loop_05_plugin.agent import app, child, root_agent
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


async def test_plugin_sees_run_agent_and_event_hooks_in_order():
    arrange()
    # 플러그인은 agent.py 의 App 에 붙은 모듈 전역 인스턴스 하나뿐이라
    # log 가 테스트 사이에 남는다. 그래서 매번 비우고 시작한다.
    tracer = app.plugins[0]
    tracer.log.clear()

    await run_turns(root_agent, ["넘겨 줘"])

    names = [name for name, _ in tracer.log]
    assert names[0] == "before_run"
    assert names[-1] == "after_run"
    # 전환 호출, 도구 응답, 자식의 답까지 이벤트 세 개가 지나간다.
    assert names.count("on_event") == 3
    assert names.index("before_agent") < names.index("on_event")


async def test_plugin_sees_child_agent_too():
    arrange()
    tracer = app.plugins[0]
    tracer.log.clear()

    await run_turns(root_agent, ["넘겨 줘"])

    agents_seen = [v for n, v in tracer.log if n == "before_agent"]
    assert agents_seen == ["loop_router", "loop_specialist"]


async def test_second_turn_plugin_log_shows_child_only():
    arrange()
    tracer = app.plugins[0]
    tracer.log.clear()

    await run_turns(root_agent, ["넘겨 줘", "하나 더"])

    # 턴 하나가 before_run 으로 시작하므로 두 번째 before_run 부터가
    # 둘째 턴의 로그다. 부모는 아예 실행되지 않는다.
    starts = [i for i, (n, _) in enumerate(tracer.log) if n == "before_run"]
    second_turn = tracer.log[starts[1] :]
    agents_seen = [v for n, v in second_turn if n == "before_agent"]
    assert agents_seen == ["loop_specialist"]
