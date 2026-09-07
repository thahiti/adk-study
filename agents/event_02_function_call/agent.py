"""event_02_function_call: 도구 호출 한 번이 이벤트 셋을 만든다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model


def count_chars(text: str) -> int:
    """공백을 뺀 글자 수를 센다.

    Args:
        text: 글자 수를 셀 문자열.
    """
    return len(text.replace(" ", ""))


root_agent = LlmAgent(
    name="event_tool",
    model=make_model(),
    description="글자 수를 세어 주는 에이전트",
    instruction="사용자가 글자 수를 물으면 count_chars 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[count_chars],
)
