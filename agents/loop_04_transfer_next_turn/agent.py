"""loop_04_transfer_next_turn: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

# disallow_transfer_to_parent 를 건드리지 않아 기본값 False 로 둔다.
# 이 기본값이 두 가지를 동시에 정한다. 자식에게 부모로 돌아가는
# transfer_to_agent 도구가 붙고, 러너가 둘째 턴에 이 자식을 고를 수
# 있게 된다. 러너는 root 까지 부모로 되돌아갈 수 있는 에이전트만
# 다음 턴의 주인으로 인정하기 때문이다.
child = LlmAgent(
    name="loop_specialist",
    model=make_model(),
    description="넘겨받은 뒤의 대화를 계속 맡는다",
    instruction="사용자 메시지에 한국어 한 문장으로 답한다.",
)

# 부모와 자식에게 각각 model 을 준다. 자식의 model 을 비우면
# 조상 LlmAgent 의 모델을 그대로 물려받아 둘이 같은 객체가 되고,
# 그러면 둘째 턴에 부모 모델이 불리지 않는 것을 셀 수 없다.
root_agent = LlmAgent(
    name="loop_router",
    model=make_model(),
    description="첫 메시지를 받아 전문가에게 넘긴다",
    instruction="사용자 요청은 loop_specialist 에게 넘긴다.",
    sub_agents=[child],
)
