# loop_01_pause_resume

## 이 단계가 보여주는 것

- Event 는 LLM 만 만드는 것이 아니다.
  BaseAgent 를 상속해 `_run_async_impl` 에서 Event 를 직접 만들어 yield 하면 Runner 는 똑같이 처리한다.
- 하위 클래스가 채우는 것은 `_run_async_impl` 하나다.
  `run_async` 는 `@final` 이라 덮어쓸 수 없고, 콜백 처리와 InvocationContext 준비를 한 뒤 `_run_async_impl` 을 부른다.
  기본 구현은 호출될 때 NotImplementedError 를 내므로 빠뜨리면 첫 실행 때 드러난다.
  음성과 영상용 `_run_live_impl` 은 텍스트 대화에서는 필요 없다.
- Event 에서 필수인 필드는 author 뿐이고 content 는 없어도 된다.
  그래도 author 와 invocation_id 는 직접 채운다.
  author 는 Runner 가 다음 턴에 실행할 에이전트를 세션의 마지막 에이전트 이벤트 author 로 찾기 때문에 자기 name 이어야 한다.
  invocation_id 는 기본값이 빈 문자열이라 안 채워도 오류는 없지만, 세션에 빈 값으로 남아 사용자 메시지와 같은 턴이라는 연결이 끊긴다.
  `ctx.invocation_id` 에 Runner 가 턴을 시작할 때 만든 값이 들어 있다.
- `actions=EventActions(state_delta={...})` 를 실으면 세션 상태에 반영된다.
  Runner 가 이벤트를 `session_service.append_event` 에 넘기고, 거기서 state_delta 를 세션 state 에 합친다.
  상태가 어떻게 바뀌고 읽히는지는 state 토픽에서 다룬다.
- yield 한 번이 Runner 로 제어를 넘기는 지점이다.
  Runner 가 이벤트를 세션에 기록하고 호출자에게 넘긴 뒤, 호출자가 다음 이벤트를 요청해야 다음 줄이 실행된다.
  이 흐름은 runtime-loop 토픽에서 다룬다.
- `@override` 는 실행에 영향이 없는 타입 검사기용 표시다.
  부모에 같은 이름의 메서드가 없으면 mypy 가 오류를 내므로 메서드 이름 오타를 잡아 준다.
  반환 타입 `AsyncGenerator[Event]` 는 Python 3.13 부터 허용되는 표기이고 생략한 send 타입은 None 으로 본다.

## adk web 에서 확인할 것

- 아무 메시지나 보낸다. 모델을 부르지 않으므로 OPENAI_API_KEY 가 없어도 동작한다.
- 채팅창에 알림 두 개가 차례로 나타난다.
- Events 탭에서 두 번째 이벤트의 actions.stateDelta 에 announced 가 있고, 왼쪽 State 탭에 announced 가 2 로 반영된 것을 본다.
- 세 이벤트의 invocationId 가 모두 같다. 직접 만든 이벤트에 `ctx.invocation_id` 를 실었기 때문이다.

## 이전 단계와 다른 점

LlmAgent 대신 BaseAgent 상속 클래스가 root_agent 다. 모델과 instruction 이 사라지고 `_run_async_impl` 이 생겼다.
테스트도 FakeLlm 없이 root_agent 를 그대로 돌린다.
