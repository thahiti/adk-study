# session_02_sqlite

## 이 단계가 보여주는 것

- 에이전트 코드는 session_01 과 같다. 세션을 어디에 남길지는 에이전트가 아니라 Runner 에 주입하는 SessionService 가 정한다.
- adk web 은 `--session_service_uri` 로 서비스를 고른다.
  `sqlite:///sessions.db` 를 주면 SqliteSessionService 가 되고 재시작해도 세션과 이벤트가 남는다.
- 같은 파일을 여는 새 서비스 인스턴스는 이전 프로세스가 남긴 세션을 그대로 읽는다.
  도구가 세는 events 수도 이어진다.

## adk web 에서 확인할 것

```bash
uv run adk web agents --session_service_uri sqlite:///sessions.db
```

- session_02_sqlite 를 고르고 "세션 알려 줘" 를 보낸다.
- adk web 을 끄고 같은 명령으로 다시 켠다. 왼쪽 세션 목록에 방금 세션이 남아 있다.
- 그 세션을 열어 "다시" 를 보내면 events 가 6 이다.
- 옵션 없이 켜면 목록이 비어 있다. sessions.db 는 .gitignore 에 있다.

## 이전 단계와 다른 점

코드 변경이 없다. 실행 명령의 `--session_service_uri` 와 테스트의 SqliteSessionService 만 다르다.
