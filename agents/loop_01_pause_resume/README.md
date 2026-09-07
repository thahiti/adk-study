# loop_01_pause_resume

## 이 단계가 보여주는 것

- 에이전트의 `_run_async_impl` 은 async generator 다.
  불러도 몸통이 바로 돌지 않고, 호출자가 다음 값을 요청할 때(`async for` 한 바퀴) 다음 yield 까지만 돈다.
  yield 는 값을 넘기는 동시에 함수를 그 줄에서 멈추고 지역 변수와 실행 위치를 그대로 남긴다.
  Python 자체의 동작이고 ADK 가 더한 것이 아니다.
- 러너는 이벤트를 하나 받으면 플러그인의 `on_event` 콜백에 태우고, `session_service.append_event` 로 세션에 저장하면서 `state_delta` 를 세션 상태에 반영한 뒤, 호출자(for 루프)에게 넘긴다.
  이 순서는 `runners.py` 의 `_exec_with_plugin` 안 `async for event in agen:` 블록에 그대로 적혀 있다.
  호출자가 다음 이벤트를 요청해야 에이전트가 yield 다음 줄부터 이어서 돈다.
- 그래서 스크립트 출력은 "agent: before yield 1, runner: got ..., agent: after yield 1" 순서로 번갈아 나온다.
  에이전트가 이벤트를 모두 만든 뒤 러너가 받는 것이 아니다.
- 에이전트와 for 루프 사이에는 `BaseAgent.run_async`, 러너의 `execute`, `_exec_with_plugin`, `_run_with_trace` 까지 생성자가 여러 겹 끼어 있다.
  모두 받은 이벤트를 그대로 다시 yield 하는 통로라서 중간에 쌓이는 버퍼가 없다.
- 마지막 yield 뒤에도 몸통이 남아 있다.
  "agent: after yield 2" 는 호출자가 한 번 더 요청할 때 실행되고, 그 요청은 새 이벤트 대신 생성자 종료로 끝나 루프를 빠져나가게 한다.
- 이 구조 덕분에 러너는 이벤트 하나를 다 처리한 뒤에 에이전트를 재개시킬 수 있다.
  다음 단계에서 그렇게 반영된 상태를 에이전트가 다시 읽는 것을 본다.

## adk web 에서 확인할 것

- 스크립트 `uv run python -m agents.loop_01_pause_resume.main` 을 실행해 여섯 줄의 순서를 본다.
- adk web 에서 메시지를 보내면 알림 두 개가 차례로 나타난다.
  adk web 을 띄운 터미널에는 agent 쪽 print 만 찍힌다.
  에이전트 로더가 읽는 것은 `agent.py` 뿐이고 `main.py` 는 부르지 않기 때문이다.

## 이전 단계와 다른 점

event_04_custom_event 에 yield 전후 print 와 러너 쪽 print 를 찍는 main.py 가 더해졌다.
에이전트 코드는 print 말고 달라진 것이 없다.
