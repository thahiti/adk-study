# loop_02_state_commit

## 이 단계가 보여주는 것

- `state_delta` 는 이벤트에 실려 나갈 뿐 그 자체로 세션을 바꾸지 않는다.
  그래서 그 이벤트를 yield 하기 전에는 `ctx.session.state` 에 아직 그 키가 없다.
- 러너는 에이전트가 낸 이벤트를 `session_service.append_event(session=ctx.session, event=...)` 로 저장하고,
  세션 서비스가 그 안에서 delta 를 세션 state 에 합친다.
  넘기는 세션이 에이전트가 읽는 `ctx.session` 과 같은 객체라, 저장이 끝나면 그 dict 이 이미 바뀌어 있다.
- 러너 안에서 저장은 이벤트를 호출자에게 넘기기 전에 일어나고, 에이전트는 호출자가 다음 이벤트를 요청해야 재개한다.
  그래서 yield 다음 줄은 항상 반영이 끝난 뒤에 실행된다.
  delta 를 합치는 일은 `BaseSessionService.append_event` 에 있고 모든 세션 서비스가 이것을 거치므로 서비스 종류와 무관하다.
  단, 러너는 `partial` 이 True 인 스트리밍 이벤트는 저장하지 않는다.
- 도구와 콜백은 규칙이 다르다.
  `tool_context.state` 와 `callback_context.state` 는 delta 를 세션 값 위에 겹쳐 보여 주는 `State` 래퍼라,
  쓴 값이 이벤트로 나가기 전에도 바로 읽힌다.
  이 단계처럼 이벤트를 직접 만들어 yield 할 때만 저장 시점을 기다린다.
- 셋째 이벤트는 반영된 값을 텍스트로 알리기만 하므로 delta 가 없다.
  에이전트가 낸 이벤트 셋 중 delta 를 가진 것은 둘째뿐이다.

## adk web 에서 확인할 것

- 스크립트를 실행해 `announced before yield = None` 과 `after yield = 2` 사이에 `runner: got 두 번째 알림` 이 있는지 본다.
- adk web 에서 메시지를 보내면 셋째 알림에 `state 반영 확인: 2` 가 나오고 State 탭에 announced 가 2 다.
- 세션에 쌓인 이벤트는 넷이다. 맨 앞의 사용자 메시지 이벤트도 러너가 저장하기 때문이다.

## 이전 단계와 다른 점

loop_01_pause_resume 의 둘째 yield 앞뒤에 state 읽기가 더해지고 셋째 이벤트가 생겼다.
