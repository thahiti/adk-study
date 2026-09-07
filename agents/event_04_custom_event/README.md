# event_04_custom_event

## 이 단계가 보여주는 것

- Event 는 LLM 만 만드는 것이 아니다.
  BaseAgent 를 상속해 `_run_async_impl` 에서 Event 를 직접 만들어 yield 하면 Runner 는 똑같이 처리한다.
- 직접 만들 때 채워야 하는 것은 author 와 content 다.
  invocation_id 는 `ctx.invocation_id` 에서 가져와 같은 턴임을 표시한다.
- `actions=EventActions(state_delta={...})` 를 실으면 Runner 가 세션 상태에 반영한다.
  상태가 어떻게 바뀌고 읽히는지는 state 토픽에서 다룬다.
- yield 한 번이 Runner 로 제어를 넘기는 지점이다.
  Runner 가 이벤트를 세션에 기록한 뒤 다음 줄이 실행된다. 이 흐름은 runtime-loop 토픽에서 다룬다.

## adk web 에서 확인할 것

- 아무 메시지나 보낸다. 모델을 부르지 않으므로 OPENAI_API_KEY 가 없어도 동작한다.
- 채팅창에 알림 두 개가 차례로 나타난다.
- Events 탭에서 두 번째 이벤트의 actions.stateDelta 에 announced 가 있고, 왼쪽 State 탭에 announced 가 2 로 반영된 것을 본다.

## 이전 단계와 다른 점

LlmAgent 대신 BaseAgent 상속 클래스가 root_agent 다. 모델과 instruction 이 사라지고 `_run_async_impl` 이 생겼다.
