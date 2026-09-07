"""state_04_sequential: 앞 에이전트의 output_key 를 뒤 에이전트가 읽는다."""

from google.adk.agents import LlmAgent, SequentialAgent

from adk_study.models import make_model

lister = LlmAgent(
    name="state_lister",
    model=make_model(),
    description="과일 이름을 나열한다",
    instruction="사용자가 말한 주제에 맞는 과일 이름을 쉼표로 나열한다.",
    output_key="fruits",
)

counter = LlmAgent(
    name="state_fruit_counter",
    model=make_model(),
    description="나열된 과일의 개수를 센다",
    instruction="다음 목록의 항목 수를 한국어로 답한다: {fruits}",
)

root_agent = SequentialAgent(
    name="state_pipeline",
    description="나열한 뒤 세는 두 단계 파이프라인",
    sub_agents=[lister, counter],
)
