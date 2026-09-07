# state_03_prefixes

## 이 단계가 보여주는 것

- state 키의 접두어가 범위를 정한다.
  접두어 문자열은 `google.adk.sessions.State` 의 상수 `APP_PREFIX`, `USER_PREFIX`, `TEMP_PREFIX` 다.
  - 접두어 없음: 이 세션에만 남는다.
  - `user:`: 같은 app_name 과 user_id 의 모든 세션이 공유한다.
  - `app:`: 같은 app_name 의 모든 사용자가 공유한다.
  - `temp:`: 이 턴 안에서만 읽을 수 있고 저장되지 않는다.
- 쓰는 코드는 접두어만 다르고 같다. 범위는 세션 서비스가 해석한다.
  - 저장할 때: `append_event` 가 이벤트의 `state_delta` 를 접두어별로 세션, 사용자, 앱 저장소에 나눠 넣는다.
    저장소 안에서는 접두어를 뗀 키로 둔다.
    `InMemorySessionService` 는 `user_state`, `app_state` dict 에, `SqliteSessionService` 는 `user_states`, `app_states` 테이블에 둔다.
  - 읽을 때: `create_session` 과 `get_session` 이 사용자 저장소와 앱 저장소의 값에 접두어를 다시 붙여 세션 state 에 합쳐서 돌려준다.
    그래서 새 세션도 처음부터 `user:` 와 `app:` 값을 갖고 시작한다.
  - 이 나누기와 합치기는 `InMemorySessionService`, `SqliteSessionService`, `DatabaseSessionService` 가 각각 구현한다.
- `temp:` 는 `BaseSessionService.append_event` 가 이벤트를 저장하기 전에 `state_delta` 에서 지운다.
  그래서 Runner 가 돌려주는 이벤트의 delta 에도 없고, 다음 턴에 `get_session` 으로 읽은 state 에도 없다.
  같은 턴 안에서는 세션 객체에 남아 있으므로 뒤이어 도는 도구나 에이전트는 읽을 수 있다.

## adk web 에서 확인할 것

- "올려" 를 두 번 보내고 State 탭을 본다. count, user:total, app:hits 가 모두 2 다.
  temp:last_call 은 State 탭에도, Events 탭의 function_response 이벤트 stateDelta 에도 없다.
- 새 세션을 만들고 "올려" 를 보낸다. count 는 1, user:total 과 app:hits 는 3 이다.
- 화면 위쪽 User ID 옆 편집 아이콘으로 다른 ID 를 저장하고, 새 세션을 만들어 "올려" 를 보낸다.
  count 와 user:total 은 1 이고 app:hits 만 4 로 이어서 늘어난다.
- 1.36.2 의 `adk web` 은 기본으로 `agents/state_03_prefixes/.adk/session.db` 에 SQLite 로 세션을 저장한다.
  서버를 다시 띄워도 user:total 과 app:hits 가 이어지므로, 처음부터 다시 보려면 이 파일을 지운다.

## 이전 단계와 다른 점

bump_counter 가 count 외에 user:total, app:hits, temp:last_call 을 함께 쓴다.
