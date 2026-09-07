# loop_02_state_commit

## 이 단계가 보여주는 것

- state_delta 를 실은 이벤트를 yield 하기 전에는 `ctx.session.state` 에 그 키가 없다.
  yield 한 뒤에는 있다.
- 러너는 이벤트를 받으면 `session_service.append_event` 를 부르고, 세션 서비스가 delta 를 세션 state 에 합친다.
  그 뒤에야 에이전트를 재개하므로 에이전트는 yield 다음 줄에서 반영된 값을 읽을 수 있다.
- 이것이 ADK 런타임의 핵심 약속이다.
  에이전트, 도구, 콜백이 이벤트를 내보낸 뒤 이어서 도는 코드는 그 이벤트가 처리된 뒤의 상태를 본다.
- 셋째 이벤트는 반영된 값을 텍스트로 알린다. 세션의 이벤트 셋 중 둘째만 delta 를 가진다.

## adk web 에서 확인할 것

- 스크립트를 실행해 `announced before yield = None` 과 `after yield = 2` 사이에 `runner: got 두 번째 알림` 이 있는지 본다.
- adk web 에서 메시지를 보내면 셋째 알림에 `state 반영 확인: 2` 가 나오고 State 탭에 announced 가 2 다.

## 이전 단계와 다른 점

loop_01_pause_resume 의 둘째 yield 앞뒤에 state 읽기가 더해지고 셋째 이벤트가 생겼다.
