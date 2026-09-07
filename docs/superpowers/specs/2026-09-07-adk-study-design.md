# ADK 학습 프로젝트 설계

작성일: 2026-09-07

## 목적

Google ADK(Agent Development Kit) 1.36.x의 핵심 개념을 토픽 하나씩 최소 구현에서 출발해 단계적으로 확장하며 익힌다.
모든 단계는 `adk web`에서 선택해 실행할 수 있고, 각 단계의 차이는 커밋 diff 하나로 읽을 수 있어야 한다.

## 확인된 사실

- google-adk 최신 버전은 2.8.0이고 1.36.x는 1.36.0, 1.36.1, 1.36.2가 있다.
  1.36.2는 2026-07-21에 배포된 1.x 유지보수 릴리스다.
- 1.36.2가 지원하는 Python은 3.10에서 3.13까지다.
  이 머신의 기본 python3는 3.14이므로 uv로 3.13을 고정한다.
- 1.36.2의 `adk web`은 agents 디렉터리 바로 아래 폴더만 에이전트로 인식한다.
  중첩 폴더 탐색은 2.x 기능이다.
  폴더명은 Python 식별자여야 하고 드롭다운은 알파벳순이다.
- `adk web`은 에이전트 폴더에서 상위로 올라가며 `.env`를 찾는다.
  루트에 `.env` 하나를 두면 모든 에이전트가 공유한다.
- 1.36.2에는 `google.adk.labs.openai`가 없다.
  OpenAI 모델은 `LiteLlm(model="openai/<모델명>")`으로만 쓸 수 있고 litellm은 `google-adk[extensions]` 엑스트라로 설치된다.
- 세션 서비스로 `InMemorySessionService`, `SqliteSessionService`, `DatabaseSessionService`가 있고 `adk web --session_service_uri sqlite:///<파일>`을 지원한다.
- `google.adk.plugins.BasePlugin`이 있고 before_run, on_event, after_run, before_agent, before_model, before_tool 계열 콜백을 제공한다.
- `RunConfig.streaming_mode`에 `StreamingMode.NONE`과 `StreamingMode.SSE`가 있고 SSE에서는 `Event.partial`이 True인 부분 이벤트가 온다.
- adk.dev 문서는 2.x 기준이다.
  구현 시 사실 확인은 v1.36.2 태그 소스와 `.venv`에 설치된 패키지를 기준으로 한다.

## 결정 사항

| 항목 | 결정 |
|---|---|
| 저장소 구조 | uv 단일 프로젝트, `agents/` 아래 평평한 단계 폴더 |
| 단계 노출 | 단계마다 별도 에이전트 폴더를 남겨 adk web에서 모두 선택 가능 |
| 러너 토픽 | adk web과 스크립트 병행, 스크립트는 `python -m agents.<단계>.main` |
| 모델 | OpenAI GPT, 기본 gpt-4o-mini, `.env`의 MODEL_NAME으로 변경 |
| 토픽 범위 | basics(선행), event, state, session, runner, streaming, runtime-loop |
| 테스트 | 모델 호출 없는 단위 테스트만, 가짜 모델과 InMemoryRunner 사용 |
| 언어 | 주석, 독스트링, README 모두 한글, 식별자는 영어 |
| 도구 | uv, ruff, mypy, pytest, pytest-asyncio |

## 저장소 구조

```
google-adk/
  pyproject.toml            uv 프로젝트, python 3.13, google-adk[extensions] 1.36.x
  CLAUDE.md                 프로젝트 규칙
  .env.example              OPENAI_API_KEY, MODEL_NAME
  README.md                 학습 순서와 실행 방법
  src/adk_study/            공용 코드, 설치되는 패키지
    models.py               MODEL_NAME을 읽어 LiteLlm 생성
  agents/                   adk web agents 로 실행
    __init__.py
    basics_01_hello/        __init__.py, agent.py, README.md
    ...
    runner_01_minimal/      agent.py 외에 main.py
  tests/                    단계별 pytest
  docs/superpowers/specs/   설계 문서
  docs/superpowers/plans/   구현 계획
```

- 공용 코드는 `src/adk_study`에 두어 에이전트 폴더끼리 코드를 복사하지 않는다.
- `agents`도 패키지로 설치해 러너 스크립트를 `python -m`으로 실행한다.
- 단계 폴더 이름은 `<토픽>_<두자리 번호>_<이름>` 형식이다.

## 브랜치와 커밋

### 브랜치

- 토픽 하나가 브랜치 하나다.
  `feature/basics`, `feature/event`, `feature/state`, `feature/session`, `feature/runner`, `feature/streaming`, `feature/runtime-loop` 순서다.
- 선행 토픽이 main에 머지된 뒤 다음 브랜치를 main에서 딴다.
- 머지는 rebase 후 `--no-ff`로 하고 브랜치를 지운다.
  머지 커밋 제목은 `merge:`로 시작하고 본문은 브랜치 작업 내용을 한글로 적는다.
- main의 초기 커밋들은 설계 문서, CLAUDE.md, 스캐폴드다.

### 단계 추가 규칙

1. 복사 커밋: 이전 단계 폴더와 테스트 파일을 새 단계 이름으로 그대로 복사한다.
   변경 내용은 폴더명과 에이전트 name 같은 식별자만이다.
   제목은 `copy: streaming_01_sse -> streaming_02_compare` 형식이다.
2. 수정 커밋: 새 단계가 달성할 내용만 고친다.
   diff에 학습 포인트만 남는다.
3. 첫 단계는 다른 토픽의 마지막 단계에서 출발하면 마찬가지로 복사 커밋을 먼저 만든다.
   예를 들어 event_01_text는 basics_02_tool을 복사한 뒤 수정한다.
4. 새 단계가 이전 단계와 무관하게 처음부터 쓰는 경우에만 복사 없이 추가 커밋 하나로 만들고 본문에 이유를 적는다.

### 커밋 크기 규칙

1. 수정 커밋의 Python 코드 변경량(추가와 삭제 합계)은 30줄을 목표로 한다.
   복사 커밋, 스캐폴드, uv.lock, README, 테스트는 세지 않는다.
2. 넘을 때는 실행 가능한 단위로 나눈다.
   예를 들어 커스텀 에이전트 클래스 정의 커밋과 root_agent 교체 커밋으로 나눈다.
3. 나눠도 30줄을 넘는 단일 클래스는 예외로 두고 커밋 본문에 이유를 적는다.
4. 테스트는 코드와 같은 커밋에 두되 줄 수에서 제외한다.

## 토픽별 단계

### basics (선행)

- basics_01_hello: LlmAgent와 LiteLlm, instruction만 있는 최소 에이전트
- basics_02_tool: FunctionTool 하나 추가, 함수 시그니처와 독스트링이 스키마가 되는 방식

### event

- event_01_text: Event 필드(id, invocation_id, author, content, actions, timestamp, partial)를 adk web Events 탭에서 확인
- event_02_function_call: 도구 호출 시 function_call 이벤트, function_response 이벤트, 최종 이벤트의 순서와 is_final_response 판정
- event_03_transfer: sub_agents로 위임 시 actions.transfer_to_agent가 담기는 이벤트
- event_04_custom_event: BaseAgent를 상속해 Event를 직접 만들어 yield, EventActions(state_delta) 포함

### state

- state_01_output_key: output_key로 응답 저장, instruction의 `{key}` 템플릿으로 읽기
- state_02_tool_context: 도구에서 tool_context.state 읽고 쓰기
- state_03_prefixes: app:, user:, temp: 접두어와 범위, temp:는 저장되지 않음을 확인
- state_04_sequential: SequentialAgent에서 state로 하위 에이전트 간 값 전달

### session

- session_01_inmemory: Session 구조(app_name, user_id, id, state, events), adk web에서 세션 여러 개 만들기
- session_02_sqlite: `--session_service_uri sqlite:///sessions.db`로 재시작 후에도 이력 유지
- session_03_include_contents: include_contents로 이력이 LLM 입력으로 들어가는 방식 비교
- session_04_compaction(선택): App의 events_compaction_config로 이력 압축

### runner

- runner_01_minimal: 스크립트에서 SessionService 생성, Runner 생성, create_session, run_async의 for 루프에서 이벤트 출력
- runner_02_services: Sqlite 세션 서비스와 아티팩트, 메모리 서비스 주입, 같은 session_id로 재실행
- runner_03_run_config: RunConfig(max_llm_calls), run_async의 state_delta 인자, 동기 run()과 run_async 차이

### streaming

- streaming_01_sse: RunConfig(streaming_mode=SSE)로 partial 이벤트를 받아 텍스트 누적
- streaming_02_compare: NONE과 SSE를 같은 질문으로 돌려 이벤트 수와 도착 시점 비교, adk web의 토큰 스트리밍 토글
- streaming_03_tool: 스트리밍 중 function_call 이벤트가 끼어드는 순서

### runtime-loop

- loop_01_custom_agent: `_run_async_impl`에서 이벤트 3개를 yield하며 러너 쪽 출력과 에이전트 쪽 로그를 섞어 찍어 일시정지와 재개 시점 확인
- loop_02_state_commit: state_delta를 담은 이벤트를 yield한 뒤 ctx.session.state에서 커밋된 값을 읽기
- loop_03_delegation: 커스텀 오케스트레이터가 sub_agent.run_async(ctx)를 돌려 이벤트를 다시 yield, author와 branch
- loop_04_transfer_next_turn: transfer 이후 다음 턴에서 러너가 마지막 이벤트를 보고 실행할 에이전트를 고르는 방식
- loop_05_plugin: BasePlugin의 before_run, on_event, after_run 콜백으로 adk web 안에서도 루프를 로그로 드러내기

## 환경

- Python 3.13, uv로 고정
- 의존성: `google-adk[extensions]>=1.36.2,<1.37`
- 개발 의존성: ruff, mypy, pytest, pytest-asyncio
- 환경변수는 `.env`에서 읽는다.
  OPENAI_API_KEY, MODEL_NAME(기본 gpt-4o-mini)

## 테스트

- InMemoryRunner로 커스텀 에이전트, state 변화, 이벤트 순서를 검증한다.
- LLM이 필요한 부분은 BaseLlm을 상속한 가짜 모델로 바꿔 넣어 검증한다.
- GPT 호출은 테스트하지 않는다.

## 문서

- 루트 README는 학습 순서, 실행 방법, 토픽별 단계 목록을 담는다.
- 단계 폴더마다 README를 두고 이 단계가 무엇을 보여주는지, adk web에서 무엇을 확인할지, 이전 단계와 무엇이 다른지를 적는다.
