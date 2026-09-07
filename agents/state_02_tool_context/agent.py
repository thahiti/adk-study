"""state_02_tool_context: 도구가 state 를 읽고 쓴다.

state_01 에서는 output_key 가 state 를 대신 써 줬다. 이 단계에서는
도구 함수가 ToolContext 를 받아 state 를 직접 읽고 쓴다.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


# tool_context 는 모델이 채우는 인자가 아니다. FunctionTool 이 타입
# 힌트가 ToolContext 인 매개변수를 찾아 모델에 보내는 스키마에서 빼고,
# 도구를 실행할 때 직접 넣어 준다. 그래서 모델이 보는 이 도구는
# 매개변수가 없는 도구다.
def bump_counter(tool_context: ToolContext) -> int:
    """세션의 count 를 1 올리고 새 값을 돌려준다."""
    # 새 세션에는 count 키가 없으므로 get 의 기본값으로 0 에서
    # 시작한다. 키가 없을 때 [] 로 읽으면 KeyError 가 난다.
    count = tool_context.state.get("count", 0) + 1
    # 여기서 쓴 값은 이 턴의 세션 state 와 tool_context.actions 의
    # state_delta 양쪽에 바로 들어간다. ADK 는 도구가 끝난 뒤 그
    # actions 를 그대로 function_response 이벤트에 실어 보내고, Runner 가
    # 이벤트를 저장할 때 delta 가 세션 서비스의 state 에 반영된다.
    tool_context.state["count"] = count
    # 모델에게 새 값을 알려 주려면 돌려줘야 한다. state 에 쓴 것만으로는
    # 모델이 값을 알 수 없다. dict 가 아니므로 {"result": count} 로
    # 감싸여 function_response 에 실린다.
    return count


root_agent = LlmAgent(
    name="state_counter",
    model=make_model(),
    description="부를 때마다 카운터를 올리는 에이전트",
    instruction="사용자가 올리라고 하면 bump_counter 도구를 쓰고 새 값을 "
    "한국어로 알려 준다. 직전 답: {last_answer?}",
    tools=[bump_counter],
    # output_key 는 그대로 둔다. 도구가 쓴 count 와 output_key 가 쓴
    # last_answer 는 같은 세션 state 에 나란히 저장된다.
    output_key="last_answer",
)
