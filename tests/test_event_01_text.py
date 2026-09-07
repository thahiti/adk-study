"""event_01_text: 텍스트 응답 이벤트의 구조.

README 의 Event 필드 설명을 assert 로 하나씩 옮긴 테스트다.
FakeLlm 이 텍스트 하나를 돌려주므로 모델 호출 없이 검증한다.
"""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, run_turn, text_reply
from agents.event_01_text.agent import root_agent


async def test_text_reply_yields_exactly_one_event():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    events = await run_turn(root_agent, "날씨 어때")

    # 사용자 메시지도 Event 가 되지만 run_async 는 내보내지 않는다.
    # 밖으로 나오는 것은 모델 응답 이벤트 하나뿐이다.
    assert len(events) == 1


async def test_event_carries_identity_fields():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    event = (await run_turn(root_agent, "날씨 어때"))[0]

    # id 는 Event 를 만들 때 uuid 로 자동 채워진다
    assert event.id
    # invocation_id 는 Runner 가 턴마다 "e-" + uuid 로 만든다
    assert event.invocation_id.startswith("e-")
    # author 는 "model" 이 아니라 응답을 만든 에이전트의 name 이다
    assert event.author == "event_text"
    # timestamp 는 epoch 초
    assert event.timestamp > 0


async def test_event_content_and_actions_defaults():
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])

    event = (await run_turn(root_agent, "날씨 어때"))[0]

    # content.role 은 누가 말했는지, author 는 어느 에이전트인지다
    assert event.content.role == "model"
    assert event.content.parts[0].text == "오늘은 맑아요"
    # FakeLlm 은 partial 을 건드리지 않으므로 기본값 None 이 남는다.
    # 실제 LiteLlm 을 거치면 False 가 된다. ADK 는 둘 다 조각이
    # 아닌 것으로 본다.
    assert event.partial is None
    # 텍스트 응답만 있으면 상태 변경도 에이전트 전환도 없다
    assert event.actions.state_delta == {}
    assert event.actions.transfer_to_agent is None
    # 함수 호출도 함수 응답도 없고 partial 이 아니므로 최종 응답이다.
    # Runner 는 이 값이 True 인 이벤트에서 모델 호출 루프를 멈춘다.
    assert event.is_final_response()


async def test_session_keeps_user_and_model_events_in_one_turn():
    """adk web Events 탭에 보이는 두 이벤트를 세션에서 확인한다."""
    root_agent.model = FakeLlm(replies=[text_reply("오늘은 맑아요")])
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "날씨 어때")
    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )

    assert stored is not None
    # run_async 가 내보내지 않은 사용자 이벤트도 세션에는 남는다
    assert [e.author for e in stored.events] == ["user", "event_text"]
    assert stored.events[0].content.role == "user"
    # 한 턴의 이벤트는 invocation_id 를 공유한다
    assert stored.events[0].invocation_id == stored.events[1].invocation_id
