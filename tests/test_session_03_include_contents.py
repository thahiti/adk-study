"""session_03_include_contents: 이력이 모델 입력이 되는 방식.

FakeLlm 은 받은 LlmRequest 를 requests 에 쌓아 두므로 모델이 실제로
어떤 contents 를 받았는지 턴별로 들여다볼 수 있다.
"""

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

from adk_study.testing import (
    FakeLlm,
    call_reply,
    run_in_session,
    text_reply,
)
from agents.session_03_include_contents.agent import root_agent


def texts(fake: FakeLlm, index: int) -> list[tuple[str, str]]:
    """index 번째 모델 요청의 contents 를 (role, text) 목록으로 만든다."""
    return [(c.role, c.parts[0].text) for c in fake.requests[index].contents]


async def test_default_agent_sends_whole_history():
    """기본값이 어떤 동작인지 보여 주는 대조군이다.

    root_agent 가 아니라 include_contents 를 주지 않은 LlmAgent 를
    따로 만들어 둘째 요청에 첫 턴의 질문과 답이 함께 실리는 것을
    확인한다.
    """
    fake = FakeLlm(replies=[text_reply("첫 답"), text_reply("둘째 답")])
    agent = LlmAgent(name="remembering", model=fake, instruction="")
    runner = InMemoryRunner(agent=agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "하나")
    await run_in_session(runner, session, "둘")

    assert texts(fake, 1) == [
        ("user", "하나"),
        ("model", "첫 답"),
        ("user", "둘"),
    ]


async def test_none_agent_sends_only_current_message():
    """none 이면 둘째 요청에 첫 턴이 빠지고 이번 메시지만 남는다."""
    fake = FakeLlm(replies=[text_reply("첫 답"), text_reply("둘째 답")])
    root_agent.model = fake
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "하나")
    await run_in_session(runner, session, "둘")

    assert texts(fake, 1) == [("user", "둘")]


async def test_none_agent_still_sends_tool_events_of_current_turn():
    """none 은 이번 턴 안의 도구 호출과 결과는 모델에 보낸다.

    둘째 턴에서 도구를 부르면 모델 요청이 두 번 간다. 도구 결과를
    받은 뒤의 셋째 요청에는 첫 턴은 없지만 이번 턴의 사용자 메시지,
    function_call, function_response 가 순서대로 들어 있어야 한다.
    도구가 본 events 수가 4 인 것은 세션에는 첫 턴이 남아 있다는
    뜻이다.
    """
    fake = FakeLlm(
        replies=[
            text_reply("첫 답"),
            call_reply("describe_session", {}),
            text_reply("알려 드렸어요"),
        ]
    )
    root_agent.model = fake
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "하나")
    await run_in_session(runner, session, "세션 알려 줘")

    contents = fake.requests[2].contents
    assert [c.role for c in contents] == ["user", "model", "user"]
    assert contents[0].parts[0].text == "세션 알려 줘"
    assert contents[1].parts[0].function_call.name == "describe_session"
    response = contents[2].parts[0].function_response.response
    assert response["events"] == 4


async def test_session_still_keeps_full_history():
    """모델이 앞 턴을 못 봐도 세션에는 네 이벤트가 그대로 남는다."""
    root_agent.model = FakeLlm(
        replies=[text_reply("첫 답"), text_reply("둘째 답")]
    )
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "하나")
    await run_in_session(runner, session, "둘")

    stored = await runner.session_service.get_session(
        app_name="test", user_id="user", session_id=session.id
    )
    assert len(stored.events) == 4
