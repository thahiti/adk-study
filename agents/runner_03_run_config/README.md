# runner_03_run_config

## 이 단계가 보여주는 것

- `run_async` 는 new_message 외에 `run_config` 와 `state_delta` 를 받는다.
- RunConfig 는 이 턴에만 적용되는 실행 설정이다.
  호출 횟수를 세는 카운터가 턴마다 새로 만들어지는 InvocationContext 안에 있어서 다음 턴은 0 부터 다시 센다.
  `max_llm_calls` 는 한 턴의 모델 호출 상한으로 기본값 500 이고, 0 이하로 주면 제한이 없다.
  도구 호출이 끝없이 반복되면 상한을 넘는 호출을 모델에 보내기 직전에 `LlmCallsLimitExceededError` 가 나서 루프가 끊긴다.
  예외는 `run_async` 밖으로 그대로 나오므로 호출하는 쪽이 잡는다.
  그때까지 나온 이벤트(사용자 메시지, 도구 호출과 응답)는 세션에 이미 저장돼 있고 되돌아가지 않는다.
  이 설정은 에이전트가 아니라 호출하는 쪽이 정한다.
- `state_delta` 는 에이전트가 돌기 전에 세션 state 에 넣을 값이다.
  사용자 메시지 이벤트의 `actions.state_delta` 에 실려 저장되고, 저장하는 순간 세션 state 에도 반영되므로 첫 모델 요청의 instruction 치환에 바로 쓰인다.
  외부 시스템이 아는 정보(로그인한 사용자 이름 등)를 대화에 넣는 통로다.
  사용자 메시지 이벤트는 세션에 저장만 되고 `run_async` 가 yield 하지 않는다.
  그래서 state_delta 가 어디에 실렸는지 보려면 세션을 다시 읽어야 한다.
- 동기 코드에서는 `runner.run(...)` 을 쓸 수 있다.
  별도 스레드의 이벤트 루프에서 run_async 를 돌리고 이벤트를 큐로 넘긴다.
  run_config 는 받지만 state_delta 는 받지 않는다.
  빠르게 확인할 때는 `await runner.run_debug("메시지")` 가 세션까지 만들어 준다.
  user_id 와 session_id 를 주지 않으면 `debug_user_id` 와 `debug_session_id` 를 쓰고, 이벤트를 콘솔에 출력한다(`quiet=True` 로 끈다).
  run_debug 도 run_config 만 받고 state_delta 는 없다.

## 스크립트에서 확인할 것

```bash
uv run python -m agents.runner_03_run_config.main "글자 수 세 줘"
```

- 기본 max_llm_calls 4 안에서 도구 한 번, 답 한 번으로 끝난다.
- 테스트는 도구 호출만 반복하는 가짜 모델로 상한 3 에서 예외가 나는 것, 예외가 나도 그전 이벤트가 세션에 남는 것, state 가 첫 요청의 system instruction 에 들어가는 것을 검사한다.
- `runner.run` 과 `run_debug` 도 가짜 모델로 한 번씩 돌려 본다.

## 이전 단계와 다른 점

runner_02_services 의 run 에 max_llm_calls 와 state 인자가 생기고, run_async 에 run_config 와 state_delta 를 넘긴다.
instruction 에 `{user_name?}` 이 더해졌다.
