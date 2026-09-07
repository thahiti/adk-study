"""runner_03_run_config: 도구 호출 한 번이 이벤트 셋을 만든다."""

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
    name="runner_config",
    model=make_model(),
    description="글자 수를 세어 주는 에이전트",
    # {user_name?} 은 세션 state 의 user_name 으로 치환된다. 이 단계에서
    # 이 값을 채우는 쪽은 에이전트가 아니라 main.py 의 run 이 run_async 에
    # 넘기는 state_delta 다. 에이전트는 값이 어디서 왔는지 모르고, 없으면
    # ? 덕분에 빈 문자열이 되어 adk web 에서도 그대로 쓸 수 있다.
    instruction="사용자가 글자 수를 물으면 count_chars 도구를 쓰고 결과를 "
    "한국어로 알려 준다. 사용자 이름: {user_name?}",
    tools=[count_chars],
)
