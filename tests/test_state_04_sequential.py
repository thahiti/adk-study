"""state_04_sequential: 앞 에이전트의 output_key 를 뒤 에이전트가 읽는다.

SequentialAgent 가 자식을 순서대로 한 턴 안에 돌리는 것, 앞 에이전트의
output_key 가 뒤 에이전트의 instruction 에 들어가는 것, 앞 에이전트의
응답이 대화 이력으로도 전달되는 것을 검사한다.
"""

from adk_study.testing import FakeLlm, run_turn, text_reply
from agents.state_04_sequential.agent import counter, lister, root_agent


def arrange() -> tuple[FakeLlm, FakeLlm]:
    """두 LlmAgent 에 각각 FakeLlm 을 끼운다.

    SequentialAgent 는 model 이 없으므로 자식마다 따로 끼운다.
    FakeLlm 은 replies 를 소비하며 requests 를 쌓으므로 테스트마다
    새로 만든다.
    """
    lister.model = FakeLlm(replies=[text_reply("사과, 바나나")])
    counter.model = FakeLlm(replies=[text_reply("2개")])
    return lister.model, counter.model


async def test_sub_agents_run_in_order_in_one_invocation():
    """이벤트는 sub_agents 순서대로 나오고 모두 같은 턴에 속한다.

    author 목록에 state_pipeline 이 없다. SequentialAgent 는 자기
    이벤트를 만들지 않고 자식 이벤트만 올려 보낸다.
    invocation_id 가 하나인 것은 자식이 부모의 InvocationContext 를
    복사해 쓰기 때문이다.
    """
    arrange()

    events = await run_turn(root_agent, "과일 알려 줘")

    assert [e.author for e in events] == [
        "state_lister",
        "state_fruit_counter",
    ]
    assert len({e.invocation_id for e in events}) == 1


async def test_first_agent_saves_fruits_to_state():
    """lister 의 응답 이벤트가 fruits 를 delta 에 싣는다.

    state_01 과 같은 동작이다. 달라진 것은 이 delta 를 읽는 쪽이다.
    """
    arrange()

    events = await run_turn(root_agent, "과일 알려 줘")

    assert events[0].actions.state_delta == {"fruits": "사과, 바나나"}


async def test_second_agent_reads_fruits_from_state():
    """counter 의 system_instruction 에 lister 의 답이 들어 있다.

    Runner 가 lister 의 이벤트를 세션에 저장한 뒤에 counter 가
    요청을 만들므로, 같은 턴 안인데도 {fruits} 가 치환된다.
    """
    _, counter_model = arrange()

    await run_turn(root_agent, "과일 알려 줘")

    system = str(counter_model.requests[0].config.system_instruction)
    assert "사과, 바나나" in system


async def test_second_agent_also_sees_first_reply_in_contents():
    """counter 는 lister 의 답을 대화 이력(contents)으로도 받는다.

    같은 세션의 이벤트라서 include_contents 기본값이면 앞 에이전트의
    응답도 요청에 들어간다. 다른 에이전트가 말한 것이라 model 역할이
    아니라 "For context:" 로 시작하는 user 역할 메시지로 바뀐다.
    """
    _, counter_model = arrange()

    await run_turn(root_agent, "과일 알려 줘")

    contents = counter_model.requests[0].contents
    texts = [p.text for c in contents for p in c.parts or []]
    assert contents[-1].role == "user"
    assert "For context:" in texts
    assert "[state_lister] said: 사과, 바나나" in texts
