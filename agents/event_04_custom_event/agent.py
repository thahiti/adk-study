"""event_04_custom_event: 텍스트 응답 하나가 이벤트 하나가 되는 최소 흐름."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="event_custom",
    model=make_model(),
    description="질문에 한 문단으로 답하는 에이전트",
    instruction="사용자 질문에 한국어로 한 문단 안에 답한다.",
)
