"""event_03_transfer: 에이전트 전환이 담기는 이벤트."""

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.event_03_transfer.agent import counter, root_agent


def transfer_to_counter() -> None:
    """부모는 전환을 요청하고 자식은 도구 없이 바로 답하도록 모델을 꾸민다."""
    root_agent.model = FakeLlm(
        replies=[
            call_reply("transfer_to_agent", {"agent_name": "event_counter"})
        ]
    )
    counter.model = FakeLlm(replies=[text_reply("제가 셀게요")])


async def test_parent_gets_transfer_tool_automatically():
    transfer_to_counter()

    await run_turn(root_agent, "글자 수 세 줘")

    parent_request = root_agent.model.requests[0]
    assert "transfer_to_agent" in parent_request.tools_dict


async def test_transfer_event_carries_target_in_actions():
    transfer_to_counter()

    events = await run_turn(root_agent, "글자 수 세 줘")

    call, response = events[0], events[1]
    assert call.get_function_calls()[0].name == "transfer_to_agent"
    assert response.actions.transfer_to_agent == "event_counter"
    assert response.author == "event_parent"


async def test_child_answers_in_same_invocation():
    transfer_to_counter()

    events = await run_turn(root_agent, "글자 수 세 줘")

    final = events[-1]
    assert final.author == "event_counter"
    assert final.is_final_response()
    assert final.invocation_id == events[0].invocation_id
