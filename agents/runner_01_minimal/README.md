# runner_01_minimal

## 이 단계가 보여주는 것

- adk web 없이 에이전트를 돌리려면 네 가지가 필요하다.
  SessionService, Runner, Session, 그리고 `run_async` 의 for 루프다.
  adk web 은 이 넷을 대신 해 주고 있었다.
- Runner 는 app_name, agent, session_service 로 만든다.
  session_service 는 필수 인자다. InMemoryRunner 는 이 자리에 InMemorySessionService 를 넣어 주는 축약이다.
- 세션은 Runner 가 아니라 session_service 로 만든다.
  Runner 는 run_async 를 부를 때 user_id 와 session_id 로 그 세션을 찾는다.
- `run_async` 는 async generator 다.
  for 루프가 이벤트를 하나 꺼낼 때마다 에이전트 쪽 코드가 다음 yield 까지 진행된다.
  사용자 메시지 이벤트는 세션에 저장만 되고 루프에는 나오지 않는다.
- 스크립트 실행은 `uv run python -m agents.runner_01_minimal.main` 이다.
  `.env` 의 OPENAI_API_KEY 로 실제 GPT 를 부른다.

## adk web 에서 확인할 것

- runner_01_minimal 은 adk web 에서도 그대로 동작한다. 에이전트는 event_02 와 같다.
- 같은 메시지를 adk web 과 스크립트에 보내고 Events 탭의 이벤트 셋과 스크립트의 세 줄을 비교한다.

## 이전 단계와 다른 점

event_02_function_call 에 main.py 가 더해졌다.
에이전트 코드는 그대로이고, Runner 를 만드는 쪽이 adk web 에서 스크립트로 바뀌었다.
