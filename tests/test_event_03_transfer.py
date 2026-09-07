"""event_03_transfer: 에이전트 전환이 담기는 이벤트."""

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.event_03_transfer.agent import counter, root_agent


def transfer_to_counter() -> None:
    """부모는 전환을 요청하고 자식은 도구 없이 바로 답하도록 모델을 꾸민다.

    자식도 자기 모델을 따로 가진 LlmAgent 이므로 counter.model 까지
    바꿔야 실제 모델 호출이 없다.
    """
    root_agent.model = FakeLlm(
        replies=[
            call_reply("transfer_to_agent", {"agent_name": "event_counter"})
        ]
    )
    counter.model = FakeLlm(replies=[text_reply("제가 셀게요")])


async def test_parent_gets_transfer_tool_automatically():
    """tools 를 주지 않은 부모의 모델 요청에 transfer_to_agent 가 있다."""
    transfer_to_counter()

    await run_turn(root_agent, "글자 수 세 줘")

    parent_request = root_agent.model.requests[0]
    assert "transfer_to_agent" in parent_request.tools_dict


async def test_transfer_event_carries_target_in_actions():
    """전환 대상은 function_response 이벤트의 actions 에 담긴다.

    도구 함수 transfer_to_agent 는 값을 돌려주지 않고 actions 에만
    쓰기 때문에 content 가 아니라 actions 를 봐야 한다.
    """
    transfer_to_counter()

    events = await run_turn(root_agent, "글자 수 세 줘")

    call, response = events[0], events[1]
    assert call.get_function_calls()[0].name == "transfer_to_agent"
    assert response.actions.transfer_to_agent == "event_counter"
    assert response.author == "event_parent"


async def test_child_answers_in_same_invocation():
    """자식은 새 턴이 아니라 부모와 같은 invocation 안에서 답한다."""
    transfer_to_counter()

    events = await run_turn(root_agent, "글자 수 세 줘")

    final = events[-1]
    assert final.author == "event_counter"
    assert final.is_final_response()
    assert final.invocation_id == events[0].invocation_id


async def test_parent_model_is_not_called_after_transfer():
    """자식이 최종 응답을 내면 부모 모델은 다시 호출되지 않는다.

    부모의 LLM 루프는 마지막 이벤트가 최종 응답이면 멈춘다.
    자식의 텍스트 이벤트가 그 마지막 이벤트가 되므로 부모는 한 번만
    호출된다. FakeLlm 에 답을 하나만 준 이유도 여기에 있다.
    """
    transfer_to_counter()

    await run_turn(root_agent, "글자 수 세 줘")

    assert len(root_agent.model.requests) == 1
    assert len(counter.model.requests) == 1
