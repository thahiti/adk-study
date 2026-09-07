# state_01_output_key

## 이 단계가 보여주는 것

- 세션 state 는 키와 값의 사전이다.
  세션이 만들어진 뒤 실행 중에 바뀔 때는 Event 의 `actions.state_delta` 를 거친다.
  Runner 가 이벤트를 세션에 저장하는 순간 session_service 가 delta 를 state 에 합친다.
  처음 값은 `create_session(state=...)` 으로 이벤트 없이 넣을 수 있다.
- `output_key="last_answer"` 를 주면 LlmAgent 가 최종 응답 이벤트, 즉 `is_final_response()` 가 True 인 텍스트 이벤트의 delta 에 텍스트 파트를 이어 붙인 문자열을 싣는다.
  에이전트 코드가 state 를 직접 만지지 않는다.
  도구 호출 이벤트에는 싣지 않으므로 도구를 쓰는 에이전트라도 마지막 답만 저장된다.
- instruction 의 `{last_answer?}` 는 모델 요청을 만들 때마다 그 시점의 state 값으로 치환된다.
  `?` 가 없으면 키가 없을 때 KeyError 가 나서 그 턴이 응답 없이 끝나므로 첫 턴을 위해 붙인다.
  키는 있는데 값이 None 이면 `?` 없이도 빈 문자열이 된다.
- 첫 턴의 system instruction 에는 `직전 답:` 뒤가 비어 있고, 둘째 턴부터 직전 답이 들어간다.

## adk web 에서 확인할 것

- 질문을 하나 보낸 뒤 왼쪽 State 탭을 연다. last_answer 에 방금 답이 들어 있다.
- Events 탭에서 응답 이벤트(author state_memo)의 actions.stateDelta 를 본다.
  사용자 메시지 이벤트의 stateDelta 는 비어 있다.
- 둘째 질문을 보내고 Events 탭에서 모델 요청(request)을 열면 system instruction 에 직전 답이 들어 있다.

## 이전 단계와 다른 점

event_01_text 에 `output_key` 한 줄과 instruction 의 `{last_answer?}` 가 더해졌다.
event_01_text 의 테스트가 비어 있다고 확인한 `actions.state_delta` 에 이 단계부터 값이 실린다.
