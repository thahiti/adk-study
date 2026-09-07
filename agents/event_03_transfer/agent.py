"""event_03_transfer: 자식 에이전트로 전환하는 이벤트."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model


def count_chars(text: str) -> int:
    """공백을 뺀 글자 수를 센다.

    Args:
        text: 글자 수를 셀 문자열.
    """
    return len(text.replace(" ", ""))


counter = LlmAgent(
    name="event_counter",
    model=make_model(),
    description="글자 수를 세는 일을 맡는다",
    instruction="count_chars 도구로 글자 수를 세어 한국어로 알려 준다.",
    tools=[count_chars],
)

root_agent = LlmAgent(
    name="event_parent",
    model=make_model(),
    description="요청을 알맞은 자식에게 넘기는 에이전트",
    instruction="글자 수 요청은 event_counter 에게 넘기고 나머지는 직접 "
    "한국어로 답한다.",
    sub_agents=[counter],
)
