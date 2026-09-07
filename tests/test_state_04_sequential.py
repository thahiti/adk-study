"""state_04_sequential: 앞 에이전트의 output_key 를 뒤 에이전트가 읽는다."""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.state_04_sequential.agent import counter, lister, root_agent


def arrange() -> tuple[FakeLlm, FakeLlm]:
    lister.model = FakeLlm(replies=[text_reply("사과, 바나나")])
    counter.model = FakeLlm(replies=[text_reply("2개")])
    return lister.model, counter.model


async def test_sub_agents_run_in_order_in_one_invocation():
    arrange()

    events = await run_turn(root_agent, "과일 알려 줘")

    assert [e.author for e in events] == [
        "state_lister",
        "state_fruit_counter",
    ]
    assert len({e.invocation_id for e in events}) == 1


async def test_first_agent_saves_fruits_to_state():
    arrange()

    events = await run_turn(root_agent, "과일 알려 줘")

    assert events[0].actions.state_delta == {"fruits": "사과, 바나나"}


async def test_second_agent_reads_fruits_from_state():
    _, counter_model = arrange()

    await run_turn(root_agent, "과일 알려 줘")

    system = str(counter_model.requests[0].config.system_instruction)
    assert "사과, 바나나" in system
