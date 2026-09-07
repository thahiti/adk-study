# session_04_compaction

## 이 단계가 보여주는 것

- Session 은 app_name, user_id, id 로 식별되는 대화 하나다.
  안에는 state 사전과 events 목록, last_update_time 이 있다.
- 세션은 Runner 가 아니라 SessionService 가 만들고 저장한다.
  기본은 InMemorySessionService 라 프로세스가 끝나면 사라진다.
- 턴마다 사용자 메시지 이벤트와 에이전트 이벤트가 events 에 쌓인다.
  도구가 실행되는 시점에는 이번 턴의 사용자 메시지와 function_call 이벤트가 이미 들어 있다.
- 도구는 `tool_context.session` 으로 지금 세션을 읽을 수 있다.
- 같은 사용자라도 세션이 다르면 events 를 공유하지 않는다.

## adk web 에서 확인할 것

- "세션 알려 줘" 를 보낸다. 도구가 돌려준 id 가 주소창의 session id 와 같다.
- 한 번 더 보내면 events 수가 6 이 된다. 앞 턴의 이벤트 넷과 이번 턴의 둘이다.
- 왼쪽 위에서 새 세션을 만들면 events 가 2 부터 다시 시작한다.
- adk web 을 껐다 켜면 세션 목록이 비어 있다. 다음 단계에서 남기는 방법을 본다.

## 이전 단계와 다른 점

event_01_text 에 tool_context.session 을 읽는 describe_session 도구가 더해졌다.
