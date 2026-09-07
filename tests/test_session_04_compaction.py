"""session_04_compaction: App 이 이력을 요약해 압축한다.

FakeLlm 하나가 에이전트 응답과 요약 요청을 모두 받는다.
요청이 들어온 순서와 각 요청의 contents 를 보면 압축이 언제 끼어들고
다음 턴이 무엇을 받는지 알 수 있다.
"""

from google.adk.runners import InMemoryRunner

from adk_study.testing import FakeLlm, run_in_session, text_reply
from agents.session_04_compaction.agent import app, root_agent


def four_turns_and_one_summary() -> FakeLlm:
    """세 턴 동안 모델이 받는 요청 넷에 맞춰 응답을 순서대로 준비한다.

    둘째 턴이 끝나면 Runner 가 요약 요청을 보내므로 셋째 응답이 요약이
    되고 셋째 턴의 답은 넷째 응답이다. 요약 요청도 root_agent 의 모델,
    즉 이 FakeLlm 으로 나가기 때문에 한 목록에 섞어 둔다.
    """
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
    # 첫 압축 때 Runner 가 root_agent 의 모델로 LlmEventSummarizer 를
    # 만들어 config.summarizer 에 넣고 그 뒤로는 재사용한다. app 은 모듈
    # 변수라 테스트끼리 공유되므로, 비우지 않으면 두 번째 테스트부터
    # 요약 요청이 앞 테스트의 FakeLlm 으로 간다.
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
    # 요약 요청은 세션 이력을 텍스트 하나로 이어 붙인 user 콘텐츠 하나다.
    # "summarize" 는 LlmEventSummarizer 기본 프롬프트에 들어 있는 말이다.
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
    # 요약문은 이벤트 content 가 아니라 actions.compaction 안에 있다.
    summary = compactions[0].actions.compaction.compacted_content
    assert summary.parts[0].text == "사용자가 인사했고 에이전트가 두 번 답했다"


async def test_raw_events_stay_in_session_after_compaction():
    fake = four_turns_and_one_summary()

    runner, session_id = await run_three_turns(fake)

    stored = await runner.session_service.get_session(
        app_name=app.name, user_id="user", session_id=session_id
    )
    # 압축은 원본 이벤트를 지우지 않고 둘째 턴 뒤에 요약 이벤트 하나를
    # 덧붙일 뿐이다. 요약 이벤트는 author 가 user 이고 content 가 없다.
    authors = [e.author for e in stored.events]
    assert authors == [
        "user",
        "session_compact",
        "user",
        "session_compact",
        "user",
        "user",
        "session_compact",
    ]
    assert stored.events[4].actions.compaction
    assert stored.events[4].content is None


async def test_third_turn_sees_summary_instead_of_raw_history():
    fake = four_turns_and_one_summary()

    await run_three_turns(fake)

    # "For context:" 는 세션에 저장된 것이 아니라 요청을 만들 때 생긴다.
    # 요약이 author 가 model 인 이벤트로 취급되어 다른 에이전트의 말처럼
    # "[model] said: ..." 형태의 user 콘텐츠로 바뀐다.
    third = fake.requests[3].contents
    assert third[0].parts[0].text == "For context:"
    assert "사용자가 인사했고" in third[0].parts[1].text
    assert third[-1].parts[0].text == "셋"
    # 요약 범위(타임스탬프 구간)에 든 원본 이벤트는 요청에서 빠진다.
    assert all("첫 답" not in p.text for c in third for p in c.parts if p.text)
