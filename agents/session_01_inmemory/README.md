# session_01_inmemory

## 이 단계가 보여주는 것

- Session 은 app_name, user_id, id 로 식별되는 대화 하나다.
  안에는 state 사전과 events 목록, last_update_time 이 있다.
  last_update_time 은 만들 때 찍히고 이벤트가 붙을 때마다 그 이벤트의 timestamp 로 바뀐다.
- 세션은 Runner 가 아니라 SessionService 가 만들고 저장한다.
  Runner 는 턴을 시작할 때 SessionService 에서 세션을 꺼내고, 이벤트가 생길 때마다 `append_event` 로 돌려준다.
  InMemoryRunner 가 쓰는 InMemorySessionService 는 인스턴스 안의 dict 가 저장소라 프로세스가 끝나면 사라진다.
- 턴마다 사용자 메시지 이벤트와 에이전트 이벤트가 events 에 쌓인다.
  도구를 한 번 쓰는 이 단계는 한 턴에 사용자, function_call, function_response, 텍스트 넷이다.
- 도구가 실행되는 시점에는 이번 턴의 사용자 메시지와 function_call 이벤트가 이미 들어 있다.
  Runner 는 사용자 메시지를 세션에 붙인 뒤 에이전트를 돌리고, 모델 이벤트를 받는 즉시 세션에 붙인 다음에 flow 가 도구를 부르기 때문이다.
  그래서 첫 턴의 도구는 events 를 2 로 센다.
- 도구는 `tool_context.session` 으로 지금 세션을 읽을 수 있다.
  state_02_tool_context 에서 본 `tool_context.state` 와 같은 ToolContext 의 다른 속성이다.
- 같은 사용자라도 세션이 다르면 events 를 공유하지 않는다.
  `list_sessions` 로 사용자의 세션 목록을 받을 수 있지만 목록의 세션에는 events 가 비어 있다.

## adk web 에서 확인할 것

```bash
uv run adk web agents --session_service_uri memory://
```

- 옵션 없이 켜면 1.36.2 의 adk web 은 `agents/<단계>/.adk/session.db` 에 세션을 남긴다.
  InMemorySessionService 의 동작을 보려면 `memory://` 를 준다.
- "세션 알려 줘" 를 보낸다. 도구가 돌려준 id 가 주소창 `session=` 뒤의 값과 같다.
  adk web 은 세션을 만들 때 그 id 를 주소창에 적고 이후 요청에 그대로 쓴다.
- 한 번 더 보내면 events 수가 6 이 된다. 앞 턴의 이벤트 넷과 이번 턴의 둘이다.
- 왼쪽 위에서 새 세션을 만들면 events 가 2 부터 다시 시작한다.
- adk web 을 껐다 켜면 세션 목록이 비어 있다. 다음 단계에서 남기는 방법을 본다.

## 이전 단계와 다른 점

event_01_text 에 tool_context.session 을 읽는 describe_session 도구가 더해졌다.
