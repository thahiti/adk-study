# runner_02_services

## 이 단계가 보여주는 것

- Runner 는 서비스 셋을 받는다.
  session_service 는 필수이고 artifact_service 와 memory_service 는 없으면 None 이다.
  이 단계는 셋을 모두 명시해 Runner 가 무엇에 의존하는지 드러낸다.
- 세션 서비스를 SqliteSessionService 로 바꾸면 스크립트를 다시 실행해도 세션이 남는다.
  `get_session` 으로 먼저 찾고 없을 때만 `create_session(session_id=...)` 으로 만든다.
- 에이전트와 for 루프는 runner_01 과 같다.
  어디에 저장할지는 Runner 에 넣는 서비스가 정하고, 에이전트는 모른다.

## 스크립트에서 확인할 것

```bash
uv run python -m agents.runner_02_services.main "내 이름은 철수야"
uv run python -m agents.runner_02_services.main "내 이름이 뭐지"
```

- 두 번째 실행에서 모델이 이름을 기억한다. 같은 session_id 로 이어졌기 때문이다.
- 프로젝트 루트의 sessions.db 를 지우면 처음부터 시작한다.
- adk web 에서도 runner_02_services 를 고를 수 있지만 adk web 은 자기 세션 서비스를 쓰므로 sessions.db 와 무관하다.

## 이전 단계와 다른 점

runner_01_minimal 의 InMemorySessionService 가 SqliteSessionService 로 바뀌고 아티팩트, 메모리 서비스가 명시된다.
run 에 db_path 와 session_id 인자가 생겼다.
