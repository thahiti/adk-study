"""state_01_output_key: 응답을 state 에 저장하고 다음 턴에 읽는다."""

from google.adk.agents import LlmAgent

from adk_study.models import make_model

root_agent = LlmAgent(
    name="state_memo",
    model=make_model(),
    description="직전 답을 기억하는 에이전트",
    # {last_answer?} 는 요청을 만들 때마다 그 시점의 세션 state 값으로
    # 바뀐다. 첫 턴에는 키가 아직 없어서 `?` 를 빼면 KeyError 로 턴이
    # 실패한다. `?` 를 붙이면 없는 키를 빈 문자열로 치환하고 넘어간다.
    instruction="사용자 질문에 한국어로 한 문단 안에 답한다. "
    "직전 답: {last_answer?}",
    # 최종 텍스트 응답 이벤트의 actions.state_delta 에
    # {"last_answer": 응답 텍스트} 를 실어 보낸다. 세션 state 반영은
    # Runner 가 그 이벤트를 세션에 저장할 때 일어난다.
    output_key="last_answer",
)
