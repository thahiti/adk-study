"""session_04_compaction: App 이 이력을 요약해 압축한다."""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, text_reply
from agents.session_04_compaction.agent import app, root_agent


def four_turns_and_one_summary() -> FakeLlm:
    """두 턴 뒤 요약 요청이 한 번 끼어드는 순서로 응답을 준비한다."""
    return FakeLlm(
        replies=[
            text_reply("첫 답"),
            text_reply("둘째 답"),
            text_reply("사용자가 인사했고 에이전트가 두 번 답했다"),
            text_reply("셋째 답"),
        ]
    )


async def run_three_turns(fake: FakeLlm) -> tuple[InMemoryRunner, str]:
    root_agent.model = fake
    # App 은 첫 압축 때 그 시점의 모델로 summarizer 를 만들어 config 에
    # 캐시하므로, 테스트마다 새 FakeLlm 을 쓰려면 비워 줘야 한다.
    app.events_compaction_config.summarizer = None
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name=app.name, user_id="user"
    )
    for text in ("하나", "둘", "셋"):
        await run_in_session(runner, session, text)
    return runner, session.id


async def test_summary_request_goes_to_agent_model_after_interval():
    fake = four_turns_and_one_summary()

    await run_three_turns(fake)

    assert len(fake.requests) == 4
    summary_prompt = fake.requests[2].contents[0].parts[0].text
    assert "summarize" in summary_prompt
    assert "하나" in summary_prompt and "둘째 답" in summary_prompt


async def test_compaction_event_is_stored_in_session():
    fake = four_turns_and_one_summary()

    runner, session_id = await run_three_turns(fake)

    stored = await runner.session_service.get_session(
        app_name=app.name, user_id="user", session_id=session_id
    )
    compactions = [e for e in stored.events if e.actions.compaction]
    assert len(compactions) == 1
    summary = compactions[0].actions.compaction.compacted_content
    assert summary.parts[0].text == "사용자가 인사했고 에이전트가 두 번 답했다"


async def test_third_turn_sees_summary_instead_of_raw_history():
    fake = four_turns_and_one_summary()

    await run_three_turns(fake)

    third = fake.requests[3].contents
    assert third[0].parts[0].text == "For context:"
    assert "사용자가 인사했고" in third[0].parts[1].text
    assert third[-1].parts[0].text == "셋"
    assert all("첫 답" not in p.text for c in third for p in c.parts if p.text)
