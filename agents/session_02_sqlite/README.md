# session_02_sqlite

## 이 단계가 보여주는 것

- 에이전트 코드는 session_01 과 같다.
  세션을 어디에 남길지는 에이전트가 아니라 Runner 에 넣는 SessionService 가 정한다.
  Runner 생성자의 session_service 는 기본값이 없는 필수 인자이고, InMemoryRunner 는 여기에 InMemorySessionService 를 대신 넣어 주는 축약이다.
- adk web 은 `--session_service_uri` 의 스킴으로 서비스를 고른다.
  `sqlite://` 는 SqliteSessionService, `memory://` 는 InMemorySessionService 다.
  `sqlite:///sessions.db` 처럼 슬래시 셋이면 adk web 을 실행한 디렉터리 기준 상대경로, `sqlite:////Users/me/sessions.db` 처럼 넷이면 절대경로다.
- 옵션을 아예 빼면 1.36.2 는 InMemory 가 아니라 `agents/<에이전트>/.adk/session.db` 에 에이전트별 SQLite 를 만든다.
  그래서 session_01 에서도 재시작 후 세션이 남아 있었을 수 있다.
  메모리 동작을 보려면 `--session_service_uri memory://` 를 준다.
- SqliteSessionService 는 경로 외에 아무것도 메모리에 두지 않고 호출마다 파일을 새로 연다.
  같은 파일을 여는 새 인스턴스는 이전 프로세스가 남긴 세션을 그대로 읽고, 도구가 세는 events 수도 이어진다.
  테스트는 이 성질을 이용해 프로세스 재시작을 새 인스턴스로 대신한다.

## adk web 에서 확인할 것

```bash
uv run adk web agents --session_service_uri sqlite:///sessions.db
```

- session_02_sqlite 를 고르고 "세션 알려 줘" 를 보낸다.
  프로젝트 루트에 sessions.db 가 생긴다.
- adk web 을 끄고 같은 명령으로 다시 켠다. 왼쪽 세션 목록에 방금 세션이 남아 있다.
- 그 세션을 열어 "다시" 를 보내면 events 가 6 이다.
- `--session_service_uri memory://` 로 켜면 목록이 비어 있고, 껐다 켜면 방금 만든 세션도 사라진다.
- sessions.db 와 .adk/session.db 는 .gitignore 의 `*.db` 규칙에 걸려 커밋되지 않는다.

## 이전 단계와 다른 점

에이전트 코드 변경이 없다.
실행 명령의 `--session_service_uri` 와, 테스트에서 InMemoryRunner 대신 Runner 에 SqliteSessionService 를 직접 넣는 것만 다르다.
