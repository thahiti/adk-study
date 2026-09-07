"""session_03_include_contents: 이력이 모델 입력이 되는 방식."""

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, text_reply
from agents.session_03_include_contents.agent import root_agent


def texts(fake: FakeLlm, index: int) -> list[tuple[str, str]]:
    """index 번째 모델 요청의 contents 를 (role, text) 목록으로 만든다."""
    return [(c.role, c.parts[0].text) for c in fake.requests[index].contents]


async def test_default_agent_sends_whole_history():
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
    fake = FakeLlm(replies=[text_reply("첫 답"), text_reply("둘째 답")])
    root_agent.model = fake
    runner = InMemoryRunner(agent=root_agent, app_name="test")
    session = await runner.session_service.create_session(
        app_name="test", user_id="user"
    )

    await run_in_session(runner, session, "하나")
    await run_in_session(runner, session, "둘")

    assert texts(fake, 1) == [("user", "둘")]


async def test_session_still_keeps_full_history():
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
