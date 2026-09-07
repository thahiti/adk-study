"""streaming_02_compare: streaming_01_sse 와 같은 에이전트다.

이 단계의 학습 포인트는 main.py 의 compare 에 있고 에이전트는 이름만
다르다. 기본 메시지는 도구를 부르지 않아 텍스트 이벤트만 비교한다.
"""

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
    name="stream_compare",
    model=make_model(),
    description="글자 수를 세어 주는 에이전트",
    instruction="사용자가 글자 수를 물으면 count_chars 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[count_chars],
)
