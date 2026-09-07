"""loop_05_plugin: 전환 뒤 다음 턴은 자식이 바로 이어받는다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

child = LlmAgent(
    name="loop_specialist",
    model=make_model(),
    description="넘겨받은 뒤의 대화를 계속 맡는다",
    instruction="사용자 메시지에 한국어 한 문장으로 답한다.",
)

root_agent = LlmAgent(
    name="loop_router",
    model=make_model(),
    description="첫 메시지를 받아 전문가에게 넘긴다",
    instruction="사용자 요청은 loop_specialist 에게 넘긴다.",
    sub_agents=[child],
)
