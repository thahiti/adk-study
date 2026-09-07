"""runner_02_services: 도구 호출 한 번이 이벤트 셋을 만든다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model


# 일반 함수를 tools 에 넣으면 LlmAgent 가 FunctionTool 로 감싼다.
# 독스트링은 도구 설명으로, 타입 힌트는 인자 스키마로 모델에 전달되므로
# 둘 다 모델이 도구를 고르고 인자를 채우는 근거가 된다.
def count_chars(text: str) -> int:
    """공백을 뺀 글자 수를 센다.

    Args:
        text: 글자 수를 셀 문자열.
    """
    # 반환값이 dict 가 아니면 ADK 가 {"result": 값} 으로 감싸서
    # function_response 에 싣는다.
    return len(text.replace(" ", ""))


root_agent = LlmAgent(
    name="runner_services",
    model=make_model(),
    description="글자 수를 세어 주는 에이전트",
    instruction="사용자가 글자 수를 물으면 count_chars 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[count_chars],
)
