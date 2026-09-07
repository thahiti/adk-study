# loop_01_pause_resume

## 이 단계가 보여주는 것

- 에이전트의 `_run_async_impl` 은 async generator 다.
  yield 는 이벤트를 러너에 넘기는 동시에 에이전트를 그 자리에서 멈추는 지점이다.
- 러너는 이벤트를 받으면 세션에 저장하고 호출자(for 루프)에게 넘긴다.
  호출자가 다음 이벤트를 요청해야 에이전트가 yield 다음 줄부터 이어서 돈다.
- 그래서 스크립트 출력은 "agent: before yield 1, runner: got ..., agent: after yield 1" 순서로 번갈아 나온다.
  에이전트가 이벤트를 모두 만든 뒤 러너가 받는 것이 아니다.
- 이 구조 덕분에 러너는 이벤트 하나를 처리(저장, 플러그인, 상태 반영)한 뒤에 에이전트를 재개할 수 있다.
  다음 단계에서 그 결과를 에이전트가 읽는 것을 본다.

## adk web 에서 확인할 것

- 스크립트 `uv run python -m agents.loop_01_pause_resume.main` 을 실행해 여섯 줄의 순서를 본다.
- adk web 에서 메시지를 보내면 알림 두 개가 차례로 나타난다. 터미널에는 agent 쪽 print 만 찍힌다.

## 이전 단계와 다른 점

event_04_custom_event 에 yield 전후 print 와 러너 쪽 print 를 찍는 main.py 가 더해졌다.
