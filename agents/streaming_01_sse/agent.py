"""streaming_01_sse: 텍스트 답을 조각으로 받는 에이전트.

에이전트 정의는 runner_01_minimal 과 같다. 스트리밍은 에이전트가
아니라 main.py 가 run_async 에 넘기는 RunConfig 로 켜므로 여기에는
스트리밍 관련 설정이 없다. 도구는 그대로 두어 SSE 모드에서도
function_call 이벤트가 어떻게 오는지 볼 수 있게 한다.
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
    name="stream_tool",
    model=make_model(),
    description="글자 수를 세어 주는 에이전트",
    instruction="사용자가 글자 수를 물으면 count_chars 도구를 쓰고 결과를 "
    "한국어로 알려 준다.",
    tools=[count_chars],
)
