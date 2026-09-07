# state_02_tool_context

## 이 단계가 보여주는 것

- 도구 함수에 `tool_context: ToolContext` 인자를 두면 ADK 가 자동으로 채워 준다.
  FunctionTool 이 타입 힌트가 ToolContext 인 매개변수를 찾아 모델에 보내는 스키마에서 빼고, 도구를 실행할 때 직접 넣는다.
  그래서 모델이 보는 bump_counter 는 매개변수가 없는 도구다.
  1.36.2 에서 ToolContext 는 `google.adk.agents.context.Context` 의 별칭이라 소스를 열면 Context 로 보인다.
- `tool_context.state` 는 세션 state 와 이 도구 호출의 delta 를 함께 보는 객체다.
  읽으면 delta 에 있는 값을 먼저, 없으면 세션 state 값을 돌려준다.
  쓰면 이 턴의 세션 state 와 `tool_context.actions.state_delta` 양쪽에 바로 들어간다.
- 도구가 끝나면 ADK 가 `tool_context.actions` 를 그대로 function_response 이벤트의 actions 로 삼는다.
  그래서 도구가 쓴 값이 그 이벤트의 `actions.state_delta` 에 실려 Runner 로 가고, Runner 가 이벤트를 저장할 때 세션 서비스의 state 에 반영된다.
  이 저장은 모델을 다시 부르기 전에 끝나므로, 같은 턴의 둘째 모델 호출과 그 뒤의 도구 호출은 이미 새 값을 본다.
- state 에 쓴 것만으로는 모델이 값을 알 수 없다.
  모델에게 알려 줄 값은 도구가 돌려줘야 하고, 그 값이 function_response 의 response 로 간다.
- 같은 세션에서 턴을 거듭하면 값이 누적된다. 세션이 다르면 count 는 0 부터 시작한다.
- output_key 와 도구의 state 쓰기는 같은 세션 state 를 공유한다.
  한 턴 안에서 count 는 function_response 이벤트에, last_answer 는 최종 텍스트 이벤트에 따로 실린다.

## adk web 에서 확인할 것

- "올려" 를 세 번 보낸다. 답이 1, 2, 3 으로 늘어난다.
- Events 탭에서 function_call 이벤트의 args 가 비어 있다. tool_context 는 모델이 채우는 인자가 아니다.
- Events 탭에서 function_response 이벤트의 actions.stateDelta 에 count 가 있다.
  최종 응답 이벤트의 stateDelta 에는 last_answer 만 있다.
- State 탭에 count 와 last_answer 가 함께 있다.
- 왼쪽 위에서 새 세션을 만들고 "올려" 를 보내면 다시 1 이다.

## 이전 단계와 다른 점

state_01_output_key 에 ToolContext 를 받는 bump_counter 도구가 더해졌다.
state_01 에서는 output_key 가 state 를 대신 써 줬고, 이 단계부터 코드가 state 를 직접 읽고 쓴다.

테스트에서는 `fake.requests[0].config.tools` 로 모델에 실제로 보낸 도구 선언을 꺼내 tool_context 가 빠졌는지 본다.
