"""basics_01_hello: instruction 만 있는 최소 에이전트.

실제 모델을 부르지 않는다. FakeLlm 은 BaseLlm 을 상속한 가짜
모델로, 미리 넣어 둔 응답을 순서대로 돌려주고 자기가 받은
LlmRequest 를 requests 에 쌓는다. LlmAgent.model 은 문자열 대신
BaseLlm 객체도 받으므로 root_agent.model 에 대입하면 에이전트
코드는 그대로 둔 채 모델만 바꿔 끼울 수 있다.
"""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, run_turn, text_reply
from agents.basics_01_hello.agent import root_agent


async def test_hello_returns_model_text_as_final_event():
    """모델이 텍스트로 답하면 그 텍스트가 에이전트의 최종 이벤트다.

    run_turn 은 runner.run_async 가 내놓는 이벤트만 모은다.
    도구 호출이 없는 이 단계에서는 모델 응답 이벤트 하나뿐이다.
    """
    fake = FakeLlm(replies=[text_reply("안녕하세요, 반가워요")])
    root_agent.model = fake

    events = await run_turn(root_agent, "안녕")

    # author 는 LlmAgent 의 name 이다.
    assert events[-1].author == "hello"
    # 함수 호출도, 스트리밍 조각(partial)도 아니면 최종 응답이다.
    assert events[-1].is_final_response()
    assert events[-1].content.parts[0].text == "안녕하세요, 반가워요"


async def test_instruction_is_sent_as_system_instruction():
    """instruction 은 대화 내용이 아니라 system_instruction 으로 간다.

    ADK 는 instruction 뒤에 name 과 description 으로 만든 정체성
    문장을 덧붙이므로, 같음이 아니라 포함 여부를 확인한다.
    """
    fake = FakeLlm(replies=[text_reply("네")])
    root_agent.model = fake

    await run_turn(root_agent, "안녕")

    system = fake.requests[0].config.system_instruction
    assert "한국어" in str(system)


async def test_session_keeps_user_and_agent_events():
    """세션에는 사용자 메시지와 모델 응답이 이벤트로 하나씩 남는다.

    Runner 는 사용자 메시지를 author 가 user 인 이벤트로 세션에
    먼저 저장하지만 run_async 로 내놓지는 않는다. adk web 의
    Events 탭은 이 세션 이벤트를 보여주므로 둘 다 나타난다.
    """
    fake = FakeLlm(replies=[text_reply("안녕하세요")])
    root_agent.model = fake
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    yielded = await run_in_session(runner, session, "안녕")

    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    # get_session 은 없는 세션이면 None 을 돌려준다.
    assert stored is not None
    assert [e.author for e in yielded] == ["hello"]
    assert [e.author for e in stored.events] == ["user", "hello"]
