# runner_02_services

## 이 단계가 보여주는 것

- Runner 는 session_service 외에 세 서비스를 선택으로 받는다.
  artifact_service, memory_service, credential_service 이고 기본값은 모두 None 이다.
  InMemoryRunner 는 이 중 세션, 아티팩트, 메모리 셋에 InMemory 구현을 넣어 주는 축약이다.
  이 단계는 그 셋을 직접 명시해 Runner 가 무엇에 의존하는지 드러낸다.
- 아티팩트 서비스는 파일 같은 바이너리 데이터를 세션별로 버전을 붙여 보관하는 저장소다.
  메모리 서비스는 지난 세션의 내용을 다른 세션에서 검색하기 위한 저장소다.
  둘 다 도구나 콜백이 `tool_context.save_artifact`, `search_memory` 처럼 직접 불러야 쓰인다.
  count_chars 는 그런 호출을 하지 않으므로 이 단계에서 두 서비스는 한 번도 호출되지 않는다.
  None 인 채로 그 메서드를 부르면 ValueError 가 난다.
- 세션 서비스를 SqliteSessionService 로 바꾸면 스크립트를 다시 실행해도 세션이 남는다.
  `get_session` 으로 먼저 찾고 없을 때만 `create_session(session_id=...)` 으로 만든다.
  `run_async` 는 세션을 찾기만 하고 없으면 SessionNotFoundError 를 내며, 이미 있는 id 로 `create_session` 을 부르면 AlreadyExistsError 가 나기 때문이다.
  `Runner(auto_create_session=True)` 를 주면 Runner 가 이 일을 대신하지만, 이 단계는 세션이 언제 생기는지 보이려고 직접 한다.
- 두 번째 실행이 이어지는 이유는 두 가지가 합쳐진 결과다.
  Runner 가 사용자 메시지를 포함한 모든 이벤트를 세션에 저장하고, 다음 실행에서 그 세션의 이벤트 전체를 모델에 보낸다.
  그래서 Runner 도 에이전트도 새로 만들었는데 모델은 이전 대화를 본다.
- 에이전트와 for 루프는 runner_01 과 같다.
  어디에 저장할지는 Runner 에 넣는 서비스가 정하고, 에이전트는 모른다.

## 스크립트에서 확인할 것

```bash
uv run python -m agents.runner_02_services.main "내 이름은 철수야"
uv run python -m agents.runner_02_services.main "내 이름이 뭐지"
```

- 두 번째 실행에서 모델이 이름을 기억한다. 같은 session_id 로 이어졌기 때문이다.
- 프로젝트 루트의 sessions.db 를 지우면 처음부터 시작한다.
- adk web 에서도 runner_02_services 를 고를 수 있다.
  옵션 없이 켜면 session_02 에서 본 대로 `agents/runner_02_services/.adk/session.db` 를 쓰므로 sessions.db 와 무관하다.
  `uv run adk web agents --session_service_uri sqlite:///sessions.db` 로 켜면 같은 파일을 연다.
  app_name 은 폴더 이름이고 웹 UI 의 user_id 도 "user" 라서 스크립트가 만든 runner-demo 세션이 왼쪽 목록에 보인다.

## 이전 단계와 다른 점

runner_01_minimal 의 InMemorySessionService 가 SqliteSessionService 로 바뀌고 아티팩트, 메모리 서비스가 명시된다.
세션을 `create_session` 으로 바로 만들던 것이 `get_session` 뒤 없을 때만 만드는 방식으로 바뀐다.
run 에 db_path 와 session_id 인자가 생겼다.
