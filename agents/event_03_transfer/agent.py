"""event_03_transfer: 자식 에이전트로 전환하는 이벤트."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model


def count_chars(text: str) -> int:
    """공백을 뺀 글자 수를 센다.

    Args:
        text: 글자 수를 셀 문자열.
    """
    return len(text.replace(" ", ""))


# description 은 부모 모델이 읽는 글이다. ADK 가 자식의 name 과
# description 을 부모의 system instruction 에 넣어 주므로 어떤 일을
# 맡는지 한 줄로 분명히 적는다.
counter = LlmAgent(
    name="event_counter",
    model=make_model(),
    description="글자 수를 세는 일을 맡는다",
    instruction="count_chars 도구로 글자 수를 세어 한국어로 알려 준다.",
    tools=[count_chars],
)

# sub_agents 가 있으면 tools 를 주지 않아도 transfer_to_agent 도구가
# 자동으로 붙는다. instruction 에 자식의 name 을 그대로 쓰는 이유는
# 그 도구의 agent_name 인자로 name 을 넘겨야 하기 때문이다.
root_agent = LlmAgent(
    name="event_parent",
    model=make_model(),
    description="요청을 알맞은 자식에게 넘기는 에이전트",
    instruction="글자 수 요청은 event_counter 에게 넘기고 나머지는 직접 "
    "한국어로 답한다.",
    sub_agents=[counter],
)
