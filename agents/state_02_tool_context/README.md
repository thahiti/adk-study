# state_02_tool_context

## 이 단계가 보여주는 것

- 세션 state 는 키와 값의 사전이고, 바뀔 때는 반드시 Event 의 `actions.state_delta` 를 거친다.
- `output_key="last_answer"` 를 주면 LlmAgent 가 최종 텍스트를 delta 에 실어 보내고 Runner 가 세션에 반영한다.
  에이전트 코드가 state 를 직접 만지지 않는다.
- instruction 의 `{last_answer?}` 는 실행 시점의 state 값으로 치환된다.
  `?` 가 없으면 키가 없을 때 KeyError 가 나므로 첫 턴을 위해 붙인다.
- 첫 턴의 system instruction 에는 값이 비어 있고, 둘째 턴부터 직전 답이 들어간다.

## adk web 에서 확인할 것

- 질문을 하나 보낸 뒤 왼쪽 State 탭을 연다. last_answer 에 방금 답이 들어 있다.
- Events 탭에서 응답 이벤트의 actions.stateDelta 를 본다.
- 둘째 질문을 보내고 Events 탭에서 모델 요청(request)을 열면 system instruction 에 직전 답이 들어 있다.

## 이전 단계와 다른 점

event_01_text 에 `output_key` 한 줄과 instruction 의 `{last_answer?}` 가 더해졌다.
