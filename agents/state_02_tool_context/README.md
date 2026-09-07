# state_02_tool_context

## 이 단계가 보여주는 것

- 도구 함수에 `tool_context: ToolContext` 인자를 두면 ADK 가 자동으로 채워 준다.
  이 인자는 모델에 보내는 스키마에 들어가지 않는다.
- `tool_context.state` 는 읽으면 현재 세션 state 이고, 쓰면 delta 에 쌓인다.
  쓴 값은 function_response 이벤트의 `actions.state_delta` 에 실려 Runner 로 간다.
- 같은 세션에서 턴을 거듭하면 값이 누적된다. 세션이 다르면 count 는 0 부터 시작한다.
- output_key 와 도구의 state 쓰기는 같은 세션 state 를 공유한다.

## adk web 에서 확인할 것

- "올려" 를 세 번 보낸다. 답이 1, 2, 3 으로 늘어난다.
- Events 탭에서 function_response 이벤트의 actions.stateDelta 에 count 가 있다.
- State 탭에 count 와 last_answer 가 함께 있다.
- 왼쪽 위에서 새 세션을 만들고 "올려" 를 보내면 다시 1 이다.

## 이전 단계와 다른 점

state_01_output_key 에 ToolContext 를 받는 bump_counter 도구가 더해졌다.
