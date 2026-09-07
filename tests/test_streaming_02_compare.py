"""streaming_02_compare: NONE 과 SSE 를 같은 메시지로 비교한다."""

from adk_study.testing import FakeStreamLlm
from agents.streaming_02_compare.agent import root_agent
from agents.streaming_02_compare.main import APP_NAME, compare, run


def chunked_answer() -> FakeStreamLlm:
    return FakeStreamLlm(replies=[["안녕", "하세", "요"]])


async def test_sse_yields_partials_then_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕", True),
        ("하세", True),
        ("요", True),
        ("안녕하세요", False),
    ]
    assert [e.is_final_response() for e in events] == [
        False,
        False,
        False,
        True,
    ]


async def test_none_mode_yields_only_final():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=False)

    assert [(e.content.parts[0].text, e.partial) for e in events] == [
        ("안녕하세요", False),
    ]


async def test_partials_are_printed_inline_then_final_line(capsys):
    root_agent.model = chunked_answer()

    await run(root_agent, "인사해 줘", streaming=True)

    out = capsys.readouterr().out
    assert out.startswith("안녕하세요\n")
    assert "[stream_compare] text 안녕하세요" in out


async def test_all_events_share_one_invocation():
    root_agent.model = chunked_answer()

    events = await run(root_agent, "인사해 줘", streaming=True)

    assert len({e.invocation_id for e in events}) == 1


def test_app_name_matches_folder():
    assert APP_NAME == "streaming_02_compare"


async def test_compare_counts_events_of_both_modes():
    root_agent.model = FakeStreamLlm(
        replies=[["안녕", "하세", "요"], ["안녕", "하세", "요"]]
    )

    counts = await compare(root_agent, "인사해 줘")

    assert counts == {"none": 1, "sse": 4}


async def test_compare_reports_same_stored_count(capsys):
    root_agent.model = FakeStreamLlm(
        replies=[["안녕", "하세", "요"], ["안녕", "하세", "요"]]
    )

    await compare(root_agent, "인사해 줘")

    out = capsys.readouterr().out
    assert "none: events=1 stored=2" in out
    assert "sse: events=4 stored=2" in out


async def test_compare_calls_model_once_per_mode():
    # FakeStreamLlm 은 호출마다 replies 를 하나씩 소비하므로 모드마다
    # 한 번씩 부르면 답 두 개가 딱 맞게 쓰인다.
    model = FakeStreamLlm(
        replies=[["안녕", "하세", "요"], ["안녕", "하세", "요"]]
    )
    root_agent.model = model

    await compare(root_agent, "인사해 줘")

    # SSE 가 조각을 여러 개 내도 모델 호출은 NONE 과 같이 한 번이다.
    assert len(model.requests) == 2
