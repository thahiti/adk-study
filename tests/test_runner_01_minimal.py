"""runner_01_minimal: 도구 호출이 만드는 이벤트 셋.

FakeLlm 에 응답을 두 개 넣는 이유는 도구 턴에서 모델이 두 번
불리기 때문이다. 첫 응답은 도구 호출 요청, 둘째 응답은 도구 결과를
본 뒤의 최종 답이다.
"""

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.runner_01_minimal.agent import count_chars, root_agent


def test_count_chars_counts_without_spaces():
    assert count_chars("안녕 하세요") == 5


async def test_tool_turn_yields_three_events_in_order():
    root_agent.model = FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "안녕 하세요"}),
            text_reply("5글자예요"),
        ]
    )

    events = await run_turn(root_agent, "글자 수 세 줘")

    # 사용자 메시지는 세션에만 쌓이고 run_async 가 내보내지 않는다.
    assert len(events) == 3
    call, response, final = events
    assert call.get_function_calls()[0].name == "count_chars"
    # int 반환값은 ADK 가 {"result": 값} 으로 감싼다.
    assert response.get_function_responses()[0].response == {"result": 5}
    assert final.content.parts[0].text == "5글자예요"


async def test_only_last_event_is_final():
    root_agent.model = FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "abc"}),
            text_reply("3글자예요"),
        ]
    )

    events = await run_turn(root_agent, "세 줘")

    # LlmFlow 는 is_final_response() 가 True 인 이벤트가 나올 때까지
    # 모델 호출을 반복한다. 앞 두 이벤트가 False 라서 턴이 이어진다.
    assert [e.is_final_response() for e in events] == [False, False, True]


async def test_all_events_share_invocation_and_author():
    root_agent.model = FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "abc"}),
            text_reply("3글자예요"),
        ]
    )

    events = await run_turn(root_agent, "세 줘")

    assert len({e.invocation_id for e in events}) == 1
    # 도구를 실행한 주체는 ADK 지만 author 는 에이전트 name 이다.
    assert {e.author for e in events} == {"runner_tool"}
    # role 은 user 와 model 둘뿐이라 도구 결과는 user 가 된다.
    assert [e.content.role for e in events] == ["model", "user", "model"]


async def test_tool_result_goes_back_to_model_as_user_content():
    root_agent.model = FakeLlm(
        replies=[
            call_reply("count_chars", {"text": "abc"}),
            text_reply("3글자예요"),
        ]
    )

    events = await run_turn(root_agent, "세 줘")

    call, response, _ = events
    # 응답의 id 가 호출의 id 와 같아서 어느 호출의 결과인지 이어진다.
    assert response.get_function_responses()[0].id == (
        call.get_function_calls()[0].id
    )
    # 두 번째 모델 호출의 대화 기록 마지막이 role user 인 도구 결과다.
    requests = root_agent.model.requests
    assert len(requests) == 2
    last = requests[1].contents[-1]
    assert last.role == "user"
    assert last.parts[0].function_response.name == "count_chars"
