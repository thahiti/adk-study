"""state_04_sequential: 앞 에이전트의 output_key 를 뒤 에이전트가 읽는다."""

from google.adk.agents import LlmAgent, SequentialAgent

from adk_study.models import make_model

lister = LlmAgent(
    name="state_lister",
    model=make_model(),
    description="과일 이름을 나열한다",
    instruction="사용자가 말한 주제에 맞는 과일 이름을 쉼표로 나열한다.",
    # state_01 과 같은 output_key 지만 읽는 쪽이 다르다. 다음 턴의
    # 자기 자신이 아니라 같은 턴 안에서 바로 뒤에 도는 counter 가 읽는다.
    # Runner 는 이 이벤트를 받는 즉시 세션에 저장하고, SequentialAgent 는
    # 그 뒤에야 counter 를 시작하므로 counter 가 요청을 만들 때는
    # state 에 fruits 가 이미 들어 있다.
    output_key="fruits",
)

counter = LlmAgent(
    name="state_fruit_counter",
    model=make_model(),
    description="나열된 과일의 개수를 센다",
    # {fruits} 에 `?` 를 붙이지 않는다. lister 가 항상 먼저 돌아 값을
    # 남기므로 없는 경우는 파이프라인 구성이 깨진 것이고, 빈 문자열로
    # 조용히 넘어가는 것보다 KeyError 로 드러나는 편이 낫다.
    instruction="다음 목록의 항목 수를 한국어로 답한다: {fruits}",
)

# SequentialAgent 는 model 과 instruction 이 없다. LLM 을 부르지 않고
# sub_agents 를 순서대로 실행해 자식이 만든 이벤트를 그대로 올려 보낸다.
# 자식들은 부모의 InvocationContext 를 복사해 쓰므로 invocation_id 와
# 세션이 같다. 한 사용자 메시지가 시작한 한 턴이다.
root_agent = SequentialAgent(
    name="state_pipeline",
    description="나열한 뒤 세는 두 단계 파이프라인",
    sub_agents=[lister, counter],
)
