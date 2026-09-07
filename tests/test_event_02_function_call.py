"""event_02_function_call: 도구 호출이 만드는 이벤트 셋."""

from adk_study.testing import FakeLlm, call_reply, run_turn, text_reply
from agents.event_02_function_call.agent import count_chars, root_agent


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

    assert len(events) == 3
    call, response, final = events
    assert call.get_function_calls()[0].name == "count_chars"
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
    assert {e.author for e in events} == {"event_tool"}
    assert [e.content.role for e in events] == ["model", "user", "model"]
