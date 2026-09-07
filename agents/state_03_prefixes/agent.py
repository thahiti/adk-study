"""state_03_prefixes: user:, app:, temp: 접두어로 범위를 나눈다.

접두어는 키 문자열의 일부일 뿐이라 쓰는 쪽 코드는 접두어 없는 키와
같다. 세션 서비스가 이벤트를 저장할 때 접두어를 보고 세션, 사용자,
앱 저장소로 나누고, 세션을 읽을 때 다시 합쳐서 돌려준다.
접두어 문자열은 google.adk.sessions.State 의 상수로 정해져 있다.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

from adk_study.models import make_model


def bump_counter(tool_context: ToolContext) -> int:
    """세션, 사용자, 앱 범위의 카운터를 각각 1 올린다.

    모델에 돌려주는 값은 세션 범위의 count 하나다. 나머지 키는
    범위 차이를 State 탭과 테스트에서 비교해 보기 위해 함께 쓴다.
    """
    state = tool_context.state
    # 접두어가 없는 count 는 이 세션에만 남는다.
    count = state.get("count", 0) + 1
    state["count"] = count
    # user: 는 같은 user_id 의 다른 세션에서도 이어서 늘어난다.
    state["user:total"] = state.get("user:total", 0) + 1
    # app: 은 user_id 가 달라도 이어서 늘어난다.
    state["app:hits"] = state.get("app:hits", 0) + 1
    # temp: 는 이 턴 안에서만 읽힌다. 세션 서비스가 이벤트를 저장하기
    # 전에 delta 에서 지우므로 다음 턴의 state 에는 없다.
    state["temp:last_call"] = "bump_counter"
    return count


root_agent = LlmAgent(
    name="state_scoped",
    model=make_model(),
    description="부를 때마다 카운터를 올리는 에이전트",
    instruction="사용자가 올리라고 하면 bump_counter 도구를 쓰고 새 값을 "
    "한국어로 알려 준다. 직전 답: {last_answer?}",
    tools=[bump_counter],
    output_key="last_answer",
)
