"""event_01_text: instruction 만 있는 최소 LlmAgent."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="event_text",
    model=make_model(),
    description="인사만 하는 최소 에이전트",
    instruction="사용자에게 한국어로 짧고 친절하게 인사한다.",
)
