"""event_01_text: 텍스트 응답 하나가 이벤트 하나가 되는 최소 흐름.

에이전트 코드는 basics_01_hello 와 같다. 도구 없이 텍스트로만 답하게
해서 한 턴에 모델 응답 이벤트가 하나만 생기게 하는 것이 목적이다.
Event 의 필드는 tests/test_event_01_text.py 에서 하나씩 확인한다.
"""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="event_text",
    model=make_model(),
    description="질문에 한 문단으로 답하는 에이전트",
    instruction="사용자 질문에 한국어로 한 문단 안에 답한다.",
)
