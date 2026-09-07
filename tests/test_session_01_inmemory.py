"""session_01_inmemory: Session 의 구조와 이벤트 누적.

README 의 Session 설명을 assert 로 옮긴 테스트다. FakeLlm 이 도구
호출 한 번과 텍스트 한 번을 순서대로 돌려주므로 한 턴에 이벤트가
넷(사용자, function_call, function_response, 텍스트) 생긴다.
"""

from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService

from adk_study.testing import FakeLlm, call_reply, run_in_session, text_reply
from agents.session_01_inmemory.agent import root_agent


def describe_then_answer() -> FakeLlm:
    # 한 턴 분량이다. FakeLlm 은 replies 를 소비하므로 턴마다 새로 만든다.
    return FakeLlm(
        replies=[
            call_reply("describe_session", {}),
            text_reply("알려 드렸어요"),
        ]
    )


async def test_new_session_has_identity_and_empty_history():
    # 세션은 Runner 가 아니라 session_service 가 만든다.
    # InMemoryRunner 는 InMemorySessionService 를 안에 만들어 둔다.
    runner = InMemoryRunner(agent=root_agent, app_name="test")

    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    # app_name, user_id, id 세 값이 세션 하나를 가리키는 열쇠다.
    # id 는 넘기지 않으면 uuid 로 채워진다.
    assert session.app_name == "test"
    assert session.user_id == "user"
    assert session.id
    assert session.state == {}
    assert session.events == []


async def test_tool_sees_session_with_events_so_far():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    root_agent.model = describe_then_answer()
    first = await run_in_session(runner, session, "세션 알려 줘")
    root_agent.model = describe_then_answer()
    second = await run_in_session(runner, session, "다시")

    # run_async 가 내보내는 순서는 function_call, function_response,
    # 텍스트다. [1] 이 function_response 이고 도구의 반환값이 들어 있다.
    seen_first = first[1].get_function_responses()[0].response
    seen_second = second[1].get_function_responses()[0].response
    # 도구가 돌 때 이미 사용자 메시지와 function_call 이 세션에 있다.
    # Runner 가 모델 이벤트를 받는 즉시 세션에 붙인 뒤에야 flow 가
    # 도구를 부르기 때문이다. 그래서 첫 턴은 0 이 아니라 2 다.
    assert seen_first == {"id": session.id, "user_id": "user", "events": 2}
    # 둘째 턴은 앞 턴의 넷에 이번 턴의 둘을 더한 6 이다.
    assert seen_second["events"] == 6


async def test_each_turn_appends_user_and_agent_events():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    root_agent.model = describe_then_answer()
    await run_in_session(runner, session, "세션 알려 줘")

    # Runner 는 저장소에서 꺼낸 복사본에 이벤트를 붙이므로 위의
    # session 객체는 그대로다. 결과는 다시 꺼내서 본다.
    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    # 사용자 메시지 뒤에 에이전트가 만든 function_call,
    # function_response, 텍스트가 붙어 한 턴에 넷이다.
    authors = [e.author for e in stored.events]
    assert authors == ["user"] + ["session_inspector"] * 3
    # last_update_time 은 만들 때 찍히고 이벤트가 붙을 때마다 그
    # 이벤트의 timestamp 로 바뀐다.
    assert stored.last_update_time >= session.last_update_time


async def test_sessions_of_same_user_are_independent():
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    first = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )
    root_agent.model = describe_then_answer()
    await run_in_session(runner, first, "세션 알려 줘")

    second = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    # list_sessions 는 ListSessionsResponse 를 주고 세션 목록은
    # .sessions 에 있다. 목록의 세션에는 events 가 비어 있으므로
    # 이벤트를 보려면 get_session 으로 하나씩 꺼내야 한다.
    listed = await runner.session_service.list_sessions(
        app_name="test", user_id="user"
    )
    assert {s.id for s in listed.sessions} == {first.id, second.id}
    assert all(s.events == [] for s in listed.sessions)
    assert second.events == []


async def test_in_memory_sessions_live_only_inside_the_service():
    """InMemorySessionService 는 인스턴스 안의 dict 가 저장소다."""
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    # 같은 app_name, user_id, id 라도 다른 인스턴스는 모른다.
    # 프로세스를 다시 띄우면 이 상황이 된다.
    other = InMemorySessionService()
    missing = await other.get_session(
        app_name="test", user_id="user", session_id=session.id
    )

    assert missing is None
