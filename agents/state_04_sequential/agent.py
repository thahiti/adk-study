"""state_04_sequential: 응답을 state 에 저장하고 다음 턴에 읽는다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="state_lister",
    model=make_model(),
    description="직전 답을 기억하는 에이전트",
    instruction="사용자 질문에 한국어로 한 문단 안에 답한다. "
    "직전 답: {last_answer?}",
    output_key="last_answer",
)
