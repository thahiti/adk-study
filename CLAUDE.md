# ADK 학습 프로젝트

Google ADK(Agent Development Kit) 1.36.x의 핵심 개념을 토픽별로 최소 구현에서 출발해 단계적으로 확장하며 익히는 프로젝트다.
설계 문서는 /Users/randy/study/google-adk/docs/superpowers/specs/2026-09-07-adk-study-design.md 에 있다.

## 사실 확인 원칙

- adk.dev 문서와 Context7 결과는 2.x 기준인 경우가 많다.
  API를 쓰기 전에 v1.36.2 태그 소스나 `.venv/lib/python3.13/site-packages/google/adk/` 에 설치된 코드로 확인한다.
- 1.36.2의 `adk web`은 agents 디렉터리 바로 아래 폴더만 인식한다. 중첩 폴더를 만들지 않는다.
- OpenAI 모델은 `LiteLlm(model="openai/<모델명>")` 으로만 쓴다. `google.adk.labs.openai`는 1.36.2에 없다.

## 구조

```
pyproject.toml          uv 단일 프로젝트, python 3.13
src/adk_study/          공용 코드 (models.py 등)
agents/<토픽>_<번호>_<이름>/   단계 하나가 폴더 하나, __init__.py + agent.py + README.md
agents/runner_*/main.py 러너 스크립트, `uv run python -m agents.<단계>.main`
tests/test_<단계>.py    단계별 테스트, 모델 호출 없음
docs/superpowers/       설계 문서와 구현 계획
```

- 단계 폴더 이름은 Python 식별자여야 한다.
- 공용 코드는 `src/adk_study`에 두고 에이전트 폴더끼리 복사하지 않는다.
- 모델은 `adk_study.models.make_model()` 으로만 만든다. `.env`의 MODEL_NAME을 읽는다.

## 명령

```
uv sync                              의존성 설치
uv run adk web agents                모든 단계를 드롭다운에서 선택
uv run adk web agents --session_service_uri sqlite:///sessions.db
uv run python -m agents.runner_01_minimal.main
uv run ruff check . && uv run ruff format --check .
uv run mypy src agents
uv run pytest
```

## 토픽과 브랜치 순서

basics, event, state, session, runner, streaming, runtime-loop 순서다.
토픽 하나가 `feature/<토픽>` 브랜치 하나이고, 선행 토픽이 main에 머지된 뒤 다음 브랜치를 main에서 딴다.
머지는 rebase 후 `--no-ff`, 머지 커밋 제목은 `merge:`로 시작한다.

## 단계 추가 규칙

1. 복사 커밋: 이전 단계 폴더와 테스트 파일을 새 이름으로 그대로 복사한다.
   바꾸는 것은 폴더명과 에이전트 name 같은 식별자뿐이다.
   제목은 `copy: state_01_output_key -> state_02_tool_context` 형식이다.
2. 수정 커밋: 새 단계가 달성할 내용만 고친다. diff에 학습 포인트만 남긴다.
3. 다른 토픽의 마지막 단계에서 출발하는 첫 단계도 복사 커밋을 먼저 만든다.
4. 처음부터 새로 쓰는 단계만 복사 없이 커밋 하나로 만들고 본문에 이유를 적는다.

## 커밋 크기 규칙

1. 수정 커밋의 Python 코드 변경량(추가와 삭제 합계)은 30줄을 목표로 한다.
   복사 커밋, 스캐폴드, uv.lock, README, 테스트는 세지 않는다.
2. 넘으면 실행 가능한 단위로 나눈다. 예: 클래스 정의 커밋, root_agent 교체 커밋.
3. 나눠도 넘는 단일 클래스는 예외로 두고 본문에 이유를 적는다.
4. 테스트는 코드와 같은 커밋에 둔다.

## 문서와 언어

- 주석, 독스트링, README는 한글로 쓴다. 식별자는 영어다.
- 단계 README에는 이 단계가 보여주는 것, adk web에서 확인할 것, 이전 단계와 다른 점을 적는다.
- 커밋 제목은 영어 50자 이내, 본문은 한글로 왜 바꿨는지 적는다.

## 테스트

- InMemoryRunner와 BaseLlm을 상속한 가짜 모델로 검증한다.
- GPT 호출은 테스트하지 않는다.
