# runner_03_run_config

## 이 단계가 보여주는 것

- `run_async` 는 new_message 외에 `run_config` 와 `state_delta` 를 받는다.
- RunConfig 는 이 턴에만 적용되는 실행 설정이다.
  `max_llm_calls` 는 한 턴의 모델 호출 상한으로 기본값 500 이다.
  도구 호출이 끝없이 반복되면 이 상한에서 `LlmCallsLimitExceededError` 가 나서 루프가 끊긴다.
  이 설정은 에이전트가 아니라 호출하는 쪽이 정한다.
- `state_delta` 는 에이전트가 돌기 전에 세션 state 에 넣을 값이다.
  사용자 메시지 이벤트의 `actions.state_delta` 에 실려 저장되므로 첫 모델 요청의 instruction 치환에 바로 쓰인다.
  외부 시스템이 아는 정보(로그인한 사용자 이름 등)를 대화에 넣는 통로다.
- 동기 코드에서는 `runner.run(...)` 을 쓸 수 있다.
  별도 스레드의 이벤트 루프에서 run_async 를 돌리고 이벤트를 큐로 넘긴다.
  빠르게 확인할 때는 `await runner.run_debug("메시지")` 가 세션까지 만들어 준다.

## 스크립트에서 확인할 것

```bash
uv run python -m agents.runner_03_run_config.main "글자 수 세 줘"
```

- 기본 max_llm_calls 4 안에서 도구 한 번, 답 한 번으로 끝난다.
- 테스트는 도구 호출만 반복하는 가짜 모델로 상한 3 에서 예외가 나는 것과, state 가 첫 요청의 system instruction 에 들어가는 것을 검사한다.

## 이전 단계와 다른 점

runner_02_services 의 run 에 max_llm_calls 와 state 인자가 생기고, run_async 에 run_config 와 state_delta 를 넘긴다.
instruction 에 `{user_name?}` 이 더해졌다.
