"""basics_02_tool: 도구 하나를 가진 에이전트.

FakeLlm 은 모델 대신 미리 정한 응답을 순서대로 돌려준다.
call_reply 로 모델이 도구 호출을 요청한 것처럼 꾸미면 실제 모델
없이도 ADK 가 도구를 실행하고 이벤트를 만드는 과정을 볼 수 있다.
"""

from google.genai import types

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.basics_02_tool.agent import roll_die, root_agent


async def test_hello_returns_model_text_as_final_event():
    """도구를 부르지 않은 턴은 이전 단계와 똑같이 이벤트가 하나다."""
    fake = FakeLlm(replies=[text_reply("안녕하세요, 반가워요")])
    root_agent.model = fake

    events = await run_turn(root_agent, "안녕")

    assert events[-1].author == "dice"
    assert events[-1].is_final_response()
    assert events[-1].content.parts[0].text == "안녕하세요, 반가워요"


async def test_instruction_is_sent_as_system_instruction():
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    system = fake.requests[0].config.system_instruction
    assert "한국어" in str(system)


def test_roll_die_stays_in_range():
    """도구 함수는 ADK 없이 그냥 파이썬 함수로도 부를 수 있다."""
    for _ in range(50):
        assert 1 <= roll_die(6) <= 6


async def test_tool_call_produces_call_and_response_events():
    """도구 호출 한 번이 이벤트 셋과 모델 호출 둘로 이어진다.

    첫 응답은 도구 호출 요청, 둘째 응답은 도구 결과를 받은 뒤의
    최종 텍스트다. 모델이 두 번 불리므로 응답도 두 개 준다.
    """
    fake = FakeLlm(
        replies=[call_reply("roll_die", {"sides": 6}), text_reply("굴렸어요")]
    )
    root_agent.model = fake

    events = await run_turn(root_agent, "주사위 굴려")

    # 첫 이벤트는 모델이 요청한 function_call 그대로다.
    assert events[0].get_function_calls()[0].name == "roll_die"
    # 둘째 이벤트는 ADK 가 roll_die 를 실행한 결과다. 반환값이 int 라
    # ADK 가 {"result": 값} 으로 감싼다.
    result = events[1].get_function_responses()[0].response["result"]
    assert 1 <= result <= 6
    # 앞의 두 이벤트는 최종 응답이 아니다. 셋째만 True 다.
    assert events[2].is_final_response()


async def test_tool_schema_is_sent_to_model():
    """tools_dict 는 ADK 가 요청에 실은 도구를 이름으로 찾는 dict 다.

    모델이 function_call 을 보내면 ADK 는 이 dict 에서 이름으로
    도구를 찾아 실행한다.
    """
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    assert "roll_die" in fake.requests[0].tools_dict


async def test_docstring_and_type_hint_become_tool_schema():
    """모델이 받는 도구 선언은 독스트링과 타입 힌트로만 만들어진다.

    독스트링은 Args: 절까지 통째로 description 이 된다. 매개변수에는
    타입 힌트에서 얻은 타입만 들어가고 설명은 비어 있다.
    """
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    declaration = fake.requests[0].config.tools[0].function_declarations[0]
    assert declaration.name == "roll_die"
    assert declaration.description == roll_die.__doc__
    assert "Args:" in declaration.description
    sides = declaration.parameters.properties["sides"]
    assert sides.type == types.Type.INTEGER
    assert sides.description is None
    assert declaration.parameters.required == ["sides"]
